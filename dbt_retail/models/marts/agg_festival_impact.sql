with daily as (

    select
        d.date_day,
        coalesce(d.festival_name, 'Normal day')  as period,
        sum(f.net_amount)                        as revenue,
        count(distinct f.txn_id)                 as orders
    from {{ ref('fct_sales') }} f
    join {{ ref('dim_date') }} d on f.date_key = d.date_key
    group by 1, 2

)

select
    period,
    count(*)                                                         as days,
    round(avg(revenue), 2)                                           as avg_daily_revenue,
    round(avg(orders), 0)                                            as avg_daily_orders,
    round(
        avg(revenue) / (select avg(revenue) from daily where period = 'Normal day') - 1,
        4
    )                                                                as uplift_vs_normal
from daily
group by 1