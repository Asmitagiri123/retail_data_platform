select
    date_trunc('month', d.date_day)                                  as month_start,
    p.product_id,
    p.product_name,
    p.brand,
    p.category,
    sum(f.quantity)                                                  as units,
    sum(f.net_amount)                                                as revenue,
    sum(f.margin_amount)                                             as margin,
    rank() over (
        partition by date_trunc('month', d.date_day)
        order by sum(f.net_amount) desc
    )                                                                as revenue_rank
from {{ ref('fct_sales') }} f
join {{ ref('dim_date') }} d     on f.date_key = d.date_key
join {{ ref('dim_product') }} p  on f.product_key = p.product_key
group by 1, 2, 3, 4, 5