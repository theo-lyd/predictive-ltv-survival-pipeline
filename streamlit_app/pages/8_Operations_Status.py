from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from streamlit_app.core.charts import (
    sla_breach_warning_trend_figure,
    sla_compliance_trend_figure,
    sla_grade_trend_figure,
)
from streamlit_app.core.sla import build_operational_snapshot, load_sla_history
from streamlit_app.core.ui import render_sidebar_filters, require_view_access


st.set_page_config(page_title="Operations Status", layout="wide")
filters = render_sidebar_filters()
require_view_access(filters["role"], "Operations Status", "sla_operations")

st.title("Operations Status")
st.caption("Phase 7 Batch 2: consolidated operational health and trend visibility")

history = load_sla_history()
snapshot = build_operational_snapshot(history=history)
report = snapshot["report"]
latest = snapshot["latest"]
run_history_df = pd.DataFrame(snapshot["history_runs"])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Latest Score", f"{latest['overall_score']:.1f}/100")
col2.metric("Latest Grade", latest["grade"])
col3.metric("Latest Breaches", latest["breach_count"])

freshness = snapshot["history_freshness_hours"]
freshness_display = "unknown" if freshness is None else f"{freshness:.1f}h"
col4.metric("History Freshness", freshness_display)

if snapshot["score_delta"] is not None:
    st.info(
        f"Score delta vs previous run: {snapshot['score_delta']:+.1f}. "
        f"Breach delta: {snapshot['breach_delta']:+d}."
    )

st.subheader("Run Trends")
if not run_history_df.empty:
    left, right = st.columns(2)
    with left:
        st.plotly_chart(sla_grade_trend_figure(run_history_df), use_container_width=True)
    with right:
        st.plotly_chart(sla_breach_warning_trend_figure(run_history_df), use_container_width=True)

    st.plotly_chart(sla_compliance_trend_figure(run_history_df), use_container_width=True)
else:
    st.warning("No operational history available yet. Run the SLA monitor to populate trends.")

st.subheader("Latest Breaches")
if report["breaches"]:
    for item in report["breaches"]:
        st.error(f"{item['layer']} - {item['metric']} ({item['severity']})")
        st.write(item["recommended_action"])
else:
    st.success("No active SLA breaches in the latest report.")

with st.expander("Operational Snapshot JSON"):
    st.code(json.dumps(snapshot, indent=2), language="json")
