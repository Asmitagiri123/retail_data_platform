select
    product_id,
    trim(product_name)                 as product_name,
    brand,
    category,
    sub_category,
    supplier_id,
    try_to_number(list_price)          as list_price,
    try_to_decimal(cost, 12, 2)        as cost,
    upper(status)                      as status,
    try_to_date(updated_at)            as updated_at
from {{ source('bronze', 'raw_products') }}