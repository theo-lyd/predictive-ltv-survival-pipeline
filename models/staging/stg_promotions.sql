with source as (
    select
        promotion_id,
        customer_id,
        discount_type,
        discount_percent,
        promotion_start_date,
        promotion_channel,
        ingested_at_utc
    from {{ source('raw', 'promotions') }}
)

select
    trim(promotion_id) as promotion_id,
    trim(customer_id) as customer_id,
    trim(discount_type) as discount_type,
    cast(discount_percent as decimal(5,2)) as discount_percent,
    to_utc_timestamp(
        coalesce(
            to_timestamp(promotion_start_date, 'yyyy-MM-dd'),
            to_timestamp(promotion_start_date, 'dd/MM/yyyy'),
            to_timestamp(promotion_start_date, 'yyyy/MM/dd')
        ),
        'UTC'
    ) as promotion_start_ts,
    lower(trim(promotion_channel)) as promotion_channel,
    to_utc_timestamp(cast(ingested_at_utc as timestamp), 'UTC') as ingested_at_utc,
    md5(
        concat_ws(
            '||',
            trim(customer_id),
            trim(discount_type),
            cast(
                coalesce(
                    to_timestamp(promotion_start_date, 'yyyy-MM-dd'),
                    to_timestamp(promotion_start_date, 'dd/MM/yyyy'),
                    to_timestamp(promotion_start_date, 'yyyy/MM/dd')
                ) as string
            )
        )
    ) as promotion_identity_key,
    case when discount_percent > 15 then true else false end as is_heavy_promotion
from source
