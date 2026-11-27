with sales as (

    select
        date_trunc('month', d.date_day)  as month_start,
        p.category,
        sum(f.quantity)                  as units_sold,
        sum(f.net_amount)                as revenue
    from {{ ref('fct_sales') }} f
    join {{ ref('dim_date') }} d     on f.date_key = d.date_key
    join {{ ref('dim_product') }} p  on f.product_key = p.product_key
    group by 1, 2

),

returned as (

    select
        date_trunc('month', d.date_day)  as month_start,
        p.category,
        sum(r.quantity_returned)         as units_returned,
        sum(r.refund_amount)             as refund_amount
    from {{ ref('fct_returns') }} r
    join {{ ref('dim_date') }} d     on r.date_key = d.date_key
    join {{ ref('dim_product') }} p  on r.product_key = p.product_key
    where not r.is_orphan
    group by 1, 2

)

select
    s.month_start,
    s.category,
    s.units_sold,
    s.revenue,
    coalesce(r.units_returned, 0)                                            as units_returned,
    coalesce(r.refund_amount, 0)                                             as refund_amount,
    round(coalesce(r.units_returned, 0) / nullif(s.units_sold, 0), 4)        as return_rate
from sales s
left join returned r
    on s.month_start = r.month_start
   and s.category = r.category