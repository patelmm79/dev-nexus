# A2A Integration Guide: Bidirectional Agent Communication

## Overview

Dev-nexus serves as the **central hub** for a network of specialized A2A agents, coordinating architectural consistency, pattern discovery, and dependency management across your repositories.

## Architecture

```
                         ┌─────────────────────┐
                         │    dev-nexus        │
                         │  (Pattern Hub)      │
                         │  - Knowledge Base   │
                         │  - 7 A2A Skills     │
                         └──────────┬──────────┘
                                    │
                ┌───────────────────┼───────────────────┐
                │                   │                   │
       ┌────────▼────────┐ ┌───────▼────────┐ ┌───────▼────────┐
       │ dependency-      │ │ pattern-       │ │ (future        │
       │ orchestrator     │ │ miner          │ │  agents)       │
       │                  │ │                │ │                │
       │ - Dep graphs     │ │ - Deep analysis│ │                │
       │ - Impact triage  │ │ - Comparisons  │ │                │
       └──────────────────┘ └────────────────┘ └────────────────┘
```

## External Agents

### 1. dependency-orchestrator

**Purpose**: Manages dependency relationships and coordinates updates across dependent repositories

**Capabilities**:
- Receives pattern change notifications from dev-nexus
- Maintains dependency graph between repositories
- Performs impact analysis when dependencies change
- Triages which repos need attention
- Notifies dependent repositories via GitHub issues/PRs

**A2A Skills Exposed**:
- `receive_change_notification` - Accepts pattern updates from dev-nexus
- `get_impact_analysis` - Returns affected repositories
- `get_dependencies` - Returns dependency graph for a repo

**Integration**:
```bash
# Set in dev-nexus environment
ORCHESTRATOR_URL=https://dependency-orchestrator-xxxxx.run.app
ORCHESTRATOR_TOKEN=<service-account-token>

# Allow orchestrator to call dev-nexus
ALLOWED_SERVICE_ACCOUNTS=orchestrator@project.iam.gserviceaccount.com,...
```

### 2. pattern-miner

**Purpose**: Deep pattern extraction and code comparison across repositories

**Capabilities**:
- Detailed pattern analysis beyond dev-nexus's basic extraction
- Compares how different repos implement the same patterns
- Provides pattern recommendations based on context
- Analyzes code quality and adherence to best practices

**A2A Skills Exposed**:
- `analyze_repository` - Deep pattern analysis for specific files
- `compare_implementations` - Compare pattern implementations across repos
- `get_recommendations` - Pattern recommendations based on context

**Integration**:
```bash
# Set in dev-nexus environment
PATTERN_MINER_URL=https://pattern-miner-xxxxx.run.app
PATTERN_MINER_TOKEN=<service-account-token>

# Allow pattern-miner to call dev-nexus
ALLOWED_SERVICE_ACCOUNTS=pattern-miner@project.iam.gserviceaccount.com,...
```

## Dev-Nexus A2A Skills

### Public Skills (No Authentication)

#### 1. query_patterns
Search for similar architectural patterns across all repositories

**Use Case**: dependency-orchestrator queries dev-nexus to find repos with similar error handling before making recommendations

```bash
curl -X POST https://dev-nexus-xxxxx.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "query_patterns",
    "input": {
      "keywords": ["retry", "circuit breaker"],
      "min_matches": 1
    }
  }'
```

#### 2. get_deployment_info
Retrieve deployment metadata and lessons learned

**Use Case**: pattern-miner gets deployment context before analyzing code

```bash
curl -X POST https://dev-nexus-xxxxx.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "get_deployment_info",
    "input": {
      "repository": "patelmm79/api-service",
      "include_lessons": true
    }
  }'
```

#### 3. get_repository_list
List all tracked repositories with metadata

**Use Case**: dependency-orchestrator discovers all repos in the ecosystem

```bash
curl -X POST https://dev-nexus-xxxxx.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "get_repository_list",
    "input": {
      "include_metadata": true
    }
  }'
```

#### 4. get_cross_repo_patterns
Find patterns used across multiple repositories

**Use Case**: pattern-miner identifies common patterns for comparison analysis

```bash
curl -X POST https://dev-nexus-xxxxx.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "get_cross_repo_patterns",
    "input": {
      "min_repos": 3,
      "pattern_type": "authentication"
    }
  }'
```

