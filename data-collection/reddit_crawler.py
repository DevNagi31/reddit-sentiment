import datetime
import logging
import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extensions import register_adapter
from psycopg2.extras import Json
from pyfaktory import Client, Job, Producer

from reddit_client import RedditClient

register_adapter(dict, Json)
load_dotenv()

logger = logging.getLogger("reddit_crawler")
logger.propagate = False
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
numeric_level = getattr(logging, log_level_str, logging.INFO)
logger.setLevel(numeric_level)
sh = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sh.setFormatter(formatter)
logger.addHandler(sh)

DATABASE_URL = os.environ.get("DATABASE_URL")
FACTORY_SERVER_URL = os.environ.get("FACTORY_SERVER_URL")
REDDIT_USER_AGENT = os.environ.get("REDDIT_USER_AGENT")


def crawl_subreddit_posts(subreddit, after=None):
    client = RedditClient(REDDIT_USER_AGENT)
    logger.info(f"Crawling r/{subreddit}")

    data = client.get_subreddit_new(subreddit, limit=100, after=after)

    if not data or "data" not in data:
        logger.warning(f"No data for r/{subreddit}")
        schedule_next_subreddit_crawl(subreddit, after)
        return

    posts = data["data"]["children"]
    after_cursor = data["data"].get("after")

    conn = psycopg2.connect(dsn=DATABASE_URL)
    cur = conn.cursor()

    for post_wrapper in posts:
        post = post_wrapper["data"]
        post_id = post["id"]
        created_at = datetime.datetime.fromtimestamp(post["created_utc"])

        q = """INSERT INTO posts (board_name, thread_number, post_number, created_at, data)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT DO NOTHING"""
        cur.execute(q, (f"reddit_{subreddit}", post_id, post_id, created_at, post))

        with Client(faktory_url=FACTORY_SERVER_URL, role="producer") as faktory_client:
            producer = Producer(client=faktory_client)
            job = Job(
                jobtype="crawl_reddit_comments",
                args=(subreddit, post_id),
                queue="crawl-reddit-comments",
            )
            producer.push(job)

    conn.commit()
    cur.close()
    conn.close()

    logger.info(f"Crawled {len(posts)} posts from r/{subreddit}")
    schedule_next_subreddit_crawl(subreddit, after_cursor)


def schedule_next_subreddit_crawl(subreddit, after):
    with Client(faktory_url=FACTORY_SERVER_URL, role="producer") as faktory_client:
        producer = Producer(client=faktory_client)
        run_at = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
        run_at = run_at.isoformat()[:-7] + "Z"

        job = Job(
            jobtype="crawl_subreddit",
            args=(subreddit, after),
            queue="crawl-subreddit",
            at=str(run_at),
        )
        producer.push(job)
        logger.info(f"Scheduled next crawl for r/{subreddit} at {run_at}")


def crawl_reddit_comments(subreddit, post_id):
    client = RedditClient(REDDIT_USER_AGENT)
    logger.info(f"Crawling comments for r/{subreddit}/{post_id}")

    data = client.get_post_comments(subreddit, post_id)

    if not data or len(data) < 2:
        logger.warning(f"No comments for {post_id}")
        return

    comments_listing = data[1]["data"]["children"]

    conn = psycopg2.connect(dsn=DATABASE_URL)
    cur = conn.cursor()

    def process_comment(comment_data):
        if comment_data["kind"] == "more":
            return

        comment = comment_data["data"]
        comment_id = comment["id"]
        created_at = datetime.datetime.fromtimestamp(comment["created_utc"])

        q = """INSERT INTO posts (board_name, thread_number, post_number, created_at, data)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT DO NOTHING"""
        cur.execute(q, (f"reddit_{subreddit}", post_id, comment_id, created_at, comment))

        if "replies" in comment and comment["replies"]:
            if isinstance(comment["replies"], dict):
                for reply in comment["replies"]["data"]["children"]:
                    process_comment(reply)

    for comment_wrapper in comments_listing:
        process_comment(comment_wrapper)

    conn.commit()
    cur.close()
    conn.close()

    logger.info(f"Finished comments for r/{subreddit}/{post_id}")
