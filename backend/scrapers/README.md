# JobVision Scraper - Stage 1: Get the Data

This directory contains the Scrapy project for scraping job postings from JobVision.ir.

## Overview

The scraper operates in **two phases**:

### Phase 1: Discovery
- Parses the JobVision sitemap (`https://jobvision.ir/sitemap/jobposts.xml`)
- Filters URLs to only include jobs updated within the last 50 days (configurable)
- Outputs a JSONL file with URLs and metadata

### Phase 2: Detail Scraping
- Reads the URL list from Phase 1
- Visits each job page and extracts structured data
- Prioritizes JSON-LD structured data, falls back to CSS selectors
- Outputs detailed job information to JSONL

## Project Structure

```
backend/scrapers/
├── __init__.py              # Package initialization
├── settings.py              # Scrapy configuration (politeness settings)
├── middleware.py            # Soft ban detection middleware
├── pipelines.py             # Data validation and enrichment pipeline
└── spiders/
    ├── __init__.py
    ├── jobvision_discovery.py   # Phase 1: Sitemap parser
    └── jobvision_detail.py      # Phase 2: Job detail scraper
```

## Installation

Scrapy is already installed. If you need to reinstall:

```bash
pip install scrapy
```

## Usage

### Phase 1: Discover Recent Jobs

Run the discovery spider to extract URLs from the sitemap:

```bash
cd /workspace

# Basic usage (last 50 days)
scrapy crawl jobvision_discovery \
    -o data/raw/jobvision_urls_last50days.jsonl \
    -s JOBDIR=data/scrapy_jobs/discovery

# Custom time window (e.g., last 30 days)
scrapy crawl jobvision_discovery \
    -a days_ago=30 \
    -o data/raw/jobvision_urls_last30days.jsonl \
    -s JOBDIR=data/scrapy_jobs/discovery_30d
```

**Output format** (`jobvision_urls_last50days.jsonl`):
```json
{"id": "1523449", "source_url": "https://jobvision.ir/jobs/1523449/software-engineer", "lastmod": "2026-09-14T13:56:42+00:00", "discovered_at": "2026-09-16T10:30:00+00:00"}
```

### Phase 2: Scrape Job Details

Run the detail spider to scrape full job information:

```bash
cd /workspace

# Generate timestamp for output filename
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Basic usage (uses default URL file)
scrapy crawl jobvision_detail \
    -s JOBDIR=data/scrapy_jobs/detail_${TIMESTAMP} \
    -o data/raw/jobvision_jobs_${TIMESTAMP}.jsonl

# Specify custom URL file
scrapy crawl jobvision_detail \
    -a url_file=data/raw/jobvision_urls_last50days.jsonl \
    -s JOBDIR=data/scrapy_jobs/detail_run1 \
    -o data/raw/jobvision_jobs_20260916_103000.jsonl
```

**Output fields** (per job):
- `id`: JobVision job ID (numeric)
- `source_url`: Full original URL
- `scraped_at`: ISO timestamp when scraped
- `posted_date`: Date the job was posted
- `status`: "active"
- `title_raw`: Original job title
- `description_raw`: Full raw description text
- `description_clean`: Empty (filled in Stage 2)
- `language`: "fa", "en", or "mixed"
- `category`: Job category
- `company`: Company name
- `location`: City/location
- `salary_range`: Salary information (if available)
- `employment_type`: Full-time, part-time, etc.
- `experience_level`: Experience requirements
- `required_skills`: List of skills/tags
- `content_hash`: MD5 hash for deduplication
- `first_seen`: First scrape timestamp
- `last_seen`: Last scrape timestamp
- `scraper_run_id`: Unique batch identifier

## Politeness Settings

The scraper is configured to be very polite:

- ✅ Respects `robots.txt`
- ✅ AutoThrottle enabled (3-30s delay)
- ✅ Max 2 concurrent requests per domain
- ✅ 2s base download delay
- ✅ User agent identifies our bot
- ✅ HTTP caching enabled for development

