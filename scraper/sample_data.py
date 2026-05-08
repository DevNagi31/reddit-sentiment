"""Generate deterministic sample posts/comments so the pipeline is runnable
without Reddit API credentials. Useful for demos and CI.
"""
from __future__ import annotations

import argparse
import hashlib
import random
from datetime import datetime, timedelta, timezone

from config import COMPANIES, SUBREDDITS
from warehouse.db import init_schema, upsert_comments, upsert_posts


# Title templates per "tone" — sentiment model will pick these up naturally.
TEMPLATES = {
    "positive": [
        "{co} {alias} is incredible — best release in years",
        "Just bought {alias} and I love it, fantastic value",
        "{co} earnings beat expectations, stock looks strong",
        "{alias} customer service was excellent, highly recommend",
        "The new {alias} update is a game changer",
    ],
    "negative": [
        "{co} {alias} recall is terrible, safety concerns mounting",
        "Disappointed with {alias} — quality has really dropped",
        "{co} stock tanking after weak guidance",
        "Avoid {alias} — worst purchase I've made this year",
        "{co} support is broken, took 3 weeks for a refund",
    ],
    "neutral": [
        "Anyone tried the new {alias}? Looking for opinions",
        "{co} announced changes to {alias}, thoughts?",
        "What does the {co} earnings report mean for {alias}?",
        "Comparing {alias} vs competitors, who has experience?",
        "{co} rumored to be working on a new {alias}",
    ],
}


def _gen_id(*parts) -> str:
    h = hashlib.md5("|".join(map(str, parts)).encode()).hexdigest()
    return h[:10]


def generate(days: int = 30, posts_per_day: int = 25) -> tuple[list[dict], list[dict]]:
    rng = random.Random(42)
    now = datetime.now(tz=timezone.utc)
    posts, comments = [], []

    for day_offset in range(days):
        day = now - timedelta(days=day_offset)

        # Inject a "Tesla recall" event mid-window — gives the dashboard a
        # storyline to actually narrate.
        recall_window = 5 <= day_offset <= 12
        for _ in range(posts_per_day):
            company = rng.choice(COMPANIES)
            sub = rng.choice(SUBREDDITS)
            alias = rng.choice(company["aliases"])

            if recall_window and company["name"] == "Tesla":
                tone = rng.choices(["negative", "neutral", "positive"], weights=[7, 2, 1])[0]
            else:
                tone = rng.choices(["positive", "neutral", "negative"], weights=[4, 4, 2])[0]

            title = rng.choice(TEMPLATES[tone]).format(co=company["name"], alias=alias)
            body = title + " " + rng.choice([
                "What do you all think?",
                "Curious to hear other perspectives.",
                "This has been bothering me for a while.",
                "Posting because I haven't seen this discussed yet.",
                "",
            ])
            post_id = _gen_id(sub["name"], day_offset, _, title)
            created = day - timedelta(hours=rng.randint(0, 23))

            posts.append({
                "post_id":      post_id,
                "subreddit":    sub["name"],
                "title":        title,
                "body":         body,
                "author":       f"user_{rng.randint(1000, 9999)}",
                "upvotes":      rng.randint(1, 4000),
                "num_comments": rng.randint(0, 250),
                "created_utc":  created,
                "permalink":    f"https://reddit.com/r/{sub['name']}/comments/{post_id}",
            })

            for ci in range(rng.randint(0, 4)):
                comments.append({
                    "comment_id": _gen_id(post_id, ci),
                    "post_id":    post_id,
                    "subreddit":  sub["name"],
                    "body":       rng.choice([
                        "Totally agree", "Not so sure about that",
                        "Same experience here", "Strong disagree",
                        "Source?", "This is the way",
                    ]),
                    "author":     f"user_{rng.randint(1000, 9999)}",
                    "upvotes":    rng.randint(-5, 200),
                    "created_utc": created + timedelta(minutes=rng.randint(5, 600)),
                })

    return posts, comments


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--posts-per-day", type=int, default=25)
    args = parser.parse_args()

    init_schema()
    posts, comments = generate(days=args.days, posts_per_day=args.posts_per_day)
    n_posts = upsert_posts(posts)
    n_comments = upsert_comments(comments)
    print(f"Inserted {n_posts} posts, {n_comments} comments (sample data).")


if __name__ == "__main__":
    main()
