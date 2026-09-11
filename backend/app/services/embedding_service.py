"""
Embedding service using sentence-transformers
"""
from typing import List, Optional
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.core import logger


class EmbeddingService:
    """Service for generating embeddings using multilingual models."""
    
    def __init__(self):
        """Initialize the embedding model."""
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        
        self.model = SentenceTransformer(
            settings.embedding_model,
            trust_remote_code=True,
        )
        
        logger.info("Embedding model loaded successfully")
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
        
        Returns:
            Embedding vector as list of floats
        """
        embedding = self.model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embedding.tolist()
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of input texts
        
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        embeddings = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            batch_size=32,
            show_progress_bar=len(texts) > 10,
        )
        
        return embeddings.tolist()
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding vectors."""
        return self.model.get_sentence_embedding_dimension()


# Singleton instance
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """Get or create EmbeddingService singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
