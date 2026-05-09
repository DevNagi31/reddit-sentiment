-- Run after `docker compose up -d`:
--   docker exec -i reddit-sentiment-db psql -U postgres -d reddit_crawler < init_db.sql
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
CREATE INDEX IF NOT EXISTS idx_thread       ON posts(thread_number);
CREATE INDEX IF NOT EXISTS idx_created_at   ON posts(created_at DESC);
