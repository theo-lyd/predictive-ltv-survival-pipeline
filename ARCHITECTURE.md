# Architecture & Infrastructure

## System Architecture

### High-Level Data Flow

```
External Sources (CSV, JSON, APIs)
        ↓
    Bronze Layer (Immutable, Raw)
    Delta Lake: /mnt/bronze/
        ↓
    Silver Layer (Cleaned, Validated)
    dbt Transformations + Great Expectations
        ↓
    Gold Layer (Business-Ready Analytics)
    dbt Models + Semantic Layer
        ↓
    Executive Dashboard (Streamlit)
    AI Narrative + What-If Simulator
```

### Technology Stack

#### Data Platform
- **Cloud Platform**: Databricks (Unity Catalog)
- **Storage**: Delta Lake (S3/ADLS backend)
- **Format**: Parquet/Delta Tables

#### Processing
- **SQL**: Databricks SQL + dbt
- **Python**: PySpark for complex transformations
- **Orchestration**: Airflow for DAG scheduling

#### Analytics & Modeling
- **Transformation**: dbt-databricks (dbt with Spark backend)
- **Quality Assurance**: Great Expectations + dbt tests
- **Modeling**: Kaplan-Meier survival analysis via dbt-python

#### BI & Visualization
- **Dashboard**: Streamlit
- **Charts**: Plotly
- **AI Narrative**: LLM integration for summaries

#### DevOps
- **Container**: Docker + Codespaces
- **CI/CD**: GitHub Actions
- **IaC**: Terraform (planned)

## Medallion Architecture Details

### Bronze Layer (Raw)
```sql
-- Example: Bronze ingestion
CREATE TABLE bronze.raw_customers (
    customer_id STRING,
    signup_date STRING,      -- Raw format
    subscription_id STRING,
    _ingested_at TIMESTAMP
)
USING DELTA
TBLPROPERTIES (
    'delta.appendOnly' = 'true'
);
```

**Characteristics**:
- Append-only Delta tables
- Full audit trail with `_ingested_at`
- All types as strings initially (flexible)
- No deduplication or quality checks
- Preserves 100% of source data

### Silver Layer (Trusted)
```sql
-- Example: Silver transformation
CREATE TABLE IF NOT EXISTS silver.stg_customers (
    customer_id STRING NOT NULL,
    signup_dt TIMESTAMP NOT NULL,
    subscription_id STRING NOT NULL,
    region STRING,
    status STRING,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
)
USING DELTA;
```

**Characteristics**:
- dbt-managed transformation
- Schema enforcement
- Deduplication and identity stitching
- Business logic (e.g., churn classification)
- Great Expectations validation
- Typically 90-95% data retained

### Gold Layer (Analytics)
```sql
-- Example: Gold fact table
CREATE TABLE IF NOT EXISTS gold.marts.fct_customer_ltv (
    customer_id STRING NOT NULL,
    cohort_year INT,
    discount_tier STRING,
    ltv DECIMAL(18, 2),
    churn_probability DECIMAL(5, 4),
    tenure_days INT,
    net_revenue DECIMAL(18, 2),
    created_at TIMESTAMP NOT NULL
)
USING DELTA;
```

**Characteristics**:
- Fact and dimension tables
- Pre-aggregated metrics
- Single source of truth for metrics
- Unity Catalog lineage tracking
- Optimized for dashboard consumption

## Data Governance

### Unity Catalog Structure

```
Catalog: main
├── Schema: predictive_ltv_dev
│   ├── stg_customers (Silver)
│   ├── stg_promotions (Silver)
│   └── fct_customer_ltv (Gold)
└── Schema: predictive_ltv_prod
    ├── stg_customers (Silver)
    ├── stg_promotions (Silver)
    └── fct_customer_ltv (Gold)
```

### Lineage Tracking

Every transformation is tracked:
- **Source**: Raw CSV in Bronze
- **Transformation**: stg_* model in Silver
- **Output**: fct_customer_ltv in Gold
- **Consumer**: Executive dashboard

View lineage with:
```bash
dbt docs generate && dbt docs serve
```

## Deployment Environments

### Development (Dev)
- Schema: `predictive_ltv_dev`
- Auto-refreshing on commit
- 4 concurrent threads in dbt
- Target for experimentation

### Production (Prod)
- Schema: `predictive_ltv_prod`
- Controlled releases via main branch
- 8 concurrent threads for performance
- SLA: 6-hour freshness window

## Secrets & Access Management

### Databricks Credentials

Stored securely in:
- **Local Dev**: `~/.dbt/profiles.yml` (excluded from git)
- **GitHub Actions**: GitHub Secrets
- **Codespaces**: GitHub Codespaces Secrets

### GitHub Secrets Setup

```bash
# Set in your GitHub repo settings
DATABRICKS_HOST=abc123.cloud.databricks.com
DATABRICKS_TOKEN=dbapin1234567890...
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/abc123
```

## Scalability Considerations

### Cluster Configuration

**Development Cluster**:
- Node type: i3.xlarge (8GB RAM)
- Min workers: 1, Max workers: 4
- Auto-termination: 15 minutes

**Production Warehouse**:
- Type: Pro SQL Warehouse
- Min clusters: 1, Max clusters: 4
- Scaling: Automatic

### Optimization Strategies

1. **Partition by date** for large fact tables
2. **Z-order by high-cardinality keys** (customer_id, cohort)
3. **Cache frequently accessed views** in Gold layer
4. **Use predict/persist** for churn models

## Monitoring & Observability

### Data Quality Monitoring

- **Great Expectations**: Automated validation on each run
- **Monte Carlo**: Schema drift and freshness alerts
- **dbt tests**: Model-level quality gates

### Pipeline Monitoring

- **Airflow**: DAG execution and task-level logs
- **Databricks**: Job cluster metrics and SQL performance
- **GitHub Actions**: CI/CD pipeline status

### Health Checks

Run nightly:
```bash
make validate         # Environment and dbt connection
dbt test              # All model tests
dbt docs generate     # Regenerate lineage
```

## Disaster Recovery

### Backup Strategy

- **Bronze**: Immutable append-only (version history via Delta)
- **Silver/Gold**: Daily snapshots via Delta time travel
- **Restore**: `SELECT * FROM table@v123` (Delta version history)

### Rollback Procedure

```sql
-- Restore to a previous state
RESTORE TABLE gold.marts.fct_customer_ltv 
TO VERSION AS OF 123;
```

## Cost Optimization

1. **Use All-Purpose clusters** for dev (share compute)
2. **Schedule batch jobs** during off-peak hours
3. **Leverage spot instances** where appropriate
4. **Archive old data** to cheaper storage tiers
5. **Monitor Databricks cost reports** monthly

## Runbooks

### Incident: Pipeline Fails

1. Check Airflow DAG logs for task failure
2. Review Databricks cluster logs
3. Run `dbt debug` to verify connectivity
4. Check data freshness in Gold layer
5. Alert slack channel if SLA breached

### Incident: Metric Discrepancy

1. Compare Silver and Gold counts: `SELECT COUNT(*) FROM silver.stg_* vs gold.marts.fct_*`
2. Check for duplicates: `SELECT customer_id, COUNT(*) as cnt FROM silver.stg_* GROUP BY 1 HAVING cnt > 1`
3. Review recent dbt model changes in git history
4. Roll back if necessary

### Incident: Schema Drift

1. Monitor alerts from Monte Carlo
2. Review source schema changes
3. Update Bronze ingestion schema
4. Test Silver models with new schema
5. Update downstream dependencies
