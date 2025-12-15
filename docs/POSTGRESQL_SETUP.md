# PostgreSQL Setup Guide with pgvector

Complete guide for deploying PostgreSQL with vector embeddings support to GCP.

## Overview

This setup deploys a self-hosted PostgreSQL database on GCP Compute Engine with:

- ✅ **PostgreSQL 15** with **pgvector extension** for vector embeddings
- ✅ **e2-micro VM** (FREE tier eligible - $0/month!)
- ✅ **Automated backups** to Cloud Storage
- ✅ **VPC connector** for secure Cloud Run → PostgreSQL communication
- ✅ **Monitoring and alerting** with Cloud Monitoring
- ✅ **Full-text search** capabilities
- ✅ **Optimized schema** for pattern discovery

## Why PostgreSQL + pgvector?

### pgvector Extension
- **Store embeddings** alongside patterns for semantic similarity
- **Vector similarity search** using cosine distance, L2 distance, inner product
- **HNSW and IVFFlat indices** for fast similarity queries
- **Native PostgreSQL** - no external vector database needed

### Use Cases
- Find similar patterns across repositories using embeddings
- Semantic search: "find authentication patterns"
- Pattern recommendations based on existing code
- Detect architectural drift through embedding comparison

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Frontend (Vercel/Netlify)                      │
│  - React dashboard                              │
└─────────────────┬───────────────────────────────┘
                  │ HTTPS
                  │
┌─────────────────▼───────────────────────────────┐
│  Cloud Run (Serverless)                         │
│  - FastAPI A2A Server                           │
│  - Auto-scaling                                 │
└─────────────────┬───────────────────────────────┘
                  │
                  │ VPC Connector (Private Network)
                  │
┌─────────────────▼───────────────────────────────┐
│  PostgreSQL VM (e2-micro - FREE!)               │
│  - PostgreSQL 15 + pgvector                     │
│  - 30 GB storage                                │
│  - Automated backups                            │
│  - Internal IP only (secure)                    │
└─────────────────┬───────────────────────────────┘
                  │ Daily Backup
                  │
┌─────────────────▼───────────────────────────────┐
│  Cloud Storage                                  │
│  - Compressed SQL backups                       │
│  - 30-day retention                             │
│  - Audit trail and disaster recovery            │
└─────────────────────────────────────────────────┘
```

**Note:** As of v2.0.0, GitHub JSON storage has been removed. PostgreSQL is the single source of truth.

## Current Integration Status (v2.0.0)

**✅ Fully Integrated** - All components use PostgreSQL:

### Core Services
- **PostgresRepository** (`core/postgres_repository.py`) - Data access layer for all database operations
- **DatabaseManager** (`core/database.py`) - Connection pool management with asyncpg
- **No KnowledgeBaseManager** - JSON-based manager completely removed

### A2A Skills Using PostgreSQL
All 13 skills read/write directly to PostgreSQL:

**Pattern Query Skills:**
- `query_patterns` - Search patterns using PostgreSQL queries
- `get_cross_repo_patterns` - Aggregate patterns across repositories

**Repository Info Skills:**
- `get_repository_list` - Query repositories table
- `get_deployment_info` - Load repository metadata from PostgreSQL

**Knowledge Management Skills (Write Operations):**
- `add_lesson_learned` - Insert into lessons_learned table
- `update_dependency_info` - Update repository_relationships
- `add_deployment_info` - Insert deployment metadata

**Runtime Monitoring Skills:**
- `add_runtime_issue` - Track runtime issues
- `get_pattern_health` - Query issue counts
- `query_known_issues` - Search runtime_issues table

**Integration Skills:**
- `health_check_external` - Check external agents

**Documentation Skills:**
- `check_documentation_standards` - Validate docs
- `validate_documentation_update` - Check doc updates

### Environment Configuration

**Required Environment Variables:**
```bash
# PostgreSQL Connection (REQUIRED)
USE_POSTGRESQL=true
POSTGRES_HOST=10.8.0.2  # Internal VM IP
POSTGRES_PORT=5432
POSTGRES_DB=devnexus
POSTGRES_USER=devnexus
POSTGRES_PASSWORD=<from-secret-manager>

