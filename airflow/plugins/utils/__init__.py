"""Utilities for Airflow plugins."""

try:
    # Try relative import first (when run as a module)
    from .resilience import (
        SlackNotifier,
        on_failure_callback,
        on_retry_callback,
        on_success_callback,
        ErrorAggregator,
        skip_on_failure,
        retry_with_backoff,
        create_task_config_with_resilience,
        log_task_start,
        log_task_end,
    )
    from .monte_carlo_alerts import (
        MonteCarloAlertHandler,
        IncidentResponseHandler,
        create_mc_health_check_task,
    )
    from .observability_dashboards import (
        collect_observability_snapshot,
        publish_grafana_dashboard,
        publish_datadog_metrics,
    )
    from .automated_remediation import run_automated_remediation
    from .anomaly_learning import learn_monitor_thresholds
except ImportError:
    # Fall back to absolute import (when run standalone)
    from resilience import (
        SlackNotifier,
        on_failure_callback,
        on_retry_callback,
        on_success_callback,
        ErrorAggregator,
        skip_on_failure,
        retry_with_backoff,
        create_task_config_with_resilience,
        log_task_start,
        log_task_end,
    )
    from monte_carlo_alerts import (
        MonteCarloAlertHandler,
        IncidentResponseHandler,
        create_mc_health_check_task,
    )
    from observability_dashboards import (
        collect_observability_snapshot,
        publish_grafana_dashboard,
        publish_datadog_metrics,
    )
    from automated_remediation import run_automated_remediation
    from anomaly_learning import learn_monitor_thresholds

__all__ = [
    "SlackNotifier",
    "on_failure_callback",
    "on_retry_callback",
    "on_success_callback",
    "ErrorAggregator",
    "skip_on_failure",
    "retry_with_backoff",
    "create_task_config_with_resilience",
    "log_task_start",
    "log_task_end",
    "MonteCarloAlertHandler",
    "IncidentResponseHandler",
    "create_mc_health_check_task",
    "collect_observability_snapshot",
    "publish_grafana_dashboard",
    "publish_datadog_metrics",
    "run_automated_remediation",
    "learn_monitor_thresholds",
]
