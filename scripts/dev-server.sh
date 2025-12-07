#!/bin/bash
# Start Pattern Discovery Agent A2A Server locally

set -e

# Load environment variables from .env if exists
if [ -f .env ]; then
    echo "Loading environment variables from .env..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check required environment variables
REQUIRED_VARS=("ANTHROPIC_API_KEY" "GITHUB_TOKEN" "KNOWLEDGE_BASE_REPO")

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var environment variable not set"
        echo "Please create a .env file or set environment variables"
        exit 1
    fi
done

# Configuration
PORT="${PORT:-8080}"
HOST="${HOST:-0.0.0.0}"

echo "================================================"
echo "Starting Pattern Discovery Agent A2A Server"
echo "================================================"
echo "Host: ${HOST}"
echo "Port: ${PORT}"
echo
echo "AgentCard: http://localhost:${PORT}/.well-known/agent.json"
echo "Health:    http://localhost:${PORT}/health"
echo
echo "Press Ctrl+C to stop"
echo "================================================"
echo

# Run server with hot reload
uvicorn a2a.server:app \
    --host "${HOST}" \
    --port "${PORT}" \
    --reload \
    --log-level info
