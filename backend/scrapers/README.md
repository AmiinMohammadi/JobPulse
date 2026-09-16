# JobVision Scraper - Stage 1

Polite two-phase Scrapy crawler for JobVision job postings.

## Overview

This scraper operates in two phases:
1. **Phase 1 - Discovery**: Parses the sitemap, filters URLs from the last 50 days, saves to JSONL
2. **Phase 2 - Detail Scraping**: Visits each URL and extracts job details

## Prerequisites

```bash
# Install scrapy (already in project)
uv add scrapy
```

## Configuration

The scraper is configured to be polite:
- Respects robots.txt
- AutoThrottle enabled (3-30s delay)
- Max 2 concurrent requests per domain
- 2s download delay
- Can be paused/resumed via JOBDIR

## Usage

### Phase 1: Discover Recent URLs

Extract job URLs from the last 50 days:

```bash
cd /workspace
uv run scrapy crawl jobvision_discovery \
  -s JOBDIR=/workspace/data/scrapers/discovery_state \
  -o data/raw/jobvision_urls_last50days.jsonl
```

**Output**: `data/raw/jobvision_urls_last50days.jsonl`
- Each line contains: `{"url": "...", "lastmod": "2026-09-02T18:13:56Z"}`

### Phase 2: Scrape Job Details

Scrape detailed information from the discovered URLs:

```bash
cd /workspace
uv run scrapy crawl jobvision_detail \
  -s JOBDIR=/workspace/data/scrapers/detail_state \
  -s JOBVISION_URL_FILE=data/raw/jobvision_urls_last50days.jsonl \
  -o data/raw/jobvision_jobs_$(date +%Y%m%d_%H%M%S).jsonl
```

**Output**: `data/raw/jobvision_jobs_YYYYMMDD_HHMMSS.jsonl`
- Each line is a complete job record with all required fields

## Output Fields

Each scraped job contains:

| Field | Description |
|-------|-------------|
| `id` | JobVision numeric ID from URL |
| `source_url` | Full original URL |
| `scraped_at` | ISO timestamp of scraping |
| `posted_date` | Date from sitemap lastmod or page |
| `status` | "active" (default) |
| `title_raw` | Original job title |
| `description_raw` | Full raw description text |
| `description_clean` | Empty for now (cleaned later with Hazm) |
| `language` | "fa", "en", or "mixed" |
| `category` | Job category/subcategory |
| `company` | Company name (nullable) |
| `location` | City/location (nullable) |
| `salary_range` | Salary if present (nullable) |
| `employment_type` | full-time/part-time/etc. (nullable) |
| `experience_level` | Experience level if present (nullable) |
| `required_skills` | List of skills/tags (empty list if none) |
| `content_hash` | MD5 of title + description |
| `first_seen` | Same as scraped_at initially |
| `last_seen` | Same as scraped_at initially |
| `scraper_run_id` | Unique ID for this crawl batch |

## Resuming Interrupted Crawls

Both spiders support resumption. Simply re-run the same command with the same JOBDIR:

```bash
# Resume discovery
uv run scrapy crawl jobvision_discovery \
  -s JOBDIR=/workspace/data/scrapers/discovery_state

# Resume detail scraping
uv run scrapy crawl jobvision_detail \
  -s JOBDIR=/workspace/data/scrapers/detail_state \
  -s JOBVISION_URL_FILE=data/raw/jobvision_urls_last50days.jsonl
```

## Testing

1. **Test Phase 1 with small sample**:
```bash
uv run scrapy crawl jobvision_discovery --set DOWNLOAD_DELAY=1 -s JOBDIR=/tmp/test_disc
```

2. **Test Phase 2 with 5 URLs**:
   - Manually create a test file with 5 URLs
   - Run the detail spider on it

3. **Verify output**:
```bash
# Count records
wc -l data/raw/jobvision_urls_last50days.jsonl
wc -l data/raw/jobvision_jobs_*.jsonl

# View first record
head -1 data/raw/jobvision_jobs_*.jsonl | python -m json.tool
```

## Notes

- The site uses Angular SSR - all data is in static HTML (JSON-LD structured data)
- No JavaScript rendering needed (no Playwright required)
- Personal info (phone/email) is NOT extracted per requirements
- All timestamps are in ISO 8601 format
