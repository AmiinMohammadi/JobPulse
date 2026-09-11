# Job Pulse Backend

FastAPI backend for Job Pulse - RAG-powered resume analysis for the Iranian job market.

## Setup

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your Gemini API key
```

Get your Gemini API key from: https://makersuite.google.com/app/apikey

### 4. Run the Server

```bash
# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the main.py directly
python app/main.py
```

## API Documentation

Once running, access the interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root endpoint |
| GET | `/api/v1/health` | Health check |
| GET | `/api/v1/stats` | System statistics |
| POST | `/api/v1/analyze` | Analyze resume text |
| POST | `/api/v1/analyze/upload` | Upload and analyze resume file |
| POST | `/api/v1/jobs/ingest` | Ingest job postings |
| GET | `/api/v1/jobs` | List jobs |
| GET | `/api/v1/jobs/{id}` | Get job details |
| GET | `/api/v1/market/stats` | Market statistics |

## Project Structure

```
backend/
├── app/
│   ├── api/          # API routes
│   │   ├── health.py
│   │   ├── analysis.py
│   │   └── jobs.py
│   ├── core/         # Core configuration
│   │   ├── config.py
│   │   └── logging.py
│   ├── models/       # Pydantic schemas
│   │   └── schemas.py
│   ├── services/     # Business logic
│   │   ├── chroma_service.py
│   │   ├── embedding_service.py
│   │   ├── resume_parser.py
│   │   ├── gemini_service.py
│   │   └── rag_pipeline.py
│   └── main.py       # Application entry point
├── data/             # Persistent data (ChromaDB)
├── logs/             # Log files
├── tests/            # Test files
├── requirements.txt
├── .env.example
└── README.md
```

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

The project uses type hints throughout. Ensure proper typing for all functions.

## Notes

- The embedding model (`BAAI/bge-m3`) will be downloaded on first run (~2GB)
- ChromaDB stores data persistently in `./data/chroma`
- Gemini API requires a valid API key (free tier available)
- Maximum resume file size: 10MB
- Supported resume formats: PDF, DOCX, TXT, MD
