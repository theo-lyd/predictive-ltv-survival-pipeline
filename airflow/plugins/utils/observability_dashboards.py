"""Dashboard utilities for Batch 5 observability publishing."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any

import requests
from airflow.models import Variable

from config.phase_4_batch_5_observability_config import DASHBOARD_CONFIG


logger = logging.getLogger(__name__)


def _safe_mkdir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def collect_observability_snapshot(**context) -> dict[str, Any]:
    """Collect DAG and Monte Carlo health signals into a single snapshot payload."""
    ti = context["task_instance"]

    snapshot = {
        "collected_at": datetime.utcnow().isoformat(),
        "dag_id": context["dag"].dag_id,
        "run_id": context["run_id"],
        "execution_date": str(context.get("execution_date")),
        "mc_health": {
            "bronze": ti.xcom_pull(task_ids="mc_check_bronze_health", key="mc_health_bronze"),
            "silver": ti.xcom_pull(task_ids="mc_check_silver_health", key="mc_health_silver"),
            "gold": ti.xcom_pull(task_ids="mc_check_gold_health", key="mc_health_gold"),
        },
    }

    totals = {
        "critical_incidents": 0,
        "degraded_layers": 0,
        "healthy_layers": 0,
    }

    for layer in ("bronze", "silver", "gold"):
        health = snapshot["mc_health"].get(layer) or {}
        status = (health or {}).get("overall_status", "unknown")

        if status == "critical":
            totals["degraded_layers"] += 1
        elif status == "degraded":
            totals["degraded_layers"] += 1
        elif status == "healthy":
            totals["healthy_layers"] += 1

        totals["critical_incidents"] += len((health or {}).get("critical_incidents", []))

    snapshot["summary"] = totals

    ti.xcom_push(key="batch_5_observability_snapshot", value=snapshot)
    logger.info("Observability snapshot collected: %s", snapshot["summary"])
    return snapshot


def publish_grafana_dashboard(**context) -> dict[str, Any]:
    """Render and persist Grafana dashboard JSON artifact from snapshot data."""
    cfg = DASHBOARD_CONFIG["grafana"]
    if not cfg.get("enabled", False):
        return {"status": "skipped", "reason": "grafana disabled"}

    ti = context["task_instance"]
    snapshot = ti.xcom_pull(key="batch_5_observability_snapshot", task_ids="collect_observability_snapshot")
    snapshot = snapshot or {}
    summary = snapshot.get("summary", {})

    dashboard = {
        "uid": cfg["dashboard_uid"],
        "title": cfg["dashboard_title"],
        "schemaVersion": 36,
        "version": 1,
        "tags": ["ltv", "survival", "batch-5", "observability"],
        "time": {"from": "now-7d", "to": "now"},
        "panels": [
            {
                "id": 1,
                "title": "Critical Incidents",
                "type": "stat",
                "description": "Number of critical incidents from latest snapshot",
                "targets": [],
                "options": {"reduceOptions": {"calcs": ["lastNotNull"]}},
                "fieldConfig": {
                    "defaults": {
                        "mappings": [],
                        "thresholds": {
                            "mode": "absolute",
                            "steps": [
                                {"color": "green", "value": 0},
                                {"color": "red", "value": 1},
                            ],
                        },
                    }
                },
                "transparent": True,
            },
            {
                "id": 2,
                "title": "Layer Health",
                "type": "table",
                "description": "Bronze/Silver/Gold health status from Monte Carlo checks",
                "targets": [],
                "transparent": True,
            },
        ],
        "templating": {"list": []},
        "annotations": {"list": []},
        "meta": {
            "generated_at": datetime.utcnow().isoformat(),
            "latest_summary": summary,
        },
    }

    output_path = os.path.join(os.getcwd(), cfg["output_path"])
    _safe_mkdir(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dashboard, f, indent=2)

    result = {
        "status": "published",
        "path": output_path,
        "summary": summary,
    }
    ti.xcom_push(key="batch_5_grafana_dashboard", value=result)
    logger.info("Grafana dashboard artifact written to %s", output_path)
    return result


def publish_datadog_metrics(**context) -> dict[str, Any]:
    """Send snapshot counters to Datadog if API key is configured."""
    cfg = DASHBOARD_CONFIG["datadog"]
    if not cfg.get("enabled", False):
        return {"status": "skipped", "reason": "datadog disabled"}

    ti = context["task_instance"]
    snapshot = ti.xcom_pull(key="batch_5_observability_snapshot", task_ids="collect_observability_snapshot")
    snapshot = snapshot or {}
    summary = snapshot.get("summary", {})

    metric_namespace = cfg["metric_namespace"]
    points_at = int(datetime.utcnow().timestamp())

    payload = {
        "series": [
            {
                "metric": f"{metric_namespace}.critical_incidents",
                "type": "gauge",
                "points": [[points_at, float(summary.get("critical_incidents", 0))]],
                "tags": ["pipeline:ltv_survival"],
            },
            {
                "metric": f"{metric_namespace}.healthy_layers",
                "type": "gauge",
                "points": [[points_at, float(summary.get("healthy_layers", 0))]],
                "tags": ["pipeline:ltv_survival"],
            },
            {
                "metric": f"{metric_namespace}.degraded_layers",
                "type": "gauge",
                "points": [[points_at, float(summary.get("degraded_layers", 0))]],
                "tags": ["pipeline:ltv_survival"],
            },
        ]
    }

    api_key = Variable.get("DATADOG_API_KEY", default_var="")
    if not api_key:
        logger.warning("DATADOG_API_KEY is not set; metrics payload logged only")
        return {
            "status": "not_sent",
            "reason": "missing DATADOG_API_KEY",
            "payload": payload,
        }

    headers = {
        "Content-Type": "application/json",
        "DD-API-KEY": api_key,
    }

    response = requests.post(cfg["api_host"], headers=headers, json=payload, timeout=15)
    response.raise_for_status()

    result = {"status": "sent", "http_status": response.status_code}
    ti.xcom_push(key="batch_5_datadog_metrics", value=result)
    logger.info("Datadog metrics emitted successfully")
    return result
