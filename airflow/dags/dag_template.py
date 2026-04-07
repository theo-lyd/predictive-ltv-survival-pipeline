"""
Base DAG Template for Predictive LTV Survival Pipeline

This template demonstrates Airflow best practices and naming conventions
for the predictive-ltv-survival-pipeline project.

Key Principles:
1. Single responsibility per DAG (one logical workflow)
2. Idempotent tasks (can be safely re-run)
3. Clear task naming: `{domain}_{action}_{target}`
4. Explicit error handling and retry policies
5. Task dependencies documented with comments
6. All configuration externalizable (no hardcoding)

Usage:
    Copy this template to create new DAGs:
    cp airflow/dags/dag_template.py airflow/dags/dag_name.py
    Customize DAG name, schedule, and tasks
"""

from datetime import datetime, timedelta
from typing import Any, Dict

from airflow import DAG
from airflow.models import Variable
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup


# ============================================================================
# DAG Configuration
# ============================================================================

# Configuration keys (externalizable via Airflow Variables)
OWNER = "analytics_engineering"
CONTACT_EMAIL = "analytics@predictive-ltv-pipeline.local"
ALERT_EMAIL = ["alerts@predictive-ltv-pipeline.local"]

# DAG metadata
dag_id = "ltv_pipeline_template"
dag_description = """
Template DAG demonstrating best practices for the predictive-ltv-survival pipeline.

This DAG is meant to be copied and customized for specific workflows.
"""

# Schedule and timing
schedule = "@daily"  # Daily at midnight UTC (replaces deprecated schedule_interval)
start_date = datetime(2024, 1, 1)
catchup = False  # Don't backfill missing runs

# Default task arguments (inherited by all tasks)
default_args = {
    "owner": OWNER,
    "depends_on_past": False,
    "email": ALERT_EMAIL,
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 2,  # Retry failed tasks up to 2 times
    "retry_delay": timedelta(minutes=5),  # Wait 5 minutes between retries
    "retry_exponential_backoff": True,  # Exponential backoff: 5m, 10m, 20m, ...
    "max_retry_delay": timedelta(minutes=60),  # Cap at 60 minutes
    "execution_timeout": timedelta(hours=2),  # Kill task if running >2 hours
    "queue": "default",  # Queue/worker pool
    "pool": "default_pool",  # Task pool (limits concurrency)
    "pool_slots": 1,  # How many slots this task consumes
}

# DAG-level parameters
dag_params = {
    "observation_date": datetime.now().strftime("%Y-%m-%d"),
    "dbt_select": "+models/staging",  # dbt selection syntax
    "airbyte_connection_id": "airbyte_default",
}


# ============================================================================
# DAG Definition
# ============================================================================

with DAG(
    dag_id=dag_id,
    default_args=default_args,
    description=dag_description,
    schedule=schedule,
    start_date=start_date,
    catchup=catchup,
    tags=["ltv", "pipeline", "production"],
    max_active_runs=1,  # Max 1 active run at a time
) as dag:
    """
    DAG: {{ dag_id }}
    
    Purpose: Template for creating new Airflow DAGs in the predictive-ltv-survival pipeline.
    
    Task Flow:
        start_task
            ↓
        [task_group_a] (parallel subtasks)
            ↓
        [task_group_b] (sequential subtasks)
            ↓
        end_task
    """

    # ========================================================================
    # Example: Start Task (Marker/Placeholder)
    # ========================================================================
    
    start_task = BashOperator(
        task_id="start",
        bash_command="echo 'Starting DAG execution' && date",
        do_xcom_push=True,  # Push output to XCom for downstream tasks
    )

    # ========================================================================
    # Example: Task Group A (Parallel Subtasks)
    # ========================================================================
    
    with TaskGroup("task_group_a", tooltip="Parallel tasks") as task_group_a:
        """
        Group of tasks that run in parallel.
        
        Why TaskGroup?
        - Visual organization in Airflow UI
        - Shared error handling
        - Cleaner DAG graph
        """
        
        task_a1 = BashOperator(
            task_id="subtask_1",
            bash_command="echo 'Subtask A1' && sleep 5",
        )
        
        task_a2 = BashOperator(
            task_id="subtask_2",
            bash_command="echo 'Subtask A2' && sleep 5",
        )
        
        # Subtasks run in parallel (no explicit dependency)
        [task_a1, task_a2]

    # ========================================================================
    # Example: Task Group B (Sequential Subtasks)
    # ========================================================================
    
    def log_task_context(**context) -> Dict[str, Any]:
        """
        Python operator example: logs task execution context.
        
        Args:
            **context: Airflow task context (execution_date, ti, ds, etc.)
        
        Returns:
            Dictionary of values to push to XCom
        """
        ti = context["task_instance"]
        execution_date = context["execution_date"]
        
        execution_info = {
            "dag_id": ti.dag_id,
            "task_id": ti.task_id,
            "execution_date": str(execution_date),
            "try_number": ti.try_number,
        }
        
        print(f"Task execution info: {execution_info}")
        
        # Push to XCom for downstream tasks
        ti.xcom_push(key="execution_info", value=execution_info)
        
        return execution_info

    with TaskGroup("task_group_b", tooltip="Sequential tasks") as task_group_b:
        """
        Group of tasks that run sequentially (dependencies explicit).
        """
        
        task_b1 = PythonOperator(
            task_id="log_context",
            python_callable=log_task_context,
            provide_context=True,
        )
        
        task_b2 = BashOperator(
            task_id="next_step",
            bash_command="echo 'Task B2' && sleep 2",
        )
        
        # Explicit sequential dependency
        task_b1 >> task_b2

    # ========================================================================
    # Example: End Task (Marker/Placeholder)
    # ========================================================================
    
    end_task = BashOperator(
        task_id="end",
        bash_command="echo 'DAG execution complete' && date",
        trigger_rule="all_done",  # Run even if previous tasks fail
    )

    # ========================================================================
    # DAG Dependencies (Task Flow)
    # ========================================================================
    
    # start_task → task_group_a → task_group_b → end_task
    start_task >> task_group_a >> task_group_b >> end_task


# ============================================================================
# DAG Documentation
# ============================================================================

dag.doc_md = """
# {{ dag_id }} DAG

## Overview
This is a template DAG demonstrating best practices for the predictive-ltv-survival pipeline.

## Key Features
- **Retry Logic**: Exponential backoff (2 retries, max 60min)
- **Error Handling**: Email alerts on failure
- **Task Groups**: Organized parallel/sequential execution
- **Idempotency**: Safe to re-run any task without side effects
- **Timeout**: 2-hour execution limit per task

## Parameters
- observation_date: Current date ({{ params.observation_date }})
- dbt_select: dbt selection syntax ({{ params.dbt_select }})

## SLA & Monitoring
- SLA: Tasks should complete within their execution_timeout
- Failure notifications: Sent to {{ default_args.email }}
- Max active runs: {{ max_active_runs }}

## Runbook
If this DAG fails:
1. Check Airflow logs: `/airflow/logs/{{ dag_id }}/`
2. Identify failed task from DAG UI
3. Check task logs for root cause
4. Re-run failed task with `airflow dags test` or manual trigger
5. Escalate to on-call if corrective action needed (see RUNBOOK.md)
"""

# Make documentation accessible in DAG UI
for task in dag.tasks:
    task.doc_md = f"""
    ## Task: {task.task_id}
    
    Type: {task.__class__.__name__}
    Owner: {OWNER}
    Timeout: {default_args['execution_timeout']}
    Retries: {default_args['retries']}
    
    Reference: See RUNBOOK.md for troubleshooting.
    """
