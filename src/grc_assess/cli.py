"""Command-line interface.

Examples:
    python -m grc_assess samples/example_manufacturer_weak.json
    python -m grc_assess samples/example_manufacturer_weak.json --baseline high --format html md --out reports
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .catalog import BASELINES, load_catalog, load_rules
from .checks import FAIL
from .engine import assess
from .reporting import WRITERS


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="grc_assess",
        description="Assess a system configuration against NIST SP 800-53 Rev. 5 baselines.",
    )
    p.add_argument("config", help="Path to the system configuration JSON file")
    p.add_argument("--baseline", choices=BASELINES,
                   help="Control baseline (default: value in the config file, else moderate)")
    p.add_argument("--format", nargs="+", choices=sorted(WRITERS), default=["html", "json"],
                   help="Report formats to write (default: html json)")
    p.add_argument("--out", default="reports", help="Output directory (default: reports)")
    p.add_argument("--rules", help="Path to a custom rules JSON file")
    p.add_argument("--fail-on", choices=["critical", "high", "medium", "low"],
                   help="Exit with code 2 if any finding at or above this severity exists (useful in CI)")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not read configuration file: {exc}", file=sys.stderr)
        return 1

    catalog = load_catalog()
    rules = load_rules(args.rules, catalog=catalog) if args.rules else load_rules(catalog=catalog)
    result = assess(config, baseline=args.baseline, catalog=catalog, rules=rules)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = Path(args.config).stem + f"_{result.baseline}"
    for fmt in args.format:
        path = out / f"{stem}.{fmt}"
        path.write_text(WRITERS[fmt](result), encoding="utf-8")
        print(f"Wrote {path}")

    rc = result.rule_counts
    print(f"\n{result.organization} | {result.baseline.title()} baseline")
    comp = "n/a" if result.compliance_pct is None else f"{result.compliance_pct:.1f}%"
    print(f"Compliance: {comp} | Risk exposure: {result.risk_score:.1f}/100 ({result.risk_rating})")
    print(f"Checks: {rc['PASS']} passed, {rc[FAIL]} failed, {rc['NOT_ASSESSED']} not assessed")
    for f in result.findings[:5]:
        print(f"  [{f.severity.upper():8}] {f.rule_id} {f.title}")
    if len(result.findings) > 5:
        print(f"  ... and {len(result.findings) - 5} more in the report")

    if args.fail_on:
        order = ["critical", "high", "medium", "low"]
        threshold = order.index(args.fail_on)
        if any(order.index(f.severity) <= threshold for f in result.findings):
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
