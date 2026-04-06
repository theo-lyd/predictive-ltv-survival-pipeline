with source as (
    select
        customer_id,
        invoice_id,
        invoice_date,
        invoice_amount,
        currency,
        payment_status,
        ingestion_run_id,
        ingested_at_utc
    from {{ source('raw', 'billing') }}
)

select
    trim(customer_id) as customer_id,
    trim(invoice_id) as invoice_id,
    to_utc_timestamp(cast(invoice_date as timestamp), 'UTC') as invoice_ts,
    cast(regexp_replace(cast(invoice_amount as string), '[^0-9.-]', '') as decimal(18,2)) as invoice_amount,
    upper(trim(currency)) as currency,
    lower(payment_status) as payment_status,
    ingestion_run_id,
    to_utc_timestamp(cast(ingested_at_utc as timestamp), 'UTC') as ingested_at_utc
from source
