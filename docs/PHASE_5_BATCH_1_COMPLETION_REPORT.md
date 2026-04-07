# Phase 5 Batch 1 Completion Report

## What Was Built
- Modular Streamlit core package under `streamlit_app/core`.
- Shared global filters + KPI ribbon.
- Executive page with cohort heatmap, survival comparison, sankey LTV journey, and discount simulator.
- Multi-page role shells for RevOps, Finance, Sales, AI Narrative, and KPI Glossary.

## Why These Choices
- Modular core helpers reduce repeated chart/filter logic and make role pages maintainable.
- Plotly chosen for interactive executive-ready visuals (heatmap, line, sankey) in Streamlit.
- Shared sidebar in each page keeps global filter semantics consistent.

## Issues and Resolutions
- Existing app was scaffold-only and not role-capable.
- Resolved by replacing entrypoint and introducing page-based navigation.

## Acceptance Mapping
- Sidebar global filters: implemented.
- KPI ribbon: implemented.
- Cohort heatmap: implemented.
- Survival comparison view: implemented.
- Sankey LTV journey: implemented.
- What-if discount simulator: implemented.
