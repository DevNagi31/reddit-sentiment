"""CLI entrypoint for the scraping job.

No Reddit credentials needed — uses public reddit.com/*.json endpoints.

Usage:
  python -m scraper.collectors --subreddits stocks,technology --limit 100
  python -m scraper.collectors --sample --days 30          # synthetic data
  python -m scraper.collectors --no-comments               # posts only (faster)
"""
from __future__ import annotations

import argparse
import logging

from config import SUBREDDITS
from scraper import reddit_client, sample_data
from warehouse.db import init_schema, upsert_comments, upsert_posts

log = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--subreddits",
        default=",".join(s["name"] for s in SUBREDDITS),
        help="Comma-separated subreddit names.",
    )
    parser.add_argument("--limit", type=int, default=100,
                        help="Posts per subreddit.")
    parser.add_argument("--no-comments", action="store_true",
                        help="Skip per-post comment fetching (faster).")
    parser.add_argument("--sample", action="store_true",
                        help="Use synthetic sample data instead of hitting Reddit.")
    parser.add_argument("--days", type=int, default=30,
                        help="(sample mode) days of history to generate.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    init_schema()

    if args.sample:
        posts, comments = sample_data.generate(days=args.days)
    else:
        subs = [s.strip() for s in args.subreddits.split(",") if s.strip()]
        posts, comments = reddit_client.fetch_all(
            subs, limit=args.limit, pull_comments=not args.no_comments
        )

    n_posts = upsert_posts(posts)
    n_comments = upsert_comments(comments)
    log.info("Inserted %d new posts, %d new comments.", n_posts, n_comments)


if __name__ == "__main__":
    main()
