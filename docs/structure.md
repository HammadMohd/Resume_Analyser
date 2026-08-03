# Project Structure

## Overview

```
Resume_Analyser/
├── backend/              → Backend application
│   ├── api/              → HTTP layer
│   │   └── routes/       → API endpoints
│   │       └── resume.py → Upload endpoint
│   ├── services/         → Business logic
│   │   ├── upload_service.py    → Upload orchestration
│   │   ├── validation_service.py → File validation
│   │   └── storage_service.py   → File storage
│   ├── schemas/          → Data models
│   │   └── upload.py     → Upload response schemas
│   ├── config/           → Configuration
│   │   └── settings.py   → App settings
│   ├── utils/            → Utilities
│   │   └── logging.py    → Logging setup
│   ├── exceptions.py     → Custom exceptions
│   └── main.py           → FastAPI app
├── tests/                → Test suite
│   ├── conftest.py       → Fixtures
│   ├── test_validation.py → Validation tests
│   ├── test_storage.py   → Storage tests
│   ├── test_upload.py    → Upload endpoint tests
│   └── test_integration.py → End-to-end tests
├── uploads/              → Uploaded files
│   └── resumes/          → Resume files
├── docker/               → Docker configuration
│   ├── Dockerfile        → Container build
│   └── docker-compose.yml → Services
├── docs/                 → Documentation
│   ├── api.md            → API docs
│   └── upload-workflow.md → Upload flow
├── pyproject.toml        → Dependencies
├── .env.example          → Environment template
├── .gitignore            → Git ignore rules
└── README.md             → Project overview
```

## Responsibility Map

| Folder | Responsibility |
|--------|----------------|
| `backend/api/routes/` | HTTP endpoints (thin) |
| `backend/services/` | Business logic |
| `backend/schemas/` | Data contracts |
| `backend/config/` | Settings |
| `backend/utils/` | Helpers |
| `tests/` | Test suite |
| `uploads/` | Stored files |
| `docs/` | Documentation |

## Dependency Flow

```
Router → Service → Infrastructure
  ↓         ↓           ↓
HTTP    Business    Filesystem
```

Dependencies flow downward only. No circular imports.

## Adding New Features

1. Define schema in `backend/schemas/`
2. Create service in `backend/services/`
3. Add endpoint in `backend/api/routes/`
4. Write tests in `tests/`
5. Update documentation in `docs/`
