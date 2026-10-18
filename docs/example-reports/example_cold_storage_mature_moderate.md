# NIST SP 800-53 assessment: Northfield Cold Logistics (fictional)

Baseline: **Moderate** | Sector: Food and agriculture, refrigerated warehousing | Generated: 2026-10-17 23:28 UTC

- Compliance (automated checks passed): **96.6%**
- Weighted risk exposure (higher is worse): **2.0 / 100 (Low)**
- Checks: 28 passed, 1 failed, 0 not assessed, 0 not applicable

## How the risk score is calculated

Each assessed check carries a weight based on its severity (critical 10, high 6, medium 3, low 1). The failed checks carry 3 of the 152 total weight points, so risk exposure = 100 x 3 / 152 = 2.0. A score of 0 to below 10 is rated Low. This differs from the share of checks passed, which counts every check equally: failing a few critical checks raises risk exposure far more than failing many low-severity ones.

| Severity | Weight | Checks assessed | Checks failed | Failed weight | Total weight |
|---|---|---|---|---|---|
| Critical | 10 | 4 | 0 | 0 | 40 |
| High | 6 | 13 | 0 | 0 | 78 |
| Medium | 3 | 11 | 1 | 3 | 33 |
| Low | 1 | 1 | 0 | 0 | 1 |
| **Total** | | | | **3** | **152** |

Rating bands: below 10 Low, 10 to below 25 Moderate, 25 to below 50 High, 50 or more Critical.

## Organization-defined parameters used

| Check | Parameter | Value used | Default |
|---|---|---|---|
| IAM-03 | Days of inactivity before an account must be disabled | 90 days | 90 days |
| IAM-05 | Maximum share of enabled accounts that may be privileged | 10% | 10% |
| IAM-06 | Maximum failed sign-in attempts before lockout | 5 | 5 |
| IAM-07 | Minimum password length | 12 characters | 12 characters |
| IAM-08 | Maximum minutes of inactivity before the device locks | 15 minutes | 15 minutes |
| LOG-02 | Minimum audit log retention | 90 days | 90 days |
| LOG-03 | Maximum days between audit log reviews | 7 days | 7 days |
| VUL-01 | Maximum days between vulnerability scans | 30 days | 30 days |
| VUL-02 | Maximum days to apply critical patches | 15 days | 15 days |
| BCP-01 | Maximum hours between backups | 24 hours | 24 hours |
| BCP-03 | Maximum days since the last backup restore test | 180 days | 180 days |
| IR-02 | Maximum days since the incident response plan was reviewed | 365 days | 365 days |
| TRN-01 | Minimum security awareness training completion | 95% | 95% |

## Findings by priority

### [MEDIUM] TRN-01: Security awareness training completion of 95% or more (ODP)
Controls: AT-2  
Observation: governance.training_completion_rate is 0.91; expected at least 0.95.  
Remediation: Require annual security awareness training, including phishing, and follow up with non-completers.

## Control status

| Control | Title | Status |
|---|---|---|
| AC-2 | Account Management | Implemented |
| AC-2(3) | Account Management | Disable Accounts | Implemented |
| AC-3 | Access Enforcement | Not assessed |
| AC-6 | Least Privilege | Implemented |
| AC-7 | Unsuccessful Logon Attempts | Implemented |
| AC-11 | Device Lock | Implemented |
| AC-17 | Remote Access | Implemented |
| AT-2 | Literacy Training and Awareness | Partially implemented |
| AU-2 | Event Logging | Implemented |
| AU-6 | Audit Record Review, Analysis, and Reporting | Implemented |
| AU-11 | Audit Record Retention | Implemented |
| CM-2 | Baseline Configuration | Implemented |
| CM-6 | Configuration Settings | Implemented |
| CM-7 | Least Functionality | Implemented |
| CP-9 | System Backup | Implemented |
| CP-9(1) | System Backup | Testing for Reliability and Integrity | Implemented |
| CP-10 | System Recovery and Reconstitution | Implemented |
| IA-2 | Identification and Authentication (Organizational Users) | Implemented |
| IA-2(1) | Identification and Authentication | Multi-factor Authentication to Privileged Accounts | Implemented |
| IA-2(2) | Identification and Authentication | Multi-factor Authentication to Non-privileged Accounts | Implemented |
| IA-5 | Authenticator Management | Implemented |
| IR-4 | Incident Handling | Implemented |
| IR-8 | Incident Response Plan | Implemented |
| RA-5 | Vulnerability Monitoring and Scanning | Implemented |
| SA-22 | Unsupported System Components | Implemented |
| SC-7 | Boundary Protection | Implemented |
| SC-8 | Transmission Confidentiality and Integrity | Implemented |
| SC-13 | Cryptographic Protection | Implemented |
| SC-28 | Protection of Information at Rest | Implemented |
| SI-2 | Flaw Remediation | Implemented |
| SI-3 | Malicious Code Protection | Implemented |
| SI-4 | System Monitoring | Implemented |

## Compliance by control family

Families scored on fewer than 3 checks are marked as limited coverage, because one or two checks cannot show that a whole family is in place.

| Family | Checks passed | Compliance | Coverage |
|---|---|---|---|
| AC Access Control | 7 of 7 | 100.0% | Adequate |
| AT Awareness and Training | 0 of 1 | 0.0% | Limited: only 1 check |
| AU Audit and Accountability | 4 of 4 | 100.0% | Adequate |
| CM Configuration Management | 3 of 3 | 100.0% | Adequate |
| CP Contingency Planning | 3 of 3 | 100.0% | Adequate |
| IA Identification and Authentication | 5 of 5 | 100.0% | Adequate |
| IR Incident Response | 2 of 2 | 100.0% | Limited: only 2 checks |
| RA Risk Assessment | 1 of 1 | 100.0% | Limited: only 1 check |
| SA System and Services Acquisition | 1 of 1 | 100.0% | Limited: only 1 check |
| SC System and Communications Protection | 4 of 4 | 100.0% | Adequate |
| SI System and Information Integrity | 3 of 3 | 100.0% | Adequate |

_This report is generated by an automated assessment aid. It does not replace a formal assessment, authorization decision, or the judgment of a qualified auditor. Controls without automated checks are reported as not assessed and require manual review._
