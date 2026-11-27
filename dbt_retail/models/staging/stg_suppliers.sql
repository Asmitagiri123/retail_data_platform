select
    supplier_id,
    supplier_name,
    city
from {{ source('bronze', 'raw_suppliers') }}