# Stage 1: Build dependencies
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY backend/ backend/

RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: Production image
FROM python:3.11-slim AS production

WORKDIR /app

COPY --from=builder /install /usr/local

COPY backend/ backend/
COPY frontend/ frontend/
COPY start.sh .

RUN chmod +x start.sh && \
    groupadd -r appuser && useradd -r -g appuser -d /app appuser && \
    mkdir -p /app/uploads && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["./start.sh"]
