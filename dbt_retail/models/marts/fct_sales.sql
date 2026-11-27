{{ config(
    materialized='incremental',
    unique_key='sales_line_key',
    incremental_strategy='merge',
    on_schema_change='append_new_columns'
) }}

with sales as (

    select * from {{ ref('stg_sales') }}

    {% if is_incremental() %}
    where ingested_at >= (select dateadd('day', -2, max(ingested_at)) from {{ this }})
    {% endif %}

)

select
    s.sales_line_key,
    s.txn_id,
    s.line_no,
    to_number(to_char(s.sale_date, 'YYYYMMDD'))                    as date_key,
    st.store_key,
    p.product_key,
    coalesce(c.customer_key, {{ surrogate_key(["'UNKNOWN'"]) }})   as customer_key,
    pm.payment_method_key,
    s.channel,
    s.quantity,
    s.unit_price,
    s.discount,
    s.gross_amount,
    s.net_amount,
    {{ vat_from_gross('s.net_amount') }}                           as vat_amount,
    s.quantity * p.cost                                            as cost_amount,
    s.net_amount - {{ vat_from_gross('s.net_amount') }}
        - s.quantity * p.cost                                      as margin_amount,
    s.event_ts,
    s.ingested_at
from sales s
left join {{ ref('dim_store') }} st
    on s.store_id = st.store_id
left join {{ ref('dim_payment_method') }} pm
    on s.payment_method = pm.payment_method
left join {{ ref('dim_product') }} p
    on s.product_id = p.product_id
   and s.event_ts >= p.valid_from
   and (s.event_ts < p.valid_to or p.valid_to is null)
left join {{ ref('dim_customer') }} c
    on s.customer_id = c.customer_id
   and s.event_ts >= c.valid_from
   and (s.event_ts < c.valid_to or c.valid_to is null)