-- Comment-level sentiment rolled up per company. Comments are routed to a
-- company via the post they belong to (the post's company resolution).

with comments_enriched as (
    select
        c.comment_id,
        c.post_id,
        c.subreddit,
        c.body,
        c.upvotes,
        cs.sentiment,
        cs.score,
        pc.company_id,
        pc.company_name
    from {{ ref('stg_comments') }}              c
    join {{ ref('stg_comment_sentiment') }}     cs using (comment_id)
    join {{ ref('int_post_company') }}          pc using (post_id)
)

select
    company_id,
    company_name,
    count(*)                                                  as comments,
    avg(score)                                                as avg_sentiment,
    sum(case when sentiment = 'negative' then 1 else 0 end)   as negative_comments,
    sum(case when sentiment = 'positive' then 1 else 0 end)   as positive_comments,
    sum(upvotes)                                              as total_comment_upvotes
from comments_enriched
group by 1, 2
