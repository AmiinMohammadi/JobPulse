"""
JobVision Discovery Spider - Phase 1

Parses the JobVision sitemap to extract job posting URLs from the last 50 days.
Outputs a JSONL file with URLs and their lastmod dates for Phase 2 scraping.
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Generator, Optional

from scrapy import Spider, Request
from scrapy.http import Response


class JobvisionDiscoverySpider(Spider):
    """
    Spider to discover recent job posting URLs from JobVision sitemap.
    
    This spider:
    1. Downloads the sitemap XML
    2. Parses each URL entry
    3. Filters by lastmod date (last 50 days)
    4. Yields URL + lastmod pairs for Phase 2
    
    Usage:
        scrapy crawl jobvision_discovery \
          -o data/raw/jobvision_urls_last50days.jsonl
    """

    name = "jobvision_discovery"
    allowed_domains = ["jobvision.ir"]
    
    # Sitemap URL (can be overridden via settings)
    sitemap_url = "https://jobvision.ir/sitemap/jobposts.xml"
    
    # Number of days to look back
    days_back = 50

    def start_requests(self) -> Generator[Request, None, None]:
        """
        Generate initial requests to the sitemap.
        
        Yields:
            Request to download the sitemap XML
        """
        yield Request(
            url=self.sitemap_url,
            callback=self.parse_sitemap,
            meta={"dont_cache": True},  # Always fetch fresh sitemap
        )

    def parse_sitemap(
        self, response: Response
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Parse the sitemap XML and extract URLs from the last N days.
        
        Args:
            response: HTTP response containing sitemap XML
            
        Yields:
            Dictionary with 'url' and 'lastmod' keys for recent jobs
        """
        # Calculate cutoff date
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=self.days_back)
        
        # Parse XML using Scrapy's selector
        urls = response.xpath("//url")
        
        count_total = 0
        count_filtered = 0
        
        for url_entry in urls:
            count_total += 1
            
            # Extract URL and lastmod
            loc = url_entry.xpath("loc/text()").get(default="").strip()
            lastmod_str = url_entry.xpath("lastmod/text()").get(default="").strip()
            
            if not loc:
                continue
            
            # Parse lastmod timestamp
            lastmod_date = self._parse_timestamp(lastmod_str)
            
            if lastmod_date is None:
                # If no lastmod, skip (or could include all)
                continue
            
            # Filter by date
            if lastmod_date < cutoff_date:
                continue
            
            count_filtered += 1
            
            # Yield the URL with metadata
            yield {
                "url": loc,
                "lastmod": lastmod_str,
                "lastmod_parsed": lastmod_date.isoformat(),
            }
        
        self.logger.info(
            f"Sitemap parsing complete: {count_filtered}/{count_total} URLs "
            f"from the last {self.days_back} days"
        )

    def _parse_timestamp(
        self, timestamp_str: str
    ) -> Optional[datetime]:
        """
        Parse various timestamp formats from sitemap.
        
        Args:
            timestamp_str: Timestamp string from sitemap
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        if not timestamp_str:
            return None
        
        # Common sitemap timestamp formats
        formats = [
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                # Ensure timezone-aware
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        
        self.logger.warning(f"Could not parse timestamp: {timestamp_str}")
        return None