#### 5. health_check_external
Check health of external A2A agents

**Use Case**: Monitoring system verifies all agents are operational

```bash
curl -X POST https://dev-nexus-xxxxx.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "health_check_external",
    "input": {}
  }'
```

### Authenticated Skills (Require Token)

#### 6. add_lesson_learned
Record lessons learned for a repository

**Use Case**: dependency-orchestrator records deployment issues discovered during triage

```bash
curl -X POST https://dev-nexus-xxxxx.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ORCHESTRATOR_TOKEN" \
  -d '{
    "skill_id": "add_lesson_learned",
    "input": {
      "repository": "patelmm79/api-service",
      "category": "reliability",
      "lesson": "Always implement graceful shutdown for long-running tasks",
      "context": "Service terminated mid-request during deployment",
      "severity": "warning",
      "recorded_by": "dependency-orchestrator"
    }
  }'
```

#### 7. update_dependency_info
Update dependency graph information

**Use Case**: dependency-orchestrator updates the dependency graph after analyzing imports

```bash
curl -X POST https://dev-nexus-xxxxx.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ORCHESTRATOR_TOKEN" \
  -d '{
    "skill_id": "update_dependency_info",
    "input": {
      "repository": "patelmm79/shared-lib",
      "dependency_info": {
        "consumers": [
          {"repository": "patelmm79/api-service", "relationship": "imports"},
          {"repository": "patelmm79/worker-service", "relationship": "imports"}
        ],
        "derivatives": [],
        "external_dependencies": ["requests", "pydantic", "tenacity"]
      }
    }
  }'
```

## Workflow Examples

### Example 1: Pattern Change Notification

**Trigger**: Developer pushes code to `api-service`

1. GitHub Actions triggers pattern analyzer
2. Dev-nexus extracts patterns using Claude
3. Dev-nexus updates knowledge base
4. **Integration Service** calls `dependency-orchestrator`:
   ```python
   coordination_result = integration_service.coordinate_pattern_update(
       repository="patelmm79/api-service",
       patterns=extracted_patterns,
       commit_sha="abc123"
   )
   ```
5. dependency-orchestrator analyzes impact
6. dependency-orchestrator returns list of affected repos
7. dependency-orchestrator creates GitHub issues in affected repos

### Example 2: Deep Pattern Analysis Request

**Trigger**: dependency-orchestrator finds inconsistency in error handling

1. dependency-orchestrator calls `pattern-miner`:
   ```python
   analysis = miner_client.execute_skill(
       skill_id="compare_implementations",
       input_data={
           "repositories": ["api-service", "worker-service"],
           "pattern_type": "error_handling"
       }
   )
   ```
2. pattern-miner calls dev-nexus `query_patterns` to get baseline
3. pattern-miner performs deep analysis
4. pattern-miner returns comparison with recommendations
5. dependency-orchestrator calls dev-nexus `add_lesson_learned` to record findings

### Example 3: Repository Discovery

**Trigger**: New monitoring agent wants to understand ecosystem

1. Monitoring agent calls dev-nexus `get_repository_list`
2. For each repository, calls `get_deployment_info`
3. Calls `health_check_external` to verify all agents operational
4. Aggregates data into dashboard

## Setting Up Bidirectional Communication

### 1. Deploy All Services

```bash
# Deploy dev-nexus
cd dev-nexus
bash scripts/deploy.sh

# Deploy dependency-orchestrator
cd dependency-orchestrator
bash scripts/deploy.sh

# Deploy pattern-miner
cd pattern-miner
bash scripts/deploy.sh
```

### 2. Configure Service Accounts

Each service needs a Google Cloud service account with appropriate permissions:

