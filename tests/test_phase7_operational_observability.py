from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.export_operational_snapshot import export_operational_snapshot
from streamlit_app.core.charts import sla_breach_warning_trend_figure, sla_grade_trend_figure
from streamlit_app.core.sla import build_operational_snapshot, build_sla_run_history


def test_build_sla_run_history_aggregates_rows_by_run():
    history = [
        {
            "generated_at": "2026-04-07T00:00:00+00:00",
            "layer": "Bronze",
            "status": "PASS",
            "overall_score": 98.0,
            "grade": "A",
            "source_layer": "gold",
            "alert_count": 0,
            "breach_count": 0,
            "warning_count": 1,
            "contract_valid": True,
        },
        {
            "generated_at": "2026-04-07T00:00:00+00:00",
            "layer": "Silver",
            "status": "WARN",
            "overall_score": 98.0,
            "grade": "A",
            "source_layer": "gold",
            "alert_count": 0,
            "breach_count": 0,
            "warning_count": 1,
            "contract_valid": True,
        },
        {
            "generated_at": "2026-04-06T00:00:00+00:00",
            "layer": "Bronze",
            "status": "FAIL",
            "overall_score": 80.0,
            "grade": "C",
            "source_layer": "raw-fallback",
            "alert_count": 1,
            "breach_count": 1,
            "warning_count": 0,
            "contract_valid": False,
        },
    ]

    runs = build_sla_run_history(history)

    assert len(runs) == 2
    assert runs[-1]["generated_at"] == "2026-04-07T00:00:00+00:00"
    assert runs[-1]["grade"] == "A"


def test_build_operational_snapshot_handles_missing_history():
    report = {
        "generated_at": "2026-04-07T10:00:00+00:00",
        "overall_score": 92.5,
        "grade": "B",
        "source_layer": "gold",
        "alert_count": 1,
        "contract_valid": True,
        "breaches": [{"layer": "Bronze", "metric": "Data availability"}],
        "warnings": [{"layer": "Silver", "metric": "Quality checkpoint"}],
        "items": [],
    }

    snapshot = build_operational_snapshot(report=report, history=[])

    assert snapshot["history_run_count"] == 1
    assert snapshot["latest"]["grade"] == "B"
    assert snapshot["latest"]["breach_count"] == 1


def test_operational_trend_charts_render_with_run_history():
    run_history = pd.DataFrame(
        [
            {
                "generated_at": "2026-04-06T00:00:00+00:00",
                "grade": "C",
                "breach_count": 2,
                "warning_count": 1,
            },
            {
                "generated_at": "2026-04-07T00:00:00+00:00",
                "grade": "A",
                "breach_count": 0,
                "warning_count": 1,
            },
        ]
    )

    grade_fig = sla_grade_trend_figure(run_history)
    breach_fig = sla_breach_warning_trend_figure(run_history)

    assert len(grade_fig.data) > 0
    assert len(breach_fig.data) > 0


def test_export_operational_snapshot_writes_json(tmp_path):
    history_file = tmp_path / "sla_history.jsonl"
    history_file.write_text(
        json.dumps(
            {
                "generated_at": "2026-04-07T00:00:00+00:00",
                "layer": "Bronze",
                "status": "PASS",
                "overall_score": 96.0,
                "grade": "A",
                "source_layer": "gold",
                "alert_count": 0,
                "breach_count": 0,
                "warning_count": 1,
                "contract_valid": True,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    output_file = tmp_path / "operational_snapshot.json"
    snapshot = export_operational_snapshot(output_file, history_file)

    assert output_file.exists()
    payload = json.loads(output_file.read_text(encoding="utf-8"))
    assert payload["history_run_count"] >= 1
    assert snapshot["latest"]["grade"] in {"A+", "A", "B", "C", "D"}
