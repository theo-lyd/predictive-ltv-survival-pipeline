with scores as (
    select
        customer_id,
        churn_probability,
        risk_bucket,
        is_active_customer
    from {{ ref('fct_churn_scores') }}
),

features as (
    select
        customer_id,
        state_transition
    from {{ ref('fct_gold_customer_features') }}
),

scored as (
    select
        s.customer_id,
        s.churn_probability,
        s.risk_bucket,
        s.is_active_customer,
        case
            when f.state_transition in ('active_to_churn', 'discounted_to_churn') then 1
            else 0
        end as observed_churn
    from scores s
    left join features f on s.customer_id = f.customer_id
)

select
    count(*) as scored_population,
    avg(churn_probability) as mean_churn_probability,
    avg(case when risk_bucket = 'high' then 1 else 0 end) as high_risk_share,
    avg(case when observed_churn = 1 then churn_probability else 1 - churn_probability end) as directional_accuracy_proxy,
    current_timestamp() as model_built_at
from scored
