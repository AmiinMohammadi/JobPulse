"""
RAG (Retrieval-Augmented Generation) pipeline service
Orchestrates resume analysis workflow
"""
from typing import List, Dict, Any, Optional
import time
from app.core import logger
from app.services import (
    get_embedding_service,
    get_chroma_service,
    get_gemini_service,
)


class RAGPipelineService:
    """Main RAG pipeline for resume-job matching."""
    
    def __init__(self):
        """Initialize RAG pipeline services."""
        self.embedding_service = get_embedding_service()
        self.chroma_service = get_chroma_service()
        self.gemini_service = get_gemini_service()
        
        logger.info("RAG Pipeline initialized")
    
    def analyze_resume(
        self,
        resume_text: str,
        top_k_jobs: int = 20,
        top_n_results: int = 10
    ) -> Dict[str, Any]:
        """
        Complete RAG pipeline for resume analysis.
        
        Args:
            resume_text: Extracted resume text
            top_k_jobs: Number of jobs to retrieve from vector DB
            top_n_results: Number of results to return after ranking
        
        Returns:
            Analysis results with ranked jobs and skill gaps
        """
        start_time = time.time()
        
        # Step 1: Generate embedding for resume
        logger.info("Generating resume embedding...")
        resume_embedding = self.embedding_service.generate_embedding(resume_text)
        
        # Step 2: Retrieve relevant jobs from ChromaDB
        logger.info(f"Retrieving top {top_k_jobs} jobs...")
        matched_jobs = self.chroma_service.search_jobs(
            query_embedding=resume_embedding,
            n_results=top_k_jobs
        )
        
        if not matched_jobs:
            logger.warning("No matching jobs found in database")
            return {
                "ranked_jobs": [],
                "skill_gap_summary": {
                    "top_missing_skills": [],
                    "top_required_skills": [],
                    "market_insights": "هیچ شغلی در پایگاه داده یافت نشد."
                }
            }
        
        logger.info(f"Found {len(matched_jobs)} matching jobs")
        
        # Step 3: Analyze with Gemini
        logger.info("Analyzing with Gemini...")
        analysis_result = self.gemini_service.analyze_resume_jobs(
            resume_text=resume_text,
            matched_jobs=matched_jobs,
            top_n=top_n_results
        )
        
        processing_time = time.time() - start_time
        logger.info(f"Analysis completed in {processing_time:.2f}s")
        
        return {
            "ranked_jobs": analysis_result.get("ranked_jobs", []),
            "skill_gap_summary": analysis_result.get("skill_gap_summary"),
            "total_jobs_in_db": self.chroma_service.get_job_count(),
            "jobs_retrieved": len(matched_jobs),
            "processing_time_seconds": round(processing_time, 2)
        }
    
    def ingest_jobs(self, jobs: List[Dict[str, Any]]) -> int:
        """
        Ingest job postings into the vector database.
        
        Args:
            jobs: List of job posting dictionaries with required fields:
                  - id, title, company, city, description, skills
        
        Returns:
            Number of jobs ingested
        """
        logger.info(f"Ingesting {len(jobs)} jobs...")
        
        # Prepare documents for embedding
        documents = [
            f"{job['title']} at {job['company']} in {job['city']}. "
            f"Skills: {', '.join(job.get('skills', []))}. "
            f"Description: {job['description']}"
            for job in jobs
        ]
        
        # Generate embeddings
        embeddings = self.embedding_service.generate_embeddings(documents)
        
        # Add to ChromaDB
        count = self.chroma_service.add_jobs(jobs, embeddings)
        
        logger.info(f"Successfully ingested {count} jobs")
        return count
    
    def get_market_stats(self) -> Dict[str, Any]:
        """Get basic market statistics from stored jobs."""
        total_jobs = self.chroma_service.get_job_count()
        
        if total_jobs == 0:
            return {
                "total_jobs": 0,
                "top_companies": [],
                "top_cities": [],
                "top_skills": []
            }
        
        # Get sample jobs for analysis
        all_jobs = self.chroma_service.get_all_jobs(limit=100)
        
        # Aggregate statistics
        companies = {}
        cities = {}
        skills = {}
        
        for job in all_jobs:
            metadata = job.get('metadata', {})
            
            # Companies
            company = metadata.get('company', 'Unknown')
            companies[company] = companies.get(company, 0) + 1
            
            # Cities
            city = metadata.get('city', 'Unknown')
            cities[city] = cities.get(city, 0) + 1
            
            # Skills
            skills_str = metadata.get('skills', '')
            for skill in [s.strip() for s in skills_str.split(',') if s.strip()]:
                skills[skill] = skills.get(skill, 0) + 1
        
        # Sort and get top items
        top_companies = sorted(companies.items(), key=lambda x: x[1], reverse=True)[:5]
        top_cities = sorted(cities.items(), key=lambda x: x[1], reverse=True)[:5]
        top_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_jobs": total_jobs,
            "top_companies": [{"name": name, "count": count} for name, count in top_companies],
            "top_cities": [{"name": name, "count": count} for name, count in top_cities],
            "top_skills": [{"name": name, "count": count} for name, count in top_skills]
        }


# Singleton instance
_rag_pipeline_service: Optional[RAGPipelineService] = None


def get_rag_pipeline_service() -> RAGPipelineService:
    """Get or create RAGPipelineService singleton."""
    global _rag_pipeline_service
    if _rag_pipeline_service is None:
        _rag_pipeline_service = RAGPipelineService()
    return _rag_pipeline_service
