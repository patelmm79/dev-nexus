# Unified Terraform Initialization Pattern

This guide shows how to initialize Terraform consistently across **all projects** (dev-nexus, resume-customizer, etc.) with a single standardized command pattern.

## Problem Solved

Previously, each project had different initialization commands:
- Resume-customizer: `terraform init -backend-config="bucket=globalbiting-dev-terraform-state" -backend-config="prefix=resume-customizer/dev"`
- Dev-nexus: `terraform init -backend-config="prefix=dev-nexus/dev"` (bucket hardcoded)

**Result**: Inconsistency, confusion, manual errors

## Unified Solution

All projects now use:
```bash
terraform init \
  -backend-config="bucket=globalbiting-dev-terraform-state" \
  -backend-config="prefix=<project-name>/<environment>"
```

## Configuration

### Shared Backend Bucket

All projects store state in the **same bucket** with **project-specific prefixes**:

```
gs://globalbiting-dev-terraform-state/
├─ dev-nexus/dev/default.tfstate
├─ dev-nexus/staging/default.tfstate
├─ dev-nexus/prod/default.tfstate
├─ resume-customizer/dev/default.tfstate
├─ resume-customizer/staging/default.tfstate
├─ resume-customizer/prod/default.tfstate
└─ <other-projects>/...
```

### Backend Files (Removed Hardcoding)

Each project's `main.tf` now has empty backend block:

```hcl
# terraform/main.tf
terraform {
  backend "gcs" {
    # Bucket and prefix configured via terraform init CLI flags
  }
}
```

This allows flexible backend configuration via command line.

## Usage: Helper Script (Recommended)

### Quick Start

```bash
cd terraform

# Initialize development environment
bash scripts/terraform-init-unified.sh dev

# Initialize staging environment
bash scripts/terraform-init-unified.sh staging

# Initialize production environment
bash scripts/terraform-init-unified.sh prod
```

**That's it!** The script automatically:
- ✅ Detects project name from directory
- ✅ Sets correct bucket and prefix
- ✅ Handles reconfiguration when switching environments
- ✅ Validates configuration
- ✅ Shows next steps

### How Script Works

```bash
bash scripts/terraform-init-unified.sh dev
    ↓
PROJECT_NAME = dev-nexus (auto-detected)
ENVIRONMENT = dev (from parameter)
STATE_BUCKET = globalbiting-dev-terraform-state (default)
    ↓
terraform init \
  -backend-config="bucket=globalbiting-dev-terraform-state" \
  -backend-config="prefix=dev-nexus/dev"
    ↓
State path: gs://globalbiting-dev-terraform-state/dev-nexus/dev/default.tfstate
```

### Custom Project Name (if needed)

```bash
# Override project name for a different project
PROJECT_NAME=resume-customizer bash scripts/terraform-init-unified.sh dev

# This creates state at:
# gs://globalbiting-dev-terraform-state/resume-customizer/dev/default.tfstate
```

### Custom Bucket (if needed)

```bash
# Use different bucket
TERRAFORM_STATE_BUCKET=my-custom-bucket bash scripts/terraform-init-unified.sh dev

# This creates state at:
# gs://my-custom-bucket/dev-nexus/dev/default.tfstate
```

## Usage: Manual Command (Advanced)

If you prefer explicit commands:

```bash
# Development
terraform init \
  -backend-config="bucket=globalbiting-dev-terraform-state" \
  -backend-config="prefix=dev-nexus/dev"

# Staging (reconfigure to switch environments)
terraform init \
  -backend-config="bucket=globalbiting-dev-terraform-state" \
  -backend-config="prefix=dev-nexus/staging" \
  -reconfigure

# Production (reconfigure to switch environments)
terraform init \
  -backend-config="bucket=globalbiting-dev-terraform-state" \
  -backend-config="prefix=dev-nexus/prod" \
  -reconfigure
```

## Across Multiple Projects

### Scenario 1: Working on dev-nexus

```bash
cd ~/projects/dev-nexus/terraform

# Initialize dev environment
bash scripts/terraform-init-unified.sh dev

# Now you're working on dev-nexus/dev state
# gs://globalbiting-dev-terraform-state/dev-nexus/dev/default.tfstate
```

### Scenario 2: Switch to resume-customizer

```bash
cd ~/projects/resume-customizer/terraform

# Initialize dev environment
bash scripts/terraform-init-unified.sh dev

# Now you're working on resume-customizer/dev state
# gs://globalbiting-dev-terraform-state/resume-customizer/dev/default.tfstate
```

### Scenario 3: Back to dev-nexus prod

```bash
cd ~/projects/dev-nexus/terraform

# Initialize prod environment (auto-reconfigures)
bash scripts/terraform-init-unified.sh prod

# Now you're working on dev-nexus/prod state
# gs://globalbiting-dev-terraform-state/dev-nexus/prod/default.tfstate
```

## Environment Variables

You can customize behavior without modifying scripts:

```bash
# Use different bucket for this initialization
export TERRAFORM_STATE_BUCKET="my-backup-bucket"
bash scripts/terraform-init-unified.sh dev

# Use different project name
export PROJECT_NAME="my-custom-project"
bash scripts/terraform-init-unified.sh dev

# Both together
export TERRAFORM_STATE_BUCKET="backup-bucket"
export PROJECT_NAME="my-app"
bash scripts/terraform-init-unified.sh prod
```

