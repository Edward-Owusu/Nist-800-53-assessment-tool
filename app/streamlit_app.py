"""Interactive dashboard for the NIST SP 800-53 assessment tool.

Run locally:   streamlit run app/streamlit_app.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from grc_assess import __version__, assess, load_catalog, load_rules  # noqa: E402
from grc_assess.catalog import BASELINES  # noqa: E402
from grc_assess.engine import MIN_FAMILY_CHECKS, RISK_BANDS, SEVERITY_WEIGHTS  # noqa: E402
from grc_assess.guided import ASSET_TYPES, UNKNOWN, YES_NO_UNKNOWN, build_config  # noqa: E402
from grc_assess.parameters import default_value, format_value  # noqa: E402
from grc_assess.reporting import DISCLAIMER, result_text, to_csv, to_html, to_json, to_markdown  # noqa: E402

SAMPLES = {
    "Small manufacturer with control gaps (fictional)": ROOT / "samples" / "example_manufacturer_weak.json",
    "Cold storage warehouse with mature controls (fictional)": ROOT / "samples" / "example_cold_storage_mature.json",
}
TEMPLATE = ROOT / "samples" / "config_template.json"
SEVERITY_ICON = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}
SOURCES = ["Use a sample", "Fill in a form", "Upload my own JSON"]

st.set_page_config(page_title="NIST SP 800-53 Assessment", page_icon="🛡️", layout="wide")

st.title("NIST SP 800-53 control assessment")
st.write(
    "Check a system configuration against the NIST SP 800-53 Rev. 5 low, moderate, or high baseline "
    "and get a prioritized remediation list. Built for small and mid-sized organizations without a "
    "dedicated compliance team."
)

ODP_RULES = [r for r in load_rules(catalog=load_catalog()) if r.odp]


def _yes_no(label: str, key: str, help_text: str | None = None) -> str:
    return st.selectbox(label, YES_NO_UNKNOWN, key=key, help=help_text)


def _number(label: str, key: str, help_text: str | None = None, max_value: float | None = None):
    return st.number_input(label, min_value=0, max_value=max_value, value=None, step=1, key=key,
                           placeholder="Leave blank if you don't know", help=help_text)


def guided_form() -> dict | None:
    """Fill-in form for people who don't write JSON. Returns a configuration dict once submitted."""
    st.subheader("Tell us about your organization")
    st.write(
        "Answer what you can. Anything left blank or marked \"Don't know\" is reported as not assessed, "
        "so the tool never guesses. You can save your answers as a file and load them again later."
    )
    with st.form("guided_form"):
        c1, c2 = st.columns(2)
        org_name = c1.text_input("Organization name", key="g_name")
        sector = c2.text_input("Sector", key="g_sector", placeholder="For example: health clinic, manufacturing")

        with st.expander("Passwords and sign-in", expanded=True):
            a1, a2, a3 = st.columns(3)
            with a1:
                min_length = _number("Minimum password length (characters)", "g_minlen")
            with a2:
                lockout = _number("Failed attempts before an account locks", "g_lockout",
                                  "Use 0 if accounts never lock.")
            with a3:
                lock_minutes = _number("Minutes of inactivity before screens lock", "g_lockmin")

        with st.expander("User accounts", expanded=True):
            st.caption("Add one row per account. Tick the boxes that apply. You can paste rows from a spreadsheet.")
            accounts = st.data_editor(
                pd.DataFrame([{"username": "", "enabled": True, "privileged": False, "mfa_enabled": False,
                               "days_since_last_login": None, "shared": False}]),
                num_rows="dynamic", use_container_width=True, key="g_accounts",
                column_config={
                    "username": st.column_config.TextColumn("Username", required=True),
                    "enabled": st.column_config.CheckboxColumn("Enabled", default=True),
                    "privileged": st.column_config.CheckboxColumn("Admin rights", default=False),
                    "mfa_enabled": st.column_config.CheckboxColumn("MFA on", default=False),
                    "days_since_last_login": st.column_config.NumberColumn("Days since last sign-in", min_value=0, step=1),
                    "shared": st.column_config.CheckboxColumn("Shared account", default=False),
                },
            )

        with st.expander("Computers and servers", expanded=True):
            st.caption("Add one row per system. For internet-facing ports, list numbers such as 22, 3389, "
                       "or leave blank if none.")
            assets = st.data_editor(
                pd.DataFrame([{"hostname": "", "type": "workstation", "os_supported": True,
                               "logging_enabled": False, "av_enabled": False, "disk_encryption": False,
                               "stores_sensitive_data": False, "max_critical_patch_age_days": None,
                               "public_ports": "", "unnecessary_services": ""}]),
                num_rows="dynamic", use_container_width=True, key="g_assets",
                column_config={
                    "hostname": st.column_config.TextColumn("System name", required=True),
                    "type": st.column_config.SelectboxColumn("Type", options=list(ASSET_TYPES), default="workstation"),
                    "os_supported": st.column_config.CheckboxColumn("OS still supported", default=True),
                    "logging_enabled": st.column_config.CheckboxColumn("Security logging on", default=False),
                    "av_enabled": st.column_config.CheckboxColumn("Antivirus / EDR on", default=False),
                    "disk_encryption": st.column_config.CheckboxColumn("Disk encrypted", default=False),
                    "stores_sensitive_data": st.column_config.CheckboxColumn("Holds sensitive data", default=False),
                    "max_critical_patch_age_days": st.column_config.NumberColumn(
                        "Days oldest critical patch has been waiting", min_value=0, step=1),
                    "public_ports": st.column_config.TextColumn("Ports open to the internet"),
                    "unnecessary_services": st.column_config.TextColumn("Unneeded services running"),
                },
            )

        with st.expander("Logging, scanning and network"):
            b1, b2, b3 = st.columns(3)
            with b1:
                retention = _number("Days security logs are kept", "g_ret")
                review = _number("Days between log reviews", "g_review")
                siem = _yes_no("Logs sent to a central monitoring system (SIEM)?", "g_siem")
            with b2:
                scan = _number("Days between vulnerability scans", "g_scan")
                firewall = _yes_no("Firewall blocks everything not explicitly allowed?", "g_fw")
                tls = st.selectbox("Oldest TLS version allowed", [UNKNOWN, "1.0", "1.1", "1.2", "1.3"], key="g_tls")
            with b3:
                vpn = _yes_no("Remote access requires VPN with MFA?", "g_vpn")

        with st.expander("Backups, incidents and training"):
            d1, d2, d3 = st.columns(3)
            with d1:
                backup_hours = _number("Hours between backups", "g_bkh")
                offline = _yes_no("An offline or immutable backup copy exists?", "g_off")
                restore = _number("Days since a backup restore was last tested", "g_rest")
            with d2:
                ir_plan = _yes_no("Written incident response plan exists?", "g_ir")
                ir_review = _number("Days since the plan was last reviewed", "g_irrev")
            with d3:
                training = _number("Staff who completed security training (%)", "g_train", max_value=100)
                baseline_doc = _yes_no("Secure configuration baselines are documented?", "g_cfg")

        submitted = st.form_submit_button("Run assessment", type="primary")

    if submitted:
        answers = {
            "identity.password_policy.min_length": min_length,
            "identity.password_policy.lockout_threshold": lockout,
            "identity.password_policy.session_lock_minutes": lock_minutes,
            "logging.retention_days": retention,
            "logging.review_frequency_days": review,
            "logging.centralized_siem": siem,
            "vulnerability_management.scan_frequency_days": scan,
            "network.firewall_default_deny": firewall,
            "network.min_tls_version": tls,
            "remote_access.vpn_mfa": vpn,
            "backup.frequency_hours": backup_hours,
            "backup.offline_or_immutable_copy": offline,
            "backup.last_restore_test_days_ago": restore,
            "incident_response.plan_exists": ir_plan,
            "incident_response.plan_last_reviewed_days_ago": ir_review,
            "governance.training_completion_rate": training,
            "governance.baseline_config_documented": baseline_doc,
        }
        try:
            st.session_state["form_config"] = build_config(
                {"name": org_name or "Your organization", "sector": sector or "Not specified"},
                answers, accounts.to_dict("records"), assets.to_dict("records"))
        except ValueError as exc:
            st.error(f"{exc} Fix the entry and run the assessment again.")
            st.session_state.pop("form_config", None)
    return st.session_state.get("form_config")


