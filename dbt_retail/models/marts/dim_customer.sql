select
    {{ surrogate_key(['customer_id', 'dbt_valid_from']) }} as customer_key,
    customer_id,
    customer_name,
    city,
    loyalty_tier,
    signup_date,
    dbt_valid_from                                         as valid_from,
    dbt_valid_to                                           as valid_to,
    dbt_valid_to is null                                   as is_current
from {{ ref('snap_customers') }}

union all


select
    {{ surrogate_key(["'UNKNOWN'"]) }}  as customer_key,
    'UNKNOWN'                           as customer_id,
    'Anonymous customer'                as customer_name,
    null                                as city,
    'NONE'                              as loyalty_tier,
    null                                as signup_date,
    null                                as valid_from,
    null                                as valid_to,
    true                                as is_current