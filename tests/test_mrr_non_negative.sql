select *
from {{ ref('stg_customers') }}
where monthly_recurring_revenue < 0
