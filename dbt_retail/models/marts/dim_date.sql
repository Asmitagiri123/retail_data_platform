select
    to_number(to_char(calendar_date, 'YYYYMMDD'))   as date_key,
    calendar_date                                    as date_day,
    year(calendar_date)                              as year_number,
    quarter(calendar_date)                           as quarter_number,
    month(calendar_date)                             as month_number,
    monthname(calendar_date)                         as month_name,
    weekofyear(calendar_date)                        as week_of_year,
    dayname(calendar_date)                           as day_name,
    dayofweekiso(calendar_date) = 6                  as is_weekend,
    is_holiday,
    nullif(festival_name, '')                        as festival_name,
    nullif(festival_name, '') is not null            as is_festival,
    sales_multiplier
from {{ ref('festival_calendar') }}