# Data Lineage & Provenance Tracking

## Overview

Data lineage provides the complete historical record of how data flows through the pipeline from source systems to final metrics. This document defines how data provenance is captured, tracked, visualized, and validated.

**Lineage Philosophy**:
- Every data transformation is transparent and traceable
- Provenance metadata captured at ingestion, transformation, and output stages
- Lineage graph queryable for impact analysis ("what data changed?")
- Schema and business logic changes tracked and auditable
- Unity Catalog provides centralized metadata governance

---

## Data Lineage Architecture

### Layers & Connections

```
┌─────────────────┐
│ Source Systems  │  (CRM, billing, product databases)
│ ┌─────────────┐ │
│ │ Customers   │ │
│ │ Promotions  │ │
│ │ Billing     │ │
│ │ Churn Data  │ │
│ └─────────────┘ │
└────────┬────────┘
         │ Airflow: Scheduled Ingest
         ▼
┌─────────────────┐
│ Bronze Layer    │  (raw, immutable)
│ ┌─────────────┐ │
│ │ raw_*       │ │
│ │ Timestamped │ │
│ │ No transform│ │
│ └─────────────┘ │
└────────┬────────┘
         │ dbt: Cleanse + Denormalize
         ▼
┌─────────────────┐
│ Silver Layer    │  (trusted, tested)
│ ┌─────────────┐ │
│ │ trusted_*   │ │
│ │ Deduplicated│ │
│ │ Validated   │ │
│ └─────────────┘ │
└────────┬────────┘
         │ dbt: Business Logic
         ▼
┌─────────────────┐
│ Gold Layer      │  (metrics, dimensions)
│ ┌─────────────┐ │
│ │ fact_*      │ │
│ │ dim_*       │ │
│ │ Aggregated  │ │
│ └─────────────┘ │
└────────┬────────┘
         │ Streamlit
         ▼
┌─────────────────┐
│ Presentation    │  (dashboards)
│ ┌─────────────┐ │
│ │ Visualized  │ │
│ │ Interactive │ │
│ └─────────────┘ │
└─────────────────┘
```

### Metadata Captured

**At Each Layer**:
```
Bronze:
  - Source system identifier
  - Load timestamp (when ingested)
  - Row count and data size
  - Transformation job ID (Airflow task)
  - Data freshness (delta from source)

Silver:
  - Lineage: which Bronze tables used
  - Transformation logic (dbt model SQL)
  - Column mappings (Bronze → Silver)
  - Test results (data quality checks)
  - Schema: column names, types, descriptions
  - Downstream dependencies (which models depend on this?)

Gold:
  - Lineage: which Silver tables used
  - Business logic: aggregation rules, metric definitions
  - Calculation metadata (counts, sums)
  - Owner and SLA target
  - Change history (schema versions)

Presentation:
  - Dashboard ID and definition
  - Data source (Gold tables used)
  - Query performance metrics
  - User access logs
```

---

## Provenance Tracking Implementation

### Airflow: Bronze Layer Ingestion

**Every ingestion captures**:

```python
# In Airflow DAG
from datetime import datetime
import uuid

def ingest_customers():
    """Ingest raw customer data with full provenance"""
    
    ingestion_id = str(uuid.uuid4())  # Unique batch ID
    load_time = datetime.utcnow()
    
    # Source metadata
    source_metadata = {
        'source_system': 'CRM_API',
        'source_table': 'customers',
        'batch_id': ingestion_id,
        'load_timestamp': load_time,
        'source_freshness_lag_hours': calculate_source_lag()
    }
    
    # Ingest data
    df = query_source_system('SELECT * FROM customers WHERE updated > ?', source_lag)
    
    # Add provenance columns
    df['_ingestion_batch_id'] = ingestion_id
    df['_load_timestamp'] = load_time
    df['_source_system'] = 'CRM_API'
    
    # Write to Bronze
    write_to_bronze('bronze.raw_customers', df)
    
    # Log to lineage database
    log_ingestion({
        **source_metadata,
        'row_count': len(df),
        'data_size_mb': df.memory_usage(deep=True).sum() / 1_000_000,
        'job_id': os.getenv('AIRFLOW_JOB_ID'),
        'dag_run_id': context['dag_run'].run_id
    })
```

