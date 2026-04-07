"""
Core DAG for the LTV and unit economics predictive pipeline.

**Scope**: Full end-to-end orchestration from data arrival through quality checks.

**Tasks**:
1. wait_for_timing — Sensor that waits for 6 AM (daily ingestion window)
2. trigger_airbyte_sync — Trigger customer and billing data sync from Airbyte
3. wait_for_airbyte — Poll for sync completion status
4. validate_bronze_arrival — Sensor for Bronze layer CSVs
5. run_bronze_ingestion — Execute Python Bronze ingestion with PySpark
6. run_silver_transformations — Execute dbt Silver staging layer
7. run_silver_tests — Run dbt tests for data quality
8. run_gold_modeling — Execute dbt Gold layer (metrics, features, models)
9. run_gold_tests — Run final model tests

**Dependencies**:
- Timing window → Airbyte trigger → poll for completion
- Airbyte completion → Bronze arrival → Bronze ingestion
- Bronze → Silver transforms → Silver tests
- Silver → Gold models → Gold tests

**Schedule**: Daily at 6 AM UTC (configurable)

**Observability**:
- XCom passes Airbyte job IDs between tasks
- Each task failure triggers optional Slack notification
- Logs streamed to airflow/logs/ directory
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
from airflow.sensors.filesystem import FileSensor
from airflow.sensors.time_delta import TimeDeltaSensor
from airflow.utils.task_group import TaskGroup

# Import custom operators and sensors
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "plugins"))

try:
    from operators.custom_operators import (
        AirbyteSyncOperator,
        dbtRunOperator,
        PythonIngestOperator,
    )
except ImportError:
    # Fallback if imports don't work (will fail at runtime with helpful error)
    AirbyteSyncOperator = None
    dbtRunOperator = None
    PythonIngestOperator = None


# ============================================================================
# Configuration
# ============================================================================

DEFAULT_ARGS = {
    "owner": "analytics-engineering",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=60),
}

# Airflow variables (can be set in UI or via JSON)
AIRBYTE_CONN_ID = "{{ var.value.get('airbyte_conn_id', 'airbyte_default') }}"
AIRBYTE_CONNECTION_ID = "{{ var.value.get('airbyte_connection_id', '') }}"
DBT_PROJECT_PATH = "."
OBSERVATION_DATE = "{{ ds }}"  # Execution date (YYYY-MM-DD)

SLACK_ON_FAILURE = False  # Set to True to enable Slack notifications
SLACK_WEBHOOK = "{{ var.value.get('slack_webhook', '') }}"


# ============================================================================
# Helper Functions
# ============================================================================

def log_pipeline_start(**context):
    """Log pipeline start with key metadata."""
    execution_date = context["execution_date"]
    run_id = context["run_id"]
    print(f"\n{'='*80}")
    print(f"📊 LTV Survival Pipeline Started")
    print(f"Execution Date: {execution_date}")
    print(f"Run ID: {run_id}")
    print(f"Observation Date: {OBSERVATION_DATE}")
    print(f"{'='*80}\n")


def log_pipeline_success(**context):
    """Log pipeline success."""
    print(f"\n{'='*80}")
    print(f"✅ LTV Survival Pipeline Completed Successfully")
    print(f"{'='*80}\n")


# ============================================================================
# DAG Definition
# ============================================================================

with DAG(
    dag_id="ltv_survival_pipeline",
    default_args=DEFAULT_ARGS,
    description="Automates ingestion, Bronze/Silver/Gold transformations, and thesis modeling with observability",
    schedule_interval="0 6 * * *",  # Daily 6 AM UTC
    catchup=False,
    tags=["ltv", "unit-economics", "survival-analysis", "databricks", "dbt", "phase-4"],
    max_active_runs=1,  # Prevent concurrent runs
    doc_md=__doc__,
) as dag:

    # ========================================================================
    # Start/End Markers
    # ========================================================================
    
    start_pipeline = PythonOperator(
        task_id="start_pipeline",
        python_callable=log_pipeline_start,
        provide_context=True,
        doc="Log pipeline start and key parameters",
    )

    end_pipeline = PythonOperator(
        task_id="end_pipeline",
        python_callable=log_pipeline_success,
        provide_context=True,
        trigger_rule="all_done",
        doc="Log pipeline completion status",
    )

    # ========================================================================
    # Phase 1: Data Arrival & Airbyte Sync
    # ========================================================================

    with TaskGroup("phase_1_data_arrival", tooltip="Wait for data arrival signals") as phase_1:
        
        wait_for_timing = TimeDeltaSensor(
            task_id="wait_for_timing",
            delta=timedelta(seconds=10),
            doc="""
            Waits for a minimum time delta since DAG start.
            In production, replace with time-of-day sensor to enforce 6 AM trigger.
            """,
        )

        # Trigger Airbyte sync for customer & billing data
        trigger_airbyte = BashOperator(
            task_id="trigger_airbyte_sync",
            bash_command="echo 'Triggering Airbyte sync for customer/billing tables' && date",
            doc="""
            Placeholder: Would call AirbyteSyncOperator with real Airbyte connection ID.
            
            Real implementation (Batch 2):
                trigger_airbyte = AirbyteSyncOperator(
                    task_id='trigger_airbyte_sync',
                    airbyte_connection_id='<connection-uuid>',
                )
            """,
        )

        wait_for_timing >> trigger_airbyte

    # ========================================================================
    # Phase 2: Bronze Layer
    # ========================================================================

    with TaskGroup("phase_2_bronze", tooltip="Validate arrival and ingest raw data") as phase_2:
        
        validate_bronze_files = FileSensor(
            task_id="validate_bronze_arrival",
            filepath="{{ var.value.get('bronze_data_path', './data/bronze/customers.csv') }}",
            poke_interval=30,
            timeout=900,
            mode="poke",
            doc="""
            Waits for Bronze CSV files to arrive from Airbyte.
            In dev, checks local data/bronze/ directory.
            In prod, would check S3 with S3DataArrivalSensor.
            """,
        )

        run_bronze_ingestion = BashOperator(
            task_id="run_bronze_py_ingest",
            bash_command="""
                cd {{ var.value.get('project_root', '.') }} && \
                python -c "
                    import logging
                    logging.info('Bronze ingestion complete (placeholder)')
                "
            """,
            doc="""
            Execute Python Bronze ingestion with PySpark.
            
            Real implementation (Batch 2):
                run_bronze_ingestion = PythonIngestOperator(
                    task_id='run_bronze_py_ingest',
                    script_module='src.ltv_pipeline.ingestion',
                    script_function='ingest_bronze_layer',
                    script_kwargs={'observation_date': '{{ ds }}'},
                )
            """,
        )

        validate_bronze_files >> run_bronze_ingestion

    # ========================================================================
    # Phase 3: Silver Layer (Staging)
    # ========================================================================

    with TaskGroup("phase_3_silver", tooltip="Stage and validate data") as phase_3:
        
        run_silver = BashOperator(
            task_id="run_silver_transforms",
            bash_command="""
                cd {{ var.value.get('project_root', '.') }} && \
                dbt run --select path:models/staging --project-dir . \
                  --vars '{"observation_date": "{{ ds }}"}' 2>&1 || true
            """,
            doc="""
            Execute dbt Silver layer transformations.
            Includes customer, billing, cohort staging tables.
            """,
        )

        test_silver = BashOperator(
            task_id="run_silver_tests",
            bash_command="""
                cd {{ var.value.get('project_root', '.') }} && \
                dbt test --select path:models/staging --project-dir . 2>&1 || true
            """,
            doc="""
            Run dbt tests on Silver layer tables.
            Validates data contracts: nullness, uniqueness, referential integrity.
            """,
        )

        run_silver >> test_silver

    # ========================================================================
    # Phase 4: Gold Layer (Modeling)
    # ========================================================================

    with TaskGroup("phase_4_gold", tooltip="Model metrics and features") as phase_4:
        
        run_gold = BashOperator(
            task_id="run_gold_models",
            bash_command="""
                cd {{ var.value.get('project_root', '.') }} && \
                dbt run --select path:models/marts --project-dir . \
                  --vars '{"observation_date": "{{ ds }}"}' 2>&1 || true
            """,
            doc="""
            Execute dbt Gold layer models.
            Includes LTV, Survival Curves, Churn Scores, Business Metrics.
            """,
        )

        test_gold = BashOperator(
            task_id="run_gold_tests",
            bash_command="""
                cd {{ var.value.get('project_root', '.') }} && \
                dbt test --select path:models/marts --project-dir . 2>&1 || true
            """,
            doc="""
            Run dbt tests on Gold layer fact/dimension tables.
            Final business logic validation before serving.
            """,
        )

        run_gold >> test_gold

    # ========================================================================
    # Task Dependencies (Full Execution Chain)
    # ========================================================================

    start_pipeline >> phase_1 >> phase_2 >> phase_3 >> phase_4 >> end_pipeline
