"""Load the control catalog and the rule set."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "data"
DEFAULT_CATALOG = DATA_DIR / "controls_nist_800_53_r5.json"
DEFAULT_RULES = DATA_DIR / "rules.json"

BASELINES = ("low", "moderate", "high")
SEVERITIES = ("critical", "high", "medium", "low")


@dataclass(frozen=True)
class Control:
    id: str
    title: str
    family: str
    family_name: str
    baselines: tuple[str, ...]
    summary: str

    def in_baseline(self, baseline: str) -> bool:
        return baseline in self.baselines


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    controls: tuple[str, ...]
    severity: str
    check: dict[str, Any] = field(hash=False)
    remediation: str = ""


@dataclass
class Catalog:
    name: str
    controls: dict[str, Control]

    def for_baseline(self, baseline: str) -> dict[str, Control]:
        return {cid: c for cid, c in self.controls.items() if c.in_baseline(baseline)}


def _family_of(control_id: str) -> str:
    return control_id.split("-", 1)[0]


def load_catalog(path: str | Path = DEFAULT_CATALOG) -> Catalog:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    families = raw.get("families", {})
    controls: dict[str, Control] = {}
    for item in raw["controls"]:
        fam = _family_of(item["id"])
        controls[item["id"]] = Control(
            id=item["id"],
            title=item["title"],
            family=fam,
            family_name=families.get(fam, fam),
            baselines=tuple(item["baselines"]),
            summary=item.get("summary", ""),
        )
    return Catalog(name=raw.get("catalog", "NIST SP 800-53"), controls=controls)


def load_rules(path: str | Path = DEFAULT_RULES, catalog: Catalog | None = None) -> list[Rule]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    rules: list[Rule] = []
    seen: set[str] = set()
    for item in raw["rules"]:
        if item["id"] in seen:
            raise ValueError(f"Duplicate rule id: {item['id']}")
        seen.add(item["id"])
        severity = item["severity"].lower()
        if severity not in SEVERITIES:
            raise ValueError(f"Rule {item['id']}: unknown severity '{severity}'")
        if catalog is not None:
            unknown = [c for c in item["controls"] if c not in catalog.controls]
            if unknown:
                raise ValueError(f"Rule {item['id']} references controls not in catalog: {unknown}")
        rules.append(
            Rule(
                id=item["id"],
                title=item["title"],
                controls=tuple(item["controls"]),
                severity=severity,
                check=item["check"],
                remediation=item.get("remediation", ""),
            )
        )
    return rules
