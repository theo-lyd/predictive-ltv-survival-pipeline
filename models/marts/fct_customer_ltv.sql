with features as (
    select
        customer_id,
        product_tier,
        signup_ts,
        churn_ts,
        is_churned,
        customer_tenure_months,
        monthly_recurring_revenue,
        discount_intensity_index,
        contributed_margin_monthly,
        acquisition_cost,
        state_transition
    from {{ ref('fct_gold_customer_features') }}
),

assembled as (
    select
        f.customer_id,
        f.product_tier,
        f.signup_ts,
        f.churn_ts,
        f.is_churned,
        f.state_transition,
        f.monthly_recurring_revenue,
        f.discount_intensity_index,
        f.contributed_margin_monthly,
        f.acquisition_cost,
        case
            when f.state_transition in ('active_to_churn', 'discounted_to_churn') then 0.95
            when f.state_transition = 'active_with_discount' then 0.35
            else 0.15
        end as churn_probability,
        least(greatest(coalesce(f.customer_tenure_months, 1), 1), 36) as capped_tenure_months
    from features f
)

select
    customer_id,
    product_tier,
    signup_ts,
    churn_ts,
    is_churned,
    state_transition,
    monthly_recurring_revenue,
    discount_intensity_index,
    contributed_margin_monthly,
    acquisition_cost,
    churn_probability,
    capped_tenure_months,
    monthly_recurring_revenue * capped_tenure_months as gross_revenue_ltv,
    monthly_recurring_revenue * capped_tenure_months * (1 - discount_intensity_index) as discounted_revenue_ltv,
    contributed_margin_monthly * capped_tenure_months as contributed_margin_ltv,
    (contributed_margin_monthly * capped_tenure_months) - acquisition_cost as ltv_net_value,
    current_timestamp() as model_built_at
from assembled
