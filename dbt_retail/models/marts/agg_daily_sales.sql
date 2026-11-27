select
    d.date_day,
    d.festival_name,
    d.is_festival,
    st.store_name,
    st.city,
    p.category,
    count(distinct f.txn_id)                                         as orders,
    sum(f.quantity)                                                  as units,
    sum(f.net_amount)                                                as revenue,
    sum(f.margin_amount)                                             as margin,
    round(sum(f.margin_amount) / nullif(sum(f.net_amount), 0), 4)    as margin_pct
from {{ ref('fct_sales') }} f
join {{ ref('dim_date') }} d     on f.date_key = d.date_key
join {{ ref('dim_store') }} st   on f.store_key = st.store_key
join {{ ref('dim_product') }} p  on f.product_key = p.product_key
group by 1, 2, 3, 4, 5, 6