from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from streamlit_app.core.charts import (
    sla_breach_warning_trend_figure,
    sla_compliance_trend_figure,
    sla_grade_trend_figure,
    sla_status_distribution_figure,
)
from streamlit_app.core.sla import (
    build_alert_payload,
    build_operational_snapshot,
    build_sla_report,
    build_sla_run_history,
    load_sla_history,
)
from streamlit_app.core.ui import render_sidebar_filters, require_view_access


st.set_page_config(page_title="SLA Compliance", layout="wide")
filters = render_sidebar_filters()
require_view_access(filters["role"], "SLA Compliance", "sla_operations")

st.title("SLA Compliance Monitoring")
st.caption("Phase 6 Batch 4: monitored SLAs, alert payloads, and compliance tracking")

report = build_sla_report()
history = load_sla_history()
snapshot = build_operational_snapshot(report=report, history=history)
run_history = build_sla_run_history(history, report)

if history:
    history_df = pd.DataFrame(history)
else:
    history_df = pd.DataFrame(
        [
            {
                "generated_at": report["generated_at"],
                "layer": item["layer"],
                "metric": item["metric"],
                "status": item["status"],
                "overall_score": report["overall_score"],
            }
            for item in report["items"]
        ]
    )

run_history_df = pd.DataFrame(run_history)

score_col, grade_col, breach_col, source_col = st.columns(4)
score_col.metric("Overall Score", f"{report['overall_score']:.1f}/100")
grade_col.metric("Grade", report["grade"])
breach_col.metric("Breaches", report["alert_count"])
source_col.metric("Source Layer", report["source_layer"])

st.progress(min(1.0, report["overall_score"] / 100.0))

st.subheader("Historical Compliance")
if not history_df.empty and not run_history_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(sla_compliance_trend_figure(history_df), use_container_width=True)
    with col2:
        st.plotly_chart(sla_status_distribution_figure(history_df), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(sla_grade_trend_figure(run_history_df), use_container_width=True)
    with col4:
        st.plotly_chart(sla_breach_warning_trend_figure(run_history_df), use_container_width=True)
else:
    st.info("No persisted SLA history found yet. Scheduled runs will populate the trend charts.")

st.subheader("Operational Snapshot")
latest = snapshot["latest"]
op_col1, op_col2, op_col3, op_col4 = st.columns(4)
op_col1.metric("History Runs", snapshot["history_run_count"])
op_col2.metric("Latest Grade", latest["grade"])
op_col3.metric("Latest Breaches", latest["breach_count"])
freshness_display = (
    "unknown"
    if snapshot["history_freshness_hours"] is None
    else f"{snapshot['history_freshness_hours']:.1f}h"
)
op_col4.metric("History Freshness", freshness_display)

if snapshot["score_delta"] is not None:
    st.caption(
        f"Score delta vs previous run: {snapshot['score_delta']:+.1f}; "
        f"breach delta: {snapshot['breach_delta']:+d}"
    )

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
