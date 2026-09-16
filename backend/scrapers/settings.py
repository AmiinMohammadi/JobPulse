"""
JobVision Scrapy Project Configuration

This module contains all Scrapy settings for the Job Pulse job scraper.
Politeness and respect for the target server are prioritized.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

# Basic Scrapy configuration
BOT_NAME: str = "jobvision_scraper"
SPIDER_MODULES: list[str] = ["backend.scrapers.spiders"]
NEWSPIDER_MODULE: str = "backend.scrapers.spiders"

# Respect robots.txt rules (mandatory)
ROBOTSTXT_OBEY: bool = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# We use very conservative settings to be polite
CONCURRENT_REQUESTS: int = 4
CONCURRENT_REQUESTS_PER_DOMAIN: int = 2

# Delay between requests to the same website
DOWNLOAD_DELAY: float = 2.0

# Enable AutoThrottle extension with conservative settings
AUTOTHROTTLE_ENABLED: bool = True
AUTOTHROTTLE_START_DELAY: float = 3.0
AUTOTHROTTLE_MAX_DELAY: float = 30.0
AUTOTHROTTLE_TARGET_CONCURRENCY: float = 1.0

# Enable cookies (needed for some sites)
COOKIES_ENABLED: bool = True

# Enable soft ban detection middleware
DOWNLOADER_MIDDLEWARES: dict[str, int] = {
    "backend.scrapers.middleware.SoftBanDetectionMiddleware": 543,
}

# Enable item pipeline for data validation
ITEM_PIPELINES: dict[str, int] = {
    "backend.scrapers.pipelines.JobDataPipeline": 300,
}

# Output configuration - stream to JSONL to avoid memory issues
# The filename will be dynamically set by spiders
FEEDS: dict[str, dict[str, Any]] = {}

# Enable JOBDIR for resumable crawls
# Set via command line: scrapy crawl <spider> -s JOBDIR=/path/to/jobdir
# This allows pausing and resuming crawls

# HTTP caching to reduce repeated requests during development
HTTPCACHE_ENABLED: bool = True
HTTPCACHE_DIR: str = "/tmp/scrapy_httpcache"
HTTPCACHE_EXPIRATION_SECS: int = 86400 * 7  # 7 days

# User agent - be transparent about who we are
USER_AGENT: str = "JobPulse-Research-Bot (+https://github.com/your-repo/job-pulse)"

# Timeout for requests
DOWNLOAD_TIMEOUT: int = 30

# Don't follow redirects by default (we want to know if something changed)
REDIRECT_ENABLED: bool = True
MAX_REDIRECTS: int = 3

# Logging
LOG_LEVEL: str = "INFO"
LOG_FORMAT: str = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"


def get_jobdir_path() -> Path:
    """Get the path for storing crawl state (JOBDIR)."""
    base_path = Path(__file__).parent.parent.parent / "data" / "scrapy_jobs"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path


def get_raw_data_path() -> Path:
    """Get the path for storing scraped data."""
    base_path = Path(__file__).parent.parent.parent / "data" / "raw"
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path
