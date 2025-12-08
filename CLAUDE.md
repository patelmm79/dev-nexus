# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Pattern Discovery Agent System - an automated architectural consistency and pattern discovery tool that analyzes code commits across GitHub repositories using Claude AI. The system acts as institutional memory, detecting similar patterns, architectural drift, and opportunities for code reuse across multiple projects.

**Key Features**:
1. **Pattern Discovery**: Detects similar patterns across repositories
2. **Knowledge Base Management**: Maintains centralized architectural memory (v2 schema)
3. **Reusable Workflows**: Monitored projects only need a tiny 15-line workflow file
4. **A2A Protocol Support**: Agent-to-Agent communication for programmatic access
5. **Hybrid Architecture**: GitHub Actions CLI + A2A Server modes
6. **Extensible**: Can notify external orchestration services (e.g., [dependency-orchestrator](https://github.com/patelmm79/dependency-orchestrator))

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
   - Nine skills for comprehensive agent coordination:
     - `query_patterns` (public) - Search for similar patterns
     - `get_deployment_info` (public) - Get deployment/infrastructure info
     - `add_lesson_learned` (authenticated) - Record lessons learned
     - `get_repository_list` (public) - List all tracked repositories
     - `get_cross_repo_patterns` (public) - Find patterns across multiple repos
     - `update_dependency_info` (authenticated) - Update dependency graphs
     - `health_check_external` (public) - Check external agent health
     - `check_documentation_standards` (public) - **NEW** Check repository docs for standards conformity
     - `validate_documentation_update` (public) - **NEW** Validate docs updated after code changes
   - Flexible authentication (Workload Identity + Service Account)
   - Cloud Run deployment ready
   - Coordinates with dependency-orchestrator and pattern-miner

4. **Modular Skills** (`a2a/skills/`) **NEW in v2.0**
   - **BaseSkill Interface**: Standard skill contract for consistency
   - **SkillRegistry**: Dynamic skill discovery and routing
   - **Self-contained modules**: Each skill in its own file
   - Skills auto-register on import
   - Independently testable
   - `pattern_query.py` - Pattern search skills
   - `repository_info.py` - Repository information skills
   - `a2a/skills/knowledge_management.py` - KB update skills (authenticated)
   - `integration.py` - External agent coordination
   - `documentation_standards.py` - **NEW** Documentation standards compliance checking
   - Adding new skill = create one file (not edit multiple files)

5. **Core Modules** (`core/`)
   - `pattern_extractor.py` - Pattern extraction with Claude
   - `knowledge_base.py` - KB CRUD with v2 schema and auto-migration
   - `core/similarity_finder.py` - Enhanced similarity detection
   - `integration_service.py` - Bidirectional A2A coordination with external agents
   - `core/documentation_standards_checker.py` - **NEW** Documentation standards compliance checker
   - Shared by both GitHub Actions CLI and A2A server

5. **Enhanced Knowledge Base v2** (`schemas/`) **NEW**
   - Pydantic models for data validation
   - New sections: deployment, dependencies, testing, security
   - Automatic migration from v1 to v2
   - `knowledge_base_v2.py` - Complete schema definitions
   - `migration.py` - v1→v2 migration logic

6. **Pre-commit Checker** (`scripts/precommit_checker.py`)
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

2. **pattern-miner** (Future)
   - **Role**: Deep code analysis and pattern comparison
   - **Communication**: Request-response via A2A
   - **Key Functions**:
     - Performs detailed code comparison
     - Provides implementation recommendations
     - Tracks pattern evolution over time

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
      "history": []
    }
  }
}
```

**Automatic Migration**: V1 knowledge bases are automatically migrated to v2 on first load

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

### Deploying A2A Server to Cloud Run

```bash
# Set up GCP
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
export KNOWLEDGE_BASE_REPO="patelmm79/dev-nexus"

# Create secrets in Secret Manager
export GITHUB_TOKEN="ghp_xxxxx"
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
bash scripts/setup-secrets.sh

# Deploy to Cloud Run
bash scripts/deploy.sh

# Test deployment
SERVICE_URL=$(gcloud run services describe pattern-discovery-agent \
  --region=us-central1 --format="value(status.url)")
curl ${SERVICE_URL}/health
curl ${SERVICE_URL}/.well-known/agent.json
```

### Dashboard Usage

Open `pattern_dashboard.html` in a browser and load `knowledge_base.json` to visualize:
- Repository statistics
- Pattern similarity network graph
- Cross-repository relationships
- Redundancy metrics

## Key Implementation Details

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
- `DISCORD_WEBHOOK_URL` - For notifications (optional)
- `KNOWLEDGE_BASE_REPO` - Format: "username/dev-nexus" (optional)
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions

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
