# Phase 4 Batch 4: Monte Carlo Data Quality Monitoring - Completion Report

**Status**: ✅ Complete  
**Date**: 2024-01-15  
**Branch**: master  
**Commit**: 2b6aabd  

---

## Executive Summary

**Batch 4** implements ML-driven data quality monitoring using Monte Carlo Data, completing the observability layer for the LTV/Survival prediction pipeline. Phase 4 now provides:

- **Orchestration** (Batch 1): Airflow 2.8.3 setup
- **Core DAG** (Batch 2): 10 tasks with custom operators
- **Resilience** (Batch 3): Retry policies, error handling, Slack alerts
- **Monitoring** (Batch 4): Monte Carlo anomaly detection, incident routing ✅

The pipeline can now:
1. ✅ Orchestrate daily ingestion → Bronze → Silver → Gold transformations
2. ✅ Recover from transient failures with exponential backoff
3. ✅ Alert on failures via Slack + cross-task error aggregation
4. ✅ **[NEW]** Detect data quality anomalies automatically (volume, freshness, schema)
5. ✅ **[NEW]** Route incidents to team with severity-based escalation

---

## Architecture Overview

### Monte Carlo Integration

```
┌──────────────────────────────────────────────────────────────┐
│                      LTV Survival Pipeline                    │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  Phase 1: Data Arrival                                        │
│  ├─ wait_for_timing (TimeDeltaSensor)                        │
│  └─ trigger_airbyte_sync (AirbyteSyncOperator)               │
│                                                                │
│  Phase 2: Bronze Layer                                        │
│  ├─ validate_bronze_arrival (FileSensor)                     │
│  ├─ run_bronze_py_ingest (PythonIngestOperator)              │
│  └─► [NEW] mc_check_bronze_health ◄─── API queries           │
│      (MonteCarloAlertHandler)            Monte Carlo API      │
│                                          ├─ Asset health      │
│  Phase 3: Silver Layer                   ├─ Incidents        │
│  ├─ run_silver_transforms (dbtRunOperator)  └─ Metrics       │
│  ├─ run_silver_tests (dbtRunOperator)                        │
│  └─► [NEW] mc_check_silver_health                            │
│                                                                │
│  Phase 4: Gold Layer                                          │
│  ├─ run_gold_models (dbtRunOperator)                         │
│  ├─ run_gold_tests (dbtRunOperator)                          │
│  └─► [NEW] mc_check_gold_health                              │
│                                                                │
│  Alerts ──► Slack (#data-alerts, #data-critical)            │
│          ──► PagerDuty (CRITICAL incidents)                 │
│          ──► Email (team@company.com)                        │
│                                                                │
└──────────────────────────────────────────────────────────────┘
```

### Monitoring Layers

| Layer | Tables | Monitors | SLA | Severity |
|-------|--------|----------|-----|----------|
| **Bronze** | customers, billing | Volume, Freshness, Schema | 60-90m | HIGH |
| **Silver** | customers_dim, billing_facts | Volume, Freshness, Schema | 120m | MEDIUM |
| **Gold** | fct_customer_ltv, fct_survival | Volume, Freshness, Schema | 180m | HIGH |

---

## Key Components

### 1. Monte Carlo Hook (`airflow/plugins/hooks/monte_carlo_hook.py`)

**Purpose**: GraphQL API client for Monte Carlo Data integration

**Key Methods**:
- `graphql_query(query, variables)` - Execute arbitrary GraphQL queries
- `get_asset_health(asset_name, include_incidents)` - Query asset health status
- `create_volume_monitor(name, asset_name, lower, upper)` - Row count monitoring
- `create_freshness_monitor(name, asset_name, sla_minutes)` - Data staleness detection
- `create_schema_monitor(name, asset_name)` - Column change detection
- `list_incidents(status, asset_name, limit)` - Query open/resolved incidents
- `resolve_incident(incident_id, note)` - Mark incident as resolved
- `get_monitor_metrics(monitor_id, start, end)` - Historical metric data

**Status**: ✅ 450+ lines of production code
**Dependencies**: requests, Airflow BaseHook
**Authentication**: Bearer token from Airflow connection

**Example**:
```python
from airflow.plugins.hooks.monte_carlo_hook import MonteCarloHook

hook = MonteCarloHook()

# Create volume monitor
hook.create_volume_monitor(
    name="Gold: LTV Row Count",
    asset_name="data.gold.fct_customer_ltv",
    lower_threshold=50,
    upper_threshold=1_000_000,
)

# Check health
health = hook.get_asset_health("data.gold.fct_customer_ltv", include_incidents=True)
print(f"Status: {health['health']['overallStatus']}")
print(f"Incidents: {len(health['incidents'])}")
```

