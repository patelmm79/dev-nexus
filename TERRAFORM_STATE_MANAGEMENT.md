# Terraform State Management

This document explains how dev-nexus manages Terraform state for multi-environment deployments, including state capture, backup, recovery, and disaster recovery procedures.

## Overview

Terraform state is the **source of truth** for infrastructure configuration. It tracks:
- All deployed resources (Cloud Run services, PostgreSQL VMs, networks, etc.)
- Resource dependencies and configurations
- Sensitive data (secrets, passwords, API keys)

**Critical**: Losing state can require complete infrastructure recreation. This system implements multiple safeguards to prevent data loss.

## State Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Google Cloud Project                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Google Cloud Storage (GCS) Buckets              │  │
│  ├──────────────────────────────────────────────────┤  │
│  │                                                  │  │
│  │  Primary State Bucket:                          │  │
│  │  gs://terraform-state-globalbiting-dev/         │  │
│  │  ├─ dev-nexus/dev/default.tfstate               │  │
│  │  ├─ dev-nexus/staging/default.tfstate           │  │
│  │  └─ dev-nexus/prod/default.tfstate              │  │
│  │                                                  │  │
│  │  Backup Bucket:                                 │  │
│  │  gs://terraform-state-globalbiting-dev-backups/ │  │
│  │  ├─ dev-nexus-dev-20240115-143022.tfstate       │  │
│  │  ├─ dev-nexus-staging-20240115-143022.tfstate   │  │
│  │  └─ dev-nexus-prod-20240115-143022.tfstate      │  │
│  │                                                  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Features:                                              │
│  • Versioning: Keep 10 versions per state file         │
│  • Lifecycle: Delete old versions after 90 days        │
│  • Logging: All access logged                          │
│  • Backups: Manual backup to separate bucket           │
│  • Lock: Automatic locking during apply                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

## State Capture & Storage

### Initial Setup (One-time)

```bash
# Set up the remote GCS backend
export GCP_PROJECT_ID="globalbiting-dev"
bash scripts/setup-terraform-backend.sh

# This creates:
# - Primary state bucket: gs://terraform-state-globalbiting-dev/
# - Backup bucket: gs://terraform-state-globalbiting-dev-backups/
# - Enables versioning, lifecycle policies, and logging
```

### Environment-Specific State

Each environment has its own state file with isolated prefix:

```
Primary State Bucket:
  dev-nexus/dev/       -> Development state
  dev-nexus/staging/   -> Staging state
  dev-nexus/prod/      -> Production state
```

### How State is Captured

```bash
# When you run terraform apply:
cd terraform

# 1. Initialize with environment-specific prefix
terraform init -backend-config="prefix=dev-nexus/dev"

# 2. Show plan
terraform plan -var-file="dev.tfvars" -out=tfplan

# 3. Apply configuration
terraform apply tfplan

# What happens:
# ✓ Terraform creates/updates resources on GCP
# ✓ State is automatically captured and uploaded to GCS
# ✓ Previous version preserved (versioning enabled)
# ✓ All changes logged for audit trail
```

### State Lock

During `terraform apply`, Terraform automatically locks the state to prevent concurrent modifications:

```bash
# Lock details stored in GCS
# Lock timeout: 10 minutes
# Lock message: Includes timestamp and unique ID

# View locks (if stuck):
# gsutil ls -r gs://terraform-state-globalbiting-dev/.terraform-lock.*

# Force unlock (if necessary):
# terraform force-unlock <LOCK_ID>
```

## Automatic State Versioning

GCS versioning automatically preserves state history:

```bash
# View state file versions
gsutil ls -h gs://terraform-state-globalbiting-dev/dev-nexus/dev/

# Output:
#   gs://terraform-state-globalbiting-dev/dev-nexus/dev/default.tfstate#1702648400000000
#   gs://terraform-state-globalbiting-dev/dev-nexus/dev/default.tfstate#1702648500000000
#   gs://terraform-state-globalbiting-dev/dev-nexus/dev/default.tfstate#1702648600000000

# Lifecycle policy:
# - Keeps: 10 versions per state file
# - Deletes: Non-current versions older than 90 days
```

## Manual State Backup

### Backup All Environments

```bash
# Backs up all environments to backup bucket
bash scripts/backup-terraform-state.sh

# Creates backups:
# - dev-nexus-dev-20240115-143022.tfstate
# - dev-nexus-staging-20240115-143022.tfstate
# - dev-nexus-prod-20240115-143022.tfstate

# Useful before risky operations:
# - Major infrastructure changes
# - Terraform upgrades
# - Permission changes
# - Security patches
```

