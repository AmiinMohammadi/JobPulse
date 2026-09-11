"""
Pydantic models for request/response schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============ Resume Analysis ============

class ResumeAnalysisRequest(BaseModel):
    """Request schema for resume analysis."""
    resume_text: str = Field(..., description="Extracted resume text")
    
    class Config:
        json_schema_extra = {
            "example": {
                "resume_text": "John Doe\nSoftware Engineer\nSkills: Python, FastAPI, React..."
            }
        }


class JobMatch(BaseModel):
    """Single job match result."""
    job_id: str
    title: str
    company: str
    city: str
    salary: Optional[str] = None
    match_score: float = Field(..., ge=0.0, le=1.0, description="Match score between 0 and 1")
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    explanation: str = Field(..., description="Short AI-generated explanation")
    source_url: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_123",
                "title": "Senior Python Developer",
                "company": "Tech Corp",
                "city": "Tehran",
                "salary": "40-60M Toman",
                "match_score": 0.85,
                "matched_skills": ["Python", "FastAPI", "Docker"],
                "missing_skills": ["Kubernetes", "CI/CD"],
                "explanation": "Strong match with excellent Python skills. Consider learning DevOps tools."
            }
        }


class SkillGapSummary(BaseModel):
    """Aggregate skill gap summary."""
    top_missing_skills: List[Dict[str, Any]] = Field(
        ..., 
        description="List of most common missing skills with counts"
    )
    top_required_skills: List[Dict[str, Any]] = Field(
        ...,
        description="List of most in-demand skills in matched jobs"
    )
    market_insights: str = Field(..., description="AI-generated market insight summary")
    
    class Config:
        json_schema_extra = {
            "example": {
                "top_missing_skills": [
                    {"skill": "Docker", "count": 5},
                    {"skill": "Kubernetes", "count": 3}
                ],
                "top_required_skills": [
                    {"skill": "Python", "count": 8},
                    {"skill": "FastAPI", "count": 6}
                ],
                "market_insights": "The market shows high demand for Python developers with DevOps experience."
            }
        }


class ResumeAnalysisResponse(BaseModel):
    """Complete response for resume analysis."""
    success: bool
    message: str
    total_jobs_analyzed: int
    ranked_jobs: List[JobMatch]
    skill_gap_summary: Optional[SkillGapSummary] = None
    processing_time_seconds: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Analysis completed successfully",
                "total_jobs_analyzed": 50,
                "ranked_jobs": [],
                "skill_gap_summary": {},
                "processing_time_seconds": 3.5
            }
        }


# ============ Job Management ============

class JobPosting(BaseModel):
    """Job posting schema."""
    id: str
    title: str
    company: str
    city: str
    salary: Optional[str] = None
    description: str
    requirements: List[str] = []
    skills: List[str] = []
    source_url: Optional[str] = None
    posted_date: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "job_123",
                "title": "Senior Python Developer",
                "company": "Tech Corp",
                "city": "Tehran",
                "salary": "40-60M Toman",
                "description": "We are looking for...",
                "requirements": ["5+ years experience", "BS in CS"],
                "skills": ["Python", "FastAPI", "PostgreSQL"],
                "source_url": "https://example.com/job/123"
            }
        }


class JobIngestRequest(BaseModel):
    """Request to ingest a single job posting."""
    title: str
    company: str
    city: str
    salary: Optional[str] = None
    description: str
    requirements: List[str] = []
    skills: List[str] = []
    source_url: Optional[str] = None


class JobIngestResponse(BaseModel):
    """Response after ingesting jobs."""
    success: bool
    jobs_ingested: int
    message: str


# ============ Health & Stats ============

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    chromadb_connected: bool
    gemini_available: bool


class StatsResponse(BaseModel):
    """System statistics."""
    total_jobs_in_db: int
    total_resumes_analyzed: int
    last_job_update: Optional[datetime] = None
