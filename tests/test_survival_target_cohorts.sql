with required as (
    select 'high_discount_gt20' as cohort_label
    union all
    select 'low_discount_lt5' as cohort_label
),

available as (
    select distinct cohort_label
    from {{ ref('fct_survival_curves') }}
)

select r.cohort_label
from required r
left join available a on r.cohort_label = a.cohort_label
where a.cohort_label is null
