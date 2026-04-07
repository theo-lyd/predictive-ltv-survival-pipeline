# Service Level Agreement (SLA) Framework

## Overview

This document defines the Service Level Agreements (SLAs) for the predictive-ltv-survival-pipeline data platform. SLAs establish measurable commitments for data availability, latency, quality, and reliability across all layers of the platform.

**SLA Philosophy**: 
- Bronze/Silver layers require 24/7 monitoring (data foundation)
- Gold layer emphasizes correctness over speed (metrics confidence)
- Presentation layer balances accessibility with accuracy
- Escalation is automatic based on severity, not discretionary

---

## SLA Metrics by Layer

### Bronze Layer: Raw Data Ingestion

**Owner**: Data Ingestion Lead  
**Criticality**: 🔴 Critical (foundation for all downstream)  
**On-Call**: 24/7 rotation (no business hours limit)

#### Primary Metrics

| Metric | Target | Target | Response SLA | Severity |
|--------|--------|--------|--------------|----------|
| Data Availability | 8:00am UTC | Daily refresh complete by 8am | P1: ≤15min | Critical |
| Data Freshness | 24 hours max lag | No data older than 1 day | P1: Resolve within 2 hours | High |
| Ingestion Success Rate | 99.5% | 1 failure per 200 runs acceptable | P1: <30min recovery | Critical |
| Error Recovery | <5 minutes | Failed ingestion pipes retry auto-recover | P2: <1 hour fix | High |

#### SLA Details

**Metric 1: Daily Data Availability (8:00 AM)**
- **Definition**: All scheduled data sources successfully ingested and available in Bronze layer
- **Measurement**: Airflow DAG completion status + row count validation
- **Success Criteria**: ✅ All 5 data sources present with non-zero row counts
- **Failure**: ❌ Any source missing or 0 rows by 8:15 AM

**Alert Threshold**:
```
IF ingestion_job.status = FAILED OR table_row_count = 0
   THEN trigger P1 alert (Slack + PagerDuty)
```

**Test Case**:
```python
def test_bronze_8am_sla():
    # Check 8:00 AM data availability
    assert get_table_rows('bronze.raw_churn') > 0
    assert get_table_rows('bronze.raw_promotions') > 0
    assert get_table_rows('bronze.raw_billing') > 0
    assert get_table_rows('bronze.raw_customers') > 0
```

**Metric 2: Data Freshness (24-hour max lag)**
- **Definition**: No raw data is older than 24 hours from source system
- **Measurement**: `MAX(data_timestamp) - NOW()` per table
- **Success Criteria**: ✅ All tables updated within 24 hours
- **Failure**: ❌ Any table hasn't updated in >24 hours

**Alert Threshold**:
```
IF DATEDIFF(HOUR, MAX(data_timestamp), NOW()) > 24
   THEN trigger P1 alert (Slack)
```

**Metric 3: Ingestion Success Rate (99.5%)**
- **Definition**: Percentage of scheduled ingestion jobs that complete successfully
- **Measurement**: `success_jobs / total_jobs * 100` (rolling 30-day window)
- **Success Criteria**: ✅ Success rate ≥ 99.5%
- **Failure**: ❌ Success rate < 99.5%

**Tracking Query**:
```sql
SELECT 
  DATE(execution_date) as date,
  COUNT(CASE WHEN status = 'success' THEN 1 END) as success_count,
  COUNT(*) as total_count,
  ROUND(100.0 * COUNT(CASE WHEN status = 'success' THEN 1 END) / COUNT(*), 2) as success_rate
FROM airflow_dag_runs
WHERE dag_id LIKE 'bronze_%'
GROUP BY DATE(execution_date)
ORDER BY date DESC
```

**Metric 4: Error Recovery Time (<5 minutes)**
- **Definition**: Time from job failure to automatic recovery/retry
- **Measurement**: `time_to_recovery = retry_success_time - failure_detection_time`
- **Success Criteria**: ✅ Recovery within 5 minutes
- **Failure**: ❌ Manual intervention required (escalate to P2)

---

### Silver Layer: Trusted Transformed Data

**Owner**: Data Analyst Lead  
**Criticality**: 🟠 High (analytics foundation)  
**On-Call**: Business hours (9am-6pm, 5-day week)

