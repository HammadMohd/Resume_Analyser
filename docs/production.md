# Phase 12 — Production Readiness

## Overview
Production-ready features: rate limiting, metrics, CI/CD, optimized Docker, and security.

## Files Created/Modified

### `backend/middleware/rate_limit.py`
- In-memory rate limiter
- Configurable requests per minute
- Client IP detection (X-Forwarded-For support)
- 429 response with clear error message

### `backend/api/routes/metrics.py`
- `/metrics` endpoint for monitoring
- Uptime tracking
- Custom metric counters
- Human-readable uptime format

### `.github/workflows/ci.yml`
- CI/CD pipeline with GitHub Actions
- Runs on push/PR to master/main
- Steps: lint, type check, test, build Docker, push to DockerHub

### `docker/Dockerfile` (Optimized)
- Multi-stage build (builder → production)
- Non-root user (security)
- Health check built-in
- 4 uvicorn workers for production

### `backend/config/settings.py` (Updated)
- Added `workers` setting
- Added `rate_limit_per_minute`
- Added `api_key` for API security

### `tests/test_production.py`
- 9 tests for production features
- Rate limiting tests
- Metrics tests
- Health check tests

## Production Architecture

```
┌─────────────────────────────────────┐
│           Load Balancer             │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│     Rate Limiter (per IP)           │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│      Uvicorn (4 workers)            │
│  ┌───────────────────────────────┐  │
│  │ FastAPI App                   │  │
│  │ • 5 API routers               │  │
│  │ • Metrics endpoint            │  │
│  │ • Static file serving         │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

## Running in Production

### Docker Compose
```bash
docker-compose -f docker/docker-compose.yml up -d
```

### Manual
```bash
$env:ENVIRONMENT="production"
$env:RATE_LIMIT_PER_MINUTE="60"
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
1. Test Job:
   - Python 3.11 setup
   - Install dependencies
   - Ruff linter
   - MyPy type checker
   - Pytest tests
   - Codecov upload

2. Build Job (on push to main):
   - Docker Buildx
   - Push to DockerHub
   - GitHub Actions cache
```

## Security Features

| Feature | Implementation |
|---------|----------------|
| Rate Limiting | 60 req/min per IP |
| Non-root user | Docker container runs as appuser |
| CORS | Configurable origins |
| Health check | Built-in Docker healthcheck |

## Metrics Endpoint

```bash
GET /metrics
{
    "uptime_seconds": 3600.5,
    "uptime_human": "1h 0m 0s",
    "metrics": {
        "upload_count": 42,
        "analysis_count": 38
    }
}

POST /metrics/custom_metric
{"success": true, "metric": "custom_metric"}
```

## Learning Notes

### Multi-Stage Docker Build
```dockerfile
# Stage 1: Build dependencies (large image)
FROM python:3.11-slim AS builder
RUN pip install --prefix=/install ...

# Stage 2: Production (small image)
FROM python:3.11-slim AS production
COPY --from=builder /install /usr/local
# Only copies installed packages, not build tools
```

### Uvicorn Workers
```bash
# 1 worker = single process (development)
uvicorn app:app --workers 1

# 4 workers = 4 processes (production)
# Rule of thumb: workers = 2 * CPU cores + 1
uvicorn app:app --workers 4
```

### GitHub Actions Cache
```yaml
cache-from: type=gha    # GitHub Actions cache
cache-to: type=gha,mode=max
# Speeds up subsequent builds significantly
```
