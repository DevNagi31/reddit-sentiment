select
    comment_id,
    sentiment,
    score,
    model_version,
    scored_at
from {{ source('raw', 'comment_sentiment') }}
