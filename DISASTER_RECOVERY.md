# Disaster Recovery & State Management

This guide explains the disaster recovery infrastructure that prevents data loss from infrastructure changes and temporary cloud instance destruction.

## Problem

Previously, running `terraform apply` multiple times on temporary cloud instances could accidentally destroy infrastructure (like the PostgreSQL VM) due to local Terraform state being lost between sessions. This caused data loss despite having persistent disk setup.

## Solution: Remote State + Automated Backups

The system now uses three layers of protection:

### 1. Remote Terraform State (GCS Backend)

**What it does**: Stores Terraform state in a shared Google Cloud Storage bucket instead of locally

**Benefits**:
- Terraform state persists even if the instance running Terraform is destroyed
- Multiple temporary instances can safely run Terraform without losing state
- Prevents accidental resource destruction from state inconsistency
- Enables team collaboration on infrastructure

**How it works**:
```
Local Terraform Run (temporary instance)
    ↓
    ├─ terraform init (downloads state from GCS)
    ├─ terraform plan (compares to remote state)
    └─ terraform apply (updates both GCS and GCP)
    ↓
State saved to: gs://terraform-state-{PROJECT_ID}/dev-nexus/
```

### 2. Automated Daily Disk Snapshots

**What it does**: Creates automatic snapshots of the PostgreSQL persistent disk every day at 2 AM UTC

**Benefits**:
- Point-in-time recovery for data
- 30-day retention (keeps last 30 days of snapshots)
- Automatic via GCP resource policies (no manual intervention)
- Can restore to any snapshot date

**How it works**:
```
PostgreSQL Persistent Disk (dev-nexus-postgres-data)
    ↓
Daily at 2 AM UTC (GCP Resource Policy)
    ↓
Create Snapshot → Store in GCS → Keep 30 days
```

### 3. Manual Backup Script

**What it does**: Provides on-demand backup capability using `pg_dump`

**Benefits**:
- Full database backup compressed with gzip
- Uploaded to GCS for long-term storage
- Automatic cleanup of backups older than 30 days
- Can be scheduled via Cloud Scheduler for periodic backups

**Usage**:
```bash
# Run manually
bash scripts/backup-postgres.sh

# Schedule via Cloud Scheduler (optional)
gcloud scheduler jobs create pubsub postgres-backup \
  --schedule="0 2 * * *" \
  --message-body='{"action": "backup"}' \
  --topic=postgres-backups
```

## Setup Instructions

### Initial Setup (One-time)

On your GCP cloud instance:

```bash
cd ~/dev-nexus

# 1. Create shared Terraform state bucket with versioning
bash scripts/setup-terraform-state.sh

# 2. Initialize Terraform with remote backend
cd terraform
terraform init

# When prompted about existing state, answer: yes (to migrate local state to GCS)
```

### What `setup-terraform-state.sh` Does

1. **Creates GCS bucket**: `terraform-state-{PROJECT_ID}` (e.g., `terraform-state-globalbiting-dev`)
2. **Enables versioning**: Protects against accidental deletion
3. **Sets lifecycle policy**:
   - Keeps 5 versions of state
   - Deletes non-current versions after 30 days
4. **Enables logging**: Tracks bucket access for audit

### What `terraform init` Does (after bucket exists)

1. **Connects to GCS backend**
2. **Migrates local state** to remote (if present)
3. **Configures local Terraform** to use remote state going forward
4. **Creates `.terraform` backend config**

## Usage

### Normal Terraform Operations

After initial setup, use Terraform normally:

```bash
cd terraform

# Create infrastructure
terraform apply

# Destroy infrastructure (safely - state prevents accidents)
terraform destroy

# Switch to another temporary instance
# (state is preserved in GCS, no risk of data loss)
```

### Verifying State Backup

Check that Terraform state is stored in GCS:

```bash
# List all terraform state versions
gsutil ls -L gs://terraform-state-globalbiting-dev/dev-nexus/

# Download current state for inspection
gsutil cp gs://terraform-state-globalbiting-dev/dev-nexus/default.tfstate .
```

### Creating Manual Database Backup

```bash
# Create backup immediately
bash scripts/backup-postgres.sh

# Verify backup was created
gsutil ls gs://dev-nexus-postgres-backups/

# Restore from backup if needed
gsutil cp gs://dev-nexus-postgres-backups/devnexus_YYYY-MM-DD_HH-MM-SS.sql.gz .
gunzip devnexus_YYYY-MM-DD_HH-MM-SS.sql.gz
psql -h POSTGRES_IP -U devnexus -d devnexus < devnexus_YYYY-MM-DD_HH-MM-SS.sql
```

## Verification Checklist

After setup, verify disaster recovery is working:

- [ ] **Terraform State**
  - [ ] Run `terraform state list` - shows resources
  - [ ] Run `gsutil ls gs://terraform-state-globalbiting-dev/dev-nexus/` - shows state file in GCS
  - [ ] Run `gcloud storage buckets describe gs://terraform-state-globalbiting-dev --format="value(versioning.enabled)"` - returns "True"

