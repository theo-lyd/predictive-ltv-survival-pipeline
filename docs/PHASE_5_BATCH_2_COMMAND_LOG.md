# Phase 5 Batch 2 Command Log

```bash
# Add executive storytelling config and utility
# (file creation via editor/tooling)

# DAG parse check
cd airflow
source ../.venv/bin/activate
export AIRFLOW_HOME=$(pwd)
python dags/ltv_pipeline_dag.py

# Confirm task registration
airflow tasks list ltv_survival_pipeline | grep generate_daily_ai_summary
```
