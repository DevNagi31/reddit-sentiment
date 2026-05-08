"""Reddit API client wrapper around PRAW.

Returns plain dicts that match the raw.posts / raw.comments schema in
warehouse/db.py.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable

from config import (
    REDDIT_CLIENT_ID,
    REDDIT_CLIENT_SECRET,
    REDDIT_USER_AGENT,
    has_reddit_credentials,
)

log = logging.getLogger(__name__)


def _client():
    import praw
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )


def fetch_subreddit(name: str, limit: int = 100) -> tuple[list[dict], list[dict]]:
    """Fetch hot posts + top-level comments from a subreddit."""
    if not has_reddit_credentials():
        raise RuntimeError(
            "Reddit credentials missing. Set REDDIT_CLIENT_ID and "
            "REDDIT_CLIENT_SECRET in .env, or run scraper/sample_data.py "
            "to load synthetic data."
        )

    reddit = _client()
    posts: list[dict] = []
    comments: list[dict] = []

    for submission in reddit.subreddit(name).hot(limit=limit):
        posts.append({
            "post_id":      submission.id,
            "subreddit":    name,
            "title":        submission.title,
            "body":         submission.selftext or "",
            "author":       str(submission.author) if submission.author else "[deleted]",
            "upvotes":      int(submission.score),
            "num_comments": int(submission.num_comments),
            "created_utc":  datetime.fromtimestamp(submission.created_utc, tz=timezone.utc),
            "permalink":    f"https://reddit.com{submission.permalink}",
        })
        submission.comments.replace_more(limit=0)
        for c in submission.comments.list()[:25]:
            comments.append({
                "comment_id":  c.id,
                "post_id":     submission.id,
                "subreddit":   name,
                "body":        c.body,
                "author":      str(c.author) if c.author else "[deleted]",
                "upvotes":     int(c.score),
                "created_utc": datetime.fromtimestamp(c.created_utc, tz=timezone.utc),
            })

    return posts, comments


def fetch_all(subreddits: Iterable[str], limit: int = 100) -> tuple[list[dict], list[dict]]:
    all_posts: list[dict] = []
    all_comments: list[dict] = []
    for sub in subreddits:
        log.info("Fetching r/%s", sub)
        try:
            p, c = fetch_subreddit(sub, limit=limit)
            all_posts.extend(p)
            all_comments.extend(c)
        except Exception as e:
            log.warning("Failed to fetch r/%s: %s", sub, e)
    return all_posts, all_comments
