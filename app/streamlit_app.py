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

from grc_assess import __version__, assess  # noqa: E402
from grc_assess.catalog import BASELINES  # noqa: E402
from grc_assess.reporting import DISCLAIMER, to_csv, to_html, to_json, to_markdown  # noqa: E402

SAMPLES = {
    "Small manufacturer with control gaps (fictional)": ROOT / "samples" / "example_manufacturer_weak.json",
    "Cold storage warehouse with mature controls (fictional)": ROOT / "samples" / "example_cold_storage_mature.json",
}
TEMPLATE = ROOT / "samples" / "config_template.json"
SEVERITY_ICON = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "⚪"}

st.set_page_config(page_title="NIST SP 800-53 Assessment", page_icon="🛡️", layout="wide")

st.title("NIST SP 800-53 control assessment")
st.write(
    "Check a system configuration against the NIST SP 800-53 Rev. 5 low, moderate, or high baseline "
    "and get a prioritized remediation list. Built for small and mid-sized organizations without a "
    "dedicated compliance team."
)

with st.sidebar:
    st.header("1. Choose data")
    source = st.radio("Configuration source", ["Use a sample", "Upload my own JSON"], label_visibility="collapsed")
    config: dict | None = None
    if source == "Use a sample":
        choice = st.selectbox("Sample organization", list(SAMPLES))
        config = json.loads(SAMPLES[choice].read_text(encoding="utf-8"))
    else:
        upload = st.file_uploader("Configuration file (.json)", type=["json"])
        if TEMPLATE.exists():
            st.download_button("Download blank template", TEMPLATE.read_bytes(),
                               file_name="config_template.json", mime="application/json")
        if upload is not None:
            try:
                config = json.loads(upload.getvalue().decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                st.error(f"This file is not valid JSON: {exc}. Fix the file and upload it again.")

    st.header("2. Choose baseline")
    default_baseline = ((config or {}).get("organization", {}).get("baseline") or "moderate").lower()
    baseline = st.selectbox("Control baseline", BASELINES,
                            index=BASELINES.index(default_baseline) if default_baseline in BASELINES else 1,
                            format_func=str.title)
    st.caption(f"grc_assess {__version__}. Runs entirely in this session; uploaded files are not stored.")

if config is None:
    st.info("Upload a configuration file in the sidebar, or switch to a sample, to see results.")
    st.stop()

result = assess(config, baseline=baseline)
rc = result.rule_counts

st.subheader(f"{result.organization}")
st.caption(f"{result.sector}. {result.baseline.title()} baseline.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Weighted risk exposure", f"{result.risk_score:.0f} / 100", result.risk_rating, delta_color="off")
c2.metric("Automated checks passed",
          "n/a" if result.compliance_pct is None else f"{result.compliance_pct:.1f}%")
c3.metric("Failed checks", rc["FAIL"])
c4.metric("Checks lacking data", rc["NOT_ASSESSED"])

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
    fam_df = pd.DataFrame(
        [{"Family": f"{x.family} {x.family_name}", "Compliance %": x.compliance_pct,
          "Checks assessed": x.rules_assessed} for x in result.families]
    )
    chart_df = fam_df.dropna(subset=["Compliance %"]).set_index("Family")[["Compliance %"]]
    if not chart_df.empty:
        st.bar_chart(chart_df, horizontal=True)
    st.dataframe(fam_df, hide_index=True)

with tab_controls:
    st.dataframe(
        pd.DataFrame([{"Control": c.control_id, "Title": c.title, "Status": c.status,
                       "Evidence checks": ", ".join(c.rules) or "Manual review"} for c in result.controls]),
        hide_index=True)

with tab_checks:
    st.dataframe(
        pd.DataFrame([{"Check": r.rule_id, "Title": r.title, "Severity": r.severity.title(),
                       "Result": r.status.replace("_", " ").title(), "Detail": r.detail} for r in result.rules]),
        hide_index=True)

st.subheader("Download the report")
stem = f"assessment_{result.baseline}"
d1, d2, d3, d4 = st.columns(4)
d1.download_button("HTML report", to_html(result), f"{stem}.html", "text/html")
d2.download_button("Markdown", to_markdown(result), f"{stem}.md", "text/markdown")
d3.download_button("CSV findings", to_csv(result), f"{stem}.csv", "text/csv")
d4.download_button("JSON results", to_json(result), f"{stem}.json", "application/json")

st.caption(DISCLAIMER)