These settings are in `backend/scrapers/settings.py`.

## Resuming Interrupted Crawls

Both spiders support resumption via `JOBDIR`:

```bash
# If a crawl is interrupted, resume with same JOBDIR
scrapy crawl jobvision_detail \
    -s JOBDIR=data/scrapy_jobs/detail_run1 \
    -o data/raw/jobvision_jobs_resumed.jsonl
```

The `JOBDIR` stores:
- Request queue state
- Seen URLs (to avoid duplicates)
- Crawl statistics

## Testing

### Test Phase 1 (Discovery)

```bash
# Run with small time window for quick test
scrapy crawl jobvision_discovery \
    -a days_ago=7 \
    -o data/raw/test_urls.jsonl \
    --loglevel=INFO

# Check output
wc -l data/raw/test_urls.jsonl
head -n 5 data/raw/test_urls.jsonl
```

### Test Phase 2 (Detail)

```bash
# Create a small test URL file (first 5 URLs from Phase 1)
head -n 5 data/raw/jobvision_urls_last50days.jsonl > data/raw/test_urls.jsonl

# Scrape just those 5 jobs
scrapy crawl jobvision_detail \
    -a url_file=data/raw/test_urls.jsonl \
    -s JOBDIR=data/scrapy_jobs/test_detail \
    -o data/raw/test_jobs.jsonl \
    --loglevel=INFO

# Inspect output
cat data/raw/test_jobs.jsonl | python -m json.tool | head -50
```

### Verify Extraction Quality

Check if JSON-LD data was found:

```bash
# Count jobs with titles
grep -c '"title_raw"' data/raw/jobvision_jobs_*.jsonl

# Sample a job posting
tail -n 1 data/raw/jobvision_jobs_*.jsonl | python -m json.tool
```

## Troubleshooting

### No URLs Found in Phase 1

1. Check if sitemap is accessible:
   ```bash
   curl -I https://jobvision.ir/sitemap/jobposts.xml
   ```

2. Check sitemap content:
   ```bash
   curl -s https://jobvision.ir/sitemap/jobposts.xml | head -50
   ```

3. Try a larger time window:
   ```bash
   scrapy crawl jobvision_discovery -a days_ago=90
   ```

### Poor Extraction in Phase 2

If you're getting empty fields:

1. **Check the actual HTML** of a job page:
   ```bash
   curl -s https://jobvision.ir/jobs/1234567/example > sample.html
   ```

2. **Look for JSON-LD**:
   ```bash
   grep -o '<script type="application/ld+json">[^<]*</script>' sample.html
   ```

3. **Look for ng-state**:
   ```bash
   grep 'id="ng-state"' sample.html
   ```

4. Update CSS selectors in `jobvision_detail.py` based on actual HTML structure.

### Soft Ban Detection

The middleware logs warnings if it detects:
- Suspiciously small responses (<500 bytes)
- Keywords like "captcha", "blocked", etc.

Check logs for these warnings. If you see many, increase delays or reduce concurrency.

## Next Steps (Stage 2)

After successfully scraping jobs:

1. **Clean & Normalize** (Stage 2):
   - Strip HTML from descriptions
   - Remove duplicates using `content_hash`
   - Normalize Persian text with Hazm
   - Create `description_clean` field

2. **Quality Check**:
   - Spot-check 20 random records
   - Verify all required fields are populated
   - Check language detection accuracy

## Notes

- **No personal data**: Phone numbers and private emails are not extracted
- **Streaming output**: Uses JSONL feeds to avoid memory issues
- **Resumable**: Can pause and resume crawls with `JOBDIR`
- **Type-hinted**: All code uses Python type hints
- **Tested**: Basic tests provided above

## Support

For issues or questions, check:
- Scrapy logs in the console
- `data/scrapy_jobs/<run_name>/stats.json` for crawl statistics
- This README for troubleshooting tips
