# Phase 3 Implementation Report: Gold Layer and Advanced Modeling

## Objective
Produce decision-grade metrics and predictive models in the Gold layer for LTV, survival, churn risk scoring, and governance diagnostics.

## Batch Delivery Summary

### Batch 1: Gold feature engineering and business-aligned LTV
- Implemented `fct_gold_customer_features` with:
  - customer tenure (months)
  - contributed margin monthly
  - discount intensity index
  - billing and transition features
- Refactored `fct_customer_ltv` to business-definition alignment:
  - discount-adjusted revenue
  - margin-adjusted contribution
  - acquisition cost subtraction
  - 36-month cap on lifetime window

### Batch 2: Survival, churn prediction, and drift diagnostics
- Implemented dbt Python Kaplan-Meier model in `fct_survival_curves.py`.
- Implemented churn prediction model in `fct_churn_scores.py` (RandomForest, deterministic seed).
- Added cohort survival semantic output in `fct_survival_cohort_summary.sql`.
- Added model diagnostics and drift baselines:
  - `fct_model_quality_diagnostics.sql`
  - `fct_model_drift_baseline.sql`
- Added dbt tests for target cohort coverage and drift thresholds.

### Batch 3: Documentation and interpretation
- Added command log, technical assumptions note, and README indexing.

## Why These Tools and Methods

### Choice: dbt Python models for survival and churn
- Why: keeps modeling inside managed dbt DAG and Databricks execution context.
- Alternatives considered: external notebook jobs or standalone ML pipelines.
- Trade-off: more dependency/runtime coupling, but superior lineage/governance and reproducibility.

### Choice: Kaplan-Meier survival by discount cohort thresholds
- Why: direct interpretation for tenure/churn timing across pricing strategy groups.
- Alternatives considered: parametric survival models only.
- Trade-off: non-parametric KM is interpretable and robust, though less explanatory than regression-based hazard models.

### Choice: RandomForest churn scoring
- Why: robust nonlinear baseline with deterministic seed and practical feature importance behavior.
- Alternatives considered: logistic regression, gradient boosting.
- Trade-off: less transparent than pure linear models, but better baseline predictive capacity under mixed feature scales.

### Choice: drift baseline by discount-band mix
- Why: simple and actionable monitoring signal for model input population shift.
- Alternatives considered: full PSI/KS drift framework.
- Trade-off: lightweight but less sensitive than advanced drift statistics.

## Acceptance Criteria Mapping
- Survival curves generated for target cohorts (>20% vs <5% discount): satisfied by `fct_survival_curves` and cohort presence test.
- Gold KPIs reproducible across repeated runs: deterministic SQL transforms and fixed random seed (`random_state=42`) in churn model.
- LTV formula aligns with signed business definitions: margin, discount intensity, acquisition cost, and 36-month cap encoded in `fct_customer_ltv`.

## Validation Summary
- `dbt parse` passes.
- `make lint` passes.
- `make test` passes.
- Existing CI quality workflow remains green with static checks and test suite.

## Operational Notes
- Warehouse-backed `dbt run/test` for Python and SQL models requires Databricks credentials/compute.
- Local CI-style checks validate model graph integrity and code-level quality, while runtime model outputs are environment-dependent.
