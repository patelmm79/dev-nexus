# A2A Pattern Discovery Agent - Quick Start Guide

## 🎉 Implementation Complete!

Your Pattern Discovery Agent has been successfully converted to an A2A (Agent-to-Agent) protocol server. This guide will help you get started.

## 📋 What Was Built

### Hybrid Architecture
- ✅ **Existing GitHub Actions workflow** continues to work unchanged
- ✅ **New A2A server** exposes pattern discovery via agent protocol
- ✅ **Shared core logic** used by both CLI and A2A server

### Enhanced Knowledge Base (v2)
- Patterns (existing)
- **NEW**: Deployment info (scripts, lessons learned, reusable components)
- **NEW**: Dependencies (consumers, derivatives, external deps)
- **NEW**: Testing metadata
- **NEW**: Security information

### A2A Skills
1. **query_patterns** (Public) - Search for similar patterns across repositories
2. **get_deployment_info** (Public) - Get deployment and infrastructure information
3. **add_lesson_learned** (Authenticated) - Record lessons learned

## 🚀 Local Development

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

```bash
# Copy example and edit with your credentials
cp .env.example .env

# Required variables:
# - ANTHROPIC_API_KEY=sk-ant-xxxxx
# - GITHUB_TOKEN=ghp_xxxxx
# - KNOWLEDGE_BASE_REPO=patelmm79/dev-nexus
```

### 3. Run Server Locally

```bash
# Option 1: Using the dev script
bash scripts/dev-server.sh

# Option 2: Direct uvicorn
python a2a/server.py

# Option 3: Uvicorn with reload
uvicorn a2a.server:app --host 0.0.0.0 --port 8080 --reload
```

### 4. Test Endpoints

```bash
# Health check
curl http://localhost:8080/health

# Get AgentCard
curl http://localhost:8080/.well-known/agent.json | jq

# Query patterns (public)
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "query_patterns",
    "input": {
      "keywords": ["retry", "exponential backoff"]
    }
  }' | jq

# Get deployment info (public)
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "get_deployment_info",
    "input": {
      "repository": "patelmm79/my-repo",
      "include_lessons": true
    }
  }' | jq

# Add lesson learned (requires auth)
curl -X POST http://localhost:8080/a2a/execute \
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
  }' | jq
```

## ☁️ Cloud Run Deployment

### 1. Set Up GCP

```bash
# Set environment variables
export GCP_PROJECT_ID="your-project-id"
export GCP_REGION="us-central1"
export KNOWLEDGE_BASE_REPO="patelmm79/dev-nexus"

# Authenticate
gcloud auth login
gcloud config set project $GCP_PROJECT_ID
```

### 2. Create Secrets

```bash
# Set your credentials
export GITHUB_TOKEN="ghp_xxxxx"
export ANTHROPIC_API_KEY="sk-ant-xxxxx"

# Run setup script
bash scripts/setup-secrets.sh
```

### 3. Deploy to Cloud Run

```bash
# Deploy using the script
bash scripts/deploy.sh

# The script will:
# 1. Build Docker image via Cloud Build
# 2. Deploy to Cloud Run
# 3. Configure secrets
# 4. Test endpoints
# 5. Print service URL
```

### 4. Update GitHub Actions Workflows (Optional)

Your existing workflows continue to work as-is. To also notify the A2A service:

```yaml
# In monitored project's .github/workflows/pattern-monitoring.yml
- name: Notify A2A Service
  if: env.A2A_SERVICE_URL != ''
  run: |
    curl -X POST "${{ secrets.A2A_SERVICE_URL }}/api/webhook" \
      -H "Content-Type: application/json" \
      -d @pattern_analysis.json
```

## 🔑 Authentication

### Public Skills (No Auth Required)
- `query_patterns` - Anyone can search patterns
- `get_deployment_info` - Anyone can read deployment info

### Authenticated Skills
- `add_lesson_learned` - Requires A2A authentication with allowed service account

### Configure Authentication

