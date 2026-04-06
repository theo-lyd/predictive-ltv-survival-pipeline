with source as (
    select
        promotion_id,
        customer_id,
        discount_type,
        discount_percent,
        promotion_start_ts,
        promotion_channel,
        ingested_at_utc,
        promotion_identity_key
    from {{ ref('stg_promotions') }}
),

ranked as (
    select
        *,
        row_number() over (
            partition by customer_id, promotion_identity_key
            order by ingested_at_utc desc, promotion_id desc
        ) as row_rank
    from source
),

resolved as (
    select
        promotion_id,
        customer_id,
        discount_type,
        discount_percent,
        promotion_start_ts,
        promotion_channel,
        ingested_at_utc,
        promotion_identity_key,
        md5(concat_ws('||', customer_id, promotion_identity_key)) as promotion_surrogate_key
    from ranked
    where row_rank = 1
)

select *
from resolved
