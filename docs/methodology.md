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

Thresholds marked **ODP** are organization-defined parameters. NIST SP 800-53 leaves many values (such as the inactivity period before accounts are disabled) for each organization to set, so a clinic and a water utility can reasonably choose different numbers. The tool ships with defaults that reflect common practice, and each organization can set its own:

- In the dashboard, under **3. Set your own targets** in the sidebar.
- In the configuration file, in a `parameters` section keyed by check ID, for example `"parameters": {"IAM-03": 60, "IAM-05": 15}`. Percentages are whole numbers (15 means 15%).
- In code, with `assess(config, parameters={...})`.

Each value must fall within a sensible range defined in the rules file. The check, its title, and its remediation text all update to the chosen value, and every report lists the parameters used and marks any that differ from the default, so a reviewer can see exactly which targets were applied.

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
| Partially implemented | Some assessed checks pass and some fail, or every check fails but the evidence shows the control is in place and misses its target. |
| Not implemented | All assessed checks fail and there is no evidence the control is in place. |
| Not assessed | No mapped check could be assessed, or no check exists (manual review). |
| Not applicable | All mapped checks were not applicable. |

A failed check counts as **partly in place** when the evidence shows the control exists but falls short: some items in a collection comply and others don't (MFA on some accounts but not all), a ratio check misses its tolerance (40% of accounts privileged against a 10% target), or a numeric setting exists but is weaker than required (an 8-character password minimum against 12). A failure is not partial when the control is absent, such as a setting of `false`, a value of zero, or a collection where no item complies. This keeps "Not implemented" for controls with no evidence of being in place, instead of using it whenever one check fails.

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

Risk exposure and compliance answer different questions, so they can look inconsistent at first. Compliance counts every check equally. Risk exposure weights them by severity, so an organization that passes about half its checks but fails most of the critical ones will still score high (worse) on risk exposure. The dashboard's **How is the risk score calculated?** panel and every report show the per-severity breakdown behind the number, so the headline score can be traced and defended like every other result.

**Family compliance** is the share of assessed checks in a control family that pass. A family score based on fewer than three checks is marked **limited coverage**, and reports show the count behind every percentage (for example "2 of 2"). One or two passing checks show that those specific checks passed, not that the whole family is in place.

Severities reflect the author's professional judgment about how directly each gap enables common attacks on small and mid-sized organizations, informed by CISA guidance on ransomware and baseline security practices. They are a prioritization aid, not a quantitative risk model. Organizations should adjust them to their own risk appetite.

## 6. Limitations

- Results depend entirely on the accuracy of the configuration data supplied.
- The tool assesses a subset of NIST SP 800-53 controls and only the aspects that can be evidenced from configuration data. Policy, procedure, and organizational aspects of controls still require manual review.
- Baseline membership in the catalog should be verified against the official NIST SP 800-53B publication before use in a formal assessment.
- The tool supports, and does not replace, a formal assessment or authorization decision.
