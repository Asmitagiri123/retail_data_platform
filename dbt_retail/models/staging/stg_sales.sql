select
    txn_id || '-' || line_no                 as sales_line_key,
    txn_id,
    line_no,
    store_id,
    product_id,
    customer_id,
    quantity,
    unit_price,
    discount,
    quantity * unit_price                    as gross_amount,
    quantity * unit_price - discount         as net_amount,
    payment_method,
    channel,
    event_ts,
    event_ts::date                           as sale_date,
    ingested_at
from {{ ref('stg_sales_checked') }}
where reject_reason is null