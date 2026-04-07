from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AIRFLOW_ROOT = REPO_ROOT / "airflow"
PLUGINS_ROOT = AIRFLOW_ROOT / "plugins"

if str(AIRFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(AIRFLOW_ROOT))
if str(PLUGINS_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGINS_ROOT))

from utils.anomaly_learning import _detect_anomalies, learn_monitor_thresholds
from utils.automated_remediation import run_automated_remediation
from utils.observability_dashboards import (
    collect_observability_snapshot,
    publish_datadog_metrics,
)


class FakeTaskInstance:
    def __init__(self, pulls: dict[tuple[str, str], object] | None = None):
        self.pulls = pulls or {}
        self.pushed = {}

    def xcom_pull(self, task_ids: str, key: str):
        return self.pulls.get((task_ids, key))

    def xcom_push(self, key: str, value):
        self.pushed[key] = value


class FakeDag:
    dag_id = "ltv_survival_pipeline"


def test_detect_anomalies_flags_outlier():
    values = [10.0, 10.2, 9.9, 10.1, 50.0]
    outliers = _detect_anomalies(values, z_threshold=1.5)
    assert outliers == [4]


def test_collect_observability_snapshot_summarizes_health():
    ti = FakeTaskInstance(
        pulls={
            ("mc_check_bronze_health", "mc_health_bronze"): {
                "overall_status": "healthy",
                "critical_incidents": [],
            },
            ("mc_check_silver_health", "mc_health_silver"): {
                "overall_status": "degraded",
                "critical_incidents": [],
            },
            ("mc_check_gold_health", "mc_health_gold"): {
                "overall_status": "critical",
                "critical_incidents": [{"id": "i-1"}],
            },
        }
    )

    result = collect_observability_snapshot(
        task_instance=ti,
        dag=FakeDag(),
        run_id="test-run",
        execution_date="2026-04-07",
    )

    assert result["summary"]["healthy_layers"] == 1
    assert result["summary"]["degraded_layers"] == 2
    assert result["summary"]["critical_incidents"] == 1
    assert "batch_5_observability_snapshot" in ti.pushed


def test_publish_datadog_metrics_without_api_key(monkeypatch):
    ti = FakeTaskInstance(
        pulls={
            (
                "collect_observability_snapshot",
                "batch_5_observability_snapshot",
            ): {
                "summary": {
                    "critical_incidents": 0,
                    "healthy_layers": 3,
                    "degraded_layers": 0,
                }
            }
        }
    )

    from airflow.models import Variable

    monkeypatch.setattr(Variable, "get", staticmethod(lambda *args, **kwargs: ""))

    result = publish_datadog_metrics(task_instance=ti)
    assert result["status"] == "not_sent"
    assert result["reason"] == "missing DATADOG_API_KEY"


def test_run_automated_remediation_with_no_incidents():
    ti = FakeTaskInstance(
        pulls={
            ("mc_check_bronze_health", "mc_health_bronze"): {"tables": {}},
            ("mc_check_silver_health", "mc_health_silver"): {"tables": {}},
            ("mc_check_gold_health", "mc_health_gold"): {"tables": {}},
        }
    )

    result = run_automated_remediation(task_instance=ti)

    assert result["processed_incidents"] == 0
    assert result["resolved_count"] == 0
    assert result["recommendation_count"] == 0
    assert "batch_5_remediation_result" in ti.pushed


def test_learn_monitor_thresholds_handles_empty_monitor_variables(monkeypatch, tmp_path):
    from airflow.models import Variable
    from config.phase_4_batch_5_observability_config import ANOMALY_LEARNING_CONFIG

    monkeypatch.setattr(Variable, "get", staticmethod(lambda *args, **kwargs: ""))

    output_path = tmp_path / "monitor-thresholds.json"
    monkeypatch.setitem(
        ANOMALY_LEARNING_CONFIG,
        "learning_output_path",
        str(output_path),
    )

    ti = FakeTaskInstance()
    result = learn_monitor_thresholds(task_instance=ti)

    assert result["monitor_count"] == 0
    assert output_path.exists()

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["monitor_count"] == 0
    assert "batch_5_anomaly_learning_result" in ti.pushed
