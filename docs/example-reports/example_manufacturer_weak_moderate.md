# NIST SP 800-53 assessment: Riverbend Components (fictional)

Baseline: **Moderate** | Sector: Manufacturing, automotive parts supplier | Generated: 2026-10-17 23:28 UTC

- Compliance (automated checks passed): **21.4%**
- Weighted risk exposure (higher is worse): **81.2 / 100 (Critical)**
- Checks: 6 passed, 22 failed, 1 not assessed, 0 not applicable

## How the risk score is calculated

Each assessed check carries a weight based on its severity (critical 10, high 6, medium 3, low 1). The failed checks carry 121 of the 149 total weight points, so risk exposure = 100 x 121 / 149 = 81.2. A score of 50 or more is rated Critical. This differs from the share of checks passed, which counts every check equally: failing a few critical checks raises risk exposure far more than failing many low-severity ones.

| Severity | Weight | Checks assessed | Checks failed | Failed weight | Total weight |
|---|---|---|---|---|---|
| Critical | 10 | 4 | 4 | 40 | 40 |
| High | 6 | 13 | 9 | 54 | 78 |
| Medium | 3 | 10 | 9 | 27 | 30 |
| Low | 1 | 1 | 0 | 0 | 1 |
| **Total** | | | | **121** | **149** |

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

### [CRITICAL] BCP-02: An offline or immutable backup copy exists
Controls: CP-9, CP-10  
Observation: backup.offline_or_immutable_copy is false; expected equal to true.  
Remediation: Keep at least one backup copy offline or immutable so ransomware cannot encrypt or delete it.

### [CRITICAL] IAM-01: MFA enforced on all privileged accounts
Controls: IA-2(1)  
Observation: 3 of 3 items fail: mfa_enabled must be equal to true.  
Affected: j.miller, it.admin, contractor.hv  
Remediation: Enroll every enabled administrative account in phishing-resistant MFA and block privileged sign-in without it.

### [CRITICAL] NET-01: No remote administration ports exposed to the internet
Controls: SC-7, AC-17  
Observation: 1 of 6 items fail: public_ports must be free of [22, 23, 3389, 5900].  
Affected: ERP01  
Remediation: Close SSH, Telnet, RDP, and VNC to the internet; require VPN with MFA for remote administration.

### [CRITICAL] VUL-02: Critical security patches applied within 15 days (ODP)
Controls: SI-2  
Observation: 2 of 6 items fail: max_critical_patch_age_days must be at most 15.  
Affected: ERP01, WS-SHOP2  
Remediation: Patch critical vulnerabilities within 15 days, prioritizing internet-facing systems and known-exploited vulnerabilities.

### [HIGH] CRY-02: Disk encryption on systems storing sensitive data
Controls: SC-28, SC-13  
Observation: 1 of 3 items fail: disk_encryption must be equal to true.  
Affected: ERP01  
Remediation: Enable full-disk encryption (for example BitLocker or FileVault) on every system that stores sensitive data.

### [HIGH] IAM-02: MFA enforced on standard user accounts
Controls: IA-2(2)  
Observation: 3 of 6 items fail: mfa_enabled must be equal to true.  
Affected: r.patel, floor.kiosk, t.brooks  
Remediation: Roll out MFA to all standard users, starting with email and remote-access applications.

### [HIGH] IAM-03: Accounts inactive for more than 90 days are disabled (ODP)
Controls: AC-2(3), AC-2  
Observation: 2 of 9 items fail: days_since_last_login must be at most 90.  
Affected: t.brooks, contractor.hv  
Remediation: Disable accounts with no sign-in for more than 90 days and add a recurring access review.

### [HIGH] LOG-01: Security event logging enabled on all systems
Controls: AU-2  
Observation: 3 of 6 items fail: logging_enabled must be equal to true.  
Affected: ERP01, WS-SHOP2, CNC-HMI-3  
Remediation: Enable security event logging (authentication, privilege use, configuration changes) on every system.

### [HIGH] MAL-01: Endpoint malware protection on workstations and servers
Controls: SI-3  
Observation: 1 of 5 items fail: av_enabled must be equal to true.  
Affected: WS-SHOP2  
Remediation: Deploy and centrally manage endpoint protection (EDR or antivirus) on every workstation and server.

### [HIGH] MON-01: Centralized security monitoring in place
Controls: SI-4, AU-6  
Observation: logging.centralized_siem is false; expected equal to true.  
Remediation: Forward logs to a central platform (SIEM or managed detection service) with alerting on suspicious activity.

### [HIGH] REM-01: Remote access requires VPN with MFA
Controls: AC-17, IA-2(2)  
Observation: remote_access.vpn_mfa is false; expected equal to true.  
Remediation: Require MFA on the VPN or remote-access gateway for every user.

### [HIGH] VUL-01: Vulnerability scans run at least every 30 days (ODP)
Controls: RA-5  
Observation: vulnerability_management.scan_frequency_days is 90; expected at most 30.  
Remediation: Schedule authenticated vulnerability scans of all systems at least every 30 days.

### [HIGH] VUL-03: No unsupported operating systems in use
Controls: SA-22, CM-2  
Observation: 2 of 6 items fail: os_supported must be equal to true.  
Affected: ERP01, WS-SHOP2  
Remediation: Upgrade or replace systems running end-of-life software; isolate any that cannot be replaced yet.

### [MEDIUM] BCP-03: Backup restore tested within the last 180 days (ODP)
Controls: CP-9(1), CP-10  
Observation: backup.last_restore_test_days_ago is 400; expected at most 180.  
Remediation: Perform and document a test restore of critical systems at least every 180 days.