with st.sidebar:
    st.header("1. Choose data")
    source = st.radio("Configuration source", SOURCES, label_visibility="collapsed")
    config: dict | None = None
    if source == "Use a sample":
        choice = st.selectbox("Sample organization", list(SAMPLES))
        config = json.loads(SAMPLES[choice].read_text(encoding="utf-8"))
    elif source == "Upload my own JSON":
        upload = st.file_uploader("Configuration file (.json)", type=["json"])
        if TEMPLATE.exists():
            st.download_button("Download blank template", TEMPLATE.read_bytes(),
                               file_name="config_template.json", mime="application/json")
        if upload is not None:
            try:
                config = json.loads(upload.getvalue().decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                st.error(f"This file is not valid JSON: {exc}. Fix the file and upload it again.")
    else:
        st.caption("Fill in the form on the right, then select Run assessment.")

    st.header("2. Choose baseline")
    default_baseline = ((config or {}).get("organization", {}).get("baseline") or "moderate").lower()
    baseline = st.selectbox("Control baseline", BASELINES,
                            index=BASELINES.index(default_baseline) if default_baseline in BASELINES else 1,
                            format_func=str.title)

    st.header("3. Set your own targets")
    st.caption(
        "NIST SP 800-53 lets each organization set some values itself. These are called "
        "organization-defined parameters (ODPs). The defaults reflect common practice; change any "
        "that don't fit your organization."
    )
    file_params = (config or {}).get("parameters") or {}
    overrides: dict[str, float] = {}
    with st.expander("Organization-defined parameters"):
        for rule in ODP_RULES:
            odp = rule.odp
            default = default_value(rule)
            low, high = float(odp.get("min", 0)), float(odp.get("max", 10_000))
            start = file_params.get(rule.id, default)
            start = min(max(float(start), low), high) if isinstance(start, (int, float)) else float(default)
            value = st.number_input(
                f"{odp['label']} ({odp['unit']})", min_value=low, max_value=high, value=start, step=1.0,
                key=f"odp_{rule.id}", help=f"Check {rule.id}. Default: {format_value(default, odp['unit'])}.")
            # Every value is passed on, so the sidebar always wins over values in an uploaded file.
            overrides[rule.id] = int(value) if float(value).is_integer() else value

    st.caption(
        f"grc_assess {__version__}. Your data is processed in memory on Streamlit Community Cloud and "
        "is not saved. For sensitive data, run the tool on your own computer using the code on GitHub."
    )

if source == "Fill in a form":
    config = guided_form()
    if config is not None:
        st.download_button("Save my answers as a file", json.dumps(config, indent=2),
                           file_name="my_assessment_answers.json", mime="application/json",
                           help="Upload this file later with \"Upload my own JSON\" to pick up where you left off.")

if config is None:
    if source != "Fill in a form":
        st.info("Upload a configuration file in the sidebar, or switch to a sample, to see results.")
    st.stop()

try:
    result = assess(config, baseline=baseline, parameters=overrides)
except ValueError as exc:
    st.error(f"{exc} Correct the value and try again.")
    st.stop()
rc = result.rule_counts

st.subheader(f"{result.organization}")
st.caption(f"{result.sector}. {result.baseline.title()} baseline.")

c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Risk exposure: {result.risk_rating}", f"{result.risk_score:.0f} / 100",
          help="Higher is worse. See \"How is the risk score calculated?\" below.")
