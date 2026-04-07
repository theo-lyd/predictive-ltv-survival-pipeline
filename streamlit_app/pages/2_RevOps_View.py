from __future__ import annotations

import streamlit as st

from streamlit_app.core.data_access import build_kpis
from streamlit_app.core.simulator import simulate_nrr_impact
from streamlit_app.core.ui import (
	get_filtered_dashboard_data,
	render_data_provenance_badge,
	render_kpi_ribbon,
	render_sidebar_filters,
)


st.title("RevOps Leadership View")
filters = render_sidebar_filters()

data = get_filtered_dashboard_data(filters)
render_data_provenance_badge(data)

kpis = build_kpis(data)
render_kpi_ribbon(kpis)

st.subheader("Revenue Retention Levers")
st.write("RevOps focus: optimize expansion without over-discounting and protect renewal conversion.")

discount = st.slider("Planned discount policy", 0, 30, 8)
elasticity = st.slider("Pipeline elasticity", 0.0, 1.5, 0.5, 0.05)
projected = simulate_nrr_impact(kpis["nrr"], discount, elasticity)
st.metric("Projected NRR under policy", f"{projected * 100:.1f}%")
