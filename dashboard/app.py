"""Streamlit storytelling dashboard.

Run after dbt has built the marts:
    streamlit run dashboard/app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow imports from the project root when run via `streamlit run dashboard/app.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

from config import DUCKDB_PATH
from nlp.summarize import generate as generate_narrative


st.set_page_config(
    page_title="RedditSentiment — Brand Intelligence",
    page_icon="📊",
    layout="wide",
)


@st.cache_resource
def _conn():
    return duckdb.connect(str(DUCKDB_PATH), read_only=True)


@st.cache_data(ttl=300)
def load(query: str) -> pd.DataFrame:
    return _conn().execute(query).fetchdf()


def _has_marts() -> bool:
    try:
        load("SELECT 1 FROM marts.company_sentiment LIMIT 1")
        return True
    except Exception:
        return False


# --- Header ---------------------------------------------------------------
st.title("RedditSentiment — Brand Intelligence Dashboard")
st.caption("Reddit posts → NLP → DuckDB warehouse → dbt marts → narrative insights")

if not _has_marts():
    st.error(
        "No mart data found. Run the pipeline first:\n\n"
        "1. `python -m scraper.collectors --sample`\n"
        "2. `python -m nlp.sentiment && python -m nlp.themes`\n"
        "3. `cd dbt && dbt run --profiles-dir .`"
    )
    st.stop()

# --- Sidebar --------------------------------------------------------------
companies = load("SELECT company_id, company_name FROM marts.company_sentiment ORDER BY company_name")
company_name = st.sidebar.selectbox("Company", companies["company_name"].tolist())
company_id = int(companies.loc[companies.company_name == company_name, "company_id"].iloc[0])

# --- KPI strip ------------------------------------------------------------
kpis = load(f"""
    SELECT total_posts, avg_sentiment, negative_share, positive_posts, negative_posts
    FROM marts.company_sentiment
    WHERE company_id = {company_id}
""").iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total posts", f"{int(kpis.total_posts):,}")
c2.metric("Avg sentiment", f"{kpis.avg_sentiment:+.2f}")
c3.metric("Negative share", f"{kpis.negative_share:.0%}")
c4.metric("Positive posts", f"{int(kpis.positive_posts):,}")

# --- Storytelling narrative ----------------------------------------------
st.subheader("📊 The story this week")

weekly = load(f"""
    SELECT week_start, posts, avg_sentiment, wow_sentiment_pct_change
    FROM marts.weekly_summary
    WHERE company_id = {company_id}
    ORDER BY week_start DESC
    LIMIT 1
""")

themes_this_co = load(f"""
    SELECT theme, posts, avg_sentiment
    FROM marts.theme_breakdown
    WHERE company_id = {company_id}
    ORDER BY posts DESC
""")

if not weekly.empty and not themes_this_co.empty:
    neg_themes = themes_this_co.sort_values("avg_sentiment").head(1).iloc[0]
    pos_themes = themes_this_co.sort_values("avg_sentiment", ascending=False).head(1).iloc[0]
    facts = {
        "company":               company_name,
        "sentiment_delta_pct":   float(weekly.iloc[0].wow_sentiment_pct_change or 0),
        "total_posts":           int(weekly.iloc[0].posts),
        "top_negative_theme":    neg_themes.theme,
        "top_negative_posts":    int(neg_themes.posts),
        "top_negative_score":    float(neg_themes.avg_sentiment),
        "top_positive_theme":    pos_themes.theme,
        "top_positive_posts":    int(pos_themes.posts),
        "top_positive_score":    float(pos_themes.avg_sentiment),
    }
    st.info(generate_narrative(facts))

# --- Trend chart ----------------------------------------------------------
st.subheader("Sentiment over time")
trend = load(f"""
    SELECT date, avg_sentiment, rolling_7d_sentiment, posts
    FROM marts.trend_analysis
    WHERE company_id = {company_id}
    ORDER BY date
""")
fig = px.line(
    trend, x="date", y=["avg_sentiment", "rolling_7d_sentiment"],
    labels={"value": "Sentiment", "variable": "Series"},
)
fig.update_layout(legend_title_text="", hovermode="x unified")
st.plotly_chart(fig, use_container_width=True)

# --- Theme breakdown ------------------------------------------------------
st.subheader(f"Top themes — {company_name}")
st.dataframe(
    themes_this_co.assign(
        avg_sentiment=lambda d: d.avg_sentiment.round(2)
    ),
    use_container_width=True,
    hide_index=True,
)

# --- Cross-company comparison --------------------------------------------
st.subheader("All companies — at a glance")
overview = load("""
    SELECT company_name, total_posts, avg_sentiment, negative_share
    FROM marts.company_sentiment
    ORDER BY avg_sentiment DESC
""")
fig2 = px.bar(
    overview, x="company_name", y="avg_sentiment",
    color="avg_sentiment", color_continuous_scale="RdYlGn",
    labels={"avg_sentiment": "Avg sentiment", "company_name": ""},
)
st.plotly_chart(fig2, use_container_width=True)
