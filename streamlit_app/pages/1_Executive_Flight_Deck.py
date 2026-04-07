from __future__ import annotations

import streamlit as st

from streamlit_app.core.charts import cohort_heatmap_figure, ltv_journey_sankey_figure, survival_comparison_figure
from streamlit_app.core.data_access import (
    apply_global_filters,
    build_kpis,
    cohort_matrix,
    load_dashboard_data,
    sankey_flows,
    survival_curves,
)
from streamlit_app.core.narrative import load_daily_summary
from streamlit_app.core.simulator import simulate_nrr_impact
from streamlit_app.core.ui import render_kpi_ribbon, render_sidebar_filters


st.title("Executive Flight Deck")
filters = render_sidebar_filters()

data = apply_global_filters(
    load_dashboard_data(),
    region=filters["region"],
    product_tier=filters["product_tier"],
)

kpis = build_kpis(data)
render_kpi_ribbon(kpis)

st.subheader("Cohort Heatmap")
st.plotly_chart(cohort_heatmap_figure(cohort_matrix(data)), use_container_width=True)

st.subheader("Survival Comparison")
st.plotly_chart(survival_comparison_figure(survival_curves(data)), use_container_width=True)

st.subheader("Sankey LTV Journey")
st.plotly_chart(ltv_journey_sankey_figure(sankey_flows(data)), use_container_width=True)

st.subheader("What-if Discount Simulator (NRR Impact)")
col1, col2 = st.columns(2)
with col1:
    discount_pct = st.slider("Discount %", 0, 40, 10)
with col2:
    elasticity = st.slider("Retention Elasticity", 0.0, 2.0, 0.6, 0.05)

projected_nrr = simulate_nrr_impact(kpis["nrr"], discount_pct, elasticity)
st.metric("Projected NRR", f"{projected_nrr * 100:.1f}%", delta=f"{(projected_nrr - kpis['nrr']) * 100:.1f}pp")

st.subheader("AI Narrative Panel")
summary = load_daily_summary()
st.write(f"**Headline:** {summary.get('headline', 'N/A')}")
for insight in summary.get("insights", []):
    st.write(f"- {insight}")
