import os
import scrapy
from urllib.parse import urlparse
from ..config import domain, download_folder

class PdfSpider(scrapy.Spider):
    name = "test_spider"
    domain = domain
    download_folder = download_folder
    allowed_domains = [domain]
    start_urls = [
        f"https://{domain}/",
        f"https://{domain}/robots.txt",
        f"https://{domain}/wp-sitemap.xml",
        f"https://{domain}/sitemaps.xml",
        f"https://{domain}/sitemap.xml",
    ]

    custom_settings = {
        'ROBOTSTXT_OBEY': False,    # remove or set to True in production
        'LOG_LEVEL':    'DEBUG',
        'LOG_FILE':     f'logs/{domain}.log',
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
        folder_path = os.path.join(self.download_folder, sub)
        os.makedirs(folder_path, exist_ok=True)

        # use only the filename portion (strip params again)
        filename = response.url.split('/')[-1].split('?', 1)[0]
        path = os.path.join(folder_path, filename)

        self.logger.info(f"Saving {file_type.upper()} → {path}")
        with open(path, 'wb') as f:
            f.write(response.body)