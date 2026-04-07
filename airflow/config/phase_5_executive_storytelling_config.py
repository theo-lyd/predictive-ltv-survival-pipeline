"""Configuration for Phase 5 executive storytelling workflow."""

from datetime import timedelta

EXEC_SUMMARY_CONFIG = {
    "artifact_path": "airflow/artifacts/executive_storytelling/daily_summary.json",
    "use_llm": True,
    "llm_timeout_seconds": 20,
    "fallback_enabled": True,
    "max_prompt_chars": 4000,
}

EXEC_SUMMARY_TASK_POLICY = {
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=20),
    "execution_timeout": timedelta(minutes=15),
}
