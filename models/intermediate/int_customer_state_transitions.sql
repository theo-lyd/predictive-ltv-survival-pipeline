with customers as (
    select
        customer_id,
        signup_ts,
        churn_ts,
        is_churned,
        monthly_recurring_revenue
    from {{ ref('stg_customers') }}
),

latest_promotions as (
    select
        customer_id,
        max(promotion_start_ts) as latest_promotion_ts,
        max(discount_percent) as latest_discount_percent
    from {{ ref('int_promotions_resolved') }}
    group by customer_id
),

billing as (
    select
        customer_id,
        count(*) as invoice_count,
        sum(invoice_amount) as invoice_amount_total
    from {{ ref('stg_billing') }}
    group by customer_id
)

select
    c.customer_id,
    c.signup_ts,
    c.churn_ts,
    c.monthly_recurring_revenue,
    lp.latest_promotion_ts,
    lp.latest_discount_percent,
    b.invoice_count,
    b.invoice_amount_total,
    case
        when c.is_churned and lp.latest_promotion_ts is not null and lp.latest_promotion_ts <= c.churn_ts
            then 'discounted_to_churn'
        when c.is_churned then 'active_to_churn'
        when not c.is_churned and lp.latest_promotion_ts is not null then 'active_with_discount'
        else 'active_without_discount'
    end as state_transition
from customers c
left join latest_promotions lp on c.customer_id = lp.customer_id
left join billing b on c.customer_id = b.customer_id
