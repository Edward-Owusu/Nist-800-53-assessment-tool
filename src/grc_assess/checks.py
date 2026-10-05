"""Evaluate a single rule's check against a system configuration.

Three check types are supported:

* ``value``  - compare one setting, e.g. ``logging.retention_days >= 90``.
* ``each``   - every item in a collection must satisfy a condition,
               e.g. every privileged account has MFA. Failing items are listed.
* ``ratio``  - the share of items matching a filter must satisfy a condition,
               e.g. privileged accounts <= 10% of enabled accounts.

Missing evidence is handled conservatively, the way an auditor would:
a missing top-level setting or collection makes the rule NOT_ASSESSED,
while an item inside a collection that does not report the required
field counts as a failure ("not evidenced").
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

PASS = "PASS"
FAIL = "FAIL"
NOT_ASSESSED = "NOT_ASSESSED"
NOT_APPLICABLE = "NOT_APPLICABLE"

_MISSING = object()


@dataclass
class CheckOutcome:
    status: str
    detail: str
    failing_items: list[str] = field(default_factory=list)
    observed: Any = None


def get_path(data: Any, path: str) -> Any:
    """Return the value at a dotted path, or the _MISSING sentinel."""
    current = data
    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return _MISSING
    return current


def _between(actual: Any, bounds: Any) -> bool:
    low, high = bounds
    return low <= actual <= high


def _contains_none(actual: Any, forbidden: Any) -> bool:
    return not set(actual or []) & set(forbidden)


OPERATORS: dict[str, Callable[[Any, Any], bool]] = {
    "eq": lambda a, b: a == b,
    "ne": lambda a, b: a != b,
    "gt": lambda a, b: a > b,
    "gte": lambda a, b: a >= b,
    "lt": lambda a, b: a < b,
    "lte": lambda a, b: a <= b,
    "between": _between,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
    "contains_none": _contains_none,
    "is_empty": lambda a, _b: not a,
}

_OP_TEXT = {
    "eq": "equal to", "ne": "not equal to", "gt": "greater than", "gte": "at least",
    "lt": "less than", "lte": "at most", "between": "between", "in": "one of",
    "not_in": "not one of", "contains_none": "free of", "is_empty": "empty",
}


def apply_op(op: str, actual: Any, expected: Any) -> bool:
    if op not in OPERATORS:
        raise ValueError(f"Unknown operator '{op}'")
    try:
        return bool(OPERATORS[op](actual, expected))
    except TypeError:
        # Wrong data type in the configuration (e.g. "yes" instead of true) fails the check.
        return False


def _matches(item: dict, where: dict | None) -> bool:
    if not where:
        return True
    for key, wanted in where.items():
        value = item.get(key, _MISSING)
        if isinstance(wanted, list):
            if value not in wanted:
                return False
        elif value != wanted:
            return False
    return True


def _fmt(value: Any) -> str:
    """Show values the way they appear in the JSON configuration (true, not True)."""
    try:
        return json.dumps(value)
    except (TypeError, ValueError):
        return str(value)


def _expectation(op: str, value: Any) -> str:
    if op == "is_empty":
        return "empty"
    if op == "between":
        return f"between {value[0]} and {value[1]}"
    return f"{_OP_TEXT.get(op, op)} {_fmt(value)}"


def _check_value(config: dict, check: dict) -> CheckOutcome:
    actual = get_path(config, check["path"])
    if actual is _MISSING:
        return CheckOutcome(NOT_ASSESSED, f"No data provided for '{check['path']}'.")
    ok = apply_op(check["op"], actual, check.get("value"))
    expect = _expectation(check["op"], check.get("value"))
    detail = f"{check['path']} is {_fmt(actual)}; expected {expect}."
    return CheckOutcome(PASS if ok else FAIL, detail, observed=actual)


def _check_each(config: dict, check: dict) -> CheckOutcome:
    collection = get_path(config, check["collection"])
    if collection is _MISSING or not isinstance(collection, list):
        return CheckOutcome(NOT_ASSESSED, f"No data provided for '{check['collection']}'.")
    in_scope = [i for i in collection if isinstance(i, dict) and _matches(i, check.get("where"))]
    if not in_scope:
        return CheckOutcome(NOT_APPLICABLE, "No items in scope for this check.")
    label_key = check.get("item_label", "id")
    fld = check["field"]
    failing: list[str] = []
    for idx, item in enumerate(in_scope):
        actual = item.get(fld, _MISSING)
        label = str(item.get(label_key, f"item #{idx + 1}"))
        if actual is _MISSING:
            failing.append(f"{label} (not evidenced)")
        elif not apply_op(check["op"], actual, check.get("value")):
            failing.append(label)
    expect = _expectation(check["op"], check.get("value"))
    if failing:
        detail = f"{len(failing)} of {len(in_scope)} items fail: {fld} must be {expect}."
        return CheckOutcome(FAIL, detail, failing, observed=f"{len(in_scope) - len(failing)}/{len(in_scope)} compliant")
    return CheckOutcome(PASS, f"All {len(in_scope)} items have {fld} {expect}.",
                        observed=f"{len(in_scope)}/{len(in_scope)} compliant")


def _check_ratio(config: dict, check: dict) -> CheckOutcome:
    collection = get_path(config, check["collection"])
    if collection is _MISSING or not isinstance(collection, list):
        return CheckOutcome(NOT_ASSESSED, f"No data provided for '{check['collection']}'.")
    base = [i for i in collection if isinstance(i, dict) and _matches(i, check.get("base_where"))]
    if not base:
        return CheckOutcome(NOT_APPLICABLE, "No items in scope for this check.")
    hits = [i for i in base if _matches(i, check.get("where"))]
    ratio = len(hits) / len(base)
    ok = apply_op(check["op"], ratio, check["value"])
    detail = (f"{len(hits)} of {len(base)} ({ratio:.0%}) match; "
              f"expected {_OP_TEXT.get(check['op'], check['op'])} {check['value']:.0%}.")
    return CheckOutcome(PASS if ok else FAIL, detail, observed=round(ratio, 4))


CHECK_TYPES: dict[str, Callable[[dict, dict], CheckOutcome]] = {
    "value": _check_value,
    "each": _check_each,
    "ratio": _check_ratio,
}


def evaluate(config: dict, check: dict) -> CheckOutcome:
    kind = check.get("type")
    if kind not in CHECK_TYPES:
        raise ValueError(f"Unknown check type '{kind}'")
    return CHECK_TYPES[kind](config, check)
