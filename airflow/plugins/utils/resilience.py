"""
Resilience and error handling utilities for Airflow pipeline.

Provides callbacks, error handlers, and recovery patterns for task failures,
including Slack notifications, error aggregation, and retry logic.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any

import requests

try:
    from airflow.exceptions import AirflowException
    from airflow.models import Variable
    from airflow.utils.context import Context
except ModuleNotFoundError:

    class AirflowException(Exception):
        """Fallback exception when Airflow is not installed."""

    class Variable:  # type: ignore[override]
        """Fallback Variable shim for non-Airflow test environments."""

        @staticmethod
        def get(_key: str, default_var: Any = None):
            return default_var

    Context = dict[str, Any]


logger = logging.getLogger(__name__)


# ============================================================================
# Slack Notifications
# ============================================================================


class SlackNotifier:
    """Sends task failure and status notifications to Slack."""

    def __init__(self, webhook_url: str | None = None, channel: str | None = None):
        """
        Initialize Slack notifier.

        :param webhook_url: Slack webhook URL (or read from Airflow Variable 'slack_webhook')
        :param channel: Slack channel override (e.g., '#data-alerts')
        """
        self.webhook_url = webhook_url or Variable.get("slack_webhook", "")
        self.channel = channel or Variable.get("slack_channel", "#data-alerts")
        self.enabled = bool(self.webhook_url)

    def is_enabled(self) -> bool:
        """Check if Slack notifications are configured."""
        return self.enabled

    def send_message(self, message: dict[str, Any]) -> bool:
        """
        Send message to Slack.

        :param message: Slack message payload (blocks format)
        :return: True if successful
        """
        if not self.enabled:
            logger.warning("Slack webhook not configured; notifications disabled")
            return False

        try:
            response = requests.post(
                self.webhook_url,
                json=message,
                timeout=10,
            )
            response.raise_for_status()
            logger.info("Slack notification sent successfully")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send Slack notification: {str(e)}")
            return False

    def task_failure(self, context: Context) -> None:
        """
        Send task failure notification to Slack.

        :param context: Airflow task context
        """
        if not self.enabled:
            return

        task_instance = context["task_instance"]
        dag_id = task_instance.dag_id
        task_id = task_instance.task_id
        execution_date = context["execution_date"]
        exception = context.get("exception", "Unknown error")
        try_number = task_instance.try_number
        max_tries = task_instance.max_tries

        # Build message
        message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔴 Task Failure Alert",
                        "emoji": True,
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*DAG*\n{dag_id}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Task*\n{task_id}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Execution Date*\n{execution_date.strftime('%Y-%m-%d %H:%M:%S')}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Attempt*\n{try_number}/{max_tries}",
                        },
                    ],
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Error*\n```{str(exception)[:500]}```",
                    },
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Logs*\n<http://localhost:8080/log?dag_id={dag_id}&task_id={task_id}&execution_date={execution_date.isoformat()}|View in Airflow>",
                    },
                },
                {
                    "type": "divider",
                },
            ]
        }

        self.send_message(message)

    def task_retry(self, context: Context) -> None:
        """
        Send task retry notification to Slack.

        :param context: Airflow task context
        """
        if not self.enabled:
            return

        task_instance = context["task_instance"]
        dag_id = task_instance.dag_id
        task_id = task_instance.task_id
        try_number = task_instance.try_number
        max_tries = task_instance.max_tries

        message = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⚠️ *Task Retry* — {dag_id}.{task_id}\n"
                        f"Attempt {try_number} of {max_tries}. Retrying...",
                    },
                }
            ]
        }

        self.send_message(message)

    def task_success(self, context: Context) -> None:
        """
        Send task success notification to Slack (optional).

        :param context: Airflow task context
        """
        if not self.enabled or not Variable.get("slack_notify_success", False):
            return

        task_instance = context["task_instance"]
        dag_id = task_instance.dag_id
        task_id = task_instance.task_id

        message = {
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"✅ *Task Succeeded* — {dag_id}.{task_id}",
                    },
                }
            ]
        }

        self.send_message(message)


# ============================================================================
# Callback Functions (for use in DAG task definitions)
# ============================================================================


def on_failure_callback(context: Context) -> None:
    """
    Callback function for task failure.

    Called automatically by Airflow when a task fails.
    Sends Slack notification and logs error for debugging.

    :param context: Airflow task context
    """
    task_instance = context["task_instance"]

    logger.error(
        f"Task {task_instance.task_id} failed on attempt {task_instance.try_number}",
        exc_info=True,
    )

    # Send Slack notification
    notifier = SlackNotifier()
    notifier.task_failure(context)


def on_retry_callback(context: Context) -> None:
    """
    Callback function for task retry.

    Called automatically by Airflow when a task is retried.

    :param context: Airflow task context
    """
    task_instance = context["task_instance"]

    logger.warning(
        f"Task {task_instance.task_id} failed; retrying (attempt {task_instance.try_number})"
    )

    # Send Slack notification
    notifier = SlackNotifier()
    notifier.task_retry(context)


def on_success_callback(context: Context) -> None:
    """
    Callback function for task success.

    Called automatically by Airflow when a task succeeds (optional).

    :param context: Airflow task context
    """
    task_instance = context["task_instance"]
    logger.info(f"Task {task_instance.task_id} succeeded")

    # Optionally send Slack notification
    notifier = SlackNotifier()
    notifier.task_success(context)


# ============================================================================
# Error Aggregation & Recovery
# ============================================================================


class ErrorAggregator:
    """Collects and aggregates errors from multiple tasks for root cause analysis."""

    def __init__(self, dag_id: str, execution_date: str):
        self.dag_id = dag_id
        self.execution_date = execution_date
        self.errors: list[dict[str, Any]] = []

    def add_error(
        self,
        task_id: str,
        error_type: str,
        error_message: str,
        timestamp: str | None = None,
    ) -> None:
        """
        Add error to aggregator.

        :param task_id: Task that failed
        :param error_type: Category (e.g., 'timeout', 'retry_exhausted', 'exception')
        :param error_message: Details about error
        :param timestamp: When error occurred
        """
        timestamp = timestamp or datetime.utcnow().isoformat()
        self.errors.append(
            {
                "task_id": task_id,
                "error_type": error_type,
                "error_message": error_message,
                "timestamp": timestamp,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for storage/logging."""
        return {
            "dag_id": self.dag_id,
            "execution_date": self.execution_date,
            "error_count": len(self.errors),
            "errors": self.errors,
        }

    def to_json(self) -> str:
        """Convert to JSON for storage."""
        return json.dumps(self.to_dict(), indent=2)

    def should_escalate(self) -> bool:
        """
        Determine if error should be escalated to on-call engineer.

        :return: True if critical errors present
        """
        # Escalate if >2 retries exhausted or if any critical errors
        for error in self.errors:
            if error["error_type"] in {"retry_exhausted", "timeout", "critical"}:
                return True
        return False