#### Primary Metrics

| Metric | Target | Limit | Response SLA | Severity |
|--------|--------|-------|--------------|----------|
| Quality Checkpoint Pass | 9:00am | All tests must pass | P2: ≤1 hour | High |
| Data Completeness | ≥98% | Max 2% null/missing | P2: <1 hour fix | High |
| Freshness | 6 hours max lag | Transformations run every 6h | P2: <1 hour retry | High |
| Test Coverage | ≥90% columns | All business logic tested | P3: Next sprint | Medium |

#### SLA Details

**Metric 1: Quality Checkpoint Pass (9:00 AM)**
- **Definition**: Great Expectations checkpoint passes all validations
- **Measurement**: GE checkpoint status from DAG execution
- **Success Criteria**: ✅ 100% checks pass (green status)
- **Failure**: ❌ Any check fails (red status)

**Alert Threshold**:
```yaml
if checkpoint_status == 'FAILED':
  send_alert('P2', 'Silver quality check failed', channels=['slack', 'email'])
```

**Checkpoints Defined**:
```python
# Silver layer quality checkpoint
checkpoints:
  - silver_completeness:
      min_row_count: 10000
      max_null_percent: 2.0
      
  - silver_uniqueness:
      check_columns: ['customer_id', 'billing_period']
      
  - silver_referential_integrity:
      check: 'customer_id refs bronze.raw_customers.customer_id'
```

**Metric 2: Data Completeness (≥98%)**
- **Definition**: Percentage of expected non-null values in analytics datasets
- **Measurement**: `(total_rows - null_rows) / total_rows * 100`
- **Success Criteria**: ✅ Completeness ≥ 98%
- **Failure**: ❌ Completeness < 98% (triggers investigation)

**Tracking Query**:
```sql
SELECT 
  column_name,
  COUNT(*) as total_rows,
  COUNT(CASE WHEN value IS NULL THEN 1 END) as null_count,
  ROUND(100.0 * (COUNT(*) - COUNT(CASE WHEN value IS NULL THEN 1 END)) / COUNT(*), 2) as completeness_pct
FROM silver.transformed_data
GROUP BY column_name
ORDER BY completeness_pct ASC
```

**Metric 3: Freshness (6-hour max lag)**
- **Definition**: Silver transformation runs every 6 hours
- **Measurement**: `MAX(transformation_time) < NOW() - INTERVAL '6 hours'`
- **Success Criteria**: ✅ Transformations run on schedule
- **Failure**: ❌ >6 hours since last transformation

**Alert Threshold**:
```
IF transformation_lag_hours > 6
   THEN trigger P2 alert (within business hours)
```

**Metric 4: Test Coverage (≥90%)**
- **Definition**: Percentage of data columns covered by dbt tests
- **Measurement**: `tested_columns / total_columns * 100`
- **Success Criteria**: ✅ Coverage ≥ 90%
- **Failure**: ❌ New columns without tests (code review gate)

---

### Gold Layer: Metrics & Analytics

**Owner**: Analytics Engineering Lead  
**Criticality**: 🟠 High (business metrics)  
**On-Call**: 24/7 rotation (key metrics critical for decisions)

#### Primary Metrics

| Metric | Target | Limit | Response SLA | Severity |
|--------|--------|-------|--------------|----------|
| Metric Computation | 10:00am | All KPIs calculated by 10am | P1: ≤30min | Critical |
| Correctness Validation | 100% | Manual validation pass | P1: <2 hours | Critical |
| Data Reconciliation | ≤1% variance | vs. source of truth | P2: <4 hours | High |
| Schema Integrity | 100% | All columns present/typed | P1: ≤15min | Critical |

#### SLA Details

**Metric 1: Metric Computation (10:00 AM)**
- **Definition**: All Gold layer metrics calculated and available for reporting
- **Measurement**: dbt job completion status + metric table row count
- **Success Criteria**: ✅ All metrics present with valid values by 10:00 AM
- **Failure**: ❌ Any metric missing or contains NULL by 10:15 AM

