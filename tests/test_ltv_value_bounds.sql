-- Test that ltv_net_value does not fall outside reasonable bounds
-- ltv_net_value should be: (contributed_margin_monthly * tenure_months) - acquisition_cost
-- It can be negative (customer has low margin), but should not be extreme outliers

select customer_id, ltv_net_value
from {{ ref('fct_customer_ltv') }}
where ltv_net_value < -100000 or ltv_net_value > 10000000
