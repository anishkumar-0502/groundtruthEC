#!/usr/bin/env bash
# ==============================================================================
# Ground Truth — TNREGINET EC Retrieval Service Startup Script
# ==============================================================================
set -e

# Navigate to project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================================================"
echo " Ground Truth — TNREGINET Encumbrance Certificate Retrieval Service"
echo "========================================================================"

# Auto-detect or activate virtual environment
if [ -d ".venv" ]; then
    echo "Activating virtual environment (.venv)..."
    source .venv/bin/activate
elif [ -d "venv" ]; then
    echo "Activating virtual environment (venv)..."
    source venv/bin/activate
else
    echo "Creating virtual environment (.venv)..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "Installing dependencies from requirements.txt..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Load environment configuration if available
if [ -f ".env" ]; then
    echo "Loading configuration from .env..."
    export $(grep -v '^#' .env | xargs)
fi

HOST="${APP_HOST:-0.0.0.0}"
PORT="${APP_PORT:-8000}"

echo "Starting FastAPI server on http://${HOST}:${PORT}..."
echo "Swagger UI Documentation: http://localhost:${PORT}/docs"
echo "Demonstration UI:         http://localhost:${PORT}/"
echo "------------------------------------------------------------------------"

# Note: Single worker with auto-reload for local development
exec uvicorn app.main:app --host "$HOST" --port "$PORT" --reload