### Backup Specific Environment

```bash
# Backup only production before risky change
bash scripts/backup-terraform-state.sh prod

# Backup only staging
bash scripts/backup-terraform-state.sh staging
```

### Backup Retention

```
Backup Bucket Policy:
- Versioning: Enabled
- Retention: 30 days (old backups auto-deleted)
- Location: gs://terraform-state-globalbiting-dev-backups/
```

## State Recovery

### List Available Backups

```bash
# View all backups for production
bash scripts/recover-terraform-state.sh prod

# Output:
#   20240115-143022 (size: 245K)
#   20240114-091500 (size: 246K)
#   20240113-085900 (size: 244K)
```

### Recover from Backup

```bash
# Recover production to specific backup
bash scripts/recover-terraform-state.sh prod 20240115-143022

# Script automatically:
# 1. Downloads backup
# 2. Creates safety backup of current state
# 3. Restores state from backup
# 4. Verifies restoration success
# 5. Shows review steps

# After recovery, always verify:
terraform state list
terraform plan -var-file="prod.tfvars"
```

### Manual Recovery (Advanced)

```bash
# Download backup manually
gsutil cp gs://terraform-state-globalbiting-dev-backups/dev-nexus-prod-20240115-143022.tfstate ./

# Switch to environment
cd terraform
terraform init -backend-config="prefix=dev-nexus/prod" -reconfigure

# Verify current state
terraform state pull > current-backup.tfstate

# Push recovered state
terraform state push ./dev-nexus-prod-20240115-143022.tfstate

# Verify
terraform state list
terraform plan -var-file="prod.tfvars"

# If something wrong, restore current backup
terraform state push ./current-backup.tfstate
```

## State Inspection

### View Current State

```bash
# List all resources in current state
terraform state list

# Show specific resource
terraform state show 'google_cloud_run_v2_service.pattern_discovery_agent'

# Show entire state (verbose)
terraform show

# Export state as JSON
terraform state pull > state.json
```

### Remote State Inspection

```bash
# Download state file directly from GCS
gsutil cp gs://terraform-state-globalbiting-dev/dev-nexus/prod/default.tfstate ./prod-state.json

# Inspect with jq
cat prod-state.json | jq '.resources[0]'

# Check last modified time
gsutil stat gs://terraform-state-globalbiting-dev/dev-nexus/prod/default.tfstate
```

### State Size and History

```bash
# Current state file size
gsutil stat -h gs://terraform-state-globalbiting-dev/dev-nexus/prod/default.tfstate

# All state file versions and sizes
gsutil ls -Lh gs://terraform-state-globalbiting-dev/dev-nexus/prod/

# State growth over time
gsutil ls -h gs://terraform-state-globalbiting-dev-backups/ | grep "prod"
```

## State Troubleshooting

### State Lock Error

```
Error: Error acquiring the lock
```

**Cause**: Previous terraform operation didn't complete (crashed, network failure, etc.)

**Solution**:
```bash
# List locks
gsutil ls -r gs://terraform-state-globalbiting-dev/.terraform-lock.*

# Force unlock (use with caution!)
terraform force-unlock <LOCK_ID>

# Then retry operation
terraform apply
```

### State Corruption

```
Error: "invalid character..."
```

**Cause**: State file corrupted (rare, usually from manual edits)

**Solution**:
```bash
# Check backup
gsutil ls -h gs://terraform-state-globalbiting-dev-backups/

# Recover from backup
bash scripts/recover-terraform-state.sh prod

# Verify
terraform state list
```

### State Drift (Resources changed outside Terraform)

```
# Terraform shows different state than actual resources
terraform plan  # Shows unexpected changes

# Solution: Refresh state
terraform refresh
terraform state pull  # Review changes

# Then decide:
# Option A: Accept changes and update state
terraform apply

# Option B: Recreate resources as per terraform
terraform destroy
terraform apply
```

### Lost State Scenario

```
Scenario: State file accidentally deleted from GCS
```

**Recovery Steps**:

```bash
# 1. Check if version exists
gsutil ls -h gs://terraform-state-globalbiting-dev/dev-nexus/prod/default.tfstate

# 2. List available versions
gsutil ls -L gs://terraform-state-globalbiting-dev/dev-nexus/prod/

# 3. Restore previous version
gsutil cp gs://terraform-state-globalbiting-dev/dev-nexus/prod/default.tfstate#<VERSION_ID> \
    gs://terraform-state-globalbiting-dev/dev-nexus/prod/default.tfstate

# 4. Or recover from backup
bash scripts/recover-terraform-state.sh prod
```

