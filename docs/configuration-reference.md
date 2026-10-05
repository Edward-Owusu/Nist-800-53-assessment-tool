# Configuration file reference

The tool reads one JSON file describing an organization's systems. Start from `samples/config_template.json`. Any section you cannot provide can be removed; the related checks are reported as not assessed rather than passed.

## organization

| Field | Type | Description |
|---|---|---|
| `name` | text | Organization name shown on the report |
| `sector` | text | Industry or critical infrastructure sector |
| `employees` | number | Headcount (informational) |
| `baseline` | `low`, `moderate`, `high` | Default baseline if none is given on the command line |

## identity.password_policy

| Field | Type | Used by |
|---|---|---|
| `min_length` | number | IAM-07 (IA-5) |
| `lockout_threshold` | number, 0 means no lockout | IAM-06 (AC-7) |
| `session_lock_minutes` | number | IAM-08 (AC-11) |

## identity.accounts (list)

One entry per user account, for example exported from Active Directory or Microsoft Entra ID.

| Field | Type | Used by |
|---|---|---|
| `username` | text | Identifies the account in findings |
| `enabled` | true/false | Scope for all account checks |
| `privileged` | true/false | IAM-01, IAM-02, IAM-05 |
| `mfa_enabled` | true/false | IAM-01 (IA-2(1)), IAM-02 (IA-2(2)) |
| `days_since_last_login` | number | IAM-03 (AC-2(3)) |
| `shared` | true/false | IAM-04 (AC-2, IA-2) |

## assets (list)

One entry per server, workstation, or operational technology device.

| Field | Type | Used by |
|---|---|---|
| `hostname` | text | Identifies the asset in findings |
| `type` | `server`, `workstation`, `ot_device`, ... | MAL-01 applies to servers and workstations |
| `os` | text | Informational |
| `os_supported` | true/false | VUL-03 (SA-22) |
| `logging_enabled` | true/false | LOG-01 (AU-2) |
| `av_enabled` | true/false | MAL-01 (SI-3) |
| `disk_encryption` | true/false | CRY-02 (SC-28) |
| `stores_sensitive_data` | true/false | Scope for CRY-02 |
| `max_critical_patch_age_days` | number | VUL-02 (SI-2) |
| `public_ports` | list of numbers | NET-01 (SC-7, AC-17) |
| `unnecessary_services` | list of text | CFG-02 (CM-7) |

## Organization-level settings

| Path | Type | Used by |
|---|---|---|
| `logging.retention_days` | number | LOG-02 (AU-11) |
| `logging.review_frequency_days` | number | LOG-03 (AU-6) |
| `logging.centralized_siem` | true/false | MON-01 (SI-4) |
| `vulnerability_management.scan_frequency_days` | number | VUL-01 (RA-5) |
| `network.firewall_default_deny` | true/false | NET-02 (SC-7) |
| `network.min_tls_version` | text, e.g. `"1.2"` | CRY-01 (SC-8) |
| `remote_access.vpn_mfa` | true/false | REM-01 (AC-17) |
| `backup.frequency_hours` | number | BCP-01 (CP-9) |
| `backup.offline_or_immutable_copy` | true/false | BCP-02 (CP-9, CP-10) |
| `backup.last_restore_test_days_ago` | number | BCP-03 (CP-9(1)) |
| `incident_response.plan_exists` | true/false | IR-01 (IR-8) |
| `incident_response.plan_last_reviewed_days_ago` | number | IR-02 (IR-8) |
| `governance.training_completion_rate` | number from 0 to 1 | TRN-01 (AT-2) |
| `governance.baseline_config_documented` | true/false | CFG-01 (CM-2) |
