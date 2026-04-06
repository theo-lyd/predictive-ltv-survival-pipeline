with source as (
    select
        customer_id,
        subscription_id,
        signup_date,
        churn_date,
        region,
        product_tier,
        monthly_recurring_revenue
    from {{ source('raw', 'churn') }}
)

select
    customer_id,
    subscription_id,
    cast(signup_date as timestamp) as signup_ts,
    cast(churn_date as timestamp) as churn_ts,
    region,
    product_tier,
    cast(monthly_recurring_revenue as decimal(18,2)) as monthly_recurring_revenue,
    case
        when churn_date is null then false
        else true
    end as is_churned
from source