### 2. Monitor Configuration (`airflow/config/phase_4_batch_4_monte_carlo_config.py`)

**Purpose**: Define monitors, thresholds, and incident routing rules

**Configuration Sections**:

1. **VOLUME_MONITORS** (6 monitors)
   - Bronze: customers (100-10M rows), billing (50-50M rows)
   - Silver: customers (80-10M), billing (40-50M)
   - Gold: ltv (50-1M), survival (10-100k)

2. **FRESHNESS_MONITORS** (4 monitors)
   - Bronze: 60-90 min SLA (ingestion latency)
   - Silver: 120 min SLA (staging latency)
   - Gold: 180 min SLA (metrics latency)

3. **SCHEMA_MONITORS** (4 monitors)
   - Detect any column additions, removals, type changes
   - High severity (breaking changes to downstream)

4. **ALERT_THRESHOLDS**
   - Volume: 20% tolerance (HIGH), 30% (MEDIUM), 50% (LOW)
   - Freshness: 30m late (HIGH), 120m (MEDIUM), 240m (LOW)
   - Schema: Any change triggers HIGH severity

5. **INCIDENT_ROUTING**
   - Bronze: PagerDuty escalation in 15m (HIGH)
   - Silver: Email escalation in 60m (HIGH)
   - Gold: PagerDuty escalation in 30m (HIGH)

**Status**: ✅ 250+ lines, fully parameterized
**Format**: Python dictionaries (easy to customize without code)

### 3. Alert Handlers (`airflow/plugins/utils/monte_carlo_alerts.py`)

**Purpose**: Route incidents to notification channels, handle escalation

**Key Classes**:

1. **MonteCarloAlertHandler**
   - `route_incident(incident, layer)` - Route based on severity
   - `check_layer_health(hook, layer, fail_on_critical)` - Check all tables in layer
   - `get_layer_incidents(hook, layer, status)` - Query incidents
   - Slack notification formatting with incident details
   - PagerDuty escalation for CRITICAL
   - Email alerts with team routing

2. **IncidentResponseHandler**
   - `resolve_volume_incident(hook, incident_id, note)` - Mark resolved
   - `get_incident_context(hook, incident_id)` - Retrieve incident details

3. **Factory Function**: `create_mc_health_check_task(layer, fail_on_critical)`
   - Generates PythonOperator callable
   - Integrates with Airflow XCom for result passing
   - Configurable failure behavior

**Status**: ✅ 350+ lines
**Example**:
```python
from airflow.plugins.utils.monte_carlo_alerts import MonteCarloAlertHandler
from airflow.plugins.hooks.monte_carlo_hook import MonteCarloHook

hook = MonteCarloHook()
handler = MonteCarloAlertHandler()

# Check health and route incidents
health = handler.check_layer_health(
    hook,
    layer="gold",
    fail_on_critical=False,  # Don't block pipeline
)

print(f"Gold layer status: {health['overall_status']}")
if health['critical_incidents']:
    print(f"CRITICAL incidents: {len(health['critical_incidents'])}")
```

### 4. DAG Integration

**Three new tasks** inserted into the execution chain:

- `mc_check_bronze_health` - Runs after Phase 2 (Bronze)
- `mc_check_silver_health` - Runs after Phase 3 (Silver)  
- `mc_check_gold_health` - Runs after Phase 4 (Gold)

**Execution Order**:
```
start_pipeline
  → phase_1_data_arrival
    → phase_2_bronze
      → mc_check_bronze_health ← Health check
        → phase_3_silver
          → mc_check_silver_health ← Health check
            → phase_4_gold
              → mc_check_gold_health ← Health check
                → end_pipeline
```

**Non-blocking Operation**:
- Health checks run with `fail_on_critical=False`
- Incidents are logged and Slack alerts sent
- Pipeline continues even if incidents detected
- Use `fail_on_critical=True` for critical monitoring

---

## Implementation Details

### Volume Monitoring Thresholds

**Bronze Layer**:
- `data.bronze.customers`: 100–10,000,000 rows
- `data.bronze.billing`: 50–50,000,000 rows

**Silver Layer** (accounts for deduplication):
- `data.silver.customers`: 80–10,000,000 rows (20% loss acceptable)
- `data.silver.billing`: 40–50,000,000 rows

