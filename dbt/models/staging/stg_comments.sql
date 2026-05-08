with src as (
    select * from {{ source('raw', 'comments') }}
)

select
    comment_id,
    post_id,
    subreddit,
    body,
    author,
    upvotes,
    created_utc,
    cast(created_utc as date) as comment_date
from src
where body is not null
  and body not in ('[deleted]', '[removed]')
