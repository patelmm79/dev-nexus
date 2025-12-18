# Multi-Environment Terraform Setup

This document explains how to deploy dev-nexus to multiple environments (dev, staging, prod) using environment-specific Terraform configurations and state isolation.

## Overview

The multi-environment setup enables:

1. **State Isolation** - Each environment maintains separate Terraform state in GCS with unique prefixes
2. **Secret Isolation** - Environment-specific secrets in Google Secret Manager (dev-nexus-dev_*, dev-nexus-staging_*, dev-nexus-prod_*)
3. **Resource Naming** - No collisions between environments when sharing a GCP project
4. **Configuration Management** - tfvars files define environment-specific settings (scaling, security, resources)
5. **CI/CD Integration** - Cloud Build supports multi-environment deployment via substitution variables

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│         Google Cloud Project (globalbiting-dev)          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   DEV       │  │  STAGING    │  │   PROD      │     │
│  │ Environment │  │ Environment │  │ Environment │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│        ↓                 ↓                 ↓            │
│    Cloud Run        Cloud Run         Cloud Run        │
│   (1 vCPU)         (1 vCPU)          (2 vCPU)          │
│  (Scale-to-0)      (Auth req)       (HA, Always-on)   │
│        ↓                 ↓                 ↓            │
│  Postgres VM        Postgres VM       Postgres VM      │
│  (e2-micro)         (e2-micro)        (e2-small)       │
│        ↓                 ↓                 ↓            │
│  Separate State     Separate State   Separate State    │
│  Bucket: GCS        Bucket: GCS      Bucket: GCS       │
│  Prefix: .../dev    Prefix:.../staging Prefix:.../prod │
│                                                          │
│  Separate Secrets  Separate Secrets Separate Secrets   │
│  dev-nexus-dev_*   dev-nexus-staging_* dev-nexus-prod_*│
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Environment Configurations

### Development (dev)

- **Unauthenticated**: Public API access (test with frontend directly)
- **Scale-to-zero**: Scales to 0 instances when idle (cost savings)
- **Resources**: 1 vCPU, 1GB RAM
- **Database**: e2-micro, 30GB (free tier)
- **State**: `terraform-state-globalbiting-dev/dev-nexus/dev`
- **Secrets**: `dev-nexus-dev_*` in Secret Manager
- **Use case**: Local development, testing, experimentation

### Staging (staging)

- **Authenticated**: API requires authentication (like production)
- **Moderate scaling**: Min 0, Max 10 instances
- **Resources**: 1 vCPU, 2GB RAM
- **Database**: e2-micro, 50GB
- **State**: `terraform-state-globalbiting-dev/dev-nexus/staging`
- **Secrets**: `dev-nexus-staging_*` in Secret Manager
- **External agents**: Service accounts created for orchestrator/log-attacker testing
- **Use case**: Pre-production testing, integration testing

### Production (prod)

- **Authenticated**: API requires authentication
- **High availability**: Min 1, Max 20 instances (always-on, no cold starts)
- **Resources**: 2 vCPU, 2GB RAM, CPU always allocated
- **Database**: e2-small, 100GB
- **State**: `terraform-state-globalbiting-dev/dev-nexus/prod`
- **Secrets**: `dev-nexus-prod_*` in Secret Manager
- **Monitoring**: Cloud Monitoring enabled with alerting
- **Use case**: Production deployment, user traffic

## Quick Start

### 1. Initialize Development Environment

```bash
# Navigate to terraform directory
cd terraform

# Initialize with dev environment
bash scripts/terraform-init.sh dev

# On Windows:
# terraform-init.bat dev
```

### 2. Review the Plan

```bash
terraform plan -var-file="dev.tfvars" -out=tfplan
```

### 3. Apply Configuration

```bash
terraform apply tfplan
```

### 4. View Outputs

```bash
terraform output
```

## Detailed Setup Instructions

