# Run notes

## Quickstart (no API keys, sample data)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

make all           # seed sample posts -> NLP -> dbt run+test
make dashboard     # streamlit dashboard at http://localhost:8501
make api           # FastAPI at http://localhost:8000/docs
```

## Real Reddit data

1. Create an app at https://www.reddit.com/prefs/apps (type: "script")
2. Copy `.env.example` to `.env` and fill in `REDDIT_CLIENT_ID` /
   `REDDIT_CLIENT_SECRET` / `REDDIT_USER_AGENT`
3. `make scrape && make nlp && make dbt`

## NLP backends

- `python -m nlp.sentiment` — auto-detects HuggingFace; falls back to lexicon
- `python -m nlp.sentiment --backend lexicon` — fast, no model download
- `python -m nlp.sentiment --backend transformer` — force HuggingFace

The first transformer run downloads ~500MB.

## AI narrative summary (Groq)

Set `GROQ_API_KEY` in `.env` (free tier at https://console.groq.com).
Without a key, the dashboard renders a deterministic template summary.

## Airflow

```bash
cd airflow && docker compose up -d
# UI at http://localhost:8080  (admin / admin)
```

DAGs: `scrape_reddit` → `run_nlp` → `transform_dbt`.

## Smoke test

```bash
.venv/bin/python tests/test_smoke.py
```

Exercises lexicon scoring, theme tagging, and the full
ingest → NLP → DuckDB write path against a throwaway DB.
