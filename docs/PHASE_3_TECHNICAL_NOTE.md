# Phase 3 Technical Note: Assumptions and Statistical Interpretation

## Modeling Assumptions

1. Tenure definition
- Tenure is measured in months from `signup_ts` to `churn_ts` if churned, else to current timestamp.

2. Discount intensity index
- Defined as `avg_discount_percent / 50`, clamped to [0, 1].
- Interpreted as normalized pricing pressure proxy.

3. Contributed margin
- Monthly contributed margin is `MRR * gross_margin_rate * (1 - discount_intensity_index)`.
- Gross margin rate is tier-based assumption:
  - enterprise: 0.72
  - pro: 0.68
  - basic/other: 0.62

4. LTV formula
- Signed-business alignment encoded as:
  - `discounted_revenue_ltv = MRR * capped_tenure_months * (1 - discount_intensity_index)`
  - `contributed_margin_ltv = contributed_margin_monthly * capped_tenure_months`
  - `ltv_net_value = contributed_margin_ltv - acquisition_cost`
- Lifetime horizon cap: 36 months.

5. Churn prediction model
- RandomForest classifier with fixed `random_state=42` for reproducibility.
- Output is probability-based risk score, not causal inference.

## Survival Interpretation Guidance

1. Cohort setup
- Target cohorts are split by observed max discount:
  - `high_discount_gt20`
  - `low_discount_lt5`

2. Kaplan-Meier curve interpretation
- Survival probability at timeline `t` is the estimated probability of remaining active beyond `t` months.
- A steeper curve indicates faster churn dynamics.

3. Decision interpretation
- Lower survival in high-discount cohorts suggests discount-led acquisition may trade off long-term retention quality.
- Use with caution: correlation does not imply causal impact without controlled experimentation.

## Drift Baseline Interpretation

- Drift baseline monitors discount-band population share changes.
- Threshold is currently `<= 0.20` absolute share delta per band.
- Breach indicates population shift risk and triggers deeper model performance review.

## Caveats

- Runtime model outputs depend on Silver data quality and Databricks execution environment.
- Cohort and drift thresholds are policy choices and should be reviewed quarterly with business stakeholders.
