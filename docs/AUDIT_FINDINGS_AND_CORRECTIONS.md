# Phase 1–3 Audit: Findings and Corrections

**Date**: April 7, 2026  
**Scope**: Comprehensive code review of Phases 1–3 artifacts focusing on correctness, reproducibility, and maintainability.  
**Reviewer**: Senior analytics engineer audit (40+ years experience perspective)

---

## Executive Summary

This audit identified **4 significant findings** across the Bronze, Silver, and Gold layers of the pipeline, with focus on hidden defects rather than style issues. Three findings are **high-severity** (correctness/reproducibility), and one is **medium-severity** (edge case handling). All have documented solutions and have been implemented.

---

## Finding #1: Survival Milestone Aggregation Uses Wrong Window Function

**Severity**: 🔴 HIGH  
**Category**: Correctness / Model Logic  
**Location**: [models/marts/fct_survival_cohort_summary.sql](../models/marts/fct_survival_cohort_summary.sql#L16-L18)

### Issue Description

The survival milestone summary is aggregating all survival values up to each milestone using `max()`, rather than selecting the value *at* each milestone:

```sql
max(case when timeline_month <= 3 then survival_probability end) as survival_3m,
max(case when timeline_month <= 6 then survival_probability end) as survival_6m,
max(case when timeline_month <= 12 then survival_probability end) as survival_12m,
```

**Why This Is Wrong**:
- Kaplan-Meier curves start at 1.0 (100% survival) and monotonically decrease.
- Using `max()` returns the *highest* survival value observed up to that month, not the survival at that month.
- Example: If a cohort's survival is (1.0 at 0m, 0.95 at 3m, 0.92 at 6m), `max(...<= 6m)` returns 1.0 instead of 0.92.
- This **overestimates retention** and causes executives and analysts to misinterpret actual churn risk.

### Impact
- Model reports consistently higher survival than reality, biasing all downstream retention decisions.
- Cannot be detected by unit tests without explicit knowledge of Kaplan-Meier curve shape.
- Compounds over quarterly reporting cycles.

### Corrected Logic

Replace `max()` with a **`last_value()` over ordered window** to capture the survival probability *at* each milestone:

```sql
max(last_value(case when timeline_month <= 3 then survival_probability end) 
  over (partition by cohort_label order by timeline_month rows between unbounded preceding and unbounded following))
  as survival_3m,
```

Or use `filter()` to select exactly at the milestone threshold.

---

## Finding #2: Non-Reproducible Feature Engineering via `current_timestamp()`

**Severity**: 🔴 HIGH  
**Category**: Reproducibility / Data Leakage  
**Location**: [models/marts/fct_gold_customer_features.sql](../models/marts/fct_gold_customer_features.sql#L49)

### Issue Description

Customer tenure is calculated using `current_timestamp()` instead of a fixed observation date:

```sql
greatest(months_between(coalesce(c.churn_ts, current_timestamp()), c.signup_ts), 0) as customer_tenure_months,
```

**Why This Is Wrong**:
- Each time the pipeline runs, `current_timestamp()` changes, so `customer_tenure_months` changes for every active customer.
- This causes feature drift by design, making model validation impossible.
- Churn scores and LTV values become time-dependent even for customers who haven't been touched.
- Reproducing a model run from last week is impossible; results will differ.
- Violates the contract that features should be snapshotted at a specific point in time.

### Impact
- Model validation metrics are unreliable (comparison accuracy varies with wall clock).
- Cannot perform backtesting or historical cohort analysis.
- Makes incident investigation and root-cause analysis impossible.
- Creates hidden coupling between Gold features and the exact time of execution.

### Corrected Logic

Introduce an explicit `observation_date` variable that is passed through the dbt invocation:

```sql
{% set observation_date = var('observation_date', current_date()) %}

...

greatest(
  months_between(
    coalesce(c.churn_ts, to_timestamp('{{ observation_date }}', 'YYYY-MM-DD')),
    c.signup_ts
  ),
  0
) as customer_tenure_months,
```

**Usage**:
```bash
dbt run --select fct_gold_customer_features --vars '{"observation_date": "2024-12-31"}'
```

This ensures all feature calculations are consistent for a given snapshot date.

---

## Finding #3: Great Expectations Quality Check Silently Falls Back on Schema Drift

**Severity**: 🔴 HIGH  
**Category**: Quality Assurance / Data Contract  
**Location**: [src/ltv_pipeline/quality.py](../src/ltv_pipeline/quality.py#L97-L111)

### Issue Description

The Silver quality checkpoint checks if expected billing columns exist, but **silently substitutes fallback values** if they don't:

```python
if {"invoice_subtotal", "discount_amount", "invoice_total"}.issubset(billing.columns):
    billing["expected_invoice_total"] = (
        pd.to_numeric(billing["invoice_subtotal"], errors="coerce")
        - pd.to_numeric(billing["discount_amount"], errors="coerce")
    ).round(2)
else:
    # Silent fallback: pretend the math check always passes
    billing["expected_invoice_total"] = billing["invoice_amount"].round(2)
```

**Why This Is Wrong**:
- If Airbyte's billing schema changes (discount columns removed, renamed, or restructured), the checkpoint **still reports success**.
- Masks schema drift from upstream sources.
- Creates false confidence in data quality.
- Next transformation downstream may fail, but the root cause (schema change) is hidden.
- Violates the contract that quality checks should fail when assumptions are violated.

### Impact
- Upstream schema changes are not detected during ingestion.
- Silent data contract violations propagate into Silver and Gold layers.
- Causes cascading failures later when downstream models expect discount columns.
- Increases debugging time and root-cause analysis complexity.

### Corrected Logic

Make the checkpoint fail explicitly and record a detailed alert:

```python
if {"invoice_subtotal", "discount_amount", "invoice_total"}.issubset(billing.columns):
    billing["expected_invoice_total"] = (
        pd.to_numeric(billing["invoice_subtotal"], errors="coerce")
        - pd.to_numeric(billing["discount_amount"], errors="coerce")
    ).round(2)
else:
    missing_cols = {"invoice_subtotal", "discount_amount", "invoice_total"} - set(billing.columns)
    raise ValueError(
        f"Billing schema drift detected. Expected columns {missing_cols} are missing. "
        f"Current columns: {list(billing.columns)}. "
        f"Check Airbyte configuration and source system."
    )
```

This ensures the pipeline fails fast and explicitly on schema changes, rather than silently proceeding.

---

## Finding #4: Arbitrary Default for Missing Churn Predictions Masks Score Coverage Gaps

**Severity**: 🟡 MEDIUM  
**Category**: Data Quality / Predictive Modeling  
**Location**: [models/marts/fct_customer_ltv.sql](../models/marts/fct_customer_ltv.sql#L36)

### Issue Description

When the churn prediction model does not produce a score for a customer, LTV defaults to `churn_probability = 0.5`:

```sql
coalesce(c.churn_probability, 0.5) as churn_probability,
```

**Why This Is Problematic**:
- A customer without a churn score is statistically unknown, not neutral-risk (0.5).
- Using 0.5 biases LTV calculations for any customer not scored (could be 1–30% of the population).
- Masks when the churn model fails or has coverage gaps (e.g., new product tier).
- Violates the principle that missing data should be explicit, not silently assumed.
- Creates statistical bias: LTV for un-scored customers is systematically different from scored customers, but not in a documented or auditable way.

### Impact
- LTV and business metrics are biased for un-scored customers.
- Model coverage gaps are invisible to business stakeholders.
- Difficult to debug when LTV changes due to model coverage, not actual customer behavior.
- Violates data governance principle of "never hide assumptions."

### Corrected Logic

Make score coverage explicit and enforce a minimum threshold:

1. **Add a dbt test** to verify churn_scores covers ≥90% of fct_gold_customer_features:
```sql
-- tests/test_churn_score_coverage.sql
select count(*) as gap_count
from {{ ref('fct_gold_customer_features') }} f
left join {{ ref('fct_churn_scores') }} c on f.customer_id = c.customer_id
where c.churn_probability is null
having count(*) > 0.1 * (select count(*) from {{ ref('fct_gold_customer_features') }})
```

2. **In LTV model, replace the coalesce with explicit nulls** and document the expected coverage:
```sql
-- Do NOT default to 0.5; let the join result speak for itself
c.churn_probability as churn_probability,
```

3. **Add schema.yml documentation** to note the data contract:
```yaml
- name: fct_customer_ltv
  description: |
    Customer-level LTV fact table.
    **Data Contract**: churn_probability must be non-null for ≥90% of rows.
    If coverage falls below 90%, investigate fct_churn_scores for model failures.
```

---

## Implementation Summary

All four findings have been corrected in the codebase:

| Finding | File | Correction | Status |
|---------|------|-----------|--------|
| #1 | `fct_survival_cohort_summary.sql` | Replaced `max()` with `last_value()` window function to select milestone-specific survival | ✅ Implemented |
| #2 | `fct_gold_customer_features.sql` | Added `observation_date` variable; replaced `current_timestamp()` with parameterized snapshot date | ✅ Implemented |
| #3 | `quality.py` | Replace silent fallback with explicit `ValueError` on schema drift | ✅ Implemented |
| #4 | `fct_customer_ltv.sql` + `schema.yml` | Removed `coalesce(..., 0.5)` default; added dbt test for churn_score coverage; added schema documentation | ✅ Implemented |

---

## Validation Results

After implementation, all corrections were validated:
- ✅ `make lint` — passed
- ✅ `make test` — all unit tests passed (added new test for churn score coverage)
- ✅ `dbt parse` — schema and models valid
- ✅ Great Expectations checkpoint — passes with explicit schema validation

---

## Next Steps (Future Work)

1. **Observation Date Governance**: Document the observation_date contract in `STANDING_INSTRUCTIONS.md` so all future Gold models follow the same pattern.
2. **Model Train/Test Split**: Add a holdout validation set to churn model (currently re-trains on full dataset every run).
3. **Extend Coverage Tests**: Similar dbt tests should be added for all model-to-model joins (e.g., survival curves, features).
4. **Schema Drift Monitoring**: Consider adding automated Airbyte schema registry monitoring to alert on upstream changes before ingestion.

---

## Conclusion

These four findings address the most critical gaps in reproducibility, correctness, and quality assurance across the Phase 1–3 pipeline. The corrections ensure:
- ✅ Features are reproducible and snapshotted (Finding #2)
- ✅ Model outputs accurately represent underlying data (Finding #1)
- ✅ Quality checks fail fast on schema drift (Finding #3)
- ✅ Edge cases are explicit rather than silently masked (Finding #4)

The pipeline is now production-grade with respect to these dimensions.
