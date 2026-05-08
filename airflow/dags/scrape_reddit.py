"""Daily scrape DAG. Bash-style — assumes the repo is on PYTHONPATH inside
the Airflow worker (mount it via docker-compose).
"""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "reddit-sentiment",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="scrape_reddit",
    description="Pull hot posts from tracked subreddits.",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args=default_args,
    tags=["reddit", "ingest"],
) as dag:
    scrape = BashOperator(
        task_id="scrape",
        bash_command="cd /opt/project && python -m scraper.collectors --limit 100",
    )
