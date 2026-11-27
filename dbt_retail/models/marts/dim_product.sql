select
    {{ surrogate_key(['p.product_id', 'p.dbt_valid_from']) }} as product_key,
    p.product_id,
    p.product_name,
    p.brand,
    p.category,
    p.sub_category,
    s.supplier_name,
    p.list_price,
    p.cost,
    p.status,
    p.dbt_valid_from                                         as valid_from,
    p.dbt_valid_to                                           as valid_to,
    p.dbt_valid_to is null                                   as is_current
from {{ ref('snap_products') }} p
left join {{ ref('stg_suppliers') }} s
    on p.supplier_id = s.supplier_id