```bash
# Create service accounts
gcloud iam service-accounts create dev-nexus-sa
gcloud iam service-accounts create orchestrator-sa
gcloud iam service-accounts create pattern-miner-sa

# Grant Cloud Run Invoker role to each
gcloud run services add-iam-policy-binding dev-nexus \
  --member="serviceAccount:orchestrator-sa@project.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### 3. Set Environment Variables

**In dev-nexus**:
```bash
ORCHESTRATOR_URL=https://dependency-orchestrator-xxxxx.run.app
PATTERN_MINER_URL=https://pattern-miner-xxxxx.run.app
ALLOWED_SERVICE_ACCOUNTS=orchestrator-sa@project.iam.gserviceaccount.com,pattern-miner-sa@project.iam.gserviceaccount.com
```

**In dependency-orchestrator**:
```bash
DEV_NEXUS_URL=https://dev-nexus-xxxxx.run.app
PATTERN_MINER_URL=https://pattern-miner-xxxxx.run.app
```

**In pattern-miner**:
```bash
DEV_NEXUS_URL=https://dev-nexus-xxxxx.run.app
ORCHESTRATOR_URL=https://dependency-orchestrator-xxxxx.run.app
```

### 4. Test Integration

```bash
# Test dev-nexus can reach orchestrator
curl -X POST $DEV_NEXUS_URL/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{"skill_id": "health_check_external", "input": {}}'

# Test orchestrator can reach dev-nexus
# (from orchestrator service account context)
curl -X POST $DEV_NEXUS_URL/a2a/execute \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  -H "Content-Type: application/json" \
  -d '{"skill_id": "get_repository_list", "input": {}}'
```

## Monitoring and Observability

### Health Checks

All services expose `/health` endpoints:

```bash
curl https://dev-nexus-xxxxx.run.app/health
curl https://dependency-orchestrator-xxxxx.run.app/health
curl https://pattern-miner-xxxxx.run.app/health
```

### AgentCards

Each service publishes its capabilities at `/.well-known/agent.json`:

```bash
curl https://dev-nexus-xxxxx.run.app/.well-known/agent.json
```

### Logging

All A2A interactions are logged to Cloud Logging:

```bash
gcloud logging read "resource.type=cloud_run_revision AND \
  resource.labels.service_name=dev-nexus AND \
  textPayload:\"A2A\"" \
  --limit 50 --format json
```

## Security Considerations

1. **Authentication**: All write operations require A2A authentication
2. **Authorization**: Use `ALLOWED_SERVICE_ACCOUNTS` to whitelist callers
3. **Network**: Cloud Run services use HTTPS by default
4. **Secrets**: Store tokens in Secret Manager, not environment variables
5. **Audit**: All A2A calls are logged with caller identity

## Troubleshooting

### Agent Not Reachable

```bash
# Check if service is healthy
curl https://service-url.run.app/health

# Check if AgentCard is published
curl https://service-url.run.app/.well-known/agent.json

# Verify environment variables
gcloud run services describe dev-nexus --region=us-central1 --format=json | jq '.spec.template.spec.containers[0].env'
```

### Authentication Failures

```bash
# Verify service account has permissions
gcloud run services get-iam-policy dev-nexus

# Test authentication manually
TOKEN=$(gcloud auth print-identity-token --impersonate-service-account=orchestrator-sa@project.iam.gserviceaccount.com)
curl -H "Authorization: Bearer $TOKEN" https://dev-nexus-xxxxx.run.app/a2a/execute \
  -d '{"skill_id": "add_lesson_learned", ...}'
```

### Coordination Failures

Check logs for coordination errors:

```bash
gcloud logging read "resource.type=cloud_run_revision AND \
  textPayload:\"coordination\" AND severity>=WARNING" \
  --limit 10
```

## Best Practices

1. **Idempotency**: Design skills to be idempotent (safe to retry)
2. **Timeouts**: Set reasonable timeouts (default 30s in A2AClient)
3. **Error Handling**: Always check for errors in responses
4. **Rate Limiting**: Respect Cloud Run quotas and limits
5. **Versioning**: Include version in AgentCard metadata
6. **Documentation**: Keep AgentCards up to date with skill changes

## Cost Optimization

- **Cloud Run**: Pay per request, set max instances to control costs
- **Secret Manager**: Minimal cost (~$0.06/month per secret)
- **Cloud Logging**: Set retention periods appropriately
- **Network Egress**: All services in same region to minimize egress

Typical monthly cost for 3 agents with moderate usage: **$10-20/month**

## Future Enhancements

- [ ] Add caching layer for frequently accessed patterns
- [ ] Implement async task execution for long-running operations
- [ ] Add webhook support for event-driven architecture
- [ ] Create SDKs for common languages (Python, TypeScript)
- [ ] Add observability dashboard showing agent interaction graph
- [ ] Implement circuit breakers for resilience

---

**Ready to integrate?** Start with dependency-orchestrator and pattern-miner setup, then configure dev-nexus with their endpoints!