### [MEDIUM] CFG-01: Baseline configurations are documented
Controls: CM-2, CM-6  
Observation: governance.baseline_config_documented is false; expected equal to true.  
Remediation: Document secure baseline configurations (for example CIS Benchmarks) for each system type.

### [MEDIUM] CFG-02: Unnecessary services are disabled
Controls: CM-7  
Observation: 2 of 6 items fail: unnecessary_services must be empty.  
Affected: ERP01, WS-SHOP2  
Remediation: Disable services that are not needed for the system's business function.

### [MEDIUM] IAM-04: No shared or generic user accounts
Controls: AC-2, IA-2  
Observation: 2 of 9 items fail: shared must be equal to false.  
Affected: it.admin, floor.kiosk  
Remediation: Replace shared accounts with individually assigned accounts so every action is attributable to one person.

### [MEDIUM] IAM-05: Privileged accounts limited to 10% of enabled accounts (ODP)
Controls: AC-6  
Observation: 3 of 9 (33%) match; expected at most 10%.  
Remediation: Review administrative group membership and remove rights that are not required for the job role.

### [MEDIUM] IAM-06: Account lockout after 1 to 5 failed attempts (ODP)
Controls: AC-7  
Observation: identity.password_policy.lockout_threshold is 10; expected between 1 and 5.  
Remediation: Set the account lockout threshold to 5 or fewer consecutive failed sign-in attempts.

### [MEDIUM] IAM-07: Minimum password length of 12 characters (ODP)
Controls: IA-5  
Observation: identity.password_policy.min_length is 8; expected at least 12.  
Remediation: Raise the minimum password length to at least 12 characters and allow passphrases.

### [MEDIUM] IR-02: Incident response plan reviewed within the last 365 days (ODP)
Controls: IR-8  
Observation: incident_response.plan_last_reviewed_days_ago is 540; expected at most 365.  
Remediation: Review and update the incident response plan annually and after any significant incident.

### [MEDIUM] TRN-01: Security awareness training completion of 95% or more (ODP)
Controls: AT-2  
Observation: governance.training_completion_rate is 0.72; expected at least 0.95.  
Remediation: Require annual security awareness training, including phishing, and follow up with non-completers.

## Control status

| Control | Title | Status |
|---|---|---|
| AC-2 | Account Management | Partially implemented |
| AC-2(3) | Account Management | Disable Accounts | Partially implemented |
| AC-3 | Access Enforcement | Not assessed |
| AC-6 | Least Privilege | Partially implemented |
| AC-7 | Unsuccessful Logon Attempts | Partially implemented |
| AC-11 | Device Lock | Implemented |
| AC-17 | Remote Access | Partially implemented |
| AT-2 | Literacy Training and Awareness | Partially implemented |
| AU-2 | Event Logging | Partially implemented |
| AU-6 | Audit Record Review, Analysis, and Reporting | Not implemented |
| AU-11 | Audit Record Retention | Implemented |
| CM-2 | Baseline Configuration | Partially implemented |
| CM-6 | Configuration Settings | Not implemented |
| CM-7 | Least Functionality | Partially implemented |
| CP-9 | System Backup | Partially implemented |
| CP-9(1) | System Backup | Testing for Reliability and Integrity | Partially implemented |
| CP-10 | System Recovery and Reconstitution | Partially implemented |
| IA-2 | Identification and Authentication (Organizational Users) | Partially implemented |
| IA-2(1) | Identification and Authentication | Multi-factor Authentication to Privileged Accounts | Not implemented |
| IA-2(2) | Identification and Authentication | Multi-factor Authentication to Non-privileged Accounts | Partially implemented |
| IA-5 | Authenticator Management | Partially implemented |
| IR-4 | Incident Handling | Implemented |
| IR-8 | Incident Response Plan | Partially implemented |
| RA-5 | Vulnerability Monitoring and Scanning | Partially implemented |
| SA-22 | Unsupported System Components | Partially implemented |
| SC-7 | Boundary Protection | Partially implemented |
| SC-8 | Transmission Confidentiality and Integrity | Implemented |
| SC-13 | Cryptographic Protection | Partially implemented |
| SC-28 | Protection of Information at Rest | Partially implemented |
| SI-2 | Flaw Remediation | Partially implemented |
| SI-3 | Malicious Code Protection | Partially implemented |
| SI-4 | System Monitoring | Not implemented |

## Compliance by control family

Families scored on fewer than 3 checks are marked as limited coverage, because one or two checks cannot show that a whole family is in place.

| Family | Checks passed | Compliance | Coverage |
|---|---|---|---|
| AC Access Control | 1 of 7 | 14.3% | Adequate |
| AT Awareness and Training | 0 of 1 | 0.0% | Limited: only 1 check |
| AU Audit and Accountability | 1 of 3 | 33.3% | Adequate |
| CM Configuration Management | 0 of 3 | 0.0% | Adequate |
| CP Contingency Planning | 1 of 3 | 33.3% | Adequate |
| IA Identification and Authentication | 0 of 5 | 0.0% | Adequate |
| IR Incident Response | 1 of 2 | 50.0% | Limited: only 2 checks |
| RA Risk Assessment | 0 of 1 | 0.0% | Limited: only 1 check |
| SA System and Services Acquisition | 0 of 1 | 0.0% | Limited: only 1 check |
| SC System and Communications Protection | 2 of 4 | 50.0% | Adequate |
| SI System and Information Integrity | 0 of 3 | 0.0% | Adequate |

_This report is generated by an automated assessment aid. It does not replace a formal assessment, authorization decision, or the judgment of a qualified auditor. Controls without automated checks are reported as not assessed and require manual review._
