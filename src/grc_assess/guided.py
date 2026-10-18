"""Build a configuration from plain answers, for people who don't write JSON.

The dashboard's fill-in form collects answers as simple values (numbers, Yes/No/
Don't know, and two editable tables). ``build_config`` turns them into the same
configuration structure the JSON upload uses. Anything left blank or answered
"Don't know" is left out, so the related checks are reported as not assessed
instead of being guessed.
"""

from __future__ import annotations

from typing import Any, Iterable

YES, NO, UNKNOWN = "Yes", "No", "Don't know"
YES_NO_UNKNOWN = (UNKNOWN, YES, NO)

ACCOUNT_FIELDS = ("username", "enabled", "privileged", "mfa_enabled", "days_since_last_login", "shared")
ASSET_FIELDS = ("hostname", "type", "os_supported", "logging_enabled", "av_enabled", "disk_encryption",
                "stores_sensitive_data", "max_critical_patch_age_days", "public_ports", "unnecessary_services")
ASSET_TYPES = ("server", "workstation", "ot_device", "other")

# Simple questions: (section, key, kind). Kinds: "number", "percent", "yesno", "choice".
QUESTIONS = [
    ("identity.password_policy", "min_length", "number"),
    ("identity.password_policy", "lockout_threshold", "number"),
    ("identity.password_policy", "session_lock_minutes", "number"),
    ("logging", "retention_days", "number"),
    ("logging", "review_frequency_days", "number"),
    ("logging", "centralized_siem", "yesno"),
    ("vulnerability_management", "scan_frequency_days", "number"),
    ("network", "firewall_default_deny", "yesno"),
    ("network", "min_tls_version", "choice"),
    ("remote_access", "vpn_mfa", "yesno"),
    ("backup", "frequency_hours", "number"),
    ("backup", "offline_or_immutable_copy", "yesno"),
    ("backup", "last_restore_test_days_ago", "number"),
    ("incident_response", "plan_exists", "yesno"),
    ("incident_response", "plan_last_reviewed_days_ago", "number"),
    ("governance", "training_completion_rate", "percent"),
    ("governance", "baseline_config_documented", "yesno"),
]


def _blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and value != value:  # NaN from an empty table cell
        return True
    return isinstance(value, str) and value.strip() in ("", UNKNOWN)


def _to_number(value: Any) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number


def _split_list(value: Any, numeric: bool = False) -> list:
    """'22, 3389' -> [22, 3389]. Empty text means an empty list (nothing exposed)."""
    if isinstance(value, (list, tuple)):
        items = list(value)
    else:
        items = [p.strip() for p in str(value or "").replace(";", ",").split(",") if p.strip()]
    if numeric:
        out = []
        for item in items:
            try:
                out.append(int(item))
            except (TypeError, ValueError):
                raise ValueError(f"'{item}' is not a port number. List ports as numbers, for example 22, 3389.")
        return out
    return [str(i) for i in items]


def _set(config: dict, section: str, key: str, value: Any) -> None:
    node = config
    for part in section.split("."):
        node = node.setdefault(part, {})
    node[key] = value


def _rows(rows: Iterable[dict] | None, required: str) -> list[dict]:
    """Keep rows that have the identifying field filled in; drop blank cells."""
    out = []
    for row in rows or []:
        if _blank(row.get(required)):
            continue
        out.append({k: v for k, v in row.items() if not _blank(v)})
    return out


def build_config(
    organization: dict | None,
    answers: dict[str, Any],
    accounts: Iterable[dict] | None = None,
    assets: Iterable[dict] | None = None,
) -> dict:
    """Return a configuration dict from form answers.

    ``answers`` is keyed by "section.key", for example ``"backup.frequency_hours"``.
    """
    config: dict[str, Any] = {"organization": {k: v for k, v in (organization or {}).items() if not _blank(v)}}

    for section, key, kind in QUESTIONS:
        value = answers.get(f"{section}.{key}")
        if _blank(value):
            continue
        if kind == "yesno":
            if value not in (YES, NO):
                raise ValueError(f"Answer for {section}.{key} must be Yes, No, or Don't know.")
            value = value == YES
        elif kind == "number":
            value = _to_number(value)
        elif kind == "percent":
            value = round(float(value) / 100, 4)
        _set(config, section, key, value)

    account_rows = []
    for row in _rows(accounts, "username"):
        item = {k: row[k] for k in ACCOUNT_FIELDS if k in row}
        if "days_since_last_login" in item:
            item["days_since_last_login"] = _to_number(item["days_since_last_login"])
        for flag in ("enabled", "privileged", "mfa_enabled", "shared"):
            if flag in item:
                item[flag] = bool(item[flag])
        account_rows.append(item)
    if account_rows:
        _set(config, "identity", "accounts", account_rows)

    asset_rows = []
    for row in _rows(assets, "hostname"):
        item = {k: row[k] for k in ASSET_FIELDS if k in row}
        for flag in ("os_supported", "logging_enabled", "av_enabled", "disk_encryption", "stores_sensitive_data"):
            if flag in item:
                item[flag] = bool(item[flag])
        if "max_critical_patch_age_days" in item:
            item["max_critical_patch_age_days"] = _to_number(item["max_critical_patch_age_days"])
        item["public_ports"] = _split_list(row.get("public_ports"), numeric=True)
        item["unnecessary_services"] = _split_list(row.get("unnecessary_services"))
        asset_rows.append(item)
    if asset_rows:
        config["assets"] = asset_rows

    return config
