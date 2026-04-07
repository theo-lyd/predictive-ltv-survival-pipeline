"""Validate Streamlit Phase 5 data and chart latency for executive UX targets."""

from __future__ import annotations

import time
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from streamlit_app.core.charts import (
    cohort_heatmap_figure,
    ltv_journey_sankey_figure,
    survival_comparison_figure,
)
from streamlit_app.core.data_access import (
    build_kpis,
    cohort_matrix,
    dashboard_snapshot_timestamp,
    load_dashboard_data,
    sankey_flows,
    survival_curves,
)
from streamlit_app.core.narrative import narrative_snapshot_timestamp


MAX_LOAD_SECONDS = 1.5
MAX_CHART_SECONDS = 2.0


def main() -> int:
    t0 = time.perf_counter()
    _ = dashboard_snapshot_timestamp()
    _ = narrative_snapshot_timestamp()
    data = load_dashboard_data()
    _ = build_kpis(data)
    load_elapsed = time.perf_counter() - t0

    c0 = time.perf_counter()
    _ = cohort_heatmap_figure(cohort_matrix(data))
    _ = survival_comparison_figure(survival_curves(data))
    _ = ltv_journey_sankey_figure(sankey_flows(data))
    chart_elapsed = time.perf_counter() - c0

    print(f"Data load latency: {load_elapsed:.3f}s")
    print(f"Chart build latency: {chart_elapsed:.3f}s")

    failures = []
    if load_elapsed > MAX_LOAD_SECONDS:
        failures.append(f"load latency {load_elapsed:.3f}s > {MAX_LOAD_SECONDS:.3f}s")
    if chart_elapsed > MAX_CHART_SECONDS:
        failures.append(f"chart latency {chart_elapsed:.3f}s > {MAX_CHART_SECONDS:.3f}s")

    if failures:
        print("FAILED latency validation:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("Latency validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
