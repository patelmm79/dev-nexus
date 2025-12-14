#!/bin/bash
# Fix VPC Connector Connection for Cloud Run
# This script fixes the PostgreSQL connection issue by ensuring Cloud Run is connected to VPC

set -e

echo "========================================="
echo "VPC Connector Fix Script"
echo "========================================="
echo ""

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-globalbiting-dev}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="pattern-discovery-agent"
VPC_CONNECTOR="dev-nexus-connector"

echo "Configuration:"
echo "  Project: $PROJECT_ID"
echo "  Region: $REGION"
echo "  Service: $SERVICE_NAME"
echo "  VPC Connector: $VPC_CONNECTOR"
echo ""

# Step 1: Verify VPC Connector exists and is ready
echo "Step 1: Checking VPC Connector status..."
CONNECTOR_STATE=$(gcloud compute networks vpc-access connectors describe $VPC_CONNECTOR \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="value(state)" 2>&1)

if [ "$CONNECTOR_STATE" != "READY" ]; then
  echo "❌ ERROR: VPC Connector is not READY (current state: $CONNECTOR_STATE)"
  echo "Please wait for the connector to be ready or check Terraform logs"
  exit 1
fi
echo "✓ VPC Connector is READY"
echo ""

# Step 2: Update Cloud Run service to use VPC connector
echo "Step 2: Updating Cloud Run service to use VPC connector..."
gcloud run services update $SERVICE_NAME \
  --vpc-connector=$VPC_CONNECTOR \
  --vpc-egress=private-ranges-only \
  --region=$REGION \
  --project=$PROJECT_ID

echo "✓ Cloud Run service updated"
echo ""

# Step 3: Verify the connection
echo "Step 3: Verifying VPC access configuration..."
VPC_CONFIG=$(gcloud run services describe $SERVICE_NAME \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="yaml(spec.template.spec.vpcAccess)")

if echo "$VPC_CONFIG" | grep -q "connector:"; then
  echo "✓ VPC connector is now configured"
  echo "$VPC_CONFIG"
else
  echo "⚠ WARNING: VPC connector configuration not detected"
  echo "$VPC_CONFIG"
fi
echo ""

# Step 4: Wait for new revision
echo "Step 4: Waiting for new revision to deploy..."
sleep 5

# Step 5: Check logs
echo "Step 5: Checking recent logs for PostgreSQL connection..."
gcloud logging read \
  "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME" \
  --limit=10 \
  --project=$PROJECT_ID \
  --format="table(timestamp,textPayload)" | head -20

echo ""
echo "========================================="
echo "Fix Complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Test the service: curl \$(gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.url)')/health"
echo "2. Check logs if needed: gcloud logging read 'resource.labels.service_name=$SERVICE_NAME' --limit=50"
echo "3. Re-run Terraform to ensure state is synchronized"
echo ""