- [ ] **Disk Snapshots**
  - [ ] Run `gcloud compute resource-policies list --filter="name:postgres-daily-snapshots"` - shows policy exists
  - [ ] Check policy details: `gcloud compute resource-policies describe postgres-daily-snapshots`

- [ ] **Backup Script**
  - [ ] Run `bash scripts/backup-postgres.sh` - completes successfully
  - [ ] Check GCS: `gsutil ls gs://dev-nexus-postgres-backups/` - shows backup file

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Disaster Recovery System                     │
└─────────────────────────────────────────────────────────────────┘

                        Remote State (GCS)
                  terraform-state-globalbiting-dev/
                    ├─ dev-nexus/default.tfstate
                    └─ (versioned, keeps 30 days)

                             ▲
                             │ (managed by Terraform)
                             │
┌────────────────────────────┴───────────────────────────┐
│                                                        │
│         Temporary Cloud Instance                       │
│         (destroyed after terraform run)                │
│                                                        │
│    ┌─────────────────────────────────────────┐         │
│    │  terraform init/plan/apply              │         │
│    │  (syncs with GCS backend)               │         │
│    │  (downloads/uploads state)              │         │
│    └─────────────────────────────────────────┘         │
│                                                        │
└────────────────────────┬───────────────────────────────┘
                         │
                         │ manages
                         ▼
          PostgreSQL VM + Persistent Disk
                         │
                         ├─ Boot Disk (20GB)
                         │
                         └─ Data Disk (100GB, persistent)
                            ├─ Auto-snapshot daily @ 2 AM UTC
                            │  └─ gs://postgres-snapshots/
                            │
                            └─ Manual backups
                               └─ gs://dev-nexus-postgres-backups/
```

## Recovery Procedures

### Scenario 1: Terraform Instance Destroyed

**Problem**: Cloud instance running Terraform is deleted

**Solution**: State is safe in GCS
```bash
# Create new instance
gcloud compute instances create terraform-instance

# SSH into new instance, clone repo, setup state
cd ~/dev-nexus
bash scripts/setup-terraform-state.sh
cd terraform
terraform init  # Fetches state from GCS
terraform plan  # Shows current infrastructure
```

### Scenario 2: PostgreSQL Data Corrupted

**Problem**: Database has corruption or unwanted changes

**Solution**: Restore from daily snapshot
```bash
# List available snapshots
gcloud compute snapshots list --filter="source_disk:postgres-data"

# Create disk from snapshot
gcloud compute disks create postgres-data-restored \
  --source-snapshot=postgres-data-TIMESTAMP \
  --zone=us-central1-a

# Attach to VM and restore
# (detailed instructions depend on your recovery RTO/RPO requirements)
```

### Scenario 3: Full Infrastructure Loss

**Problem**: Entire GCP project or resource deleted

**Solution**: Recreate from Terraform + restore data
```bash
# Recreate infrastructure from state
cd terraform
terraform apply

# Restore database from backup
bash scripts/backup-postgres.sh  # (or restore from previous backup)
```

## Cost Considerations

- **GCS State Bucket**: ~$0.02/GB/month for storage + versioning
- **Daily Snapshots**: ~$0.05 per snapshot, 30 retained = ~$1.50/month
- **Manual Backups**: Same as snapshots, depends on backup frequency

Total cost: ~$10-20/month for complete disaster recovery

## Best Practices

1. **Always run `terraform init` before `terraform apply`** on any instance
2. **Keep GCS bucket versioning enabled** - protects against accidental deletes
3. **Test recovery procedures quarterly** - ensure backups are restorable
4. **Monitor backup completion** - set Cloud Logging alerts for backup failures
5. **Document your RTO/RPO requirements** - determines backup frequency needed
6. **Store secrets separately** - Terraform state contains sensitive data
   - Use Secret Manager for credentials
   - Restrict GCS bucket access with IAM

## Troubleshooting

### `terraform init` fails with "bucket doesn't exist"

```bash
# Run setup script first
bash scripts/setup-terraform-state.sh
```

### `terraform init` asks about state migration

This is expected when migrating from local to remote state:
```
Do you want to copy existing state to the new backend?
```
Answer: **yes** (to preserve your infrastructure state)

### Snapshots not being created

```bash
# Check resource policy exists
gcloud compute resource-policies describe postgres-daily-snapshots

# Check policy is attached to disk
gcloud compute disks describe postgres-data --zone=us-central1-a
```

### Backup script fails

```bash
# Verify PostgreSQL is running
gcloud compute ssh dev-nexus-postgres --zone=us-central1-a --command="pg_isready"

# Check GCS bucket permissions
gsutil ls gs://dev-nexus-postgres-backups/

# View backup script logs
bash -x scripts/backup-postgres.sh
```

## Related Documentation

- [CLAUDE.md](CLAUDE.md#deploying-a2a-server-to-cloud-run) - Deployment instructions
- [SETUP_MONITORING.md](SETUP_MONITORING.md) - GitHub Actions workflow setup
- [INTEGRATION.md](INTEGRATION.md) - External agent integration
- [terraform/README.md](terraform/README.md) - Terraform configuration details