# ============================================================================
# Recovery Patterns
# ============================================================================


def skip_on_failure(exception: Exception) -> bool:
    """
    Determine if task should be skipped (not cause DAG to fail).

    Return True to skip (continue to downstream), False to fail.

    Example use case: If optional data source is unavailable, skip that load.

    :param exception: Exception raised by task
    :return: True if should skip, False if should fail
    """
    # Example: Skip if data file not found (optional source)
    if "FileNotFoundError" in str(type(exception)):
        logger.warning(f"Skipping task due to missing file: {exception}")
        return True
    return False


def retry_with_backoff(
    attempt: int,
    max_attempts: int = 3,
    base_delay_seconds: int = 60,
    max_delay_seconds: int = 3600,
) -> timedelta:
    """
    Calculate retry delay with exponential backoff.

    Formula: delay = min(base_delay * (2 ^ attempt), max_delay)

    Example:
    - Attempt 1: 60s
    - Attempt 2: 120s
    - Attempt 3: 240s (capped at max_delay)

    :param attempt: Current retry attempt (0-indexed)
    :param max_attempts: Maximum retry attempts
    :param base_delay_seconds: Initial delay in seconds
    :param max_delay_seconds: Maximum delay in seconds
    :return: Delay as timedelta
    """
    delay_seconds = min(
        base_delay_seconds * (2**attempt),
        max_delay_seconds,
    )
    return timedelta(seconds=delay_seconds)


def create_task_config_with_resilience(
    base_config: dict[str, Any],
    task_type: str = "default",
    max_retries: int = 2,
    retry_delay_minutes: int = 5,
    timeout_hours: int = 2,
) -> dict[str, Any]:
    """
    Create task configuration with standard resilience settings.

    :param base_config: Base task configuration dict
    :param task_type: Task type (e.g., 'dbt', 'airbyte', 'sensor')
    :param max_retries: Number of retries
    :param retry_delay_minutes: Initial retry delay in minutes
    :param timeout_hours: Task timeout in hours
    :return: Updated config with resilience settings
    """
    config = base_config.copy()

    # Add resilience defaults
    config.setdefault("retries", max_retries)
    config.setdefault("retry_delay", timedelta(minutes=retry_delay_minutes))
    config.setdefault("retry_exponential_backoff", True)
    config.setdefault(
        "max_retry_delay",
        timedelta(hours=1),
    )
    config.setdefault("on_failure_callback", on_failure_callback)
    config.setdefault("on_retry_callback", on_retry_callback)
    config.setdefault("execution_timeout", timedelta(hours=timeout_hours))

    # Task-type-specific settings
    if task_type == "dbt":
        config.setdefault("pool", "dbt_pool")
        config.setdefault("pool_slots", 1)
    elif task_type == "airbyte":
        config.setdefault("pool", "airbyte_pool")
        config.setdefault("pool_slots", 1)
    elif task_type == "sensor":
        config.setdefault("poke_interval", 60)
        config.setdefault("timeout", 3600)

    return config


# ============================================================================
# Logging Utilities
# ============================================================================


def log_task_start(task_id: str, **kwargs: Any) -> None:
    """Log task start with context."""
    logger.info(f"\n{'='*80}")
    logger.info(f"🔧 Task Started: {task_id}")
    for key, value in kwargs.items():
        logger.info(f"  {key}: {value}")
    logger.info(f"{'='*80}\n")


def log_task_end(task_id: str, status: str = "completed", **kwargs: Any) -> None:
    """Log task end with status."""
    logger.info(f"\n{'='*80}")
    logger.info(f"✅ Task {status.title()}: {task_id}")
    for key, value in kwargs.items():
        logger.info(f"  {key}: {value}")
    logger.info(f"{'='*80}\n")
