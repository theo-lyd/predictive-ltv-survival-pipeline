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
