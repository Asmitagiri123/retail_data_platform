with source as (

    select * from {{ source('bronze', 'raw_returns') }}

),

typed as (

    select
        return_id,
        txn_id,
        try_to_number(line_no)                as line_no,
        try_to_number(quantity)               as quantity,
        try_to_decimal(refund_amount, 12, 2)  as refund_amount,
        upper(trim(reason_code))              as reason_code,
        try_to_timestamp(return_ts)           as return_ts,
        _ingest_ts                            as ingested_at
    from source

),

ranked as (

    select
        *,
        row_number() over (partition by return_id order by ingested_at desc) as rn
    from typed

)

select * exclude (rn)
from ranked
where rn = 1
  and quantity > 0