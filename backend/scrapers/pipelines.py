"""
Scrapy pipelines for processing and validating scraped job data.

This module contains pipelines that:
- Validate required fields
- Clean and normalize data
- Compute derived fields (content_hash, language detection)
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from scrapy import Spider

logger = logging.getLogger(__name__)


class JobDataPipeline:
    """
    Pipeline for validating and enriching job posting data.
    
    This pipeline ensures all required fields are present and computes
    derived fields like content_hash and language detection.
    """

    # Required fields that must be present in every item
    REQUIRED_FIELDS: list[str] = [
        "id",
        "source_url",
        "scraped_at",
        "title_raw",
        "description_raw",
    ]

    def process_item(self, item: dict[str, Any], spider: Spider) -> dict[str, Any]:
        """
        Process and validate a scraped job item.
        
        Args:
            item: The scraped job data dictionary
            spider: The spider that scraped this item
            
        Returns:
            The validated and enriched item
            
        Raises:
            KeyError: If a required field is missing
        """
        # Validate required fields
        for field in self.REQUIRED_FIELDS:
            if field not in item:
                raise KeyError(f"Missing required field: {field}")
        
        # Compute content hash if not already set
        if "content_hash" not in item or not item["content_hash"]:
            item["content_hash"] = self._compute_content_hash(
                item.get("title_raw", ""),
                item.get("description_raw", "")
            )
        
        # Detect language if not already set
        if "language" not in item or not item["language"]:
            item["language"] = self._detect_language(
                item.get("title_raw", ""),
                item.get("description_raw", "")
            )
        
        # Ensure scraped_at is ISO format
        if "scraped_at" in item and isinstance(item["scraped_at"], datetime):
            item["scraped_at"] = item["scraped_at"].isoformat()
        
        # Set defaults for optional fields
        item.setdefault("description_clean", "")
        item.setdefault("required_skills", [])
        item.setdefault("status", "active")
        
        return item

    @staticmethod
    def _compute_content_hash(title: str, description: str) -> str:
        """
        Compute MD5 hash of title + description for deduplication.
        
        Args:
            title: Job title
            description: Job description
            
        Returns:
            Hexadecimal MD5 hash string
        """
        content = f"{title}{description}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()

    @staticmethod
    def _detect_language(title: str, description: str) -> str:
        """
        Simple heuristic to detect if text is Persian, English, or mixed.
        
        This is a basic implementation. For production, consider using
        langdetect or fasttext libraries.
        
        Args:
            title: Job title
            description: Job description
            
        Returns:
            Language code: 'fa', 'en', or 'mixed'
        """
        text = f"{title} {description}"
        
        # Count Persian characters (Unicode range for Arabic/Persian script)
        persian_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        
        # Count Latin characters
        latin_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        
        total_chars = persian_chars + latin_chars
        
        if total_chars == 0:
            return "fa"  # Default to Persian
        
        persian_ratio = persian_chars / total_chars
        
        # Heuristic thresholds
        if persian_ratio > 0.7:
            return "fa"
        elif persian_ratio < 0.3:
            return "en"
        else:
            return "mixed"
