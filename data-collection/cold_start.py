import os
import sys

from dotenv import load_dotenv
from pyfaktory import Client, Job, Producer

load_dotenv()

FACTORY_SERVER_URL = os.environ.get("FACTORY_SERVER_URL")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cold_start.py <subreddit> [<subreddit> ...]")
        print("Example: python cold_start.py stocks technology RealTesla")
        sys.exit(1)

    subreddits = sys.argv[1:]

    with Client(faktory_url=FACTORY_SERVER_URL, role="producer") as client:
        producer = Producer(client=client)
        for sub in subreddits:
            job = Job(
                jobtype="crawl_subreddit",
                args=(sub, None),
                queue="crawl-subreddit",
            )
            producer.push(job)
            print(f"Queued crawl_subreddit for r/{sub}")

    print(f"\n{len(subreddits)} job(s) queued.")
