# Assessment methodology

This document explains how `grc_assess` turns a configuration file into control statuses and risk scores, so that results can be reviewed, challenged, and reproduced by an auditor.

## 1. Scope: baselines

Controls are drawn from NIST SP 800-53 Rev. 5. Each control in the catalog lists the baselines it belongs to, following NIST SP 800-53B. When you choose a baseline (low, moderate, or high), only controls in that baseline are in scope, and only checks mapped to at least one in-scope control are run.

The catalog is a subset of the full control set, focused on controls that can be evidenced from common system data. Controls in scope without an automated check are reported as **Not assessed** and listed as needing manual review. The tool never reports a control as implemented without evidence.

## 2. Checks

Each check in `src/grc_assess/data/rules.json` has an ID, a title, one or more mapped controls, a severity, a check definition, and remediation guidance. There are three check types.

| Type | What it tests | Example |
|---|---|---|
| `value` | One setting against an expected value | `logging.retention_days` at least 90 |
| `each` | Every item in a collection, optionally filtered | every enabled privileged account has MFA |
| `ratio` | The share of items matching a filter | privileged accounts are at most 10% of enabled accounts |

Operators: `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `between`, `in`, `not_in`, `contains_none`, `is_empty`.

Thresholds marked **ODP** are organization-defined parameters. NIST SP 800-53 leaves many values (such as the inactivity period before accounts are disabled) for each organization to set. The defaults reflect common practice and can be changed by editing the rules file or supplying a custom one with `--rules`.

## 3. Check outcomes and missing evidence

| Outcome | Meaning |
|---|---|
| Pass | The evidence meets the expectation. |
| Fail | The evidence does not meet the expectation. |
| Not assessed | The setting or collection was not provided, so no conclusion is drawn. |
| Not applicable | The collection exists but contains no items in scope (for example, no systems store sensitive data). |

Missing evidence is treated the way an auditor would treat it. If a whole setting is missing, the check is not assessed rather than passed. If an individual item in a collection does not report a required field (for example, a server with no `logging_enabled` value), that item counts as a failure marked "not evidenced", because the organization has asserted the item exists but not that it is protected. A value with the wrong data type (such as `"yes"` instead of `true`) also fails.

For `each` checks, one failing item fails the whole check. This mirrors audit practice: a control is not effective if it is missing on some in-scope systems. The report lists the affected items and the share that comply.

## 4. Control status

A control's status is rolled up from all checks mapped to it:

| Status | Rule |
|---|---|
| Implemented | All assessed checks pass. |
| Partially implemented | Some assessed checks pass and some fail. |
| Not implemented | All assessed checks fail. |
| Not assessed | No mapped check could be assessed, or no check exists (manual review). |
| Not applicable | All mapped checks were not applicable. |

## 5. Scores

**Compliance** is the percentage of assessed checks that pass. It ignores checks that were not assessed or not applicable.

**Weighted risk exposure** (0 to 100) weights each assessed check by severity and reports the share of total weight that fails:

```
risk exposure = 100 x (sum of weights of failed checks) / (sum of weights of all assessed checks)
```

| Severity | Weight | Typical meaning |
|---|---|---|
| Critical | 10 | Directly enables common attacks such as ransomware or account takeover |
| High | 6 | Significant gap in prevention, detection, or recovery |
| Medium | 3 | Weakens the control environment; exploitable with other gaps |
| Low | 1 | Hygiene issue with limited direct impact |

The overall rating uses these bands: below 10 is Low, 10 to below 25 is Moderate, 25 to below 50 is High, and 50 or more is Critical.

Severities reflect the author's professional judgment about how directly each gap enables common attacks on small and mid-sized organizations, informed by CISA guidance on ransomware and baseline security practices. They are a prioritization aid, not a quantitative risk model. Organizations should adjust them to their own risk appetite.

## 6. Limitations

- Results depend entirely on the accuracy of the configuration data supplied.
- The tool assesses a subset of NIST SP 800-53 controls and only the aspects that can be evidenced from configuration data. Policy, procedure, and organizational aspects of controls still require manual review.
- Baseline membership in the catalog should be verified against the official NIST SP 800-53B publication before use in a formal assessment.
- The tool supports, and does not replace, a formal assessment or authorization decision.
