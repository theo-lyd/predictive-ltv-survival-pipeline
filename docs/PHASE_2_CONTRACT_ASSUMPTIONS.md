# Phase 2 Contract Assumptions and Null-Handling Strategy

## Contract assumptions

1. Time semantics
- All Silver timestamps are normalized to UTC.
- Promotion start date parsing precedence is fixed:
  1. `%Y-%m-%d`
  2. `%d/%m/%Y`
  3. `%Y/%m/%d`

2. Promotion identity
- Deterministic identity is derived from `(customer_id, discount_type, normalized_promotion_start_ts)`.
- Duplicate records resolve by latest `ingested_at_utc`, then `promotion_id` tie-break.

3. Billing amount parsing
- Billing amount strips non-numeric symbols before decimal cast.
- Currency values are normalized to uppercase.

4. Reconciliation tolerance
- Silver-vs-Bronze aggregate deltas are tolerated up to 2%.
- Breach is treated as integrity failure.

## Null-handling strategy

1. `discount_percent`
- Nullable by design because Bronze carries intentionally imperfect source quality.
- Null is preserved in staging to avoid false imputation in trusted core.

2. `churn_ts`
- Null indicates active customer; never imputed in Silver.

3. `promotion_start_ts`
- If unparseable after all accepted formats, value remains null.
- Downstream temporal checks apply only where churn date exists.

4. Invoice math consistency
- If explicit subtotal/discount/total fields exist, strict equality check is applied.
- If not, fallback assumption is `invoice_total = invoice_amount` for consistency validation.

## Why this strategy

- Preserves source fidelity while still enforcing high-integrity business constraints.
- Makes assumptions explicit, testable, and auditable for future model evolution.
