#!/bin/bash
# Run Phase 1: Discover recent job URLs from JobVision sitemap

set -e

cd "$(dirname "$0")/.."

DAYS_AGO=${1:-50}
OUTPUT_FILE="${2:-../data/raw/jobvision_urls_last${DAYS_AGO}days.jsonl}"
JOBDIR="../data/scrapy_jobs/discovery_${DAYS_AGO}d"

echo "========================================="
echo "JobVision Discovery Spider (Phase 1)"
echo "========================================="
echo "Looking back: ${DAYS_AGO} days"
echo "Output file:  ${OUTPUT_FILE}"
echo "Job directory: ${JOBDIR}"
echo ""

export PYTHONPATH="$(pwd)/..:$PYTHONPATH"

scrapy crawl jobvision_discovery \
    -a days_ago=${DAYS_AGO} \
    -o ${OUTPUT_FILE} \
    -s JOBDIR=${JOBDIR}

echo ""
echo "========================================="
echo "Discovery complete!"
echo "URLs found: $(wc -l < ${OUTPUT_FILE})"
echo "========================================="