**Provenance Schema** (stored alongside data):
```python
@dataclass
class IngestionProvenance:
    """Metadata for Bronze layer ingestion"""
    batch_id: str                    # Unique identifier for this batch
    source_system: str               # Where did data come from?
    source_table: str                # Which table in source?
    load_timestamp: datetime         # When did we ingest?
    source_freshness_lag_hours: int  # How stale was source data?
    airflow_dag_id: str              # Which DAG ran?
    airflow_task_id: str             # Which task in DAG?
    row_count: int                   # How many rows ingested?
    data_size_mb: float              # Size of payload
    data_hash: str                   # SHA256(data) for uniqueness
```

### dbt: Silver & Gold Layer Transformations

**Lineage automatically captured by dbt**:

```sql
-- In dbt model: silver/trusted_customers.sql
{{ config(
  materialized='table',
  meta={
    'owner': 'data_analytics_team',
    'sla': 'daily_9am',
    'description': 'Deduplicated, validated customer master'
  }
) }}

-- dbt automatically tracks:
-- 1. Source: bronze.raw_customers (Bronze source)
-- 2. This model: silver.trusted_customers
-- 3. Downstream: gold.dim_customer

SELECT
  customer_id,
  email,
  signup_date,
  -- Add metadata
  CURRENT_TIMESTAMP() as computed_at,
  '{{ run_started_at }}' as dbt_run_timestamp,
  '{{ invocation_id }}' as dbt_invocation_id,
  -- Provenance: track which Bronze record
  _ingestion_batch_id as source_batch_id,
  _load_timestamp as source_load_time
FROM {{ source('bronze', 'raw_customers') }}
WHERE _deleted_flag IS NULL
  AND email IS NOT NULL  -- Validation: remove nulls
```

**Generated Manifest**:
```json
{
  "nodes": {
    "model.predictive_ltv.trusted_customers": {
      "name": "trusted_customers",
      "description": "Deduplicated, validated customer master",
      "fqn": ["predictive_ltv", "silver", "trusted_customers"],
      "depends_on": {
        "nodes": ["source.bronze.raw_customers"],
        "macros": []
      },
      "columns": [
        {
          "name": "customer_id",
          "description": "Primary key",
          "tests": ["unique", "not_null"]
        }
      ],
      "compiled_code": "SELECT customer_id FROM bronze.raw_customers WHERE ...",
      "meta": {
        "owner": "data_analytics_team",
        "sla": "daily_9am"
      }
    }
  }
}
```

**dbt Lineage Query** (programmatic access):

```python
import json
import dbt.logger

def get_model_lineage(model_name):
    """Query dbt manifest for lineage"""
    
    with open('target/manifest.json') as f:
        manifest = json.load(f)
    
    # Find model
    model_node = next(
        (node for uid, node in manifest['nodes'].items() 
         if node['name'] == model_name),
        None
    )
    
    if not model_node:
        raise ValueError(f"Model {model_name} not found")
    
    return {
        'upstream': model_node['depends_on']['nodes'],  # What sources this from
        'downstream': find_downstream_models(model_node, manifest),  # What depends on this
        'tables': extract_table_references(model_node['raw_code']),
        'columns': model_node['columns'],
        'owner': model_node['meta'].get('owner'),
        'tests': [
            test for col in model_node['columns']
            for test in col.get('tests', [])
        ]
    }
```

---

## Lineage Query Patterns

### Pattern 1: Trace Data Backward (Impact Analysis)

**Question**: "Customer LTV metric changed. Why?"

