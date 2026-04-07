from __future__ import annotations

import streamlit as st

from streamlit_app.core.data_access import apply_global_filters, build_kpis, load_dashboard_data
from streamlit_app.core.ui import render_kpi_ribbon, render_sidebar_filters


st.title("Sales Leadership View")
filters = render_sidebar_filters()

data = apply_global_filters(
	load_dashboard_data(),
	filters["region"],
	filters["product_tier"],
	filters["date_range"],
)
kpis = build_kpis(data)
render_kpi_ribbon(kpis)

st.subheader("Pipeline Quality and Expansion")
st.write("Sales focus: identify segments where expansion probability is high and churn risk is low.")

expansion_score = max(0.0, min(1.0, (kpis["nrr"] - kpis["churn_rate"])))
st.metric("Expansion Readiness Score", f"{expansion_score * 100:.1f}%")
