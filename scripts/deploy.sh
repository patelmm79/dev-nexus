#!/bin/bash
# Deploy Pattern Discovery Agent A2A Server to Cloud Run

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="pattern-discovery-agent"
KNOWLEDGE_BASE_REPO="${KNOWLEDGE_BASE_REPO:-patelmm79/dev-nexus}"

# Validation
if [ -z "$PROJECT_ID" ]; then
    echo "Error: GCP_PROJECT_ID environment variable not set"
    echo "Usage: export GCP_PROJECT_ID=your-project-id"
    exit 1
fi

echo "================================================"
echo "Deploying Pattern Discovery Agent to Cloud Run"
echo "================================================"
echo "Project:  $PROJECT_ID"
echo "Region:   $REGION"
echo "Service:  $SERVICE_NAME"
echo "KB Repo:  $KNOWLEDGE_BASE_REPO"
echo

# Get current git commit SHA (or use timestamp if not in git repo)
if git rev-parse HEAD >/dev/null 2>&1; then
    COMMIT_SHA=$(git rev-parse --short HEAD)
else
    COMMIT_SHA=$(date +%Y%m%d-%H%M%S)
fi

echo "Image tag: $COMMIT_SHA"
echo

# Build and deploy using Cloud Build
echo "Starting Cloud Build..."
gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions="_REGION=${REGION},_KNOWLEDGE_BASE_REPO=${KNOWLEDGE_BASE_REPO},COMMIT_SHA=${COMMIT_SHA}" \
    --project="${PROJECT_ID}"

# Get service URL
echo
echo "Retrieving service URL..."
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(status.url)")

echo
echo "================================================"
echo "Deployment complete!"
echo "================================================"
echo "Service URL:  ${SERVICE_URL}"
echo "AgentCard:    ${SERVICE_URL}/.well-known/agent.json"
echo "Health:       ${SERVICE_URL}/health"
echo

# Test health endpoint
echo "Testing health endpoint..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/health")

if [ "$HTTP_STATUS" -eq 200 ]; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed (HTTP ${HTTP_STATUS})"
fi

# Test AgentCard endpoint
echo "Testing AgentCard endpoint..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/.well-known/agent.json")

if [ "$HTTP_STATUS" -eq 200 ]; then
    echo "✓ AgentCard endpoint available"
else
    echo "✗ AgentCard endpoint failed (HTTP ${HTTP_STATUS})"
fi

echo
echo "Deployment verified!"
