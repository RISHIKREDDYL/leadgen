# LeadGen Pipeline with Airflow and Docker

This project implements a scalable web crawling and document parsing pipeline using **Scrapy** and **Apache Airflow**, all containerized with **Docker**.

It is designed to be deployed on a Linux environment (e.g., Ubuntu on DigitalOcean) and uses **Tesseract OCR** for processing PDFs and images.

## Architecture

*   **Scrapy**: Crawls specific domains (e.g., `mits.ac.in`) to find PDF, DOCX, and XLSX files.
*   **Parsing Logic**: Extracts text from downloaded files, performs OCR on scanned PDFs, and sorts files based on the count of mobile numbers found.
*   **Airflow**: Orchestrates the workflow.
    *   **Scheduler/Webserver/Worker**: Runs the DAGs.
    *   **PostgreSQL**: Metadata database for Airflow.
    *   **Redis**: Message broker for CeleryExecutor (allows scaling workers).

## Prerequisites

*   [Docker](https://docs.docker.com/get-docker/) installed.
*   [Docker Compose](https://docs.docker.com/compose/install/) installed.

## Project Structure

```
.
├── dags/                   # Airflow DAGs
│   └── leadgen_dag.py      # Main pipeline definition
├── leadgen/                # Scrapy project and parsing logic
│   ├── leadgen/
│   │   ├── spiders/        # Scrapy spiders
│   │   ├── parsing.py      # Text extraction and sorting logic
│   │   └── config.py       # Configuration settings
│   └── scrapy.cfg
├── files/                  # Mounted volume for data storage
│   └── mits.ac.in/         # Downloaded and sorted files
├── Dockerfile              # Custom Airflow image with Tesseract
├── docker-compose.yml      # Service orchestration
└── requirements.txt        # Python dependencies
```

## Quick Start

### 1. Build the Docker Image

The custom image installs system dependencies for OCR (Tesseract, Poppler).

```bash
docker-compose build
```

### 2. Initialize Airflow

This step initializes the database and creates the default `airflow` user.

```bash
docker-compose up airflow-init
```

### 3. Start the Services

Run the full stack in the background.

```bash
docker-compose up -d
```

### 4. Access the Interface

*   Open your browser and go to: `http://localhost:8080`
*   **Username**: `airflow`
*   **Password**: `airflow`

## Usage

1.  In the Airflow UI, locate the **`leadgen_weekly`** DAG.
2.  Toggle the switch to **Unpause** the DAG.
3.  It is scheduled to run weekly (`@weekly`). You can also manually trigger it by clicking the "Play" button.

### Pipeline Steps
1.  **crawl_task**: Runs the Scrapy spider (`test_spider`) to download files to `files/mits.ac.in/downloaded`.
2.  **parse_task**: Runs the `process_files` logic to OCR and sort the files into `files/mits.ac.in/sorted`.

## Configuration

The following environment variables are set in `docker-compose.yml` and can be adjusted as needed:

*   `DOWNLOAD_FOLDER`: Path where Scrapy saves files (Default: `/opt/airflow/files/mits.ac.in/downloaded`)
*   `OUTPUT_FOLDER`: Path where sorted files are moved (Default: `/opt/airflow/files/mits.ac.in/sorted`)

## Troubleshooting

*   **Logs**: Check logs for specific services:
    ```bash
    docker-compose logs -f airflow-worker
    ```
*   **OCR Issues**: If Tesseract fails, ensure the `tessdata` is correctly installed in the image (handled by the Dockerfile).
*   **Permissions**: If you encounter permission errors with the `files/` directory, ensure the user running Docker has write access, or adjust the `AIRFLOW_UID` in `.env` (default is 50000).
