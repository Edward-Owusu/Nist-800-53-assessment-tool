"""Organization-defined parameters (ODPs).

NIST SP 800-53 leaves many values for each organization to set, such as how many
days of inactivity are allowed before an account is disabled. Rules that use such
a value carry an ``odp`` entry in ``rules.json``. The number in the rule's check is
the default. An organization can supply its own value, either in the configuration
file under ``"parameters"`` or through the dashboard, and the check, title, and
remediation text are adjusted to match.

Percent parameters are entered as whole percentages (10 means 10%) and converted
to the 0-1 ratios the checks use.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from .catalog import Rule


@dataclass
class Parameter:
    rule_id: str
    label: str
    unit: str
    default: float
    value: float
    minimum: float
    maximum: float

    @property
    def customized(self) -> bool:
        return self.value != self.default

    @property
    def display(self) -> str:
        return format_value(self.value, self.unit)


def _num(value: float) -> str:
    return f"{value:g}"


def format_value(value: float, unit: str) -> str:
    if unit == "percent":
        return f"{_num(value)}%"
    if unit == "attempts":
        return _num(value)
    if unit == "characters":
        return f"{_num(value)} characters"
    singular = unit[:-1] if unit.endswith("s") else unit
    return f"{_num(value)} {singular if value == 1 else unit}"


def default_value(rule: Rule) -> float:
    """The default parameter value as shown to users (percent units as whole numbers)."""
    odp = rule.odp or {}
    raw = rule.check["value"]
    if isinstance(raw, list):
        raw = raw[1] if odp.get("bound", "upper") == "upper" else raw[0]
    if odp.get("unit") == "percent":
        return round(raw * 100, 4)
    return raw


def _validate(rule: Rule, value: Any) -> float:
    odp = rule.odp or {}
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"Parameter for {rule.id} must be a number, got {value!r}.")
    low, high = odp.get("min", 0), odp.get("max", float("inf"))
    if not low <= value <= high:
        raise ValueError(
            f"Parameter for {rule.id} ({odp.get('label', 'value')}) must be between "
            f"{_num(low)} and {_num(high)}, got {_num(value)}."
        )
    return float(value) if isinstance(value, float) and not value.is_integer() else int(value)


def apply_parameters(rules: list[Rule], overrides: dict[str, Any] | None = None) -> tuple[list[Rule], list[Parameter]]:
    """Return rules with parameter values applied, plus the parameters that were used.

    Rules without an ``odp`` entry are returned unchanged. Overrides for unknown rule
    IDs, or for rules that have no parameter, raise ValueError so typos are caught.
    """
    overrides = dict(overrides or {})
    by_id = {r.id: r for r in rules}
    for rule_id in overrides:
        if rule_id not in by_id:
            raise ValueError(f"Parameter given for unknown check '{rule_id}'.")
        if not by_id[rule_id].odp:
            raise ValueError(f"Check '{rule_id}' has no organization-defined parameter.")

    out: list[Rule] = []
    used: list[Parameter] = []
    for rule in rules:
        if not rule.odp:
            out.append(rule)
            continue
        odp = rule.odp
        default = default_value(rule)
        value = _validate(rule, overrides[rule.id]) if rule.id in overrides else default
        check = copy.deepcopy(rule.check)
        internal = value / 100 if odp.get("unit") == "percent" else value
        if isinstance(check["value"], list):
            idx = 1 if odp.get("bound", "upper") == "upper" else 0
            check["value"][idx] = internal
        else:
            check["value"] = internal
        param = Parameter(rule.id, odp.get("label", rule.id), odp.get("unit", ""), default, value,
                          odp.get("min", 0), odp.get("max", float("inf")))
        fmt = {"value": _num(value), "display": param.display}
        out.append(Rule(
            id=rule.id,
            title=rule.title.format(**fmt),
            controls=rule.controls,
            severity=rule.severity,
            check=check,
            remediation=rule.remediation.format(**fmt),
            odp=rule.odp,
        ))
        used.append(param)
    return out, used