**Alert Mechanism**:
```python
def check_gold_metric_sla():
    """Verify all Gold metrics computed by 10:00 AM"""
    metrics_to_check = [
        ('customer_ltv', 'gold.fact_customer_ltv'),
        ('churn_probability', 'gold.fact_churn_predictions'),
        ('nrr_monthly', 'gold.fact_monthly_nrr'),
        ('discount_efficiency', 'gold.fact_discount_roi')
    ]
    
    for metric_name, table_name in metrics_to_check:
        row_count = get_row_count(table_name)
        null_percent = get_null_percent(table_name)
        
        if row_count == 0 or null_percent >= 10:
            raise MetricComputationSLABreach(
                metric=metric_name,
                table=table_name,
                severity='P1',
                message=f'{metric_name} computation failed'
            )
```

**Metric 2: Correctness Validation (100%)**
- **Definition**: Manual validation passes (business logic verified)
- **Measurement**: Analytics Lead reviews 5 sample metrics daily
- **Success Criteria**: ✅ All 5 spot-checks match expected values
- **Failure**: ❌ Any metric deviates from expected value within 5%

**Validation Checklist**:
```
Daily @ 10:00 AM Analytics Lead reviews:
☐ Customer LTV top 10: values between $1k-$50k (reasonable range)
☐ Churn probability: values between 0-1 (valid probability)
☐ NRR: values between 80-120% (sustainable business range)
☐ Discount ROI: positive correlation with discount size
☐ Row count growth: month-over-month trend consistent

Sign-off: ✅ Approve or ❌ Escalate if anomaly detected
```

**Metric 3: Data Reconciliation (≤1% variance)**
- **Definition**: Gold metrics reconcile to source system within acceptable variance
- **Measurement**: `ABS(gold_metric - source_metric) / source_metric * 100`
- **Success Criteria**: ✅ Variance ≤ 1% (acceptable rounding/timing differences)
- **Failure**: ❌ Variance > 1% (investigation required)

**Reconciliation Query**:
```sql
SELECT 
  'LTV' as metric,
  COUNT(DISTINCT gold.customer_id) as gold_count,
  COUNT(DISTINCT source.customer_id) as source_count,
  ROUND(ABS(gold_count - source_count) / CAST(source_count AS FLOAT) * 100, 2) as variance_pct
FROM gold.fact_customer_ltv gold
FULL OUTER JOIN source_system.customers source 
  ON gold.customer_id = source.customer_id
WHERE variance_pct > 1.0  -- Only show failures
ORDER BY variance_pct DESC
```

**Metric 4: Schema Integrity (100%)**
- **Definition**: All expected columns present with correct data types
- **Measurement**: dbt schema validation + column type checks
- **Success Criteria**: ✅ All 15 columns present with correct types
- **Failure**: ❌ Missing column or type mismatch detected

**Schema Test (dbt)**:
```yaml
models:
  - name: fact_customer_ltv
    columns:
      - name: customer_id
        data_type: bigint
        tests:
          - not_null
          - relationships
          
      - name: ltv_amount
        data_type: decimal(15,2)
        tests:
          - not_null
          - dbt_expectations.expect_column_values_to_be_between:
              min_value: 0
              max_value: 1000000
```

---

### Presentation Layer: Dashboards & BI

**Owner**: BI/Analytics Lead  
**Criticality**: 🟡 Medium (business visibility)  
**On-Call**: Business hours (9am-6pm)

#### Primary Metrics

| Metric | Target | Limit | Response SLA | Severity |
|--------|--------|-------|--------------|----------|
| Dashboard Load Time | 10:30am | All dashboards load in <5 sec | P3: <1 hour fix | Medium |
| Data Refresh | 10:30am | Dashboard data in sync with Gold | P3: Check refresh job | Medium |
| Visualization Accuracy | 100% | Charts match underlying data | P2: <4 hours | High |
| User Access | 99% availability | Streamlit app accessible | P2: <2 hours | High |

#### SLA Details

**Metric 1: Dashboard Load Time (<5 seconds)**
- **Definition**: Time from page load to first data rendering
- **Measurement**: Streamlit cached metrics + query execution
- **Success Criteria**: ✅ Page loads in ≤5 seconds
- **Failure**: ❌ Page load time > 5 seconds

