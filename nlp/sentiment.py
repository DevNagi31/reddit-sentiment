"""Sentiment scoring.

Default backend is `cardiffnlp/twitter-roberta-base-sentiment` from
HuggingFace. A lightweight lexicon-based fallback is provided so the pipeline
runs in environments where downloading a 500MB model isn't practical (CI,
demos, this dev box).

Usage:
  python -m nlp.sentiment                # transformer if available, else lexicon
  python -m nlp.sentiment --backend lexicon
  python -m nlp.sentiment --limit 1000
"""
from __future__ import annotations

import argparse
import logging
import re
from typing import Iterable

from warehouse.db import connect, init_schema, upsert_sentiment

log = logging.getLogger(__name__)


# ---------- Lexicon fallback ----------

POSITIVE_WORDS = {
    "love", "great", "excellent", "amazing", "incredible", "fantastic",
    "best", "good", "strong", "beat", "win", "wins", "recommend",
    "perfect", "awesome", "happy", "impressed", "game changer", "value",
    "highly recommend",
}
NEGATIVE_WORDS = {
    "terrible", "awful", "bad", "worst", "hate", "broken", "disappointed",
    "avoid", "weak", "tanking", "drop", "drops", "issue", "issues",
    "concerns", "concern", "recall", "complaint", "refund", "fail",
    "failure", "scam", "ripoff",
}

_TOKEN = re.compile(r"[a-z][a-z'\- ]+")


def _lexicon_score(text: str) -> tuple[str, float]:
    t = (text or "").lower()
    pos = sum(1 for w in POSITIVE_WORDS if w in t)
    neg = sum(1 for w in NEGATIVE_WORDS if w in t)
    if pos == 0 and neg == 0:
        return "neutral", 0.0
    score = (pos - neg) / max(pos + neg, 1)
    if score >= 0.2:
        label = "positive"
    elif score <= -0.2:
        label = "negative"
    else:
        label = "neutral"
    return label, round(score, 4)


# ---------- Transformer backend ----------

_HF_MODEL = "cardiffnlp/twitter-roberta-base-sentiment"
_LABEL_MAP = {"LABEL_0": "negative", "LABEL_1": "neutral", "LABEL_2": "positive"}


def _load_transformer():
    from transformers import pipeline
    log.info("Loading HuggingFace model: %s", _HF_MODEL)
    return pipeline("sentiment-analysis", model=_HF_MODEL, top_k=None, truncation=True)


def _transformer_scores(pipe, texts: list[str]) -> list[tuple[str, float]]:
    out = pipe(texts, batch_size=16)
    results: list[tuple[str, float]] = []
    for entry in out:
        # entry is a list of {label, score} for top_k=None
        scored = {_LABEL_MAP[d["label"]]: d["score"] for d in entry}
        label = max(scored, key=scored.get)
        # signed score in [-1, 1]: positive prob minus negative prob
        score = scored.get("positive", 0) - scored.get("negative", 0)
        results.append((label, round(score, 4)))
    return results


# ---------- Driver ----------

def _iter_unscored(con, limit: int | None) -> Iterable[tuple[str, str]]:
    sql = """
        SELECT p.post_id, COALESCE(p.title, '') || ' ' || COALESCE(p.body, '')
        FROM raw.posts p
        LEFT JOIN raw.post_sentiment s USING (post_id)
        WHERE s.post_id IS NULL
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    return con.execute(sql).fetchall()


def score(backend: str = "auto", limit: int | None = None) -> int:
    init_schema()
    con = connect()
    try:
        rows = list(_iter_unscored(con, limit))
    finally:
        con.close()

    if not rows:
        log.info("Nothing to score.")
        return 0

    log.info("Scoring %d posts (backend=%s)", len(rows), backend)

    pipe = None
    use_transformer = backend == "transformer"
    if backend == "auto":
        try:
            pipe = _load_transformer()
            use_transformer = True
        except Exception as e:
            log.warning("Transformer unavailable (%s); falling back to lexicon.", e)
            use_transformer = False
    elif use_transformer:
        pipe = _load_transformer()

    texts = [text for _, text in rows]
    if use_transformer:
        scored = _transformer_scores(pipe, texts)
        model_version = _HF_MODEL
    else:
        scored = [_lexicon_score(t) for t in texts]
        model_version = "lexicon-v1"

    out = [
        {
            "post_id":       post_id,
            "sentiment":     label,
            "score":         s,
            "theme":         None,        # populated by themes.py
            "model_version": model_version,
        }
        for (post_id, _), (label, s) in zip(rows, scored)
    ]
    n = upsert_sentiment(out)
    log.info("Wrote sentiment for %d posts.", n)
    return n


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--backend", choices=["auto", "transformer", "lexicon"],
                        default="auto")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    score(backend=args.backend, limit=args.limit)


if __name__ == "__main__":
    main()