c2.metric("Automated checks passed",
          "n/a" if result.compliance_pct is None else f"{result.compliance_pct:.1f}%",
          help="Every assessed check counts equally here, whatever its severity.")
c3.metric("Failed checks", rc["FAIL"])
c4.metric("Checks lacking data", rc["NOT_ASSESSED"])

with st.expander("How is the risk score calculated?"):
    st.write(result.score_explanation)
    st.dataframe(pd.DataFrame(
        [{"Severity": s.severity.title(), "Weight": s.weight, "Checks assessed": s.assessed,
          "Checks failed": s.failed, "Failed weight": s.failed_weight, "Total weight": s.total_weight}
         for s in result.score_breakdown]
        + [{"Severity": "Total", "Weight": None, "Checks assessed": None, "Checks failed": None,
            "Failed weight": result.failed_weight, "Total weight": result.total_weight}]),
        hide_index=True)
    lows = [0] + [hi for hi, _ in RISK_BANDS[:-1]]
    st.write("Rating bands: " + ", ".join(
        f"{label} {lo} to below {hi}" if hi <= 100 else f"{label} {lo} or more"
        for lo, (hi, label) in zip(lows, RISK_BANDS)) + ".")
    st.caption(
        "Severity weights: " + ", ".join(f"{k} {v}" for k, v in SEVERITY_WEIGHTS.items())
        + ". Full method: docs/methodology.md on GitHub.")

