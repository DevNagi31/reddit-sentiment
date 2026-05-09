"""RedditSentiment — Brand Intelligence Dashboard.

A clean, data-dense Streamlit dashboard built on the dbt marts.
macOS-inspired visual language; no AI narrative; every panel is grounded
in a query against the warehouse.

Run after the pipeline has built the marts:
    streamlit run dashboard/app.py
"""
from __future__ import annotations

import html
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import DUCKDB_PATH


# ---------- Page setup -----------------------------------------------------

st.set_page_config(
    page_title="RedditSentiment — Brand Intelligence",
    page_icon="https://cdn.simpleicons.org/reddit/FF4500",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# macOS-inspired styling: SF Pro stack, Apple's neutral grays, soft shadows.
st.markdown("""
<style>
  :root {
    --bg:          #F5F5F7;
    --card:        #FFFFFF;
    --text:        #1D1D1F;
    --text-2:      #6E6E73;
    --separator:   #D2D2D7;
    --separator-l: #E8E8ED;
    --accent:      #0071E3;
    --positive:    #30D158;
    --neutral:     #8E8E93;
    --negative:    #FF453A;
  }

  /* font + base */
  html, body, [class*="css"], button, input, textarea, select {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display",
                 "SF Pro Text", "Helvetica Neue", Helvetica, Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
    color: var(--text);
  }
  .stApp { background: var(--bg); }

  /* hide Streamlit chrome */
  #MainMenu, header[data-testid="stHeader"], footer { visibility: hidden; }
  .block-container { padding-top: 1.6rem; padding-bottom: 2.5rem; max-width: 1400px; }

  /* page header */
  .page-title { font-size: 2.2rem; font-weight: 600; letter-spacing: -0.025em;
                color: var(--text); margin-bottom: 0.15rem; }
  .page-sub   { color: var(--text-2); font-size: 0.95rem; margin-bottom: 1.0rem;
                font-weight: 400; }

  /* KPI cards */
  .kpi-card { background: var(--card); border: 1px solid var(--separator-l);
              border-radius: 12px; padding: 18px 20px;
              box-shadow: 0 1px 3px rgba(0,0,0,0.03); }
  .kpi-label { color: var(--text-2); font-size: 0.7rem; text-transform: uppercase;
               letter-spacing: 0.06em; font-weight: 500; }
  .kpi-value { color: var(--text); font-size: 1.7rem; font-weight: 600;
               letter-spacing: -0.02em; line-height: 1.15; margin-top: 0.2rem; }
  .kpi-delta-pos { color: var(--positive); font-size: 0.85rem; font-weight: 500; }
  .kpi-delta-neg { color: var(--negative); font-size: 0.85rem; font-weight: 500; }
  .kpi-delta-neu { color: var(--text-2);   font-size: 0.85rem; font-weight: 500; }
  .kpi-with-logo { display:flex; align-items:center; gap:10px; }
  .kpi-with-logo img { width:24px; height:24px; border-radius:4px; }

  /* sentiment pills */
  .pill { padding:2px 10px; border-radius:999px; font-size:0.72rem;
          font-weight:600; letter-spacing:0.01em; }
  .pill-pos { background:#E5F8EA; color:#1B7F3A; }
  .pill-neu { background:#EEF0F3; color:#3A3A3C; }
  .pill-neg { background:#FFE5E3; color:#A4271F; }

  /* post cards */
  .post-card { background: var(--card); border:1px solid var(--separator-l);
               border-radius:12px; padding:14px 16px; margin-bottom:10px;
               box-shadow: 0 1px 2px rgba(0,0,0,0.02); transition: all .15s ease; }
  .post-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.06); border-color: var(--separator); }
  .post-row { display:flex; align-items:flex-start; gap:12px; }
  .post-logo { width:24px; height:24px; flex-shrink:0; margin-top:2px;
               border-radius:4px; }
  .post-body { flex:1; min-width:0; }
  .post-title { color: var(--text); font-weight:500; line-height:1.35;
                text-decoration:none; }
  .post-title:hover { color: var(--accent); }
  .post-meta  { color: var(--text-2); font-size:0.78rem; margin-top:4px;
                display:flex; gap:10px; align-items:center; }
  .post-meta .sep { color: var(--separator); }

  /* tabs — full-width segmented control with clear active state */
  div[data-baseweb="tab-list"] {
    gap: 6px;
    background: #FFFFFF;
    padding: 6px;
    border-radius: 12px;
    border: 1px solid var(--separator-l);
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    display: flex;
    width: 100%;
    margin-bottom: 1.2rem;
  }
  div[data-baseweb="tab"] {
    background: transparent;
    border-radius: 8px;
    padding: 10px 18px !important;
    height: auto;
    font-weight: 500;
    font-size: 0.95rem;
    color: var(--text-2);
    flex: 1;
    text-align: center;
    transition: all 0.15s ease;
    cursor: pointer;
  }
  div[data-baseweb="tab"]:hover {
    background: var(--separator-l);
    color: var(--text);
  }
  div[data-baseweb="tab"][aria-selected="true"] {
    background: var(--accent);
    color: #FFFFFF !important;
    box-shadow: 0 1px 4px rgba(0,113,227,0.35);
  }
  div[data-baseweb="tab"][aria-selected="true"] p {
    color: #FFFFFF !important;
    font-weight: 600;
  }
  /* hide Streamlit's default tab underline + border */
  div[data-baseweb="tab-highlight"], div[data-baseweb="tab-border"] {
    display: none !important;
  }

  /* tables */
  div[data-testid="stDataFrame"] { border:1px solid var(--separator-l);
                                    border-radius:12px; overflow:hidden; }

  /* divider tighter */
  hr { margin: 1.5rem 0 1.2rem 0 !important; border-color: var(--separator-l) !important; }

  /* selectbox + multiselect — softer */
  div[data-baseweb="select"] > div { background: var(--card);
                                     border-color: var(--separator) !important;
                                     border-radius: 8px !important; }

  /* section header */
  .sec-h { font-size: 0.95rem; font-weight: 600; color: var(--text);
           letter-spacing: -0.01em; margin: 0.4rem 0 0.6rem 0; }
  .sec-cap { color: var(--text-2); font-size: 0.78rem; margin-bottom: 0.6rem; }
</style>
""", unsafe_allow_html=True)


# ---------- Logos ----------------------------------------------------------

# Google's favicon service. Works reliably for any domain (simple-icons
# dropped Microsoft and Amazon). Returns the live company favicon.
COMPANY_DOMAINS: dict[str, str] = {
    "Tesla":     "tesla.com",
    "Apple":     "apple.com",
    "Google":    "google.com",
    "Microsoft": "microsoft.com",
    "Amazon":    "amazon.com",
}


def logo_url(company: str) -> str:
    domain = COMPANY_DOMAINS.get(company)
    if not domain:
        return ""
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=128"


def logo_img(company: str, size: int = 20) -> str:
    url = logo_url(company)
    if not url:
        return ""
    return (f'<img src="{url}" width="{size}" height="{size}" '
            f'style="vertical-align:middle;margin-right:8px;border-radius:4px;" />')


# ---------- Data layer -----------------------------------------------------

@st.cache_resource
def _conn():
    return duckdb.connect(str(DUCKDB_PATH), read_only=True)


@st.cache_data(ttl=300)
def q(sql: str) -> pd.DataFrame:
    return _conn().execute(sql).fetchdf()


def _has_marts() -> bool:
    try:
        q("SELECT 1 FROM marts.company_sentiment LIMIT 1")
        return True
    except Exception:
        return False


# ---------- Helpers --------------------------------------------------------

_DELTA_CLS = {
    "pos": "kpi-delta-pos",
    "neg": "kpi-delta-neg",
    "neu": "kpi-delta-neu",
}


def delta_color_for(value: float, threshold: float = 0.05) -> str:
    """Return 'pos' / 'neg' / 'neu' based on a small dead-zone around 0."""
    if value > threshold:
        return "pos"
    if value < -threshold:
        return "neg"
    return "neu"


def kpi(label: str, value: str, delta: str | None = None,
        delta_color: str = "pos", logo_company: str | None = None) -> None:
    delta_html = ""
    if delta:
        cls = _DELTA_CLS.get(delta_color, "kpi-delta-neu")
        delta_html = f'<div class="{cls}">{delta}</div>'
    if logo_company:
        value_html = (f'<div class="kpi-value kpi-with-logo">'
                      f'{logo_img(logo_company, size=24)}{value}</div>')
    else:
        value_html = f'<div class="kpi-value">{value}</div>'
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
        f'{value_html}{delta_html}</div>',
        unsafe_allow_html=True,
    )


