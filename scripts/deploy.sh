#!/bin/bash
# Deploy Pattern Discovery Agent A2A Server to Cloud Run
# Supports multi-environment deployment
#
# Usage:
#   bash deploy.sh dev
#   bash deploy.sh staging
#   bash deploy.sh prod
#
# Or set environment variables:
#   export GCP_PROJECT_ID=your-project
#   export GCP_REGION=us-central1
#   bash deploy.sh dev

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="pattern-discovery-agent"
KNOWLEDGE_BASE_REPO="${KNOWLEDGE_BASE_REPO:-patelmm79/dev-nexus}"
ENVIRONMENT="${1:-dev}"

# Validation
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP_PROJECT_ID environment variable not set${NC}"
    echo "Usage: export GCP_PROJECT_ID=your-project-id"
    echo "       bash $0 [environment]"
    echo ""
    echo "Environments: dev, staging, prod (default: dev)"
    exit 1
fi

# Validate environment
case "$ENVIRONMENT" in
    dev|staging|prod)
        ;;
    *)
        echo -e "${RED}Error: Invalid environment '$ENVIRONMENT'${NC}"
        echo "Allowed values: dev, staging, prod"
        exit 1
        ;;
esac

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Deploying Pattern Discovery Agent to Cloud Run${NC}"
echo -e "${BLUE}================================================${NC}"
echo "Project:      $PROJECT_ID"
echo "Region:       $REGION"
echo "Service:      $SERVICE_NAME"
echo "KB Repo:      $KNOWLEDGE_BASE_REPO"
echo "Environment:  $ENVIRONMENT"
echo

# Build and deploy using Cloud Build with environment substitution
echo -e "${YELLOW}Starting Cloud Build...${NC}"
gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions="_REGION=${REGION},_ENVIRONMENT=${ENVIRONMENT},_KNOWLEDGE_BASE_REPO=${KNOWLEDGE_BASE_REPO}" \
    --project="${PROJECT_ID}"

# Get service URL
echo
echo -e "${YELLOW}Retrieving service URL...${NC}"
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
    --region=${REGION} \
    --project=${PROJECT_ID} \
    --format="value(status.url)")

echo
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}✓ Deployment complete!${NC}"
echo -e "${BLUE}================================================${NC}"
echo "Service URL:  ${SERVICE_URL}"
echo "AgentCard:    ${SERVICE_URL}/.well-known/agent.json"
echo "Health:       ${SERVICE_URL}/health"
echo ""
echo "Environment: $ENVIRONMENT"

case "$ENVIRONMENT" in
    dev)
        echo "Mode:        Development (unauthenticated, scale-to-zero)"
        echo "State:       Stored at: terraform-state-globalbiting-dev/dev-nexus/dev"
        echo "Secrets:     dev-nexus-dev_* in Secret Manager"
        ;;
    staging)
        echo "Mode:        Staging (authenticated, moderate resources)"
        echo "State:       Stored at: terraform-state-globalbiting-dev/dev-nexus/staging"
        echo "Secrets:     dev-nexus-staging_* in Secret Manager"
        ;;
    prod)
        echo "Mode:        Production (authenticated, HA, monitoring)"
        echo "State:       Stored at: terraform-state-globalbiting-dev/dev-nexus/prod"
        echo "Secrets:     dev-nexus-prod_* in Secret Manager"
        ;;
esac

echo

# Test health endpoint
echo -e "${YELLOW}Testing health endpoint...${NC}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/health")

if [ "$HTTP_STATUS" -eq 200 ]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}✗ Health check failed (HTTP ${HTTP_STATUS})${NC}"
fi

# Test AgentCard endpoint
echo -e "${YELLOW}Testing AgentCard endpoint...${NC}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/.well-known/agent.json")

if [ "$HTTP_STATUS" -eq 200 ]; then
    echo -e "${GREEN}✓ AgentCard endpoint available${NC}"
else
    echo -e "${RED}✗ AgentCard endpoint failed (HTTP ${HTTP_STATUS})${NC}"
fi

echo
echo -e "${GREEN}Deployment verified!${NC}"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  - Monitor logs: gcloud run services logs read ${SERVICE_NAME} --region=${REGION}"
echo "  - View environment: terraform output -var-file=\"terraform/${ENVIRONMENT}.tfvars\""
echo "  - Update Cloud Build triggers in GCP Console to deploy other environments"
