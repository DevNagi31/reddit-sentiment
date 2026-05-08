-- Star-schema fact table: one row per post.

with enriched as (
    select * from {{ ref('int_post_enriched') }}
),

dates as (
    select date_id, date from {{ ref('dim_date') }}
),

subs as (
    select subreddit_id, name from {{ ref('dim_subreddit') }}
)

select
    e.post_id,
    s.subreddit_id,
    e.company_id,
    d.date_id,
    e.sentiment,
    e.sentiment_score                                  as score,
    e.theme,
    e.upvotes,
    e.num_comments,
    e.created_utc,
    e.title,
    e.permalink
from enriched e
left join subs  s on s.name = e.subreddit
left join dates d on d.date = e.post_date