### Step 1: Prepare Environment Variables

```bash
export GCP_PROJECT_ID="globalbiting-dev"
export GCP_REGION="us-central1"
export KNOWLEDGE_BASE_REPO="patelmm79/dev-nexus"
```

### Step 2: Create GCS Bucket for Terraform State (One-time)

If not already created:

```bash
gsutil mb gs://terraform-state-${GCP_PROJECT_ID}

# Enable versioning for backup
gsutil versioning set on gs://terraform-state-${GCP_PROJECT_ID}
```

### Step 3: Initialize Terraform for Development

```bash
cd terraform

# Initialize with dev backend prefix
terraform init -backend-config="prefix=dev-nexus/dev"

# Verify
terraform validate
```

### Step 4: Configure Secrets (Important!)

Before applying, update `dev.tfvars` with actual credentials:

```bash
# Get secrets from Secret Manager (or create if not exists)
gcloud secrets versions access latest --secret="dev-nexus-dev_GITHUB_TOKEN"
gcloud secrets versions access latest --secret="dev-nexus-dev_ANTHROPIC_API_KEY"
gcloud secrets versions access latest --secret="dev-nexus-dev_POSTGRES_PASSWORD"

# Update dev.tfvars with actual values
vim dev.tfvars
```

### Step 5: Plan and Apply

```bash
# Review changes
terraform plan -var-file="dev.tfvars" -out=tfplan

# Apply
terraform apply tfplan

# View outputs
terraform output
```

## Switching Between Environments

### From Dev to Staging

```bash
# Reinitialize terraform with staging backend
terraform init -backend-config="prefix=dev-nexus/staging" -reconfigure

# Validate configuration
terraform validate -var-file="staging.tfvars"

# Plan changes
terraform plan -var-file="staging.tfvars" -out=tfplan

# Apply
terraform apply tfplan
```

### From Staging to Production

```bash
# Reinitialize terraform with prod backend
terraform init -backend-config="prefix=dev-nexus/prod" -reconfigure

# **IMPORTANT**: Review prod.tfvars before applying!
# - Update allow_ssh_from_cidrs to YOUR_OFFICE_IP/32
# - Add orchestrator_url and log_attacker_url
# - Add alert_notification_channels

# Validate
terraform validate -var-file="prod.tfvars"

# Create secrets in Secret Manager first
gcloud secrets create dev-nexus-prod_GITHUB_TOKEN --replication-policy=automatic
gcloud secrets versions add dev-nexus-prod_GITHUB_TOKEN --data-file=- < /dev/stdin
# (repeat for ANTHROPIC_API_KEY and POSTGRES_PASSWORD)

# Plan (always review in prod!)
terraform plan -var-file="prod.tfvars" -out=tfplan

# Show plan before applying
terraform show tfplan

# Apply
terraform apply tfplan
```

## Secret Management

### Creating Environment Secrets

```bash
# Create dev secrets (do once)
gcloud secrets create dev-nexus-dev_GITHUB_TOKEN --replication-policy=automatic
gcloud secrets create dev-nexus-dev_ANTHROPIC_API_KEY --replication-policy=automatic
gcloud secrets create dev-nexus-dev_POSTGRES_PASSWORD --replication-policy=automatic

# Add secret values
echo -n "your-github-token" | gcloud secrets versions add dev-nexus-dev_GITHUB_TOKEN --data-file=-
echo -n "your-anthropic-key" | gcloud secrets versions add dev-nexus-dev_ANTHROPIC_API_KEY --data-file=-
echo -n "your-db-password" | gcloud secrets versions add dev-nexus-dev_POSTGRES_PASSWORD --data-file=-

# List secrets
gcloud secrets list --filter="dev-nexus"

# View secret versions
gcloud secrets versions list dev-nexus-dev_GITHUB_TOKEN
```

### Rotating Secrets

