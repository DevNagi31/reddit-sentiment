select
    company_id,
    name,
    ticker,
    sector,
    -- aliases stored as comma-separated string in seed; split into a list
    string_split(lower(aliases), ',') as alias_list
from {{ source('seed', 'companies') }}
