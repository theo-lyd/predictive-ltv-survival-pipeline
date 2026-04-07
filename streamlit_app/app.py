"""Phase 5 executive storytelling dashboard entrypoint."""

from __future__ import annotations

import streamlit as st

from streamlit_app.core.kpi_glossary import STRATEGIC_QUESTIONS
from streamlit_app.core.ui import render_sidebar_filters


st.set_page_config(page_title="Executive Flight Deck", layout="wide")
filters = render_sidebar_filters()

st.title("Executive Flight Deck")
st.caption("Phase 5: BI + AI-supported storytelling for executive decisioning")

st.subheader("Strategic Questions This App Answers")
for i, question in enumerate(STRATEGIC_QUESTIONS, start=1):
	st.write(f"{i}. {question}")

st.info(
	"Use pages in the left navigation to review Executive, RevOps, Finance, Sales, "
	"AI Narrative, KPI Glossary, and SLA Compliance views. Global filters are shared across pages."
)

st.write("Current role view:", filters["role"])
