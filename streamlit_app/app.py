"""Phase 5 executive storytelling dashboard entrypoint."""

from __future__ import annotations

import streamlit as st

from streamlit_app.core.kpi_glossary import STRATEGIC_QUESTIONS
from streamlit_app.core.auth import get_locked_views, get_visible_views
from streamlit_app.core.ui import render_access_summary, render_sidebar_filters


st.set_page_config(page_title="Executive Flight Deck", layout="wide")
filters = render_sidebar_filters()
render_access_summary(filters["role"])

st.title("Executive Flight Deck")
st.caption("Phase 5: BI + AI-supported storytelling for executive decisioning")

visible_views = get_visible_views(filters["role"])
locked_views = get_locked_views(filters["role"])

st.subheader("Role-Based Access")
st.write(f"Current role: {filters['role']}")

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Available views**")
    for view in visible_views:
        st.write(f"- {view.label}")
with col2:
    st.markdown("**Restricted views**")
    if locked_views:
        for view in locked_views:
            st.write(f"- {view.label}")
    else:
        st.write("- None")

st.subheader("Strategic Questions This App Answers")
for i, question in enumerate(STRATEGIC_QUESTIONS, start=1):
    st.write(f"{i}. {question}")

st.info(
    "Use pages in the left navigation to review Executive, RevOps, Finance, Sales, "
    "AI Narrative, KPI Glossary, and SLA Compliance views. Global filters are shared across pages."
)

st.write("Current role view:", filters["role"])