def _safe(value, fallback: str = "—") -> str:
    """Coerce a possibly-None / NaN / non-string value to a safe display string.

    `x or fallback` doesn't work for NaN because NaN is truthy in Python.
    """
    if value is None:
        return fallback
    if isinstance(value, float) and pd.isna(value):
        return fallback
    s = str(value)
    return s if s else fallback


def sentiment_pill(s: str) -> str:
    return {
        "positive": '<span class="pill pill-pos">positive</span>',
        "neutral":  '<span class="pill pill-neu">neutral</span>',
        "negative": '<span class="pill pill-neg">negative</span>',
    }.get(s, "")


PLOTLY_LAYOUT = dict(
    template="simple_white",
    font=dict(family='-apple-system, BlinkMacSystemFont, "SF Pro Text", '
                     'Helvetica, Arial, sans-serif',
              size=12, color="#1D1D1F"),
    margin=dict(l=20, r=20, t=30, b=20),
    plot_bgcolor="white",
    paper_bgcolor="white",
    xaxis=dict(gridcolor="#F2F2F7", linecolor="#D2D2D7", tickfont=dict(color="#6E6E73")),
    yaxis=dict(gridcolor="#F2F2F7", linecolor="#D2D2D7", tickfont=dict(color="#6E6E73")),
)


