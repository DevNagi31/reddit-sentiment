# data-collection

Continuous Reddit crawler — same architecture as `chess-toxicity-analysis/data-collection`,
adapted to the subreddits this project tracks.

## Architecture

- **Faktory** (job queue) — jobs reschedule themselves every 10 minutes
- **PostgreSQL 17** with JSONB — raw posts/comments stored verbatim
- **Custom HTTP client** — no PRAW, just `reddit.com/r/{sub}/new.json` with a
  User-Agent header and a 2s sleep between requests
- **Two-stage**: `crawl_subreddit` enqueues a `crawl_reddit_comments` job per post
- **Docker Compose** — Postgres + Faktory containers

## Files

| File                   | Purpose                                            |
|------------------------|----------------------------------------------------|
| `reddit_client.py`     | Bare HTTP client over `reddit.com/*.json`          |
| `reddit_crawler.py`    | `crawl_subreddit_posts` + `crawl_reddit_comments`  |
| `crawler_manager.py`   | Faktory consumer; concurrency=5                    |
| `cold_start.py`        | Seed initial jobs (`python cold_start.py stocks`)  |
| `check_status.py`      | DB row counts per board                            |
| `sync_to_duckdb.py`    | Project Postgres JSONB → DuckDB raw.posts/comments |
| `docker-compose.yml`   | Postgres + Faktory services                        |

## Setup

```bash
cd data-collection
cp .env.example .env
pip install -r requirements.txt

docker compose up -d
sleep 10

# Create the posts table
docker exec reddit-sentiment-db psql -U postgres -d reddit_crawler -c "
CREATE TABLE IF NOT EXISTS posts (
    id BIGSERIAL PRIMARY KEY,
    board_name TEXT NOT NULL,
    thread_number TEXT NOT NULL,
    post_number TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    data JSONB NOT NULL,
    UNIQUE(board_name, post_number)
);
CREATE INDEX IF NOT EXISTS idx_board_created ON posts(board_name, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_thread ON posts(thread_number);
CREATE INDEX IF NOT EXISTS idx_created_at ON posts(created_at DESC);
"
```

## Run

Terminal 1 — start workers:
```bash
python crawler_manager.py
```

Terminal 2 — seed the queue:
```bash
python cold_start.py stocks investing technology cars RealTesla apple Android
```

Crawls reschedule themselves every 10 minutes. Faktory web dashboard:
http://localhost:7420 (password: `password`).

## Status check

```bash
python check_status.py
```

## Feed the rest of the pipeline

The downstream NLP / dbt / dashboard layers read from DuckDB. Sync periodically:

```bash
python sync_to_duckdb.py        # Postgres → DuckDB raw.posts + raw.comments
python -m nlp.sentiment         # score new posts
python -m nlp.themes
cd ../dbt && dbt run --profiles-dir . && dbt test --profiles-dir .
```

## Stop

```bash
# Ctrl+C in the crawler_manager.py terminal
docker compose down
```

## Ports

| Port | Service                   |
|------|---------------------------|
| 5433 | PostgreSQL                |
| 7419 | Faktory                   |
| 7420 | Faktory web UI            |

## Subreddits

Defaults to the subreddits listed in `../config.py` (`SUBREDDITS`):
`stocks`, `investing`, `technology`, `cars`, `RealTesla`, `apple`, `Android`.

Add more anytime:
```bash
python cold_start.py wallstreetbets
```
