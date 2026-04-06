with promotions as (
    select
        customer_id,
        discount_type,
        discount_percent,
        promotion_start_ts,
        promotion_surrogate_key
    from {{ ref('int_promotions_resolved') }}
),

customers as (
    select
        customer_id,
        signup_ts
    from {{ ref('stg_customers') }}
),

joined as (
    select
        p.customer_id,
        p.promotion_surrogate_key,
        p.discount_type,
        p.discount_percent,
        p.promotion_start_ts,
        c.signup_ts,
        months_between(p.promotion_start_ts, c.signup_ts) as customer_tenure_months
    from promotions p
    left join customers c on p.customer_id = c.customer_id
)

select
    customer_id,
    promotion_surrogate_key,
    discount_type,
    discount_percent,
    promotion_start_ts,
    customer_tenure_months,
    case
        when discount_percent >= 35 then 'deep_discount'
        when discount_percent >= 15 then 'seasonal_discount'
        when discount_percent is not null then 'loyalty_discount'
        else 'unknown_discount'
    end as discount_cohort,
    case
        when customer_tenure_months < 6 then 'early_lifecycle'
        when customer_tenure_months < 18 then 'mid_lifecycle'
        else 'late_lifecycle'
    end as tenure_cohort
from joined
