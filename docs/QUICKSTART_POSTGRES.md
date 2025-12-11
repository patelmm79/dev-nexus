# Quick Start: PostgreSQL Deployment

**Deploy PostgreSQL with pgvector in 15 minutes** using GCP Free Tier.

## Prerequisites Checklist

- ✅ GCP account with billing enabled
- ✅ Terraform installed (`terraform --version`)
- ✅ gcloud CLI installed and authenticated (`gcloud auth login`)
- ✅ GitHub token (https://github.com/settings/tokens)
- ✅ Anthropic API key (https://console.anthropic.com)
- ✅ Strong PostgreSQL password ready

## Step 1: Configure Terraform (2 minutes)

```bash
cd terraform

# Copy example configuration
cp terraform.tfvars.example terraform.tfvars

# Edit configuration
nano terraform.tfvars  # or use your preferred editor
```

**Required fields:**
```hcl
project_id            = "your-gcp-project-id"
region                = "us-central1"  # Free tier eligible
github_token          = "ghp_xxxxx"
anthropic_api_key     = "sk-ant-xxxxx"
knowledge_base_repo   = "username/dev-nexus"
postgres_db_password  = "STRONG-PASSWORD-HERE"  # NEW!
```

**Tip:** Use FREE tier settings:
```hcl
postgres_machine_type = "e2-micro"  # FREE tier
postgres_disk_size_gb = 30          # FREE tier
min_instances         = 0           # Scale to zero
allow_unauthenticated = true        # For testing (disable in prod)
```

## Step 2: Deploy Infrastructure (10 minutes)

```bash
# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy!
terraform apply
# Type 'yes' when prompted
```

**What's being deployed:**
- VPC network and firewall rules
- PostgreSQL VM (e2-micro, FREE!)
- pgvector extension
- Automated backups
- VPC connector
- Cloud Run service with database connection

**Expected output:**
```
Apply complete! Resources: 15 added, 0 changed, 0 destroyed.

Outputs:
postgres_internal_ip = "10.8.0.2"
postgres_connection_string = "postgresql://devnexus:****@10.8.0.2:5432/devnexus"
service_url = "https://pattern-discovery-agent-xxxxx.run.app"
```

## Step 3: Verify Deployment (1 minute)

```bash
# Test Cloud Run health
SERVICE_URL=$(terraform output -raw service_url)
curl $SERVICE_URL/health | jq

# Expected response:
{
  "status": "healthy",
  "database": {
    "status": "healthy",
    "pgvector_version": "0.6.0"
  },
  "database_type": "postgresql",
  "pgvector_enabled": true
}
```

## Step 4: Migrate Existing Data (Optional, 5 minutes)

If you have existing JSON knowledge base:

```bash
# Get database IP
POSTGRES_IP=$(terraform output -raw postgres_internal_ip)

# Run migration (from your local machine or Cloud Shell)
cd ..  # Back to project root

python scripts/migrate_json_to_postgres.py \
  --json-url https://raw.githubusercontent.com/YOUR-USER/YOUR-REPO/main/knowledge_base.json \
  --db-host $POSTGRES_IP \
  --db-name devnexus \
  --db-user devnexus \
  --db-password YOUR-PASSWORD \
  --generate-embeddings  # Optional: generates OpenAI embeddings

# Expected output:
Migration complete!
Repositories:       5
Patterns:           127
Embeddings generated: 127
Errors:              0
```

## Step 5: Enable PostgreSQL in Cloud Run (1 minute)

PostgreSQL is deployed but Cloud Run needs to be configured to use it:

```bash
# Update Cloud Run environment variable
gcloud run services update pattern-discovery-agent \
  --region=us-central1 \
  --update-env-vars USE_POSTGRESQL=true

# Verify
curl $SERVICE_URL/health | jq '.database_type'
# Should return: "postgresql"
```

## Step 6: Generate Embeddings (Optional)

If you want semantic pattern search:

```bash
# Set OpenAI API key in Cloud Run
gcloud run services update pattern-discovery-agent \
  --region=us-central1 \
  --update-env-vars OPENAI_API_KEY=sk-xxxxx

# Or generate embeddings via migration script (shown in Step 4)
```

## Verify pgvector Installation

SSH into VM and test:

```bash
# SSH to PostgreSQL VM
terraform output -raw postgres_ssh_command | bash

# Once inside VM, test pgvector
sudo -u postgres psql -d devnexus -c "
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
"

# Expected output:
 extname | extversion
---------+------------
 vector  | 0.6.0

# Test vector operations
sudo -u postgres psql -d devnexus -c "
SELECT vector_dims(ARRAY[1,2,3]::vector);
"

# Expected output:
 vector_dims
-------------
           3

# Exit VM
exit
```

## Cost Verification

Your setup should be **$0-1/month** on free tier:

```bash
# Check VM type
terraform output postgres_instance_name

gcloud compute instances describe $(terraform output -raw postgres_instance_name) \
  --zone=$(terraform output -raw postgres_zone) \
  --format="value(machineType)"

# Should show: e2-micro (FREE tier eligible)
```

## Common Issues

### Issue: "Connection refused"

**Cause:** VPC connector not ready

**Solution:**
```bash
# Wait 2-3 minutes for VPC connector to be ready
gcloud compute networks vpc-access connectors describe dev-nexus-connector \
  --region=us-central1

# Status should be "READY"
```

### Issue: "pgvector not found"

**Cause:** Startup script didn't complete

**Solution:**
```bash
# SSH into VM and check logs
terraform output -raw postgres_ssh_command | bash
sudo journalctl -u google-startup-scripts -f

# Re-run initialization if needed
sudo bash /var/lib/google/startup-scripts/startup-script.sh
```

### Issue: "Authentication failed"

**Cause:** Wrong password or not set in Secret Manager

**Solution:**
```bash
# Verify password in Secret Manager
gcloud secrets versions access latest --secret=POSTGRES_PASSWORD

# Update if needed
echo -n "NEW-PASSWORD" | gcloud secrets versions add POSTGRES_PASSWORD --data-file=-
```

## Next Steps

1. **✅ Deploy frontend** - Follow `FRONTEND_SETUP.md`
2. **✅ Add more repositories** - Configure monitoring on other repos
3. **✅ Generate embeddings** - Enable semantic pattern search
4. **✅ Set up monitoring** - Configure alerts for disk usage, errors
5. **✅ Backup verification** - Test restore from backup

## Production Checklist

Before going to production:

```hcl
# In terraform.tfvars:
allow_unauthenticated = false  # Require authentication
allow_ssh_from_cidrs = ["YOUR-IP/32"]  # Restrict SSH
min_instances = 1  # No cold starts
enable_postgres_monitoring = true  # Enable monitoring
backup_retention_days = 90  # Longer retention
```

## Useful Commands

```bash
# View outputs
terraform output

# SSH to PostgreSQL
terraform output -raw postgres_ssh_command | bash

# View backups
gsutil ls gs://$(terraform output -raw postgres_backup_bucket)/

# Restart Cloud Run
gcloud run services update pattern-discovery-agent --region=us-central1

# View Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# Check pgvector version
curl $SERVICE_URL/health | jq '.database.pgvector_version'
```

## Resources

- Full setup guide: `POSTGRESQL_SETUP.md`
- Migration script: `scripts/migrate_json_to_postgres.py`
- Database module: `core/database.py`
- Embeddings module: `core/embeddings.py`

---

**Total deployment time:** ~15 minutes
**Monthly cost:** $0-1 (FREE tier)
**Maintenance:** Automated backups, minimal intervention

🎉 **You're done! PostgreSQL with pgvector is running on GCP Free Tier!**
