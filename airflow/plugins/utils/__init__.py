"""Utilities for Airflow plugins.

This package intentionally uses lazy imports so that modules that depend on
Apache Airflow are not imported during unrelated unit tests.
"""

from __future__ import annotations

from importlib import import_module


_EXPORT_MAP = {
    "SlackNotifier": ("utils.resilience", "SlackNotifier"),
    "on_failure_callback": ("utils.resilience", "on_failure_callback"),
    "on_retry_callback": ("utils.resilience", "on_retry_callback"),
    "on_success_callback": ("utils.resilience", "on_success_callback"),
    "ErrorAggregator": ("utils.resilience", "ErrorAggregator"),
    "skip_on_failure": ("utils.resilience", "skip_on_failure"),
    "retry_with_backoff": ("utils.resilience", "retry_with_backoff"),
    "create_task_config_with_resilience": (
        "utils.resilience",
        "create_task_config_with_resilience",
    ),
    "log_task_start": ("utils.resilience", "log_task_start"),
    "log_task_end": ("utils.resilience", "log_task_end"),
    "MonteCarloAlertHandler": ("utils.monte_carlo_alerts", "MonteCarloAlertHandler"),
    "IncidentResponseHandler": ("utils.monte_carlo_alerts", "IncidentResponseHandler"),
    "create_mc_health_check_task": ("utils.monte_carlo_alerts", "create_mc_health_check_task"),
    "collect_observability_snapshot": (
        "utils.observability_dashboards",
        "collect_observability_snapshot",
    ),
    "publish_grafana_dashboard": ("utils.observability_dashboards", "publish_grafana_dashboard"),
    "publish_datadog_metrics": ("utils.observability_dashboards", "publish_datadog_metrics"),
    "run_automated_remediation": ("utils.automated_remediation", "run_automated_remediation"),
    "learn_monitor_thresholds": ("utils.anomaly_learning", "learn_monitor_thresholds"),
    "generate_daily_ai_summary": ("utils.executive_storytelling", "generate_daily_ai_summary"),
}


__all__ = list(_EXPORT_MAP)


def __getattr__(name: str):
    if name not in _EXPORT_MAP:
        raise AttributeError(name)

    module_name, symbol_name = _EXPORT_MAP[name]
    module = import_module(module_name)
    value = getattr(module, symbol_name)
    globals()[name] = value
    return value
