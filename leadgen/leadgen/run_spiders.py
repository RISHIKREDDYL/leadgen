import sys
import subprocess
from pathlib import Path

DOMAINS_FILE = Path("domains/domainsAP.txt")
CONFIG_FILE   = Path("config.py")
SPIDER_NAME   = "test_spider"
POST_SCRIPT   = Path("parsing.py")

template = """domain = '{domain}'
download_folder = fr"files\{domain}\downloaded"
"""
# Read and clean domains
domains = [d.strip() for d in DOMAINS_FILE.read_text().splitlines() if d.strip()]

for domain in domains:
    print(f"\n▶ Running for: {domain}\n")

    # 1. Rewrite config.py
    CONFIG_FILE.write_text(template.format(domain=domain))

    # 2. Launch Scrapy crawl via the same Python
    subprocess.run(
        [sys.executable, "-m", "scrapy", "crawl", SPIDER_NAME],
        check=True
    )

    # 3. Post‐process with pdftext.py via the same Python
    subprocess.run(
        [sys.executable, str(POST_SCRIPT)],
        check=True
    )