## Verify Initialization

After running init, verify state location:

```bash
# Check current backend configuration
terraform show -no-color | grep -A 10 "backend"

# Or list state file in GCS
gsutil ls -h gs://globalbiting-dev-terraform-state/dev-nexus/dev/

# Or pull current state and check
terraform state pull | head -20
```

## State Isolation Guarantee

```
┌─────────────────────────────────────────────┐
│     gs://globalbiting-dev-terraform-state/  │
├─────────────────────────────────────────────┤
│                                             │
│  dev-nexus/dev/default.tfstate             │
│  ✓ Isolated from resume-customizer         │
│  ✓ Isolated from other projects            │
│  ✓ Safe to destroy without affecting others│
│                                             │
│  resume-customizer/dev/default.tfstate     │
│  ✓ Isolated from dev-nexus                 │
│  ✓ Can be backed up independently          │
│  ✓ Can be restored independently           │
│                                             │
│  <project>/prod/default.tfstate            │
│  ✓ Production isolated in same bucket      │
│                                             │
└─────────────────────────────────────────────┘
```

## State Bucket Setup (One-time)

```bash
# Create shared state bucket (do this once per GCP project)
export GCP_PROJECT_ID="globalbiting-dev"

gsutil mb gs://globalbiting-dev-terraform-state/

# Enable versioning
gsutil versioning set on gs://globalbiting-dev-terraform-state/

# Set lifecycle policy
cat > /tmp/lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"numNewerVersions": 10}
      },
      {
        "action": {"type": "Delete"},
        "condition": {"isLive": false, "age": 90}
      }
    ]
  }
}
EOF

gsutil lifecycle set /tmp/lifecycle.json gs://globalbiting-dev-terraform-state/
```

## Troubleshooting

### Issue: "backend is already configured"

```
Error: Unsupported backend argument
```

**Solution:** Use `-reconfigure` flag when switching environments

```bash
bash scripts/terraform-init-unified.sh staging  # Auto-handles -reconfigure
# Or manually:
terraform init \
  -backend-config="bucket=globalbiting-dev-terraform-state" \
  -backend-config="prefix=dev-nexus/staging" \
  -reconfigure
```

### Issue: Wrong bucket being used

```bash
# Verify current bucket
terraform state pull | jq .terraform_version

# Reset and reconfigure
rm -rf .terraform
bash scripts/terraform-init-unified.sh dev
```

### Issue: State already exists elsewhere

```bash
# If state exists in old location and you want to migrate:
terraform state pull > backup.tfstate

# Then init with new backend
terraform init \
  -backend-config="bucket=globalbiting-dev-terraform-state" \
  -backend-config="prefix=dev-nexus/dev"

# Say 'no' when asked to copy existing state (if you're switching projects)
# Or say 'yes' if migrating from local/old backend
```

## CI/CD Integration

Both Cloud Build and GitHub Actions can use the unified pattern:

### Cloud Build (cloudbuild.yaml)

```yaml
steps:
  - name: 'gcr.io/cloud-builders/gke-deploy'
    args:
      - 'run'
      - 'apply'
      - '--cloud-build-config=cloudbuild.yaml'
      - '--config=terraform'

  - name: 'hashicorp/terraform:latest'
    entrypoint: 'sh'
    args:
      - '-c'
      - |
        cd terraform
        terraform init \
          -backend-config="bucket=${_STATE_BUCKET}" \
          -backend-config="prefix=${_PROJECT_NAME}/${_ENVIRONMENT}"
        terraform apply -auto-approve -var-file="${_ENVIRONMENT}.tfvars"
    env:
      - '_STATE_BUCKET=globalbiting-dev-terraform-state'
      - '_PROJECT_NAME=dev-nexus'
      - '_ENVIRONMENT=${_ENVIRONMENT}'
```

### GitHub Actions

```yaml
- name: Terraform Init
  run: |
    cd terraform
    terraform init \
      -backend-config="bucket=globalbiting-dev-terraform-state" \
      -backend-config="prefix=${{ github.event.repository.name }}/${{ inputs.environment }}"
    terraform plan -var-file="${{ inputs.environment }}.tfvars"
```

## Benefits

✅ **Consistency**: Same pattern across all projects
✅ **Efficiency**: Single command, no manual bucket/prefix configuration
✅ **Safety**: State isolation prevents cross-project accidents
✅ **Scalability**: Easy to add new projects (just use same bucket, new prefix)
✅ **Automation**: CI/CD can use consistent initialization
✅ **Flexibility**: Override defaults with environment variables

## Related Documentation

- [MULTI_ENV_SETUP.md](MULTI_ENV_SETUP.md) - Environment-specific configuration
- [TERRAFORM_STATE_MANAGEMENT.md](TERRAFORM_STATE_MANAGEMENT.md) - State backup/recovery
- [resume-customizer README_DEPLOY.md](https://github.com/patelmm79/resume-customizer/blob/main/README_DEPLOY.md) - Reference implementation
