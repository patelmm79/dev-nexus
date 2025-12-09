# Dev-Nexus: Pattern Discovery Agent

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

> Automated architectural consistency and pattern discovery across your GitHub repositories

---

## 📚 Table of Contents

### Quick Links
- **[🚀 Quick Start](#-quick-start)** - Get started in 5 minutes
- **[☁️ Cloud Deployment](#️-deployment-to-cloud-run)** - Deploy to Google Cloud Run
- **[📖 Documentation Index](#-documentation-index)** - Complete documentation guide

### Main Sections
1. [Overview](#overview)
2. [What This Solves](#-what-this-solves)
3. [Installation](#installation)
4. [Usage](#usage)
5. [What's Included](#-whats-included)
6. [Quick Start](#-quick-start)
7. [Deployment to Cloud Run](#️-deployment-to-cloud-run)
8. [Dashboard Usage](#-dashboard-usage)
9. [Configuration](#-configuration)
10. [A2A Integration](#-a2a-integration)
11. [Cost Estimation](#-cost-estimation)
12. [Troubleshooting](#-troubleshooting)
13. [Documentation Index](#-documentation-index)
14. [License](#-license)

---

## Overview

Dev-Nexus is an automated pattern discovery agent that acts as your institutional memory across GitHub repositories. It uses Claude AI to detect architectural patterns, find code similarities, and maintain consistency as your projects scale.

**Key capabilities:**
- Automatic pattern extraction from every commit
- Cross-repository similarity detection
- Centralized knowledge base management
- Agent-to-Agent (A2A) protocol support
- Real-time notifications for pattern matches

## Installation

### Prerequisites

- Python 3.11 or higher
- GitHub account with repository access
- Anthropic API key ([get one here](https://console.anthropic.com))
- (Optional) Discord/Slack webhook for notifications

### Quick Install

```bash
# Clone the repository
git clone https://github.com/patelmm79/dev-nexus.git
cd dev-nexus

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials

# Test the installation
python scripts/pattern_analyzer.py --help
```

### For Monitoring Other Repositories

No installation required in monitored repos! Just add a small workflow file:

```bash
mkdir -p .github/workflows
# See Quick Start section below for workflow configuration
```

## Usage

### Basic Usage - GitHub Actions (Recommended)

Add pattern monitoring to any repository with a single workflow file:

```yaml
name: Pattern Monitoring
on:
  push:
    branches: [main, master, develop]
jobs:
  analyze-patterns:
    uses: patelmm79/dev-nexus/.github/workflows/analyze-reusable.yml@main
    secrets:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      KNOWLEDGE_BASE_REPO: ${{ secrets.KNOWLEDGE_BASE_REPO }}
```

### Usage - A2A Server

Deploy as a 24/7 service for agent-to-agent communication:

```bash
# Run locally
bash scripts/dev-server.sh

# Deploy to Cloud Run
export GCP_PROJECT_ID="your-project-id"
bash scripts/deploy.sh
```

### Usage - Manual Analysis

Run pattern analysis locally:

```bash
export ANTHROPIC_API_KEY="your-key"
export GITHUB_TOKEN="your-token"
export KNOWLEDGE_BASE_REPO="username/dev-nexus"

python scripts/pattern_analyzer.py
```

See [QUICK_START.md](QUICK_START.md) for detailed setup instructions.

## 🎯 What This Solves

When building multiple projects with AI assistance, you face:
- **Pattern drift**: Similar problems solved differently across repos
- **Code duplication**: Reimplementing the same logic multiple times
- **Lost context**: Forgetting how you solved something last month
- **Technical debt**: Inconsistency compounds over time

This system acts as your **automated institutional memory**, watching your commits and:
- ✅ Detecting similar patterns in other repos you can reuse
- ✅ Finding opportunities to extract shared libraries
- ✅ Catching architectural inconsistencies before they spread
- ✅ Identifying potential redundancy in real-time

**Need dependency coordination?** Check out the companion project: [dependency-orchestrator](https://github.com/patelmm79/dependency-orchestrator) - AI-powered triage agents that notify dependent repos when changes require action.

## 📦 What's Included

### Hybrid Architecture

**GitHub Actions Mode** (Traditional)
- Automated pattern analysis on every commit
- Background processing via workflows

**A2A Protocol Server** (NEW)
- Agent-to-Agent protocol for programmatic access
- Query patterns, get deployment info, add lessons learned
- Deploy to Cloud Run for 24/7 availability
- Enables integration with other AI agents

### Core Components

1. **Reusable GitHub Workflow** (`.github/workflows/analyze-reusable.yml`)
   - Called from monitored repositories
   - No file copying required - automatically pulls latest code
   - Triggers on push/PR events
   - Uses Claude API for semantic analysis

2. **Pattern Analyzer** (`scripts/pattern_analyzer.py`)
   - Extracts semantic patterns from code changes
   - Compares patterns across repositories
   - Updates central knowledge base automatically
   - Sends smart notifications via Discord/Slack webhooks
   - Can notify external orchestrator services (like [dependency-orchestrator](https://github.com/patelmm79/dependency-orchestrator))

3. **A2A Server** (`a2a/server.py`) **NEW**
   - FastAPI server with A2A protocol support
   - Three skills:
     - `query_patterns` (public) - Search for similar patterns
     - `get_deployment_info` (public) - Get deployment metadata
     - `add_lesson_learned` (authenticated) - Record lessons
   - Publishes AgentCard at `/.well-known/agent.json`
   - Deploy to Cloud Run for agent-to-agent communication
   - See [A2A_QUICKSTART.md](A2A_QUICKSTART.md) for details

4. **Enhanced Knowledge Base v2** **NEW**
   - Patterns (existing)
   - Deployment info: scripts, lessons learned, reusable components
   - Dependency graph: consumers, derivatives, external deps
   - Testing metadata and security posture
   - Automatic migration from v1 to v2

5. **Dashboard** (`pattern_dashboard.html`)
   - Visualize your architectural landscape
   - Interactive pattern similarity network graph
   - Track redundancy metrics across repos
   - Browse repository details and history

6. **Pre-commit Hook** (`scripts/precommit_checker.py`) [Optional]
   - Check patterns before commit locally
   - Warn about divergence from other repos
   - Interactive approval workflow

## 🚀 Quick Start

### 1. Create Knowledge Base Repository

```bash
gh repo create dev-nexus --private
cd dev-nexus
echo "# Architecture Knowledge Base" > README.md
git add . && git commit -m "init" && git push
```

### 2. Set Up Secrets

In **each repository** you want to monitor, add these GitHub secrets:

**Required:**
- `ANTHROPIC_API_KEY` - Get from console.anthropic.com

**Optional:**
- `DISCORD_WEBHOOK_URL` - For notifications
- `KNOWLEDGE_BASE_REPO` - Format: `username/dev-nexus`

### 3. Add to Repository

**No files to copy!** Just create one small workflow file:

```bash
# In your project repo
cd my-project

# Create workflow directory
mkdir -p .github/workflows

# Create the workflow file
cat > .github/workflows/pattern-monitoring.yml << 'EOF'
name: Pattern Monitoring

on:
  push:
    branches: [main, master, develop]
  pull_request:
    types: [opened, synchronize]

jobs:
  analyze-patterns:
    uses: patelmm79/dev-nexus/.github/workflows/analyze-reusable.yml@main
    secrets:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
      KNOWLEDGE_BASE_REPO: ${{ secrets.KNOWLEDGE_BASE_REPO }}
      ORCHESTRATOR_URL: ${{ secrets.ORCHESTRATOR_URL }}  # Optional: for dependency triage
EOF

# Commit
git add .github/workflows/pattern-monitoring.yml
git commit -m "Enable pattern monitoring"
git push
```

**That's it!** The workflow automatically pulls the latest analyzer from this repo.

### 4. (Optional) Deploy A2A Server to Cloud Run

Enable 24/7 agent-to-agent communication by deploying to Google Cloud Run:

```bash
# Quick deployment (3 commands)
export GCP_PROJECT_ID="your-project-id"
bash scripts/setup-secrets.sh
bash scripts/deploy.sh
```

**📖 Complete Deployment Guide:** See **[DEPLOYMENT.md](DEPLOYMENT.md)** for:
- Detailed step-by-step instructions
- Prerequisites and setup
- Configuration options
- Monitoring and troubleshooting
- Production checklist
- Cost optimization

**🔧 Local Development:** See [A2A_QUICKSTART.md](A2A_QUICKSTART.md) for local testing and A2A protocol usage.

### 5. Watch It Work

On your next commit, the action will:
1. Call the reusable workflow from dev-nexus
2. Analyze your changes using Claude
3. Extract patterns and update knowledge base
4. Check for similarities across other repos
5. Notify you via Discord/Slack if patterns match

**See [SETUP_MONITORING.md](SETUP_MONITORING.md) for detailed instructions and troubleshooting.**

## 📊 Example Workflow

### Day 1: First Repository
```bash
# You build a web scraper with retry logic
git commit -m "Add scraper with exponential backoff"
git push
```
**System:** ✅ Patterns recorded: "Retry logic with exponential backoff", "Rate limiting"

### Day 7: Second Repository
```bash
# You build an API client
git commit -m "Add API client"
git push
```
**System:** 🔔 "Found similar pattern in **web-scraper**: 'Retry logic with exponential backoff'. Consider extracting to shared library?"

### Day 14: Review Patterns
Open your knowledge base dashboard to see patterns across all repos:
1. Download `knowledge_base.json` from your dev-nexus repo
2. Open `pattern_dashboard.html` in your browser
3. Load the knowledge base file
4. Explore:
   - Retry logic used in 2 repos: web-scraper, api-client
   - Environment-based configuration in 3 repos
   - Visual similarity network showing connections

## 🎨 Dashboard Usage

1. Open `pattern_dashboard.html` in your browser
2. Load your `knowledge_base.json` (from your KB repo)
3. Explore:
   - Repository statistics
   - Pattern similarity network
   - Detailed pattern breakdowns
   - Cross-repo relationships

## 🔧 Configuration

### Adjust Sensitivity

In `pattern_analyzer.py`, modify the `find_similar_patterns()` method:

```python
# Current: Alert on any keyword overlap
if keyword_overlap > 0 or pattern_overlap > 0:

# More selective: Require 2+ overlaps
if keyword_overlap > 1 or pattern_overlap > 1:
```

### Customize Notifications

Edit the `notify()` method to change format:

```python
# Add more detail
notification['embeds'][0]['fields'].append({
    "name": "Reusable Components",
    "value": "\n".join(components),
    "inline": False
})
```

### Filter Files

Add to `_is_meaningful_file()`:

```python
ignore_patterns = [
    r'\.lock$', 
    r'test_.*\.py$',  # Ignore test files
    r'.*_generated\..*',  # Ignore generated code
]
```

## 📈 Understanding the Knowledge Base

Your `knowledge_base.json` structure:

```json
{
  "repositories": {
    "username/repo-name": {
      "patterns": {
        "patterns": ["Pattern A", "Pattern B"],
        "decisions": ["Tech decision 1"],
        "reusable_components": [
          {
            "name": "RetryClient",
            "description": "HTTP client with retry logic",
            "files": ["src/client.py"]
          }
        ],
        "dependencies": ["requests", "tenacity"],
        "problem_domain": "Web scraping with resilience",
        "keywords": ["http", "retry", "scraping"]
      },
      "history": [
        {
          "timestamp": "2024-12-01T10:00:00",
          "commit_sha": "abc123",
          "patterns": {...}
        }
      ]
    }
  },
  "last_updated": "2024-12-01T12:00:00"
}
```

## 🎯 Advanced Usage

### Pre-commit Checking

Install the pre-commit hook:

```bash
# Make executable
chmod +x pre_commit_check.py

# Add to git hooks
cp pre_commit_check.py .git/hooks/pre-commit

# Set environment
export ANTHROPIC_API_KEY="your-key"
export KNOWLEDGE_BASE_URL="https://raw.githubusercontent.com/user/kb/main/knowledge_base.json"
```

Now on every commit:
```bash
git commit -m "Add feature"

# Output:
🔍 Checking patterns...
⚠️  Pattern Analysis Warnings:

1. Your new error handling resembles pattern in web-scraper
   Similar to: username/web-scraper
   💡 Consider using the same approach for consistency

Continue with commit? [y/N]
```

### Integration with CI/CD

Add to your `Jenkinsfile` or `.gitlab-ci.yml`:

```yaml
pattern-check:
  stage: validate
  script:
    # Call the reusable workflow or run analyzer directly
    - python scripts/pattern_analyzer.py
  artifacts:
    paths:
      - pattern_analysis.json
```

### Weekly Reports

Set up a cron job to generate reports:

```bash
# crontab -e
0 9 * * 1 cd ~/dev-nexus && python generate_weekly_report.py
```

## 🚀 A2A Integration

The system now supports Agent-to-Agent (A2A) protocol for programmatic access:

### Query Patterns from Other Agents

```bash
curl -X POST https://your-service.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "query_patterns",
    "input": {
      "keywords": ["retry", "exponential backoff"]
    }
  }'
```

### Get Deployment Info

```bash
curl -X POST https://your-service.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "get_deployment_info",
    "input": {
      "repository": "patelmm79/my-repo",
      "include_lessons": true
    }
  }'
```

### Add Lesson Learned (Authenticated)

```bash
curl -X POST https://your-service.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "skill_id": "add_lesson_learned",
    "input": {
      "repository": "patelmm79/my-repo",
      "category": "performance",
      "lesson": "Use connection pooling for database clients",
      "context": "High load caused connection exhaustion",
      "severity": "warning"
    }
  }'
```

**AgentCard**: Published at `/.well-known/agent.json` for discovery

### 🔗 Integration with Other AI Agents

Dev-Nexus acts as the **central pattern intelligence hub** in a distributed system of AI agents:

```
                    ┌────────────────────────┐
                    │   GitHub Repositories   │
                    │   Repo A, B, C, D...    │
                    └───────────┬─────────────┘
                                │
                    ┌───────────▼──────────────┐
                    │      DEV-NEXUS           │
                    │  Pattern Discovery Agent │
                    │                          │
                    │  • Pattern Extraction    │
                    │  • Knowledge Base (v2)   │
                    │  • 9 A2A Skills          │
                    └────┬──────────────┬──────┘
                         │              │
        ┌────────────────┴──┐      ┌───┴────────────────┐
        │                   │      │                    │
        ▼                   ▼      ▼                    ▼
┌──────────────────┐  ┌─────────────────┐  ┌──────────────────┐
│ DEPENDENCY-      │  │ PATTERN-MINER   │  │ Future Agents    │
│ ORCHESTRATOR     │  │                 │  │                  │
│                  │  │ • Deep Analysis │  │ • Testing        │
│ • Triage Agent   │  │ • Code Compare  │  │ • Security       │
│ • Impact Analysis│  │ • Best Practices│  │ • Performance    │
│ • Auto PRs       │  └─────────────────┘  └──────────────────┘
└──────────────────┘
        │
        └──> Creates PRs, Updates Dependents, Records Lessons
```

#### Integration with dependency-orchestrator

**Purpose**: Automated dependency management and update coordination

**How it works:**
1. Dev-Nexus detects pattern/API changes → Notifies orchestrator
2. Orchestrator queries dev-nexus for dependency graph
3. AI triage agent analyzes impact and creates PRs
4. Results recorded back in dev-nexus as lessons learned

**Real Example:**
```
Your API library update → Dev-Nexus detects breaking change
                       ↓
         Orchestrator finds 3 dependent repos
                       ↓
     Auto-creates PRs with context from dev-nexus
                       ↓
        Updates propagate in minutes, not days!
```

**See [INTEGRATION.md](INTEGRATION.md) for complete integration guide with detailed diagrams and examples.**

#### Integration with pattern-miner

**Purpose**: Deep code analysis and pattern comparison

**Capabilities:**
- Line-by-line implementation comparison
- Pattern quality scoring
- Anti-pattern detection
- Best practice recommendations

#### Available Skills for Integration

Dev-Nexus exposes 9 skills via A2A protocol:

**Public Skills (No auth):**
1. `query_patterns` - Search patterns
2. `get_deployment_info` - Get deployment metadata
3. `get_repository_list` - List tracked repos
4. `get_cross_repo_patterns` - Find patterns across repos
5. `health_check_external` - Check external agent health
6. `check_documentation_standards` - Check doc conformity
7. `validate_documentation_update` - Validate doc updates

**Authenticated Skills:**
8. `add_lesson_learned` - Record lessons
9. `update_dependency_info` - Update dependency graphs

#### Configuration

Set these environment variables to enable bidirectional communication:

```bash
# dependency-orchestrator
export ORCHESTRATOR_URL=https://your-orchestrator-service.run.app
export ORCHESTRATOR_TOKEN=your-service-account-token

# pattern-miner
export PATTERN_MINER_URL=https://your-pattern-miner-service.run.app
export PATTERN_MINER_TOKEN=your-service-account-token

# Allow these services to call dev-nexus
export ALLOWED_SERVICE_ACCOUNTS=orchestrator@project.iam.gserviceaccount.com,pattern-miner@project.iam.gserviceaccount.com
```

When pattern analysis completes, dev-nexus automatically:
1. Notifies dependency-orchestrator of pattern changes
2. Requests impact analysis for dependent repos
3. Logs coordination results

## 🔮 Roadmap

### ✅ Phase 1: Pattern Discovery (Complete)
- [x] Pattern extraction with Claude
- [x] Cross-repo similarity detection
- [x] Knowledge base management
- [x] Reusable GitHub workflow
- [x] Dashboard visualization

### ✅ Phase 2: A2A Protocol Support (Complete)
- [x] A2A server with FastAPI
- [x] Three A2A skills (query, get info, add lessons)
- [x] Enhanced knowledge base v2 schema
- [x] Cloud Run deployment
- [x] Flexible authentication

### Phase 3: Enhanced Intelligence (Next)
- [ ] Add vector embeddings for better pattern matching
- [ ] Implement confidence score improvements
- [ ] Pattern recommendation engine
- [ ] Weekly digest notifications
- [ ] Automated refactoring suggestions

### Phase 3: Scale & Observability (Future)
- [ ] Enhanced dashboard features
- [ ] Historical trend analysis
- [ ] Custom notification templates
- [ ] Learning from user feedback

## ☁️ Deployment to Cloud Run

Deploy dev-nexus as a 24/7 A2A service on Google Cloud Run:

### Quick Deployment

```bash
# 1. Set up GCP project
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"

# 2. Set up secrets
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
export GITHUB_TOKEN="ghp_xxxxx"
export KNOWLEDGE_BASE_REPO="username/repo"
bash scripts/setup-secrets.sh

# 3. Deploy
bash scripts/deploy.sh

# 4. Test
SERVICE_URL=$(gcloud run services describe pattern-discovery-agent \
  --region=$GCP_REGION --format="value(status.url)")
curl $SERVICE_URL/health
```

### What You Get

- **24/7 Availability:** Always-on A2A protocol endpoint
- **Auto-scaling:** 0-10 instances based on traffic
- **Secure:** Secrets managed by Google Secret Manager
- **Monitored:** Built-in Cloud Monitoring integration
- **Cost-effective:** Free tier covers most usage

### Complete Documentation

📖 **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide with:
- Prerequisites and API setup
- Step-by-step deployment instructions
- Configuration and scaling options
- Monitoring and alerting setup
- Troubleshooting common issues
- Production readiness checklist
- Cost optimization strategies

📖 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Comprehensive troubleshooting for:
- Deployment failures
- Runtime errors
- Authentication issues
- Performance problems
- Integration debugging

📖 **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design documentation

📖 **[PRODUCTION_READY.md](PRODUCTION_READY.md)** - Production checklist

---

## 🐛 Troubleshooting

### Quick Fixes

#### Action fails immediately
**Check:** Secrets are set correctly (case-sensitive)

#### No notifications
**Check:** Webhook URL is valid, test with curl:
```bash
curl -X POST $DISCORD_WEBHOOK_URL -H "Content-Type: application/json" -d '{"content": "test"}'
```

#### Knowledge base not updating
**Check:**
- `KNOWLEDGE_BASE_REPO` format is `username/repo`
- GitHub token has `repo` scope
- KB repo exists and is accessible

#### Too many false positives
**Adjust:** Increase thresholds in `find_similar_patterns()`

#### Not enough detection
**Adjust:**
- Increase context in LLM prompts
- Add more keywords to extraction
- Lower similarity thresholds

### Complete Troubleshooting

📖 **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Comprehensive guide covering 50+ scenarios with diagnostic commands and solutions

## 💰 Cost Estimation

Typical monthly costs for active development:

- **GitHub Actions**: Free (public repos), ~$2-5 (private)
- **Claude API**:
  - Per analysis: $0.01-0.05
  - 50 commits/month: $0.50-2.50
- **Storage**: Free (JSON in GitHub)

**Total: $3-8/month** for 5-10 active repositories

**Need dependency orchestration?** The companion [dependency-orchestrator](https://github.com/patelmm79/dependency-orchestrator) adds ~$3-5/month for AI triage agents.

## 🤝 Contributing

This is your personal system, but you can extend it:

1. Fork patterns for specific languages/frameworks
2. Add domain-specific pattern extractors
3. Build custom notification formatters
4. Share your `knowledge_base.json` structure

## 📖 Documentation Index

### Getting Started
| Document | Purpose | Audience |
|----------|---------|----------|
| **[README.md](README.md)** | Project overview and quick start | Everyone |
| **[QUICK_START.md](QUICK_START.md)** | Detailed setup instructions | New users |
| **[CLAUDE.md](CLAUDE.md)** | AI assistant guidance | Claude Code |

### Deployment & Operations
| Document | Purpose | Audience |
|----------|---------|----------|
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Complete Cloud Run deployment guide | DevOps |
| **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** | Comprehensive troubleshooting (50+ scenarios) | Operators |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | System design and components | Architects |
| **[PRODUCTION_READY.md](PRODUCTION_READY.md)** | Production readiness checklist | DevOps |

### Integration & Development
| Document | Purpose | Audience |
|----------|---------|----------|
| **[INTEGRATION.md](INTEGRATION.md)** | Complete A2A integration guide | Developers |
| **[INTEGRATION_LOG_ATTACKER.md](INTEGRATION_LOG_ATTACKER.md)** | Log attacker integration example | Developers |
| **[API.md](API.md)** | API reference and endpoints | Developers |
| **[AGENTCARD.md](AGENTCARD.md)** | AgentCard specification | Developers |
| **[A2A_QUICKSTART.md](A2A_QUICKSTART.md)** | Local A2A development | Developers |

### Extension & Contribution
| Document | Purpose | Audience |
|----------|---------|----------|
| **[EXTENDING_DEV_NEXUS.md](EXTENDING_DEV_NEXUS.md)** | How to add features and skills | Contributors |
| **[docs/QUICK_START_EXTENDING.md](docs/QUICK_START_EXTENDING.md)** | Quick guide to adding skills | Contributors |
| **[docs/DOCUMENTATION_STANDARDS.md](docs/DOCUMENTATION_STANDARDS.md)** | Documentation requirements | Contributors |
| **[docs/LICENSE_STANDARD.md](docs/LICENSE_STANDARD.md)** | GPL v3 licensing standard | Contributors |
| **[docs/LESSONS_LEARNED_ARCHITECTURE.md](docs/LESSONS_LEARNED_ARCHITECTURE.md)** | Architectural lessons learned | Architects |

### Examples
| Document | Purpose | Audience |
|----------|---------|----------|
| **[examples/integration_scenarios.md](examples/integration_scenarios.md)** | Integration examples | Developers |
| **[examples/add_documentation_review_skill.md](examples/add_documentation_review_skill.md)** | Adding new skills example | Developers |

### Infrastructure
| Document | Purpose | Audience |
|----------|---------|----------|
| **[terraform/README.md](terraform/README.md)** | Terraform infrastructure guide | DevOps |
| **[config/README.md](config/README.md)** | Configuration reference | Operators |

### Quick Navigation by Task

**"I want to deploy to Cloud Run"**
→ [DEPLOYMENT.md](DEPLOYMENT.md)

**"I want to integrate with another agent"**
→ [INTEGRATION.md](INTEGRATION.md)

**"Something is broken"**
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

**"I want to add a new skill"**
→ [EXTENDING_DEV_NEXUS.md](EXTENDING_DEV_NEXUS.md)

**"I want to understand the architecture"**
→ [ARCHITECTURE.md](ARCHITECTURE.md)

**"I want to check documentation standards"**
→ [docs/DOCUMENTATION_STANDARDS.md](docs/DOCUMENTATION_STANDARDS.md)

---

## 📚 Related Resources

- [Claude Prompt Engineering](https://docs.anthropic.com/claude/docs)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [Architectural Decision Records](https://adr.github.io/)

## 🎓 Learning More

This system implements several concepts:

- **Knowledge Graphs**: Connecting repos by patterns
- **Semantic Analysis**: Understanding code intent, not just text
- **Proactive Monitoring**: Catching issues before they spread
- **Institutional Memory**: Codifying decisions automatically

## 📝 License

This project is licensed under the **GNU General Public License v3.0** (GPL-3.0).

**What this means:**
- ✅ **Free to use** for any purpose
- ✅ **Free to modify** and create derivative works
- ✅ **Free to distribute** copies
- ⚠️ **Copyleft**: Derivative works must also be GPL-3.0
- ✅ **Patent protection** for users
- ✅ **Source code** must remain available

See the [LICENSE](LICENSE) file for full details or visit [https://www.gnu.org/licenses/gpl-3.0](https://www.gnu.org/licenses/gpl-3.0).

**Why GPL v3?** This ensures that all improvements and derivative works benefit the entire community and remain free software.

---

**Remember:** This system is a tool to help you maintain consistency as you scale. It's not about restricting creativity—it's about making informed decisions and avoiding accidental inconsistency.

Start small, iterate, and let it grow with your needs. 🚀