def themed(fig: go.Figure, **overrides) -> go.Figure:
    layout = {**PLOTLY_LAYOUT, **overrides}
    fig.update_layout(**layout)
    return fig


# ---------- Header ---------------------------------------------------------

st.markdown('<div class="page-title">RedditSentiment</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="page-sub">Brand intelligence from raw Reddit posts — '
    'sentiment, themes, and trends across tracked companies.</div>',
    unsafe_allow_html=True,
)

if not _has_marts():
    st.error(
        "No mart data found. Run the pipeline first:\n\n"
        "1. python -m scraper.collectors --no-comments\n"
        "2. python -m nlp.sentiment --backend lexicon && python -m nlp.themes\n"
        "3. cd dbt && dbt run --profiles-dir ."
    )
    st.stop()


# ---------- Global KPI strip ----------------------------------------------

global_stats = q("""
    SELECT
        COUNT(*)                                          AS total_posts,
        COUNT(DISTINCT company_id)                        AS companies,
        COUNT(DISTINCT subreddit_id)                      AS subreddits,
        AVG(score)                                        AS avg_sentiment,
        QUANTILE_CONT(EPOCH(created_utc), 0.05)           AS first_epoch,
        MAX(created_utc)::DATE                            AS last_date
    FROM marts.fact_posts
""").iloc[0]

leaderboard = q("""
    SELECT company_name, total_posts, avg_sentiment, negative_share
    FROM marts.company_sentiment
    ORDER BY avg_sentiment DESC
""")

most_positive = leaderboard.iloc[0]
most_negative = leaderboard.iloc[-1]

c1, c2, c3, c4, c5 = st.columns(5)
with c1: kpi("Total posts",  f"{int(global_stats.total_posts):,}")
with c2: kpi("Companies",    f"{int(global_stats.companies)}")
with c3: kpi("Subreddits",   f"{int(global_stats.subreddits)}")
with c4: kpi("Most positive", most_positive.company_name,
             delta=f"{most_positive.avg_sentiment:+.2f} avg",
             delta_color=delta_color_for(most_positive.avg_sentiment),
             logo_company=most_positive.company_name)
with c5: kpi("Most negative", most_negative.company_name,
             delta=f"{most_negative.avg_sentiment:+.2f} avg",
             delta_color=delta_color_for(most_negative.avg_sentiment),
             logo_company=most_negative.company_name)

first_d = pd.to_datetime(global_stats.first_epoch, unit="s").strftime("%b %d, %Y")
last_d  = pd.to_datetime(global_stats.last_date).strftime("%b %d, %Y")
st.markdown(
    f'<div class="page-sub" style="margin-top:0.4rem">Window: '
    f'{first_d} → {last_d} <span style="opacity:0.6">'
    f'(5th–100th percentile of post timestamps)</span></div>',
    unsafe_allow_html=True,
)
st.divider()


# ---------- Tabs -----------------------------------------------------------

tab_overview, tab_company, tab_themes, tab_posts = st.tabs(
    ["Overview", "Company Deep-Dive", "Themes", "Posts Explorer"]
)


# === Overview =============================================================

