from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago
import os

# Configuration
# This assumes the DAG is running in an environment where the 'leadgen' code is available
# and dependencies are installed.

# Path to the root of the project where 'leadgen' package is located
# Adjust this based on where you clone the repo in your Airflow environment.
# For example, if you clone to /opt/airflow/dags/repo, this might be /opt/airflow/dags/repo/leadgen
PROJECT_ROOT = os.environ.get("LEADGEN_PROJECT_ROOT", "/opt/airflow/dags/repo/leadgen")

# Path to the domains file
DOMAINS_FILE = os.path.join(PROJECT_ROOT, "leadgen", "domains", "domainsAP.txt")

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'start_date': days_ago(1),
    'retries': 1,
}

# Define the DAG
with DAG(
    dag_id='leadgen_pipeline',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    max_active_runs=1, # Run only one DAG instance at a time to avoid overwhelming the system
    tags=['leadgen'],
) as dag:

    # 1. Read domains
    # Note: Reading files at top-level DAG code is generally discouraged if the file is huge
    # or on a slow network drive, but for a text file of domains, it's acceptable.
    domains = []
    if os.path.exists(DOMAINS_FILE):
        with open(DOMAINS_FILE, 'r') as f:
            domains = [line.strip() for line in f if line.strip()]
    else:
        print(f"Warning: Domains file not found at {DOMAINS_FILE}")

    # 2. Create tasks for each domain
    for domain in domains:
        safe_domain = domain.replace(".", "_") # Clean task_id

        # Define paths for this domain
        # We use absolute paths to ensure commands work regardless of CWD
        # Using /tmp or a mounted volume for files is recommended
        base_files_dir = os.environ.get("LEADGEN_FILES_DIR", "/tmp/leadgen_files")
        download_folder = os.path.join(base_files_dir, domain, "downloaded")
        sorted_folder = os.path.join(base_files_dir, domain, "sorted")

        # Task 1: Spider
        # Runs 'scrapy crawl test_spider -a domain=... -a download_folder=...'
        # We assume 'scrapy' is in the PATH or we use full path to python executable
        spider_cmd = (
            f"cd {PROJECT_ROOT} && "
            f"scrapy crawl test_spider "
            f"-a domain={domain} "
            f"-a download_folder={download_folder}"
        )

        spider_task = BashOperator(
            task_id=f'crawl_{safe_domain}',
            bash_command=spider_cmd,
            # Pool: We can allow many spiders to run in parallel as they are I/O bound
            pool='default_pool',
        )

        # Task 2: Parser
        # Runs 'python3 leadgen/parsing.py --domain ... --input_folder ...'
        parser_cmd = (
            f"python3 {os.path.join(PROJECT_ROOT, 'leadgen', 'parsing.py')} "
            f"--domain {domain} "
            f"--input_folder {download_folder} "
            f"--output_folder {sorted_folder}"
        )

        parser_task = BashOperator(
            task_id=f'parse_{safe_domain}',
            bash_command=parser_cmd,
            # Pool: LIMIT THIS! OCR is CPU heavy.
            # You should create a pool named 'ocr_pool' in Airflow UI with slots = 2 or 4 (depending on CPU cores)
            pool='ocr_pool',
        )

        # Dependency: Spider -> Parser
        spider_task >> parser_task
