{{ config(
    materialized='incremental',
    unique_key='return_id',
    incremental_strategy='merge'
) }}

with returns as (

    select * from {{ ref('stg_returns') }}

    {% if is_incremental() %}
    where ingested_at >= (select dateadd('day', -2, max(ingested_at)) from {{ this }})
    {% endif %}

)

select
    r.return_id,
    r.txn_id,
    r.line_no,
    s.sales_line_key,
    to_number(to_char(r.return_ts::date, 'YYYYMMDD'))   as date_key,
    s.store_key,
    s.product_key,
    r.quantity                                           as quantity_returned,
    r.refund_amount,
    r.reason_code,
    r.return_ts,
    datediff('day', s.event_ts, r.return_ts)             as days_to_return,
    s.sales_line_key is null                             as is_orphan,
    r.ingested_at
from returns r
left join {{ ref('fct_sales') }} s
    on r.txn_id = s.txn_id
   and r.line_no = s.line_no