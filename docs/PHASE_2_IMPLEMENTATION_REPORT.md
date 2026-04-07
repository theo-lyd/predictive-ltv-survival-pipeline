# Phase 2 Implementation Report: Silver Layer and Trusted Core

## Scope and Objective
Phase 2 implemented the Silver trusted core for cleaning, harmonization, and deterministic entity resolution.

## Batch Breakdown

### Batch 1: Silver dbt models and deterministic entity resolution
- Delivered typed, normalized staging models:
  - models/staging/stg_customers.sql
  - models/staging/stg_promotions.sql
  - models/staging/stg_billing.sql
- Added intermediate resolution models:
  - models/intermediate/int_promotions_resolved.sql
  - models/intermediate/int_discount_cohorts.sql
  - models/intermediate/int_customer_state_transitions.sql
  - models/intermediate/int_silver_bronze_reconciliation.sql
- Added critical dbt tests:
  - tests/test_mrr_non_negative.sql
  - tests/test_discount_start_precedes_churn.sql
  - tests/test_reconciliation_within_tolerance.sql

### Batch 2: Great Expectations checkpoints and validation artifacts
- Implemented checkpoint logic in src/ltv_pipeline/quality.py.
- Added checkpoint runner in src/scripts/run_silver_quality_checkpoint.py.
- Added GE suite/checkpoint definitions under great_expectations/.
- Added quality tests in tests/test_phase2_quality.py.

### Batch 3: Documentation and contract strategy
- Added implementation report, command log, data dictionary, and contract assumptions documentation.
- Updated README index with Phase 2 deliverables.

## Why These Choices Were Made

### Choice: dbt staging + intermediate split
- Why: Separates strict typing/harmonization from business-state modeling.
- Alternatives considered: Single-layer transformations in staging only.
- Trade-off: More models to maintain, but clearer lineage and lower blast radius for changes.

### Choice: Deterministic promotion identity stitching
- Why: Business keys must resolve consistently under duplicates/mixed source quality.
- Alternatives considered: Last-write-wins on promotion_id only.
- Trade-off: Additional key logic, but stable and auditable identity resolution.

### Choice: Great Expectations for runtime integrity
- Why: Captures row-level semantic constraints that SQL typing/tests alone cannot enforce.
- Alternatives considered: dbt tests only.
- Trade-off: Additional runtime step, but stronger quality evidence and artifacted validation reports.

### Choice: Bronze vs Silver reconciliation model
- Why: Enables trust checks with explicit tolerance gates.
- Alternatives considered: Spot checks and ad hoc SQL.
- Trade-off: Additional model and test maintenance, but repeatable quality controls in CI workflows.

## Contract and Null-Handling Highlights
- `discount_percent` remains nullable by design in Silver staging because Bronze intentionally carries source defects.
- `promotion_start_ts` parsing supports `%Y-%m-%d`, `%d/%m/%Y`, and `%Y/%m/%d` with deterministic precedence.
- Invoice math checkpoint supports two modes:
  - explicit subtotal/discount/total columns when provided,
  - fallback assumption `invoice_total = invoice_amount` when only amount is present.

## Acceptance Criteria Coverage
- Silver model set with tests: Implemented.
- GE suite and validation artifacts: Implemented.
- Data dictionary for core Silver entities: Implemented.
- Deterministic business key resolution: Implemented via `promotion_identity_key` + dedup ranking.
- Reconciliation within tolerance: Implemented in `int_silver_bronze_reconciliation` + singular tolerance test.

## Validation Summary
- `dbt parse` passes.
- `make lint` passes.
- `make test` passes.
- `make phase2-ge-check` passes and writes artifact to `data/quality/silver_ge_validation.json`.

## Known Constraints
- Full dbt `run/test` against Databricks requires valid workspace credentials and reachable compute.
- CI executes static and local integrity gates; warehouse-backed execution remains environment-dependent.
