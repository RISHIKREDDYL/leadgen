import os
import scrapy
from urllib.parse import urlparse

class PdfSpider(scrapy.Spider):
    name = "test_spider"

    def __init__(self, domain=None, download_folder=None, *args, **kwargs):
        super(PdfSpider, self).__init__(*args, **kwargs)
        if not domain:
            raise ValueError("Argument 'domain' is required.")
        if not download_folder:
            # Fallback for local testing if not provided, but ideally should be passed
            download_folder = os.path.join('files', domain, 'downloaded')

        self.domain = domain
        self.download_folder = download_folder
        self.allowed_domains = [domain]
        self.start_urls = [
            f"https://{domain}/",
            f"https://{domain}/robots.txt",
            f"https://{domain}/wp-sitemap.xml",
            f"https://{domain}/sitemaps.xml",
            f"https://{domain}/sitemap.xml",
        ]

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(PdfSpider, cls).from_crawler(crawler, *args, **kwargs)
        # Update settings dynamically if needed, though LOG_FILE is usually set at startup
        # To handle dynamic log files per domain, it's often better to control logging
        # from the runner (Scrapy CLI) or via custom settings here if the crawler isn't running yet.
        # However, custom_settings class attribute is read before __init__.
        # So we leave standard logging configuration to the caller (Airflow).
        return spider

    custom_settings = {
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'DEBUG',
        # LOG_FILE is removed here to allow the runner (Airflow/Bash) to redirect stdout/stderr
        # or specify a log file via CLI argument -s LOG_FILE=...
    }

    def parse(self, response):
        self.logger.info(f"Crawling page: {response.url}")
        links = response.css("a::attr(href)").getall()
        self.logger.debug(f"Found {len(links)} links on this page")

        for href in links:
            url = response.urljoin(href)
            parsed = urlparse(url)
            # skip out-of-domain
            if self.domain not in parsed.netloc:
                self.logger.debug(f"Skipping external URL: {url}")
                continue

            # normalize & strip any query strings
            lower = url.lower().split('?', 1)[0]

            if lower.endswith('.pdf'):
                yield scrapy.Request(url, callback=self.save_file, meta={'type': 'pdf'})
            elif lower.endswith('.docx'):
                yield scrapy.Request(url, callback=self.save_file, meta={'type': 'docx'})
            elif lower.endswith('.xlsx'):
                yield scrapy.Request(url, callback=self.save_file, meta={'type': 'xlsx'})
            else:
                # follow on-site HTML pages
                yield scrapy.Request(url, callback=self.parse)

    def save_file(self, response):
        file_type = response.meta['type']
        # map each type to its download subfolder
        subfolders = {
            'pdf':    'pdfs',
            'docx':   'docx',
            'xlsx':   'spreadsheets',
        }
        sub = subfolders[file_type]
        # Ensure cross-platform path handling
        folder_path = os.path.join(self.download_folder, sub)
        os.makedirs(folder_path, exist_ok=True)

        # use only the filename portion (strip params again)
        filename = response.url.split('/')[-1].split('?', 1)[0]
        # Clean filename to avoid OS issues (e.g. %20 or illegal chars) is a good practice,
        # but sticking to minimal changes for now.
        path = os.path.join(folder_path, filename)

        self.logger.info(f"Saving {file_type.upper()} → {path}")
        with open(path, 'wb') as f:
            f.write(response.body)
