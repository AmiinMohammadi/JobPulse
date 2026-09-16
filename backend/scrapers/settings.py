"""
JobVision Spider Settings

Configured for polite crawling with AutoThrottle and resumability.
"""

import os
from datetime import datetime

# Basic Scrapy settings
BOT_NAME = "jobvision_spiders"
SPIDER_MODULES = ["backend.scrapers.spiders"]
NEWSPIDER_MODULE = "backend.scrapers.spiders"

# Obey robots.txt rules (mandatory)
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests (polite crawling)
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2

# Download delay for politeness
DOWNLOAD_DELAY = 2

# Enable AutoThrottle extension
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 3
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# User agent
USER_AGENT = "JobPulse-Research-Bot (+https://github.com/your-repo/jobpulse)"

# Enable cookies
COOKIES_ENABLED = False

# Disable Telnet Console
TELNETCONSOLE_ENABLED = False

# Default request headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fa,en-US;q=0.7,en;q=0.3",
    "Connection": "keep-alive",
}

# Enable or disable spider middlewares
SPIDER_MIDDLEWARES = {
    # Disable default spider middleware to avoid async issues
    # "backend.scrapers.middlewares.JobvisionSpiderMiddleware": 543,
}

# Enable or disable downloader middlewares
DOWNLOADER_MIDDLEWARES = {
    "backend.scrapers.middlewares.JobvisionDownloaderMiddleware": 543,
    "backend.scrapers.middlewares.SoftBanDetectionMiddleware": 600,
}

# Enable or disable extensions
EXTENSIONS = {
    "scrapy.extensions.telnet.TelnetConsole": None,
}

# Configure item pipelines
ITEM_PIPELINES = {
    "backend.scrapers.pipelines.JobvisionPipeline": 300,
}

# Enable and configure the HTTP cache
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400  # 24 hours
HTTPCACHE_DIR = "data/scrapers/httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = ["500", "502", "503", "504", "408", "429"]
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Job directory for pausing/resuming crawls
# Set via command line: -s JOBDIR=/path/to/state
# JOBDIR = "data/scrapers/state"

# Feed exports configuration (JSONL streaming)
FEEDS = {
    "data/raw/jobs_%(time)s.jsonl": {
        "format": "jsonlines",
        "encoding": "utf-8",
        "overwrite": False,
    }
}

# Custom settings
JOBVISION_SITEMAP_URL = "https://jobvision.ir/sitemap/jobposts.xml"
JOBVISION_BASE_URL = "https://jobvision.ir"
JOBVISION_DAYS_BACK = 50

# Generate a unique run ID for this crawl
JOBVISION_RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
