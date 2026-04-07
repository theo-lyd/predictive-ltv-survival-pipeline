"""Shared Streamlit UI elements and filter handling."""

from __future__ import annotations

from datetime import date

import streamlit as st


ROLE_OPTIONS = ["Executive", "RevOps", "Finance", "Sales Leadership"]
REGION_OPTIONS = ["All", "Unknown", "EU", "APAC", "North America", "EMEA"]
TIER_OPTIONS = ["All", "Basic", "Pro", "Growth", "Enterprise"]


def render_sidebar_filters() -> dict[str, object]:
    st.sidebar.header("Global Filters")

    role = st.sidebar.selectbox("Role View", ROLE_OPTIONS, key="global_role")
    region = st.sidebar.selectbox("Region", REGION_OPTIONS, key="global_region")
    product_tier = st.sidebar.selectbox("Product Tier", TIER_OPTIONS, key="global_product_tier")
    date_range = st.sidebar.date_input(
        "Date Range",
        (date(2024, 1, 1), date.today()),
        key="global_date_range",
    )

    return {
        "role": role,
        "region": region,
        "product_tier": product_tier,
        "date_range": date_range,
    }


def render_kpi_ribbon(kpis: dict[str, float]) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NRR", f"{kpis['nrr'] * 100:.1f}%")
    c2.metric("LTV/CAC", f"{kpis['ltv_cac']:.2f}x")
    c3.metric("Churn", f"{kpis['churn_rate'] * 100:.1f}%")
    c4.metric("Discount Efficiency", f"{kpis['discount_efficiency']:.2f}")