with tab_overview:
    left, right = st.columns([5, 4])

    with left:
        st.markdown('<div class="sec-h">Company leaderboard</div>',
                    unsafe_allow_html=True)
        lb = leaderboard.copy()
        lb.insert(0, "Logo", lb["company_name"].apply(logo_url))
        lb["avg_sentiment"]  = lb["avg_sentiment"].round(3)
        lb["negative_share"] = (lb["negative_share"] * 100).round(1)
        lb.columns = ["Logo", "Company", "Posts", "Avg sentiment", "Negative %"]
        st.dataframe(
            lb,
            hide_index=True,
            use_container_width=True,
            column_config={
                "Logo": st.column_config.ImageColumn("", width="small"),
                "Avg sentiment": st.column_config.ProgressColumn(
                    format="%.2f", min_value=-1.0, max_value=1.0
                ),
                "Negative %": st.column_config.ProgressColumn(
                    format="%.1f%%", min_value=0.0, max_value=100.0
                ),
            },
        )

    with right:
        st.markdown('<div class="sec-h">Sentiment vs volume</div>',
                    unsafe_allow_html=True)
        scatter_df = q("""
            SELECT company_name, total_posts, avg_sentiment, negative_share
            FROM marts.company_sentiment
        """)
        fig = px.scatter(
            scatter_df, x="total_posts", y="avg_sentiment",
            size="total_posts", color="avg_sentiment",
            color_continuous_scale="RdYlGn", range_color=[-0.5, 0.5],
            text="company_name",
            labels={"total_posts": "Posts", "avg_sentiment": "Avg sentiment"},
        )
        fig.update_traces(textposition="top center",
                          textfont=dict(size=11, color="#1D1D1F"))
        themed(fig, height=320, showlegend=False, coloraxis_showscale=False)
        fig.add_hline(y=0, line_dash="dot", line_color="#D2D2D7")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="sec-h">Company × theme sentiment heatmap</div>',
                unsafe_allow_html=True)
    heat = q("""
        SELECT company_name, theme, avg_sentiment, posts
        FROM marts.theme_breakdown
        WHERE posts >= 3
    """)
    if not heat.empty:
        pivot = heat.pivot(index="theme", columns="company_name",
                           values="avg_sentiment")
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values, x=pivot.columns, y=pivot.index,
            colorscale="RdYlGn", zmid=0, zmin=-1, zmax=1,
            colorbar=dict(title="Avg<br>sentiment", thickness=14, len=0.7,
                          tickfont=dict(color="#6E6E73")),
            hovertemplate="%{y} • %{x}<br>avg: %{z:.2f}<extra></extra>",
        ))
        themed(fig, height=380)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Not enough data to render the heatmap (need ≥3 posts per company × theme cell).")


# === Company Deep-Dive =====================================================

