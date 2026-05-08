.PHONY: install seed scrape nlp dbt dashboard api airflow-up airflow-down clean all

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

# Full local pipeline against sample data.
all: seed nlp dbt
	@echo ""
	@echo "Pipeline complete. Launch the dashboard with: make dashboard"

clean:
	rm -f data/reddit_sentiment.duckdb
	rm -rf dbt/target dbt/logs
