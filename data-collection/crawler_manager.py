import logging
import os

from dotenv import load_dotenv
from pyfaktory import Client, Consumer

from reddit_crawler import crawl_reddit_comments, crawl_subreddit_posts

load_dotenv()

logger = logging.getLogger("crawler_manager")
logger.propagate = False
logger.setLevel(logging.INFO)
sh = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sh.setFormatter(formatter)
logger.addHandler(sh)

FACTORY_SERVER_URL = os.environ.get("FACTORY_SERVER_URL")

if __name__ == "__main__":
    logger.info("Starting crawler workers...")

    with Client(faktory_url=FACTORY_SERVER_URL, role="consumer") as client:
        consumer = Consumer(
            client=client,
            queues=["default", "crawl-subreddit", "crawl-reddit-comments"],
            concurrency=5,
        )

        consumer.register("crawl_subreddit", crawl_subreddit_posts)
        consumer.register("crawl_reddit_comments", crawl_reddit_comments)

        logger.info("Workers ready. Waiting for jobs...")
        consumer.run()
