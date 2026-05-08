-- Company-level rollup: total volume, avg sentiment, share of negative posts.

select
    c.company_id,
    c.name                                                as company_name,
    c.ticker,
    c.sector,
    count(*)                                              as total_posts,
    avg(f.score)                                          as avg_sentiment,
    sum(case when f.sentiment = 'positive' then 1 else 0 end) as positive_posts,
    sum(case when f.sentiment = 'neutral'  then 1 else 0 end) as neutral_posts,
    sum(case when f.sentiment = 'negative' then 1 else 0 end) as negative_posts,
    1.0 * sum(case when f.sentiment = 'negative' then 1 else 0 end)
        / nullif(count(*), 0)                             as negative_share,
    sum(f.upvotes)                                        as total_upvotes
from {{ ref('fact_posts') }} f
join {{ ref('dim_company') }} c using (company_id)
group by 1, 2, 3, 4
