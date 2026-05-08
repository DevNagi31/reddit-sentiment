with sub as (
    select * from {{ ref('stg_subreddits') }}
),

post_counts as (
    select subreddit, count(*) as post_count
    from {{ ref('stg_posts') }}
    group by 1
)

select
    row_number() over (order by sub.name) as subreddit_id,
    sub.name,
    sub.category,
    coalesce(pc.post_count, 0)            as post_count
from sub
left join post_counts pc on pc.subreddit = sub.name
