.PHONY: install seed scrape nlp dbt dashboard api airflow-up airflow-down \
        crawler-up crawler-down crawler-status sync clean all

PYTHON ?= python

install:
	$(PYTHON) -m pip install -r requirements.txt

# Quick end-to-end run with sample data — no API keys needed.
seed:
	$(PYTHON) -m scraper.collectors --sample --days 30

scrape:
	$(PYTHON) -m scraper.collectors

nlp:
	$(PYTHON) -m nlp.sentiment
	$(PYTHON) -m nlp.themes

dbt:
	cd dbt && dbt run --profiles-dir . && dbt test --profiles-dir .

dashboard:
	streamlit run dashboard/app.py

api:
	uvicorn api.main:app --reload

airflow-up:
	cd airflow && docker compose up -d

airflow-down:
	cd airflow && docker compose down

# --- Continuous Faktory crawler (production path) ---------------------------

crawler-up:
	cd data-collection && docker compose up -d
	@echo "Waiting for Postgres..."
	@until docker exec reddit-sentiment-db pg_isready -U postgres >/dev/null 2>&1; do sleep 1; done
	@docker exec -i reddit-sentiment-db psql -U postgres -d reddit_crawler < data-collection/init_db.sql >/dev/null
	@echo ""
	@echo "Postgres + Faktory up. Faktory UI: http://localhost:7420"
	@echo "Now in two terminals:"
	@echo "  1) cd data-collection && python crawler_manager.py"
	@echo "  2) cd data-collection && python cold_start.py stocks technology RealTesla apple Android microsoft"

crawler-down:
	cd data-collection && docker compose down

crawler-status:
	cd data-collection && python check_status.py

sync:
	cd data-collection && python sync_to_duckdb.py

# Full local pipeline against sample data.
all: seed nlp dbt
	@echo ""
	@echo "Pipeline complete. Launch the dashboard with: make dashboard"

clean:
	rm -f data/reddit_sentiment.duckdb
	rm -rf dbt/target dbt/logs
