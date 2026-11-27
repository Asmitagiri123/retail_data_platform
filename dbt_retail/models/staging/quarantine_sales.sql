{{ config(materialized='table') }}

select
    txn_id,
    line_no,
    store_id,
    product_id,
    customer_id,
    quantity,
    unit_price,
    event_ts,
    reject_reason,
    _source_file,
    ingested_at
from {{ ref('stg_sales_checked') }}
where reject_reason is not null