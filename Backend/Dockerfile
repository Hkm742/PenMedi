# Multi-stage Dockerfile for FastAPI Backend using Astral uv
FROM ghcr.io/astral-sh/uv:0.6.1-python3.12-bookworm-slim AS builder

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy project definition
COPY pyproject.toml .

# Install dependencies using uv sync without the project itself
RUN uv sync --no-dev --no-install-project

# Runtime stage
FROM python:3.12-slim-bookworm AS runtime

WORKDIR /app

# Install curl for healthcheck and libpq for PostgreSQL runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Environment variable to use the virtualenv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Copy application code and alembic migrations
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY app /app/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