```sql
-- Query: Find what data changed in upstream layers
SELECT 
  'Bronze' as layer,
  'raw_customers' as table_name,
  COUNT(*) as row_count,
  MAX(_load_timestamp) as latest_load,
  COUNT(DISTINCT _ingestion_batch_id) as batches_today
FROM bronze.raw_customers
WHERE DATE(_load_timestamp) = CURRENT_DATE()
  AND (_load_timestamp >= NOW() - INTERVAL '1 hour')  -- Recent loads
GROUP BY layer, table_name

UNION ALL

SELECT 
  'Silver' as layer,
  'trusted_customers' as table_name,
  COUNT(*) as row_count,
  MAX(updated_at) as last_updated,
  STRING(CARDINALITY(COLLECT_SET(dbt_invocation_id))) as dbt_runs
FROM silver.trusted_customers
WHERE DATE(updated_at) = CURRENT_DATE()
  AND (updated_at >= NOW() - INTERVAL '1 hour')
GROUP BY layer, table_name

UNION ALL

SELECT 
  'Gold' as layer,
  'fact_customer_ltv' as table_name,
  COUNT(*) as row_count,
  MAX(computed_at) as last_computed,
  STRING(CARDINALITY(COLLECT_SET(dbt_invocation_id))) as dbt_runs
FROM gold.fact_customer_ltv
WHERE DATE(computed_at) = CURRENT_DATE()
  AND (computed_at >= NOW() - INTERVAL '1 hour')
GROUP BY layer, table_name
```

**Result**:
```
Layer    Table                  Row Count  Latest    Details
─────────────────────────────────────────────────────────────────
Bronze   raw_customers         120,000    09:15:00  ✅ Fresh
Silver   trusted_customers     119,500    09:30:00  ✅ Clean
Gold     fact_customer_ltv      98,750    10:00:00  ⚠️ 1% missing (normal)
```

### Pattern 2: Trace Data Forward (Blast Radius)

**Question**: "We fixed a bug in Bronze raw_churn. Which downstream metrics are affected?"

```python
def find_downstream_impact(changed_table):
    """Find all models impacted by a table change"""
    
    with open('target/manifest.json') as f:
        manifest = json.load(f)
    
    # Start: find all models that reference changed_table
    def find_dependents(table_ref, depth=0, visited=None):
        if visited is None:
            visited = set()
        if table_ref in visited or depth > 5:
            return []
        
        visited.add(table_ref)
        
        dependents = []
        for uid, node in manifest['nodes'].items():
            if table_ref in node['depends_on']['nodes']:
                dependents.append({
                    'name': node['name'],
                    'layer': extract_layer(node['fqn']),
                    'owner': node['meta'].get('owner'),
                    'sla': node['meta'].get('sla'),
                    'children': find_dependents(uid, depth+1, visited)
                })
        
        return dependents
    
    source_uid = f"source.bronze.{changed_table}"
    impact = find_dependents(source_uid)
    
    return {
        'changed_table': changed_table,
        'directly_affected': len(flatten(impact)),
        'tree': impact
    }

# Example output:
# {
#   'changed_table': 'raw_churn',
#   'directly_affected': 12,
#   'tree': [
#     {
#       'name': 'trusted_churn',
#       'layer': 'silver',
#       'owner': 'analytics_team',
#       'sla': 'daily_9am',
#       'children': [
#         {
#           'name': 'fact_churn_predictions',
#           'layer': 'gold',
#           'owner': 'ml_engineering',
#           'sla': 'daily_10am',
#           'children': [
#             {
#               'name': 'churn_dashboard_page',
#               'layer': 'presentation',
#               'owner': 'bi_team',
#               'sla': 'daily_10:30am',
#               'children': []
#             }
#           ]
#         }
#       ]
#     }
#   ]
# }
```

### Pattern 3: Schema Change Tracking

**Question**: "When was the LTV column added to customer metrics?"

