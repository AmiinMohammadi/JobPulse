# Job Pulse – Project Structure & Status

## Overview
Job Pulse (جاب پالس) is a RAG-powered full-stack application for analyzing resumes against the Iranian job market.

## Current Status: ✅ Backend Complete

### Backend (`/backend`)
**Status:** Fully implemented and tested

#### Structure
```
backend/
├── app/
│   ├── api/              # REST API endpoints
│   │   ├── __init__.py
│   │   ├── health.py     # Health check & stats
│   │   ├── analysis.py   # Resume analysis endpoints
│   │   └── jobs.py       # Job management endpoints
│   ├── core/             # Core configuration
│   │   ├── __init__.py
│   │   ├── config.py     # Settings & env vars
│   │   └── logging.py    # Loguru setup
│   ├── models/           # Pydantic schemas
│   │   ├── __init__.py
│   │   └── schemas.py    # Request/Response models
│   ├── services/         # Business logic
│   │   ├── __init__.py
│   │   ├── chroma_service.py      # Vector DB operations
│   │   ├── embedding_service.py   # BGE-M3 embeddings
│   │   ├── resume_parser.py       # PDF/DOCX/TXT parsing
│   │   ├── gemini_service.py      # Google Gemini LLM
│   │   └── rag_pipeline.py        # Main RAG orchestration
│   └── main.py           # FastAPI app factory
├── data/                 # ChromaDB persistent storage
├── logs/                 # Application logs
├── tests/                # Test suite (to implement)
├── requirements.txt      # Python dependencies
├── .env.example          # Environment template
├── .env                  # Active configuration
└── README.md             # Setup instructions
```

#### Implemented Features
✅ FastAPI application with CORS support  
✅ ChromaDB vector store (persistent, local)  
✅ BGE-M3 embedding service (multilingual, Persian-ready)  
✅ Resume parser (PDF, DOCX, TXT, MD)  
✅ Google Gemini integration with fallback  
✅ RAG pipeline orchestration  
✅ Resume analysis endpoint (`POST /api/v1/analyze`)  
✅ File upload endpoint (`POST /api/v1/analyze/upload`)  
✅ Job ingestion endpoint (`POST /api/v1/jobs/ingest`)  
✅ Health check & statistics endpoints  
✅ Comprehensive error handling  
✅ Logging with Loguru  

#### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root info |
| GET | `/api/v1/health` | System health |
| GET | `/api/v1/stats` | Statistics |
| POST | `/api/v1/analyze` | Analyze resume text |
| POST | `/api/v1/analyze/upload` | Upload & analyze file |
| POST | `/api/v1/jobs/ingest` | Add jobs to DB |
| GET | `/api/v1/jobs` | List jobs |
| GET | `/api/v1/jobs/{id}` | Get job details |
| GET | `/api/v1/market/stats` | Market insights |

#### Requirements Met
- ✅ FastAPI framework
- ✅ ChromaDB (persistent, local)
- ✅ BAAI/bge-m3 embedding model
- ✅ Google Gemini API (2.0 Flash)
- ✅ Python 3.11+ compatible
- ✅ Type hints throughout
- ✅ Clean, decoupled architecture
- ✅ Swagger/OpenAPI docs at `/docs`

---

## Next Steps: Frontend Development

### Frontend (`/frontend`)
**Status:** Not yet started

#### Planned Stack
- Next.js (App Router)
- TypeScript
- Tailwind CSS + shadcn/ui
- RTL-first with Vazirmatn font
- Light/Dark theme support

#### To Implement
1. **Setup**
   - `npx create-next-app@latest` with TypeScript
   - Configure Tailwind CSS
   - Install shadcn/ui components
   - Set up RTL direction
   - Add Vazirmatn font

2. **Pages**
   - Landing page (value prop + CTA)
   - Resume upload page (file + text paste)
   - Loading state page
   - Results page (job cards + skill gaps)
   - Job detail page

3. **Components**
   - Theme toggle (light/dark)
   - RTL layout wrapper
   - Job card component
   - Skill tag component
   - Loading spinner
   - Error boundary

4. **Integration**
   - API client for backend
   - File upload handling
   - State management
   - Error handling

---

## System Requirements

### Backend
- Python 3.11+
- 4GB+ RAM (for embedding model)
- 5GB+ disk space
- Google Gemini API key (free tier)

### Frontend
- Node.js 18+
- npm or pnpm
- Modern browser

---

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add GEMINI_API_KEY
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Access API docs: http://localhost:8000/docs

### Frontend (To Do)
```bash
cd frontend
# Will be implemented next
```

---

## Notes

1. **Memory**: The BGE-M3 model requires ~2GB RAM. In low-memory environments, consider:
   - Using a smaller model (`paraphrase-multilingual-MiniLM-L12-v2`)
   - Running on a machine with more RAM
   - Using cloud-based embeddings

2. **Gemini API**: Free tier available. Get key from https://makersuite.google.com/app/apikey

3. **ChromaDB**: Stores data persistently in `./data/chroma`. Safe to delete for fresh start.

4. **Persian Support**: All services are configured for multilingual/Persian text processing.

---

## Development Order Completed

1. ✅ Backend foundation (FastAPI, config, logging)
2. ✅ Services (ChromaDB, embeddings, parser, Gemini, RAG)
3. ✅ API routes (health, analysis, jobs)
4. ✅ Documentation and testing
5. ⏳ Frontend (Next.js) - **Next phase**

---

*Generated: $(date)*  
*Project: Job Pulse MVP*
