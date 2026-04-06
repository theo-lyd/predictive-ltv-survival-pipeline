with customers as (
    select * from {{ ref('stg_customers') }}
),
promotions as (
    select * from {{ ref('stg_promotions') }}
),
customer_rollup as (
    select
        c.customer_id,
        c.subscription_id,
        c.region,
        c.product_tier,
        c.signup_ts,
        c.churn_ts,
        c.monthly_recurring_revenue,
        coalesce(max(p.discount_percent), 0) as discount_percent,
        case
            when c.churn_ts is null then 0
            else greatest(datediff(c.churn_ts, c.signup_ts), 0)
        end as tenure_days
    from customers c
    left join promotions p
        on c.customer_id = p.customer_id
    group by 1,2,3,4,5,6,7
)

select
    customer_id,
    subscription_id,
    region,
    product_tier,
    signup_ts,
    churn_ts,
    tenure_days,
    monthly_recurring_revenue,
    discount_percent,
    monthly_recurring_revenue * greatest(tenure_days / 30.0, 1) as gross_revenue_proxy,
    monthly_recurring_revenue * greatest(tenure_days / 30.0, 1) * (1 - discount_percent / 100.0) as net_revenue_proxy,
    current_timestamp() as model_built_at
from customer_rollup
