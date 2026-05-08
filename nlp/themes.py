"""Keyword-based theme tagging.

Lightweight by design — picks the theme whose keyword set has the most
hits in the post text. Returns NULL when no theme matches. Real BERTopic
clustering would slot in here as a swap-in.
"""
from __future__ import annotations

import argparse
import logging

from config import THEMES
from warehouse.db import connect, init_schema

log = logging.getLogger(__name__)


def _theme_for(text: str) -> str | None:
    t = (text or "").lower()
    best, best_hits = None, 0
    for theme, keywords in THEMES.items():
        hits = sum(1 for kw in keywords if kw in t)
        if hits > best_hits:
            best, best_hits = theme, hits
    return best


def tag(limit: int | None = None) -> int:
    init_schema()
    con = connect()
    try:
        sql = """
            SELECT p.post_id, COALESCE(p.title, '') || ' ' || COALESCE(p.body, '')
            FROM raw.posts p
            JOIN raw.post_sentiment s USING (post_id)
            WHERE s.theme IS NULL
        """
        if limit:
            sql += f" LIMIT {int(limit)}"
        rows = con.execute(sql).fetchall()

        if not rows:
            log.info("No untagged posts.")
            return 0

        updates = [(_theme_for(text), pid) for pid, text in rows]
        con.executemany(
            "UPDATE raw.post_sentiment SET theme = ? WHERE post_id = ?",
            updates,
        )
        log.info("Tagged %d posts with themes.", len(updates))
        return len(updates)
    finally:
        con.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    tag(limit=args.limit)


if __name__ == "__main__":
    main()
