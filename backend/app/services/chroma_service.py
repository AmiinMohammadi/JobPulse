"""
ChromaDB vector store service for job embeddings
"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from app.core.config import settings
from app.core import logger


class ChromaService:
    """Service for managing ChromaDB vector store."""
    
    def __init__(self):
        """Initialize ChromaDB client and collection."""
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        
        # Get or create the jobs collection
        self.collection = self.client.get_or_create_collection(
            name="job_postings",
            metadata={"description": "Iranian job postings for RAG"}
        )
        
        logger.info(f"ChromaDB initialized with {self.collection.count()} documents")
    
    def add_jobs(self, jobs: List[Dict[str, Any]], embeddings: List[List[float]]) -> int:
        """
        Add job postings to the vector store.
        
        Args:
            jobs: List of job posting dictionaries
            embeddings: List of embedding vectors (same length as jobs)
        
        Returns:
            Number of jobs added
        """
        if len(jobs) != len(embeddings):
            raise ValueError("Jobs and embeddings must have the same length")
        
        ids = [f"job_{job['id']}" for job in jobs]
        metadatas = [
            {
                "title": job["title"],
                "company": job["company"],
                "city": job["city"],
                "salary": job.get("salary", ""),
                "skills": ",".join(job.get("skills", [])),
                "source_url": job.get("source_url", ""),
            }
            for job in jobs
        ]
        documents = [job["description"] for job in jobs]
        
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )
        
        logger.info(f"Added {len(jobs)} jobs to ChromaDB")
        return len(jobs)
    
    def search_jobs(
        self, 
        query_embedding: List[float], 
        n_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for relevant jobs using query embedding.
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
        
        Returns:
            List of matching job documents with metadata and distances
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )
        
        if not results["ids"] or not results["ids"][0]:
            return []
        
        # Format results
        formatted_results = []
        for i, job_id in enumerate(results["ids"][0]):
            job_data = {
                "id": job_id.replace("job_", ""),
                "document": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0.0,
            }
            formatted_results.append(job_data)
        
        return formatted_results
    
    def get_job_count(self) -> int:
        """Get total number of jobs in the database."""
        return self.collection.count()
    
    def get_all_jobs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve all jobs from the database.
        
        Args:
            limit: Maximum number of jobs to return
        
        Returns:
            List of job documents with metadata
        """
        results = self.collection.get(
            limit=limit,
            include=["documents", "metadatas"],
        )
        
        if not results["ids"]:
            return []
        
        formatted_jobs = []
        for i, job_id in enumerate(results["ids"]):
            job_data = {
                "id": job_id.replace("job_", ""),
                "document": results["documents"][i] if results["documents"] else "",
                "metadata": results["metadatas"][i] if results["metadatas"] else {},
            }
            formatted_jobs.append(job_data)
        
        return formatted_jobs
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job by ID."""
        try:
            self.collection.delete(ids=[f"job_{job_id}"])
            logger.info(f"Deleted job {job_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            return False
    
    def reset_collection(self) -> None:
        """Reset the collection (delete all jobs). Use with caution."""
        self.client.delete_collection("job_postings")
        self.collection = self.client.get_or_create_collection(
            name="job_postings",
            metadata={"description": "Iranian job postings for RAG"}
        )
        logger.warning("ChromaDB collection reset")


# Singleton instance
_chroma_service: Optional[ChromaService] = None


def get_chroma_service() -> ChromaService:
    """Get or create ChromaService singleton."""
    global _chroma_service
    if _chroma_service is None:
        _chroma_service = ChromaService()
    return _chroma_service
