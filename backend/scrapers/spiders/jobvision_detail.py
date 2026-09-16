"""
Phase 2 Spider: Scrape detailed job information from JobVision.

This spider takes a list of job URLs (from Phase 1 discovery) and scrapes
detailed information for each job posting.

Key features:
- Extracts data from JSON-LD structured data (most reliable)
- Falls back to CSS selectors and ng-state script if needed
- Resumable with JOBDIR
- Streams output to JSONL to avoid memory issues

Usage:
    scrapy crawl jobvision_detail \
        -s JOBDIR=/path/to/jobdir \
        -o data/raw/jobvision_jobs_20260914_135642.jsonl
        
To use a specific URL file:
    scrapy crawl jobvision_detail -a url_file=data/raw/jobvision_urls_last50days.jsonl
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator
from urllib.parse import urlparse

from scrapy import Request, Spider
from scrapy.http import Response

logger = logging.getLogger(__name__)


class JobvisionDetailSpider(Spider):
    """
    Spider to scrape detailed job information from JobVision job pages.
    
    This spider:
    1. Reads job URLs from a JSONL file (or starts with empty list)
    2. Visits each job page
    3. Extracts structured data from JSON-LD and/or ng-state script
    4. Falls back to CSS selectors if needed
    5. Outputs structured job data to JSONL
    """

    name: str = "jobvision_detail"
    allowed_domains: list[str] = ["jobvision.ir"]
    
    # Default URL file (Phase 1 output)
    default_url_file: str = "data/raw/jobvision_urls_last50days.jsonl"

    def __init__(
        self, 
        url_file: str | None = None, 
        scraper_run_id: str | None = None,
        *args: Any, 
        **kwargs: Any
    ) -> None:
        """
        Initialize the detail spider.
        
        Args:
            url_file: Path to JSONL file containing URLs to scrape
            scraper_run_id: Unique ID for this crawl batch (auto-generated if not provided)
            *args: Additional positional arguments for Spider
            **kwargs: Additional keyword arguments for Spider
        """
        super().__init__(*args, **kwargs)
        
        # Set up URL file path
        self.url_file = url_file or self.default_url_file
        
        # Generate or use provided run ID
        self.scraper_run_id = scraper_run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Load URLs from file
        self.job_urls: list[dict[str, Any]] = self._load_urls()
        logger.info(f"Loaded {len(self.job_urls)} URLs from {self.url_file}")
        logger.info(f"Scraper run ID: {self.scraper_run_id}")

    def _load_urls(self) -> list[dict[str, Any]]:
        """
        Load job URLs from the Phase 1 output file.
        
        Returns:
            List of URL dictionaries with metadata
        """
        url_path = Path(self.url_file)
        if not url_path.exists():
            logger.warning(f"URL file not found: {url_path}")
            return []
        
        urls = []
        try:
            with open(url_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            url_data = json.loads(line)
                            urls.append(url_data)
                        except json.JSONDecodeError as e:
                            logger.warning(f"Invalid JSON line: {e}")
        except Exception as e:
            logger.error(f"Failed to load URL file: {e}")
        
        return urls

    def start_requests(self) -> Generator[Request, None, None]:
        """
        Generate requests for all job URLs.
        
        Yields:
            Request objects for each job page
        """
        for idx, url_data in enumerate(self.job_urls):
            source_url = url_data.get("source_url")
            if not source_url:
                continue
            
            yield Request(
                url=source_url,
                callback=self.parse_job_page,
                errback=self.handle_error,
                meta={
                    "job_id": url_data.get("id"),
                    "lastmod": url_data.get("lastmod"),
                    "discovered_at": url_data.get("discovered_at"),
                    "request_idx": idx,
                },
            )

    def parse_job_page(self, response: Response) -> Generator[dict[str, Any], None, None]:
        """
        Parse a job detail page and extract all required fields.
        
        Extraction strategy (in order of preference):
        1. JSON-LD structured data (type: JobPosting) - most reliable
        2. ng-state script (Angular SSR data)
        3. CSS selectors as fallback
        
        Args:
            response: HTTP response containing the job page HTML
            
        Yields:
            Dictionary with all extracted job fields
        """
        logger.debug(f"Parsing job page: {response.url}")
        
        # Initialize item with basic info
        item: dict[str, Any] = {
            "id": response.meta.get("job_id"),
            "source_url": response.url,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "posted_date": response.meta.get("lastmod"),
            "status": "active",
            "description_clean": "",  # Will be filled in later stage
            "first_seen": datetime.now(timezone.utc).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "scraper_run_id": self.scraper_run_id,
        }
        
        # Try to extract from JSON-LD first
        json_ld_data = self._extract_json_ld(response)
        if json_ld_data:
            logger.debug(f"Found JSON-LD data for {response.url}")
            item = self._merge_json_ld(item, json_ld_data)
        
        # Try to extract from ng-state script (Angular SSR)
        ng_state_data = self._extract_ng_state(response)
        if ng_state_data:
            logger.debug(f"Found ng-state data for {response.url}")
            item = self._merge_ng_state(item, ng_state_data)
        
        # Fallback: extract with CSS selectors
        item = self._extract_with_css(item, response)
        
        # Validate we got minimum required data
        if not item.get("title_raw"):
            logger.warning(f"No title extracted for {response.url}")
        
        if not item.get("description_raw"):
            logger.warning(f"No description extracted for {response.url}")
        
        # Compute content hash
        item["content_hash"] = self._compute_content_hash(
            item.get("title_raw", ""),
            item.get("description_raw", "")
        )
        
        # Detect language
        item["language"] = self._detect_language(
            item.get("title_raw", ""),
            item.get("description_raw", "")
        )
        
        yield item

    @staticmethod
    def _extract_json_ld(response: Response) -> dict[str, Any] | None:
        """
        Extract structured data from JSON-LD script tags.
        
        Looks for <script type="application/ld+json"> with JobPosting type.
        
        Args:
            response: HTTP response
            
        Returns:
            Parsed JSON-LD data or None
        """
        json_ld_scripts = response.xpath(
            '//script[@type="application/ld+json"]/text()'
        ).getall()
        
        for script_content in json_ld_scripts:
            try:
                data = json.loads(script_content.strip())
                # Check if this is a JobPosting
                if isinstance(data, dict):
                    if data.get("@type") == "JobPosting":
                        return data
                    # Handle array of schemas
                    if "@graph" in data:
                        for item in data["@graph"]:
                            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                                return item
            except json.JSONDecodeError:
                continue
        
        return None

    @staticmethod
    def _extract_ng_state(response: Response) -> dict[str, Any] | None:
        """
        Extract data from Angular ng-state script.
        
        JobVision uses Angular SSR, and the initial state contains structured data.
        
        Args:
            response: HTTP response
            
        Returns:
            Parsed ng-state data or None
        """
        ng_state = response.xpath('//script[@id="ng-state"]/text()').get()
        if not ng_state:
            return None
        
        try:
            # The ng-state might contain multiple JSON objects
            # Try to parse as single JSON first
            return json.loads(ng_state.strip())
        except json.JSONDecodeError:
            # Might be multiple concatenated JSON objects
            # This is more complex - skip for now
            logger.debug("Could not parse ng-state as JSON")
            return None

    def _merge_json_ld(
        self, item: dict[str, Any], json_ld: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Merge JSON-LD data into the item dictionary.
        
        Args:
            item: Current item dictionary
            json_ld: Parsed JSON-LD data
            
        Returns:
            Updated item dictionary
        """
        # Map JSON-LD fields to our schema
        field_mapping = {
            "title_raw": "title",
            "description_raw": "description",
            "company": lambda x: x.get("hiringOrganization", {}).get("name") if isinstance(x.get("hiringOrganization"), dict) else None,
            "location": lambda x: x.get("jobLocation", {}).get("address", {}).get("addressLocality") if isinstance(x.get("jobLocation"), dict) else None,
            "employment_type": "employmentType",
            "salary_range": lambda x: x.get("baseSalary", {}).get("value", {}).get("minValue") if isinstance(x.get("baseSalary"), dict) else None,
            "posted_date": "datePosted",
        }
        
        for target_field, source_field in field_mapping.items():
            if callable(source_field):
                value = source_field(json_ld)
            else:
                value = json_ld.get(source_field)
            
            if value and not item.get(target_field):
                item[target_field] = value
        
        # Extract skills if present
        if not item.get("required_skills"):
            skills = json_ld.get("skills", [])
            if isinstance(skills, str):
                item["required_skills"] = [s.strip() for s in skills.split(",")]
            elif isinstance(skills, list):
                item["required_skills"] = skills
        
        # Extract category from job title or additional info
        if not item.get("category"):
            item["category"] = json_ld.get("industry", json_ld.get("occupationalCategory"))
        
        return item

    def _merge_ng_state(
        self, item: dict[str, Any], ng_state: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Merge ng-state data into the item dictionary.
        
        Args:
            item: Current item dictionary
            ng_state: Parsed ng-state data
            
        Returns:
            Updated item dictionary
        """
        # The structure of ng-state depends on the site's Angular app
        # This is a placeholder - adjust based on actual structure
        if "jobDetail" in ng_state:
            job_detail = ng_state["jobDetail"]
            item.setdefault("title_raw", job_detail.get("title"))
            item.setdefault("description_raw", job_detail.get("description"))
            item.setdefault("company", job_detail.get("company"))
            item.setdefault("location", job_detail.get("location"))
        
        if "requirements" in ng_state:
            item.setdefault("required_skills", ng_state["requirements"])
        
        return item

    def _extract_with_css(
        self, item: dict[str, Any], response: Response
    ) -> dict[str, Any]:
        """
        Extract job data using CSS selectors as fallback.
        
        These selectors are educated guesses based on common patterns.
        They should be verified against actual JobVision HTML.
        
        Args:
            item: Current item dictionary
            response: HTTP response
            
        Returns:
            Updated item dictionary
        """
        # Common CSS selectors for job sites (adjust based on actual HTML)
        selectors = {
            "title_raw": [
                "h1.job-title::text",
                "h1::text",
                ".job-title::text",
                '[data-test="job-title"]::text',
            ],
            "description_raw": [
                ".job-description::text",
                '[data-test="job-description"]::text',
                ".description::text",
                "#job-description::text",
            ],
            "company": [
                ".company-name::text",
                ".company::text",
                '[data-test="company-name"]::text',
            ],
            "location": [
                ".job-location::text",
                ".location::text",
                '[data-test="job-location"]::text',
            ],
            "employment_type": [
                ".employment-type::text",
                ".job-type::text",
                '[data-test="employment-type"]::text',
            ],
        }
        
        for field, selector_list in selectors.items():
            if item.get(field):
                continue  # Already have this field from JSON-LD
            
            for selector in selector_list:
                value = response.css(selector).get()
                if value:
                    item[field] = value.strip()
                    break
        
        # Extract skills from tags
        if not item.get("required_skills"):
            skill_tags = response.css(
                ".skill-tag::text, .tags .tag::text, [data-test='skill-tag']::text"
            ).getall()
            if skill_tags:
                item["required_skills"] = [tag.strip() for tag in skill_tags]
        
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

    def handle_error(self, failure: Any) -> None:
        """
        Handle errors during job page download.
        
        Args:
            failure: Twisted Failure object describing the error
        """
        logger.error(f"Failed to scrape {failure.request.url}: {failure.value}")