```sql
-- Track schema changes via dbt artifacts
SELECT 
  DATE(run_started_at) as run_date,
  model_name,
  'COLUMN_ADDED' as change_type,
  column_name,
  column_type
FROM dbt_schema_changes
WHERE model_name = 'fact_customer_ltv'
  AND change_type = 'COLUMN_ADDED'
ORDER BY run_date DESC

-- Result:
-- 2026-04-01  fact_customer_ltv  COLUMN_ADDED  ltv_segment  VARCHAR
-- 2026-03-15  fact_customer_ltv  COLUMN_ADDED  ltv_amount   DECIMAL
```

---

## Lineage Visualization

### Lineage Graph (dbt docs + custom)

**dbt docs** (built-in):
- Generates `index.html` with interactive lineage graph
- Hover over nodes to see SQL and descriptions
- Navigate upstream/downstream dependencies
- Export to PNG for documentation

**Setup**:
```bash
# Generate docs
dbt docs generate

# View locally
dbt docs serve  # Opens http://localhost:8000

# Deploy docs
# Push docs JSON to S3 or Git Pages
aws s3 cp target/manifest.json s3://docs-bucket/manifest.json
aws s3 cp target/catalog.json s3://docs-bucket/catalog.json
```

### Custom Lineage Graph (Python/D3.js)

**Interactive visualization** (Streamlit page):

```python
# streamlit_app/pages/5_Data_Lineage.py
import streamlit as st
import json
from pathlib import Path
import plotly.graph_objects as go

st.set_page_config(page_title="Data Lineage", layout="wide")
st.title("📊 Data Lineage Graph")

# Load manifest
with open('target/manifest.json') as f:
    manifest = json.load(f)

# UI: Search for model
selected_model = st.selectbox(
    "Select a model to explore",
    options=sorted([n['name'] for n in manifest['nodes'].values() if 'model' in n['fqn']])
)

# Display lineage depth
col1, col2 = st.columns(2)
with col1:
    upstream_depth = st.slider("Upstream depth", 1, 5, 2)
with col2:
    downstream_depth = st.slider("Downstream depth", 1, 5, 2)

# Build graph
def build_lineage_graph(model_name, upstream_d, downstream_d):
    """Build Plotly network graph"""
    nodes_set = set()
    edges_list = []
    
    # Find model
    model_node = next(
        (n for n in manifest['nodes'].values() if n.get('name') == model_name),
        None
    )
    
    if not model_node:
        return None
    
    # Traverse upstream
    def traverse_upstream(node, depth):
        if depth <= 0:
            return
        for dep_uid in node['depends_on']['nodes']:
            dep_node = manifest['nodes'].get(dep_uid, {})
            nodes_set.add(dep_node.get('name', dep_uid))
            edges_list.append((dep_node.get('name'), node.get('name')))
            traverse_upstream(dep_node, depth - 1)
    
    # Traverse downstream
    def traverse_downstream(target_node, depth):
        if depth <= 0:
            return
        for uid, node in manifest['nodes'].items():
            if target_node['name'] in [
                m.get('name') for m in 
                [manifest['nodes'].get(d) for d in node['depends_on']['nodes']]
            ]:
                nodes_set.add(node.get('name'))
                edges_list.append((target_node.get('name'), node.get('name')))
                traverse_downstream(node, depth - 1)
    
    nodes_set.add(model_name)
    traverse_upstream(model_node, upstream_d)
    traverse_downstream(model_node, downstream_d)
    
    # Create Plotly graph
    x_pos = {node: i * 100 for i, node in enumerate(sorted(nodes_set))}
    y_pos = {node: hash(node) % 200 for node in nodes_set}
    
    edge_x = []
    edge_y = []
    for source, target in edges_list:
        edge_x.extend([x_pos[source], x_pos[target], None])
        edge_y.extend([y_pos[source], y_pos[target], None])
    
    fig = go.Figure()
    
    # Add edges
    fig.add_trace(go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=2, color='#cccccc'),
        hoverinfo='none',
        showlegend=False
    ))
    
    # Add nodes
    fig.add_trace(go.Scatter(
        x=[x_pos[n] for n in nodes_set],
        y=[y_pos[n] for n in nodes_set],
        mode='markers+text',
        text=[n for n in nodes_set],
        textposition="top center",
        hoverinfo='text',
        hovertext=[f"{n} ({get_model_type(n, manifest)})" for n in nodes_set],
        marker=dict(
            size=[15 if n == model_name else 10 for n in nodes_set],
            color=['#FF6B6B' if n == model_name else '#4ECDC4' for n in nodes_set],
            line=dict(width=2)
        )
    ))
    
    return fig

# Display graph
graph = build_lineage_graph(selected_model, upstream_depth, downstream_depth)
if graph:
    st.plotly_chart(graph, use_container_width=True)
    
    # Show details
    st.subheader("📋 Model Details")
    model_node = next(
        (n for n in manifest['nodes'].values() if n.get('name') == selected_model),
        None
    )
    if model_node:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Owner", model_node['meta'].get('owner', 'N/A'))
        with col2:
            st.metric("SLA", model_node['meta'].get('sla', 'N/A'))
        with col3:
            st.metric("Materialization", model_node['config'].get('materialized', 'view'))
        
        st.text_area("SQL", value=model_node['raw_code'], height=200)
```

