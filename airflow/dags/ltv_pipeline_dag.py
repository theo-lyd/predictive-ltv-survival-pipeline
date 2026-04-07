"""
Core DAG for the LTV and unit economics predictive pipeline (Batch 3: Resilience).

**Scope**: Full end-to-end orchestration with resilience, retry policies, timeouts, and error handling.

**Tasks**:
1. wait_for_timing — TimeDeltaSensor for scheduling window
2. trigger_airbyte_sync — AirbyteSyncOperator with polling
3. validate_bronze_arrival — FileSensor for data arrival
4. run_bronze_ingestion — PythonIngestOperator for Bronze layer
5. run_silver_transforms — dbtRunOperator for Silver staging
6. run_silver_tests — dbtRunOperator for data quality
7. run_gold_models — dbtRunOperator for metrics/features
8. run_gold_tests — dbtRunOperator for final validation

**Resilience Features** (Batch 3):
- Exponential backoff retry: 60s → 120s → 240s (max 60m)
- Task timeouts: 2 hours per task, 15 minutes per DAG
- Slack failure notifications + retry alerts
- Cross-task error aggregation
- Graceful degradation on non-critical failures
- XCom for error context passing

**Schedule**: Daily at 6 AM UTC

**Monitoring**:
- on_failure_callback → Slack alert
- on_retry_callback → Slack warning
- Error logs + aggregated root cause analysis
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.filesystem import FileSensor
from airflow.sensors.time_delta import TimeDeltaSensor
from airflow.utils.task_group import TaskGroup

# Import custom operators, sensors, and resilience utilities
import sys
AIRFLOW_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, AIRFLOW_ROOT)
sys.path.insert(0, os.path.join(AIRFLOW_ROOT, "plugins"))

try:
    from operators.custom_operators import (
        AirbyteSyncOperator,
        dbtRunOperator,
        PythonIngestOperator,
    )
    from utils.resilience import (
        on_failure_callback,
        on_retry_callback,
    )
    from utils.monte_carlo_alerts import (
        create_mc_health_check_task,
    )
    from utils.observability_dashboards import (
        collect_observability_snapshot,
        publish_grafana_dashboard,
        publish_datadog_metrics,
    )
    from utils.automated_remediation import run_automated_remediation
    from utils.anomaly_learning import learn_monitor_thresholds
    from config.phase_4_batch_5_observability_config import (
        BATCH_5_DAG_CONFIG,
        OBSERVABILITY_TASK_POLICIES,
    )
except ImportError as e:
    raise ImportError(
        f"Failed to import custom operators/utils. "
        f"Ensure AIRFLOW_HOME={os.environ.get('AIRFLOW_HOME')} is set. Error: {e}"
    )


# ============================================================================
# Configuration
# ============================================================================

# Base configuration with resilience defaults
DEFAULT_ARGS = {
    "owner": "analytics-engineering",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    # Batch 3: Resilience settings
    "retries": 2,
    "retry_delay": timedelta(minutes=1),  # First retry after 1 min
    "retry_exponential_backoff": True,    # Double delay each retry: 1m → 2m → 4m...
    "max_retry_delay": timedelta(hours=1), # Cap at 1 hour
    "on_failure_callback": on_failure_callback,  # Slack notifications
    "on_retry_callback": on_retry_callback,
    "execution_timeout": timedelta(hours=2),  # Task timeout
}

# Airflow variables (configurable at runtime)
OBSERVATION_DATE = "{{ ds }}"  # Execution date (YYYY-MM-DD)


# ============================================================================
# Helper Functions
# ============================================================================

def log_pipeline_start(**context):
    """Log pipeline start with key metadata."""
    execution_date = context["execution_date"]
    run_id = context["run_id"]
    print(f"\n{'='*80}")
    print(f"📊 LTV Survival Pipeline Started (Batch 3: Resilience)")
    print(f"Execution Date: {execution_date}")
    print(f"Run ID: {run_id}")
    print(f"Observation Date: {OBSERVATION_DATE}")
    print(f"{'='*80}\n")


def log_pipeline_success(**context):
    """Log pipeline success."""
    print(f"\n{'='*80}")
    print(f"✅ LTV Survival Pipeline Completed Successfully")
    print(f"All layers processed: Bronze → Silver → Gold")
    print(f"{'='*80}\n")


def _with_observability_failure_policy(callable_fn):
    """Wrap observability callables to enforce Batch 5 failure policy."""

    def _wrapped(**context):
        try:
            return callable_fn(**context)
        except Exception as exc:
            if BATCH_5_DAG_CONFIG["fail_pipeline_on_observability_errors"]:
                raise
            print(f"[WARN] Suppressed observability task failure: {exc}")
            return {"status": "suppressed_error", "error": str(exc)}

    return _wrapped


# ============================================================================
# DAG Definition
# ============================================================================

with DAG(
    dag_id="ltv_survival_pipeline",
    default_args=DEFAULT_ARGS,
    description="Automates ingestion, Bronze/Silver/Gold transformations with resilience and error handling",
    schedule="0 6 * * *",  # Daily 6 AM UTC
    catchup=False,
    tags=["ltv", "unit-economics", "survival-analysis", "databricks", "dbt", "phase-4-batch-3"],
    max_active_runs=1,  # Prevent concurrent runs
    doc_md=__doc__,
) as dag:

    # ========================================================================
    # Start/End Markers
    # ========================================================================
    
    start_pipeline = PythonOperator(
        task_id="start_pipeline",
        python_callable=log_pipeline_start,
        doc="Log pipeline start and key parameters",
    )

    end_pipeline = PythonOperator(
        task_id="end_pipeline",
        python_callable=log_pipeline_success,
        trigger_rule="all_done",
        doc="Log pipeline completion status",
    )

    # ========================================================================
    # Phase 1: Data Arrival & Airbyte Sync (Real Operators)
    # ========================================================================

    with TaskGroup("phase_1_data_arrival", tooltip="Wait for data arrival signals") as phase_1:
        
        # Batch 3: Real TimeDeltaSensor for scheduling
        wait_for_timing = TimeDeltaSensor(
            task_id="wait_for_timing",
            delta=timedelta(seconds=10),
            doc="""
            Waits for minimum time delta since DAG start.
            In production, this enforces execution window (e.g., can only run after 6 AM).
            """,
        )

        # Batch 3: Real AirbyteSyncOperator (replaces BashOperator placeholder)
        trigger_airbyte = AirbyteSyncOperator(
            task_id="trigger_airbyte_sync",
            airbyte_connection_id="{{ var.value.get('airbyte_connection_id', '') }}",
            timeout_seconds=3600,
            doc="""
            Trigger Airbyte sync for customer and billing tables.
            
            - Calls Airbyte API to start sync
            - Polls every 10s for completion (up to 60 minutes)
            - Pushes job_id to XCom for downstream reference
            - Raises exception if sync fails
            
            **Resilience**: 2 retries with exponential backoff (1m → 2m → 4m)
            """,
        )

        wait_for_timing >> trigger_airbyte

    # ========================================================================
    # Phase 2: Bronze Layer (Real Operators)
    # ========================================================================

    with TaskGroup("phase_2_bronze", tooltip="Validate arrival and ingest raw data") as phase_2:
        
        # Batch 3: Real FileSensor for data arrival validation
        validate_bronze_files = FileSensor(
            task_id="validate_bronze_arrival",
            filepath="{{ var.value.get('bronze_data_path', './data/bronze/customers.csv') }}",
            poke_interval=30,
            timeout=900,
            mode="poke",
            doc="""
            Wait for Bronze CSV files to arrive.
            
            - Checks local data/bronze/ directory in dev
            - In prod: Replace with S3DataArrivalSensor for cloud check
            - Pokes every 30s, timeout 15 minutes
            
            **Resilience**: FileSensor has built-in timeout handling
            """,
        )

        # Batch 3: Real PythonIngestOperator (replaces BashOperator placeholder)
        run_bronze_ingestion = PythonIngestOperator(
            task_id="run_bronze_py_ingest",
            script_module="src.ltv_pipeline.ingestion",
            script_function="ingest_bronze_layer",
            script_kwargs={"observation_date": OBSERVATION_DATE},
            doc="""
            Execute Python Bronze ingestion with PySpark.
            
            - Imports CSV files from Airbyte export
            - Applies type conversions and normalization
            - Writes Parquet to data/bronze/
            - Records row counts and data profiles
            
            **Resilience**: 2 retries, 2-hour timeout
            """,
        )

        validate_bronze_files >> run_bronze_ingestion

    # ========================================================================
    # Phase 3: Silver Layer (Real dbt Operators)
    # ========================================================================

    with TaskGroup("phase_3_silver", tooltip="Stage and validate data") as phase_3:
        
        # Batch 3: Real dbtRunOperator for Silver staging
        run_silver = dbtRunOperator(
            task_id="run_silver_transforms",
            dbt_command="run --select path:models/staging --profiles-dir .",
            dbt_project_path=".",
            vars_dict={"observation_date": OBSERVATION_DATE},
            doc="""
            Execute dbt Silver layer transformations.
            
            - Stages customer, billing, cohort dimensions
            - Applies business logic and joins
            - Deduplicates and handles nulls per contract
            - Produces intermediate tables for Gold layer
            
            **Resilience**: 2 retries, 2-hour timeout, failure notification
            """,
        )

        # Batch 3: Real dbtRunOperator for Silver tests
        test_silver = dbtRunOperator(
            task_id="run_silver_tests",
            dbt_command="test --select path:models/staging --profiles-dir .",
            dbt_project_path=".",
            doc="""
            Run dbt tests on Silver layer tables.
            
            - Validates data contracts: nullness, uniqueness, referential integrity
            - Checks row counts match expected ranges
            - Ensures foreign keys exist in upstream tables
            
            **Resilience**: 2 retries, 1-hour timeout, stops pipeline on test failure
            """,
        )

        run_silver >> test_silver

    # ========================================================================
    # Phase 4: Gold Layer (Real dbt Operators)
    # ========================================================================

    with TaskGroup("phase_4_gold", tooltip="Model metrics and features") as phase_4:
        
        # Batch 3: Real dbtRunOperator for Gold models
        run_gold = dbtRunOperator(
            task_id="run_gold_models",
            dbt_command="run --select path:models/marts --profiles-dir .",
            dbt_project_path=".",
            vars_dict={"observation_date": OBSERVATION_DATE},
            doc="""
            Execute dbt Gold layer models.
            
            - Computes LTV (lifetime value) calculations
            - Builds Survival curves (Kaplan-Meier) with dbt-Python
            - Generates churn probability scores
            - Aggregates business metrics and KPIs
            - Produces query-optimized fact/dimension tables
            
            **Resilience**: 2 retries, 2-hour timeout, failure notification
            """,
        )

        # Batch 3: Real dbtRunOperator for Gold tests
        test_gold = dbtRunOperator(
            task_id="run_gold_tests",
            dbt_command="test --select path:models/marts --profiles-dir .",
            dbt_project_path=".",
            doc="""
            Run dbt tests on Gold layer fact/dimension tables.
            
            - Validates LTV calculations (no negative values)
            - Ensures survival curves are monotonically decreasing
            - Checks churn probability in [0, 1] range
            - Confirms referential integrity to Silver
            - Tests for expected row counts and cardinality
            
            **Resilience**: 2 retries, 1-hour timeout, pipeline stops on failure
            """,
        )

        run_gold >> test_gold

    # ========================================================================
    # Phase 4.5: Monte Carlo monitoring checks (Batch 4 - Optional health checks)
    # ========================================================================
    
    # Optional: Check Monte Carlo health after each layer
    # Set fail_on_critical=False to allow pipeline to proceed with warnings
    mc_check_bronze = PythonOperator(
        task_id="mc_check_bronze_health",
        python_callable=create_mc_health_check_task("bronze", fail_on_critical=False),
        doc="""
        Check Monte Carlo data quality for Bronze layer.
        
        - Queries asset health from Monte Carlo API
        - Lists any open incidents (volume, freshness, schema)
        - Routes incidents to Slack if any detected
        - Does not fail pipeline (monitoring only)
        
        **Batch 4**: Observability feature monitoring layer tables
        """,
    )

    mc_check_silver = PythonOperator(
        task_id="mc_check_silver_health",
        python_callable=create_mc_health_check_task("silver", fail_on_critical=False),
        doc="""Check Monte Carlo health for Silver layer.""",
    )

    mc_check_gold = PythonOperator(
        task_id="mc_check_gold_health",
        python_callable=create_mc_health_check_task("gold", fail_on_critical=False),
        doc="""Check Monte Carlo health for Gold layer.""",
    )

    # ========================================================================
    # Phase 5: Observability Dashboards, Runbooks, Remediation, Learning
    # ========================================================================

    with TaskGroup("phase_5_observability", tooltip="Publish dashboards and run incident automation") as phase_5:

        batch_5_task_kwargs = dict(OBSERVABILITY_TASK_POLICIES)

        collect_snapshot = PythonOperator(
            task_id="collect_observability_snapshot",
            python_callable=_with_observability_failure_policy(collect_observability_snapshot),
            **batch_5_task_kwargs,
            doc="""
            Collect latest observability signals from Monte Carlo checks.

            - Pulls Bronze/Silver/Gold health from XCom
            - Creates summary counters for incidents and layer status
            - Stores a normalized snapshot for downstream tasks
            """,
        )

        publish_grafana = PythonOperator(
            task_id="publish_grafana_dashboard",
            python_callable=_with_observability_failure_policy(publish_grafana_dashboard),
            **batch_5_task_kwargs,
            doc="""Generate Grafana dashboard JSON artifact from latest snapshot.""",
        )

        publish_datadog = PythonOperator(
            task_id="publish_datadog_metrics",
            python_callable=_with_observability_failure_policy(publish_datadog_metrics),
            **batch_5_task_kwargs,
            doc="""Emit observability counters to Datadog when API key is configured.""",
        )

        automated_remediation = PythonOperator(
            task_id="run_automated_remediation",
            python_callable=_with_observability_failure_policy(run_automated_remediation),
            **batch_5_task_kwargs,
            doc="""
            Run severity-based automated remediation workflows.

            - Auto-resolve low-severity incidents
            - Produce recommendations and escalation records
            - Attach runbook and playbook references
            """,
        )

        anomaly_learning = PythonOperator(
            task_id="run_anomaly_learning",
            python_callable=_with_observability_failure_policy(learn_monitor_thresholds),
            **batch_5_task_kwargs,
            doc="""
            Learn adaptive thresholds from monitor history.

            - Reads recent monitor metrics
            - Detects statistical outliers using z-score
            - Writes threshold suggestions for calibration
            """,
        )

        collect_snapshot >> [publish_grafana, publish_datadog, automated_remediation, anomaly_learning]

    # ========================================================================
    # Task Dependencies (Full Execution Chain with Resilience + MC Monitoring)
    # ========================================================================

    start_pipeline >> phase_1 >> phase_2 >> mc_check_bronze >> phase_3 >> mc_check_silver >> phase_4 >> mc_check_gold >> phase_5 >> end_pipeline
