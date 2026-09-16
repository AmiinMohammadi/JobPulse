"""
Scrapy middleware for detecting soft bans and suspicious responses.

A soft ban occurs when the server returns HTTP 200 but with suspicious content:
- Very short response body (likely an error page or CAPTCHA)
- Specific keywords indicating blocking
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from scrapy.http import Request, Response
from scrapy.spiders import Spider

if TYPE_CHECKING:
    from scrapy.crawler import Crawler

logger = logging.getLogger(__name__)


class SoftBanDetectionMiddleware:
    """
    Detects potential soft bans by analyzing response characteristics.
    
    A soft ban is when the server returns HTTP 200 OK but actually blocks
    the scraper with a CAPTCHA, error page, or empty response.
    
    Detection criteria:
    - Response body shorter than 500 bytes (suspiciously small for a job page)
    - Presence of blocking-related keywords in the response
    """

    # Minimum expected size for a valid job posting page (in bytes)
    MIN_RESPONSE_SIZE: int = 500
    
    # Keywords that might indicate a block/CAPTCHA page
    BLOCK_KEYWORDS: list[str] = [
        "captcha",
        "blocked",
        "access denied",
        "suspicious activity",
        "verify you are human",
        "rate limit",
    ]

    def __init__(self, crawler: Crawler) -> None:
        """Initialize the middleware with crawler settings."""
        self.crawler = crawler
        self.min_size = crawler.settings.getint(
            "SOFT_BAN_MIN_SIZE", default=self.MIN_RESPONSE_SIZE
        )
        logger.info("SoftBanDetectionMiddleware initialized")

    @classmethod
    def from_crawler(cls, crawler: Crawler) -> SoftBanDetectionMiddleware:
        """Create middleware instance from crawler (Scrapy convention)."""
        return cls(crawler)

    def process_response(
        self, request: Request, response: Response, spider: Spider
    ) -> Response | Request:
        """
        Analyze the response for signs of soft banning.
        
        Args:
            request: The original request that was made
            response: The response received from the server
            spider: The spider that made the request
            
        Returns:
            The response if it looks valid, or the request to retry if suspicious
        """
        # Skip non-200 responses (they're handled elsewhere)
        if response.status != 200:
            return response
        
        # Check response size
        body_size = len(response.body)
        if body_size < self.min_size:
            logger.warning(
                f"Suspiciously small response ({body_size} bytes) from {response.url}. "
                f"Possible soft ban detected."
            )
            spider.crawler.stats.inc_value("softban/suspicious_small_response")
            # Don't block the request, just log it
            # The spider can decide what to do based on this
        
        # Check for block keywords in the response text
        response_text = response.text.lower()
        for keyword in self.BLOCK_KEYWORDS:
            if keyword in response_text:
                logger.warning(
                    f"Found blocking keyword '{keyword}' in response from {response.url}. "
                    f"Possible soft ban detected."
                )
                spider.crawler.stats.inc_value(f"softban/keyword_{keyword}")
                break
        
        return response

    def process_exception(
        self, request: Request, exception: Exception, spider: Spider
    ) -> Response | Request | None:
        """
        Handle exceptions during download.
        
        This can be extended to implement retry logic or circuit breakers.
        
        Args:
            request: The original request
            exception: The exception that occurred
            spider: The spider that made the request
        """
        logger.error(f"Request failed: {exception} for {request.url}")
        spider.crawler.stats.inc_value("softban/request_exception")
        return None
