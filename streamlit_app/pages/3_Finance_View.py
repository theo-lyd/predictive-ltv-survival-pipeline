from __future__ import annotations

import streamlit as st

from streamlit_app.core.data_access import apply_global_filters, build_kpis, load_dashboard_data
from streamlit_app.core.ui import render_kpi_ribbon, render_sidebar_filters


st.title("Finance Leadership View")
filters = render_sidebar_filters()

data = apply_global_filters(load_dashboard_data(), filters["region"], filters["product_tier"])
kpis = build_kpis(data)
render_kpi_ribbon(kpis)

st.subheader("Margin and Efficiency")
st.write("Finance focus: balance retention investment versus gross margin protection.")

estimated_margin_risk = max(0.0, 0.25 - (kpis["discount_efficiency"] / 10.0))
st.metric("Estimated Margin Risk", f"{estimated_margin_risk * 100:.1f}%")
