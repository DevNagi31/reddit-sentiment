"""Tiny smoke tests that exercise the lexicon path end-to-end without needing
HuggingFace, Reddit creds, or dbt. Run with: python -m tests.test_smoke
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# Use a throwaway DB so we don't clobber the dev one. DuckDB needs to create
# the file itself, so we just hand it a path inside a fresh temp dir.
_tmp_dir = tempfile.mkdtemp(prefix="reddit_sentiment_smoke_")
os.environ["DUCKDB_PATH"] = str(Path(_tmp_dir) / "smoke.duckdb")

# Make the project importable when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> None:
    from nlp.sentiment import _lexicon_score, score
    from nlp.themes import _theme_for, tag
    from scraper.sample_data import generate
    from warehouse.db import connect, init_schema, upsert_posts

    # 1. lexicon scoring
    label, s = _lexicon_score("Tesla recall is terrible, avoid")
    assert label == "negative", f"expected negative, got {label}"
    assert s < 0
    print(f"[ok] lexicon negative path: {label} ({s})")

    label, s = _lexicon_score("Apple iPhone is incredible, love it")
    assert label == "positive", f"expected positive, got {label}"
    print(f"[ok] lexicon positive path: {label} ({s})")

    # 2. theme tagging
    assert _theme_for("Tesla recall investigation by NHTSA") == "Recall / Safety"
    assert _theme_for("Pixel price discount this week") == "Pricing"
    print("[ok] theme tagging")

    # 3. end-to-end ingest -> sentiment -> themes
    init_schema()
    posts, _ = generate(days=3, posts_per_day=5)
    n = upsert_posts(posts)
    assert n > 0
    print(f"[ok] inserted {n} sample posts")

    n = score(backend="lexicon")
    assert n > 0
    print(f"[ok] scored {n} posts")

    n = tag()
    print(f"[ok] tagged {n} posts with themes")

    con = connect()
    counts = con.execute("""
        SELECT sentiment, COUNT(*) FROM raw.post_sentiment GROUP BY 1 ORDER BY 1
    """).fetchall()
    con.close()
    print(f"[ok] sentiment distribution: {counts}")

    print("\nAll smoke tests passed.")


if __name__ == "__main__":
    main()
