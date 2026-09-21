"""
Weather ELT — scheduled orchestration.

Extract  : weatherstack REST API (or the bundled offline fixture)
Load     : raw, untransformed rows into dev.raw_weather_data in Postgres
Transform: dbt builds the staging model and dimensional marts

Deliberately ELT rather than ETL: the raw payload lands first and is never
mutated in place, so a transformation bug is fixed by re-running dbt against
rows that are already safely stored, not by re-fetching from a rate-limited
third-party API that may no longer return the same values.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator

# The project root is mounted into the container; make the loader importable.
sys.path.insert(0, "/opt/airflow/project")

DEFAULT_ARGS = {
    "owner": "zwestfall",
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
    "retry_exponential_backoff": True,
    "max_retry_delay": timedelta(minutes=15),
}

# Offline mode lets the whole DAG run without an API key, so the pipeline is
# demonstrable from a clean clone.
USE_MOCK = os.getenv("WEATHER_USE_MOCK", "false").lower() == "true"


def extract(**context):
    """Fetch one observation and hand it to the next task via XCom."""
    from api_request import fetch_data, mock_fetch_data

    payload = mock_fetch_data() if USE_MOCK else fetch_data()
    if not payload:
        raise ValueError("Extraction returned no payload; failing rather than loading nothing.")
    return payload


def load(**context):
    """Persist the raw observation. Idempotent table creation, explicit commit."""
    from insert_records import connect_to_db, create_table, insert_records

    payload = context["ti"].xcom_pull(task_ids="extract")
    if not payload:
        raise ValueError("No payload received from extract task.")

    conn = connect_to_db()
    try:
        create_table(conn)
        insert_records(conn, payload)
    finally:
        conn.close()


with DAG(
    dag_id="weather_elt",
    description="Extract weather observations, load raw, transform with dbt",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 1, 1),
    schedule="@hourly",
    catchup=False,
    max_active_runs=1,
    tags=["elt", "weather", "dbt"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract",
        python_callable=extract,
    )

    load_task = PythonOperator(
        task_id="load",
        python_callable=load,
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/project/dbt/weather && dbt run --profiles-dir .",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/project/dbt/weather && dbt test --profiles-dir .",
    )

    # dbt_test runs after dbt_run so a failing assertion surfaces as a failed
    # task rather than silently publishing a bad mart.
    extract_task >> load_task >> dbt_run >> dbt_test
