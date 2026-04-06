with source as (
    select
        promotion_id,
        customer_id,
        discount_type,
        discount_percent,
        promotion_start_date,
        promotion_channel
    from {{ source('raw', 'promotions') }}
)

select
    promotion_id,
    customer_id,
    discount_type,
    cast(discount_percent as decimal(5,2)) as discount_percent,
    cast(promotion_start_date as timestamp) as promotion_start_ts,
    promotion_channel,
    case when discount_percent > 15 then true else false end as is_heavy_promotion
from source
