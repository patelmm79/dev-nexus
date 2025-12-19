# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Pattern Discovery Agent System - an automated architectural consistency and pattern discovery tool that analyzes code commits across GitHub repositories using Claude AI. The system acts as institutional memory, detecting similar patterns, architectural drift, and opportunities for code reuse across multiple projects.

**Key Features**:
1. **Pattern Discovery**: Detects similar patterns across repositories
2. **Knowledge Base Management**: Maintains centralized architectural memory (v2 schema)
3. **Runtime Monitoring**: Tracks production issues and pattern health across deployments
4. **Reusable Workflows**: Monitored projects only need a tiny 15-line workflow file
5. **A2A Protocol Support**: Agent-to-Agent communication for programmatic access
6. **Hybrid Architecture**: GitHub Actions CLI + A2A Server modes
7. **Extensible**: Can notify external orchestration services (e.g., [dependency-orchestrator](https://github.com/patelmm79/dependency-orchestrator))

## Core Architecture

### Hybrid Architecture (GitHub Actions + A2A Server)

The system now operates in two modes:

**1. GitHub Actions Mode (Traditional)**
- Automated pattern analysis on every commit
- Background processing via reusable workflows
- Push-based architecture

**2. A2A Server Mode (NEW)**
- FastAPI server with A2A protocol support
- Query patterns, get deployment info, add lessons learned
- Pull-based architecture for agent-to-agent communication
- Deploy to Cloud Run for 24/7 availability

**Shared Core Logic**:
- `core/pattern_extractor.py` - Claude API pattern extraction
- `core/knowledge_base.py` - GitHub storage with v2 schema
- `core/similarity_finder.py` - Pattern matching algorithms
- Both modes use the same business logic (no duplication)

### System Components

1. **GitHub Actions Workflow** (`.github/workflows/main.yml`)
   - Triggers on push/PR to main/master/develop branches
   - Runs pattern analysis via Python script
   - Uploads analysis artifacts with 90-day retention

2. **Pattern Analyzer** (`scripts/pattern_analyzer.py`)
   - Core analysis engine using Anthropic Claude API
   - Extracts semantic patterns from git diffs using LLM
   - Manages knowledge base stored in separate GitHub repository
   - Compares patterns across repositories
   - Sends notifications via Discord/Slack webhooks
   - Can notify external orchestrator services (optional)

3. **A2A Server** (`a2a/server.py`) **MODULAR v2.0**
   - FastAPI application with A2A protocol endpoints
   - **Modular Architecture**: Skills in separate, self-contained modules
   - **Dynamic AgentCard**: Generated from skill registry (not hardcoded)
   - **Thin Coordinator**: 250 lines (reduced from 445 lines)
   - Publishes AgentCard at `/.well-known/agent.json`
   - 17 skills for comprehensive agent coordination:
     - `query_patterns` (public) - Search for similar patterns
     - `get_deployment_info` (public) - Get deployment/infrastructure info
     - `add_lesson_learned` (authenticated) - Record lessons learned
     - `get_repository_list` (public) - List all tracked repositories
     - `get_cross_repo_patterns` (public) - Find patterns across multiple repos
     - `update_dependency_info` (authenticated) - Update dependency graphs
     - `add_deployment_info` (authenticated) - Add/initialize deployment metadata
     - `health_check_external` (public) - Check external agent health
     - `check_documentation_standards` (public) - Check repository docs for standards conformity
     - `validate_documentation_update` (public) - Validate docs updated after code changes
     - `add_runtime_issue` (authenticated) - Record runtime issues from production monitoring
     - `get_pattern_health` (public) - Analyze runtime health of patterns
     - `query_known_issues` (public) - Search for previously encountered runtime issues
     - `trigger_deep_analysis` (authenticated) - Trigger pattern-miner for deep code analysis
     - `validate_repository_architecture` (public) - **NEW** Full architectural compliance validation
     - `check_specific_standard` (public) - **NEW** Single standard category validation
     - `suggest_improvements` (public) - **NEW** Prioritized improvement recommendations
   - Flexible authentication (Workload Identity + Service Account)
   - Cloud Run deployment ready
   - Coordinates with dependency-orchestrator, pattern-miner, and monitoring systems

4. **Modular Skills** (`a2a/skills/`) **NEW in v2.0**
   - **BaseSkill Interface**: Standard skill contract for consistency
   - **SkillRegistry**: Dynamic skill discovery and routing
   - **Self-contained modules**: Each skill in its own file
   - Skills auto-register on import
   - Independently testable
   - `pattern_query.py` - Pattern search skills
   - `repository_info.py` - Repository information skills
   - `a2a/skills/knowledge_management.py` - KB update skills (authenticated)
   - `integration.py` - External agent coordination and deep analysis triggering
   - `documentation_standards.py` - Documentation standards compliance checking
   - `runtime_monitoring.py` - Runtime issue tracking and pattern health analysis
   - `architectural_compliance.py` - **NEW** Comprehensive architectural standards validation
   - Adding new skill = create one file (not edit multiple files)

4a. **Architectural Compliance Skills** (`a2a/skills/architectural_compliance.py`) **NEW**
   - **Purpose**: Validate repositories against comprehensive architectural standards
   - **Validation Scope**: 10 standard categories covering license, documentation, terraform, deployment, database, CI/CD, and containerization
   - **Pure GitHub API**: Uses GitHub API for repository scanning (no git clone needed)
   - **Three Skills**:
     1. `validate_repository_architecture` - Full validation with compliance score
        - Inputs: repository, optional validation_scope, optional recommendations flag
        - Outputs: compliance score (0-1), grade (A-F), violations by category, recommendations
        - Use case: Comprehensive architectural audit
     2. `check_specific_standard` - Single standard category validation
        - Inputs: repository, standard_category (enum of 10 options)
        - Outputs: pass/fail, violations, compliance score for category
        - Use case: Focused compliance checks on specific domains
     3. `suggest_improvements` - Prioritized improvement recommendations
        - Inputs: repository, optional max_recommendations count
        - Outputs: recommendations organized by priority (CRITICAL > HIGH > MEDIUM > LOW)
        - Use case: Roadmap planning for architectural improvements
   - **Validation Standards**:
     - License: GPL v3.0 compliance (LICENSE file, size >= 30KB, badge in README)
     - Documentation: README.md and CLAUDE.md present with required sections
     - Terraform Init: Unified initialization pattern with terraform-init-unified.sh
     - Multi-Env: Separate tfvars for dev, staging, prod environments
     - Terraform State: Remote GCS backend with backup procedures
     - Disaster Recovery: DR documentation and backup scripts
     - Deployment: Deployment docs and secrets management setup
     - PostgreSQL: PostgreSQL 15 setup docs and terraform configuration
     - CI/CD: Cloud Build multi-stage configuration
     - Containerization: Docker multi-stage build exposing port 8080
   - **Scoring**: Weighted by violation severity (critical -10, high -5, medium -2, low -1)
   - **A2A Protocol Integration**: Bidirectional coordination with external agents:
     * **dependency-orchestrator**: Notified of critical violations; queries dependencies
     * **pattern-miner**: Triggered for deep code analysis on violations
     * **monitoring-system**: Records compliance metrics and trends
     * Graceful fallback if agents not configured
     * Comprehensive error handling and logging
   - **Integration Workflow**:
     1. ValidateRepositoryArchitectureSkill validates repository
     2. If critical violations → records compliance snapshot
     3. Notifies dependency-orchestrator of violations
     4. Triggers pattern-miner for deep analysis
     5. Queries dependency context for impact assessment
     6. Returns integration results in skill output
   - **Integration Service** (`core/compliance_integration.py`):
     * ComplianceIntegrationService manages external agent coordination
     * Methods: notify_compliance_violation(), trigger_deep_analysis(), record_compliance_snapshot(), process_compliance_report(), get_integration_status()
     * Uses ExternalAgentRegistry for agent discovery
     * Enables multi-agent collaboration for architectural improvement

5. **Core Modules** (`core/`)
   - `pattern_extractor.py` - Pattern extraction with Claude
   - `knowledge_base.py` - KB CRUD with v2 schema and auto-migration
   - `core/similarity_finder.py` - Enhanced similarity detection
   - `integration_service.py` - Bidirectional A2A coordination with external agents
   - `core/documentation_standards_checker.py` - Documentation standards compliance checker
   - `core/database.py` - PostgreSQL connection with exponential backoff retry logic
   - `core/standards_loader.py` - Load and parse 10 architectural standards documents
   - `core/architectural_validator.py` - GitHub API-based repository validation engine
   - `core/category_validators.py` - 10 category-specific validators for standards compliance
   - `core/compliance_integration.py` - **NEW** A2A protocol coordination for compliance violations
   - Shared by both GitHub Actions CLI and A2A server

6. **Enhanced Knowledge Base v2** (`schemas/`) **NEW**
   - Pydantic models for data validation
   - New sections: deployment, dependencies, testing, security
   - Automatic migration from v1 to v2
   - `knowledge_base_v2.py` - Complete schema definitions
   - `migration.py` - v1→v2 migration logic

7. **Pre-commit Checker** (`scripts/precommit_checker.py`)
   - Optional local validation before commits
   - Fetches knowledge base from remote URL
   - Warns developers about pattern divergence interactively

### Data Flow

```text
Monitored Project (Push) → Calls Reusable Workflow → Pattern Analyzer → Claude API
                                                            ↓
                                                     Extract Patterns
                                                            ↓
                                                  Knowledge Base Repo (JSON)
                                                            ↓
                                                  Find Similar Patterns
                                                            ↓
                                                  Webhook Notification
                                                            ↓
                                               (Optional) External Orchestrator
```

### Integration Architecture

Dev-Nexus integrates with external AI agents to provide comprehensive project management:

**Integration Partners:**

1. **dependency-orchestrator** ([GitHub](https://github.com/patelmm79/dependency-orchestrator))
   - **Role**: Dependency management and impact analysis
   - **Communication**: Bidirectional A2A protocol
   - **Key Functions**:
     - Receives pattern change notifications from dev-nexus
     - Queries dev-nexus for dependency graphs and patterns
     - Creates automated PRs for dependent repositories
     - Records update outcomes as lessons learned in dev-nexus
   - **Integration Point**: `core/integration_service.py`

2. **pattern-miner** (Active)
   - **Role**: Deep code analysis and pattern comparison
   - **Communication**: Request-response via A2A protocol
   - **Key Functions**:
     - Performs detailed code comparison on demand
     - Provides implementation recommendations based on focus areas
     - Tracks pattern evolution over time
     - Triggered via `trigger_deep_analysis` skill
   - **Integration Point**: `a2a/skills/integration.py` (TriggerDeepAnalysisSkill)

3. **Monitoring Systems** (e.g., agentic-log-attacker)
   - **Role**: Production monitoring and issue detection
   - **Communication**: One-way via A2A (monitoring → dev-nexus)
   - **Key Functions**:
     - Reports runtime issues detected in production
     - Links issues to patterns automatically
     - Provides log snippets and performance metrics
     - Tracks issue resolution
   - **Integration Point**: `a2a/skills/runtime_monitoring.py`

**Integration Data Flow:**

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Pattern Change Event                         │
└─────────────────────────────────────────────────────────────────┘

  Dev-Nexus                    dependency-orchestrator
      │                                  │
      │ 1. Detect pattern change         │
      │    (e.g., API update)            │
      │                                  │
      │ 2. Notify orchestrator           │
      ├─────────────────────────────────>│
      │    POST /a2a/execute             │
      │    skill: notify_pattern_change  │
      │                                  │
      │                                  │ 3. Query dependencies
      │ 4. Request dependency graph      │
      │<─────────────────────────────────┤
      │    POST /a2a/execute             │
      │    skill: query_patterns         │
      │                                  │
      │ 5. Return consumers & patterns   │
      ├─────────────────────────────────>│
      │                                  │
      │                                  │ 6. Analyze impact
      │                                  │    Create PRs
      │                                  │
      │ 7. Record lesson learned         │
      │<─────────────────────────────────┤
      │    POST /a2a/execute             │
      │    skill: add_lesson_learned     │
      │                                  │
      │ 8. Confirm lesson stored         │
      ├─────────────────────────────────>│
      │                                  │
```

**See [INTEGRATION.md](INTEGRATION.md) for complete integration documentation with detailed examples.**

### Reusable Workflow Architecture

The workflow in `.github/workflows/main.yml` is configured with `workflow_call` trigger, allowing other repositories to call it without copying code:

1. **Monitored Project**: Contains only a small workflow file that calls this repository's workflow
2. **This Repository**: Contains all the logic, scripts, and dependencies
3. **Execution**: GitHub Actions checks out both repos and runs the analyzer on the monitored code

### Knowledge Base Structure v2 (Enhanced)

Stored as `knowledge_base.json` in a separate repository with enhanced schema:

**V2 Schema Structure**:
```json
{
  "schema_version": "2.0",
  "repositories": {
    "owner/repo": {
      "latest_patterns": {
        "patterns": [],
        "decisions": [],
        "reusable_components": [],
        "dependencies": [],
        "problem_domain": "...",
        "keywords": []
      },
      "deployment": {
        "scripts": [],
        "lessons_learned": [],
        "reusable_components": [],
        "ci_cd_platform": "...",
        "infrastructure": {}
      },
      "dependencies": {
        "consumers": [],
        "derivatives": [],
        "external_dependencies": []
      },
      "testing": {
        "test_frameworks": [],
        "coverage_percentage": 0.0,
        "test_patterns": []
      },
      "security": {
        "security_patterns": [],
        "authentication_methods": [],
        "compliance_standards": []
      },
      "runtime_issues": [],
      "production_metrics": {},
      "history": []
    }
  }
}
```

**Automatic Migration**: V1 knowledge bases are automatically migrated to v2 on first load

### Runtime Monitoring & Pattern Health (NEW)

The system now includes runtime monitoring capabilities that connect production issues to patterns:

**Runtime Issues Tracking**:
- Record production issues detected by monitoring systems (e.g., agentic-log-attacker)
- Link issues to specific patterns in the knowledge base
- Track issue severity, service type, root cause, and suggested fixes
- Find similar issues across repositories

**Pattern Health Analysis**:
- Calculate health scores for patterns based on production issues
- Analyze pattern reliability across all repositories using it
- Identify problematic patterns that need review
- Track issue trends over time

**Integration with Monitoring Systems**:
- `add_runtime_issue` skill accepts issue reports from monitoring agents
- Issues are automatically linked to patterns
- Pattern health can be queried before adopting patterns
- Supports Cloud Run, Cloud Functions, Cloud Build, GCE, GKE, App Engine

**Schema Fields**:
- `runtime_issues[]` - List of production issues per repository
- `production_metrics{}` - Performance metrics at time of issue
- Pattern objects can include `runtime_issues[]` for pattern-specific tracking

## Development Commands

### Setup for Local Development

```bash
# Install all dependencies (includes A2A server)
pip install -r requirements.txt

# Install dev dependencies (testing, linting)
pip install -r requirements-dev.txt

# Activate virtual environment (if using venv)
venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix
```

### Running A2A Server Locally

**Environment Setup:**

Required environment variables:
- `ANTHROPIC_API_KEY` - From console.anthropic.com (required)
- `GITHUB_TOKEN` - For knowledge base access (required)
- `USE_POSTGRESQL` - Set to "true" to enable PostgreSQL backend (optional, defaults to SQLite)

PostgreSQL-specific variables (when `USE_POSTGRESQL=true`):
- `POSTGRES_HOST` - PostgreSQL server hostname (e.g., "localhost")
- `POSTGRES_PORT` - PostgreSQL port (default: 5432)
- `POSTGRES_DB` - Database name (e.g., "devnexus")
- `POSTGRES_USER` - Database user (e.g., "devnexus")
- `POSTGRES_PASSWORD` - Database password

External agent integration (optional):
- `ORCHESTRATOR_URL` - URL to dependency-orchestrator service (e.g., `https://orchestrator.run.app`)
- `ORCHESTRATOR_TOKEN` - API token for orchestrator authentication
- `PATTERN_MINER_URL` - URL to pattern-miner service
- `PATTERN_MINER_TOKEN` - API token for pattern-miner authentication

```bash
# Set up environment
cp .env.example .env
# Edit .env with your credentials

# Run server
bash scripts/dev-server.sh

# Or directly
python a2a/server.py

# Or with hot reload
uvicorn a2a.server:app --host 0.0.0.0 --port 8080 --reload

# Test endpoints
curl http://localhost:8080/health
curl http://localhost:8080/.well-known/agent.json | jq
```

### Running Pattern Analysis Locally

```bash
# Requires environment variables:
# - ANTHROPIC_API_KEY (required)
# - GITHUB_TOKEN (required)
# - WEBHOOK_URL (optional, for Discord/Slack)
# - KNOWLEDGE_BASE_REPO (optional, format: "username/repo")

python scripts/pattern_analyzer.py
```

### Setting Up Monitoring for Other Projects

See `SETUP_MONITORING.md` for complete instructions. Quick version:

1. Add secrets to the target project (ANTHROPIC_API_KEY, etc.)
2. Create `.github/workflows/pattern-monitoring.yml` in the target project:
```yaml
name: Pattern Monitoring
on:
  push:
    branches: [main, master, develop]
jobs:
  analyze-patterns:
    uses: patelmm79/dev-nexus/.github/workflows/main.yml@main
    secrets:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
      KNOWLEDGE_BASE_REPO: ${{ secrets.KNOWLEDGE_BASE_REPO }}
```
3. Commit and push - monitoring is now active!

### Pre-commit Hook Setup

```bash
# Set environment variables
export ANTHROPIC_API_KEY="your-key"
export KNOWLEDGE_BASE_URL="https://raw.githubusercontent.com/username/dev-nexus/main/knowledge_base.json"

# Install hook (Unix)
chmod +x scripts/precommit_checker.py
cp scripts/precommit_checker.py .git/hooks/pre-commit
```

### Multi-Environment Terraform Setup (dev/staging/prod)

The infrastructure now supports multiple environments with isolated state and secrets:

**Environment-Specific Configuration:**
- **Development (dev)**: Unauthenticated, scale-to-zero, free tier resources, e2-micro database
- **Staging (staging)**: Authenticated, moderate resources, separate service accounts for integration testing
- **Production (prod)**: Authenticated, high availability (always-on), 2vCPU, monitoring enabled

**State Isolation (Important):**
- Each environment has separate Terraform state in GCS
- Backend prefix: `dev-nexus/dev`, `dev-nexus/staging`, `dev-nexus/prod`
- Initialize with: `terraform init -backend-config="prefix=dev-nexus/dev"`
- Prevents accidental destruction of other environments

**Secret Isolation:**
- Dev secrets: `dev-nexus-dev_GITHUB_TOKEN`, `dev-nexus-dev_ANTHROPIC_API_KEY`, etc.
- Staging secrets: `dev-nexus-staging_*`
- Prod secrets: `dev-nexus-prod_*`
- Prevents collisions when using shared GCP project

**Quick Start (Unified Across All Projects):**
```bash
cd terraform

# Initialize development environment
bash scripts/terraform-init-unified.sh dev
terraform plan -var-file="dev.tfvars" -out=tfplan
terraform apply tfplan

# Switch to staging (auto-reconfigures backend)
bash scripts/terraform-init-unified.sh staging
terraform plan -var-file="staging.tfvars" -out=tfplan
terraform apply tfplan

# Switch to production (after review!)
bash scripts/terraform-init-unified.sh prod
terraform plan -var-file="prod.tfvars" -out=tfplan
terraform show tfplan  # Always review prod changes
terraform apply tfplan
```

**Files:**
- `terraform/dev.tfvars` - Development configuration (unauthenticated, scale-to-zero)
- `terraform/staging.tfvars` - Staging configuration (authenticated, moderate resources)
- `terraform/prod.tfvars` - Production configuration (high availability, monitoring)
- `terraform/scripts/terraform-init-unified.sh` - Unified initialization (consistent across all projects)
- [TERRAFORM_UNIFIED_INIT.md](TERRAFORM_UNIFIED_INIT.md) - Unified initialization across projects
- [MULTI_ENV_SETUP.md](MULTI_ENV_SETUP.md) - Complete multi-environment documentation
- [TERRAFORM_STATE_MANAGEMENT.md](TERRAFORM_STATE_MANAGEMENT.md) - State capture, backup, and recovery

**State Management (Critical):**
- Remote state stored in GCS with automatic versioning (prevents data loss)
- Separate state files per environment (dev/staging/prod prefixes)
- Automatic state locking during terraform apply (prevents concurrent modifications)
- Manual backup scripts for disaster recovery
- Setup: `bash scripts/setup-terraform-backend.sh` (one-time)
- Backup: `bash scripts/backup-terraform-state.sh [env]`
- Recover: `bash scripts/recover-terraform-state.sh env`

### Deploying A2A Server to Cloud Run

**Infrastructure Architecture:**

The A2A Server can run in multiple deployment configurations:
1. **Standalone on Cloud Run** - FastAPI service with external PostgreSQL
2. **With PostgreSQL VM** - Dedicated GCE VM with persistent storage for database
3. **Hybrid Mode** - Cloud Run service communicating with separate PostgreSQL infrastructure

**Disaster Recovery (NEW):**

All deployments now include automated disaster recovery:
- **Remote Terraform State**: Stores state in GCS bucket (survives instance destruction)
- **Automated Disk Snapshots**: Daily snapshots of PostgreSQL persistent disk
- **Manual Backup Script**: On-demand database backups to GCS

See [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md) for complete setup and recovery procedures.

**Deployment Steps:**

```bash
# Set up GCP
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
export KNOWLEDGE_BASE_REPO="patelmm79/dev-nexus"

# 1. Initialize Terraform state backend (one-time)
bash scripts/setup-terraform-state.sh

cd terraform

# 2. Initialize Terraform with remote GCS backend
terraform init
# When prompted about existing state, answer: yes (to migrate local → remote)

# 3. Create secrets in Secret Manager
# Note: setup-secrets.sh is idempotent - safe to run multiple times
# If secrets already exist, it will add new versions instead of failing
export GITHUB_TOKEN="ghp_xxxxx"
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
export ORCHESTRATOR_URL="https://orchestrator-url.run.app"  # Optional
export ORCHESTRATOR_TOKEN="token-xxx"  # Optional
export PATTERN_MINER_URL="https://pattern-miner-url.run.app"  # Optional
export PATTERN_MINER_TOKEN="token-xxx"  # Optional

cd ..
bash scripts/setup-secrets.sh

# 4. Deploy to Cloud Run with Terraform
# If secrets are already configured and unchanged, you can skip setup-secrets.sh
cd terraform
terraform apply

# 5. Test deployment
SERVICE_URL=$(gcloud run services describe pattern-discovery-agent \
  --region=us-central1 --format="value(status.url)")
curl ${SERVICE_URL}/health
curl ${SERVICE_URL}/.well-known/agent.json

# 6. Verify disaster recovery
# - Check Terraform state in GCS
gsutil ls gs://terraform-state-${GCP_PROJECT_ID}/dev-nexus/

# - Check disk snapshots policy
gcloud compute resource-policies describe postgres-daily-snapshots

# - Test backup script
bash scripts/backup-postgres.sh
gsutil ls gs://dev-nexus-postgres-backups/
```

**Environment Variables for Cloud Run:**
- `USE_POSTGRESQL` - Set to "true" to use external PostgreSQL (default: SQLite)
- `POSTGRES_HOST` - PostgreSQL server address (required if USE_POSTGRESQL=true)
- `POSTGRES_PORT` - PostgreSQL port (default: 5432)
- `POSTGRES_DB` - Database name
- `POSTGRES_USER` - Database user
- `POSTGRES_PASSWORD` - Database password (from Secret Manager)
- `KNOWLEDGE_BASE_REPO` - GitHub knowledge base repository
- `GITHUB_TOKEN` - GitHub API token (from Secret Manager)
- `ANTHROPIC_API_KEY` - Claude API key (from Secret Manager)
- `ORCHESTRATOR_URL` - External orchestrator service URL
- `ORCHESTRATOR_TOKEN` - Orchestrator authentication token
- `PATTERN_MINER_URL` - Pattern miner service URL
- `PATTERN_MINER_TOKEN` - Pattern miner authentication token

**Secret Management Notes:**
- `setup-secrets.sh` automatically handles existing secrets by adding new versions
- Safe to re-run for secret rotation or updates
- If secrets are already configured and unchanged, skip directly to `deploy.sh`
- To verify existing secrets: `gcloud secrets list --project=$GCP_PROJECT_ID`
- Secrets are automatically injected as environment variables during Cloud Run deployment

**Cloud Build CI Notes:**
- Uses `cloudbuild.yaml` for automated deployment
- Environment variables are written to `env.yaml` file to avoid comma-parsing issues
- `--set-secrets` argument is quoted to ensure proper parsing
- Supports dynamic CORS origins including Vercel preview deployments
- Build substitutions are expanded before creating env file
- Machine type: N1_HIGHCPU_8 for faster builds

**PostgreSQL VM Setup** (optional, for persistent database):
- Terraform configuration creates dedicated GCE VM with persistent disk
- PostgreSQL runs on separate VM for data persistence and scalability
- Startup scripts handle disk formatting, mounting, and PostgreSQL initialization
- Connection resilience: Server handles transient connection failures with exponential backoff
- **Disaster Recovery**:
  - Persistent disk survives VM recreation
  - Automatic daily snapshots (2 AM UTC) with 30-day retention
  - Manual backup script with GCS storage
  - See [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md) for details
- See `terraform/` directory for infrastructure configuration

### Dashboard Usage

Open `pattern_dashboard.html` in a browser and load `knowledge_base.json` to visualize:
- Repository statistics
- Pattern similarity network graph
- Cross-repository relationships
- Redundancy metrics

## Key Implementation Details

### Database Resilience (PostgreSQL Connection)

The `core/database.py` module implements connection resilience with exponential backoff:
- **Retry Strategy**: Up to 6 connection attempts with exponential backoff (1s → 2s → 4s → 8s → 16s → 30s)
- **Purpose**: Tolerates transient network failures and PostgreSQL startup races during Cloud Run deployment
- **Behavior**:
  - Initial delay: 1 second
  - Exponential multiplier: 2x per attempt
  - Maximum delay: 30 seconds (capped)
  - Total retry window: ~60 seconds across all attempts
- **Error Handling**: Returns connection with descriptive error if all retries exhausted
- **Use Cases**: Handles temporary unavailability during infrastructure initialization, network glitches, and service restarts

**Connection pooling** is handled by SQLAlchemy when `USE_POSTGRESQL=true`. For development, SQLite is used by default (no retry logic needed).

### Infrastructure State Management & Disaster Recovery

Terraform state is managed with remote GCS backend to ensure infrastructure survives temporary instance destruction:

**State Persistence**:
- Remote state stored in: `gs://terraform-state-{PROJECT_ID}/dev-nexus/`
- Versioning enabled (keeps 5 versions, deletes non-current after 30 days)
- Survives instance destruction (state lives in GCS, not on ephemeral VM)

**Data Persistence**:
- PostgreSQL persistent disk: `dev-nexus-postgres-data` (survives VM recreation)
- Automatic daily snapshots at 2 AM UTC (30-day retention)
- On-demand backups via `scripts/backup-postgres.sh`

**Why This Matters**:
- Running `terraform apply` on temporary instances is safe (state won't be lost)
- If instance is destroyed, recreate with: `terraform apply` (uses GCS state)
- If PostgreSQL data is corrupted, restore from snapshot or backup
- Multiple temporary instances can share state without conflicts

See [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md) for complete procedures and troubleshooting.

### PostgreSQL Persistent Storage (GCP Infrastructure)

The system uses persistent disks on Google Cloud Platform to ensure data preservation across VM lifecycle events:

**Persistent Disk Configuration** (managed by Terraform):
- **Separate Data Disk**: Dedicated persistent disk (`dev-nexus-postgres-data`) for PostgreSQL data
- **Disk Size**: Configurable (default: 100GB)
- **Auto-Formatting**: Disk is automatically formatted and mounted to `/mnt/postgres-data` on first boot
- **Mount Point**: PostgreSQL data directory configured at `/mnt/postgres-data`
- **Boot Disk**: Separate 20GB boot disk for system files and OS
- **Persistence**: Data survives VM deletion, recreation, and updates

**Data Preservation Guarantees:**
- PostgreSQL data persists across VM restarts
- Data retained during infrastructure scaling operations
- Data preserved during upgrade cycles
- Manual backup: Can create GCP snapshots of persistent disk for recovery

**Terraform Implementation** (`terraform/postgres.tf`):
- Creates persistent disk resource with specified size
- Configures automatic mounting via startup script
- Uses `fstab` entries for persistent mount across reboots
- Provides smart formatting logic (checks if disk already formatted)

**Startup Process**:
1. VM boots with persistent disk attached
2. Startup script checks disk format status
3. If unformatted: Creates filesystem and mounts
4. If formatted: Verifies mount point exists and mounts disk
5. PostgreSQL starts with data directory on persistent disk

### External Agent Registry Logging

The system includes enhanced logging for external agent discovery and health monitoring:

**Registry Initialization** (`a2a/client.py`):
- On startup, ExternalAgentRegistry logs discovered agents
- Output includes: agent name, URL, and authentication status
- Logs all configured external agents (dependency-orchestrator, pattern-miner, monitoring systems)
- Indicates which agents have tokens configured for authentication

**Health Check Logging**:
- Periodically checks health of configured external agents
- Logs success/failure status with timestamps
- Tracks response times and availability status
- Helps diagnose integration issues before they affect operations

**Debug Output**:
- "No agents configured" message if registry is empty
- Detailed error messages if agent URLs are malformed or unreachable
- Useful for troubleshooting external service integration problems

**Integration Monitoring**:
- Log messages appear in Cloud Run logs for deployed instances
- Local development shows logs to console output
- Helps identify when external services become unavailable

### Pattern Extraction Logic

The `extract_patterns_with_llm()` method in `pattern_analyzer.py`:
- Limits to 10 files per analysis to avoid token overflow
- Truncates large diffs to 2000 characters
- Uses Claude Sonnet 4 (`claude-sonnet-4-20250514`)
- Extracts: patterns, technical decisions, reusable components, dependencies, problem domain, keywords
- Returns structured JSON with analyzed_at timestamp and commit SHA

### Similarity Detection

The `find_similar_patterns()` method uses simple set-based scoring:
- Keyword overlap: intersection of keyword sets
- Pattern overlap: intersection of pattern name lists
- Returns top 5 most similar repositories sorted by combined overlap score
- Excludes self-comparison

### File Filtering

Ignores noise files via `_is_meaningful_file()`:
- Lock files (`.lock`, `package-lock.json`, `yarn.lock`)
- Minified/map files (`.min.js`, `.map`)
- Python bytecode (`__pycache__`, `.pyc`)
- VCS/system files (`.git/`, `.DS_Store`)
- `node_modules/`

## Configuration

### GitHub Secrets Required

Each monitored repository needs:
- `ANTHROPIC_API_KEY` - From console.anthropic.com (required)
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions (required)
- `DISCORD_WEBHOOK_URL` - For notifications (optional)
- `KNOWLEDGE_BASE_REPO` - Format: "username/dev-nexus" (optional)

For Cloud Run deployment, also configure in GCP Secret Manager:
- `ANTHROPIC_API_KEY` - Claude API key
- `GITHUB_TOKEN` - GitHub personal access token
- `ORCHESTRATOR_URL` - URL to dependency-orchestrator service (if using integration)
- `ORCHESTRATOR_TOKEN` - Authentication token for orchestrator
- `PATTERN_MINER_URL` - URL to pattern-miner service (if using deep analysis)
- `PATTERN_MINER_TOKEN` - Authentication token for pattern-miner

### Adjusting Sensitivity

In `pattern_analyzer.py:228`, modify `find_similar_patterns()`:
```python
# Current: Alert on any overlap
if keyword_overlap > 0 or pattern_overlap > 0:

# More selective: Require 2+ overlaps
if keyword_overlap > 1 or pattern_overlap > 1:
```

### Adding File Filters

Edit `pattern_analyzer.py:72` in `_is_meaningful_file()`:
```python
ignore_patterns = [
    r'\.lock$',
    r'test_.*\.py$',  # Ignore test files
    r'.*_generated\..*',  # Ignore generated code
]
```

## Important Patterns

### Knowledge Base Updates

The analyzer always tries to update the knowledge base after extracting patterns. It:
1. Loads existing KB from GitHub repo
2. Appends new entry to repository history
3. Updates latest patterns for the repository
4. Commits changes back to KB repo using PyGithub
5. Handles both file creation (first run) and updates (subsequent runs)

### Error Handling Philosophy

The system is designed to be non-blocking:
- Pattern extraction errors return empty/default structures with error field
- Missing knowledge base returns empty repositories dict
- Failed notifications print to console instead of raising
- Pre-commit hook exits with code 0 if API key missing (doesn't block commit)

### Notification Format

Discord/Slack notifications use embeds structure:
- Main message with repository name and pattern count
- Embed per similar repository (top 3 shown)
- Fields showing matching patterns (max 5 displayed)
- Includes overlap counts for quick assessment

## Python Environment

- Developed for Python 3.11+
- Uses PyCharm project structure (venv in project directory)
- Windows-compatible path handling
- Virtual environment in `venv/` directory (excluded from git)

## Notes

- The workflow file location differs slightly: actual path is `.github/workflows/main.yml` but pattern_analyzer.py is in `scripts/` not `.github/scripts/`
- Dashboard is client-side only (pure HTML/JavaScript, no backend)
- Knowledge base JSON can grow large over time - consider pruning old history entries
- LLM responses are parsed with markdown code block removal before JSON parsing