**Performance Optimization**:
```python
@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_gold_metrics_cached():
    """Load metrics with caching for performance"""
    return sql_query("SELECT * FROM gold.fact_customer_ltv")

# Measure load time
import time
start = time.time()
metrics_df = load_gold_metrics_cached()
load_time = time.time() - start

if load_time > 5.0:
    logger.warning(f'Dashboard load exceeded SLA: {load_time}s')
    send_alert('P3', 'Dashboard load time exceeded SLA')
```

**Metric 2: Data Refresh (10:30 AM)**
- **Definition**: Streamlit dashboard data updated from Gold layer
- **Measurement**: Cache invalidation time + data recency
- **Success Criteria**: ✅ Dashboard shows data ≤30 minutes old by 10:30 AM
- **Failure**: ❌ Dashboard shows stale data (>1 hour old)

**Refresh Logic**:
```python
def check_data_freshness():
    """Verify dashboard data is fresh"""
    gold_data_timestamp = sql.query(
        "SELECT MAX(data_timestamp) FROM gold.fact_customer_ltv"
    )
    age_minutes = (datetime.now() - gold_data_timestamp).total_seconds() / 60
    
    if age_minutes > 30:
        st.warning(f'Data is {age_minutes} minutes old')
        if age_minutes > 60:
            raise DataRefreshSLABreach(age_minutes)
```

**Metric 3: Visualization Accuracy (100%)**
- **Definition**: Dashboard charts accurately represent underlying data
- **Measurement**: Spot-check chart values against SQL query results
- **Success Criteria**: ✅ All charts match underlying data exactly
- **Failure**: ❌ Chart shows incorrect values (data-viz bug)

**Accuracy Test**:
```python
def test_dashboard_chart_accuracy():
    """Verify charts match underlying data"""
    
    # For LTV chart, verify top customers
    expected = sql.query("SELECT TOP 10 customer_id, ltv FROM gold.fact_customer_ltv ORDER BY ltv DESC")
    actual = streamlit_chart_data()
    
    pd.testing.assert_frame_equal(expected, actual)
```

**Metric 4: Application Availability (99%)**
- **Definition**: Streamlit app is accessible and responsive
- **Measurement**: Uptime monitoring + response time
- **Success Criteria**: ✅ App available 99% of business hours
- **Failure**: ❌ Downtime >1 hour in business hours

**Monitoring**:
```python
# Synthetic uptime check
def check_app_availability():
    """Verify app is up and responding"""
    try:
        response = requests.get(
            'https://predictive-ltv-app.streamlit.app',
            timeout=5
        )
        if response.status_code == 200:
            return 'UP'  # Log success
        else:
            raise AppUnavailableSLABreach(response.status_code)
    except requests.RequestException as e:
        raise AppUnavailableSLABreach(str(e))
```

---

## SLA Escalation Matrix

### Incident Classification

**P1 (Critical)**: Data pipeline broken, metrics unavailable, business impact immediate
- Response: ≤15 minutes
- Team: On-call engineer + manager
- Escalation: CTO if not resolved in 1 hour

**P2 (High)**: Data quality issue, metrics delayed, analytics impact
- Response: ≤1 hour (during business hours) / ≤4 hours (off-hours)
- Team: On-call engineer
- Escalation: Lead after 2 hours unresolved

**P3 (Medium)**: Configuration issue, minor delay, no immediate business impact
- Response: ≤4 hours (during business hours) / Next business day (off-hours)
- Team: Regular engineering staff
- Escalation: Lead if not resolved by end of day

### Escalation Procedure

```
T+0 min:    Alert triggered
            └─ P1: Page immediately, escalate to manager on-call
            └─ P2: Slack notification during business hours
            └─ P3: Create Jira ticket

T+15 min:   P1 only - Check-in from engineer
            └─ Confirm understanding, provide ETA

T+30 min:   All levels - Update status
            └─ P1: Commit to fix or escalate CTO
            └─ P2: Continue investigation
            └─ P3: Acknowledge and plan sprint work

T+1-2 hrs:  P1/P2 - Escalate to lead if unresolved
            └─ Bring additional resources
            └─ Consider rollback if appropriate

T+4 hrs:    All - RCA started (post-incident review)
            └─ Root cause analysis
            └─ Prevention measures identified
            └─ Communication to stakeholders
```

### Example Escalation Flow

