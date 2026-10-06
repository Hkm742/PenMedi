#!/bin/sh
set -e

echo "=== Starting PM-CDSS Backend Service ==="

# Run Alembic migrations automatically on container start
echo "Applying database schema migrations..."
alembic upgrade head

# Run seed script if AUTO_SEED is true (useful for initial cloud / local provisioning)
if [ "$AUTO_SEED" = "true" ]; then
    echo "AUTO_SEED is enabled. Running database seed script..."
    python -m app.scripts.seed || echo "Seed script completed or skipped existing records."
fi

# Render dynamically passes $PORT, default to 8000 for local docker
PORT="${PORT:-8000}"
echo "Starting Uvicorn HTTP server on 0.0.0.0:${PORT}..."
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
