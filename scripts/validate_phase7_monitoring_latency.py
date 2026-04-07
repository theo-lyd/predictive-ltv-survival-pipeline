"""Validate Phase 7 monitoring and dashboard latency budgets."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from streamlit_app.core.charts import (
    sla_breach_warning_trend_figure,
    sla_compliance_trend_figure,
    sla_grade_trend_figure,
)
from streamlit_app.core.narrative import narrative_snapshot_timestamp
from streamlit_app.core.sla import (
    build_compliance_audit_artifact,
    build_operational_snapshot,
    build_sla_report,
    build_sla_run_history,
    load_sla_history,
)
from streamlit_app.core.data_access import dashboard_snapshot_timestamp


DEFAULT_THRESHOLDS = {
    "snapshot_key_seconds": 0.5,
    "report_seconds": 1.5,
    "snapshot_seconds": 1.5,
    "audit_seconds": 2.0,
    "chart_seconds": 2.0,
}


def _measure(label: str, func) -> tuple[str, float, Any]:
    start = time.perf_counter()
    result = func()
    elapsed = time.perf_counter() - start
    return label, elapsed, result


def run_latency_validation(thresholds: dict[str, float] | None = None) -> dict[str, Any]:
    thresholds = {**DEFAULT_THRESHOLDS, **(thresholds or {})}

    measurements: dict[str, float] = {}
    results: dict[str, Any] = {}

    for label, func in (
        ("dashboard_snapshot_timestamp", dashboard_snapshot_timestamp),
        ("narrative_snapshot_timestamp", narrative_snapshot_timestamp),
        ("load_sla_history", load_sla_history),
        ("build_sla_report", build_sla_report),
    ):
        measured_label, elapsed, result = _measure(label, func)
        measurements[measured_label] = elapsed
        results[measured_label] = result

    report = results["build_sla_report"]
    history = results["load_sla_history"]

    _, elapsed, operational_snapshot = _measure(
        "build_operational_snapshot",
        lambda: build_operational_snapshot(report=report, history=history),
    )
    measurements["build_operational_snapshot"] = elapsed
    results["build_operational_snapshot"] = operational_snapshot

    _, elapsed, audit_artifact = _measure(
        "build_compliance_audit_artifact",
        lambda: build_compliance_audit_artifact(report=report, history=history),
    )
    measurements["build_compliance_audit_artifact"] = elapsed
    results["build_compliance_audit_artifact"] = audit_artifact

    run_history = build_sla_run_history(history, report)
    history_df = pd.DataFrame(history)
    run_history_df = pd.DataFrame(run_history)
    _, elapsed, _ = _measure(
        "chart_generation",
        lambda: (
            sla_compliance_trend_figure(history_df),
            sla_grade_trend_figure(run_history_df),
            sla_breach_warning_trend_figure(run_history_df),
        ),
    )
    measurements["chart_generation"] = elapsed

    threshold_map = {
        "dashboard_snapshot_timestamp": thresholds["snapshot_key_seconds"],
        "narrative_snapshot_timestamp": thresholds["snapshot_key_seconds"],
        "build_sla_report": thresholds["report_seconds"],
        "build_operational_snapshot": thresholds["snapshot_seconds"],
        "build_compliance_audit_artifact": thresholds["audit_seconds"],
        "chart_generation": thresholds["chart_seconds"],
    }

    failures: list[str] = []
    for key, threshold in threshold_map.items():
        actual = measurements.get(key)
        if actual is not None and actual > threshold:
            failures.append(f"{key} {actual:.3f}s > {threshold:.3f}s")

    overall_elapsed = sum(measurements.values())
    return {
        "thresholds": thresholds,
        "measurements": measurements,
        "overall_elapsed_seconds": overall_elapsed,
        "failures": failures,
        "report_grade": report["grade"],
        "history_run_count": operational_snapshot["history_run_count"],
        "audit_schema_version": audit_artifact["schema_version"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 7 monitoring latency")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output",
    )
    parser.add_argument(
        "--snapshot-key-seconds",
        type=float,
        default=DEFAULT_THRESHOLDS["snapshot_key_seconds"],
        help="Maximum budget for snapshot timestamp lookups",
    )
    parser.add_argument(
        "--report-seconds",
        type=float,
        default=DEFAULT_THRESHOLDS["report_seconds"],
        help="Maximum budget for SLA report generation",
    )
    parser.add_argument(
        "--snapshot-seconds",
        type=float,
        default=DEFAULT_THRESHOLDS["snapshot_seconds"],
        help="Maximum budget for operational snapshot generation",
    )
    parser.add_argument(
        "--audit-seconds",
        type=float,
        default=DEFAULT_THRESHOLDS["audit_seconds"],
        help="Maximum budget for compliance audit artifact generation",
    )
    parser.add_argument(
        "--chart-seconds",
        type=float,
        default=DEFAULT_THRESHOLDS["chart_seconds"],
        help="Maximum budget for chart generation",
    )
    args = parser.parse_args(argv)

    thresholds = {
        "snapshot_key_seconds": args.snapshot_key_seconds,
        "report_seconds": args.report_seconds,
        "snapshot_seconds": args.snapshot_seconds,
        "audit_seconds": args.audit_seconds,
        "chart_seconds": args.chart_seconds,
    }
    result = run_latency_validation(thresholds)

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for name, elapsed in sorted(result["measurements"].items()):
            print(f"{name}: {elapsed:.3f}s")
        print(f"overall_elapsed_seconds: {result['overall_elapsed_seconds']:.3f}s")
        print(f"report_grade: {result['report_grade']}")
        print(f"history_run_count: {result['history_run_count']}")
        print(f"audit_schema_version: {result['audit_schema_version']}")

    if result["failures"]:
        print("FAILED latency validation:")
        for failure in result["failures"]:
            print(f"- {failure}")
        return 1

    print("Latency validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
