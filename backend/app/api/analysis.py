"""
Resume analysis endpoints
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Optional
import time
from app.models.schemas import (
    ResumeAnalysisRequest,
    ResumeAnalysisResponse,
    JobMatch,
    SkillGapSummary,
)
from app.core import logger
from app.services import get_rag_pipeline_service, get_resume_parser_service

router = APIRouter(tags=["Analysis"])


@router.post("/analyze", response_model=ResumeAnalysisResponse)
async def analyze_resume(
    request: ResumeAnalysisRequest,
    background_tasks: BackgroundTasks,
):
    """
    Analyze resume against job market.
    
    Accepts resume text and returns:
    - Ranked list of matching jobs with scores
    - Matched and missing skills for each job
    - Aggregate skill-gap summary
    """
    start_time = time.time()
    
    try:
        rag_service = get_rag_pipeline_service()
        
        # Run analysis
        result = rag_service.analyze_resume(
            resume_text=request.resume_text,
            top_k_jobs=20,
            top_n_results=10,
        )
        
        # Format response
        ranked_jobs = [
            JobMatch(
                job_id=job.get("job_id", "unknown"),
                title=job.get("title", "Unknown"),
                company=job.get("company", "Unknown"),
                city=job.get("city", "Unknown"),
                salary=job.get("salary"),
                match_score=job.get("match_score", 0.0),
                matched_skills=job.get("matched_skills", []),
                missing_skills=job.get("missing_skills", []),
                explanation=job.get("explanation", ""),
                source_url=None,
            )
            for job in result.get("ranked_jobs", [])
        ]
        
        skill_gap = result.get("skill_gap_summary")
        skill_gap_summary = None
        if skill_gap:
            skill_gap_summary = SkillGapSummary(
                top_missing_skills=skill_gap.get("top_missing_skills", []),
                top_required_skills=skill_gap.get("top_required_skills", []),
                market_insights=skill_gap.get("market_insights", ""),
            )
        
        processing_time = time.time() - start_time
        
        return ResumeAnalysisResponse(
            success=True,
            message="تحلیل با موفقیت انجام شد",
            total_jobs_analyzed=result.get("jobs_retrieved", 0),
            ranked_jobs=ranked_jobs,
            skill_gap_summary=skill_gap_summary,
            processing_time_seconds=round(processing_time, 2),
        )
    
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze/upload", response_model=ResumeAnalysisResponse)
async def analyze_resume_upload(
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, TXT)"),
):
    """
    Upload resume file and analyze against job market.
    
    Supported formats: PDF, DOCX, TXT, MD
    Maximum size: 10MB
    """
    start_time = time.time()
    
    try:
        # Validate and read file
        file_bytes = await file.read()
        
        if not file_bytes:
            raise HTTPException(status_code=400, detail="Empty file uploaded")
        
        # Validate file
        parser_service = get_resume_parser_service()
        parser_service.validate_file(
            file_bytes=file_bytes,
            filename=file.filename or "resume",
            max_size_mb=10,
        )
        
        # Extract text
        logger.info(f"Extracting text from {file.filename}")
        resume_text = parser_service.extract_resume(
            file_bytes=file_bytes,
            filename=file.filename or "resume",
        )
        
        if not resume_text.strip():
            raise HTTPException(
                status_code=400, 
                detail="No text could be extracted from the file. It may be a scanned/image-only PDF."
            )
        
        # Run analysis
        rag_service = get_rag_pipeline_service()
        result = rag_service.analyze_resume(
            resume_text=resume_text,
            top_k_jobs=20,
            top_n_results=10,
        )
        
        # Format response
        ranked_jobs = [
            JobMatch(
                job_id=job.get("job_id", "unknown"),
                title=job.get("title", "Unknown"),
                company=job.get("company", "Unknown"),
                city=job.get("city", "Unknown"),
                salary=job.get("salary"),
                match_score=job.get("match_score", 0.0),
                matched_skills=job.get("matched_skills", []),
                missing_skills=job.get("missing_skills", []),
                explanation=job.get("explanation", ""),
                source_url=None,
            )
            for job in result.get("ranked_jobs", [])
        ]
        
        skill_gap = result.get("skill_gap_summary")
        skill_gap_summary = None
        if skill_gap:
            skill_gap_summary = SkillGapSummary(
                top_missing_skills=skill_gap.get("top_missing_skills", []),
                top_required_skills=skill_gap.get("top_required_skills", []),
                market_insights=skill_gap.get("market_insights", ""),
            )
        
        processing_time = time.time() - start_time
        
        return ResumeAnalysisResponse(
            success=True,
            message="تحلیل رزومه با موفقیت انجام شد",
            total_jobs_analyzed=result.get("jobs_retrieved", 0),
            ranked_jobs=ranked_jobs,
            skill_gap_summary=skill_gap_summary,
            processing_time_seconds=round(processing_time, 2),
        )
    
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"File validation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
