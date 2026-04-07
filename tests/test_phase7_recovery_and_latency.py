from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import validate_phase7_monitoring_latency as latency_validator


def test_run_latency_validation_reports_measurements(monkeypatch):
    monkeypatch.setattr(latency_validator, "dashboard_snapshot_timestamp", lambda: 1.0)
    monkeypatch.setattr(latency_validator, "narrative_snapshot_timestamp", lambda: 2.0)
    monkeypatch.setattr(latency_validator, "load_sla_history", lambda: [{"generated_at": "t"}])
    monkeypatch.setattr(
        latency_validator,
        "build_sla_report",
        lambda: {"generated_at": "t", "grade": "A", "items": [], "breaches": [], "warnings": []},
    )
    monkeypatch.setattr(
        latency_validator,
        "build_operational_snapshot",
        lambda report, history: {"history_run_count": 1},
    )
    monkeypatch.setattr(
        latency_validator,
        "build_compliance_audit_artifact",
        lambda report, history: {"schema_version": "1.0.0"},
    )
    monkeypatch.setattr(latency_validator, "build_sla_run_history", lambda history, report: [])
    monkeypatch.setattr(latency_validator, "sla_compliance_trend_figure", lambda history: object())
    monkeypatch.setattr(latency_validator, "sla_grade_trend_figure", lambda history: object())
    monkeypatch.setattr(
        latency_validator, "sla_breach_warning_trend_figure", lambda history: object()
    )

    calls = [
        ("dashboard_snapshot_timestamp", 0.01, 1.0),
        ("narrative_snapshot_timestamp", 0.01, 2.0),
        ("load_sla_history", 0.02, [{"generated_at": "t"}]),
        (
            "build_sla_report",
            0.03,
            {"generated_at": "t", "grade": "A", "items": [], "breaches": [], "warnings": []},
        ),
        ("build_operational_snapshot", 0.04, {"history_run_count": 1}),
        ("build_compliance_audit_artifact", 0.05, {"schema_version": "1.0.0"}),
        ("chart_generation", 0.06, None),
    ]

    def fake_measure(label, func):
        expected_label, elapsed, result = calls.pop(0)
        assert label == expected_label
        return label, elapsed, result

    monkeypatch.setattr(latency_validator, "_measure", fake_measure)

    result = latency_validator.run_latency_validation({"report_seconds": 1.0})

    assert result["report_grade"] == "A"
    assert result["history_run_count"] == 1
    assert result["audit_schema_version"] == "1.0.0"
    assert result["failures"] == []
    assert result["measurements"]["build_sla_report"] == 0.03


def test_run_latency_validation_flags_threshold_breach(monkeypatch):
    monkeypatch.setattr(latency_validator, "dashboard_snapshot_timestamp", lambda: 1.0)
    monkeypatch.setattr(latency_validator, "narrative_snapshot_timestamp", lambda: 2.0)
    monkeypatch.setattr(latency_validator, "load_sla_history", lambda: [])
    monkeypatch.setattr(
        latency_validator,
        "build_sla_report",
        lambda: {"generated_at": "t", "grade": "A", "items": [], "breaches": [], "warnings": []},
    )
    monkeypatch.setattr(
        latency_validator,
        "build_operational_snapshot",
        lambda report, history: {"history_run_count": 1},
    )
    monkeypatch.setattr(
        latency_validator,
        "build_compliance_audit_artifact",
        lambda report, history: {"schema_version": "1.0.0"},
    )
    monkeypatch.setattr(latency_validator, "build_sla_run_history", lambda history, report: [])
    monkeypatch.setattr(latency_validator, "sla_compliance_trend_figure", lambda history: object())
    monkeypatch.setattr(latency_validator, "sla_grade_trend_figure", lambda history: object())
    monkeypatch.setattr(
        latency_validator, "sla_breach_warning_trend_figure", lambda history: object()
    )

    def slow_measure(label, func):
        elapsed = 0.25 if label == "build_sla_report" else 0.01
        result = func()
        return label, elapsed, result

    monkeypatch.setattr(latency_validator, "_measure", slow_measure)

    result = latency_validator.run_latency_validation({"report_seconds": 0.1})

    assert result["failures"]
    assert any("build_sla_report" in failure for failure in result["failures"])
