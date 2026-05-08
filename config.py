"""Central configuration. Loads .env if present."""
from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

DUCKDB_PATH = Path(os.getenv("DUCKDB_PATH", DATA_DIR / "reddit_sentiment.duckdb"))

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "reddit-sentiment/0.1")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


def has_reddit_credentials() -> bool:
    return bool(REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET)


def has_groq_credentials() -> bool:
    return bool(GROQ_API_KEY)


# Companies tracked by the pipeline. The scraper resolves posts to a company
# when any of these aliases appears in the title or body.
COMPANIES = [
    {"company_id": 1, "name": "Tesla",  "ticker": "TSLA", "sector": "Automotive",
     "aliases": ["tesla", "elon musk", "model y", "model 3", "cybertruck"]},
    {"company_id": 2, "name": "Apple",  "ticker": "AAPL", "sector": "Technology",
     "aliases": ["apple", "iphone", "macbook", "ios", "tim cook"]},
    {"company_id": 3, "name": "Google", "ticker": "GOOGL", "sector": "Technology",
     "aliases": ["google", "alphabet", "android", "pixel", "gemini"]},
    {"company_id": 4, "name": "Amazon", "ticker": "AMZN", "sector": "Retail",
     "aliases": ["amazon", "aws", "prime", "bezos"]},
    {"company_id": 5, "name": "Microsoft", "ticker": "MSFT", "sector": "Technology",
     "aliases": ["microsoft", "windows", "azure", "xbox", "satya nadella"]},
]

# Subreddits the scraper pulls from.
SUBREDDITS = [
    {"name": "stocks",      "category": "finance"},
    {"name": "investing",   "category": "finance"},
    {"name": "technology",  "category": "tech"},
    {"name": "cars",        "category": "auto"},
    {"name": "RealTesla",   "category": "auto"},
    {"name": "apple",       "category": "tech"},
    {"name": "Android",     "category": "tech"},
]

# Keyword themes — coarse buckets for theme tagging without needing BERTopic
# at first. The dbt mart can later swap in a richer source.
THEMES = {
    "Recall / Safety":   ["recall", "safety", "crash", "defect", "investigation", "nhtsa"],
    "Pricing":           ["price", "discount", "expensive", "cheap", "cost", "deal"],
    "Product Launch":    ["launch", "release", "announce", "unveil", "new model", "leak"],
    "Earnings":          ["earnings", "revenue", "profit", "guidance", "quarter", "eps"],
    "Customer Service":  ["support", "service", "warranty", "repair", "complaint"],
    "Software / AI":     ["ai", "software", "update", "feature", "bug", "ota"],
    "Charging / Energy": ["charging", "supercharger", "battery", "range"],
    "Leadership":        ["ceo", "musk", "tim cook", "satya", "bezos", "executive"],
}
