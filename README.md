# Resume Analyzer

Deterministic-First ATS Resume Analyzer — a production-grade system that parses, validates, scores, and refumes resumes using deterministic engineering first, LLM only for final editing.

## Architecture

```
Client → Upload → Validate → Store → Parse → Extract → Score → LLM Refine → Dashboard
```

## Current Status

**Phase 2 Complete** — Upload system with validation, storage, and metadata.

## Quick Start

```bash
# Clone and setup
git clone <repo-url>
cd Resume_Analyser
python -m venv .venv
.venv\Scripts\activate
pip install "fastapi[standard]"

# Run server
fastapi dev backend/main.py

# Run tests
python -m pytest tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/resumes/` | Upload a resume (PDF/DOCX) |
| GET | `/health` | Health check |

## Upload Response

```json
{
  "success": true,
  "message": "File uploaded and stored successfully",
  "data": {
    "id": "uuid",
    "original_filename": "resume.pdf",
    "stored_filename": "uuid.pdf",
    "content_type": "application/pdf",
    "size_bytes": 12345,
    "upload_timestamp": "2026-08-03T14:00:00Z"
  }
}
```

## Project Structure

```
Resume_Analyser/
├── backend/
│   ├── api/routes/     → HTTP endpoints
│   ├── services/       → Business logic
│   ├── schemas/        → Pydantic models
│   ├── config/         → Settings
│   ├── utils/          → Logging, helpers
│   ├── exceptions.py   → Custom exceptions
│   └── main.py         → App entry point
├── tests/              → Test suite
├── uploads/            → Stored files
├── docker/             → Docker config
└── docs/               → Documentation
```

## Tech Stack

- **Backend:** FastAPI, Python 3.11+
- **Validation:** Pydantic
- **Storage:** Local filesystem with UUID filenames
- **Testing:** pytest

## Development

```bash
# Install dependencies
pip install "fastapi[standard]" pytest pytest-asyncio httpx

# Run tests
python -m pytest tests/ -v

# Run server with debug
$env:DEBUG="true"; fastapi dev backend/main.py
```

## License

MIT
