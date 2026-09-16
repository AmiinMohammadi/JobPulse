"""
Scrapy middlewares for JobVision spider.

Includes:
- SoftBanDetectionMiddleware: Detects suspicious responses that may indicate soft bans
"""

from typing import Any, Dict
from scrapy import Spider, Request
from scrapy.http import Response
from scrapy.exceptions import IgnoreRequest
import logging

logger = logging.getLogger(__name__)


class JobvisionSpiderMiddleware:
    """
    Spider middleware for processing spider input/output.
    
    This middleware can be used to process items before they're sent to pipelines
    and to modify requests before they're scheduled.
    """

    def process_spider_output(self, response: Response, result: list, spider: Spider):
        """
        Process output from spider's parse method before sending to pipeline.
        
        Args:
            response: The HTTP response
            result: List of items/requests from parse method
            spider: The spider instance
            
        Returns:
            Modified list of items/requests
        """
        return (r for r in result)


class JobvisionDownloaderMiddleware:
    """
    Downloader middleware for processing requests/responses.
    
    This middleware can be used to modify requests before they're sent
    and to process responses before they reach the spider.
    """

    def process_request(
        self, request: Request, spider: Spider
    ) -> None:
        """
        Process each request before it's sent to the downloader.
        
        Args:
            request: The request to be sent
            spider: The spider instance
        """
        pass  # No request modification needed currently

    def process_response(
        self, request: Request, response: Response, spider: Spider
    ) -> Response:
        """
        Process each response before it reaches the spider.
        
        Args:
            request: The original request
            response: The HTTP response
            spider: The spider instance
            
        Returns:
            The response (or modified response)
        """
        return response


class SoftBanDetectionMiddleware:
    """
    Middleware to detect soft bans from the target website.
    
    A soft ban occurs when the server returns HTTP 200 but with:
    - Suspiciously short content (e.g., CAPTCHA page, error page)
    - Specific patterns indicating blocking
    
    When detected, the middleware logs a warning and can optionally
    skip the problematic request.
    """

    # Minimum acceptable response body length (bytes)
    MIN_RESPONSE_LENGTH = 1000
    
    # Patterns that might indicate a block/CAPTCHA page
    SUSPICIOUS_PATTERNS = [
        b"captcha",
        b"blocked",
        b"access denied",
        b"too many requests",
        b"rate limit",
    ]

    def process_response(
        self, request: Request, response: Response, spider: Spider
    ) -> Response:
        """
        Check if response indicates a soft ban.
        
        Args:
            request: The original request
            response: The HTTP response
            spider: The spider instance
            
        Returns:
            The response if OK, or raises IgnoreRequest if blocked
            
        Raises:
            IgnoreRequest: If response appears to be a soft ban
        """
        # Skip check for non-200 responses (handled by Scrapy)
        if response.status != 200:
            return response
        
        # Check response length
        body_length = len(response.body)
        if body_length < self.MIN_RESPONSE_LENGTH:
            logger.warning(
                f"Suspiciously short response ({body_length} bytes) "
                f"from {response.url}. Possible soft ban.",
                extra={"spider": spider},
            )
            # Don't ignore - let it through but log the warning
            # return IgnoreRequest(f"Soft ban detected: {response.url}")
        
        # Check for suspicious patterns (case-insensitive)
        body_lower = response.body.lower()
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern in body_lower:
                logger.warning(
                    f"Suspicious pattern '{pattern.decode()}' found in "
                    f"response from {response.url}. Possible soft ban.",
                    extra={"spider": spider},
                )
                # Log but don't ignore - review manually first
                # return IgnoreRequest(f"Soft ban detected: {response.url}")
        
        return response

    def process_exception(
        self, request: Request, exception: Exception, spider: Spider
    ) -> None:
        """
        Handle exceptions during request processing.
        
        Args:
            request: The original request
            exception: The exception that occurred
            spider: The spider instance
        """
        logger.error(
            f"Request failed: {request.url} - {exception}",
            extra={"spider": spider},
        )
        return None
