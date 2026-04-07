with features as (
    select
        customer_id,
        case
            when max_discount_percent > 20 then 'high_discount_gt20'
            when max_discount_percent < 5 then 'low_discount_lt5'
            else 'other'
        end as discount_band
    from {{ ref('fct_gold_customer_features') }}
),

current_distribution as (
    select
        discount_band,
        count(*) / sum(count(*)) over () as current_share
    from features
    group by discount_band
),

baseline_distribution as (
    select 'high_discount_gt20' as discount_band, 0.30 as baseline_share
    union all
    select 'low_discount_lt5' as discount_band, 0.30 as baseline_share
    union all
    select 'other' as discount_band, 0.40 as baseline_share
)

select
    b.discount_band,
    b.baseline_share,
    coalesce(c.current_share, 0) as current_share,
    abs(coalesce(c.current_share, 0) - b.baseline_share) as drift_abs,
    case
        when abs(coalesce(c.current_share, 0) - b.baseline_share) <= 0.20 then 'within_baseline'
        else 'out_of_baseline'
    end as drift_status,
    current_timestamp() as model_built_at
from baseline_distribution b
left join current_distribution c on b.discount_band = c.discount_band