### Metadata Report (Daily Export)

```python
# scripts/export_lineage_metadata.py
import json
import pandas as pd
from datetime import datetime

def export_lineage_manifest():
    """Export lineage metadata as CSV for reporting"""
    
    with open('target/manifest.json') as f:
        manifest = json.load(f)
    
    rows = []
    for uid, node in manifest['nodes'].items():
        if 'model' not in node.get('fqn', []):
            continue
        
        rows.append({
            'model_name': node['name'],
            'layer': extract_layer(node['fqn']),
            'owner': node['meta'].get('owner'),
            'sla': node['meta'].get('sla'),
            'upstream_sources': len(node['depends_on']['nodes']),
            'column_count': len(node.get('columns', {})),
            'test_count': sum(
                len(col.get('tests', [])) 
                for col in node.get('columns', {}).values()
            ),
            'materialization': node['config'].get('materialized'),
            'description': node.get('description', '')
        })
    
    df = pd.DataFrame(rows)
    
    # Export
    filename = f"lineage_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(f"reports/{filename}", index=False)
    
    print(f"Exported {len(df)} models to {filename}")
    return df
```

---

## Unity Catalog Integration

### Setting Up Unity Catalog

**Unity Catalog** provides centralized metadata governance across Databricks workspaces.

**Architecture**:
```
┌──────────────────────────────────────────────────┐
│       Unity Catalog (Metadata Hub)               │
│  ┌────────────────────────────────────────────┐  │
│  │ Bronze Schema                              │  │
│  │  - raw_customers                          │  │
│  │  - raw_promotions                         │  │
│  └────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────┐  │
│  │ Silver Schema                              │  │
│  │  - trusted_customers                      │  │
│  │  - trusted_billing                        │  │
│  └────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────┐  │
│  │ Gold Schema                                │  │
│  │  - fact_customer_ltv                      │  │
│  │  - dim_customer                           │  │
│  └────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────┘
         ↓ Lineage + Metadata tracked
┌──────────────────────────────────────────────────┐
│       Lineage Graph Engine                       │
│  (Queries, transformations, dependencies)       │
└──────────────────────────────────────────────────┘
```

### Catalog Configuration (dbt → Unity Catalog)

```yaml
# In dbt/profiles.yml
predictive-ltv:
  outputs:
    dev:
      type: databricks
      threads: 4
      catalog: predictive_ltv_dev  # UC catalog
      schema: bronze
      host: "{{ env_var('DATABRICKS_HOST') }}"
      http_path: "{{ env_var('DATABRICKS_HTTP_PATH') }}"
      token: "{{ env_var('DATABRICKS_TOKEN') }}"
      
    prod:
      type: databricks
      threads: 8
      catalog: predictive_ltv_prod  # UC catalog
      schema: bronze  # Will be set per model
      host: "{{ env_var('DATABRICKS_HOST') }}"
      http_path: "{{ env_var('DATABRICKS_HTTP_PATH') }}"
      token: "{{ env_var('DATABRICKS_TOKEN') }}"
```

