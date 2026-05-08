-- Daily sentiment per company with a 7-day rolling average — the line-chart
-- mart for the dashboard.

with daily as (
    select
        f.company_id,
        c.name                            as company_name,
        d.date,
        count(*)                          as posts,
        avg(f.score)                      as avg_sentiment
    from {{ ref('fact_posts') }} f
    join {{ ref('dim_company') }} c using (company_id)
    join {{ ref('dim_date') }}    d using (date_id)
    group by 1, 2, 3
)

select
    company_id,
    company_name,
    date,
    posts,
    avg_sentiment,
    avg(avg_sentiment) over (
        partition by company_id
        order by date
        rows between 6 preceding and current row
    ) as rolling_7d_sentiment,
    sum(posts) over (
        partition by company_id
        order by date
        rows between 6 preceding and current row
    ) as rolling_7d_posts
from daily
