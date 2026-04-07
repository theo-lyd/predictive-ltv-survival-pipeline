from __future__ import annotations

import json

import streamlit as st

from streamlit_app.core.ui import (
    get_cached_narrative_summary,
    render_narrative_contract_warning,
    render_sidebar_filters,
    require_view_access,
)


st.title("AI Daily Narrative")
filters = render_sidebar_filters()
require_view_access(filters["role"], "AI Daily Narrative", "narrative_review")

summary = get_cached_narrative_summary()
render_narrative_contract_warning(summary, severity="error")
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