### Lineage Metadata in UC

```python
# scripts/push_lineage_to_uc.py
from databricks_table_lineage import get_lineage_graph

def push_lineage_to_unity_catalog():
    """Push dbt lineage to Unity Catalog"""
    
    # Load dbt manifest
    with open('target/manifest.json') as f:
        manifest = json.load(f)
    
    # Create lineage records
    for uid, node in manifest['nodes'].items():
        if 'model' not in node.get('fqn', []):
            continue
        
        # For each upstream source
        for upstream_uid in node['depends_on']['nodes']:
            upstream_node = manifest['nodes'].get(upstream_uid, {})
            
            # Record lineage in UC
            lineage_record = {
                'upstream_catalog': 'predictive_ltv',
                'upstream_schema': extract_schema(upstream_node),
                'upstream_table': upstream_node.get('name'),
                
                'downstream_catalog': 'predictive_ltv',
                'downstream_schema': extract_schema(node),
                'downstream_table': node.get('name'),
                
                'transformation_type': 'dbt_model',
                'transformation_logic': node['raw_code'],
                'owner': node['meta'].get('owner'),
                'sla': node['meta'].get('sla'),
                'last_updated': datetime.now().isoformat()
            }
            
            # Store in UC metadata table
            spark.sql("""
                INSERT INTO predictive_ltv_prod.governance.lineage_graph
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, lineage_record.values())
```

### Querying UC Lineage

```sql
-- Query lineage in UC: What data flows from raw_customers to fact_customer_ltv?
WITH lineage_path AS (
  SELECT 
    upstream_table,
    downstream_table,
    transformation_logic,
    owner,
    sla,
    1 as hop_distance
  FROM predictive_ltv_prod.governance.lineage_graph
  WHERE upstream_table = 'raw_customers'
  
  UNION ALL
  
  SELECT 
    lp.upstream_table,
    lg.downstream_table,
    lg.transformation_logic,
    lg.owner,
    lg.sla,
    lp.hop_distance + 1
  FROM lineage_path lp
  JOIN predictive_ltv_prod.governance.lineage_graph lg
    ON lp.downstream_table = lg.upstream_table
  WHERE lp.hop_distance < 5  -- Prevent cycles
)
SELECT DISTINCT
  upstream_table,
  downstream_table,
  hop_distance,
  owner,
  sla
FROM lineage_path
ORDER BY hop_distance, downstream_table
```

---

## Testing Lineage Integrity

### Test 1: Verify No Orphaned Tables

```python
def test_no_orphaned_tables():
    """Every table should have upstream source or be root"""
    
    with open('target/manifest.json') as f:
        manifest = json.load(f)
    
    orphans = []
    for uid, node in manifest['nodes'].items():
        if 'model' not in node.get('fqn', []):
            continue
        
        # Root tables (Bronze) are allowed to have no upstream
        if 'bronze' in node['fqn']:
            continue
        
        # All other tables must have upstream
        if not node['depends_on']['nodes']:
            orphans.append(node['name'])
    
    assert len(orphans) == 0, f"Orphaned models found: {orphans}"
```

### Test 2: Verify Circular Dependencies

```python
def test_no_circular_dependencies():
    """No table should have circular references"""
    
    with open('target/manifest.json') as f:
        manifest = json.load(f)
    
    def has_cycle(node, visited=None, path=None):
        if visited is None:
            visited = set()
        if path is None:
            path = []
        
        node_uid = node.get('unique_id')
        if node_uid in path:
            return True  # Cycle detected
        
        path.append(node_uid)
        
        for dep_uid in node['depends_on']['nodes']:
            dep_node = manifest['nodes'].get(dep_uid, {})
            if has_cycle(dep_node, visited, path.copy()):
                return True
        
        visited.add(node_uid)
        return False
    
    cycles = []
    for uid, node in manifest['nodes'].items():
        if has_cycle(node):
            cycles.append(node['name'])
    
    assert len(cycles) == 0, f"Circular dependencies found: {cycles}"
```

