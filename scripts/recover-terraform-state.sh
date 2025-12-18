#!/bin/bash
# Terraform State Recovery Script
#
# Recovers Terraform state from backups in case of corruption or accidental changes
#
# Usage:
#   bash recover-terraform-state.sh prod            # List backups for prod
#   bash recover-terraform-state.sh prod 20240115   # Recover specific backup

set -e

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-globalbiting-dev}"
STATE_BUCKET="terraform-state-${PROJECT_ID}"
BACKUP_BUCKET="${STATE_BUCKET}-backups"

# Parse arguments
if [ -z "$1" ]; then
    echo "Usage: $0 <environment> [backup-timestamp]"
    echo ""
    echo "Examples:"
    echo "  $0 prod                    # List available backups for prod"
    echo "  $0 prod 20240115-143022    # Recover specific backup"
    exit 1
fi

ENVIRONMENT="$1"
BACKUP_TIMESTAMP="$2"

# Validate environment
case "$ENVIRONMENT" in
    dev|staging|prod)
        ;;
    *)
        echo -e "${RED}Invalid environment: $ENVIRONMENT${NC}"
        echo "Allowed: dev, staging, prod"
        exit 1
        ;;
esac

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Terraform State Recovery${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo "Project:       $PROJECT_ID"
echo "Environment:   $ENVIRONMENT"
echo "Backup Bucket: $BACKUP_BUCKET"
echo ""

# If no timestamp provided, list available backups
if [ -z "$BACKUP_TIMESTAMP" ]; then
    echo -e "${YELLOW}Available backups for $ENVIRONMENT:${NC}"
    echo ""

    if gsutil ls "gs://$BACKUP_BUCKET/dev-nexus-${ENVIRONMENT}-*.tfstate" &>/dev/null; then
        gsutil ls -Lh "gs://$BACKUP_BUCKET/dev-nexus-${ENVIRONMENT}-*.tfstate" | \
            grep -o "dev-nexus-${ENVIRONMENT}-[^/]*\.tfstate" | \
            while read backup; do
                size=$(gsutil ls -Lh "gs://$BACKUP_BUCKET/$backup" | grep "Content length:" | awk '{print $NF}')
                timestamp=$(echo "$backup" | sed "s/dev-nexus-${ENVIRONMENT}-//;s/\.tfstate//")
                echo "  $timestamp (size: $size)"
            done
    else
        echo -e "${RED}No backups found for $ENVIRONMENT environment${NC}"
        exit 1
    fi

    echo ""
    echo -e "${YELLOW}To recover a backup, run:${NC}"
    echo "  bash $0 $ENVIRONMENT <backup-timestamp>"
    echo ""
    exit 0
fi

# Verify backup exists
BACKUP_FILE="gs://$BACKUP_BUCKET/dev-nexus-${ENVIRONMENT}-${BACKUP_TIMESTAMP}.tfstate"

if ! gsutil ls "$BACKUP_FILE" &>/dev/null; then
    echo -e "${RED}Backup not found: $BACKUP_FILE${NC}"
    exit 1
fi

echo -e "${YELLOW}WARNING: This will overwrite the current state for $ENVIRONMENT${NC}"
echo ""
echo "Backup to restore: dev-nexus-${ENVIRONMENT}-${BACKUP_TIMESTAMP}.tfstate"
echo ""

# Confirm recovery
read -p "Are you sure you want to recover from this backup? (type 'yes' to confirm): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Recovery cancelled"
    exit 0
fi

echo ""
echo -e "${YELLOW}Step 1: Downloading backup...${NC}"

TEMP_DIR=$(mktemp -d)
LOCAL_BACKUP="$TEMP_DIR/backup.tfstate"

gsutil cp "$BACKUP_FILE" "$LOCAL_BACKUP"
echo -e "${GREEN}✓${NC} Backup downloaded"

echo ""
echo -e "${YELLOW}Step 2: Initializing Terraform for $ENVIRONMENT...${NC}"

cd terraform

terraform init -backend-config="prefix=dev-nexus/$ENVIRONMENT" -reconfigure -input=false
echo -e "${GREEN}✓${NC} Terraform initialized"

echo ""
echo -e "${YELLOW}Step 3: Creating safety backup of current state...${NC}"

SAFETY_BACKUP="terraform-state-backup-before-recovery-$(date +%Y%m%d-%H%M%S).tfstate"
terraform state pull > "$SAFETY_BACKUP"
echo -e "${GREEN}✓${NC} Current state backed up to: $SAFETY_BACKUP"

echo ""
echo -e "${YELLOW}Step 4: Restoring state from backup...${NC}"

if terraform state push "$LOCAL_BACKUP"; then
    echo -e "${GREEN}✓${NC} State restored successfully"
else
    echo -e "${RED}✗${NC} Failed to restore state"
    echo ""
    echo "Current state is preserved in: $SAFETY_BACKUP"
    rm -rf "$TEMP_DIR"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 5: Verifying restored state...${NC}"

STATE_COUNT=$(terraform state list | wc -l)
echo -e "${GREEN}✓${NC} State contains $STATE_COUNT resources"

echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}✓ Recovery Complete!${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo "Important next steps:"
echo ""
echo "1. Review the restored state:"
echo "   terraform state list"
echo "   terraform show"
echo ""
echo "2. Test the state with a plan:"
echo "   terraform plan -var-file=\"${ENVIRONMENT}.tfvars\""
echo ""
echo "3. If the plan looks wrong, restore the safety backup:"
echo "   terraform state push $SAFETY_BACKUP"
echo ""
echo "4. If everything looks correct, clean up:"
echo "   rm $SAFETY_BACKUP"
echo "   rm -rf $TEMP_DIR"
echo ""

# Cleanup temp directory
rm -rf "$TEMP_DIR"
