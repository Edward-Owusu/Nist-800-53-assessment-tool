"""Run an assessment: evaluate rules, roll results up to controls, and score risk."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .catalog import BASELINES, Catalog, Rule, load_catalog, load_rules
from .checks import FAIL, NOT_APPLICABLE, NOT_ASSESSED, PASS, evaluate

SEVERITY_WEIGHTS = {"critical": 10, "high": 6, "medium": 3, "low": 1}

# Control implementation statuses
IMPLEMENTED = "Implemented"
PARTIAL = "Partially implemented"
NOT_IMPLEMENTED = "Not implemented"
CONTROL_NOT_ASSESSED = "Not assessed"
CONTROL_NOT_APPLICABLE = "Not applicable"

# Overall risk rating bands on the 0-100 weighted risk exposure score
RISK_BANDS = [(10, "Low"), (25, "Moderate"), (50, "High"), (101, "Critical")]


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
    rule_counts: dict[str, int]
    control_counts: dict[str, int]
    rules: list[RuleResult] = field(default_factory=list)
    controls: list[ControlResult] = field(default_factory=list)
    families: list[FamilySummary] = field(default_factory=list)

    @property
    def findings(self) -> list[RuleResult]:
        """Failed rules ordered by remediation priority (severity, then id)."""
        order = {s: i for i, s in enumerate(SEVERITY_WEIGHTS)}
        failed = [r for r in self.rules if r.status == FAIL]
        return sorted(failed, key=lambda r: (order[r.severity], r.rule_id))

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["findings"] = [asdict(f) for f in self.findings]
        return data


def risk_rating(score: float) -> str:
    for upper, label in RISK_BANDS:
        if score < upper:
            return label
    return "Critical"


def _rule_in_scope(rule: Rule, scoped: dict) -> bool:
    return any(c in scoped for c in rule.controls)


def _control_status(statuses: list[str]) -> str:
    assessed = [s for s in statuses if s in (PASS, FAIL)]
    if not assessed:
        if statuses and all(s == NOT_APPLICABLE for s in statuses):
            return CONTROL_NOT_APPLICABLE
        return CONTROL_NOT_ASSESSED
    if all(s == PASS for s in assessed):
        return IMPLEMENTED
    if all(s == FAIL for s in assessed):
        return NOT_IMPLEMENTED
    return PARTIAL


def assess(
    config: dict,
    baseline: str | None = None,
    catalog: Catalog | None = None,
    rules: list[Rule] | None = None,
) -> AssessmentResult:
    """Assess a system configuration against the selected NIST SP 800-53 baseline."""
    from . import __version__

    org = config.get("organization", {}) if isinstance(config, dict) else {}
    baseline = (baseline or org.get("baseline") or "moderate").lower()
    if baseline not in BASELINES:
        raise ValueError(f"Baseline must be one of {BASELINES}, got '{baseline}'")

    catalog = catalog or load_catalog()
    rules = rules if rules is not None else load_rules(catalog=catalog)
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
            status=_control_status(statuses),
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
        rule_counts=_count(rule_results, "status", [PASS, FAIL, NOT_ASSESSED, NOT_APPLICABLE]),
        control_counts=_count(control_results, "status",
                              [IMPLEMENTED, PARTIAL, NOT_IMPLEMENTED, CONTROL_NOT_ASSESSED, CONTROL_NOT_APPLICABLE]),
        rules=rule_results,
        controls=control_results,
        families=families,
    )
