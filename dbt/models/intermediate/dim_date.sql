-- Date spine covering the range of posts we have.

with bounds as (
    select
        min(post_date) as min_d,
        max(post_date) as max_d
    from {{ ref('stg_posts') }}
),

spine as (
    select cast(d as date) as date
    from bounds,
         unnest(generate_series(min_d, max_d, interval '1 day')) as t(d)
)

select
    cast(strftime(date, '%Y%m%d') as integer)        as date_id,
    date,
    dayname(date)                                     as day_of_week,
    extract(week from date)                           as week,
    extract(month from date)                          as month,
    extract(quarter from date)                        as quarter,
    extract(year from date)                           as year,
    date_trunc('week', date)                          as week_start
from spine
