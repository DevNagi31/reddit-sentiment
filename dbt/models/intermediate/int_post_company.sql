-- Resolve each post to a single company by checking whether any of the
-- company's aliases appears in the post text. If multiple companies match,
-- pick the one with the most alias hits (ties broken by company_id).

with posts as (
    select post_id, lower(full_text) as text from {{ ref('stg_posts') }}
),

companies as (
    select company_id, name, ticker, sector, alias_list
    from {{ ref('stg_companies') }}
),

exploded as (
    select
        c.company_id,
        c.name,
        c.ticker,
        c.sector,
        trim(alias) as alias
    from companies c, unnest(c.alias_list) as t(alias)
),

matches as (
    select
        p.post_id,
        e.company_id,
        e.name,
        e.ticker,
        e.sector,
        count(*) as alias_hits
    from posts p
    join exploded e on p.text like '%' || e.alias || '%'
    group by 1, 2, 3, 4, 5
),

ranked as (
    select
        *,
        row_number() over (partition by post_id
                           order by alias_hits desc, company_id) as rn
    from matches
)

select post_id, company_id, name as company_name, ticker, sector
from ranked
where rn = 1
