"""Reddit HTTP client over public `.json` endpoints.

Mirrors the pattern from the chess-toxicity crawler in data-collection/ —
no OAuth, no PRAW, just `reddit.com/r/{sub}/new.json` with a User-Agent
header and a 2s sleep between requests.

Returns plain dicts matching the raw.posts / raw.comments schema in
warehouse/db.py.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Iterable

import requests

from config import REDDIT_USER_AGENT

log = logging.getLogger(__name__)


class RedditClient:
    def __init__(self, user_agent: str = REDDIT_USER_AGENT):
        self.headers = {"User-Agent": user_agent}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _get(self, url: str, params: dict | None = None) -> dict | list | None:
        try:
            r = self.session.get(url, params=params, timeout=15)
            r.raise_for_status()
            time.sleep(2)         # respect Reddit's unauth rate limit (~60/min)
            return r.json()
        except requests.exceptions.RequestException as e:
            log.error("HTTP error for %s: %s", url, e)
            return None

    def get_subreddit_new(self, subreddit: str, limit: int = 100, after: str | None = None):
        url = f"https://www.reddit.com/r/{subreddit}/new.json"
        params = {"limit": limit}
        if after:
            params["after"] = after
        return self._get(url, params=params)

    def get_post_comments(self, subreddit: str, post_id: str):
        url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"
        return self._get(url)


def fetch_subreddit(name: str, limit: int = 100,
                    pull_comments: bool = True,
                    comments_per_post: int = 10) -> tuple[list[dict], list[dict]]:
    """Pull recent posts and (optionally) top-level comments from a subreddit."""
    client = RedditClient()
    posts: list[dict] = []
    comments: list[dict] = []

    data = client.get_subreddit_new(name, limit=limit)
    if not data or "data" not in data:
        log.warning("No data returned for r/%s", name)
        return posts, comments

    for child in data["data"]["children"]:
        p = child["data"]
        posts.append({
            "post_id":      p["id"],
            "subreddit":    name,
            "title":        p.get("title") or "",
            "body":         p.get("selftext") or "",
            "author":       p.get("author") or "[deleted]",
            "upvotes":      int(p.get("score") or 0),
            "num_comments": int(p.get("num_comments") or 0),
            "created_utc":  datetime.fromtimestamp(p["created_utc"], tz=timezone.utc),
            "permalink":    f"https://reddit.com{p.get('permalink', '')}",
        })

        if not pull_comments:
            continue

        cdata = client.get_post_comments(name, p["id"])
        if not cdata or len(cdata) < 2:
            continue
        for cwrap in cdata[1]["data"]["children"][:comments_per_post]:
            if cwrap.get("kind") == "more":
                continue
            c = cwrap["data"]
            comments.append({
                "comment_id":  c["id"],
                "post_id":     p["id"],
                "subreddit":   name,
                "body":        c.get("body") or "",
                "author":      c.get("author") or "[deleted]",
                "upvotes":     int(c.get("score") or 0),
                "created_utc": datetime.fromtimestamp(c["created_utc"], tz=timezone.utc),
            })

    return posts, comments


def fetch_all(subreddits: Iterable[str], limit: int = 100,
              pull_comments: bool = True) -> tuple[list[dict], list[dict]]:
    all_posts: list[dict] = []
    all_comments: list[dict] = []
    for sub in subreddits:
        log.info("Fetching r/%s", sub)
        try:
            p, c = fetch_subreddit(sub, limit=limit, pull_comments=pull_comments)
            all_posts.extend(p)
            all_comments.extend(c)
        except Exception as e:
            log.warning("Failed r/%s: %s", sub, e)
    return all_posts, all_comments
