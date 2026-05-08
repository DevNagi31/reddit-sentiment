import logging
import os
import time

import requests

logger = logging.getLogger("reddit_client")
logger.propagate = False
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
numeric_level = getattr(logging, log_level_str, logging.INFO)
logger.setLevel(numeric_level)
sh = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
sh.setFormatter(formatter)
logger.addHandler(sh)


class RedditClient:
    def __init__(self, user_agent):
        self.user_agent = user_agent
        self.headers = {"User-Agent": user_agent}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def get_subreddit_new(self, subreddit, limit=100, after=None):
        url = f"https://www.reddit.com/r/{subreddit}/new.json"
        params = {"limit": limit}
        if after:
            params["after"] = after

        try:
            response = self.session.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            time.sleep(2)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching r/{subreddit}: {e}")
            return None

    def get_post_comments(self, subreddit, post_id):
        url = f"https://www.reddit.com/r/{subreddit}/comments/{post_id}.json"

        try:
            response = self.session.get(url, headers=self.headers)
            response.raise_for_status()
            time.sleep(2)
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching comments for {post_id}: {e}")
            return None
