with src as (
    select * from {{ source('raw', 'posts') }}
)

select
    post_id,
    subreddit,
    title,
    body,
    coalesce(title, '') || ' ' || coalesce(body, '')        as full_text,
    author,
    upvotes,
    num_comments,
    created_utc,
    cast(created_utc as date)                                as post_date,
    permalink
from src
