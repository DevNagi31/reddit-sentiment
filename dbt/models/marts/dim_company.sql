select
    company_id,
    name,
    ticker,
    sector
from {{ ref('stg_companies') }}
