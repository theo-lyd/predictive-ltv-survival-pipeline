"""
Timeout and Retry Policy Configuration for Phase 4 Batch 3.

Defines resilience settings for different task types in the pipeline.
"""

from datetime import timedelta

# ============================================================================
# Task-Type Retry Policies
# ============================================================================

RETRY_POLICIES = {
    # Airbyte sync: More lenient (external system may be temporarily down)
    "airbyte": {
        "retries": 3,
        "retry_delay": timedelta(minutes=2),
        "retry_exponential_backoff": True,
        "max_retry_delay": timedelta(hours=1),
        "pool": "airbyte_pool",
        "pool_slots": 1,
    },
    
    # dbt transformations: Standard retry (usually deterministic)
    "dbt": {
        "retries": 2,
        "retry_delay": timedelta(minutes=1),
        "retry_exponential_backoff": True,
        "max_retry_delay": timedelta(minutes=30),
        "pool": "dbt_pool",
        "pool_slots": 1,
    },
    
    # Sensors: More retries (may need to wait for data)
    "sensor": {
        "retries": 5,
        "retry_delay": timedelta(seconds=30),
        "retry_exponential_backoff": False,  # Linear backoff for sensors
        "max_retry_delay": timedelta(minutes=5),
        "poke_interval": 30,
        "timeout": 3600,  # 1 hour max wait
    },
    
    # Python ingestion: Standard retry
    "python": {
        "retries": 2,
        "retry_delay": timedelta(minutes=1),
        "retry_exponential_backoff": True,
        "max_retry_delay": timedelta(minutes=30),
    },
    
    # Bash commands: Lenient (external tools may be slow)
    "bash": {
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
        "retry_exponential_backoff": True,
        "max_retry_delay": timedelta(minutes=30),
    },
}

# ============================================================================
# Task-Type Timeout Policies
# ============================================================================

TIMEOUT_POLICIES = {
    # Airbyte sync: 1 hour max (includes data transfer time)
    "airbyte": timedelta(hours=1),
    
    # dbt: 2 hours max (large models can be slow)
    "dbt": timedelta(hours=2),
    
    # dbt tests: 1 hour max (should be fast)
    "dbt_test": timedelta(hours=1),
    
    # Sensors: Already have internal timeout; execution_timeout is safety net
    "sensor": timedelta(hours=2),
    
    # Python ingestion: 2 hours (PySpark jobs can be slow)
    "python": timedelta(hours=2),
    
    # Bash: 1 hour
    "bash": timedelta(hours=1),
}

# ============================================================================
# SLA (Service Level Agreement) Definitions
# ============================================================================

SLAS = {
    # Expected Bronze ingestion to complete
    "phase_2_bronze": timedelta(minutes=30),
    
    # Expected Silver transforms to complete
    "phase_3_silver": timedelta(minutes=45),
    
    # Expected Gold models to complete
    "phase_4_gold": timedelta(minutes=45),
    
    # Full DAG SLA from start to finish
    "full_dag": timedelta(hours=2),
}

# ============================================================================
# Pool Definitions
# ============================================================================

POOLS = {
    "airbyte_pool": {
        "description": "Airbyte sync concurrency limiter",
        "slots": 1,  # Only 1 Airbyte sync at a time (shared connection)
    },
    "dbt_pool": {
        "description": "dbt execution concurrency limiter",
        "slots": 2,  # Max 2 dbt tasks in parallel (resource constrained)
    },
    "sensor_pool": {
        "description": "Sensor concurrency limiter",
        "slots": 5,  # Sensors are lightweight; can run many in parallel
    },
}

# ============================================================================
# Escalation & Alerting Rules
# ============================================================================

ESCALATION_RULES = {
    "critical_tasks": [
        "phase_4_gold.run_gold_models",  # If Gold models fail, full pipeline is blocked
        "phase_4_gold.run_gold_tests",   # If tests fail, needs manual review
    ],
    
    "max_retries_before_alert": 1,  # Alert after 1st retry attempt
    
    "alert_channels": {
        "default": "slack",  # Default: Slack
        "critical": ["slack", "email"],  # Critical: Slack + email
    },
    
    "slack_channel": "#data-alerts",
    "email_recipients": ["data-team@company.com"],
}

# ============================================================================
# Example Usage in DAG
# ============================================================================

"""
from airflow import DAG
from airflow.operators.bash import BashOperator
from phase_4_batch_3_resilience_config import RETRY_POLICIES, TIMEOUT_POLICIES

# Get dbt retry policy
dbt_retry_config = RETRY_POLICIES["dbt"]
dbt_timeout = TIMEOUT_POLICIES["dbt"]

task = BashOperator(
    task_id="run_silver",
    bash_command="dbt run --select path:models/staging",
    retries=dbt_retry_config["retries"],
    retry_delay=dbt_retry_config["retry_delay"],
    retry_exponential_backoff=dbt_retry_config["retry_exponential_backoff"],
    max_retry_delay=dbt_retry_config["max_retry_delay"],
    execution_timeout=dbt_timeout,
    pool=dbt_retry_config.get("pool", "default_pool"),
    pool_slots=dbt_retry_config.get("pool_slots", 1),
)
"""
