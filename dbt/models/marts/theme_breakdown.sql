-- Theme-level mart: posts and avg sentiment per company × theme.

select
    c.company_id,
    c.name                          as company_name,
    coalesce(f.theme, 'Other')      as theme,
    count(*)                        as posts,
    avg(f.score)                    as avg_sentiment,
    sum(f.upvotes)                  as total_upvotes
from {{ ref('fact_posts') }} f
join {{ ref('dim_company') }} c using (company_id)
group by 1, 2, 3
order by company_id, posts desc
