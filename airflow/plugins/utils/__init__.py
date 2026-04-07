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
]
