# Phase 4 Batch 5 Command Log

## 1. Validate DAG Registration

```bash
cd /workspaces/predictive-ltv-survival-pipeline/airflow
source ../.venv/bin/activate
export AIRFLOW_HOME=$(pwd)
airflow tasks list ltv_survival_pipeline
```

Expected: Batch 5 tasks listed under phase_5_observability.*

## 2. Test Snapshot Task

```bash
airflow tasks test ltv_survival_pipeline phase_5_observability.collect_observability_snapshot 2026-04-07
```

## 3. Test Grafana Artifact Publication

```bash
airflow tasks test ltv_survival_pipeline phase_5_observability.publish_grafana_dashboard 2026-04-07
```

Expected output artifact:
- airflow/artifacts/grafana/ltv_pipeline_dashboard.json

## 4. Test Datadog Emission

```bash
# Set API key before task test
airflow variables set DATADOG_API_KEY <your_api_key>
airflow tasks test ltv_survival_pipeline phase_5_observability.publish_datadog_metrics 2026-04-07
```

If key is missing, task logs payload and exits safely.

## 5. Test Automated Remediation

```bash
airflow tasks test ltv_survival_pipeline phase_5_observability.run_automated_remediation 2026-04-07
```

## 6. Test Anomaly Learning

```bash
# Set monitor variable example
airflow variables set MC_MONITOR_ID_BRONZE_CUSTOMERS <monitor_id>
airflow tasks test ltv_survival_pipeline phase_5_observability.run_anomaly_learning 2026-04-07
```

Expected output artifact:
- airflow/artifacts/anomaly-learning/monitor-thresholds.json

## 7. Verify Full Task Inventory

```bash
airflow tasks list ltv_survival_pipeline | grep phase_5_observability
```

Expected tasks:
- phase_5_observability.collect_observability_snapshot
- phase_5_observability.publish_grafana_dashboard
- phase_5_observability.publish_datadog_metrics
- phase_5_observability.run_automated_remediation
- phase_5_observability.run_anomaly_learning
