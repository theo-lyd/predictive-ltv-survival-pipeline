from __future__ import annotations

import json

import streamlit as st

from streamlit_app.core.sla import build_sla_report, build_alert_payload
from streamlit_app.core.ui import render_sidebar_filters


st.set_page_config(page_title="SLA Compliance", layout="wide")
render_sidebar_filters()

st.title("SLA Compliance Monitoring")
st.caption("Phase 6 Batch 4: monitored SLAs, alert payloads, and compliance tracking")

report = build_sla_report()

score_col, grade_col, breach_col, source_col = st.columns(4)
score_col.metric("Overall Score", f"{report['overall_score']:.1f}/100")
grade_col.metric("Grade", report["grade"])
breach_col.metric("Breaches", report["alert_count"])
source_col.metric("Source Layer", report["source_layer"])

st.progress(min(1.0, report["overall_score"] / 100.0))

st.subheader("Layer Status")
for item in report["items"]:
    with st.container(border=True):
        left, right = st.columns([2, 1])
        with left:
            st.write(f"**{item['layer']}** - {item['metric']}")
            st.write(f"Target: {item['target']}")
            st.write(f"Actual: {item['actual']}")
            st.write(f"Evidence: {item['evidence']}")
        with right:
            st.metric("Status", item["status"])
            st.write(f"Owner: {item['owner']}")
            st.write(f"Channel: {item['alert_channel']}")
            st.write(f"Severity: {item['severity']}")
            st.write(f"Action: {item['recommended_action']}")

if report["breaches"]:
    st.subheader("Open Alert Payloads")
    for item in report["breaches"]:
        payload = build_alert_payload(report, item)
        st.error(payload["title"])
        st.code(json.dumps(payload, indent=2), language="json")
else:
    st.success("No blocking SLA breaches detected.")

with st.expander("Raw SLA Report JSON"):
    st.code(json.dumps(report, indent=2), language="json")
