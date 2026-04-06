# Phase 1 Implementation Report: Ingestion and Bronze Layer

## Status
- Phase: Phase 1 - Ingestion and Bronze Layer
- Implementation status: Complete
- Objective: Ingest heterogeneous and messy sources while preserving append-only historical fidelity

## Batch Plan and Execution

### Batch 1: Synthetic Promotions Generator
- Scope:
  - Implement tenure-correlated discount policy
  - Inject controlled quality defects (nulls, duplicates, mixed date formats)
  - Emit Parquet and XML payloads linked by customer_id
  - Emit reproducibility report with deterministic configuration
- Implemented artifacts:
  - src/ltv_pipeline/synthetic.py
  - src/scripts/generate_synthetic_metadata.py
  - tests/test_phase1_ingestion.py
- Deliverable mapping:
  - Synthetic promotion generator: Completed
  - XML + Parquet payload generation: Completed
  - Reproducibility report (seed/parameters): Completed

### Batch 2: Bronze Ingestion Engine and Airbyte Integration
- Scope:
  - Implement custom Spark ingest script for ugly file handling
  - Add header skip, encoding fallback, numeric abbreviation normalization
  - Add append-only Bronze writes with ingestion metadata
  - Support Airbyte billing sync when enabled
- Implemented artifacts:
  - src/scripts/run_bronze_ingest.py
  - src/ltv_pipeline/ingestion.py
  - config/airbyte/billing_sync.connection.json
- Deliverable mapping:
  - Bronze churn/promotions/billing ingestion: Completed
  - Airbyte-enabled billing sync: Completed (feature-flag via --airbyte-enabled)
  - Ingestion audit logs and row reconciliation: Completed

### Batch 3: dbt Source Contracts and Operability
- Scope:
  - Align source contracts with Bronze table naming
  - Add billing staging model
  - Add Phase 1 make targets and validation tests
- Implemented artifacts:
  - models/sources.yml
  - models/staging/stg_customers.sql
  - models/staging/stg_billing.sql
  - models/schema.yml
  - Makefile
- Deliverable mapping:
  - Bronze tables queryable via dbt source contracts: Completed
  - Non-destructive reruns supported by append mode: Completed

## Why This Tooling/Methodology Was Chosen

### Choice: Spark-based Bronze ingestion (instead of pandas-only pipeline)
- Why: Spark provides scalable ingestion semantics and aligns with Databricks production runtime.
- Alternatives considered:
  - pandas-only ingestion scripts
  - direct SQL load jobs
- Trade-offs:
  - Higher local startup overhead, but consistent with production execution model and schema handling.
- Reconsider when:
  - Data volume remains permanently tiny and infrastructure cost optimization is prioritized over platform parity.

### Choice: Append-only writes with ingestion metadata
- Why: Preserves immutable raw history and enables replay/debug lineage.
- Alternatives considered:
  - overwrite mode
  - merge/upsert directly in Bronze
- Trade-offs:
  - Storage growth increases over time, but historical fidelity and auditability are preserved.
- Reconsider when:
  - Regulatory constraints require retention windows and archival compaction strategy.

### Choice: Defect-injected synthetic promotions
- Why: Data quality checks are meaningful only when realistic defects exist.
- Alternatives considered:
  - perfectly clean synthetic datasets
  - production data snapshot
- Trade-offs:
  - Slightly more complex generation logic, but better reliability testing coverage.
- Reconsider when:
  - Production anonymized datasets are approved for development use.

### Choice: XML and Parquet dual payload generation
- Why: Simulates heterogeneous source feeds and validates multi-format ingest readiness.
- Alternatives considered:
  - Parquet only
  - CSV only
- Trade-offs:
  - Additional generation and parsing complexity, but broader ingestion robustness.
- Reconsider when:
  - Source integration standards become homogeneous and contract-enforced.

### Choice: Airbyte feature flag (--airbyte-enabled)
- Why: Enables optional billing sync without blocking baseline churn/promotions ingestion.
- Alternatives considered:
  - hard dependency on Airbyte
  - separate independent billing pipeline
- Trade-offs:
  - Adds conditional branch in ingestion flow, but improves deployment flexibility.
- Reconsider when:
  - Airbyte becomes mandatory in all deployment environments.

## Acceptance Criteria Verification

- Bronze tables append-only and queryable: Verified
  - Script uses mode append and adds ingestion_run_id + ingested_at_utc
- Re-run ingestion creates no destructive overwrite: Verified
  - No overwrite write mode used in Bronze ingestion
- Edge-case files processed without manual intervention: Verified
  - Encoding fallback: UTF-8 -> Latin-1
  - Header skip: --header-skip
  - Numeric normalization: K/Mio/million support

## Produced Runtime Deliverables
- Bronze table paths:
  - data/bronze/churn
  - data/bronze/promotions
  - data/bronze/billing
- Audit artifacts:
  - data/bronze/audit/ingestion_run_<run_id>.json
  - data/bronze/audit/row_count_reconciliation.csv
  - data/bronze/audit/synthetic_reproducibility.json

## Risks and Follow-up
- Delta format fallback:
  - Current script attempts Delta when requested, falls back to Parquet if Delta runtime is unavailable locally.
  - In Databricks production jobs, run with Delta-enabled cluster and use --prefer-delta.
- Source contracts:
  - Add freshness and anomaly checks in Phase 2 for stronger pipeline SLAs.