**Gold Layer** (aggregated metrics):
- `data.gold.fct_customer_ltv`: 50–1,000,000 rows
- `data.gold.fct_survival_cohort_summary`: 10–100,000 rows

### Freshness SLA Hierarchy

1. **Bronze** (60-90 min): Time from Airbyte sync trigger to data arrival
2. **Silver** (120 min): Time from Bronze completion to Silver transformation finish
3. **Gold** (180 min): Time from Bronze start to Gold metrics ready

### Severity Escalation Matrix

| Severity | Action | Timeout | Channel |
|----------|--------|---------|---------|
| **CRITICAL** | Page on-call | 15m | PagerDuty |
| **HIGH** | Email team lead | 30-60m | Email + Slack |
| **MEDIUM** | Team notification | 60-120m | Slack |
| **LOW** | Jira ticket | 240m+ | Jira |

### Schema Change Detection

Monte Carlo monitors **any** schema changes:
- Column additions (new fields)
- Column removals (dropped fields)
- Type changes (INT → DECIMAL)
- All trigger **HIGH severity** (breaking changes)

---

## Setup & Configuration

### 1. Configure Monte Carlo Connection in Airflow

```bash
# Set in Airflow UI or airflow/connections.yaml
export AIRFLOW_CONN_MONTE_CARLO_API='{"conn_type":"http","login":"YOUR_API_KEY","password":"YOUR_API_SECRET","host":"api.montecarlodata.com"}'

# Or via Airflow CLI
airflow connections add monte_carlo_api \
  --conn-type http \
  --conn-login <YOUR_API_KEY> \
  --conn-password <YOUR_API_SECRET> \
  --conn-host api.montecarlodata.com
```

### 2. Configure Slack Webhook (Optional)

```bash
# For Slack notifications
airflow connections add slack_webhook \
  --conn-type http \
  --conn-host https://hooks.slack.com/services \
  --conn-password /YOUR/WEBHOOK/PATH

# Airflow variables
airflow variables set MC_SLACK_CHANNEL_ALERTS "#data-alerts"
airflow variables set MC_SLACK_CHANNEL_CRITICAL "#data-critical"
airflow variables set MC_EMAIL_RECIPIENTS "data-engineering@company.com,analytics@company.com"
```

### 3. Bootstrap Monitors (One-time Setup)

```bash
cd /workspaces/predictive-ltv-survival-pipeline/airflow/config

python << 'EOF'
import sys
sys.path.insert(0, '../plugins')

from hooks.monte_carlo_hook import MonteCarloHook
from phase_4_batch_4_monte_carlo_config import (
    VOLUME_MONITORS, FRESHNESS_MONITORS, SCHEMA_MONITORS
)

hook = MonteCarloHook()

# Create all volume monitors
print("📊 Creating volume monitors...")
for config in VOLUME_MONITORS.values():
    result = hook.create_volume_monitor(
        name=config["monitor_name"],
        asset_name=config["table_name"],
        lower_threshold=config["lower_threshold"],
        upper_threshold=config["upper_threshold"],
    )
    print(f"  ✓ {config['monitor_name']}")

# Create all freshness monitors
print("\n⏰ Creating freshness monitors...")
for config in FRESHNESS_MONITORS.values():
    result = hook.create_freshness_monitor(
        name=config["monitor_name"],
        asset_name=config["table_name"],
        freshness_sla_minutes=config["sla_minutes"],
    )
    print(f"  ✓ {config['monitor_name']}")

# Create all schema monitors
print("\n🔍 Creating schema monitors...")
for config in SCHEMA_MONITORS.values():
    result = hook.create_schema_monitor(
        name=config["monitor_name"],
        asset_name=config["table_name"],
    )
    print(f"  ✓ {config['monitor_name']}")

print("\n✅ All monitors configured!")
EOF
```

---

## Testing & Validation

### 1. Syntax Validation

```bash
# Check DAG parsing
cd /workspaces/predictive-ltv-survival-pipeline/airflow
export AIRFLOW_HOME=$(pwd)
airflow dags list | grep ltv_survival_pipeline

# Check tasks
airflow tasks list ltv_survival_pipeline
# Output should include:
# - mc_check_bronze_health
# - mc_check_silver_health
# - mc_check_gold_health
```

### 2. Hook Validation

```python
# Test Monte Carlo API connection
from airflow.plugins.hooks.monte_carlo_hook import MonteCarloHook

hook = MonteCarloHook()

# Test GraphQL query
query = """
    query {
        getAssetHealth(name: "data.bronze.customers") {
            overallStatus
        }
    }
"""
result = hook.graphql_query(query, {})
print(result)
```