**Scenario: Bronze ingestion fails at 8:15 AM**

```
08:15 AM   Airflow detects failure
           └─ Automatic P1 alert fires
           
08:16 AM   PagerDuty notifies on-call engineer
           └─ Slack: "🚨 CRITICAL: Bronze ingestion failed"
           
08:17 AM   On-call checks: tables have 0 rows
           └─ Restarts failed connector
           └─ Pings Slack: "Investigating, ETA 10 min"
           
08:25 AM   Connector still failing, root cause unclear
           └─ On-call escalates to Data Ingestion Lead
           └─ Brings second engineer
           └─ Checks external data source status
           
08:30 AM   Data source confirms API outage (their side)
           └─ Updates stakeholders: "External API down, ETA unknown"
           └─ Sets up monitoring for source recovery
           
08:45 AM   Source API comes online
           └─ Manually triggers catch-up ingestion
           └─ Data available by 09:15 AM (late, but acceptable)
           
09:15 AM   Data ingestion succeeds
           └─ P1 resolved (late but recovered)
           └─ Schedule RCA for next day
           
Next Day   RCA: Add external API health check + alerts
           └─ Prevent surprise outages in future
```

---

## SLA Monitoring Dashboard

### Dashboard Queries (dbt + Great Expectations)

**Bronze SLA Status**:
```sql
SELECT 
  'data_availability' as sla_metric,
  CASE WHEN MAX(ingestion_date) >= CAST(NOW() AS DATE) THEN 'PASS' ELSE 'FAIL' END as status,
  MAX(ingestion_date) as last_success,
  COUNT(DISTINCT table_name) as tables_loaded
FROM bronze_ingestion_log
WHERE ingestion_date >= CAST(NOW() AS DATE) - INTERVAL '2 days'
GROUP BY ingestion_date
ORDER BY ingestion_date DESC
LIMIT 1
```

**Silver Quality Status**:
```sql
SELECT 
  checkpoint_name,
  execution_date,
  CASE WHEN expectation_count_pass / expectation_count * 100 >= 95 THEN 'PASS' ELSE 'FAIL' END as status,
  ROUND(100.0 * expectation_count_pass / expectation_count, 1) as pct_pass,
  expectation_count_fail as failures
FROM ge_checkpoint_runs
WHERE DATE(execution_date) = CAST(NOW() AS DATE)
ORDER BY execution_date DESC
```

**Gold Metrics Status**:
```sql
SELECT 
  metric_name,
  MAX(computation_time) as last_computed,
  COUNT(*) as metric_count,
  COUNT(CASE WHEN value IS NOT NULL THEN 1 END) as populated_count,
  DATEDIFF(MINUTE, MAX(computation_time), NOW()) as minutes_old
FROM gold.all_metrics
WHERE DATE(computation_time) = CAST(NOW() AS DATE)
GROUP BY metric_name
HAVING minutes_old > 30  -- Show if >30 min old (SLA breach)
```

---

## SLA Compliance Tracking

### Monthly SLA Report

**Format**: Spreadsheet or automated Slack notification every Friday

