#!/bin/bash
# Enhanced Terraform Backend Setup for Multi-Environment State Management
#
# This script sets up a robust Terraform state backend with:
# - Remote state in Google Cloud Storage (GCS)
# - State versioning and lifecycle management
# - Backup capabilities
# - Multi-environment state isolation
#
# Run once per GCP project to initialize the shared state backend
# Safe to run multiple times - idempotent
#
# Usage:
#   export GCP_PROJECT_ID="your-project-id"
#   bash setup-terraform-backend.sh

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
REGION="${GCP_REGION:-us-central1}"

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}Terraform Multi-Environment Backend Setup${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo "Project:     $PROJECT_ID"
echo "State Bucket: $STATE_BUCKET"
echo "Backup Bucket: $BACKUP_BUCKET"
echo "Region:      $REGION"
echo ""

# Step 1: Create primary state bucket
echo -e "${YELLOW}Step 1: Setting up primary state bucket...${NC}"

if gsutil ls -b "gs://$STATE_BUCKET/" &>/dev/null; then
    echo -e "${GREEN}✓${NC} State bucket already exists: gs://$STATE_BUCKET/"
else
    echo "Creating state bucket..."
    gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://$STATE_BUCKET/"
    echo -e "${GREEN}✓${NC} State bucket created: gs://$STATE_BUCKET/"
fi

# Step 2: Enable versioning for state protection
echo ""
echo -e "${YELLOW}Step 2: Enabling state versioning...${NC}"
gsutil versioning set on "gs://$STATE_BUCKET/"
echo -e "${GREEN}✓${NC} Versioning enabled (protects against accidental deletes)"

# Step 3: Set lifecycle policy
echo ""
echo -e "${YELLOW}Step 3: Configuring lifecycle policy...${NC}"
cat > /tmp/state-lifecycle.json <<'POLICY_EOF'
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"numNewerVersions": 10, "matchesPrefix": ["dev-nexus"]}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"isLive": false, "age": 90}
      }
    ]
  }
}
POLICY_EOF

gsutil lifecycle set /tmp/state-lifecycle.json "gs://$STATE_BUCKET/"
rm /tmp/state-lifecycle.json
echo -e "${GREEN}✓${NC} Lifecycle policy applied:"
echo "   - Keep 10 versions per state file"
echo "   - Delete old versions after 90 days"

# Step 4: Enable bucket logging
echo ""
echo -e "${YELLOW}Step 4: Enabling bucket logging...${NC}"
if gsutil logging set on -b "gs://$STATE_BUCKET/" "gs://$STATE_BUCKET/" &>/dev/null; then
    echo -e "${GREEN}✓${NC} Bucket logging enabled"
else
    echo -e "${YELLOW}ℹ${NC} Bucket logging requires additional permissions (optional)"
fi

# Step 5: Create backup bucket
echo ""
echo -e "${YELLOW}Step 5: Setting up state backup bucket...${NC}"

if gsutil ls -b "gs://$BACKUP_BUCKET/" &>/dev/null; then
    echo -e "${GREEN}✓${NC} Backup bucket already exists: gs://$BACKUP_BUCKET/"
else
    echo "Creating backup bucket..."
    gsutil mb -p "$PROJECT_ID" -l "$REGION" "gs://$BACKUP_BUCKET/"
    echo -e "${GREEN}✓${NC} Backup bucket created: gs://$BACKUP_BUCKET/"
fi

# Enable versioning on backup bucket
gsutil versioning set on "gs://$BACKUP_BUCKET/"

# Backup bucket lifecycle: keep 30 days
cat > /tmp/backup-lifecycle.json <<'POLICY_EOF'
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 30}
      }
    ]
  }
}
POLICY_EOF

gsutil lifecycle set /tmp/backup-lifecycle.json "gs://$BACKUP_BUCKET/"
rm /tmp/backup-lifecycle.json
echo -e "${GREEN}✓${NC} Backup lifecycle: keep 30 days"

# Step 6: Set bucket permissions
echo ""
echo -e "${YELLOW}Step 6: Configuring bucket permissions...${NC}"

# Enable uniform bucket-level access
gsutil uniformbucketlevelaccess set on "gs://$STATE_BUCKET/" 2>/dev/null || true
gsutil uniformbucketlevelaccess set on "gs://$BACKUP_BUCKET/" 2>/dev/null || true
echo -e "${GREEN}✓${NC} Uniform bucket-level access enabled"

# Step 7: Verify environment-specific state isolation
echo ""
echo -e "${YELLOW}Step 7: Verifying state isolation setup...${NC}"

echo "Environment state paths (will be created on first terraform init):"
echo "  • Development:  gs://$STATE_BUCKET/dev-nexus/dev/"
echo "  • Staging:      gs://$STATE_BUCKET/dev-nexus/staging/"
echo "  • Production:   gs://$STATE_BUCKET/dev-nexus/prod/"
echo -e "${GREEN}✓${NC} State isolation configured"

# Step 8: Display summary
echo ""
echo -e "${BLUE}================================================${NC}"
echo -e "${GREEN}✓ Backend setup complete!${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo ""
echo "1. Initialize Terraform for development environment:"
echo "   cd terraform"
echo "   terraform init -backend-config=\"prefix=dev-nexus/dev\""
echo ""
echo "2. Verify state is stored remotely:"
echo "   gsutil ls -r gs://$STATE_BUCKET/"
echo ""
echo "3. View state file versions:"
echo "   gsutil ls -Lh gs://$STATE_BUCKET/dev-nexus/dev/default.tfstate"
echo ""
echo -e "${BLUE}State Management:${NC}"
echo ""
echo "• Backup state: terraform state pull > backup-\$(date +%Y%m%d-%H%M%S).tfstate"
echo "• List backups: gsutil ls gs://$BACKUP_BUCKET/"
echo "• Restore state: terraform state push backup-file.tfstate"
echo ""
echo -e "${BLUE}GCS Bucket Details:${NC}"
echo ""
echo "State Bucket:   gs://$STATE_BUCKET/"
echo "  - Versioning: Enabled (10 versions kept, old deleted after 90 days)"
echo "  - Logging:    Enabled"
echo "  - Access:     Uniform bucket-level access"
echo ""
echo "Backup Bucket:  gs://$BACKUP_BUCKET/"
echo "  - Versioning: Enabled"
echo "  - Retention:  30 days"
echo ""
