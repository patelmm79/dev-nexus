#!/bin/bash
# Set up secrets in Google Cloud Secret Manager

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"

# Validation
if [ -z "$PROJECT_ID" ]; then
    echo "Error: GCP_PROJECT_ID environment variable not set"
    echo "Usage: export GCP_PROJECT_ID=your-project-id"
    exit 1
fi

echo "================================================"
echo "Setting up Secrets in Secret Manager"
echo "================================================"
echo "Project: $PROJECT_ID"
echo

# Check if required environment variables are set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN environment variable not set"
    exit 1
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Error: ANTHROPIC_API_KEY environment variable not set"
    exit 1
fi

# Function to create or update a secret
create_or_update_secret() {
    local secret_name=$1
    local secret_value=$2

    echo "Configuring ${secret_name} secret..."

    # Try to create the secret
    if echo -n "$secret_value" | gcloud secrets create "$secret_name" \
        --data-file=- \
        --project="$PROJECT_ID" \
        --replication-policy="automatic" 2>/dev/null; then
        echo "✓ Created ${secret_name}"
    else
        # Secret already exists, add new version
        echo "  Secret already exists, adding new version..."
        echo -n "$secret_value" | gcloud secrets versions add "$secret_name" \
            --data-file=- \
            --project="$PROJECT_ID"
        echo "✓ Updated ${secret_name}"
    fi
}

# Create or update secrets
create_or_update_secret "GITHUB_TOKEN" "$GITHUB_TOKEN"
create_or_update_secret "ANTHROPIC_API_KEY" "$ANTHROPIC_API_KEY"

# Get Cloud Run service account
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

echo
echo "Granting Secret Manager access to Cloud Run service account..."
echo "Service Account: $SERVICE_ACCOUNT"

# Grant access to secrets
gcloud secrets add-iam-policy-binding GITHUB_TOKEN \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" \
    --project="$PROJECT_ID"

gcloud secrets add-iam-policy-binding ANTHROPIC_API_KEY \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" \
    --project="$PROJECT_ID"

echo
echo "================================================"
echo "Secrets configured successfully!"
echo "================================================"
echo "✓ GITHUB_TOKEN"
echo "✓ ANTHROPIC_API_KEY"
echo
echo "Cloud Run service account has been granted access"