```
┌─ WEEKLY SLA REPORT (Week of April 3, 2026) ─────────────────┐
│                                                              │
│ BRONZE LAYER                                                 │
│   Data Availability (8:00 AM)............ 100% ✅             │
│   Freshness (24hr max lag)............. 100% ✅             │
│   Ingestion Success Rate (99.5%)..... 99.8% ✅             │
│   Error Recovery (<5 min).......... 100% ✅             │
│                                                              │
│ SILVER LAYER                                                │
│   Quality Checkpoint Pass (9:00 AM)... 100% ✅              │
│   Data Completeness (≥98%)............ 99.2% ✅             │
│   Freshness (6hr max lag)........... 100% ✅             │
│   Test Coverage (≥90%)............. 92% ✅             │
│                                                              │
│ GOLD LAYER                                                  │
│   Metric Computation (10:00 AM)..... 98% ⚠️  (1 late)      │
│   Correctness Validation (100%)...... 100% ✅             │
│   Data Reconciliation (≤1%)......... 0.3% ✅             │
│   Schema Integrity (100%).......... 100% ✅             │
│                                                              │
│ PRESENTATION LAYER                                          │
│   Dashboard Load Time (<5 sec)...... 2.3s ✅             │
│   Data Refresh (10:30 AM)......... 100% ✅             │
│   Visualization Accuracy (100%).... 100% ✅             │
│   App Availability (99%)........ 100% ✅             │
│                                                              │
│ OVERALL: 97% compliance (excellent)                        │
│ Issues: 1 Gold metric late (resolved by 10:45 AM)        │
│ Action: Review dbt model complexity for performance       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### SLA Health Scoring

```python
def calculate_sla_health_score():
    """
    Calculate weekly SLA health score (0-100)
    Weights:
      - Bronze: 40% (critical foundation)
      - Silver: 30% (analytics enablement)
      - Gold: 20% (metric correctness)
      - Presentation: 10% (business visibility)
    """
    scores = {
        'bronze': get_layer_compliance('bronze'),      # e.g., 98%
        'silver': get_layer_compliance('silver'),      # e.g., 99%
        'gold': get_layer_compliance('gold'),          # e.g., 97%
        'presentation': get_layer_compliance('presentation')  # e.g., 100%
    }
    
    overall = (
        scores['bronze'] * 0.40 +
        scores['silver'] * 0.30 +
        scores['gold'] * 0.20 +
        scores['presentation'] * 0.10
    )
    
    # Grade
    if overall >= 99:
        grade = 'A+ Excellent'
    elif overall >= 95:
        grade = 'A Good'
    elif overall >= 90:
        grade = 'B Acceptable'
    elif overall >= 85:
        grade = 'C At Risk'
    else:
        grade = 'F Critical'
    
    return overall, grade
```

---

## SLA Review & Adjustment

### Quarterly Review Process

**Every 3 months**, SLA review meeting:

1. **Analyze**: Review last 13 weeks of compliance data
2. **Identify**: Patterns, recurring issues, false alarms
3. **Adjust**: Modify targets if consistently met/missed
4. **Document**: Version SLA changes in git

**Example Adjustment**:
```
Q1 2026 Review:
- Bronze 24-hr freshness SLA: Always met (change to 12hr? No, too aggressive)
- Gold 10:00 AM computation: 95% compliance (add 15min buffer? Maybe)
- Silver completeness: 98% target too tight, increase to 96% (still good)

Decision: Keep all targets as-is, focus on Gold latency improvements
```

### Escalation for Chronic Failures

**If SLA breached >3 times in consecutive weeks**:

```
Week 1: ❌ SLA missed (1/1)
Week 2: ❌ SLA missed (2/1)
Week 3: ❌ SLA missed (3/1)
       └─ Trigger RCA (root cause analysis)
       └─ Assign engineer to fix
       └─ Create sprint epic
       └─ Re-baseline SLA if needed (but rare)
```

---

## Integration with Batch 3 Monitoring

### Scheduled Checks (dbt + Great Expectations)

These SLA checks will be executed hourly and logged for compliance reporting:

```yaml
# In dbt_project.yml
on_run_start:
  - "{% do execute_sla_checks() %}"   # Check all layer SLAs

# In great_expectations/checkpoints
checkpoints:
  - sla_bronze_availability.yml  # Daily 8am check
  - sla_silver_completeness.yml  # Daily 9am check
  - sla_gold_correctness.yml     # Daily 10am check
  - sla_presentation_load.yml    # Daily 10:30am check
```

### Alert Integration

```python
# In scripts/sla_monitoring.py
def monitor_slas():
    """Hourly SLA compliance check"""
    
    # Check each layer
    bronze_status = check_bronze_sla()
    silver_status = check_silver_sla()
    gold_status = check_gold_sla()
    presentation_status = check_presentation_sla()
    
    # Log to database
    log_sla_status(bronze_status, silver_status, gold_status, presentation_status)
    
    # Alert if breach
    for status in [bronze_status, silver_status, gold_status]:
        if status['is_breached']:
            send_alert(severity=status['severity'], details=status)
```

---

## Success Criteria

✅ SLA framework defined (this document)  
✅ Metrics measurable and automatable  
✅ Escalation procedures clear  
✅ Monitoring dashboard queryable  
✅ Compliance tracking implemented  
✅ Ready for Batch 4 real-time monitoring implementation

