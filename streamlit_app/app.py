"""Streamlit executive flight deck scaffold."""

from __future__ import annotations

import streamlit as st


st.set_page_config(page_title="Executive Flight Deck", layout="wide")

st.sidebar.title("Global Filters")
region = st.sidebar.selectbox("Region", ["All", "North America", "EMEA", "APAC"])
date_range = st.sidebar.date_input("Date Range")
product_tier = st.sidebar.selectbox("Product Tier", ["All", "Starter", "Growth", "Enterprise"])

st.title("Executive Flight Deck")
st.caption("LTV, churn, and discount impact in one management view")

metric_cols = st.columns(4)
metric_cols[0].metric("LTV/CAC", "3.2x")
metric_cols[1].metric("NRR", "118%")
metric_cols[2].metric("Churn", "4.1%")
metric_cols[3].metric("Discount Efficiency", "1.7x")

st.subheader("Cohort Overview")
st.write(f"Selected region: {region}")
st.write(f"Selected product tier: {product_tier}")
st.write("Dashboard visuals will be connected to Gold-layer data in the next implementation step.")

st.subheader("AI Narrative")
st.info("Warning: this cohort is trending toward lower retention under heavier discounting.")
