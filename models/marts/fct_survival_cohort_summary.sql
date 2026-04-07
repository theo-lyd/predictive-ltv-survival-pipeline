with curves as (
    select
        cohort_label,
        timeline_month,
        survival_probability,
        sample_size,
        event_count
    from {{ ref('fct_survival_curves') }}
),

milestones as (
    select
        cohort_label,
        sample_size,
        event_count,
        max(
            last_value(case when timeline_month <= 3 then survival_probability end ignore nulls)
            over (partition by cohort_label order by timeline_month rows between unbounded preceding and unbounded following)
        ) as survival_3m,
        max(
            last_value(case when timeline_month <= 6 then survival_probability end ignore nulls)
            over (partition by cohort_label order by timeline_month rows between unbounded preceding and unbounded following)
        ) as survival_6m,
        max(
            last_value(case when timeline_month <= 12 then survival_probability end ignore nulls)
            over (partition by cohort_label order by timeline_month rows between unbounded preceding and unbounded following)
        ) as survival_12m
    from curves
    group by cohort_label, sample_size, event_count
)

select
    cohort_label,
    sample_size,
    event_count,
    coalesce(survival_3m, 0) as survival_3m,
    coalesce(survival_6m, 0) as survival_6m,
    coalesce(survival_12m, 0) as survival_12m,
    current_timestamp() as model_built_at
from milestones
