select
    date_trunc('month', d.date_day)                                  as month_start,
    c.loyalty_tier,
    count(distinct c.customer_id)                                    as customers,
    count(distinct f.txn_id)                                         as orders,
    sum(f.net_amount)                                                as revenue,
    round(
        sum(f.net_amount) / sum(sum(f.net_amount)) over (partition by date_trunc('month', d.date_day)),
        4
    )                                                                as revenue_share
from {{ ref('fct_sales') }} f
join {{ ref('dim_date') }} d       on f.date_key = d.date_key
join {{ ref('dim_customer') }} c   on f.customer_key = c.customer_key
group by 1, 2