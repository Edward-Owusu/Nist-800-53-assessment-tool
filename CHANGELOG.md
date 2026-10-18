# Changelog

## 0.2.0 (2026-10-17)

This release responds to a detailed independent review of the dashboard. Thank you to the reviewer, whose feedback shaped every change below.

### Added
- **Score explanation.** The dashboard has a "How is the risk score calculated?" panel, and every report includes a section showing the severity weights, the failed and total weight behind the headline score, and the rating bands. The headline number can now be traced like every other result.
- **Organization-defined parameters.** Thirteen checks with ODP thresholds (for example the 90-day inactivity limit and the 10% privileged-account limit) can be set per organization in the dashboard sidebar, in a `parameters` section of the configuration file, or in code. Reports list the values used and mark any that differ from the defaults.
- **Fill-in form.** A new "Fill in a form" option in the dashboard builds the configuration from plain questions and two editable tables, so users don't need to write JSON. Answers can be saved and reloaded.
- **Family coverage flag.** Family results show the count behind each percentage (for example "2 of 2") and mark families scored on fewer than three checks as limited coverage.

### Changed
- **Partial implementation.** A control is now "Partially implemented" when the evidence shows it is in place but misses its target, for example 40% of accounts privileged against a 10% target. "Not implemented" is kept for controls with no evidence of being in place. Failed checks that are partly in place are labeled in the All checks table and CSV export.
- **Privacy note.** The dashboard now states accurately that data is processed in memory on Streamlit Community Cloud and not saved, and points to running the tool locally for sensitive data.
- The risk exposure metric is labeled "higher is worse" to avoid confusion with the share of checks passed.

## 0.1.1 (2026-10-04)
- Clearer risk label and live demo link.

## 0.1.0
- Initial release.
