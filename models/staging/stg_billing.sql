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
    customer_id,
    invoice_id,
    cast(invoice_date as timestamp) as invoice_ts,
    cast(invoice_amount as decimal(18,2)) as invoice_amount,
    currency,
    lower(payment_status) as payment_status,
    ingestion_run_id,
    cast(ingested_at_utc as timestamp) as ingested_at_utc
from source