# Optional Connection Pool Settings
POSTGRES_MIN_CONNECTIONS=5
POSTGRES_MAX_CONNECTIONS=20
```

**Application Behavior:**
- If `USE_POSTGRESQL=false` or not set, application **refuses to start**
- Connection pool initialized at startup
- Health check verifies PostgreSQL connectivity
- All skills fail gracefully if database unavailable

## Database Schema

The schema includes vector support for embeddings:

### Core Tables

**repositories** - Repository metadata
```sql
id, name, problem_domain, last_analyzed, created_at, updated_at
```

**patterns** - Patterns with vector embeddings
```sql
id, repo_id, name, description, context,
embedding vector(1536),  -- OpenAI embedding dimension
created_at
```

**technical_decisions** - Architectural decisions
```sql
id, repo_id, what, why, alternatives, created_at
```

**reusable_components** - Shareable code components
```sql
id, repo_id, name, purpose, location, created_at
```

**keywords** - Pattern keywords (many-to-many)
```sql
id, keyword
pattern_keywords(pattern_id, keyword_id)
```

### Advanced Tables

- `dependencies` - External dependencies
- `repository_relationships` - Consumer/derivative relationships
- `deployment_scripts` - Deployment automation
- `lessons_learned` - Historical insights
- `analysis_history` - Change tracking over time
- `test_frameworks` - Testing metadata
- `security_patterns` - Security practices

### Vector Indices

```sql
-- IVFFlat index for fast cosine similarity search
CREATE INDEX idx_patterns_embedding
ON patterns USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Full-text search indices
CREATE INDEX idx_patterns_description_fts
ON patterns USING gin(to_tsvector('english', description));
```

### Similarity View

```sql
CREATE VIEW pattern_similarity_view AS
SELECT
    p1.id as pattern1_id,
    p1.name as pattern1_name,
    p2.id as pattern2_id,
    p2.name as pattern2_name,
    1 - (p1.embedding <=> p2.embedding) as similarity_score
FROM patterns p1
CROSS JOIN patterns p2
WHERE p1.id < p2.id
  AND p1.embedding IS NOT NULL
  AND p2.embedding IS NOT NULL
  AND 1 - (p1.embedding <=> p2.embedding) > 0.8;  -- >80% similarity
```

## Prerequisites

1. **GCP Project** with billing enabled
2. **Terraform 1.0+** installed
3. **gcloud CLI** authenticated
4. **GitHub token** with repo access
5. **Anthropic API key**
6. **Strong PostgreSQL password**

## Step-by-Step Deployment

### Step 1: Configure Variables

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars
```

**Minimum required variables:**

```hcl
# Required
project_id            = "your-gcp-project"
region                = "us-central1"  # Free tier eligible
github_token          = "ghp_xxxxx"
anthropic_api_key     = "sk-ant-xxxxx"
knowledge_base_repo   = "username/repo"
postgres_db_password  = "STRONG-PASSWORD-HERE"

# Recommended FREE tier settings
postgres_machine_type = "e2-micro"
postgres_disk_size_gb = 30
postgres_version      = "15"
min_instances         = 0
cpu                   = "1"
memory                = "1Gi"
```

### Step 2: Initialize Terraform

```bash
terraform init
```

Expected output:
```
Initializing the backend...
Initializing provider plugins...
- Finding hashicorp/google versions matching "~> 5.0"...
✓ Terraform has been successfully initialized!
```

### Step 3: Plan Deployment

```bash
terraform plan
```

Review the resources to be created:
- ✅ VPC network and subnet
- ✅ Firewall rules (PostgreSQL, SSH)
- ✅ VPC connector for Cloud Run
- ✅ PostgreSQL VM (e2-micro)
- ✅ Cloud Storage backup bucket
- ✅ Secret Manager secrets
- ✅ IAM roles and permissions
- ✅ Cloud Run service with DB connection

### Step 4: Deploy Infrastructure

```bash
terraform apply
```

Type `yes` when prompted.

**Deployment time:** 10-15 minutes

**What happens:**
1. Creates VPC network and security rules
2. Provisions e2-micro VM
3. Installs PostgreSQL 15
4. Builds and installs pgvector from source
5. Configures PostgreSQL for remote connections
6. Creates database and user
7. Enables pgvector extension
8. Initializes schema with tables and indices
9. Sets up automated backup cron job
10. Creates VPC connector for Cloud Run
11. Deploys Cloud Run with PostgreSQL connection

### Step 5: Verify Deployment

