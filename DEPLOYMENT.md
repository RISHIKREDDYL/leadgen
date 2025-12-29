# Deployment Guide: Leadgen Airflow Pipeline

This guide outlines how to deploy the Leadgen project with Airflow on a DigitalOcean Droplet (Ubuntu 20.04/22.04).

## 1. Droplet Setup

1.  **Create Droplet**:
    *   **OS**: Ubuntu 22.04 LTS (x64)
    *   **Plan**: Basic (or higher).
    *   **CPU/RAM**: Recommended at least **4GB RAM / 2 vCPUs** because OCR (Tesseract) is memory and CPU intensive.

2.  **SSH into Droplet**:
    ```bash
    ssh root@<your_droplet_ip>
    ```

## 2. Install System Dependencies

Update packages and install Python, pip, and Tesseract OCR.

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv \
    tesseract-ocr libtesseract-dev \
    libpoppler-cpp-dev pkg-config # needed for some pdf libs
```

## 3. Project Setup

1.  **Clone the Repository**:
    ```bash
    mkdir -p /opt/airflow/dags/repo
    cd /opt/airflow/dags/repo
    git clone <your-repo-url> .
    ```

2.  **Set Environment Variables**:
    You need to tell Airflow where your project lives. Add this to `.bashrc` or your Airflow service config:
    ```bash
    export LEADGEN_PROJECT_ROOT="/opt/airflow/dags/repo"
    export LEADGEN_FILES_DIR="/mnt/volume_nyc1_01/leadgen_files" # Recommended: Attach a Block Storage volume for large data
    ```
    *Note: If you don't have block storage, `/tmp/leadgen_files` or `/home/airflow/leadgen_files` works too.*

## 4. Install Airflow & Python Requirements

1.  **Create Virtual Environment** (Recommended):
    ```bash
    python3 -m venv airflow_env
    source airflow_env/bin/activate
    ```

2.  **Install Airflow**:
    ```bash
    # Constraint file for reproducible installs (change 2.7.2 and 3.10 to match your versions)
    CONSTRAINT_URL="https://raw.githubusercontent.com/apache/airflow/constraints-2.7.2/constraints-3.10.txt"
    pip install "apache-airflow==2.7.2" --constraint "${CONSTRAINT_URL}"
    ```

3.  **Install Project Requirements**:
    ```bash
    pip install -r requirements-airflow.txt
    ```

## 5. Initialize Airflow

```bash
# Initialize DB (SQLite by default - okay for small scale, Postgres recommended for prod)
airflow db init

# Create User
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com
```

## 6. Run Airflow

For a simple setup, run scheduler and webserver in the background:

```bash
airflow webserver --port 8080 -D
airflow scheduler -D
```

Visit `http://<your_droplet_ip>:8080` to see the UI.

## 7. Configuration for Scaling (Crucial!)

**You must configure Pools to prevent system freezing.**

1.  Go to Airflow UI -> **Admin** -> **Pools**.
2.  Create a new pool:
    *   **Pool**: `ocr_pool`
    *   **Slots**: `2` (Start low! If you have 2 vCPUs, set to 1 or 2. If 4 vCPUs, maybe 3).
    *   **Description**: Limit concurrent OCR parsing tasks.
3.  Ensure `default_pool` has enough slots (e.g., 128) for the spiders, as they are lightweight.

## Scaling & Maintenance

### Bottlenecks
1.  **CPU (OCR)**: The `parsing.py` script uses Tesseract, which uses 100% of a CPU core per process.
    *   *Solution*: The `ocr_pool` limits how many parsers run at once. Do not increase the slots beyond your CPU core count.
2.  **Disk Space**: PDF downloads and uncompressed images can fill disk fast.
    *   *Solution*: Use DigitalOcean Block Storage (Volumes). Mount it at `/mnt/volume...` and set `LEADGEN_FILES_DIR` to point there.
    *   *Cleanup*: Add a maintenance DAG to delete old files in `LEADGEN_FILES_DIR` older than X days.

### Path Compatibility
The code has been refactored to use `os.path.join`, so it will work seamlessly on Ubuntu (forward slashes) even if you developed on Windows.
