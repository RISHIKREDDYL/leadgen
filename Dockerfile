FROM apache/airflow:2.10.2-python3.11

USER root

# Install system dependencies required for tesserocr and other libs
RUN apt-get update && apt-get install -y \
    build-essential \
    tesseract-ocr \
    libtesseract-dev \
    libleptonica-dev \
    poppler-utils \
    libpoppler-cpp-dev \
    pkg-config \
    gcc \
    g++ \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copy requirements and install
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Copy project code
COPY leadgen /opt/airflow/leadgen
