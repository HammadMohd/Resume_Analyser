# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project definition first for better caching
COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: Production image
FROM python:3.11-slim AS production

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY backend/ backend/
COPY frontend/ frontend/

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