with tab_company:
    companies = q("SELECT company_id, company_name FROM marts.company_sentiment ORDER BY company_name")
    company_name = st.selectbox("Pick a company",
                                companies["company_name"].tolist(),
                                key="company_picker")
    company_id = int(companies.loc[companies.company_name == company_name, "company_id"].iloc[0])

    st.markdown(
        f'<div class="sec-h" style="font-size:1.4rem;display:flex;align-items:center;gap:10px;">'
        f'{logo_img(company_name, size=28)}{company_name}</div>',
        unsafe_allow_html=True,
    )

    cs = q(f"""
        SELECT total_posts, avg_sentiment, negative_share, positive_posts,
               negative_posts, neutral_posts, total_upvotes
        FROM marts.company_sentiment
        WHERE company_id = {company_id}
    """).iloc[0]

    _avg = float(cs.avg_sentiment)
    _label = ("positive" if _avg > 0.05 else
              "negative" if _avg < -0.05 else "neutral")

    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi("Posts",          f"{int(cs.total_posts):,}")
    with k2: kpi("Avg sentiment",  f"{_avg:+.2f}",
                 delta=_label,
                 delta_color=delta_color_for(_avg))
    with k3: kpi("Negative share", f"{cs.negative_share:.0%}")
    with k4: kpi("Total upvotes",  f"{int(cs.total_upvotes):,}")

    mix_df = pd.DataFrame({
        "sentiment": ["Positive", "Neutral", "Negative"],
        "count": [int(cs.positive_posts), int(cs.neutral_posts), int(cs.negative_posts)],
    })
    fig = px.bar(
        mix_df, x="sentiment", y="count", color="sentiment",
        color_discrete_map={"Positive": "#30D158", "Neutral": "#8E8E93",
                            "Negative": "#FF453A"},
    )
    themed(fig, height=240, showlegend=False)
    fig.update_layout(xaxis_title=None, yaxis_title=None)

    left, right = st.columns([3, 5])
    with left:
        st.markdown('<div class="sec-h">Sentiment mix</div>', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.markdown('<div class="sec-h">Themes</div>', unsafe_allow_html=True)
        themes_df = q(f"""
            SELECT theme, posts, avg_sentiment, total_upvotes
            FROM marts.theme_breakdown
            WHERE company_id = {company_id}
            ORDER BY posts DESC
        """)
        st.dataframe(
            themes_df,
            hide_index=True,
            use_container_width=True,
            column_config={
                "avg_sentiment": st.column_config.ProgressColumn(
                    "Avg sentiment", format="%.2f",
                    min_value=-1.0, max_value=1.0,
                ),
                "posts": st.column_config.NumberColumn("Posts"),
                "total_upvotes": st.column_config.NumberColumn("Upvotes", format="%d"),
            },
        )

    st.markdown('<div class="sec-h">Sentiment trend</div>', unsafe_allow_html=True)
    trend = q(f"""
        SELECT date, avg_sentiment, rolling_7d_sentiment, posts
        FROM marts.trend_analysis
        WHERE company_id = {company_id}
        ORDER BY date
    """)
    if not trend.empty and len(trend) > 1:
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=trend.date, y=trend.posts, name="Posts/day",
            marker_color="#E8E8ED", yaxis="y2", opacity=0.7,
            hovertemplate="%{x|%b %d}<br>%{y} posts<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=trend.date, y=trend.avg_sentiment, mode="lines+markers",
            name="Daily avg", line=dict(color="#8E8E93", width=1),
            marker=dict(size=4),
            hovertemplate="%{x|%b %d}<br>avg: %{y:.2f}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=trend.date, y=trend.rolling_7d_sentiment, mode="lines",
            name="7-day rolling",
            line=dict(color="#0071E3", width=2.5),
            hovertemplate="%{x|%b %d}<br>7d avg: %{y:.2f}<extra></extra>",
        ))
        themed(fig, height=380, hovermode="x unified")
        fig.update_layout(
            yaxis=dict(title="Sentiment", zeroline=True, zerolinecolor="#E8E8ED"),
            yaxis2=dict(title="Posts", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Need at least 2 days of data to plot a trend.")

    st.markdown('<div class="sec-h">Top posts</div>', unsafe_allow_html=True)
    pp1, pp2 = st.columns(2)
    with pp1:
        st.markdown('<div class="sec-cap">Most positive</div>',
                    unsafe_allow_html=True)
        for r in q(f"""
            SELECT title, score, upvotes, permalink
            FROM marts.fact_posts
            WHERE company_id = {company_id} AND sentiment = 'positive'
            ORDER BY score DESC, upvotes DESC LIMIT 5
        """).itertuples():
            st.markdown(
                f'<div class="post-card"><div class="post-row">'
                f'<img src="{logo_url(company_name)}" class="post-logo" />'
                f'<div class="post-body">'
                f'<a href="{html.escape(_safe(r.permalink, "#"))}" target="_blank" class="post-title">'
                f'{html.escape(_safe(r.title)[:140])}</a>'
                f'<div class="post-meta">{sentiment_pill("positive")}'
                f'<span class="sep">·</span>score {r.score:+.2f}'
                f'<span class="sep">·</span>{int(r.upvotes)} upvotes</div>'
                f'</div></div></div>',
                unsafe_allow_html=True,
            )
    with pp2:
        st.markdown('<div class="sec-cap">Most negative</div>',
                    unsafe_allow_html=True)
        for r in q(f"""
            SELECT title, score, upvotes, permalink
            FROM marts.fact_posts
            WHERE company_id = {company_id} AND sentiment = 'negative'
            ORDER BY score ASC, upvotes DESC LIMIT 5
        """).itertuples():
            st.markdown(
                f'<div class="post-card"><div class="post-row">'
                f'<img src="{logo_url(company_name)}" class="post-logo" />'
                f'<div class="post-body">'
                f'<a href="{html.escape(_safe(r.permalink, "#"))}" target="_blank" class="post-title">'
                f'{html.escape(_safe(r.title)[:140])}</a>'
                f'<div class="post-meta">{sentiment_pill("negative")}'
                f'<span class="sep">·</span>score {r.score:+.2f}'
                f'<span class="sep">·</span>{int(r.upvotes)} upvotes</div>'
                f'</div></div></div>',
                unsafe_allow_html=True,
            )


# === Themes ================================================================

with tab_themes:
    st.markdown('<div class="sec-h">Theme distribution across companies</div>',
                unsafe_allow_html=True)
    tdata = q("""
        SELECT theme, company_name, posts, avg_sentiment
        FROM marts.theme_breakdown
        WHERE theme != 'Other'
    """)
    fig = px.bar(
        tdata, x="theme", y="posts", color="company_name",
        barmode="group",
        labels={"posts": "Posts", "theme": "", "company_name": "Company"},
        color_discrete_sequence=["#0071E3", "#5856D6", "#FF9500", "#30D158", "#FF453A"],
    )
    themed(fig, height=420)
    fig.update_layout(legend=dict(orientation="h", yanchor="bottom",
                                  y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="sec-h">Theme sentiment, weighted by post volume</div>',
                unsafe_allow_html=True)
    twt = q("""
        SELECT theme,
               SUM(posts) AS posts,
               SUM(posts * avg_sentiment) / NULLIF(SUM(posts), 0) AS avg_sentiment
        FROM marts.theme_breakdown
        WHERE theme != 'Other'
        GROUP BY theme
        ORDER BY avg_sentiment ASC
    """)
    fig = px.bar(
        twt, x="avg_sentiment", y="theme", orientation="h",
        color="avg_sentiment", color_continuous_scale="RdYlGn",
        range_color=[-1, 1], text="posts",
        labels={"avg_sentiment": "Avg sentiment (volume-weighted)", "theme": ""},
    )
    fig.update_traces(texttemplate="%{text:.0f} posts", textposition="outside")
    themed(fig, height=420, coloraxis_showscale=False)
    fig.add_vline(x=0, line_dash="dot", line_color="#D2D2D7")
    st.plotly_chart(fig, use_container_width=True)


# === Posts Explorer ========================================================

with tab_posts:
    st.markdown('<div class="sec-h">Filter posts</div>', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns([2, 2, 2, 1])
    with f1:
        co_filter = st.multiselect(
            "Company",
            sorted(q("SELECT name FROM marts.dim_company ORDER BY name").name.tolist()),
            default=None,
        )
    with f2:
        sent_filter = st.multiselect(
            "Sentiment", ["positive", "neutral", "negative"], default=None,
        )
    with f3:
        theme_filter = st.multiselect(
            "Theme",
            sorted(q("SELECT DISTINCT theme FROM marts.fact_posts WHERE theme IS NOT NULL").theme.tolist()),
            default=None,
        )
    with f4:
        n_posts = st.number_input("Limit", min_value=10, max_value=500, value=50, step=10)

    where = ["1=1"]
    if co_filter:
        where.append("c.name IN (" + ",".join(f"'{x}'" for x in co_filter) + ")")
    if sent_filter:
        where.append("f.sentiment IN (" + ",".join(f"'{s}'" for s in sent_filter) + ")")
    if theme_filter:
        where.append("f.theme IN (" + ",".join(f"'{t}'" for t in theme_filter) + ")")

    posts = q(f"""
        SELECT f.created_utc,
               c.name AS company_name,
               f.theme, f.sentiment, f.score, f.upvotes, f.title, f.permalink
        FROM marts.fact_posts f
        JOIN marts.dim_company c USING (company_id)
        WHERE {' AND '.join(where)}
        ORDER BY f.created_utc DESC
        LIMIT {int(n_posts)}
    """)
    st.markdown(f'<div class="sec-cap">{len(posts)} posts</div>',
                unsafe_allow_html=True)

    if posts.empty:
        st.info("No posts match the current filter.")

    for r in posts.itertuples():
        st.markdown(
            f'<div class="post-card"><div class="post-row">'
            f'<img src="{logo_url(_safe(r.company_name, ""))}" class="post-logo" />'
            f'<div class="post-body">'
            f'<a href="{html.escape(_safe(r.permalink, "#"))}" target="_blank" class="post-title">'
            f'{html.escape(_safe(r.title)[:140])}</a>'
            f'<div class="post-meta">{sentiment_pill(_safe(r.sentiment, "neutral"))}'
            f'<span class="sep">·</span><strong>{html.escape(_safe(r.company_name))}</strong>'
            f'<span class="sep">·</span>{html.escape(_safe(r.theme))}'
            f'<span class="sep">·</span>{r.created_utc:%b %d, %H:%M}'
            f'<span class="sep">·</span>score {r.score:+.2f}'
            f'<span class="sep">·</span>{int(r.upvotes)} ups'
            f'</div></div></div>',
            unsafe_allow_html=True,
        )
