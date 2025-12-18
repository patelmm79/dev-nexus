# Deployment Guide: dev-nexus to Google Cloud Run

> **Quick Start:** Deploy in 30 minutes
> **Status:** Production Ready ✅
> **⚠️ IMPORTANT:** All commands in this guide run on YOUR LOCAL MACHINE, not in the cloud.

---

## Deployment Methods

Choose your deployment approach:

### 🚀 Bash Scripts (Recommended for Quick Start)
- **Best for:** Quick deployments, learning, testing
- **Time to deploy:** 5-10 minutes
- **Prerequisites:** gcloud CLI, API keys
- **Documentation:** This guide (sections below)
- **Pros:** Simple, fast, minimal setup
- **Cons:** Manual state tracking, no rollback

### 🏗️ Terraform (Recommended for Production)
- **Best for:** Production, teams, infrastructure as code, multi-environment deployments
- **Time to deploy:** 10-15 minutes (first time)
- **Prerequisites:** Terraform, gcloud CLI, API keys
- **Documentation:**
  - [MULTI_ENV_SETUP.md](MULTI_ENV_SETUP.md) - **Recommended:** Multi-environment setup (dev/staging/prod)
  - [terraform/README.md](terraform/README.md) - Terraform configuration guide
  - [TERRAFORM_UNIFIED_INIT.md](TERRAFORM_UNIFIED_INIT.md) - Unified initialization pattern
  - [TERRAFORM_STATE_MANAGEMENT.md](TERRAFORM_STATE_MANAGEMENT.md) - State backup and recovery
- **Pros:** State management, rollback, declarative, team collaboration, includes PostgreSQL, multi-environment support
- **Cons:** Requires Terraform knowledge

### Detailed Comparison

| Aspect | Bash Scripts | Terraform |
|--------|--------------|-----------|
| **State Management** | ❌ Manual tracking | ✅ Built-in, versioned |
| **Idempotency** | ⚠️ Depends on script | ✅ Guaranteed |
| **Rollback** | ❌ Manual | ✅ Easy (`terraform apply` old state) |
| **Team Collaboration** | ❌ Difficult | ✅ Remote state, locking |
| **Infrastructure Scope** | Cloud Run only | Cloud Run + PostgreSQL + VPC |
| **Validation** | ⚠️ Manual testing | ✅ `terraform validate`, `plan` |
| **Documentation** | ⚠️ Comments in scripts | ✅ Self-documenting |
| **Learning Curve** | ✅ Simple | ⚠️ Moderate |
| **Setup Time** | ✅ 5-10 minutes | ⚠️ 10-15 minutes |
| **Production Ready** | ⚠️ Basic setup | ✅ Full infrastructure |

**Recommendation:**
- **Use Bash Scripts:** For quick tests, learning, single deployments
- **Use Terraform:** For production, teams, when you need PostgreSQL, or require rollback capability

