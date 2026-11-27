select
    store_id,
    store_name,
    city,
    region,
    upper(format)               as format,
    try_to_date(open_date)      as open_date
from {{ source('bronze', 'raw_stores') }}