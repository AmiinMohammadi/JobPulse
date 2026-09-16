"""
Phase 1 Spider: Discover recent job postings from JobVision sitemap.

This spider parses the JobVision sitemap XML and extracts URLs for job postings
that have been updated within the last N days (default: 50 days).

Usage:
    scrapy crawl jobvision_discovery -o data/raw/jobvision_urls_last50days.jsonl
    
To change the number of days:
    scrapy crawl jobvision_discovery -a days_ago=30
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Generator
from urllib.parse import urlparse

from scrapy import Request, Spider
from scrapy.http import Response

logger = logging.getLogger(__name__)


class JobvisionDiscoverySpider(Spider):
    """
    Spider to discover recent job postings from JobVision sitemap.
    
    This spider:
    1. Downloads the sitemap XML from jobvision.ir
    2. Parses each <url> entry to extract <loc> and <lastmod>
    3. Filters URLs based on lastmod date (within last N days)
    4. Outputs filtered URLs to a JSONL file
    """

    name: str = "jobvision_discovery"
    allowed_domains: list[str] = ["jobvision.ir"]
    
    # Main sitemap index (contains links to category sitemaps)
    sitemap_index_url: str = "https://jobvision.ir/sitemap.xml"
    
    # Alternative: direct jobs sitemap (compressed)
    jobs_sitemap_url: str = "https://jobvision.ir/sitemap.jobs.xml.gz"
    
    # Default number of days to look back
    days_ago: int = 50

    def __init__(self, days_ago: int = 50, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the discovery spider.
        
        Args:
            days_ago: Number of days to look back for recent jobs
            *args: Additional positional arguments for Spider
            **kwargs: Additional keyword arguments for Spider
        """
        super().__init__(*args, **kwargs)
        self.days_ago = int(days_ago)
        self.cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days_ago)
        logger.info(f"Discovery spider initialized: looking back {self.days_ago} days")
        logger.info(f"Cutoff date: {self.cutoff_date.isoformat()}")
        
        # Track statistics
        self.total_urls: int = 0
        self.filtered_urls: int = 0
        self.skipped_urls: int = 0

    def start_requests(self) -> Generator[Request, None, None]:
        """
        Generate initial requests to start the crawl.
        
        We start with the main sitemap index to discover all job sitemaps.
        
        Yields:
            Request to download the sitemap index XML
        """
        yield Request(
            url=self.sitemap_index_url,
            callback=self.parse_sitemap_index,
            errback=self.handle_error,
            meta={"dont_cache": True},  # Don't cache sitemap
        )

    def parse_sitemap_index(self, response: Response) -> Generator[Request, None, None]:
        """
        Parse the sitemap index and extract links to individual sitemaps.
        
        The sitemap index format is:
        <sitemapindex>
            <sitemap>
                <loc>https://jobvision.ir/sitemap.jobs.xml.gz</loc>
            </sitemap>
        </sitemapindex>
        
        Args:
            response: HTTP response containing the sitemap index XML
            
        Yields:
            Request to download each job sitemap
        """
        logger.info(f"Parsing sitemap index from {response.url}")
        
        # Extract all sitemap URLs
        sitemap_urls = response.xpath("//sitemap/loc/text()").getall()
        logger.info(f"Found {len(sitemap_urls)} sitemaps in index")
        
        for sitemap_url in sitemap_urls:
            # Only process job-related sitemaps (skip blog, etc.)
            if "job" in sitemap_url.lower():
                logger.info(f"Queuing job sitemap: {sitemap_url}")
                yield Request(
                    url=sitemap_url,
                    callback=self.parse_sitemap,
                    errback=self.handle_error,
                    meta={"dont_cache": True},
                )

    def parse_sitemap(self, response: Response) -> Generator[dict[str, Any], None, None]:
        """
        Parse an individual sitemap XML and extract job URLs.
        
        The sitemap format is:
        <urlset>
            <url>
                <loc>https://jobvision.ir/jobs/1234567/title</loc>
                <lastmod>2026-09-14T13:56:42Z</lastmod>
            </url>
        </urlset>
        
        Note: This handles both regular XML and gzipped XML sitemaps.
        
        Args:
            response: HTTP response containing the sitemap XML
            
        Yields:
            Dictionary with URL and metadata for each recent job posting
        """
        logger.info(f"Parsing sitemap from {response.url}")
        
        # Use XPath to extract all URL entries
        url_entries = response.xpath("//url")
        self.total_urls = len(url_entries)
        logger.info(f"Found {self.total_urls} total URLs in sitemap")
        
        for entry in url_entries:
            try:
                # Extract URL location
                loc = entry.xpath("loc/text()").get()
                if not loc:
                    continue
                
                # Extract last modification date
                lastmod_str = entry.xpath("lastmod/text()").get()
                if not lastmod_str:
                    # If no lastmod, skip (we want only dated entries)
                    logger.debug(f"Skipping {loc}: no lastmod date")
                    self.skipped_urls += 1
                    continue
                
                # Parse the ISO 8601 date
                lastmod_date = self._parse_iso_date(lastmod_str)
                if lastmod_date is None:
                    logger.warning(f"Could not parse date '{lastmod_str}' for {loc}")
                    self.skipped_urls += 1
                    continue
                
                # Check if this URL is within our time window
                if lastmod_date < self.cutoff_date:
                    logger.debug(f"Skipping {loc}: lastmod {lastmod_date} is too old")
                    self.skipped_urls += 1
                    continue
                
                # Extract job ID from URL (e.g., /jobs/1523449/title -> 1523449)
                job_id = self._extract_job_id(loc)
                
                # This URL qualifies - output it
                self.filtered_urls += 1
                yield {
                    "id": job_id,
                    "source_url": loc,
                    "lastmod": lastmod_date.isoformat(),
                    "discovered_at": datetime.now(timezone.utc).isoformat(),
                }
                
                # Log progress every 100 URLs
                if self.filtered_urls % 100 == 0:
                    logger.info(f"Found {self.filtered_urls} recent URLs so far...")
                    
            except Exception as e:
                logger.error(f"Error processing sitemap entry: {e}")
                continue
        
        logger.info(
            f"Sitemap parsing complete: "
            f"{self.filtered_urls}/{self.total_urls} URLs within last {self.days_ago} days "
            f"({self.skipped_urls} skipped)"
        )

    @staticmethod
    def _parse_iso_date(date_str: str) -> datetime | None:
        """
        Parse an ISO 8601 date string.
        
        Handles formats like:
        - 2026-09-14T13:56:42Z
        - 2026-09-14T13:56:42+00:00
        - 2026-09-14
        
        Args:
            date_str: ISO 8601 formatted date string
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        # Try common ISO formats
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                # Ensure timezone-aware (convert to UTC)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        
        return None

    @staticmethod
    def _extract_job_id(url: str) -> str:
        """
        Extract numeric job ID from JobVision URL.
        
        Examples:
        - https://jobvision.ir/jobs/1523449/software-engineer -> 1523449
        - https://jobvision.ir/jobs/987654 -> 987654
        
        Args:
            url: Full job posting URL
            
        Returns:
            Job ID as string, or the full URL if extraction fails
        """
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.strip("/").split("/")
            
            # Look for 'jobs' in path and take the next part
            for i, part in enumerate(path_parts):
                if part == "jobs" and i + 1 < len(path_parts):
                    return path_parts[i + 1]
            
            # Fallback: return full URL as ID
            return url
        except Exception:
            return url

    def handle_error(self, failure: Any) -> None:
        """
        Handle errors during sitemap download.
        
        Args:
            failure: Twisted Failure object describing the error
        """
        logger.error(f"Failed to download sitemap: {failure}")
