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
    trim(customer_id) as customer_id,
    trim(subscription_id) as subscription_id,
    to_utc_timestamp(cast(signup_date as timestamp), 'UTC') as signup_ts,
    to_utc_timestamp(cast(churn_date as timestamp), 'UTC') as churn_ts,
    upper(trim(region)) as region,
    lower(trim(product_tier)) as product_tier,
    cast(monthly_recurring_revenue as decimal(18,2)) as monthly_recurring_revenue,
    case
        when churn_date is null then false
        else true
    end as is_churned
from source
