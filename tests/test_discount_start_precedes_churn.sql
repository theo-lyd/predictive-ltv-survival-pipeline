select
    p.customer_id,
    p.promotion_start_ts,
    c.churn_ts
from {{ ref('int_promotions_resolved') }} p
join {{ ref('stg_customers') }} c on p.customer_id = c.customer_id
where c.churn_ts is not null
  and p.promotion_start_ts > c.churn_ts
