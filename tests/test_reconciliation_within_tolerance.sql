select *
from {{ ref('int_silver_bronze_reconciliation') }}
where count_delta_ratio > 0.02
   or mrr_delta_ratio > 0.02
