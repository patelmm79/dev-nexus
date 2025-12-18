#!/bin/bash
# Bootstrap script to set up shared Terraform state bucket
# Run once per GCP project to enable remote state for all terraform configurations
# Safe to run multiple times - idempotent

set -e

PROJECT_ID="${GCP_PROJECT_ID:-globalbiting-dev}"
STATE_BUCKET="terraform-state-${PROJECT_ID}"
REGION="${GCP_REGION:-us-central1}"

echo "Setting up Terraform state backend..."
echo "Project: $PROJECT_ID"
echo "Bucket: gs://$STATE_BUCKET/"
echo ""

# Check if bucket exists
if gsutil ls -b "gs://$STATE_BUCKET/" &>/dev/null; then
  echo "✓ Terraform state bucket already exists"
else
  echo "Creating Terraform state bucket..."
  gsutil mb -p "$PROJECT_ID" "gs://$STATE_BUCKET/"
  echo "✓ Bucket created"
fi

# Enable versioning (protects against accidental deletes)
echo "Enabling bucket versioning..."
gsutil versioning set on "gs://$STATE_BUCKET/"
echo "✓ Versioning enabled"

# Set lifecycle policy (keep versions for 90 days, delete non-current after 30 days)
cat > /tmp/lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"numNewerVersions": 5}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"isLive": false, "age": 30}
      }
    ]
  }
}
EOF

gsutil lifecycle set /tmp/lifecycle.json "gs://$STATE_BUCKET/"
rm /tmp/lifecycle.json
echo "✓ Lifecycle policy applied"

# Enable bucket logging
echo "Enabling bucket logging..."
gsutil logging set on -b "gs://$STATE_BUCKET/" "gs://$STATE_BUCKET/" || echo "  (logging may require additional setup)"

echo ""
echo "✓ Terraform state backend ready!"
echo ""
echo "Update your terraform/main.tf backend config:"
echo "  bucket = \"$STATE_BUCKET\""
echo ""
echo "Then run: terraform init"