### Test 3: Verify Lineage Metadata Consistency

```python
def test_lineage_metadata_consistency():
    """Lineage graph should match transformation logic"""
    
    with open('target/manifest.json') as f:
        manifest = json.load(f)
    
    for uid, node in manifest['nodes'].items():
        if 'model' not in node.get('fqn', []):
            continue
        
        declared_sources = node['depends_on']['nodes']
        
        # Parse SQL to find actual sources
        actual_sources = extract_table_references(node['raw_code'])
        
        # Check consistency
        declared_names = {
            manifest['nodes'].get(dep, {}).get('name') 
            for dep in declared_sources
        }
        
        discrepancies = actual_sources - declared_names
        assert len(discrepancies) == 0, \
            f"Model {node['name']} has undeclared sources: {discrepancies}"
```

---

## Lineage Documentation Templates

### Template 1: Model Lineage Card

```markdown
## Model: fact_customer_ltv

**Purpose**: Primary fact table for customer lifetime value metrics

**Layer**: Gold (Metrics)

**Owner**: Analytics Engineering Team (@analytics-eng)

**SLA**: Daily by 10:00 AM

**Upstream Sources**:
- `silver.trusted_customers` (customer master)
- `silver.trusted_billing` (revenue history)
- `silver.trusted_churn` (churn signals)

**Downstream Consumers**:
- `dashboard.ltv_analysis_page` (Streamlit)
- `gold.agg_ltv_by_segment` (aggregation table)
- `bi_tool.ltv_report` (BI export)

**Key Columns**:
| Column | Type | Description | Source |
|--------|------|-------------|--------|
| customer_id | BIGINT | Customer unique ID | trusted_customers |
| ltv_amount | DECIMAL(15,2) | Predicted lifetime value | billing calculation |
| churn_risk | FLOAT | Probability of churn | churn ML model |

**Transformation Logic**:
1. Join trusted_customers (dimensions)
2. Aggregate revenue from trusted_billing (5-year history)
3. Apply churn risk from ML model
4. Compute LTV = (revenue * retention_rate)

**Tests**:
- ✅ customer_id: not_null, unique
- ✅ ltv_amount: not_null, between(0, 1000000)
- ✅ Row count: >= 50000

**Last Updated**: 2026-04-07 10:00:00 UTC

**Change History**:
- 2026-03-15: Added churn_risk column
- 2026-02-01: Initial deployment
```

### Template 2: Impact Analysis Report

```markdown
## Impact Analysis: Update to raw_churn Table

**Change**: Added new column `cancellation_reason` to capture cancellation details

**Affected Downstream Models**: 12 total

**Blast Radius**:
```
Layer    Count   Models
─────────────────────────────
Silver   2       trusted_churn, trusted_churn_detailed
Gold     5       fact_churn_predictions, agg_churn_by_segment, etc.
Presentation 3   churn_dashboard, churn_report, etc.
```

**Recomputation Required**:
```bash
dbt run -s raw_churn+  # Recompute all downstream models
dbt test -s raw_churn+ # Re-test all impacted models
```

**Estimated Time**: 15 minutes

**Testing**:
- ✅ All downstream tests pass
- ✅ Row counts unchanged
- ✅ Data quality checks pass
```

---

## Success Criteria

✅ Lineage framework documented (this document)  
✅ Provenance metadata captured at each layer  
✅ dbt manifest auto-generated for queries  
✅ Lineage visualization in Streamlit  
✅ Unity Catalog integration defined  
✅ Testing procedures for lineage integrity  
✅ Ready for Batch 4 SLA monitoring implementation

