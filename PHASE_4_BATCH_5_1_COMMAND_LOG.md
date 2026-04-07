# Phase 4 Batch 5.1 Command Log

## 1. Configure Airflow Variables

```bash
cd /workspaces/predictive-ltv-survival-pipeline/airflow
source ../.venv/bin/activate
export AIRFLOW_HOME=$(pwd)

python - <<'PY'
from airflow.models import Variable
from config.phase_4_batch_4_monte_carlo_config import VOLUME_MONITORS, FRESHNESS_MONITORS

Variable.set("DATADOG_API_KEY", "")
for key in list(VOLUME_MONITORS.keys()) + list(FRESHNESS_MONITORS.keys()):
    Variable.set(f"MC_MONITOR_ID_{key.upper()}", "")
print("Variables configured")
PY
```

## 2. Task-Level Tests for Batch 5

```bash
airflow tasks test ltv_survival_pipeline phase_5_observability.collect_observability_snapshot 2026-04-07
airflow tasks test ltv_survival_pipeline phase_5_observability.publish_grafana_dashboard 2026-04-07
airflow tasks test ltv_survival_pipeline phase_5_observability.publish_datadog_metrics 2026-04-07
airflow tasks test ltv_survival_pipeline phase_5_observability.run_automated_remediation 2026-04-07
airflow tasks test ltv_survival_pipeline phase_5_observability.run_anomaly_learning 2026-04-07
```

## 3. Unit Tests (Batch 5.1)

```bash
cd /workspaces/predictive-ltv-survival-pipeline
/workspaces/predictive-ltv-survival-pipeline/.venv/bin/python -m pytest -q tests/test_phase4_batch5_hardening.py
```

Expected: `5 passed`

## 4. Verify Sensor Plugin Warning Fix

```bash
cd /workspaces/predictive-ltv-survival-pipeline/airflow
source ../.venv/bin/activate
export AIRFLOW_HOME=$(pwd)

airflow tasks test ltv_survival_pipeline phase_5_observability.collect_observability_snapshot 2026-04-07 \
  2>&1 | grep -E "Failed to import plugin|poke_mode_only|Marking task as SUCCESS"
```

Expected:
- No `Failed to import plugin ... sensors`
- Task marked as SUCCESS

## 5. Git Status / Commit

```bash
cd /workspaces/predictive-ltv-survival-pipeline
git status --short
git add airflow/plugins/sensors/custom_sensors.py airflow/plugins/sensors/__init__.py \
        PHASE_4_BATCH_5_1_HARDENING_REPORT.md PHASE_4_BATCH_5_1_COMMAND_LOG.md README.md
git commit -m "Phase 4 Batch 5.1: sensor compatibility fix and documentation"
```
