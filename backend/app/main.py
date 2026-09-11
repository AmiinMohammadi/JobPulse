"""
Job Pulse - FastAPI Backend Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core import settings, logger
from app.api import health, analysis, jobs


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title=settings.app_name,
        description="""
## Job Pulse API

RAG-powered resume analysis for the Iranian job market.

### Features
- **Resume Analysis**: Upload or paste resume text to get AI-powered job matching
- **Skill Gap Analysis**: Identify missing skills compared to market demands
- **Job Matching**: Get ranked list of relevant job postings
- **Market Insights**: Understand in-demand skills and trends

### Authentication
Currently no authentication required (MVP).
        """,
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    
    # Configure CORS for frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # Next.js dev
            "http://localhost:8000",  # Alternative
            "*",  # Allow all for MVP (restrict in production)
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(health.router, prefix=settings.api_v1_prefix)
    app.include_router(analysis.router, prefix=settings.api_v1_prefix)
    app.include_router(jobs.router, prefix=settings.api_v1_prefix)
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup."""
        logger.info(f"🚀 Starting {settings.app_name}...")
        logger.info(f"Debug mode: {settings.debug}")
        logger.info(f"API prefix: {settings.api_v1_prefix}")
        
        # Warm up services
        try:
            from app.services import get_chroma_service
            chroma = get_chroma_service()
            logger.info(f"✓ ChromaDB initialized with {chroma.get_job_count()} jobs")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
        
        try:
            from app.services import get_embedding_service
            embed = get_embedding_service()
            logger.info(f"✓ Embedding model loaded ({settings.embedding_model})")
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
        
        logger.info(f"✅ {settings.app_name} ready!")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown."""
        logger.info(f"👋 Shutting down {settings.app_name}...")
    
    @app.get("/")
    async def root():
        """Root endpoint with basic info."""
        return {
            "name": settings.app_name,
            "version": "0.1.0",
            "status": "running",
            "docs": "/docs",
        }
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
