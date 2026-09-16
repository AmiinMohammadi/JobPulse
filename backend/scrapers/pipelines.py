"""
Scrapy pipelines for JobVision spider.

Handles item validation and processing before export.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from itemadapter import ItemAdapter
from scrapy import Spider


class JobvisionPipeline:
    """
    Pipeline for processing scraped items.
    
    Performs:
    - Field validation
    - Hash computation
    - Timestamp normalization
    """

    def process_item(
        self, item: Dict[str, Any], spider: Spider
    ) -> Dict[str, Any]:
        """
        Process each scraped item before export.
        
        Args:
            item: The scraped item dictionary
            spider: The spider instance
            
        Returns:
            Processed item ready for export
        """
        # Ensure all required fields exist
        adapter = ItemAdapter(item)
        
        # Compute content hash if not already set
        if "content_hash" not in adapter or not adapter["content_hash"]:
            title = adapter.get("title_raw", "") or ""
            description = adapter.get("description_raw", "") or ""
            content = f"{title}{description}".encode("utf-8")
            adapter["content_hash"] = hashlib.md5(content).hexdigest()
        
        # Ensure scraped_at is ISO format
        if "scraped_at" in adapter and adapter["scraped_at"]:
            if isinstance(adapter["scraped_at"], datetime):
                adapter["scraped_at"] = adapter["scraped_at"].isoformat()
        
        # Set default values for nullable fields
        adapter.setdefault("company", None)
        adapter.setdefault("location", None)
        adapter.setdefault("salary_range", None)
        adapter.setdefault("employment_type", None)
        adapter.setdefault("experience_level", None)
        adapter.setdefault("required_skills", [])
        adapter.setdefault("description_clean", "")
        
        return dict(adapter)