```bash
# Get outputs
terraform output

# Test Cloud Run health
SERVICE_URL=$(terraform output -raw service_url)
curl $SERVICE_URL/health

# Expected response:
{
  "status": "healthy",
  "database": "postgresql",
  "database_connected": true,
  "pgvector_enabled": true,
  ...
}

# SSH into PostgreSQL VM (optional)
terraform output -raw postgres_ssh_command | bash

# Once inside VM, test database:
sudo -u postgres psql -d devnexus -c "\dx"
# Should show: vector | 0.6.0 | public | vector data type and ivfflat access method
```

## Cost Analysis

### FREE Tier Configuration ($0/month)

Using GCP Always Free tier:

| Resource | Spec | Cost |
|----------|------|------|
| **e2-micro VM** | 1 vCPU, 1GB RAM | $0 (free tier) |
| **Persistent Disk** | 30 GB standard | $0 (free tier) |
| **Cloud Run** | Scale to zero | $0 (2M requests free) |
| **VPC Connector** | 2-3 instances | ~$0.10-0.30/month |
| **Cloud Storage** | Backups | ~$0.60/month |
| **Network Egress** | Internal only | $0 |

**Total: $0-1/month** 🎉

### Production Configuration ($15-30/month)

| Resource | Spec | Cost |
|----------|------|------|
| **e2-small VM** | 2 vCPU, 2GB RAM | ~$13/month |
| **Persistent Disk** | 50 GB | ~$2/month |
| **Cloud Run** | Min 1 instance | ~$15/month |
| **VPC Connector** | 2-3 instances | ~$0.30/month |
| **Cloud Storage** | Backups | ~$1.20/month |

**Total: $30-35/month**

## Using pgvector for Pattern Similarity

### Generating Embeddings

Use OpenAI, Anthropic, or other embedding models:

```python
import openai
from anthropic import Anthropic

# Option 1: OpenAI embeddings (1536 dimensions)
response = openai.embeddings.create(
    model="text-embedding-3-small",
    input="API endpoint pattern with authentication"
)
embedding = response.data[0].embedding

# Option 2: Anthropic embeddings (via Claude)
# (Anthropic doesn't have dedicated embedding models yet,
#  but you can use Claude to generate semantic descriptions
#  and then use OpenAI/others for embeddings)
```

### Storing Embeddings

```python
import asyncpg

conn = await asyncpg.connect(
    host="10.8.0.2",  # Internal IP
    database="devnexus",
    user="devnexus",
    password="your-password"
)

# Insert pattern with embedding
await conn.execute("""
    INSERT INTO patterns (repo_id, name, description, context, embedding)
    VALUES ($1, $2, $3, $4, $5::vector)
""", repo_id, name, description, context, embedding)
```

### Finding Similar Patterns

```sql
-- Find patterns similar to a given embedding using cosine similarity
SELECT
    name,
    description,
    1 - (embedding <=> $1::vector) as similarity
FROM patterns
WHERE embedding IS NOT NULL
ORDER BY embedding <=> $1::vector  -- Cosine distance
LIMIT 10;

-- Find patterns similar to a specific pattern
SELECT
    p2.name,
    p2.description,
    1 - (p1.embedding <=> p2.embedding) as similarity
FROM patterns p1, patterns p2
WHERE p1.id = 123
  AND p2.id != 123
  AND p2.embedding IS NOT NULL
ORDER BY p1.embedding <=> p2.embedding
LIMIT 10;
```

### Vector Operations

```sql
-- L2 distance (Euclidean)
embedding <-> other_embedding

-- Cosine distance (most common for text embeddings)
embedding <=> other_embedding

-- Inner product
embedding <#> other_embedding

-- Cosine similarity (0 to 1, higher is more similar)
1 - (embedding <=> other_embedding)
```

## Backup and Restore

### Automated Backups

Backups run daily at 2 AM UTC via cron:

```bash
# View backup logs
gcloud compute ssh dev-nexus-postgres --zone=us-central1-a
sudo tail -f /var/log/postgres-backup.log

# List backups
gsutil ls gs://YOUR-PROJECT-postgres-backups/
```

### Manual Backup

```bash
# SSH into VM
terraform output -raw postgres_ssh_command | bash

# Run backup manually
sudo /usr/local/bin/backup-postgres.sh
```

### Restore from Backup

```bash
# Download backup from Cloud Storage
gsutil cp gs://YOUR-PROJECT-postgres-backups/dev-nexus-TIMESTAMP.sql.gz /tmp/

# Restore
gunzip < /tmp/dev-nexus-TIMESTAMP.sql.gz | sudo -u postgres psql devnexus
```

## Monitoring

### Cloud Monitoring Dashboard

