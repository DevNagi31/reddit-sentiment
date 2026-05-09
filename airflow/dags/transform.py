"""dbt transform DAG — runs models then tests."""
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    "owner": "reddit-sentiment",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="transform_dbt",
    description="Run dbt models and tests.",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args=default_args,
    tags=["reddit", "dbt"],
) as dag:
    run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/project/dbt && dbt run --profiles-dir .",
    )
    test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/project/dbt && dbt test --profiles-dir .",
    )
    run >> test