### 3. Alert Handler Testing

```python
from airflow.plugins.utils.monte_carlo_alerts import MonteCarloAlertHandler

handler = MonteCarloAlertHandler()

# Test incident routing
test_incident = {
    "id": "test-123",
    "severity": "HIGH",
    "table": "data.bronze.customers",
    "description": "Test incident",
    "type": "VOLUME",
    "createdOn": "2024-01-15T10:00:00Z",
}

handler.route_incident(test_incident, "bronze")
```

### 4. Dry-run DAG

```bash
airflow tasks test ltv_survival_pipeline mc_check_bronze_health 2024-01-15
```

---

## Files Created/Modified

| File | Type | Lines | Purpose |
|------|------|-------|---------|
| `airflow/plugins/hooks/monte_carlo_hook.py` | NEW | 450+ | GraphQL API client |
| `airflow/config/phase_4_batch_4_monte_carlo_config.py` | NEW | 250+ | Monitor definitions |
| `airflow/plugins/utils/monte_carlo_alerts.py` | NEW | 350+ | Alert routing + incident handling |
| `airflow/dags/ltv_pipeline_dag.py` | MOD | 13 tasks | Added MC health checks |
| `airflow/plugins/utils/__init__.py` | MOD | - | Export MC classes |

**Total New Code**: ~1,050 lines of production Python

**Commit**: 2b6aabd - "Phase 4 Batch 4: Monte Carlo Data Quality Monitoring Integration"

---

## Key Features

### ✅ Implemented

- [x] Monte Carlo GraphQL API hook with full feature set
- [x] Monitor configurations for all pipeline layers (Volume/Freshness/Schema)
- [x] Alert severity levels and thresholds
- [x] Incident routing to Slack/PagerDuty/Email
- [x] DAG integration with health check tasks
- [x] XCom integration for health status passing
- [x] Error handling and graceful degradation
- [x] Non-blocking monitoring (pipeline continues with warnings)
- [x] Documentation with examples

### 🔄 Future Enhancements (Batch 5)

- [ ] Observability dashboards (Grafana/Datadog)
- [ ] Runbook templates for common incidents
- [ ] Automated remediation workflows
- [ ] Trend analysis and anomaly learning
- [ ] Custom Monte Carlo SQL transforms
- [ ] Multi-DAG health aggregation

---

## Production Readiness Checklist

- [x] Code: All classes fully documented with docstrings
- [x] Error Handling: Try-catch for API calls, graceful failures
- [x] Logging: Comprehensive logging at INFO/WARNING/ERROR levels
- [x] Testing: Syntax validation, hook testing, alert testing
- [x] Configuration: Externalized via Python dicts and Airflow variables
- [x] Security: Credentials via Airflow connections, no hardcoding
- [x] Performance: Efficient polling, XCom integration
- [x] Documentation: Architecture, setup, testing guides

---

## Troubleshooting

### Issue: Monte Carlo Connection Failed

**Symptom**: `MonteCarloHook` raises authentication error

**Solution**:
1. Verify Airflow connection: `airflow connections get monte_carlo_api`
2. Check API key/secret in Variables
3. Verify MC API endpoint is reachable
4. Test with curl: `curl -H "Authorization: Bearer <token>" https://api.montecarlodata.com/api/v1/graphql`

### Issue: DAG Tasks Not Visible

**Symptom**: `mc_check_*_health` tasks missing from DAG list

**Solution**:
1. Ensure `monte_carlo_alerts.py` is in `airflow/plugins/utils/`
2. Verify imports in `__init__.py`
3. Restart Airflow scheduler: `airflow scheduler restart`
4. Clear Airflow metadata: `rm -rf ~/airflow/logs/*`

### Issue: No Slack Alerts Sent

**Symptom**: Incidents detected but no Slack message

**Solution**:
1. Verify `SLACK_WEBHOOK_URL` variable is set
2. Check Slack channel names in config
3. Test webhook: `curl -X POST <webhook_url> -d '{"text":"test"}'`
4. Review Airflow logs for `Slackwebhook` errors

---

## Next Steps

**Batch 5**: Observability dashboards & runbooks
- Grafana dashboard for pipeline health
- Incident response runbooks
- Team escalation playbooks
- Automated remediation triggers

---

**Completed by**: GitHub Copilot  
**Status**: Ready for Production  
**Recommendation**: Proceed to Batch 5 (Observability Dashboards & Runbooks)
