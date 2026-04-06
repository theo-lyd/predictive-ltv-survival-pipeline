"""Airflow DAG scaffold for the LTV and unit economics pipeline."""

from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator


default_args = {
    "owner": "analytics-engineering",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}


with DAG(
    dag_id="ltv_survival_pipeline",
    default_args=default_args,
    description="Orchestrates ingestion, dbt transformations, and thesis modeling",
    schedule_interval="0 6 * * *",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ltv", "unit-economics", "dbt", "databricks"],
) as dag:
    detect_new_files = BashOperator(
        task_id="detect_new_files",
        bash_command='echo "Checking for new files in cloud storage"',
    )

    run_bronze_ingestion = BashOperator(
        task_id="run_bronze_ingestion",
        bash_command='python -m src.scripts.run_bronze_ingest --source data/raw --target data/bronze',
    )

    run_dbt_transformations = BashOperator(
        task_id="run_dbt_transformations",
        bash_command='dbt run --project-dir . && dbt test --project-dir .',
    )

    detect_new_files >> run_bronze_ingestion >> run_dbt_transformations
