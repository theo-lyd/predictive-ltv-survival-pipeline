"""Shared Streamlit UI elements and filter handling."""

from __future__ import annotations

from datetime import date

import streamlit as st

from streamlit_app.core.auth import (
    build_access_denied_message,
    get_locked_views,
    get_visible_views,
    role_can_access,
)
from streamlit_app.core.data_access import (
    DashboardData,
    apply_global_filters,
    dashboard_snapshot_timestamp,
    load_dashboard_data,
)
from streamlit_app.core.narrative import load_daily_summary, narrative_snapshot_timestamp


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


def render_access_summary(role: str) -> None:
    visible_views = get_visible_views(role)
    locked_views = get_locked_views(role)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Available Views")
    for view in visible_views:
        st.sidebar.write(f"✓ {view.label}")

    if locked_views:
        with st.sidebar.expander("Restricted views"):
            for view in locked_views:
                st.write(f"- {view.label}: {view.description}")


def render_access_denied(role: str | None, view_label: str, capability: str | None) -> None:
    st.error(build_access_denied_message(role, view_label, capability))
    st.info("Select a permitted role from the sidebar or contact the repository owner for access.")


def require_view_access(role: str | None, view_label: str, capability: str | None) -> bool:
    if role_can_access(role, capability):
        return True

    render_access_denied(role, view_label, capability)
    st.stop()
    return False


def render_kpi_ribbon(kpis: dict[str, float]) -> None:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("NRR", f"{kpis['nrr'] * 100:.1f}%")
    c2.metric("LTV/CAC", f"{kpis['ltv_cac']:.2f}x")
    c3.metric("Churn", f"{kpis['churn_rate'] * 100:.1f}%")
    c4.metric("Discount Efficiency", f"{kpis['discount_efficiency']:.2f}")


@st.cache_data(show_spinner=False)
def cached_dashboard_data(snapshot_ts: float) -> DashboardData:
    _ = snapshot_ts
    return load_dashboard_data()


def get_filtered_dashboard_data(filters: dict[str, object]) -> DashboardData:
    return apply_global_filters(
        cached_dashboard_data(dashboard_snapshot_timestamp()),
        region=filters["region"],
        product_tier=filters["product_tier"],
        date_range=filters["date_range"],
    )


def render_data_provenance_badge(data: DashboardData) -> None:
    if data.source_layer == "gold":
        st.success(f"Data source: GOLD (snapshot_ts={data.snapshot_ts:.0f})")
    else:
        st.warning(f"Data source: RAW FALLBACK (snapshot_ts={data.snapshot_ts:.0f})")


@st.cache_data(show_spinner=False)
def cached_narrative_summary(summary_ts: float) -> dict:
    _ = summary_ts
    return load_daily_summary()


def get_cached_narrative_summary() -> dict:
    return cached_narrative_summary(narrative_snapshot_timestamp())


def render_narrative_contract_warning(summary: dict, severity: str = "warning") -> None:
    if summary.get("contract_valid", True):
        return

    message = (
        "Narrative contract check failed; fallback summary is shown. "
        f"Errors: {', '.join(summary.get('contract_errors', []))}"
    )
    if severity == "error":
        st.error(message)
        return
    st.warning(message)
