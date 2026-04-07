# Phase 3 Command Log: Gold Modeling and Thesis Engine

## Build and validation workflow

```bash
# Parse dbt graph
DBT_PROFILES_DIR=$(pwd) .venv/bin/dbt parse --project-dir .

# Enforce code quality
make format
make lint
make test
```

## Phase 3 model execution (Databricks runtime required)

```bash
# Run gold models and python models
DBT_PROFILES_DIR=$(pwd) .venv/bin/dbt run --select marts

# Run model-level and singular tests for phase 3
DBT_PROFILES_DIR=$(pwd) .venv/bin/dbt test --select marts test_survival_target_cohorts test_model_drift_within_baseline
```

## Key artifacts produced in Phase 3

- `models/marts/fct_gold_customer_features.sql`
- `models/marts/fct_customer_ltv.sql`
- `models/marts/fct_survival_curves.py`
- `models/marts/fct_churn_scores.py`
- `models/marts/fct_survival_cohort_summary.sql`
- `models/marts/fct_model_quality_diagnostics.sql`
- `models/marts/fct_model_drift_baseline.sql`

## Why this command structure

- Parse-first catches dependency and contract regressions early.
- Lint/test gates keep repository quality stable independent of warehouse runtime.
- Runtime dbt execution is isolated because Python dbt models require active Databricks execution context.
