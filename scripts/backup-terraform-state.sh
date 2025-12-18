#!/bin/bash
# Terraform State Backup Script
#
# Backs up Terraform state for all environments to GCS backup bucket
# Useful for manual backups before risky operations
#
# Usage:
#   bash backup-terraform-state.sh [environment]
#   bash backup-terraform-state.sh         # Backup all environments
#   bash backup-terraform-state.sh dev     # Backup dev only
#   bash backup-terraform-state.sh prod    # Backup prod only

set -e

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-globalbiting-dev}"
STATE_BUCKET="terraform-state-${PROJECT_ID}"
BACKUP_BUCKET="${STATE_BUCKET}-backups"
ENVIRONMENTS=("dev" "staging" "prod")
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Filter to specific environment if provided
if [ -n "$1" ]; then
    ENVIRONMENTS=("$1")
    # Validate environment
    case "$1" in
        dev|staging|prod)
            ;;
        *)
            echo "Invalid environment: $1"
            echo "Allowed: dev, staging, prod"
            exit 1
            ;;
    esac
fi

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Terraform State Backup${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo "Project:       $PROJECT_ID"
echo "State Bucket:  $STATE_BUCKET"
echo "Backup Bucket: $BACKUP_BUCKET"
echo "Timestamp:     $TIMESTAMP"
echo ""

# Verify backup bucket exists
if ! gsutil ls -b "gs://$BACKUP_BUCKET/" &>/dev/null; then
    echo -e "${YELLOW}Creating backup bucket: $BACKUP_BUCKET${NC}"
    gsutil mb -p "$PROJECT_ID" "gs://$BACKUP_BUCKET/"
fi

# Backup each environment
FAILED=0
for ENV in "${ENVIRONMENTS[@]}"; do
    echo -e "${YELLOW}Backing up $ENV environment...${NC}"

    STATE_PATH="gs://$STATE_BUCKET/dev-nexus/$ENV/default.tfstate"
    BACKUP_PATH="gs://$BACKUP_BUCKET/dev-nexus-${ENV}-${TIMESTAMP}.tfstate"

    # Check if state exists
    if gsutil ls "$STATE_PATH" &>/dev/null; then
        if gsutil cp "$STATE_PATH" "$BACKUP_PATH"; then
            echo -e "${GREEN}✓${NC} $ENV state backed up to: $BACKUP_PATH"
        else
            echo -e "${YELLOW}✗${NC} Failed to backup $ENV state"
            FAILED=$((FAILED + 1))
        fi
    else
        echo -e "${YELLOW}ℹ${NC} $ENV state not found (not initialized yet)"
    fi
done

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}Backup Summary${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# List recent backups
echo "Recent backups in $BACKUP_BUCKET:"
echo ""
gsutil ls -h "gs://$BACKUP_BUCKET/" | tail -10

echo ""
echo -e "${BLUE}Restore Instructions:${NC}"
echo ""
echo "To restore a backup:"
echo ""
echo "1. List available backups:"
echo "   gsutil ls -h gs://$BACKUP_BUCKET/"
echo ""
echo "2. Download backup:"
echo "   gsutil cp gs://$BACKUP_BUCKET/dev-nexus-prod-${TIMESTAMP}.tfstate ./"
echo ""
echo "3. Switch to environment and restore:"
echo "   cd terraform"
echo "   terraform init -backend-config=\"prefix=dev-nexus/prod\" -reconfigure"
echo "   terraform state push dev-nexus-prod-${TIMESTAMP}.tfstate"
echo ""
echo "4. Verify restored state:"
echo "   terraform state list"
echo ""

if [ $FAILED -gt 0 ]; then
    echo -e "${YELLOW}Warning: $FAILED backup(s) failed${NC}"
    exit 1
else
    echo -e "${GREEN}All backups completed successfully!${NC}"
fi
