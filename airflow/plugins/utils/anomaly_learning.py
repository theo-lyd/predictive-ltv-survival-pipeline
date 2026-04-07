"""Advanced anomaly learning utilities for Batch 5."""

from __future__ import annotations

import json
import logging
import math
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import mean, pstdev
from typing import Any

from config.phase_4_batch_4_monte_carlo_config import (
    FRESHNESS_MONITORS,
    VOLUME_MONITORS,
)
from config.phase_4_batch_5_observability_config import ANOMALY_LEARNING_CONFIG


logger = logging.getLogger(__name__)


@dataclass
class ThresholdSuggestion:
    monitor_key: str
    metric_mean: float
    metric_stddev: float
    suggested_lower: float
    suggested_upper: float
    sample_size: int


def _safe_mkdir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _detect_anomalies(values: list[float], z_threshold: float) -> list[int]:
    if len(values) < 3:
        return []
    mu = mean(values)
    sigma = pstdev(values)
    if sigma == 0:
        return []

    outlier_indexes = []
    for idx, value in enumerate(values):
        z = abs((value - mu) / sigma)
        if z >= z_threshold:
            outlier_indexes.append(idx)
    return outlier_indexes


def learn_monitor_thresholds(**context) -> dict[str, Any]:
    """Compute adaptive threshold suggestions from monitor metric history."""
    from airflow.plugins.hooks.monte_carlo_hook import MonteCarloHook

    if not ANOMALY_LEARNING_CONFIG["enabled"]:
        return {"status": "skipped", "reason": "anomaly learning disabled"}

    hook = MonteCarloHook()
    lookback_days = ANOMALY_LEARNING_CONFIG["lookback_days"]
    start_time = datetime.utcnow() - timedelta(days=lookback_days)
    end_time = datetime.utcnow()

    monitor_keys = list(VOLUME_MONITORS.keys()) + list(FRESHNESS_MONITORS.keys())
    monitor_keys = monitor_keys[: ANOMALY_LEARNING_CONFIG["max_monitors_per_run"]]

    suggestions: list[ThresholdSuggestion] = []
    anomalies: dict[str, list[int]] = {}

    for monitor_key in monitor_keys:
        # This assumes monitor IDs are stored in Airflow Variables with pattern MC_MONITOR_ID_<KEY>
        monitor_var_name = f"MC_MONITOR_ID_{monitor_key.upper()}"
        from airflow.models import Variable

        monitor_id = Variable.get(monitor_var_name, default_var="")
        if not monitor_id:
            continue

        metrics = hook.get_monitor_metrics(
            monitor_id=monitor_id,
            start_time=start_time,
            end_time=end_time,
        )
        values = [float(m.get("value", 0.0)) for m in metrics if m.get("value") is not None]
        if len(values) < ANOMALY_LEARNING_CONFIG["min_points"]:
            continue

        mu = mean(values)
        sigma = pstdev(values)
        lower = max(0.0, mu - (ANOMALY_LEARNING_CONFIG["zscore_threshold"] * sigma))
        upper = mu + (ANOMALY_LEARNING_CONFIG["zscore_threshold"] * sigma)

        suggestions.append(
            ThresholdSuggestion(
                monitor_key=monitor_key,
                metric_mean=mu,
                metric_stddev=sigma,
                suggested_lower=lower,
                suggested_upper=upper,
                sample_size=len(values),
            )
        )

        anomalies[monitor_key] = _detect_anomalies(
            values,
            ANOMALY_LEARNING_CONFIG["zscore_threshold"],
        )

    payload = {
        "generated_at": datetime.utcnow().isoformat(),
        "lookback_days": lookback_days,
        "monitor_count": len(suggestions),
        "thresholds": [s.__dict__ for s in suggestions],
        "anomaly_indexes": anomalies,
    }

    output_path = os.path.join(os.getcwd(), ANOMALY_LEARNING_CONFIG["learning_output_path"])
    _safe_mkdir(output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    logger.info("Anomaly learning generated %d threshold suggestions", len(suggestions))
    context["task_instance"].xcom_push(key="batch_5_anomaly_learning_result", value=payload)
    return payload
