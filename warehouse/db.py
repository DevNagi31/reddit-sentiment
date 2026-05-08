"""DuckDB connection helper + schema bootstrap for the raw landing tables.

The dbt project owns the analytical models (staging/intermediate/marts).
This module owns only the raw landing tables that the scraper writes to and
the seed dimension tables (companies, subreddits) populated from config.
"""
from __future__ import annotations

import duckdb
import pandas as pd

from config import COMPANIES, DUCKDB_PATH, SUBREDDITS


def connect() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(DUCKDB_PATH))


def init_schema() -> None:
    con = connect()
    try:
        con.execute("CREATE SCHEMA IF NOT EXISTS raw")
        con.execute("CREATE SCHEMA IF NOT EXISTS seed")

        con.execute("""
            CREATE TABLE IF NOT EXISTS raw.posts (
                post_id        VARCHAR PRIMARY KEY,
                subreddit      VARCHAR,
                title          VARCHAR,
                body           VARCHAR,
                author         VARCHAR,
                upvotes        INTEGER,
                num_comments   INTEGER,
                created_utc    TIMESTAMP,
                permalink      VARCHAR,
                scraped_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS raw.comments (
                comment_id     VARCHAR PRIMARY KEY,
                post_id        VARCHAR,
                subreddit      VARCHAR,
                body           VARCHAR,
                author         VARCHAR,
                upvotes        INTEGER,
                created_utc    TIMESTAMP,
                scraped_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # NLP outputs land here; dbt joins them with raw.posts.
        con.execute("""
            CREATE TABLE IF NOT EXISTS raw.post_sentiment (
                post_id        VARCHAR PRIMARY KEY,
                sentiment      VARCHAR,        -- positive / neutral / negative
                score          DOUBLE,         -- signed score in [-1, 1]
                theme          VARCHAR,
                model_version  VARCHAR,
                scored_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Seed dimensions — kept in sync with config.py on every init.
        con.execute("""
            CREATE TABLE IF NOT EXISTS seed.companies (
                company_id INTEGER PRIMARY KEY,
                name       VARCHAR,
                ticker     VARCHAR,
                sector     VARCHAR,
                aliases    VARCHAR
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS seed.subreddits (
                name     VARCHAR PRIMARY KEY,
                category VARCHAR
            )
        """)

        companies_df = pd.DataFrame([
            {**c, "aliases": ",".join(c["aliases"])} for c in COMPANIES
        ])
        subs_df = pd.DataFrame(SUBREDDITS)

        con.execute("DELETE FROM seed.companies")
        con.register("companies_df", companies_df)
        con.execute("INSERT INTO seed.companies SELECT * FROM companies_df")

        con.execute("DELETE FROM seed.subreddits")
        con.register("subs_df", subs_df)
        con.execute("INSERT INTO seed.subreddits SELECT * FROM subs_df")

    finally:
        con.close()


def upsert_posts(rows: list[dict]) -> int:
    """Insert posts, ignoring duplicates by post_id. Returns inserted count."""
    if not rows:
        return 0
    df = pd.DataFrame(rows)
    con = connect()
    try:
        con.register("incoming", df)
        before = con.execute("SELECT COUNT(*) FROM raw.posts").fetchone()[0]
        con.execute("""
            INSERT INTO raw.posts
              (post_id, subreddit, title, body, author, upvotes,
               num_comments, created_utc, permalink)
            SELECT post_id, subreddit, title, body, author, upvotes,
                   num_comments, created_utc, permalink
            FROM incoming
            WHERE post_id NOT IN (SELECT post_id FROM raw.posts)
        """)
        after = con.execute("SELECT COUNT(*) FROM raw.posts").fetchone()[0]
        return after - before
    finally:
        con.close()


def upsert_comments(rows: list[dict]) -> int:
    if not rows:
        return 0
    df = pd.DataFrame(rows)
    con = connect()
    try:
        con.register("incoming", df)
        before = con.execute("SELECT COUNT(*) FROM raw.comments").fetchone()[0]
        con.execute("""
            INSERT INTO raw.comments
              (comment_id, post_id, subreddit, body, author, upvotes, created_utc)
            SELECT comment_id, post_id, subreddit, body, author, upvotes, created_utc
            FROM incoming
            WHERE comment_id NOT IN (SELECT comment_id FROM raw.comments)
        """)
        after = con.execute("SELECT COUNT(*) FROM raw.comments").fetchone()[0]
        return after - before
    finally:
        con.close()


def upsert_sentiment(rows: list[dict]) -> int:
    if not rows:
        return 0
    df = pd.DataFrame(rows)
    con = connect()
    try:
        con.register("incoming", df)
        con.execute("DELETE FROM raw.post_sentiment WHERE post_id IN (SELECT post_id FROM incoming)")
        con.execute("""
            INSERT INTO raw.post_sentiment
              (post_id, sentiment, score, theme, model_version)
            SELECT post_id, sentiment, score, theme, model_version FROM incoming
        """)
        return len(df)
    finally:
        con.close()
