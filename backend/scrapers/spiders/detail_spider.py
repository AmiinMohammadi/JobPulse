"""
JobVision Detail Spider - Phase 2

Scrapes detailed job information from JobVision job posting pages.
Reads URLs from a JSONL file (output of Phase 1) and extracts all required fields.
"""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from scrapy import Spider, Request
from scrapy.http import Response


class JobvisionDetailSpider(Spider):
    """
    Spider to scrape detailed job information from JobVision.
    
    This spider:
    1. Reads URLs from a JSONL file (Phase 1 output)
    2. Visits each job posting page
    3. Extracts structured data from JSON-LD and HTML
    4. Yields complete job records
    
    Usage:
        scrapy crawl jobvision_detail \
          -s JOBVISION_URL_FILE=data/raw/jobvision_urls_last50days.jsonl \
          -o data/raw/jobvision_jobs_YYYYMMDD_HHMMSS.jsonl
    """

    name = "jobvision_detail"
    allowed_domains = ["jobvision.ir"]

    # Custom settings for this spider
    custom_settings = {
        # Lower concurrency for detail scraping
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "DOWNLOAD_DELAY": 2,
    }

    def __init__(
        self,
        url_file: Optional[str] = None,
        run_id: Optional[str] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the spider.
        
        Args:
            url_file: Path to JSONL file with URLs to scrape
            run_id: Unique identifier for this crawl run
        """
        super().__init__(*args, **kwargs)
        
        self.url_file = url_file or getattr(
            self.settings, "JOBVISION_URL_FILE", None
        )
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.urls_to_scrape: List[Dict[str, Any]] = []
        
        # Load URLs from file if provided
        if self.url_file:
            self._load_urls()

    def _load_urls(self) -> None:
        """Load URLs from the JSONL file."""
        url_path = Path(self.url_file)
        
        if not url_path.exists():
            self.logger.error(f"URL file not found: {self.url_file}")
            return
        
        count = 0
        with open(url_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    self.urls_to_scrape.append(data)
                    count += 1
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Invalid JSON line: {e}")
        
        self.logger.info(f"Loaded {count} URLs from {self.url_file}")

    def start_requests(self) -> Generator[Request, None, None]:
        """
        Generate requests for all URLs to scrape.
        
        Yields:
            Request objects for each job posting URL
        """
        if not self.urls_to_scrape:
            self.logger.warning("No URLs to scrape. Provide --url_file parameter.")
            return
        
        for url_data in self.urls_to_scrape:
            url = url_data.get("url", "")
            lastmod = url_data.get("lastmod", "")
            
            yield Request(
                url=url,
                callback=self.parse_job_page,
                meta={
                    "lastmod": lastmod,
                    "dont_cache": False,
                },
            )

    def parse_job_page(
        self, response: Response
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Parse a job posting page and extract all required fields.
        
        Args:
            response: HTTP response from job posting page
            
        Yields:
            Dictionary containing all job fields
        """
        url = response.url
        
        # Extract JSON-LD structured data
        job_posting = self._extract_json_ld(response)
        
        # Extract additional data from HTML
        title_raw = self._extract_title(response, job_posting)
        description_raw = self._extract_description(response, job_posting)
        company = self._extract_company(response, job_posting)
        location = self._extract_location(response, job_posting)
        employment_type = self._extract_employment_type(job_posting)
        salary_range = self._extract_salary(job_posting)
        category = self._extract_category(response)
        posted_date = self._extract_posted_date(
            response.meta.get("lastmod", ""), job_posting
        )
        
        # Detect language
        language = self._detect_language(title_raw, description_raw)
        
        # Extract job ID from URL
        job_id = self._extract_job_id(url)
        
        # Build the item
        scraped_at = datetime.now(timezone.utc).isoformat()
        
        item = {
            "id": job_id,
            "source_url": url,
            "scraped_at": scraped_at,
            "posted_date": posted_date,
            "status": "active",
            "title_raw": title_raw,
            "description_raw": description_raw,
            "description_clean": "",  # Will be filled later with Hazm
            "language": language,
            "category": category,
            "company": company,
            "location": location,
            "salary_range": salary_range,
            "employment_type": employment_type,
            "experience_level": None,  # Not readily available in HTML
            "required_skills": [],  # Not shown as tags on this site
            "content_hash": hashlib.md5(
                f"{title_raw}{description_raw}".encode("utf-8")
            ).hexdigest(),
            "first_seen": scraped_at,
            "last_seen": scraped_at,
            "scraper_run_id": self.run_id,
        }
        
        yield item

    def _extract_json_ld(
        self, response: Response
    ) -> Optional[Dict[str, Any]]:
        """
        Extract JSON-LD structured data from the page.
        
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
                # Clean up the content (may have whitespace/newlines)
                content = script_content.strip()
                if content:
                    data = json.loads(content)
                    # Look for JobPosting type
                    if isinstance(data, dict) and data.get("@type") == "JobPosting":
                        return data
                    # Handle array of schemas
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                                return item
            except json.JSONDecodeError:
                continue
        
        return None

    def _extract_title(
        self, response: Response, job_posting: Optional[Dict[str, Any]]
    ) -> str:
        """Extract job title."""
        if job_posting and "title" in job_posting:
            return job_posting["title"].strip()
        
        # Fallback: try HTML
        title = response.xpath("//h1/text()").get(default="").strip()
        return title or "Unknown"

    def _extract_description(
        self, response: Response, job_posting: Optional[Dict[str, Any]]
    ) -> str:
        """Extract full job description."""
        if job_posting and "description" in job_posting:
            # Clean up the description (may have escaped characters)
            desc = job_posting["description"]
            # Remove extra whitespace but keep structure
            desc = re.sub(r"\s+", " ", desc).strip()
            return desc
        
        # Fallback: try to extract from HTML
        # JobVision typically has description in a specific div
        desc_parts = response.xpath(
            "//div[contains(@class, 'job-detail') or contains(@class, 'description')]//text()"
        ).getall()
        
        if desc_parts:
            desc = " ".join([t.strip() for t in desc_parts if t.strip()])
            return re.sub(r"\s+", " ", desc).strip()
        
        return ""

    def _extract_company(
        self, response: Response, job_posting: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Extract company name."""
        if job_posting and "hiringOrganization" in job_posting:
            org = job_posting["hiringOrganization"]
            if isinstance(org, dict) and "name" in org:
                return org["name"].strip()
        
        return None

    def _extract_location(
        self, response: Response, job_posting: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Extract job location."""
        if job_posting and "jobLocation" in job_posting:
            location = job_posting["jobLocation"]
            if isinstance(location, dict) and "address" in location:
                address = location["address"]
                if isinstance(address, dict):
                    city = address.get("addressLocality", "")
                    region = address.get("addressRegion", "")
                    if city and region:
                        return f"{city}, {region}".strip()
                    elif city:
                        return city.strip()
                    elif region:
                        return region.strip()
        
        return None

    def _extract_employment_type(
        self, job_posting: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Extract employment type."""
        if job_posting and "employmentType" in job_posting:
            emp_type = job_posting["employmentType"]
            # Map to standard values
            type_mapping = {
                "full-time": "full-time",
                "part-time": "part-time",
                "contract": "contract",
                "internship": "internship",
                "temporary": "temporary",
            }
            return type_mapping.get(emp_type.lower(), emp_type)
        
        return None

    def _extract_salary(
        self, job_posting: Optional[Dict[str, Any]]
    ) -> Optional[str]:
        """Extract salary range if available."""
        if job_posting and "baseSalary" in job_posting:
            salary = job_posting["baseSalary"]
            # Could be a number or a Salary object
            if isinstance(salary, (int, float)):
                return str(salary)
            elif isinstance(salary, dict):
                # Schema.org Salary specification
                value = salary.get("value", "")
                currency = salary.get("currency", "IRT")
                if value:
                    return f"{value} {currency}"
        
        return None

    def _extract_category(self, response: Response) -> Optional[str]:
        """Extract job category from the page."""
        # Try to find category links or breadcrumbs
        category = response.xpath(
            "//a[contains(@href, '/jobs/category/')]/text()"
        ).get()
        
        if category:
            return category.strip()
        
        return None

    def _extract_posted_date(
        self,
        sitemap_lastmod: str,
        job_posting: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        """Extract posted date."""
        # Prefer datePosted from JSON-LD
        if job_posting and "datePosted" in job_posting:
            return job_posting["datePosted"]
        
        # Fallback to sitemap lastmod
        if sitemap_lastmod:
            return sitemap_lastmod
        
        return None

    def _extract_job_id(self, url: str) -> Optional[str]:
        """Extract job ID from URL."""
        # URL pattern: https://jobvision.ir/jobs/1508440/...
        match = re.search(r"/jobs/(\d+)/", url)
        if match:
            return match.group(1)
        return None

    def _detect_language(
        self, title: str, description: str
    ) -> str:
        """
        Detect language of the job posting.
        
        Simple heuristic based on Persian character presence.
        
        Args:
            title: Job title
            description: Job description
            
        Returns:
            "fa", "en", or "mixed"
        """
        text = f"{title} {description}"
        
        # Persian character range
        persian_pattern = re.compile(r"[\u0600-\u06FF\uFB50-\uFDFF\uFE70-\uFEFF]")
        
        has_persian = bool(persian_pattern.search(text))
        has_latin = bool(re.search(r"[a-zA-Z]", text))
        
        if has_persian and has_latin:
            return "mixed"
        elif has_persian:
            return "fa"
        else:
            return "en"