```bash
# Add new version
echo -n "new-github-token" | gcloud secrets versions add dev-nexus-dev_GITHUB_TOKEN --data-file=-

# Terraform will automatically use 'latest' version
# Rerun: terraform apply
```

### Retrieving Secrets for tfvars

```bash
# Get development secrets
gcloud secrets versions access latest --secret="dev-nexus-dev_GITHUB_TOKEN" > /tmp/github_token
gcloud secrets versions access latest --secret="dev-nexus-dev_ANTHROPIC_API_KEY" > /tmp/anthropic_key
gcloud secrets versions access latest --secret="dev-nexus-dev_POSTGRES_PASSWORD" > /tmp/db_password

# Update dev.tfvars with values from /tmp files
```

## Terraform State Management

### View State for Specific Environment

```bash
# Dev environment
gsutil ls -r gs://terraform-state-globalbiting-dev/dev-nexus/dev/

# Staging environment
gsutil ls -r gs://terraform-state-globalbiting-dev/dev-nexus/staging/

# Prod environment
gsutil ls -r gs://terraform-state-globalbiting-dev/dev-nexus/prod/
```

### Backup and Restore

```bash
# Backup prod state
gsutil cp gs://terraform-state-globalbiting-dev/dev-nexus/prod/default.tfstate ./prod-backup-$(date +%Y%m%d).tfstate

# Restore prod state (careful!)
gsutil cp ./prod-backup-20240101.tfstate gs://terraform-state-globalbiting-dev/dev-nexus/prod/default.tfstate

# Verify backup succeeded
terraform refresh -var-file="prod.tfvars"
```

## Deployment via Cloud Build

### Manual Cloud Build Deployment

```bash
# Deploy to dev
gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions="_REGION=us-central1,_ENVIRONMENT=dev,_KNOWLEDGE_BASE_REPO=patelmm79/dev-nexus" \
    --project="globalbiting-dev"

# Deploy to staging
gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions="_REGION=us-central1,_ENVIRONMENT=staging,_KNOWLEDGE_BASE_REPO=patelmm79/dev-nexus" \
    --project="globalbiting-dev"

# Deploy to prod
gcloud builds submit \
    --config=cloudbuild.yaml \
    --substitutions="_REGION=us-central1,_ENVIRONMENT=prod,_KNOWLEDGE_BASE_REPO=patelmm79/dev-nexus" \
    --project="globalbiting-dev"
```

### Automated Cloud Build Triggers

Set up separate Cloud Build triggers in GCP Console:

1. **dev-trigger**: Branch = `develop`, substitutions: `_ENVIRONMENT=dev`
2. **staging-trigger**: Branch = `staging`, substitutions: `_ENVIRONMENT=staging`
3. **prod-trigger**: Branch = `main`, substitutions: `_ENVIRONMENT=prod`, require approval

## Using deploy.sh Script

### Deploy to Development

```bash
export GCP_PROJECT_ID="globalbiting-dev"
bash scripts/deploy.sh dev
```

### Deploy to Staging

```bash
bash scripts/deploy.sh staging
```

### Deploy to Production

```bash
bash scripts/deploy.sh prod
```

## Viewing Environment Status

### Check Current Environment

```bash
# Show which environment is currently checked out
terraform show
# (Look for 'prefix' in backend configuration)

# Or check Backend state
terraform state list
```

### Compare Environments

```bash
# Dev state
terraform init -backend-config="prefix=dev-nexus/dev" -reconfigure
terraform state list

# Staging state
terraform init -backend-config="prefix=dev-nexus/staging" -reconfigure
terraform state list

# Prod state
terraform init -backend-config="prefix=dev-nexus/prod" -reconfigure
terraform state list
```

## Common Scenarios

### Scenario 1: Apply Same Change to All Environments

