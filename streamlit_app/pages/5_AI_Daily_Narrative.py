from __future__ import annotations

import json

import streamlit as st

from streamlit_app.core.narrative import load_daily_summary
from streamlit_app.core.ui import render_sidebar_filters


st.title("AI Daily Narrative")
render_sidebar_filters()

summary = load_daily_summary()
st.write(f"**Summary Date:** {summary.get('summary_date', 'N/A')}")
st.write(f"**Provenance:** {summary.get('provenance', 'N/A')}")
st.write(f"**Headline:** {summary.get('headline', 'N/A')}")

st.subheader("Insights")
for insight in summary.get("insights", []):
    st.write(f"- {insight}")

st.subheader("Recommended Actions")
for action in summary.get("actions", []):
    st.write(f"- {action}")

with st.expander("View Raw Summary JSON"):
    st.code(json.dumps(summary, indent=2), language="json")
