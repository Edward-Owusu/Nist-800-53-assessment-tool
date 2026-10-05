# NIST SP 800-53 assessment: Riverbend Components (fictional)

Baseline: **Moderate** | Sector: Manufacturing, automotive parts supplier | Generated: 2026-10-04 23:22 UTC

- Compliance (automated checks passed): **21.4%**
- Weighted risk exposure: **81.2 / 100 (Critical)**
- Checks: 6 passed, 22 failed, 1 not assessed, 0 not applicable

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

### [HIGH] IAM-03: Inactive accounts are disabled (90-day ODP)
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

### [HIGH] VUL-01: Vulnerability scans run at least every 30 days
Controls: RA-5  
Observation: vulnerability_management.scan_frequency_days is 90; expected at most 30.  
Remediation: Schedule authenticated vulnerability scans of all systems at least monthly.

### [HIGH] VUL-03: No unsupported operating systems in use
Controls: SA-22, CM-2  
Observation: 2 of 6 items fail: os_supported must be equal to true.  
Affected: ERP01, WS-SHOP2  
Remediation: Upgrade or replace systems running end-of-life software; isolate any that cannot be replaced yet.

### [MEDIUM] BCP-03: Backup restore tested within the last 180 days
Controls: CP-9(1), CP-10  
Observation: backup.last_restore_test_days_ago is 400; expected at most 180.  
Remediation: Perform and document a test restore of critical systems at least twice a year.

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

### [MEDIUM] IAM-06: Account lockout after 1 to 5 failed attempts
Controls: AC-7  
Observation: identity.password_policy.lockout_threshold is 10; expected between 1 and 5.  
Remediation: Set the account lockout threshold to 5 or fewer consecutive failed sign-in attempts.

### [MEDIUM] IAM-07: Minimum password length of 12 characters (ODP)
Controls: IA-5  
Observation: identity.password_policy.min_length is 8; expected at least 12.  
Remediation: Raise the minimum password length to at least 12 characters and allow passphrases.

### [MEDIUM] IR-02: Incident response plan reviewed within the last year
Controls: IR-8  
Observation: incident_response.plan_last_reviewed_days_ago is 540; expected at most 365.  
Remediation: Review and update the incident response plan annually and after any significant incident.

### [MEDIUM] TRN-01: Security awareness training completion of 95% or more
Controls: AT-2  
Observation: governance.training_completion_rate is 0.72; expected at least 0.95.  
Remediation: Require annual security awareness training, including phishing, and follow up with non-completers.

## Control status

| Control | Title | Status |
|---|---|---|
| AC-2 | Account Management | Not implemented |
| AC-2(3) | Account Management | Disable Accounts | Not implemented |
| AC-3 | Access Enforcement | Not assessed |
| AC-6 | Least Privilege | Not implemented |
| AC-7 | Unsuccessful Logon Attempts | Not implemented |
| AC-11 | Device Lock | Implemented |
| AC-17 | Remote Access | Not implemented |
| AT-2 | Literacy Training and Awareness | Not implemented |
| AU-2 | Event Logging | Not implemented |
| AU-6 | Audit Record Review, Analysis, and Reporting | Not implemented |
| AU-11 | Audit Record Retention | Implemented |
| CM-2 | Baseline Configuration | Not implemented |
| CM-6 | Configuration Settings | Not implemented |
| CM-7 | Least Functionality | Not implemented |
| CP-9 | System Backup | Partially implemented |
| CP-9(1) | System Backup | Testing for Reliability and Integrity | Not implemented |
| CP-10 | System Recovery and Reconstitution | Not implemented |
| IA-2 | Identification and Authentication (Organizational Users) | Not implemented |
| IA-2(1) | Identification and Authentication | Multi-factor Authentication to Privileged Accounts | Not implemented |
| IA-2(2) | Identification and Authentication | Multi-factor Authentication to Non-privileged Accounts | Not implemented |
| IA-5 | Authenticator Management | Not implemented |
| IR-4 | Incident Handling | Implemented |
| IR-8 | Incident Response Plan | Partially implemented |
| RA-5 | Vulnerability Monitoring and Scanning | Not implemented |
| SA-22 | Unsupported System Components | Not implemented |
| SC-7 | Boundary Protection | Partially implemented |
| SC-8 | Transmission Confidentiality and Integrity | Implemented |
| SC-13 | Cryptographic Protection | Partially implemented |
| SC-28 | Protection of Information at Rest | Not implemented |
| SI-2 | Flaw Remediation | Not implemented |
| SI-3 | Malicious Code Protection | Not implemented |
| SI-4 | System Monitoring | Not implemented |

## Compliance by control family

| Family | Checks assessed | Compliance |
|---|---|---|
| AC Access Control | 7 | 14.3% |
| AT Awareness and Training | 1 | 0.0% |
| AU Audit and Accountability | 3 | 33.3% |
| CM Configuration Management | 3 | 0.0% |
| CP Contingency Planning | 3 | 33.3% |
| IA Identification and Authentication | 5 | 0.0% |
| IR Incident Response | 2 | 50.0% |
| RA Risk Assessment | 1 | 0.0% |
| SA System and Services Acquisition | 1 | 0.0% |
| SC System and Communications Protection | 4 | 50.0% |
| SI System and Information Integrity | 3 | 0.0% |

_This report is generated by an automated assessment aid. It does not replace a formal assessment, authorization decision, or the judgment of a qualified auditor. Controls without automated checks are reported as not assessed and require manual review._
