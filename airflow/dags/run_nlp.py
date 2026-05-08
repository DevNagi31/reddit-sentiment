"""NLP DAG — score sentiment, then tag themes."""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "reddit-sentiment",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="run_nlp",
    description="Run sentiment + theme tagging over un-scored posts.",
    start_date=datetime(2026, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    default_args=default_args,
    tags=["reddit", "nlp"],
) as dag:
    sentiment = BashOperator(
        task_id="sentiment",
        bash_command="cd /opt/project && python -m nlp.sentiment",
    )
    themes = BashOperator(
        task_id="themes",
        bash_command="cd /opt/project && python -m nlp.themes",
    )
    sentiment >> themes
