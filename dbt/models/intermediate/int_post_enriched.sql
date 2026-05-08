-- One row per post, joined with sentiment + resolved company.
-- This is the join layer the marts build on.

select
    p.post_id,
    p.subreddit,
    p.post_date,
    p.created_utc,
    p.upvotes,
    p.num_comments,
    pc.company_id,
    pc.company_name,
    pc.ticker,
    pc.sector,
    s.sentiment,
    s.score        as sentiment_score,
    s.theme,
    p.title,
    p.permalink
from {{ ref('stg_posts') }} p
left join {{ ref('int_post_company') }} pc using (post_id)
left join {{ ref('stg_sentiment') }}    s  using (post_id)
where pc.company_id is not null   -- drop posts that don't mention any tracked company
