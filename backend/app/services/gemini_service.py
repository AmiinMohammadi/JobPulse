"""
Google Gemini LLM service for job-resume analysis
"""
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from app.core.config import settings
from app.core import logger


class GeminiService:
    """Service for interacting with Google Gemini API."""
    
    def __init__(self):
        """Initialize Gemini client."""
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY not configured")
        
        genai.configure(api_key=settings.gemini_api_key)
        
        # Use Flash model (fast and cost-effective)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        logger.info("Gemini service initialized")
    
    def analyze_resume_jobs(
        self,
        resume_text: str,
        matched_jobs: List[Dict[str, Any]],
        top_n: int = 10
    ) -> Dict[str, Any]:
        """
        Analyze resume against matched jobs using Gemini.
        
        Args:
            resume_text: Full resume text
            matched_jobs: List of relevant jobs from RAG
            top_n: Number of top jobs to include in analysis
        
        Returns:
            Analysis results with ranked jobs and skill gaps
        """
        # Prepare jobs context
        jobs_context = self._format_jobs_for_prompt(matched_jobs[:top_n])
        
        # Create the analysis prompt (in Persian/English mix for better results)
        prompt = self._create_analysis_prompt(resume_text, jobs_context)
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=4096,
                ),
            )
            
            # Parse the response
            return self._parse_gemini_response(response.text)
        
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            # Fallback to simpler analysis
            return self._fallback_analysis(resume_text, matched_jobs[:top_n])
    
    def _format_jobs_for_prompt(self, jobs: List[Dict[str, Any]]) -> str:
        """Format jobs list for the prompt."""
        formatted = []
        for i, job in enumerate(jobs, 1):
            metadata = job.get('metadata', {})
            skills_str = metadata.get('skills', 'Not specified')
            formatted.append(
                f"Job {i}:\n"
                f"Title: {metadata.get('title', 'Unknown')}\n"
                f"Company: {metadata.get('company', 'Unknown')}\n"
                f"City: {metadata.get('city', 'Unknown')}\n"
                f"Salary: {metadata.get('salary', 'Not specified')}\n"
                f"Required Skills: {skills_str}\n"
                f"Description: {job.get('document', '')[:500]}...\n"
            )
        return "\n\n".join(formatted)
    
    def _create_analysis_prompt(self, resume_text: str, jobs_context: str) -> str:
        """Create the analysis prompt for Gemini."""
        return f"""You are an expert career advisor analyzing a job seeker's resume against real job postings from the Iranian job market.

## Task
Analyze the resume and provide detailed matching analysis with the provided job postings.

## Resume Text
{resume_text[:3000]}

## Relevant Job Postings
{jobs_context}

## Required Output Format (JSON)
Return ONLY valid JSON in this exact structure:

{{
  "ranked_jobs": [
    {{
      "job_id": "extract from job posting or use title",
      "title": "job title",
      "company": "company name",
      "city": "city",
      "salary": "salary info or null",
      "match_score": 0.85,
      "matched_skills": ["skill1", "skill2"],
      "missing_skills": ["skill3", "skill4"],
      "explanation": "Brief explanation in Persian (2-3 sentences)"
    }}
  ],
  "skill_gap_summary": {{
    "top_missing_skills": [
      {{"skill": "skill name", "count": 3}}
    ],
    "top_required_skills": [
      {{"skill": "skill name", "count": 5}}
    ],
    "market_insights": "Market insights in Persian (3-4 sentences about demand, trends, recommendations)"
  }}
}}

## Guidelines
1. Rank jobs by relevance and match quality (score 0.0 to 1.0)
2. Identify matched skills (present in both resume and job requirements)
3. Identify missing skills (required by job but not in resume)
4. Provide explanations in **Persian (Farsi)**
5. Be honest and constructive in feedback
6. Consider the Iranian job market context

Return ONLY the JSON, no additional text."""
    
    def _parse_gemini_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini's JSON response."""
        import json
        
        # Try to extract JSON from response (handle markdown code blocks)
        json_str = response_text.strip()
        
        # Remove markdown code blocks if present
        if json_str.startswith('```'):
            lines = json_str.split('\n')
            json_str = '\n'.join(lines[1:-1])  # Remove first and last lines
        
        # Find JSON object
        start_idx = json_str.find('{')
        end_idx = json_str.rfind('}') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_str = json_str[start_idx:end_idx]
        
        try:
            result = json.loads(json_str)
            logger.info("Successfully parsed Gemini response")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini JSON: {e}")
            raise ValueError("Failed to parse AI response")
    
    def _fallback_analysis(
        self, 
        resume_text: str, 
        matched_jobs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Fallback analysis when Gemini fails."""
        logger.warning("Using fallback analysis")
        
        # Simple keyword-based matching
        resume_lower = resume_text.lower()
        
        ranked_jobs = []
        all_skills = []
        missing_skills = []
        
        for job in matched_jobs:
            metadata = job.get('metadata', {})
            skills_str = metadata.get('skills', '').lower()
            job_skills = [s.strip() for s in skills_str.split(',') if s.strip()]
            
            # Simple matching
            matched = [s for s in job_skills if s.lower() in resume_lower]
            missing = [s for s in job_skills if s.lower() not in resume_lower]
            
            score = len(matched) / max(len(job_skills), 1) if job_skills else 0.5
            
            ranked_jobs.append({
                "job_id": job.get('id', 'unknown'),
                "title": metadata.get('title', 'Unknown'),
                "company": metadata.get('company', 'Unknown'),
                "city": metadata.get('city', 'Unknown'),
                "salary": metadata.get('salary'),
                "match_score": round(score, 2),
                "matched_skills": matched,
                "missing_skills": missing,
                "explanation": "تحلیل خودکار انجام شد. لطفاً برای تحلیل دقیق‌تر مجدد تلاش کنید."
            })
            
            all_skills.extend(job_skills)
            missing_skills.extend(missing)
        
        # Sort by score
        ranked_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Aggregate skills
        from collections import Counter
        skill_counts = Counter(all_skills)
        missing_counts = Counter(missing_skills)
        
        return {
            "ranked_jobs": ranked_jobs[:10],
            "skill_gap_summary": {
                "top_missing_skills": [
                    {"skill": skill, "count": count}
                    for skill, count in missing_counts.most_common(5)
                ],
                "top_required_skills": [
                    {"skill": skill, "count": count}
                    for skill, count in skill_counts.most_common(5)
                ],
                "market_insights": "تحلیل بازار با استفاده از روش ساده انجام شد."
            }
        }
    
    def generate_market_insights(
        self,
        all_jobs: List[Dict[str, Any]],
        resume_text: str
    ) -> str:
        """Generate general market insights based on all jobs."""
        prompt = f"""Based on these job postings from the Iranian job market, provide 3-4 sentences of market insights in Persian:

Jobs: {str(all_jobs[:20])}

Resume: {resume_text[:500]}

Provide insights about:
- In-demand skills
- Market trends
- Salary expectations
- Recommendations for the candidate

Respond in Persian only."""
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Failed to generate market insights: {e}")
            return "تحلیل بازار در دسترس نیست."


# Singleton instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create GeminiService singleton."""
    global _gemini_service
    if _gemini_service is None:
        try:
            _gemini_service = GeminiService()
        except ValueError as e:
            logger.error(f"Cannot initialize Gemini service: {e}")
            raise
    return _gemini_service
