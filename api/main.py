"""Public sentiment API — read-only over the dbt marts.

Run:
    uvicorn api.main:app --reload
"""
from __future__ import annotations

from contextlib import contextmanager

import duckdb
from fastapi import FastAPI, HTTPException, Query

from config import DUCKDB_PATH

app = FastAPI(
    title="RedditSentiment API",
    description="Public read-only sentiment data over tracked companies.",
    version="0.1.0",
)


@contextmanager
def db():
    con = duckdb.connect(str(DUCKDB_PATH), read_only=True)
    try:
        yield con
    finally:
        con.close()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/companies")
def list_companies() -> list[dict]:
    with db() as con:
        rows = con.execute("""
            SELECT company_id, name, ticker, sector
            FROM marts.dim_company
            ORDER BY name
        """).fetchall()
    return [
        {"company_id": r[0], "name": r[1], "ticker": r[2], "sector": r[3]}
        for r in rows
    ]


@app.get("/companies/{ticker}/sentiment")
def company_sentiment(ticker: str) -> dict:
    with db() as con:
        row = con.execute("""
            SELECT total_posts, avg_sentiment, negative_share,
                   positive_posts, neutral_posts, negative_posts
            FROM marts.company_sentiment
            WHERE ticker = ?
        """, [ticker.upper()]).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker}")
    return {
        "ticker":          ticker.upper(),
        "total_posts":     row[0],
        "avg_sentiment":   row[1],
        "negative_share":  row[2],
        "positive_posts":  row[3],
        "neutral_posts":   row[4],
        "negative_posts":  row[5],
    }


@app.get("/companies/{ticker}/trend")
def company_trend(
    ticker: str,
    days: int = Query(30, ge=1, le=365),
) -> list[dict]:
    with db() as con:
        rows = con.execute(f"""
            SELECT t.date, t.posts, t.avg_sentiment, t.rolling_7d_sentiment
            FROM marts.trend_analysis t
            JOIN marts.dim_company c USING (company_id)
            WHERE c.ticker = ?
              AND t.date >= current_date - INTERVAL '{int(days)}' DAY
            ORDER BY t.date
        """, [ticker.upper()]).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No trend data for {ticker}")
    return [
        {
            "date":                 r[0].isoformat() if r[0] else None,
            "posts":                r[1],
            "avg_sentiment":        r[2],
            "rolling_7d_sentiment": r[3],
        }
        for r in rows
    ]


@app.get("/companies/{ticker}/themes")
def company_themes(ticker: str) -> list[dict]:
    with db() as con:
        rows = con.execute("""
            SELECT t.theme, t.posts, t.avg_sentiment, t.total_upvotes
            FROM marts.theme_breakdown t
            JOIN marts.dim_company c USING (company_id)
            WHERE c.ticker = ?
            ORDER BY t.posts DESC
        """, [ticker.upper()]).fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No theme data for {ticker}")
    return [
        {"theme": r[0], "posts": r[1], "avg_sentiment": r[2], "total_upvotes": r[3]}
        for r in rows
    ]


@app.get("/companies/{ticker}/comments")
def company_comments(ticker: str) -> dict:
    with db() as con:
        try:
            row = con.execute("""
                SELECT cs.comments, cs.avg_sentiment,
                       cs.positive_comments, cs.negative_comments,
                       cs.total_comment_upvotes
                FROM marts.comment_sentiment_by_company cs
                JOIN marts.dim_company c USING (company_id)
                WHERE c.ticker = ?
            """, [ticker.upper()]).fetchone()
        except Exception:
            raise HTTPException(
                status_code=503,
                detail="Comment sentiment mart not built yet — run NLP comments + dbt.",
            )
    if not row:
        raise HTTPException(status_code=404, detail=f"No comment data for {ticker}")
    return {
        "ticker":              ticker.upper(),
        "comments":            row[0],
        "avg_sentiment":       row[1],
        "positive_comments":   row[2],
        "negative_comments":   row[3],
        "total_comment_upvotes": row[4],
    }
