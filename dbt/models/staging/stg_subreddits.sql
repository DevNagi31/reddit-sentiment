select
    name,
    category
from {{ source('seed', 'subreddits') }}
