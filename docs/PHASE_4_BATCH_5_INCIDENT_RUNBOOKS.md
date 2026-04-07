# Phase 4 Batch 5 Incident Runbooks

This document defines operator-facing runbooks for incidents detected by Monte Carlo and surfaced through Airflow.

## Bronze Layer Runbook

### Typical Symptoms
- Freshness incidents on raw customer or billing ingestion
- Volume drops after source extract
- Schema additions/removals in source tables

### Triage Steps
1. Confirm Airbyte run state for the same execution date.
2. Compare source-system export counts with Bronze table row counts.
3. Inspect ingestion logs for parsing or type-casting failures.
4. Validate source schema drift against expected Bronze contracts.

### Recovery Actions
1. Re-run Phase 1 and Phase 2 tasks for the impacted date.
2. For schema changes, update ingestion mapping and restart downstream processing.
3. Resolve Monte Carlo incident with a root-cause note.

## Silver Layer Runbook

### Typical Symptoms
- Data quality test regressions
- Unexpected row-count compression after deduplication
- Stale staging tables

### Triage Steps
1. Inspect dbt logs for failed models and tests.
2. Verify join keys and deduplication filters introduced in latest changes.
3. Compare Silver row counts against Bronze reference totals.

### Recovery Actions
1. Re-run Silver transforms and tests only.
2. Patch faulty transformations and re-test in isolated run.
3. Resolve incidents once contractual tests pass.

## Gold Layer Runbook

### Typical Symptoms
- LTV facts not refreshed in SLA window
- Churn probability outputs outside expected ranges
- Survival cohort schema drift

### Triage Steps
1. Review Gold model execution and test logs.
2. Validate Silver dependencies are complete and healthy.
3. Check metric validity constraints: non-negative LTV, probability in [0,1].

### Recovery Actions
1. Re-run Gold models and tests for the affected date.
2. Backfill historical window if feature drift is detected.
3. Resolve incidents with explanation of metric impact and mitigation.

## Escalation Rules
- CRITICAL: page on-call data engineer and notify analytics leadership.
- HIGH: notify data-engineering channel and assign incident owner.
- MEDIUM: create follow-up issue and track in team backlog.
- LOW: auto-resolve if remediation workflow confirms normal state.