**This guide covers Bash Scripts.** For Terraform deployment, see **[terraform/README.md](terraform/README.md)**.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Deployment](#quick-deployment)
3. [Detailed Step-by-Step](#detailed-step-by-step)
4. [Verification](#verification)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. Google Cloud Project

- Active GCP project with billing enabled
- Owner or Editor role

### 2. Enable Required APIs

```bash
# Set your project ID
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"  # or your preferred region

# Enable APIs
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  containerregistry.googleapis.com \
  --project=$GCP_PROJECT_ID
```

### 3. Required Credentials

**Anthropic API Key** (get from [console.anthropic.com](https://console.anthropic.com)):

```bash
export ANTHROPIC_API_KEY="sk-ant-xxxxxxxxxxxxx"
```

**GitHub Token** (with repo access):

```bash
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxx"
```

**Knowledge Base Repository:**

```bash
export KNOWLEDGE_BASE_REPO="username/repo"  # e.g., patelmm79/dev-nexus
```

### 4. Install gcloud CLI

If not already installed:

```bash
# Install gcloud CLI
# See: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Set default project
gcloud config set project $GCP_PROJECT_ID
```

---

## Quick Deployment

**For experienced users who have already completed prerequisites:**

**Run on your local machine in the dev-nexus directory:**

```bash
# 1. Setup secrets in Google Cloud Secret Manager
# This creates or updates GITHUB_TOKEN and ANTHROPIC_API_KEY secrets
# NOTE: Safe to run multiple times - automatically updates existing secrets
bash scripts/setup-secrets.sh
# Expected: "Secrets configured successfully!"

# If secrets already exist and are unchanged, you can skip to step 2

# 2. Build and deploy to Cloud Run (takes 3-5 minutes)
# This builds Docker image and deploys to Cloud Run
bash scripts/deploy.sh
# Expected: "Deployment verified!" and service URL

# 3. Test the deployed service
# Get the service URL from Cloud Run
SERVICE_URL=$(gcloud run services describe pattern-discovery-agent \
  --region=$GCP_REGION --format="value(status.url)")

# Test health endpoint
curl $SERVICE_URL/health
# Expected: {"status":"healthy","version":"2.0.0",...}
```

✅ Done! Service is live at the SERVICE_URL.

**Prerequisites not met?** See [Detailed Step-by-Step](#detailed-step-by-step) below.

---

## Detailed Step-by-Step

**All steps run on your local machine:**

### Step 1: Clone Repository to Your Local Machine

```bash
# Clone the repository to your computer
git clone https://github.com/patelmm79/dev-nexus.git
cd dev-nexus

# Verify you're in the correct directory
pwd  # Should end with /dev-nexus
ls scripts/deploy.sh  # Should show: scripts/deploy.sh
```

### Step 2: Setup Environment Variables on Your Local Machine

```bash
# Set these environment variables in your terminal session
# Required for deployment
export GCP_PROJECT_ID="your-project-id"  # Your GCP project ID
export GCP_REGION="us-central1"  # Choose your region
export ANTHROPIC_API_KEY="sk-ant-xxxxx"  # From console.anthropic.com
export GITHUB_TOKEN="ghp_xxxxx"  # From GitHub settings
export KNOWLEDGE_BASE_REPO="patelmm79/dev-nexus"  # Your KB repo (format: owner/repo)

# Verify environment variables are set correctly
echo "Project: $GCP_PROJECT_ID"
echo "Region: $GCP_REGION"
echo "Anthropic Key: ${ANTHROPIC_API_KEY:0:10}..."
echo "GitHub Token: ${GITHUB_TOKEN:0:10}..."
echo "KB Repo: $KNOWLEDGE_BASE_REPO"

# All values should be displayed (not empty)
```

### Step 3: Create or Update Secrets in Secret Manager

```bash
bash scripts/setup-secrets.sh
```

**What This Does:**
- Creates new secrets if they don't exist
- Adds new versions to existing secrets (if they already exist)
- Configures IAM permissions for Cloud Run service account
- **Safe to run multiple times** - idempotent operation

**Expected Output (First Time):**

```
================================================
Setting up Secrets in Secret Manager
================================================
Project: your-project-id

Configuring GITHUB_TOKEN secret...
✓ Created GITHUB_TOKEN

Configuring ANTHROPIC_API_KEY secret...
✓ Created ANTHROPIC_API_KEY

Granting Secret Manager access to Cloud Run service account...
Service Account: 123456789-compute@developer.gserviceaccount.com

Updated IAM policy for secret [GITHUB_TOKEN].
Updated IAM policy for secret [ANTHROPIC_API_KEY].

================================================
Secrets configured successfully!
================================================
✓ GITHUB_TOKEN
✓ ANTHROPIC_API_KEY

Cloud Run service account has been granted access
```

**Expected Output (Subsequent Runs):**

```
Configuring GITHUB_TOKEN secret...
  Secret already exists, adding new version...
✓ Updated GITHUB_TOKEN

Configuring ANTHROPIC_API_KEY secret...
  Secret already exists, adding new version...
✓ Updated ANTHROPIC_API_KEY
```

**Verify Secrets Created:**

```bash
# List all secrets
gcloud secrets list --project=$GCP_PROJECT_ID

# View secret versions
gcloud secrets versions list GITHUB_TOKEN --project=$GCP_PROJECT_ID
```

**When to Run:**
- ✅ First deployment - required
- ✅ Rotating credentials - run to add new versions
- ✅ Unsure if secrets exist - safe to run
- ❌ Redeploying code only - skip and go to step 4

### Step 4: Deploy to Cloud Run

```bash
bash scripts/deploy.sh
```

**What Happens:**

1. **Build Phase** (~2-3 minutes):
   - Docker multi-stage build
   - Installs Python 3.11 dependencies
   - Copies application code
   - Pushes to Container Registry

2. **Deploy Phase** (~1-2 minutes):
   - Creates Cloud Run service
   - Configures CPU/memory (1 vCPU, 1Gi)
   - Sets up scaling (0-10 instances)
   - Injects secrets from Secret Manager
   - Enables public access (unauthenticated)

3. **Verification** (~10 seconds):
   - Health check test
   - AgentCard endpoint test

**Expected Output:**

```
================================================
Deploying Pattern Discovery Agent to Cloud Run
================================================
Project:  your-project-id
Region:   us-central1
Service:  pattern-discovery-agent
KB Repo:  patelmm79/dev-nexus

Starting Cloud Build...
Creating temporary tarball archive of 45 file(s) totalling 2.3 MiB...
Uploading tarball to [gs://...]

BUILD
ID                                    CREATE_TIME                DURATION  SOURCE
1234abcd-5678-90ef-ghij-klmnopqrstuv  2025-12-09T12:00:00+00:00  3M12S     gs://...

Retrieving service URL...

================================================
Deployment complete!
================================================
Service URL:  https://pattern-discovery-agent-abc123-uc.a.run.app
AgentCard:    https://pattern-discovery-agent-abc123-uc.a.run.app/.well-known/agent.json
Health:       https://pattern-discovery-agent-abc123-uc.a.run.app/health

Testing health endpoint...
✓ Health check passed
Testing AgentCard endpoint...
✓ AgentCard endpoint available

Deployment verified!
```

### Step 5: Save Service URL

```bash
# Get and save service URL
SERVICE_URL=$(gcloud run services describe pattern-discovery-agent \
  --region=$GCP_REGION \
  --project=$GCP_PROJECT_ID \
  --format="value(status.url)")

echo "Dev-Nexus URL: $SERVICE_URL"

# Optional: Save to .env file for local development
echo "DEV_NEXUS_URL=$SERVICE_URL" >> .env.local
```

---

## Verification

### Test 1: Health Check

```bash
curl $SERVICE_URL/health | jq
```

**Expected Response:**

```json
{
  "status": "healthy",
  "version": "2.0.0",
  "skills_loaded": 15,
  "knowledge_base_accessible": true,
  "timestamp": "2025-12-09T12:00:00Z"
}
```

### Test 2: AgentCard

```bash
curl $SERVICE_URL/.well-known/agent.json | jq
```

**Expected Response:**

```json
{
  "agent": {
    "name": "Pattern Discovery Agent",
    "description": "Automated architectural consistency and pattern discovery",
    "url": "https://pattern-discovery-agent-abc123-uc.a.run.app"
  },
  "skills": [
    {
      "id": "query_patterns",
      "name": "Query Patterns",
      "description": "Search for patterns by keywords..."
    },
    ...
  ]
}
```

### Test 3: Execute Skill

**Test a public skill (no auth required):**

```bash
curl -X POST $SERVICE_URL/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "get_repository_list",
    "input": {
      "include_metadata": true
    }
  }' | jq
```

**Expected Response:**

```json
{
  "success": true,
  "repositories": [
    "owner/repo1",
    "owner/repo2"
  ],
  "count": 2,
  "metadata": {
    "owner/repo1": {
      "patterns_count": 5,
      "last_updated": "2025-12-09T..."
    }
  }
}
```

### Test 4: Runtime Monitoring Skill

**Test add_runtime_issue (requires auth in production):**

```bash
curl -X POST $SERVICE_URL/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "add_runtime_issue",
    "input": {
      "repository": "patelmm79/dev-nexus",
      "service_type": "cloud_run",
      "issue_type": "performance",
      "severity": "low",
      "log_snippet": "Test issue from deployment verification",
      "root_cause": "Deployment verification test",
      "suggested_fix": "No fix needed - test issue"
    }
  }' | jq
```

**Verify Issue Recorded:**

```bash
curl -X POST $SERVICE_URL/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "query_known_issues",
    "input": {
      "issue_type": "performance"
    }
  }' | jq
```

---

## Configuration

### Environment Variables

**View current configuration:**

```bash
gcloud run services describe pattern-discovery-agent \
  --region=$GCP_REGION \
  --format="yaml(spec.template.spec.containers[0].env)"
```

**Update configuration:**

```bash
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --set-env-vars="NEW_VAR=value"
```

### Scaling Configuration

**Auto-scaling limits:**

```bash
# Update min/max instances
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --min-instances=1 \  # Keep warm (no cold starts)
  --max-instances=20   # Handle more traffic
```

**Resource limits:**

```bash
# Update CPU/memory
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --memory=2Gi \
  --cpu=2
```

### Enable Authentication

**For production, enable authentication:**

```bash
# Update to require authentication
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --no-allow-unauthenticated

# Create service account for external agents
gcloud iam service-accounts create log-attacker-client \
  --display-name="Log Attacker A2A Client"

# Grant invoker permission
gcloud run services add-iam-policy-binding pattern-discovery-agent \
  --region=$GCP_REGION \
  --member="serviceAccount:log-attacker-client@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

**Update dev-nexus to accept this service account:**

```bash
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --set-env-vars="ALLOWED_SERVICE_ACCOUNTS=log-attacker-client@${GCP_PROJECT_ID}.iam.gserviceaccount.com"
```

### External Agent Configuration

**For agentic-log-attacker to call dev-nexus:**

```bash
# In agentic-log-attacker .env file
DEV_NEXUS_URL=https://pattern-discovery-agent-abc123-uc.a.run.app
DEVNEXUS_INTEGRATION_ENABLED=true

# If authentication enabled:
DEV_NEXUS_TOKEN=$(gcloud auth print-identity-token \
  --impersonate-service-account=log-attacker-client@${GCP_PROJECT_ID}.iam.gserviceaccount.com)
```

---

## Monitoring

### View Logs

**Real-time logs:**

```bash
gcloud run services logs tail pattern-discovery-agent \
  --region=$GCP_REGION
```

**Recent logs:**

```bash
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=pattern-discovery-agent" \
  --limit 50 \
  --project=$GCP_PROJECT_ID
```

### View Metrics

**Cloud Console:**

1. Go to Cloud Run → pattern-discovery-agent
2. Click "Metrics" tab
3. View:
   - Request count
   - Request latency (P50, P95, P99)
   - Instance count
   - CPU utilization
   - Memory utilization

**Command line:**

```bash
# Request count (last hour)
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count" AND
    resource.labels.service_name="pattern-discovery-agent"' \
  --format="table(metric.labels.response_code_class, points[0].value.int64Value)"
```

### Setup Alerts

**Create alert for high error rate:**

```bash
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="Dev-Nexus High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=300s \
  --condition-filter='resource.type="cloud_run_revision" AND
    resource.labels.service_name="pattern-discovery-agent" AND
    metric.type="run.googleapis.com/request_count" AND
    metric.labels.response_code_class="5xx"'
```

---

## Troubleshooting

### Issue: Deployment Fails with "Permission Denied"

**Cause:** Cloud Build service account lacks permissions

**Solution:**

```bash
PROJECT_NUMBER=$(gcloud projects describe $GCP_PROJECT_ID --format="value(projectNumber)")
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"
```

### Issue: Health Check Returns 503

**Cause:** Service starting up (cold start)

**Solution:** Wait 30 seconds and retry. Cold starts can take up to 1 minute.

```bash
# Check service status
gcloud run services describe pattern-discovery-agent \
  --region=$GCP_REGION \
  --format="value(status.conditions)"
```

### Issue: "Secret not found" Error

**Cause:** Secrets not created or service account lacks access

**Solution:**

```bash
# Verify secrets exist
gcloud secrets list --project=$GCP_PROJECT_ID

# Re-run setup script
bash scripts/setup-secrets.sh

# Check IAM permissions
gcloud secrets get-iam-policy GITHUB_TOKEN --project=$GCP_PROJECT_ID
```

### Issue: Knowledge Base Access Denied

**Cause:** GitHub token lacks repo access

**Solution:**

1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token with `repo` scope
3. Update secret:

```bash
export GITHUB_TOKEN="ghp_new_token"
echo -n "$GITHUB_TOKEN" | gcloud secrets versions add GITHUB_TOKEN \
  --data-file=- \
  --project=$GCP_PROJECT_ID
```

4. Redeploy:

```bash
bash scripts/deploy.sh
```

### Issue: High Cold Start Latency

**Cause:** Service scales to zero, causing cold starts

**Solution:** Set minimum instances

```bash
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --min-instances=1  # Keep 1 instance always warm
```

**Note:** This will increase costs (~$5-10/month for 1 always-on instance)

### Issue: Out of Memory

**Cause:** Large knowledge base or complex queries

**Solution:** Increase memory

```bash
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --memory=2Gi  # or 4Gi
```

---

## Cost Optimization

### Free Tier Usage

Cloud Run free tier (per month):
- 2 million requests
- 360,000 vCPU-seconds
- 180,000 GiB-seconds

**Typical dev-nexus usage stays within free tier!**

### Minimize Costs

1. **Scale to zero:** Keep min-instances=0 (default)
2. **Right-size resources:** Use 1 vCPU, 1Gi unless needed
3. **Enable request timeout:** Prevent long-running requests

```bash
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --timeout=60s  # Kill requests after 60 seconds
```

### Monitor Costs

```bash
# View Cloud Run costs
gcloud billing accounts list
# Then view in GCP Console → Billing → Cost Table
# Filter by: Cloud Run
```

---

## Updates & Redeployment

### Update Code

```bash
# Pull latest code
git pull origin main

# Update secrets (ONLY if credentials changed)
# Skip this if your API keys/tokens are unchanged
bash scripts/setup-secrets.sh

# Redeploy (always required for code updates)
bash scripts/deploy.sh
```

**When to run `setup-secrets.sh` during redeployment:**
- ✅ **Rotating credentials** - Run to add new secret versions
- ✅ **Changed API keys** - Run to update secrets
- ❌ **Code changes only** - Skip and go straight to `deploy.sh`
- ❌ **First deployment** - Already covered in Step 3 above

### Rollback

```bash
# List revisions
gcloud run revisions list \
  --service=pattern-discovery-agent \
  --region=$GCP_REGION

# Rollback to previous revision
gcloud run services update-traffic pattern-discovery-agent \
  --region=$GCP_REGION \
  --to-revisions=pattern-discovery-agent-00002-abc=100
```

---

## CI/CD (Optional)

**Setup automatic deployment on git push:**

Create `.github/workflows/deploy-cloudrun.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}

      - name: Deploy
        run: bash scripts/deploy.sh
        env:
          GCP_PROJECT_ID: ${{ secrets.GCP_PROJECT_ID }}
          GCP_REGION: us-central1
          KNOWLEDGE_BASE_REPO: ${{ secrets.KNOWLEDGE_BASE_REPO }}
```

**Add secrets to GitHub:**

Repository → Settings → Secrets and variables → Actions:
- `GCP_SA_KEY` - Service account JSON key
- `GCP_PROJECT_ID` - Your GCP project ID
- `KNOWLEDGE_BASE_REPO` - Your KB repo

---

## Production Checklist

Before going to production:

- [ ] Enable authentication (`--no-allow-unauthenticated`)
- [ ] Setup monitoring alerts
- [ ] Configure min-instances for warm start (optional)
- [ ] Increase memory/CPU if needed
- [ ] Setup CI/CD for automatic deployments
- [ ] Configure custom domain (optional)
- [ ] Enable Cloud Armor for DDoS protection (optional)
- [ ] Setup backup strategy for knowledge base
- [ ] Document external agent service accounts
- [ ] Test failover scenarios

---

## Support

**Issues:**
- GitHub: https://github.com/patelmm79/dev-nexus/issues

**Documentation:**
- README: `/README.md`
- API Reference: `/API.md`
- Integration Guide: `/INTEGRATION.md`

---

**Last Updated:** 2025-12-09
**Version:** 1.0
