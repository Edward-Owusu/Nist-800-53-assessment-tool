"""Run an assessment: evaluate rules, roll results up to controls, and score risk."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .catalog import BASELINES, Catalog, Rule, load_catalog, load_rules
from .checks import FAIL, NOT_APPLICABLE, NOT_ASSESSED, PASS, evaluate
from .parameters import Parameter, apply_parameters

SEVERITY_WEIGHTS = {"critical": 10, "high": 6, "medium": 3, "low": 1}

# Control implementation statuses
IMPLEMENTED = "Implemented"
PARTIAL = "Partially implemented"
NOT_IMPLEMENTED = "Not implemented"
CONTROL_NOT_ASSESSED = "Not assessed"
CONTROL_NOT_APPLICABLE = "Not applicable"

# Overall risk rating bands on the 0-100 weighted risk exposure score
RISK_BANDS = [(10, "Low"), (25, "Moderate"), (50, "High"), (101, "Critical")]

# A family score based on fewer checks than this is flagged as limited coverage
MIN_FAMILY_CHECKS = 3


@dataclass
class RuleResult:
    rule_id: str
    title: str
    controls: list[str]
    severity: str
    status: str
    detail: str
    failing_items: list[str]
    remediation: str
    observed: Any = None
    partial: bool = False


@dataclass
class ControlResult:
    control_id: str
    title: str
    family: str
    family_name: str
    status: str
    rules: list[str]
    passed: int
    failed: int


@dataclass
class FamilySummary:
    family: str
    family_name: str
    rules_assessed: int
    rules_passed: int
    compliance_pct: float | None

    @property
    def limited_coverage(self) -> bool:
        """True when the family score rests on too few checks to be meaningful."""
        return 0 < self.rules_assessed < MIN_FAMILY_CHECKS

    @property
    def coverage_note(self) -> str:
        if self.rules_assessed == 0:
            return "Not assessed"
        if self.limited_coverage:
            return f"Limited: only {self.rules_assessed} check{'s' if self.rules_assessed > 1 else ''}"
        return "Adequate"

    @property
    def passed_text(self) -> str:
        return f"{self.rules_passed} of {self.rules_assessed}" if self.rules_assessed else "0 of 0"


@dataclass
class ScoreLine:
    severity: str
    weight: int
    assessed: int
    failed: int

    @property
    def failed_weight(self) -> int:
        return self.weight * self.failed

    @property
    def total_weight(self) -> int:
        return self.weight * self.assessed


@dataclass
class AssessmentResult:
    organization: str
    sector: str
    baseline: str
    catalog: str
    generated_at: str
    tool_version: str
    compliance_pct: float | None
    risk_score: float
    risk_rating: str
    failed_weight: int
    total_weight: int
    rule_counts: dict[str, int]
    control_counts: dict[str, int]
    rules: list[RuleResult] = field(default_factory=list)
    controls: list[ControlResult] = field(default_factory=list)
    families: list[FamilySummary] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)

    @property
    def score_breakdown(self) -> list[ScoreLine]:
        """Per-severity counts and weights behind the risk exposure score."""
        assessed = [r for r in self.rules if r.status in (PASS, FAIL)]
        return [
            ScoreLine(sev, weight,
                      sum(1 for r in assessed if r.severity == sev),
                      sum(1 for r in assessed if r.severity == sev and r.status == FAIL))
            for sev, weight in SEVERITY_WEIGHTS.items()
        ]

    @property
    def score_explanation(self) -> str:
        """One-paragraph, plain-language explanation of the headline score."""
        if not self.total_weight:
            return "No checks could be assessed, so no risk score was calculated."
        band = next(f"{lo} to below {hi}" if hi <= 100 else f"{lo} or more"
                    for (lo, _), (hi, label) in zip([(0, None)] + RISK_BANDS[:-1], RISK_BANDS)
                    if label == self.risk_rating)
        return (
            f"Each assessed check carries a weight based on its severity (critical 10, high 6, medium 3, low 1). "
            f"The failed checks carry {self.failed_weight} of the {self.total_weight} total weight points, so "
            f"risk exposure = 100 x {self.failed_weight} / {self.total_weight} = {self.risk_score:.1f}. "
            f"A score of {band} is rated {self.risk_rating}. "
            f"This differs from the share of checks passed, which counts every check equally: failing a few "
            f"critical checks raises risk exposure far more than failing many low-severity ones."
        )

    @property
    def findings(self) -> list[RuleResult]:
        """Failed rules ordered by remediation priority (severity, then id)."""
        order = {s: i for i, s in enumerate(SEVERITY_WEIGHTS)}
        failed = [r for r in self.rules if r.status == FAIL]
        return sorted(failed, key=lambda r: (order[r.severity], r.rule_id))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["findings"] = [asdict(f) for f in self.findings]
        data["score_breakdown"] = [dict(asdict(s), failed_weight=s.failed_weight, total_weight=s.total_weight)
                                   for s in self.score_breakdown]
        data["score_explanation"] = self.score_explanation
        for fam, raw in zip(self.families, data["families"]):
            raw["coverage"] = fam.coverage_note
        return data


def risk_rating(score: float) -> str:
    for upper, label in RISK_BANDS:
        if score < upper:
            return label
    return "Critical"


def _rule_in_scope(rule: Rule, scoped: dict) -> bool:
    return any(c in scoped for c in rule.controls)


def _control_status(linked: list[RuleResult]) -> str:
    statuses = [r.status for r in linked]
    assessed = [r for r in linked if r.status in (PASS, FAIL)]
    if not assessed:
        if statuses and all(s == NOT_APPLICABLE for s in statuses):
            return CONTROL_NOT_APPLICABLE
        return CONTROL_NOT_ASSESSED
    if all(r.status == PASS for r in assessed):
        return IMPLEMENTED
    if all(r.status == FAIL for r in assessed):
        # The control exists but misses its target (for example MFA on some accounts
        # but not all) is partial; a control with no evidence of being in place is not.
        return PARTIAL if any(r.partial for r in assessed) else NOT_IMPLEMENTED
    return PARTIAL


def assess(
    config: dict,
    baseline: str | None = None,
    catalog: Catalog | None = None,
    rules: list[Rule] | None = None,
    parameters: dict[str, Any] | None = None,
) -> AssessmentResult:
    """Assess a system configuration against the selected NIST SP 800-53 baseline.

    ``parameters`` sets organization-defined values by check ID, for example
    ``{"IAM-03": 60}``. Values in the configuration file's ``"parameters"`` section
    are used first, and this argument overrides them.
    """
    from . import __version__

    org = config.get("organization", {}) if isinstance(config, dict) else {}
    baseline = (baseline or org.get("baseline") or "moderate").lower()
    if baseline not in BASELINES:
        raise ValueError(f"Baseline must be one of {BASELINES}, got '{baseline}'")

    catalog = catalog or load_catalog()
    rules = rules if rules is not None else load_rules(catalog=catalog)
    merged = dict((config.get("parameters") or {}) if isinstance(config, dict) else {})
    merged.update(parameters or {})
    rules, params_used = apply_parameters(rules, merged)
    scoped_controls = catalog.for_baseline(baseline)

    rule_results: list[RuleResult] = []
    for rule in rules:
        if not _rule_in_scope(rule, scoped_controls):
            continue
        outcome = evaluate(config, rule.check)
        rule_results.append(RuleResult(
            rule_id=rule.id,
            title=rule.title,
            controls=[c for c in rule.controls if c in scoped_controls],
            severity=rule.severity,
            status=outcome.status,
            detail=outcome.detail,
            failing_items=outcome.failing_items,
            remediation=rule.remediation,
            observed=outcome.observed,
            partial=outcome.partial,
        ))

    # Roll rule outcomes up to controls
    per_control: dict[str, list[RuleResult]] = defaultdict(list)
    for rr in rule_results:
        for cid in rr.controls:
            per_control[cid].append(rr)

    control_results: list[ControlResult] = []
    for cid, ctrl in scoped_controls.items():
        linked = per_control.get(cid, [])
        statuses = [r.status for r in linked]
        control_results.append(ControlResult(
            control_id=cid,
            title=ctrl.title,
            family=ctrl.family,
            family_name=ctrl.family_name,
            status=_control_status(linked),
            rules=[r.rule_id for r in linked],
            passed=statuses.count(PASS),
            failed=statuses.count(FAIL),
        ))

    # Scores
    assessed = [r for r in rule_results if r.status in (PASS, FAIL)]
    passed = [r for r in assessed if r.status == PASS]
    compliance = round(100 * len(passed) / len(assessed), 1) if assessed else None

    total_weight = sum(SEVERITY_WEIGHTS[r.severity] for r in assessed)
    failed_weight = sum(SEVERITY_WEIGHTS[r.severity] for r in assessed if r.status == FAIL)
    risk_score = round(100 * failed_weight / total_weight, 1) if total_weight else 0.0

    # Per-family summary (a rule counts toward each family its in-scope controls belong to)
    fam_rules: dict[str, dict[str, RuleResult]] = defaultdict(dict)
    for rr in assessed:
        for cid in rr.controls:
            fam_rules[scoped_controls[cid].family][rr.rule_id] = rr
    families: list[FamilySummary] = []
    for fam in sorted({c.family for c in scoped_controls.values()}):
        rr_list = list(fam_rules.get(fam, {}).values())
        n_pass = sum(1 for r in rr_list if r.status == PASS)
        families.append(FamilySummary(
            family=fam,
            family_name=next(c.family_name for c in scoped_controls.values() if c.family == fam),
            rules_assessed=len(rr_list),
            rules_passed=n_pass,
            compliance_pct=round(100 * n_pass / len(rr_list), 1) if rr_list else None,
        ))

    def _count(items, attr, values):
        return {v: sum(1 for i in items if getattr(i, attr) == v) for v in values}

    return AssessmentResult(
        organization=org.get("name", "Unnamed organization"),
        sector=org.get("sector", "Not specified"),
        baseline=baseline,
        catalog=catalog.name,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        tool_version=__version__,
        compliance_pct=compliance,
        risk_score=risk_score,
        risk_rating=risk_rating(risk_score) if assessed else "Not rated",
        failed_weight=failed_weight,
        total_weight=total_weight,
        rule_counts=_count(rule_results, "status", [PASS, FAIL, NOT_ASSESSED, NOT_APPLICABLE]),
        control_counts=_count(control_results, "status",
                              [IMPLEMENTED, PARTIAL, NOT_IMPLEMENTED, CONTROL_NOT_ASSESSED, CONTROL_NOT_APPLICABLE]),
        rules=rule_results,
        controls=control_results,
        families=families,
        parameters=[p for p in params_used if p.rule_id in {r.rule_id for r in rule_results}],
    )
