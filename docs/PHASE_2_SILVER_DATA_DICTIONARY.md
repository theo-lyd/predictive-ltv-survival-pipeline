# Phase 2 Silver Data Dictionary

## stg_customers

- Grain: 1 row per customer-subscription record from Bronze churn source.
- Keys:
  - `customer_id` (business key)
  - `subscription_id`
- Core fields:
  - `signup_ts` (UTC timestamp)
  - `churn_ts` (UTC timestamp, nullable)
  - `monthly_recurring_revenue` (decimal)
  - `is_churned` (boolean)
- Notes:
  - Region and product tier are normalized (`upper`/`lower`).

## stg_promotions

- Grain: 1 row per raw promotion event.
- Keys:
  - `promotion_id` (source identifier)
  - `promotion_identity_key` (deterministic stitched identity hash)
- Core fields:
  - `promotion_start_ts` (UTC normalized from mixed source formats)
  - `discount_percent` (nullable)
  - `is_heavy_promotion` (boolean)
  - `ingested_at_utc`

## stg_billing

- Grain: 1 row per billing invoice event.
- Keys:
  - `invoice_id`
  - `customer_id`
- Core fields:
  - `invoice_ts` (UTC)
  - `invoice_amount` (decimal parsed from string/symbol inputs)
  - `currency` (uppercased ISO-like code)
  - `payment_status` (lowercased)

## int_promotions_resolved

- Grain: 1 row per resolved promotion identity per customer.
- Key strategy:
  - Deduplicate by `(customer_id, promotion_identity_key)` using latest `ingested_at_utc`.
  - Stable surrogate key: `promotion_surrogate_key`.

## int_discount_cohorts

- Grain: 1 row per resolved promotion.
- Derived fields:
  - `discount_cohort`: deep/seasonal/loyalty/unknown
  - `tenure_cohort`: early/mid/late lifecycle
  - `customer_tenure_months`

## int_customer_state_transitions

- Grain: 1 row per customer.
- Derived state:
  - `discounted_to_churn`
  - `active_to_churn`
  - `active_with_discount`
  - `active_without_discount`

## int_silver_bronze_reconciliation

- Grain: 1 row per reconciled entity aggregate.
- Metrics:
  - `count_delta_ratio`
  - `mrr_delta_ratio`
- Tolerance guard:
  - Current threshold: 2% (enforced via singular dbt test)
