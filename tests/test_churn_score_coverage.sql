-- Test that churn_scores covers at least 90% of fct_gold_customer_features
-- This ensures that we are not silently imputing missing churn probabilities at scale

select count(*) as gap_count
from {{ ref('fct_gold_customer_features') }} f
left join {{ ref('fct_churn_scores') }} c on f.customer_id = c.customer_id
where c.customer_id is null