## State Security Best Practices

### Sensitive Data in State

State files contain sensitive information:
- Database passwords
- API keys (GitHub, Anthropic)
- SSH private keys
- Auth tokens

**Protection**:
```bash
# 1. State stored in private GCS bucket
# 2. Bucket versioning prevents deletion
# 3. Access logged and audited
# 4. In-transit encryption (GCS enforced)
# 5. At-rest encryption (GCS enforced)

# 6. Never commit state to git
.gitignore contains:
  *.tfstate
  *.tfstate.*
  .terraform/

# 7. Audit access
gcloud logging read "resource.type=gcs_bucket AND protoPayload.resourceName=~\"terraform-state-*\""
```

### Rotating Secrets in State

```bash
# Update secret in Secret Manager
gcloud secrets versions add GITHUB_TOKEN --data-file=-

# Terraform will automatically use 'latest' version
# Re-run apply to refresh
terraform apply

# State will be updated with new secret reference
terraform state pull | jq '.resources[] | select(.type=="google_secret_manager_secret_version")'
```

## Disaster Recovery Scenarios

### Scenario 1: Complete Project Loss

```
Situation: Accidentally deleted GCP project
```

**Recovery**:
```bash
# 1. State is safe in GCS (separate project if possible)
# 2. Recreate GCP project
# 3. Restore state to new project
terraform init -backend-config="prefix=dev-nexus/prod" -reconfigure
terraform apply -refresh-only
```

### Scenario 2: Infrastructure Corruption

```
Situation: Resources manually deleted or modified in GCP Console
```

**Recovery**:
```bash
# 1. Terraform will detect drift
terraform plan

# 2. Shows what needs to be recreated
# 3. Either:
#    - Accept changes: terraform state rm <resource>
#    - Rebuild: terraform apply (recreates resources)
```

### Scenario 3: Multi-Environment Sync

```
Scenario: Restore prod state to staging for testing
```

```bash
# 1. Download prod state
gsutil cp gs://terraform-state-globalbiting-dev/dev-nexus/prod/default.tfstate ./prod-state.json

# 2. Switch to staging backend
terraform init -backend-config="prefix=dev-nexus/staging" -reconfigure

# 3. Replace staging state with prod backup (CAREFUL!)
terraform state push ./prod-state.json

# 4. Update resource names/configurations as needed
terraform state list

# 5. This allows testing prod changes in staging
```

## CI/CD State Management

### Cloud Build Integration

```yaml
# cloudbuild.yaml handles state automatically:
# 1. Checks out Terraform code
# 2. Initializes with correct backend prefix
# 3. Runs terraform plan
# 4. (On approval) Runs terraform apply
# 5. State captured and versioned automatically
```

### State Locking in CI/CD

```bash
# During builds, Terraform locks state automatically
# Lock prevents concurrent applies to same environment

# If build times out:
# - Lock automatically released after 10 minutes
# - Manual unlock: terraform force-unlock <ID>
```

## Monitoring & Alerting

### State Growth

```bash
# Monitor state file size (can indicate resource accumulation)
watch -n 60 'gsutil stat -h gs://terraform-state-globalbiting-dev/dev-nexus/prod/default.tfstate | grep "Content length"'

# Alert if state > 10MB (indicates too many resources)
```

### State Access Audit

```bash
# View who accessed state
gcloud logging read --limit=50 \
  "resource.type=gcs_bucket AND protoPayload.methodName=storage.objects.get" \
  --format=json

# Set up alerting in Cloud Monitoring
# Alert on: Unusual access patterns, failed access attempts
```

## Related Documentation

- [TERRAFORM_UNIFIED_INIT.md](TERRAFORM_UNIFIED_INIT.md) - Unified initialization pattern with backend configuration
- [MULTI_ENV_SETUP.md](MULTI_ENV_SETUP.md) - Environment configuration and deployment
- [terraform/README.md](terraform/README.md) - Terraform infrastructure guide
- [CLAUDE.md](CLAUDE.md) - Overall project architecture
- [Terraform GCS Backend](https://www.terraform.io/language/settings/backends/gcs)
- [GCS Versioning & Lifecycle](https://cloud.google.com/storage/docs/object-lock/overview)
