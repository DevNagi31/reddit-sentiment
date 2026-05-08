-- Weekly company summary with WoW deltas — the input the storytelling layer
-- (nlp/summarize.py) reads to produce the narrative paragraph.

with weekly as (
    select
        f.company_id,
        c.name                                   as company_name,
        date_trunc('week', d.date)               as week_start,
        count(*)                                 as posts,
        avg(f.score)                             as avg_sentiment,
        sum(case when f.sentiment = 'negative' then 1 else 0 end) as negative_posts
    from {{ ref('fact_posts') }} f
    join {{ ref('dim_company') }} c using (company_id)
    join {{ ref('dim_date') }}    d using (date_id)
    group by 1, 2, 3
)

select
    company_id,
    company_name,
    week_start,
    posts,
    avg_sentiment,
    negative_posts,
    lag(avg_sentiment) over (partition by company_id order by week_start)
        as prev_avg_sentiment,
    avg_sentiment
        - lag(avg_sentiment) over (partition by company_id order by week_start)
        as wow_sentiment_change,
    case
        when lag(avg_sentiment) over (partition by company_id order by week_start) = 0 then null
        else 100.0 * (avg_sentiment
             - lag(avg_sentiment) over (partition by company_id order by week_start))
            / abs(lag(avg_sentiment) over (partition by company_id order by week_start))
    end as wow_sentiment_pct_change
from weekly
