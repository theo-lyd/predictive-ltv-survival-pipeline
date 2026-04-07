from __future__ import annotations

import streamlit as st

from streamlit_app.core.kpi_glossary import KPI_GLOSSARY
from streamlit_app.core.ui import render_sidebar_filters


st.title("KPI Glossary & Help")
render_sidebar_filters()

for name, details in KPI_GLOSSARY.items():
    with st.expander(name):
        st.write(f"**Definition:** {details['definition']}")
        st.write(f"**Formula:** {details['formula']}")
        st.write(f"**Why it matters:** {details['why_it_matters']}")
