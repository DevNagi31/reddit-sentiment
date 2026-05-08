"""Bridge: project JSONB rows from the postgres `posts` table written by the
Faktory crawler into the DuckDB schema the rest of the pipeline expects
(raw.posts and raw.comments in warehouse/db.py).

A submission JSON has `selftext` (post body) and `num_comments`; a comment
JSON has `parent_id` like `t1_*` or `t3_*`. We use that distinction to route
rows into the right DuckDB table.

Run after the crawler has been collecting for a while:
    python data-collection/sync_to_duckdb.py
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

# Allow imports from the project root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from warehouse.db import init_schema, upsert_comments, upsert_posts  # noqa: E402

load_dotenv()
load_dotenv(Path(__file__).resolve().parent / ".env")

logger = logging.getLogger("sync_to_duckdb")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

DATABASE_URL = os.environ.get("DATABASE_URL")
BATCH = 5000


def _is_comment(row: dict) -> bool:
    parent_id = row.get("parent_id")
    if isinstance(parent_id, str) and parent_id.startswith(("t1_", "t3_")):
        return True
    # Submissions always have selftext; comments don't.
    return "selftext" not in row


def _to_post(row: dict, board_name: str) -> dict:
    subreddit = board_name.removeprefix("reddit_")
    return {
        "post_id":      row["id"],
        "subreddit":    subreddit,
        "title":        row.get("title") or "",
        "body":         row.get("selftext") or "",
        "author":       row.get("author") or "[deleted]",
        "upvotes":      int(row.get("score") or 0),
        "num_comments": int(row.get("num_comments") or 0),
        "created_utc":  datetime.fromtimestamp(float(row["created_utc"])),
        "permalink":    f"https://reddit.com{row.get('permalink', '')}",
    }


def _to_comment(row: dict, board_name: str, thread_number: str) -> dict:
    subreddit = board_name.removeprefix("reddit_")
    return {
        "comment_id":  row["id"],
        "post_id":     thread_number,
        "subreddit":   subreddit,
        "body":        row.get("body") or "",
        "author":      row.get("author") or "[deleted]",
        "upvotes":     int(row.get("score") or 0),
        "created_utc": datetime.fromtimestamp(float(row["created_utc"])),
    }


def main() -> None:
    if not DATABASE_URL:
        sys.exit("DATABASE_URL not set. Copy data-collection/.env.example to .env first.")

    init_schema()

    conn = psycopg2.connect(dsn=DATABASE_URL, cursor_factory=RealDictCursor)
    cur = conn.cursor(name="sync_cursor")    # server-side cursor for streaming
    cur.itersize = BATCH

    cur.execute("""
        SELECT board_name, thread_number, post_number, created_at, data
        FROM posts
        WHERE board_name LIKE 'reddit_%'
    """)

    posts_buf: list[dict] = []
    comments_buf: list[dict] = []
    n_posts = n_comments = 0

    def flush() -> None:
        nonlocal n_posts, n_comments, posts_buf, comments_buf
        if posts_buf:
            n_posts += upsert_posts(posts_buf)
            posts_buf = []
        if comments_buf:
            n_comments += upsert_comments(comments_buf)
            comments_buf = []

    for row in cur:
        data = row["data"]
        if _is_comment(data):
            comments_buf.append(_to_comment(data, row["board_name"], row["thread_number"]))
        else:
            posts_buf.append(_to_post(data, row["board_name"]))

        if len(posts_buf) >= BATCH or len(comments_buf) >= BATCH:
            flush()

    flush()
    cur.close()
    conn.close()

    logger.info("Sync complete. Inserted %d new posts, %d new comments into DuckDB.",
                n_posts, n_comments)


if __name__ == "__main__":
    main()
