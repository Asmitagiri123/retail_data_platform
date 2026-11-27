with source as (

    select * from {{ source('bronze', 'raw_sales') }}

),

typed as (

    select
        txn_id,
        try_to_number(line_no)                       as line_no,
        nullif(trim(store_id), '')                   as store_id,
        product_id,
        nullif(trim(customer_id), '')                as customer_id,
        try_to_number(quantity)                      as quantity,
        try_to_decimal(unit_price, 12, 2)            as unit_price,
        coalesce(try_to_decimal(discount, 12, 2), 0) as discount,
        upper(trim(payment_method))                  as payment_method,
        upper(trim(channel))                         as channel,
        try_to_timestamp(event_ts)                   as event_ts,
        _source_file,
        _ingest_ts                                   as ingested_at
    from source

),

ranked as (

    select
        *,
        row_number() over (
            partition by txn_id, line_no
            order by ingested_at desc, event_ts desc
        ) as rn
    from typed

),

deduped as (

    select * from ranked where rn = 1

)

select
    * exclude (rn),
    case
        when txn_id is null or line_no is null          then 'MISSING_KEY'
        when store_id is null                           then 'MISSING_STORE'
        when quantity is null or quantity <= 0          then 'INVALID_QUANTITY'
        when unit_price is null or unit_price < 0       then 'INVALID_PRICE'
        when event_ts is null                           then 'INVALID_TIMESTAMP'
    end as reject_reason
from deduped