```bash
# 1. Make change to shared file (variables.tf, main.tf, etc.)

# 2. Deploy to dev
terraform init -backend-config="prefix=dev-nexus/dev" -reconfigure
terraform plan -var-file="dev.tfvars" -out=dev.tfplan
terraform apply dev.tfplan

# 3. Deploy to staging
terraform init -backend-config="prefix=dev-nexus/staging" -reconfigure
terraform plan -var-file="staging.tfvars" -out=staging.tfplan
terraform apply staging.tfplan

# 4. Deploy to prod (after approval)
terraform init -backend-config="prefix=dev-nexus/prod" -reconfigure
terraform plan -var-file="prod.tfvars" -out=prod.tfplan
terraform apply prod.tfplan
```

### Scenario 2: Rollback Production

```bash
# Find state backup
gsutil ls gs://terraform-state-globalbiting-dev/dev-nexus/prod/

# Download current state
terraform init -backend-config="prefix=dev-nexus/prod" -reconfigure
terraform state pull > current.tfstate

# View state history
gsutil ls -r -h gs://terraform-state-globalbiting-dev/dev-nexus/prod/

# Restore from backup
gsutil cp gs://terraform-state-globalbiting-dev/dev-nexus/prod/previous-state.tfstate ./
terraform state push ./previous-state.tfstate
```

### Scenario 3: Deploy to New Environment (e.g., disaster-recovery)

```bash
# Create new tfvars file
cp prod.tfvars dr.tfvars
vim dr.tfvars  # Update for DR environment

# Initialize with new prefix
terraform init -backend-config="prefix=dev-nexus/dr" -reconfigure

# Deploy
terraform plan -var-file="dr.tfvars" -out=dr.tfplan
terraform apply dr.tfplan
```

## Troubleshooting

### Issue: State Lock Error

```
Error: Error acquiring the lock
```

**Solution:**
```bash
# Force unlock (use with caution!)
terraform force-unlock <LOCK_ID>

# Or wait for lock to expire (default 10 minutes)
```

### Issue: Backend Prefix Mismatch

```
Error: This configuration doesn't specify a remote backend, but Terraform state
is currently stored in a remote backend with the following configuration...
```

**Solution:**
```bash
# Reinitialize with correct prefix
terraform init -backend-config="prefix=dev-nexus/dev" -reconfigure
```

### Issue: Secret Not Found

```
Error: google_secret_manager_secret_version.github_token: error reading SecretVersion
```

**Solution:**
```bash
# Create the secret
gcloud secrets create dev-nexus-dev_GITHUB_TOKEN --replication-policy=automatic

# Add value
echo -n "your-token" | gcloud secrets versions add dev-nexus-dev_GITHUB_TOKEN --data-file=-

# Try again
terraform apply
```

### Issue: Permission Denied

```
Error: The caller does not have permission secretmanager.secrets.get
```

**Solution:**
```bash
# Grant necessary permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member=user:your-email@example.com \
    --role=roles/secretmanager.secretAccessor

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
    --member=user:your-email@example.com \
    --role=roles/compute.admin
```

## Best Practices

1. **Always Plan Before Apply**: Use `terraform plan -out=tfplan` before applying
2. **Review Prod Changes**: Always review `terraform show tfplan` before prod deployments
3. **Backup State**: `terraform state pull > backup.tfstate` before risky operations
4. **Use Secrets Manager**: Never commit secrets to git or tfvars files
5. **Environment Parity**: Keep dev/staging configs in sync (except resource sizes)
6. **State Locking**: Use remote state (GCS) to prevent concurrent modifications
7. **Separate Providers**: Consider separate GCP projects for prod (added security)
8. **Infrastructure as Code**: All infrastructure changes via Terraform (no manual Cloud Console changes)

## Related Documentation

- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Google Secret Manager](https://cloud.google.com/secret-manager)
- [Terraform Cloud Storage Backend](https://www.terraform.io/language/settings/backends/gcs)
- [CLAUDE.md](CLAUDE.md) - Dev-nexus project guidelines
