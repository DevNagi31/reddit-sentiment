# RedditSentiment — NLP Analytics Pipeline with Business Storytelling

An analytics pipeline that scrapes Reddit for product/company sentiment, builds a star-schema warehouse, transforms data with dbt, and creates a storytelling dashboard that turns raw sentiment data into actionable business insights.

## Why This Project

- **SQL + Python + BI tool** appears in 80%+ of data analyst job postings
- **Stakeholder communication** is in 60% of postings — this project practices storytelling with data
- Shows: NLP, data modeling, dbt, visualization, and translating numbers into business strategy
- Produces real, shareable insights — blog-post-worthy findings

## The Problem

Companies spend thousands on sentiment analysis tools. Reddit has millions of authentic, unfiltered opinions about every product and company — but it's unstructured noise. This turns it into structured, actionable intelligence.

## What It Does

```
┌─────────────────────────────────────────────────────┐
│ RedditSentiment — Brand Intelligence Dashboard       │
│                                                       │
│ 📊 Story: "Tesla sentiment dropped 34% this week     │
│ after the recall announcement. The most negative      │
│ subreddit shifted from r/RealTesla to r/cars,        │
│ suggesting mainstream backlash, not just critics."    │
│                                                       │
│ Sentiment Over Time                                   │
│ ▇▇▇▇▆▅▄▃▂▁▂▃  Tesla                                │
│ ▃▄▅▅▆▆▇▇▇▇▇▇  Apple                                │
│ ▅▅▅▅▅▅▅▅▅▅▅▅  Google (stable)                       │
│                                                       │
│ Top Themes (Tesla, This Week)     Volume: 12,430     │
│ ┌────────────────┬───────┬────────┐                  │
│ │ Theme          │ Sent. │ Posts  │                  │
│ ├────────────────┼───────┼────────┤                  │
│ │ Recall         │ -0.72 │ 3,240  │                  │
│ │ Autopilot      │ -0.45 │ 2,100  │                  │
│ │ Model Y Price  │ +0.31 │ 1,850  │                  │
│ │ Charging       │ +0.52 │ 1,240  │                  │
│ └────────────────┴───────┴────────┘                  │
│                                                       │
│ AI Summary: "Negative sentiment is concentrated in   │
│ safety-related themes. Price and charging sentiment   │
│ remain positive, suggesting the brand damage is       │
│ issue-specific, not systemic."                        │
└─────────────────────────────────────────────────────┘
```

### Features

- **Reddit Scraper** — collects posts and comments from configurable subreddits
- **NLP Pipeline** — sentiment scoring, topic extraction, theme clustering
- **Star Schema Warehouse** — fact and dimension tables modeled for analytics
- **dbt Transformations** — staging, intermediate, and mart models with tests
- **Storytelling Dashboard** — not just charts, but AI-generated narrative insights
- **Public API** — others can query your sentiment data
- **Automated Reports** — weekly email/Slack summaries

### The Storytelling Angle (What Sets This Apart)

Most data projects show charts. This one **tells stories**:

- "What happened?" → Sentiment dropped 34%
- "Why?" → Recall announcement drove 3,240 negative posts
- "So what?" → Damage is issue-specific, not brand-wide
- "What should we do?" → Focus PR on safety response, don't discount

This is exactly what data analyst job postings mean by "stakeholder communication."

## Data Model (Star Schema)

```
                    ┌──────────────┐
                    │ dim_subreddit│
                    │──────────────│
                    │ subreddit_id │
                    │ name         │
                    │ subscribers  │
                    │ category     │
                    └──────┬───────┘
                           │
┌──────────────┐    ┌──────┴───────┐    ┌──────────────┐
│ dim_date     │    │ fact_posts    │    │ dim_company  │
│──────────────│────│──────────────│────│──────────────│
│ date_id      │    │ post_id      │    │ company_id   │
│ date         │    │ subreddit_id │    │ name         │
│ day_of_week  │    │ company_id   │    │ ticker       │
│ week         │    │ date_id      │    │ sector       │
│ month        │    │ sentiment    │    └──────────────┘
│ quarter      │    │ score        │
└──────────────┘    │ num_comments │
                    │ upvotes      │
                    │ theme        │
                    └──────────────┘
```

## Tech Stack (All Free)

| Component | Tool | Cost |
|---|---|---|
| Data Source | Reddit API (free, 100 req/min) | $0 |
| NLP | HuggingFace transformers (local, free) — `cardiffnlp/twitter-roberta-base-sentiment` | $0 |
| Topic Modeling | BERTopic (open source) | $0 |
| Data Warehouse | DuckDB (free local analytical DB) | $0 |
| Transformations | dbt Core (open source) | $0 |
| Orchestration | Airflow (Docker, open source) | $0 |
| Dashboard | Streamlit on Streamlit Cloud or Apache Superset (free) | $0 |
| AI Summaries | Groq (Llama 3.3 70B, free) for narrative generation | $0 |
| API | FastAPI on Render (free) | $0 |
| CI/CD | GitHub Actions | $0 |

## Project Structure

```
reddit-sentiment/
├── scraper/
│   ├── reddit_client.py        # Reddit API client
│   ├── collectors.py           # Subreddit + keyword collectors
│   └── scheduler.py            # Scheduled scraping jobs
├── nlp/
│   ├── sentiment.py            # Sentiment scoring (HuggingFace)
│   ├── topics.py               # Topic extraction (BERTopic)
│   ├── themes.py               # Theme clustering
│   └── summarize.py            # AI narrative generation (Groq)
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   │   ├── stg_posts.sql           # Raw posts → cleaned
│   │   │   └── stg_comments.sql        # Raw comments → cleaned
│   │   ├── intermediate/
│   │   │   ├── int_post_sentiment.sql   # Posts + sentiment scores
│   │   │   └── int_theme_agg.sql       # Theme aggregations
│   │   └── marts/
│   │       ├── company_sentiment.sql    # Company-level metrics
│   │       ├── trend_analysis.sql       # Time-series trends
│   │       ├── theme_breakdown.sql      # Theme analysis
│   │       └── weekly_summary.sql       # Weekly narrative data
│   ├── tests/
│   └── dbt_project.yml
├── api/
│   └── main.py                 # FastAPI public sentiment API
├── dashboard/
│   └── app.py                  # Streamlit storytelling dashboard
├── airflow/
│   ├── dags/
│   │   ├── scrape_reddit.py    # Daily scraping DAG
│   │   ├── run_nlp.py          # NLP processing DAG
│   │   └── transform.py        # dbt run DAG
│   └── docker-compose.yml
└── README.md
```

## Run Locally

```bash
# Start Airflow
cd airflow && docker-compose up -d

# Scrape data
python scraper/reddit_client.py --subreddits stocks,technology --days 30

# Run NLP pipeline
python nlp/sentiment.py && python nlp/topics.py

# Run dbt
cd dbt && dbt run && dbt test

# Launch dashboard
cd dashboard && streamlit run app.py
```

## Sample Insights (What the Dashboard Produces)

> **Weekly Report — April 21, 2026**
>
> Tesla sentiment fell 34% WoW driven by the Model Y recall (3,240 posts, avg sentiment -0.72). However, sentiment on pricing (+0.31) and Supercharger network (+0.52) remained positive. This suggests a containable PR issue rather than fundamental brand erosion.
>
> Apple maintained steady positive sentiment (+0.68) with iPhone 17 leaks generating the most discussion (4,100 posts). Notably, r/Android showed 12% positive mentions of Apple — the highest cross-platform positivity in 6 months.

This is the kind of output that gets you hired as a data analyst.
