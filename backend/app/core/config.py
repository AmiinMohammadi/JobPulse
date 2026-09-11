"""
Job Pulse Backend - Core Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "Job Pulse"
    debug: bool = True
    log_level: str = "INFO"
    
    # Google Gemini API
    gemini_api_key: str
    
    # ChromaDB
    chroma_persist_dir: str = "./data/chroma"
    
    # File Upload
    max_upload_size_mb: int = 10
    
    # Embedding Model
    embedding_model: str = "BAAI/bge-m3"
    
    # API
    api_v1_prefix: str = "/api/v1"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
