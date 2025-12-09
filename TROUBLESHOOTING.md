# Troubleshooting Guide: dev-nexus

> **Quick Reference:** Common issues and their solutions

---

## Table of Contents

1. [Deployment Issues](#deployment-issues)
2. [Runtime Issues](#runtime-issues)
3. [Authentication Issues](#authentication-issues)
4. [Knowledge Base Issues](#knowledge-base-issues)
5. [Integration Issues](#integration-issues)
6. [Performance Issues](#performance-issues)
7. [Diagnostic Commands](#diagnostic-commands)

---

## Deployment Issues

### Issue: Cloud Build Fails with "Permission Denied"

**Symptoms:**
```
ERROR: (gcloud.builds.submit) PERMISSION_DENIED:
The caller does not have permission
```

**Root Cause:** Cloud Build service account lacks necessary IAM roles

**Solution:**

```bash
# Get project number
PROJECT_NUMBER=$(gcloud projects describe $GCP_PROJECT_ID \
  --format="value(projectNumber)")

# Grant Cloud Build required roles
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Retry deployment
bash scripts/deploy.sh
```

**Prevention:** Run `scripts/setup-permissions.sh` before first deployment (to be created)

---

### Issue: "Secret not found" During Deployment

**Symptoms:**
```
ERROR: Secret 'GITHUB_TOKEN' not found in project
```

**Root Cause:** Secrets not created in Secret Manager

**Solution:**

```bash
# Verify secrets exist
gcloud secrets list --project=$GCP_PROJECT_ID

# If missing, create them
export GITHUB_TOKEN="ghp_xxxxx"
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
bash scripts/setup-secrets.sh

# Verify secrets created
gcloud secrets list --project=$GCP_PROJECT_ID

# Redeploy
bash scripts/deploy.sh
```

---

### Issue: Docker Build Fails - "Cannot Find Module"

**Symptoms:**
```
ModuleNotFoundError: No module named 'a2a'
```

**Root Cause:** Incorrect PYTHONPATH or missing files in Docker image

**Solution:**

```bash
# Verify all required directories exist locally
ls -la a2a/
ls -la core/
ls -la schemas/

# Verify .dockerignore isn't excluding needed files
cat .dockerignore

# Test local build
docker build -t test-image .
docker run --rm test-image python -c "import a2a; print('OK')"

# If local build works, clean and redeploy
gcloud artifacts docker images delete \
  gcr.io/$GCP_PROJECT_ID/pattern-discovery-agent:latest \
  --quiet
bash scripts/deploy.sh
```

---

### Issue: Deployment Succeeds but Service Shows "Revision Failed"

**Symptoms:**
- Cloud Build succeeds
- Service shows as unhealthy
- Logs show startup errors

**Root Cause:** Application error on startup

**Solution:**

```bash
# Check logs for startup errors
gcloud run services logs read pattern-discovery-agent \
  --region=$GCP_REGION \
  --limit=100

# Common startup errors:

# 1. Missing environment variable
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --set-env-vars="MISSING_VAR=value"

# 2. Secret access denied
bash scripts/setup-secrets.sh  # Re-grant permissions

# 3. Invalid knowledge base repo format
# Fix: Ensure KNOWLEDGE_BASE_REPO="owner/repo" (not URL)
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --set-env-vars="KNOWLEDGE_BASE_REPO=username/repository"
```

---

## Runtime Issues

### Issue: Health Check Returns 503 Service Unavailable

**Symptoms:**
```bash
$ curl $SERVICE_URL/health
<html><head>
<title>503 Service Unavailable</title>
</head></html>
```

**Root Cause #1:** Cold start - service is starting up

**Solution:**
```bash
# Wait 30-60 seconds for cold start
sleep 60
curl $SERVICE_URL/health
```

**Root Cause #2:** Application crashed on startup

**Solution:**
```bash
# Check logs
gcloud run services logs read pattern-discovery-agent \
  --region=$GCP_REGION \
  --limit=50

# Common errors:
# - "Connection refused" to GitHub → Check GITHUB_TOKEN
# - "Anthropic API error" → Check ANTHROPIC_API_KEY
# - "Repository not found" → Check KNOWLEDGE_BASE_REPO format

# Verify secrets are accessible
gcloud run services describe pattern-discovery-agent \
  --region=$GCP_REGION \
  --format="yaml(spec.template.spec.containers[0].env)"
```

**Root Cause #3:** Memory limit exceeded

**Solution:**
```bash
# Check memory usage in logs
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=pattern-discovery-agent \
  AND textPayload=~'memory'" \
  --limit 20

# Increase memory if needed
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --memory=2Gi
```

---

### Issue: Skill Execution Returns 500 Internal Server Error

**Symptoms:**
```json
{
  "error": "Internal server error",
  "detail": "Skill execution failed"
}
```

**Root Cause:** Skill code error or dependency issue

**Solution:**

```bash
# Get detailed error from logs
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=pattern-discovery-agent \
  AND severity=ERROR" \
  --limit 10 \
  --format json

# Common skill errors:

# 1. Knowledge base access error
# Check GitHub token has repo access
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/YOUR_ORG/YOUR_REPO

# 2. Anthropic API error
# Check API key is valid
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{"model": "claude-sonnet-4-20250514", "max_tokens": 10, "messages": [{"role": "user", "content": "test"}]}'

# 3. Invalid input schema
# Check skill input matches schema
curl -X POST $SERVICE_URL/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "get_pattern_health",
    "input": {
      "pattern_name": "test"
    }
  }' | jq
```

---

### Issue: Timeout Errors (504 Gateway Timeout)

**Symptoms:**
```
Error: deadline exceeded
504 Gateway Timeout
```

**Root Cause:** Request taking longer than timeout limit (default 300s)

**Solution:**

```bash
# Increase timeout (max 3600s = 1 hour)
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --timeout=900  # 15 minutes

# For specific long-running operations, consider:
# 1. Async processing with callbacks
# 2. Breaking into smaller requests
# 3. Caching intermediate results
```

---

## Authentication Issues

### Issue: 403 Forbidden When Calling Authenticated Skills

**Symptoms:**
```json
{
  "detail": "Not authenticated"
}
```

**Root Cause #1:** No authentication provided

**Solution:**
```bash
# Get service account token
TOKEN=$(gcloud auth print-identity-token \
  --impersonate-service-account=your-sa@project.iam.gserviceaccount.com)

# Call with authentication
curl -X POST $SERVICE_URL/a2a/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "skill_id": "add_lesson_learned",
    "input": {...}
  }'
```

**Root Cause #2:** Service account not in ALLOWED_SERVICE_ACCOUNTS

**Solution:**
```bash
# Add service account to allowed list
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --set-env-vars="ALLOWED_SERVICE_ACCOUNTS=sa1@project.iam.gserviceaccount.com,sa2@project.iam.gserviceaccount.com"

# Verify
gcloud run services describe pattern-discovery-agent \
  --region=$GCP_REGION \
  --format="yaml(spec.template.spec.containers[0].env)" | grep ALLOWED
```

**Root Cause #3:** Service account lacks Cloud Run Invoker role

**Solution:**
```bash
# Grant invoker role
gcloud run services add-iam-policy-binding pattern-discovery-agent \
  --region=$GCP_REGION \
  --member="serviceAccount:your-sa@project.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

# Verify
gcloud run services get-iam-policy pattern-discovery-agent \
  --region=$GCP_REGION
```

---

### Issue: External Agent Cannot Authenticate

**Symptoms:**
```
Error: Authentication failed
Service account not authorized
```

**Root Cause:** Workload Identity not configured for external service

**Solution:**

```bash
# 1. Create service account for external agent
gcloud iam service-accounts create log-attacker-client \
  --display-name="Log Attacker Client"

# 2. Grant Cloud Run invoker permission
gcloud run services add-iam-policy-binding pattern-discovery-agent \
  --region=$GCP_REGION \
  --member="serviceAccount:log-attacker-client@${GCP_PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

# 3. Add to allowed service accounts
CURRENT_ALLOWED=$(gcloud run services describe pattern-discovery-agent \
  --region=$GCP_REGION \
  --format="value(spec.template.spec.containers[0].env[name=ALLOWED_SERVICE_ACCOUNTS].value)")

gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --set-env-vars="ALLOWED_SERVICE_ACCOUNTS=${CURRENT_ALLOWED},log-attacker-client@${GCP_PROJECT_ID}.iam.gserviceaccount.com"

# 4. In external agent, use service account to get token
# (See INTEGRATION.md for code examples)
```

---

## Knowledge Base Issues

### Issue: "Repository Not Found" Error

**Symptoms:**
```
Error: Repository 'username/repo' not found
```

**Root Cause #1:** GitHub token lacks access

**Solution:**
```bash
# Test token access
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/username/repo

# If 404:
# 1. Check repository name is correct
# 2. Verify token has 'repo' scope
# 3. For private repos, ensure token owner has access

# Update token in Secret Manager
export GITHUB_TOKEN="ghp_new_token_with_access"
echo -n "$GITHUB_TOKEN" | gcloud secrets versions add GITHUB_TOKEN \
  --data-file=- \
  --project=$GCP_PROJECT_ID

# Redeploy to pick up new secret
bash scripts/deploy.sh
```

**Root Cause #2:** Invalid KNOWLEDGE_BASE_REPO format

**Solution:**
```bash
# Check current value
gcloud run services describe pattern-discovery-agent \
  --region=$GCP_REGION \
  --format="value(spec.template.spec.containers[0].env[name=KNOWLEDGE_BASE_REPO].value)"

# Should be: "owner/repo" NOT:
# - "https://github.com/owner/repo" ❌
# - "github.com/owner/repo" ❌
# - "owner/repo.git" ❌

# Fix if wrong
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --set-env-vars="KNOWLEDGE_BASE_REPO=username/repository"
```

---

### Issue: Knowledge Base File Corruption

**Symptoms:**
```
Error: Failed to parse knowledge base JSON
JSONDecodeError: Expecting value
```

**Root Cause:** Concurrent writes or manual edit caused invalid JSON

**Solution:**

```bash
# 1. Backup current KB
git clone https://github.com/username/kb-repo.git
cp kb-repo/knowledge_base.json kb-backup-$(date +%Y%m%d).json

# 2. Validate JSON
cat kb-repo/knowledge_base.json | jq . > /dev/null

# If invalid, fix:
# Option A: Restore from git history
cd kb-repo
git log --oneline -- knowledge_base.json
git show COMMIT_SHA:knowledge_base.json > knowledge_base.json
git add knowledge_base.json
git commit -m "Restore KB from COMMIT_SHA"
git push

# Option B: Recreate from scratch
cat > knowledge_base.json << 'EOF'
{
  "schema_version": "2.0",
  "repositories": {}
}
EOF
git add knowledge_base.json
git commit -m "Reset knowledge base"
git push

# 3. Verify service can access it
curl -X POST $SERVICE_URL/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "get_repository_list",
    "input": {}
  }'
```

---

### Issue: Knowledge Base Updates Failing

**Symptoms:**
```
Error: Failed to update knowledge base
Permission denied
```

**Root Cause:** GitHub token lacks write access

**Solution:**

```bash
# Check token permissions
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/username/repo | jq '.permissions'

# Should show:
# {
#   "admin": true,
#   "push": true,   <-- Need this
#   "pull": true
# }

# If push: false:
# 1. Generate new token with write access
# 2. Update secret
export GITHUB_TOKEN="ghp_new_token_with_write"
echo -n "$GITHUB_TOKEN" | gcloud secrets versions add GITHUB_TOKEN \
  --data-file=- \
  --project=$GCP_PROJECT_ID

# 3. Restart service
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --update-labels=restarted=$(date +%s)
```

---

## Integration Issues

### Issue: External Agent Cannot Reach dev-nexus

**Symptoms:**
```
Connection refused
Connection timeout
```

**Root Cause #1:** Firewall or network restrictions

**Solution:**
```bash
# Test connectivity from external agent
curl -v $DEV_NEXUS_URL/health

# If connection refused:
# 1. Check Cloud Run service is running
gcloud run services describe pattern-discovery-agent \
  --region=$GCP_REGION \
  --format="value(status.conditions)"

# 2. Check URL is correct (should be https://)
echo $DEV_NEXUS_URL

# 3. Test from different network
curl https://pattern-discovery-agent-xxxxx.run.app/health
```

**Root Cause #2:** Service requires authentication but agent not configured

**Solution:**
```bash
# Check if service requires auth
gcloud run services describe pattern-discovery-agent \
  --region=$GCP_REGION \
  --format="value(spec.template.metadata.annotations['run.googleapis.com/ingress'])"

# If authenticated, get token in external agent
TOKEN=$(gcloud auth print-identity-token \
  --impersonate-service-account=external-agent@project.iam.gserviceaccount.com)

# Use token in requests
curl -H "Authorization: Bearer $TOKEN" $DEV_NEXUS_URL/health
```

---

### Issue: Agentic-Log-Attacker Integration Not Working

**Symptoms:**
```
Runtime issues not appearing in knowledge base
Pattern health shows no data
```

**Root Cause:** Integration not configured

**Solution:**

**In agentic-log-attacker:**

```bash
# 1. Verify environment variables
cat .env | grep DEV_NEXUS
# Should show:
# DEV_NEXUS_URL=https://...
# DEVNEXUS_INTEGRATION_ENABLED=true

# 2. Test connectivity
python -c "
import os
import httpx
url = os.getenv('DEV_NEXUS_URL')
response = httpx.get(f'{url}/health')
print(f'Status: {response.status_code}')
print(response.json())
"

# 3. Test skill execution
python examples/log_attacker_integration.py
```

**In dev-nexus:**

```bash
# Verify runtime monitoring skills loaded
curl $SERVICE_URL/.well-known/agent.json | jq '.skills[] | select(.id | contains("runtime"))'

# Should show:
# - add_runtime_issue
# - get_pattern_health
# - query_known_issues
```

---

## Performance Issues

### Issue: Slow Response Times (>5 seconds)

**Symptoms:**
- Requests take 5-30 seconds
- Timeout warnings in logs

**Root Cause:** Cold start or inefficient query

**Solution:**

**For cold starts:**
```bash
# Set minimum instances to keep warm
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --min-instances=1

# Cost: ~$5-10/month for 1 always-on instance
```

**For slow queries:**
```bash
# 1. Check logs for slow operations
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=pattern-discovery-agent \
  AND jsonPayload.duration_ms>3000" \
  --limit 20

# 2. Increase CPU
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --cpu=2

# 3. Increase memory
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --memory=2Gi

# 4. Enable request concurrency
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --concurrency=10  # Process 10 requests per instance
```

---

### Issue: High Memory Usage / Out of Memory

**Symptoms:**
```
Error: Memory limit exceeded
Container killed
```

**Root Cause:** Large knowledge base or memory leak

**Solution:**

```bash
# 1. Check memory usage
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=pattern-discovery-agent \
  AND jsonPayload.message=~'memory'" \
  --limit 10

# 2. Increase memory limit
gcloud run services update pattern-discovery-agent \
  --region=$GCP_REGION \
  --memory=4Gi  # or 8Gi

# 3. Optimize knowledge base
# - Archive old history entries
# - Split into multiple files
# - Add pagination to queries

# 4. Restart service to clear memory
gcloud run deploy pattern-discovery-agent \
  --region=$GCP_REGION \
  --image=gcr.io/$GCP_PROJECT_ID/pattern-discovery-agent:latest
```

---

### Issue: Rate Limiting from External APIs

**Symptoms:**
```
Error: Rate limit exceeded
429 Too Many Requests
```

**Root Cause:** Too many requests to GitHub or Anthropic API

**Solution:**

**For GitHub API:**
```bash
# Check rate limit status
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/rate_limit

# If rate limited:
# 1. Use authenticated requests (5000/hour vs 60/hour)
# 2. Implement caching
# 3. Use conditional requests with ETags
# 4. Add retry with exponential backoff

# Increase GitHub rate limit by using multiple tokens
# (rotating tokens in environment)
```

**For Anthropic API:**
```bash
# Check Anthropic usage limits
# (View in console.anthropic.com)

# If rate limited:
# 1. Reduce request frequency
# 2. Add request queuing
# 3. Implement caching for repeated queries
# 4. Contact Anthropic for higher limits
```

---

## Diagnostic Commands

### Get Service Status

```bash
gcloud run services describe pattern-discovery-agent \
  --region=$GCP_REGION \
  --format="table(
    status.conditions[0].status:label='Ready',
    status.conditions[0].message,
    status.latestCreatedRevisionName,
    status.url
  )"
```

### View Recent Logs

```bash
# Last 50 logs
gcloud run services logs read pattern-discovery-agent \
  --region=$GCP_REGION \
  --limit=50

# Error logs only
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=pattern-discovery-agent \
  AND severity>=ERROR" \
  --limit=20 \
  --format=json

# Follow logs (real-time)
gcloud run services logs tail pattern-discovery-agent \
  --region=$GCP_REGION
```

### Check Environment Configuration

```bash
# View all environment variables
gcloud run services describe pattern-discovery-agent \
  --region=$GCP_REGION \
  --format="yaml(spec.template.spec.containers[0].env)"

# View secrets configuration
gcloud run services describe pattern-discovery-agent \
  --region=$GCP_REGION \
  --format="yaml(spec.template.spec.containers[0].env[name~'.*_TOKEN|.*_KEY'])"
```

### Test Service Endpoints

```bash
SERVICE_URL=$(gcloud run services describe pattern-discovery-agent \
  --region=$GCP_REGION \
  --format="value(status.url)")

# Health check
curl -v $SERVICE_URL/health

# AgentCard
curl $SERVICE_URL/.well-known/agent.json | jq

# Skill execution (public skill)
curl -X POST $SERVICE_URL/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "get_repository_list",
    "input": {}
  }' | jq

# Skill execution (authenticated skill)
TOKEN=$(gcloud auth print-identity-token)
curl -X POST $SERVICE_URL/a2a/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "skill_id": "add_lesson_learned",
    "input": {
      "repository": "test/repo",
      "category": "test",
      "lesson": "Test lesson"
    }
  }' | jq
```

### Verify Secrets

```bash
# List secrets
gcloud secrets list --project=$GCP_PROJECT_ID

# Check secret value (be careful!)
gcloud secrets versions access latest \
  --secret=GITHUB_TOKEN \
  --project=$GCP_PROJECT_ID

# Check IAM permissions
gcloud secrets get-iam-policy GITHUB_TOKEN \
  --project=$GCP_PROJECT_ID
```

### Check Resource Usage

```bash
# CPU/Memory metrics (requires Cloud Monitoring)
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/container/cpu/utilizations" AND
    resource.labels.service_name="pattern-discovery-agent"' \
  --format="table(points[0].value.doubleValue)"

# Request count
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count" AND
    resource.labels.service_name="pattern-discovery-agent"' \
  --format="table(metric.labels.response_code_class, points[0].value.int64Value)"
```

---

## Getting Help

### Check Documentation

- **README.md** - Overview and quickstart
- **DEPLOYMENT.md** - Deployment instructions
- **ARCHITECTURE.md** - System design
- **INTEGRATION.md** - External agent integration
- **API.md** - API reference

### Cloud Run Documentation

- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [Troubleshooting Guide](https://cloud.google.com/run/docs/troubleshooting)
- [Logging](https://cloud.google.com/run/docs/logging)

### Report Issues

- GitHub Issues: https://github.com/patelmm79/dev-nexus/issues
- Include:
  - Error message and full stack trace
  - Logs from `gcloud run services logs read`
  - Service configuration
  - Steps to reproduce

---

**Last Updated:** 2025-12-09
**Version:** 1.0
