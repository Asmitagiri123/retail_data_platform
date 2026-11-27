select
    {{ surrogate_key(['store_id']) }}   as store_key,
    store_id,
    store_name,
    city,
    region,
    format,
    open_date
from {{ ref('stg_stores') }}