if any(p.customized for p in result.parameters):
    st.caption("Custom targets in use: " + "; ".join(
        f"{p.rule_id} {p.display} (default {format_value(p.default, p.unit)})"
        for p in result.parameters if p.customized) + ".")

tab_findings, tab_families, tab_controls, tab_checks = st.tabs(
    ["Findings", "By control family", "Control status", "All checks"])

with tab_findings:
    if not result.findings:
        st.success("No failed checks for this baseline.")
    for f in result.findings:
        with st.expander(f"{SEVERITY_ICON[f.severity]} {f.severity.title()}: {f.rule_id} {f.title}"):
            st.markdown(f"**Controls:** {', '.join(f.controls)}")
            st.markdown(f"**Observation:** {f.detail}")
            if f.failing_items:
                st.markdown(f"**Affected:** {', '.join(f.failing_items)}")
            st.markdown(f"**Remediation:** {f.remediation}")

with tab_families:
    st.caption(
        f"A family scored on fewer than {MIN_FAMILY_CHECKS} checks is marked as limited coverage. "
        "One or two checks can't show that a whole family is in place, so treat those percentages with care.")
    fam_df = pd.DataFrame(
        [{"Family": f"{x.family} {x.family_name}", "Checks passed": x.passed_text,
          "Compliance %": x.compliance_pct, "Coverage": x.coverage_note} for x in result.families]
    )
    chart_df = fam_df.dropna(subset=["Compliance %"]).set_index("Family")[["Compliance %"]]
    if not chart_df.empty:
        st.bar_chart(chart_df, horizontal=True)
    st.dataframe(fam_df, hide_index=True)

with tab_controls:
    st.caption(
        "Partially implemented means the control is in place but misses its target, for example MFA on "
        "some accounts but not all. Not implemented means there is no evidence the control is in place.")
    st.dataframe(
        pd.DataFrame([{"Control": c.control_id, "Title": c.title, "Status": c.status,
                       "Evidence checks": ", ".join(c.rules) or "Manual review"} for c in result.controls]),
        hide_index=True)

with tab_checks:
    st.dataframe(
        pd.DataFrame([{"Check": r.rule_id, "Title": r.title, "Severity": r.severity.title(),
                       "Result": result_text(r), "Detail": r.detail} for r in result.rules]),
        hide_index=True)

st.subheader("Download the report")
stem = f"assessment_{result.baseline}"
d1, d2, d3, d4 = st.columns(4)
d1.download_button("HTML report", to_html(result), f"{stem}.html", "text/html")
d2.download_button("Markdown", to_markdown(result), f"{stem}.md", "text/markdown")
d3.download_button("CSV findings", to_csv(result), f"{stem}.csv", "text/csv")
d4.download_button("JSON results", to_json(result), f"{stem}.json", "application/json")

st.caption(DISCLAIMER)
