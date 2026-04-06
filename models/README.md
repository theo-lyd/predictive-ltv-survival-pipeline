# Medallion Architecture

## Layer Structure

The project uses a three-layer Medallion architecture for data governance:

### Bronze (Raw Layer)
- **Purpose**: Immutable append-only ingestion of raw source data.
- **Schema**: `default` (or `bronze` if separate)
- **Materialization**: Parquet/Delta in cloud storage
-  **Characteristics**: 
  - Full historical audit trail
  - Preserves original data quality issues
  - Timestamps for ingestion tracking

### Silver (Trusted Layer)
- **Purpose**: Cleaned, standardized, and validated data.
- **Schema**: `stg_*` for staging models, `silver` if separate
- **Materialization**: Delta tables
- **Characteristics**:
  - Business logic applied
  - Data quality validation
  - Deduplication and identity stitching
  - Standardized types and formats

### Gold (Analytics Layer)
- **Purpose**: Business-ready metrics and analytical outputs.
- **Schema**: `marts`
- **Materialization**: Delta tables
- **Characteristics**:
  - Fact and dimension tables
  - LTV, churn, and survival metrics
  - Governed through Unity Catalog
  - Ready for BI consumption

## Directory Structure

```
models/
├── staging/           # Silver layer: stg_* models
│   ├── stg_customers.sql
│   ├── stg_promotions.sql
│   └── schema.yml
├── marts/             # Gold layer: fct_* and dim_* models
│   ├── fct_customer_ltv.sql
│   └── schema.yml
├── sources.yml        # Source definitions (Bronze)
└── README.md

macros/
├── generate_schema_name.sql
├── get_date_columns.sql
└── README.md
```

## Naming Conventions

- **Sources**: `src_*` prefix in `sources.yml`
- **Staging (Silver)**: `stg_*` prefix
- **Facts (Gold)**: `fct_*` prefix
- **Dimensions (Gold)**: `dim_*` prefix
- **Archived**: `arch_*` prefix

## Testing and Validation

Each layer includes:
- `schema.yml` with field-level documentation and tests
- Great Expectations checkpoints for critical rules
- dbt native tests for uniqueness, not-null, relationships