```bash
# In .env or Cloud Run environment variables:

# Mode: "workload_identity" (Cloud Run default) or "service_account"
AUTH_MODE=workload_identity

# Comma-separated list of allowed service accounts
ALLOWED_SERVICE_ACCOUNTS=agent1@project.iam.gserviceaccount.com,agent2@project.iam.gserviceaccount.com

# Optional: Service account JSON for local dev
SERVICE_ACCOUNT_JSON=/path/to/service-account-key.json
```

## 📊 Knowledge Base Migration

The system automatically migrates v1 knowledge base to v2 on first load:

```python
# Migration happens automatically in KnowledgeBaseManager
kb = kb_manager.load_knowledge_base()  # Auto-migrates if needed

# New v2 features:
# - Deployment info (scripts, lessons, components)
# - Dependency graph (consumers, derivatives)
# - Testing metadata
# - Security posture
```

## 🧪 Testing

```bash
# Run unit tests (create tests/ directory first)
pytest tests/ -v

# Test local server
bash scripts/test-local.sh

# Test deployed service
SERVICE_URL=$(gcloud run services describe pattern-discovery-agent \
  --region=us-central1 --format="value(status.url)")

curl ${SERVICE_URL}/health
curl ${SERVICE_URL}/.well-known/agent.json
```

## 📚 File Structure

```
architecture-kb/  (now dev-nexus)
├── a2a/                    # A2A server module
│   ├── server.py          # FastAPI application
│   ├── executor.py        # AgentExecutor
│   ├── auth.py            # Authentication
│   └── config.py          # Configuration
├── core/                   # Shared business logic
│   ├── pattern_extractor.py
│   ├── knowledge_base.py
│   └── similarity_finder.py
├── schemas/                # Data models
│   ├── knowledge_base_v2.py
│   └── migration.py
├── scripts/
│   ├── pattern_analyzer.py  # Refactored CLI (still works!)
│   ├── deploy.sh
│   ├── dev-server.sh
│   └── setup-secrets.sh
├── Dockerfile
├── cloudbuild.yaml
└── requirements.txt
```

## 🔄 Workflow Comparison

### Before (GitHub Actions Only)
```
Push → Workflow → pattern_analyzer.py → Extract patterns → Update KB → Notify
```

### After (Hybrid)
```
# Option 1: GitHub Actions (unchanged)
Push → Workflow → pattern_analyzer.py → core/ modules → Update KB

# Option 2: A2A Query
Agent → A2A /execute → executor → core/ modules → Return results

# Option 3: A2A Write
Agent → A2A /execute (auth) → add_lesson_learned → Update KB
```

## 🎯 Next Steps

1. **Test locally**: Run the dev server and test all endpoints
2. **Deploy to Cloud Run**: Use `scripts/deploy.sh`
3. **Integrate with other agents**: Use the AgentCard to call from other A2A agents
4. **Add more lessons**: Use `add_lesson_learned` to build institutional memory
5. **Monitor usage**: Check Cloud Run logs and metrics

## 🐛 Troubleshooting

### Port already in use
```bash
# Kill process on port 8080
lsof -ti:8080 | xargs kill -9
```

### Import errors
```bash
# Make sure parent directory is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Secret Manager errors
```bash
# Check permissions
gcloud secrets list
gcloud secrets describe GITHUB_TOKEN
```

### Authentication failures
```bash
# Verify service account
gcloud auth list

# Check allowed accounts
echo $ALLOWED_SERVICE_ACCOUNTS
```

## 📖 Additional Resources

- [A2A Protocol Documentation](https://google.github.io/adk-docs/a2a/)
- [Google ADK Guide](https://google.github.io/adk-docs/)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Implementation Plan](C:\Users\insan\.claude\plans\splendid-brewing-petal.md)

## 💡 Tips

- **Start local**: Test everything locally before deploying
- **Use .env**: Keep credentials in `.env` for local development
- **Monitor costs**: Cloud Run bills per request, set max instances
- **Version control**: Commit and push before deploying
- **Test auth**: Verify authentication works with test service account
- **Check logs**: Use `gcloud run logs read` for debugging

---

**Congratulations!** Your Pattern Discovery Agent is now an A2A-enabled service! 🎉
