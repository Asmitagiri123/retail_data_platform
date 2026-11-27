select
    customer_id,
    initcap(trim(customer_name))                     as customer_name,
    lower(trim(email))                               as email,
    replace(trim(phone), '+977-', '')                as phone,
    city,
    upper(loyalty_tier)                              as loyalty_tier,
    try_to_date(signup_date)                         as signup_date,
    try_to_date(updated_at)                          as updated_at
from {{ source('bronze', 'raw_customers') }}