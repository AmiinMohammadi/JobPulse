"""
Job management endpoints (ingestion, retrieval)
"""
from fastapi import APIRouter, HTTPException, Body
from typing import List
from app.models.schemas import (
    JobIngestRequest,
    JobIngestResponse,
    JobPosting,
)
from app.core import logger
from app.services import get_rag_pipeline_service, get_chroma_service

router = APIRouter(tags=["Jobs"])


@router.post("/jobs/ingest", response_model=JobIngestResponse)
async def ingest_jobs(jobs: List[JobIngestRequest]):
    """
    Ingest job postings into the vector database.
    
    This endpoint is used to populate the job database.
    In production, this would be called by a job scraper/crawler.
    """
    try:
        rag_service = get_rag_pipeline_service()
        
        # Convert Pydantic models to dicts and add IDs
        jobs_data = []
        for i, job in enumerate(jobs):
            job_dict = job.model_dump()
            # Generate ID if not provided
            if "id" not in job_dict or not job_dict["id"]:
                import uuid
                job_dict["id"] = f"auto_{uuid.uuid4().hex[:8]}"
            jobs_data.append(job_dict)
        
        count = rag_service.ingest_jobs(jobs_data)
        
        return JobIngestResponse(
            success=True,
            jobs_ingested=count,
            message=f"Successfully ingested {count} jobs",
        )
    
    except Exception as e:
        logger.error(f"Job ingestion failed: {e}")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")


@router.get("/jobs", response_model=List[JobPosting])
async def list_jobs(limit: int = 20, offset: int = 0):
    """
    List job postings from the database.
    
    For browsing available jobs in the system.
    """
    try:
        chroma_service = get_chroma_service()
        all_jobs = chroma_service.get_all_jobs(limit=limit + offset)
        
        # Skip offset
        if offset > 0:
            all_jobs = all_jobs[offset:]
        
        # Format response
        jobs = []
        for job in all_jobs[:limit]:
            metadata = job.get('metadata', {})
            jobs.append(
                JobPosting(
                    id=job.get('id', 'unknown').replace('job_', ''),
                    title=metadata.get('title', 'Unknown'),
                    company=metadata.get('company', 'Unknown'),
                    city=metadata.get('city', 'Unknown'),
                    salary=metadata.get('salary'),
                    description=job.get('document', ''),
                    requirements=[],
                    skills=[s.strip() for s in metadata.get('skills', '').split(',') if s.strip()],
                    source_url=metadata.get('source_url'),
                )
            )
        
        return jobs
    
    except Exception as e:
        logger.error(f"Failed to list jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve jobs")


@router.get("/jobs/{job_id}", response_model=JobPosting)
async def get_job(job_id: str):
    """Get details of a specific job."""
    try:
        chroma_service = get_chroma_service()
        all_jobs = chroma_service.get_all_jobs(limit=1000)
        
        # Find job by ID
        target_job = None
        for job in all_jobs:
            if job.get('id', '').replace('job_', '') == job_id:
                target_job = job
                break
        
        if not target_job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        metadata = target_job.get('metadata', {})
        
        return JobPosting(
            id=target_job.get('id', 'unknown').replace('job_', ''),
            title=metadata.get('title', 'Unknown'),
            company=metadata.get('company', 'Unknown'),
            city=metadata.get('city', 'Unknown'),
            salary=metadata.get('salary'),
            description=target_job.get('document', ''),
            requirements=[],
            skills=[s.strip() for s in metadata.get('skills', '').split(',') if s.strip()],
            source_url=metadata.get('source_url'),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get job {job_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve job")


@router.get("/market/stats")
async def get_market_stats():
    """Get aggregate market statistics."""
    try:
        rag_service = get_rag_pipeline_service()
        stats = rag_service.get_market_stats()
        return stats
    except Exception as e:
        logger.error(f"Failed to get market stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve market statistics")
