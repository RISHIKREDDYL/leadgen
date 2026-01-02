from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os

# Default args for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
}

# Define the DAG
with DAG(
    'leadgen_weekly',
    default_args=default_args,
    description='Weekly crawl and parse pipeline',
    schedule_interval='@weekly',
    start_date=days_ago(1),
    catchup=False,
) as dag:

    # Task 1: Crawl
    # We navigate to the Scrapy project root and run the spider
    crawl_task = BashOperator(
        task_id='crawl_task',
        bash_command='cd /opt/airflow/leadgen && scrapy crawl test_spider',
    )

    # Task 2: Parse
    # Define a wrapper function to import and run the parsing logic
    def run_parsing_logic():
        # Ensure the project root is in python path
        project_root = '/opt/airflow/leadgen'
        if project_root not in sys.path:
            sys.path.append(project_root)

        # Import dynamically to avoid top-level import errors during DAG parsing
        # if dependencies are missing in the webserver (though they should be present)
        from leadgen.parsing import process_files
        process_files()

    parse_task = PythonOperator(
        task_id='parse_task',
        python_callable=run_parsing_logic,
    )

    # Set dependency: Crawl -> Parse
    crawl_task >> parse_task
