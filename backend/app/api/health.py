"""
Health check and system stats endpoints
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import HealthResponse, StatsResponse
from app.core import logger
from app.services import get_chroma_service, get_gemini_service

router = APIRouter(tags=["Health & Stats"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check system health status."""
    chromadb_ok = False
    gemini_ok = False
    
    try:
        chroma_service = get_chroma_service()
        chroma_service.get_job_count()
        chromadb_ok = True
    except Exception as e:
        logger.error(f"ChromaDB health check failed: {e}")
    
    try:
        gemini_service = get_gemini_service()
        # Simple test - just check if service is initialized
        gemini_ok = gemini_service.model is not None
    except Exception as e:
        logger.error(f"Gemini health check failed: {e}")
    
    return HealthResponse(
        status="healthy" if (chromadb_ok and gemini_ok) else "degraded",
        version="0.1.0",
        chromadb_connected=chromadb_ok,
        gemini_available=gemini_ok,
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics."""
    try:
        chroma_service = get_chroma_service()
        total_jobs = chroma_service.get_job_count()
        
        return StatsResponse(
            total_jobs_in_db=total_jobs,
            total_resumes_analyzed=0,  # TODO: Track in database
            last_job_update=None,
        )
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")
