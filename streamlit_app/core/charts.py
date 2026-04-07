"""Chart builders for executive dashboard."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def cohort_heatmap_figure(matrix: pd.DataFrame) -> go.Figure:
    if matrix.empty:
        return go.Figure()
    fig = px.imshow(
        matrix,
        labels={"x": "Tenure Month", "y": "Cohort Month", "color": "Retention Rate"},
        aspect="auto",
        color_continuous_scale="Blues",
        zmin=0,
        zmax=1,
    )
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig


def survival_comparison_figure(curves: pd.DataFrame) -> go.Figure:
    if curves.empty:
        return go.Figure()
    fig = px.line(
        curves,
        x="tenure_month",
        y="survival_probability",
        color="segment",
        labels={
            "tenure_month": "Tenure Month",
            "survival_probability": "Survival Probability",
            "segment": "Product Tier",
        },
    )
    fig.update_yaxes(range=[0, 1])
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig


def ltv_journey_sankey_figure(flows: pd.DataFrame) -> go.Figure:
    if flows.empty:
        return go.Figure()
    labels = list(pd.unique(flows[["source", "target"]].values.ravel("K")))
    idx = {name: i for i, name in enumerate(labels)}

    fig = go.Figure(
        data=[
            go.Sankey(
                node=dict(label=labels, pad=15, thickness=20),
                link=dict(
                    source=flows["source"].map(idx),
                    target=flows["target"].map(idx),
                    value=flows["value"],
                ),
            )
        ]
    )
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig


def sla_compliance_trend_figure(history: pd.DataFrame) -> go.Figure:
    if history.empty:
        return go.Figure()

    fig = px.line(
        history,
        x="generated_at",
        y="overall_score",
        color="layer",
        markers=True,
        labels={"generated_at": "Run Time", "overall_score": "Compliance Score", "layer": "Layer"},
    )
    fig.update_yaxes(range=[0, 100])
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig


def sla_status_distribution_figure(history: pd.DataFrame) -> go.Figure:
    if history.empty:
        return go.Figure()

    counts = history.groupby(["layer", "status"]).size().reset_index(name="count")
    fig = px.bar(
        counts,
        x="layer",
        y="count",
        color="status",
        barmode="group",
        labels={"layer": "Layer", "count": "Run Count", "status": "Status"},
    )
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig


def sla_grade_trend_figure(run_history: pd.DataFrame) -> go.Figure:
    if run_history.empty:
        return go.Figure()

    grade_to_score = {
        "A+": 100,
        "A": 95,
        "B": 85,
        "C": 75,
        "D": 60,
    }
    data = run_history.copy()
    data["grade_score"] = data["grade"].map(grade_to_score).fillna(0)

    fig = px.line(
        data,
        x="generated_at",
        y="grade_score",
        markers=True,
        text="grade",
        labels={
            "generated_at": "Run Time",
            "grade_score": "Grade Score",
        },
    )
    fig.update_yaxes(range=[0, 100])
    fig.update_traces(textposition="top center")
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig


def sla_breach_warning_trend_figure(run_history: pd.DataFrame) -> go.Figure:
    if run_history.empty:
        return go.Figure()

    data = run_history.copy()
    chart_data = data.melt(
        id_vars=["generated_at"],
        value_vars=["breach_count", "warning_count"],
        var_name="series",
        value_name="count",
    )
    chart_data["series"] = chart_data["series"].replace(
        {"breach_count": "Breaches", "warning_count": "Warnings"}
    )

    fig = px.line(
        chart_data,
        x="generated_at",
        y="count",
        color="series",
        markers=True,
        labels={
            "generated_at": "Run Time",
            "count": "Count",
            "series": "Series",
        },
    )
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
    return fig