Access at: https://console.cloud.google.com/monitoring

Metrics tracked:
- CPU utilization
- Memory usage
- Disk I/O
- Network traffic
- Query performance (via pg_stat_statements)

### Query Performance

```sql
-- Top 10 slowest queries
SELECT
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    max_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Vector query performance
EXPLAIN ANALYZE
SELECT name FROM patterns
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

## Scaling

### Vertical Scaling (More Power)

```hcl
# Edit terraform.tfvars
postgres_machine_type = "e2-small"  # 2 vCPU, 2GB RAM
postgres_disk_size_gb = 50

# Apply changes
terraform apply
```

**Downtime:** ~2-5 minutes for VM resize

### Horizontal Scaling (Read Replicas)

For future expansion, consider:
- Cloud SQL PostgreSQL with read replicas
- PgBouncer connection pooling
- Citus extension for sharding

## Security Best Practices

1. **Restrict SSH Access**
   ```hcl
   allow_ssh_from_cidrs = ["YOUR_IP/32"]
   ```

2. **Rotate Passwords Regularly**
   ```bash
   # Update password in Secret Manager
   echo -n "NEW_PASSWORD" | gcloud secrets versions add POSTGRES_PASSWORD --data-file=-

   # Update in PostgreSQL
   sudo -u postgres psql -c "ALTER USER devnexus PASSWORD 'NEW_PASSWORD';"
   ```

3. **Enable Audit Logging**
   ```sql
   ALTER SYSTEM SET log_statement = 'all';
   SELECT pg_reload_conf();
   ```

4. **Use SSL/TLS** (Optional)
   Generate certificates and configure `postgresql.conf` for SSL

## Troubleshooting

### Connection Issues

```bash
# Check if VM is running
gcloud compute instances list --filter="name=dev-nexus-postgres"

# Check if PostgreSQL is running
gcloud compute ssh dev-nexus-postgres --zone=us-central1-a
sudo systemctl status postgresql

# Test connection from VM
sudo -u postgres psql -d devnexus -c "SELECT version();"
```

### VPC Connector Issues

```bash
# Check connector status
gcloud compute networks vpc-access connectors describe dev-nexus-connector \
  --region=us-central1

# Cloud Run logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

### pgvector Not Working

```bash
# SSH into VM
terraform output -raw postgres_ssh_command | bash

# Check if pgvector is installed
sudo -u postgres psql -d devnexus -c "SELECT * FROM pg_extension WHERE extname='vector';"

# Reinstall if needed
cd /tmp
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make && sudo make install
sudo systemctl restart postgresql
```

## Migration Path

### From GitHub JSON to PostgreSQL

See `scripts/migrate_json_to_postgres.py` for automated migration.

```bash
# Run migration
python scripts/migrate_json_to_postgres.py \
  --json-url https://raw.githubusercontent.com/user/repo/main/knowledge_base.json \
  --db-host 10.8.0.2 \
  --db-name devnexus

# Verify migration
psql -h 10.8.0.2 -U devnexus -d devnexus -c "SELECT COUNT(*) FROM repositories;"
```

### ⚠️ PostgreSQL is REQUIRED

**As of v2.0.0, JSON storage has been completely removed.**

The application will refuse to start without PostgreSQL:
```python
# In server.py startup event
if not db_manager.enabled:
    raise RuntimeError("PostgreSQL must be enabled. Set USE_POSTGRESQL=true")
```

**All data is stored in PostgreSQL:**
- ✅ Patterns and decisions
- ✅ Repository metadata
- ✅ Lessons learned
- ✅ Deployment info
- ✅ Dependency relationships
- ✅ Runtime issues

**No fallback to JSON** - PostgreSQL is the single source of truth.

## Next Steps

1. ✅ **Deploy infrastructure** (this guide)
2. ✅ **Application already uses PostgreSQL** (v2.0.0+)
3. 🔄 **Migrate existing JSON data** (if upgrading from v1.x)
4. ✅ **Generate embeddings** for existing patterns
5. ✅ **Build frontend** with vector similarity features
6. ✅ **Set up monitoring** alerts

## Resources

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/15/)
- [GCP Free Tier](https://cloud.google.com/free)
- [Vector Similarity Search Guide](https://github.com/pgvector/pgvector#querying)

---

**Deployment Status:** Ready to deploy!
**Estimated Cost:** $0-1/month (FREE tier)
**Deployment Time:** 15 minutes
**Maintenance:** Automated backups, minimal manual intervention
