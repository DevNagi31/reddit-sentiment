select
    post_id,
    sentiment,
    score,
    theme,
    model_version,
    scored_at
from {{ source('raw', 'post_sentiment') }}
