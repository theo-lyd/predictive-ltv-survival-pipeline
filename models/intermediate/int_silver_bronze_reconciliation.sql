with raw_customers as (
    select
        count(*) as raw_count,
        sum(cast(monthly_recurring_revenue as decimal(18,2))) as raw_mrr
    from {{ source('raw', 'churn') }}
),

silver_customers as (
    select
        count(*) as silver_count,
        sum(monthly_recurring_revenue) as silver_mrr
    from {{ ref('stg_customers') }}
)

select
    'customers' as entity_name,
    rc.raw_count,
    sc.silver_count,
    case when rc.raw_count = 0 then 0 else abs(sc.silver_count - rc.raw_count) / rc.raw_count end as count_delta_ratio,
    rc.raw_mrr,
    sc.silver_mrr,
    case
        when rc.raw_mrr is null or rc.raw_mrr = 0 then 0
        else abs(sc.silver_mrr - rc.raw_mrr) / rc.raw_mrr
    end as mrr_delta_ratio
from raw_customers rc
cross join silver_customers sc
