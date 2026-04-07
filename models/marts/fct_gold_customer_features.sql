{% set observation_date = var('observation_date', '2024-12-31') %}

with customers as (
    select
        customer_id,
        product_tier,
        signup_ts,
        churn_ts,
        monthly_recurring_revenue,
        is_churned
    from {{ ref('stg_customers') }}
),

promotions as (
    select
        customer_id,
        max(discount_percent) as max_discount_percent,
        avg(discount_percent) as avg_discount_percent
    from {{ ref('int_promotions_resolved') }}
    group by customer_id
),

billing as (
    select
        customer_id,
        count(*) as invoice_count,
        sum(invoice_amount) as invoice_total_amount,
        avg(invoice_amount) as avg_invoice_amount
    from {{ ref('stg_billing') }}
    group by customer_id
),

transitions as (
    select
        customer_id,
        state_transition
    from {{ ref('int_customer_state_transitions') }}
),

assembled as (
    select
        c.customer_id,
        c.product_tier,
        c.signup_ts,
        c.churn_ts,
        c.monthly_recurring_revenue,
        c.is_churned,
        coalesce(p.max_discount_percent, 0) as max_discount_percent,
        coalesce(p.avg_discount_percent, 0) as avg_discount_percent,
        least(greatest(coalesce(p.avg_discount_percent, 0) / 50.0, 0), 1) as discount_intensity_index,
        greatest(months_between(coalesce(c.churn_ts, to_timestamp('{{ observation_date }}', 'YYYY-MM-DD')), c.signup_ts), 0) as customer_tenure_months,
        coalesce(b.invoice_count, 0) as invoice_count,
        coalesce(b.invoice_total_amount, 0) as invoice_total_amount,
        coalesce(b.avg_invoice_amount, 0) as avg_invoice_amount,
        coalesce(t.state_transition, 'active_without_discount') as state_transition,
        case
            when lower(c.product_tier) = 'enterprise' then 0.72
            when lower(c.product_tier) = 'pro' then 0.68
            else 0.62
        end as gross_margin_rate,
        case
            when lower(c.product_tier) = 'enterprise' then 2500
            when lower(c.product_tier) = 'pro' then 1200
            else 600
        end as acquisition_cost
    from customers c
    left join promotions p on c.customer_id = p.customer_id
    left join billing b on c.customer_id = b.customer_id
    left join transitions t on c.customer_id = t.customer_id
)

select
    customer_id,
    product_tier,
    signup_ts,
    churn_ts,
    is_churned,
    customer_tenure_months,
    monthly_recurring_revenue,
    max_discount_percent,
    avg_discount_percent,
    discount_intensity_index,
    invoice_count,
    invoice_total_amount,
    avg_invoice_amount,
    state_transition,
    gross_margin_rate,
    acquisition_cost,
    monthly_recurring_revenue * gross_margin_rate * (1 - discount_intensity_index) as contributed_margin_monthly,
    current_timestamp() as model_built_at
from assembled
