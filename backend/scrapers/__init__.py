"""
Package initialization for JobVision scraper.

This package contains the complete Scrapy project for scraping job postings
from JobVision.ir in two phases:
1. Discovery - Parse sitemap and filter recent URLs
2. Detail - Scrape full job information from each URL
"""

__version__ = "0.1.0"
