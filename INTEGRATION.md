# Integration Architecture

> How Dev-Nexus integrates with dependency-orchestrator and other AI agents

**Last Updated**: 2025-01-10
**Version**: 2.0

---

## Overview

Dev-Nexus acts as the **central pattern intelligence hub** in a distributed system of AI agents. It coordinates with other specialized agents to provide comprehensive project management, dependency tracking, and architectural consistency.

**Key Integration Partners:**
- **dependency-orchestrator**: Dependency management and impact analysis
- **pattern-miner**: Deep code analysis and pattern extraction
- Future agents: Testing coordinator, security scanner, etc.

---

## System Architecture

### High-Level Integration Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GitHub Repositories                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │  Repo A  │  │  Repo B  │  │  Repo C  │  │  Repo D  │          │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘          │
└───────┼─────────────┼─────────────┼─────────────┼─────────────────┘
        │             │             │             │
        │ (1) Push    │ (1) Push    │ (1) Push    │ (1) Push
        │   Events    │   Events    │   Events    │   Events
        ▼             ▼             ▼             ▼
   ┌────────────────────────────────────────────────────┐
   │          GitHub Actions Workflows                  │
   │  (Triggers pattern analysis on every commit)       │
   └────────────────┬───────────────────────────────────┘
                    │ (2) Calls Reusable Workflow
                    ▼
        ┌───────────────────────────┐
        │     DEV-NEXUS (Core)      │
        │  Pattern Discovery Agent  │
        │                           │
        │  ┌─────────────────────┐  │
        │  │ Pattern Analyzer    │  │ (3) Extract patterns
        │  │ - Claude AI         │  │     using LLM
        │  │ - Similarity Finder │  │
        │  └─────────────────────┘  │
        │           │                │
        │           ▼                │
        │  ┌─────────────────────┐  │
        │  │ Knowledge Base (v2) │  │ (4) Store patterns,
        │  │ - Patterns          │  │     dependencies,
        │  │ - Dependencies      │  │     deployment info
        │  │ - Lessons Learned   │  │
        │  └─────────────────────┘  │
        │           │                │
        │           ▼                │
        │  ┌─────────────────────┐  │
        │  │ A2A Server          │  │ (5) Expose via
        │  │ - 9 Skills          │  │     A2A protocol
        │  │ - AgentCard         │  │
        │  └─────────────────────┘  │
        └───────┬───────────────────┘
                │
                │ (6) Bidirectional A2A Communication
                │
    ┌───────────┴────────────┬────────────────────┐
    │                        │                     │
    ▼                        ▼                     ▼
┌─────────────────┐  ┌──────────────────┐  ┌─────────────┐
│ DEPENDENCY-     │  │ PATTERN-MINER    │  │ Future      │
│ ORCHESTRATOR    │  │                  │  │ Agents      │
│                 │  │                  │  │             │
│ ┌─────────────┐ │  │ ┌──────────────┐ │  │ - Testing   │
│ │ Triage      │ │  │ │ Deep Code    │ │  │ - Security  │
│ │ Engine      │ │  │ │ Analysis     │ │  │ - Deploy    │
│ └─────────────┘ │  │ └──────────────┘ │  └─────────────┘
│ ┌─────────────┐ │  │ ┌──────────────┐ │
│ │ Dependency  │ │  │ │ Comparison   │ │
│ │ Graph       │ │  │ │ Engine       │ │
│ └─────────────┘ │  │ └──────────────┘ │
│ ┌─────────────┐ │  └──────────────────┘
│ │ Impact      │ │
│ │ Analysis    │ │
│ └─────────────┘ │
└─────────────────┘

    │                        │
    │ (7) Notifications     │ (7) Insights
    ▼                        ▼
┌────────────────────────────────────┐
│   Notification Channels            │
│   - Discord/Slack Webhooks         │
│   - GitHub Issues/PRs              │
│   - Email Alerts                   │
└────────────────────────────────────┘
```

---

## Integration with dependency-orchestrator

### Purpose

The **dependency-orchestrator** manages dependency relationships and coordinates updates across repositories. It works in tandem with dev-nexus to provide:

- **Dependency tracking**: Who depends on what
- **Impact analysis**: What breaks if X changes
- **Update coordination**: Automated PR creation for dependents
- **AI triage**: Smart routing of dependency updates

### Communication Flow

```
┌──────────────────────────────────────────────────────────────────┐
│                    Integration Flow                              │
└──────────────────────────────────────────────────────────────────┘

Step 1: Pattern Change Detection
─────────────────────────────────
    ┌─────────────┐
    │  Repo A     │  Git push: "Update authentication pattern"
    │  (API lib)  │
    └──────┬──────┘
           │
           ▼
    ┌─────────────────┐
    │  Dev-Nexus      │  Extracts patterns, detects changes
    │                 │  Compares to previous patterns
    └──────┬──────────┘
           │
           │ (A) Notifies orchestrator
           ▼
    ┌─────────────────────┐
    │  dependency-        │  POST /a2a/execute
    │  orchestrator       │  skill: notify_pattern_change
    │                     │  {
    │  Receives:          │    "repository": "user/repo-a",
    │  - Repository       │    "patterns_changed": [...],
    │  - Changed patterns │    "severity": "major"
    │  - Severity         │  }
    └──────┬──────────────┘
           │
           │
Step 2: Impact Analysis
───────────────────────
           │
           │ (B) Queries dev-nexus for dependencies
           ▼
    ┌─────────────────┐
    │  Dev-Nexus      │  Returns dependency graph from KB:
    │                 │  {
    │  Responds:      │    "consumers": ["user/app-1", "user/app-2"],
    │  - Consumers    │    "affected_patterns": [...]
    │  - Patterns     │  }
    └──────┬──────────┘
           │
           ▼
    ┌─────────────────────┐
    │  dependency-        │  Analyzes impact:
    │  orchestrator       │  - App-1: Uses auth pattern (HIGH impact)
    │                     │  - App-2: Doesn't use auth (LOW impact)
    │  Impact Analysis:   │
    │  ✓ High: 1 repo     │
    │  ✓ Low:  1 repo     │
    └──────┬──────────────┘
           │
           │
Step 3: Triage & Action
───────────────────────
           │
           ▼
    ┌─────────────────────┐
    │  dependency-        │  Triage decisions:
    │  orchestrator       │  - App-1: Create PR (high impact)
    │                     │  - App-2: Add to backlog (low impact)
    │  AI Triage Agent:   │
    │  - Analyzes changes │
    │  - Determines urgency│
    │  - Creates PRs       │
    └──────┬──────────────┘
           │
           │ (C) Records lesson learned
           ▼
    ┌─────────────────┐
    │  Dev-Nexus      │  POST /a2a/execute
    │                 │  skill: add_lesson_learned
    │  Records:       │  {
    │  - Update result│    "repository": "user/repo-a",
    │  - Challenges   │    "lesson": "Auth update affected 1 consumer",
    │  - Learnings    │    "context": "Breaking change in v2.0"
    └─────────────────┘  }

           │
           ▼
    Outcome: Dependent repos updated, lessons captured
```

### Real-World Example

**Scenario**: You update authentication logic in your API library

```
Timeline:
─────────

10:00 AM - Developer pushes change to API library
           ┌─────────────────────────────────────┐
           │ Repo: user/api-library              │
           │ Change: Update JWT validation logic │
           │ Files: auth/jwt.py                  │
           └─────────────────────────────────────┘
                          │
                          ▼

10:01 AM - Dev-Nexus detects pattern change
           ┌─────────────────────────────────────────┐
           │ Pattern Change Detected:                │
           │ ✓ "JWT validation with refresh tokens" │
           │ ✓ Breaking change: Yes                  │
           │ ✓ Severity: High                        │
           └─────────────────────────────────────────┘
                          │
                          ▼

10:01 AM - Dev-Nexus notifies dependency-orchestrator
           ┌─────────────────────────────────────────┐
           │ POST to orchestrator:                   │
           │ {                                       │
           │   "event": "pattern_change",            │
           │   "repository": "user/api-library",     │
           │   "patterns": ["JWT validation"],       │
           │   "breaking": true                      │
           │ }                                       │
           └─────────────────────────────────────────┘
                          │
                          ▼

10:02 AM - dependency-orchestrator queries dev-nexus
           ┌─────────────────────────────────────────┐
           │ Orchestrator: "Who uses this pattern?" │
           │                                         │
           │ Dev-Nexus responds:                     │
           │ - user/mobile-app (HIGH impact)         │
           │ - user/web-dashboard (HIGH impact)      │
           │ - user/admin-panel (MEDIUM impact)      │
           └─────────────────────────────────────────┘
                          │
                          ▼

10:03 AM - AI Triage Agent analyzes
           ┌─────────────────────────────────────────┐
           │ Triage Results:                         │
           │                                         │
           │ mobile-app:                             │
           │   Impact: HIGH (auth is critical)       │
           │   Action: Create urgent PR              │
           │   Tests: Run integration tests          │
           │                                         │
           │ web-dashboard:                          │
           │   Impact: HIGH                          │
           │   Action: Create PR + notify team       │
           │                                         │
           │ admin-panel:                            │
           │   Impact: MEDIUM (rarely used)          │
           │   Action: Create PR, normal priority    │
           └─────────────────────────────────────────┘
                          │
                          ▼

10:05 AM - PRs created automatically
           ┌─────────────────────────────────────────┐
           │ GitHub PRs Created:                     │
           │                                         │
           │ PR #123: [URGENT] Update JWT validation│
           │   Repo: user/mobile-app                 │
           │   Labels: dependency-update, urgent     │
           │   Description: Breaking change from     │
           │   api-library v2.0...                   │
           │                                         │
           │ PR #124: Update JWT validation          │
           │   Repo: user/web-dashboard              │
           │   ... (similar)                         │
           └─────────────────────────────────────────┘
                          │
                          ▼

10:06 AM - Notifications sent
           ┌─────────────────────────────────────────┐
           │ Discord Notification:                   │
           │                                         │
           │ 🚨 Breaking Change Alert                │
           │                                         │
           │ Repository: user/api-library            │
           │ Change: JWT validation logic updated    │
           │                                         │
           │ Impact:                                 │
           │ • 2 repos need urgent updates           │
           │ • 1 repo needs normal update            │
           │                                         │
           │ PRs created automatically:              │
           │ • mobile-app: PR #123 (URGENT)          │
           │ • web-dashboard: PR #124                │
           │ • admin-panel: PR #125                  │
           └─────────────────────────────────────────┘

Result: Dependencies updated within minutes, not days!
```

---

## Integration with pattern-miner

### Purpose

The **pattern-miner** provides deep code analysis capabilities beyond dev-nexus's pattern extraction:

- **Code comparison**: Line-by-line comparison of similar patterns
- **Implementation recommendations**: Suggests best implementation
- **Pattern evolution tracking**: How patterns change over time
- **Anti-pattern detection**: Identifies problematic patterns

### Communication Flow

```
┌────────────────────────────────────────────────────────┐
│  Deep Analysis Request Flow                            │
└────────────────────────────────────────────────────────┘

    User/Dev-Nexus
         │
         │ (1) Requests deep analysis
         ▼
    ┌─────────────────┐
    │  pattern-miner  │  POST /a2a/execute
    │                 │  skill: compare_implementations
    │                 │  {
    │                 │    "pattern": "Retry logic",
    │                 │    "repositories": ["repo-a", "repo-b"]
    │                 │  }
    └──────┬──────────┘
           │
           │ (2) Fetches code from dev-nexus
           ▼
    ┌─────────────────┐
    │  Dev-Nexus      │  Returns file locations and metadata
    └──────┬──────────┘
           │
           │ (3) Performs deep analysis
           ▼
    ┌─────────────────────────────┐
    │  pattern-miner              │  Analysis results:
    │                             │  - Similarity score
    │  Compares:                  │  - Differences highlighted
    │  - Code structure           │  - Best practices found
    │  - Dependencies             │  - Recommendations
    │  - Performance implications │
    └──────┬──────────────────────┘
           │
           │ (4) Stores insights in dev-nexus
           ▼
    ┌─────────────────┐
    │  Dev-Nexus      │  Updates KB with mining insights
    │                 │  - Pattern quality scores
    │  Knowledge Base │  - Recommended implementations
    └─────────────────┘
```

---

## API-Level Integration

### Dev-Nexus exposes skills for external agents

```python
# Skills available for integration

PUBLIC SKILLS (No auth required):
─────────────────────────────────

1. query_patterns
   Purpose: Search patterns by keywords
   Used by: orchestrator (finding similar patterns)

2. get_deployment_info
   Purpose: Get deployment metadata
   Used by: orchestrator (understanding deployment context)

3. get_repository_list
   Purpose: List all tracked repos
   Used by: orchestrator (discovering repositories)

4. get_cross_repo_patterns
   Purpose: Find patterns across repos
   Used by: pattern-miner (pattern analysis)

5. health_check_external
   Purpose: Check external agent health
   Used by: orchestrator, pattern-miner (monitoring)

6. check_documentation_standards
   Purpose: Check doc conformity
   Used by: orchestrator (quality gates)

7. validate_documentation_update
   Purpose: Validate docs updated with code
   Used by: orchestrator (ensuring doc updates)


AUTHENTICATED SKILLS (Requires service account):
────────────────────────────────────────────────

8. add_lesson_learned
   Purpose: Record lessons learned
   Used by: orchestrator (capturing update outcomes)

9. update_dependency_info
   Purpose: Update dependency graphs
   Used by: orchestrator (maintaining dependency data)
```

### Integration Endpoints

```bash
# dependency-orchestrator calling dev-nexus

# 1. Query patterns to find dependents
curl -X POST https://dev-nexus.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "query_patterns",
    "input": {
      "keywords": ["authentication", "jwt"],
      "limit": 10
    }
  }'

# 2. Get dependency information
curl -X POST https://dev-nexus.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "get_repository_list",
    "input": {
      "include_metadata": true
    }
  }'

# 3. Record lesson after update (authenticated)
curl -X POST https://dev-nexus.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SERVICE_ACCOUNT_TOKEN" \
  -d '{
    "skill_id": "add_lesson_learned",
    "input": {
      "repository": "user/repo",
      "category": "dependency_update",
      "lesson": "Breaking change required 2 days for dependent updates",
      "context": "JWT validation change in v2.0",
      "severity": "warning"
    }
  }'
```

---

## Configuration

### Setting up integration with dependency-orchestrator

#### 1. Environment Variables (Dev-Nexus)

```bash
# In dev-nexus .env or Cloud Run environment

# dependency-orchestrator service
ORCHESTRATOR_URL=https://dependency-orchestrator-xyz.run.app
ORCHESTRATOR_TOKEN=<service-account-token>

# Allow orchestrator to call dev-nexus
ALLOWED_SERVICE_ACCOUNTS=orchestrator@project.iam.gserviceaccount.com
```

#### 2. Environment Variables (dependency-orchestrator)

```bash
# In dependency-orchestrator .env

# Dev-Nexus service
DEV_NEXUS_URL=https://dev-nexus-xyz.run.app
DEV_NEXUS_TOKEN=<service-account-token>
```

#### 3. Service Account Setup (GCP)

```bash
# Create service accounts for bidirectional auth

# Dev-Nexus service account
gcloud iam service-accounts create dev-nexus-sa \
  --display-name="Dev-Nexus A2A Service Account"

# dependency-orchestrator service account
gcloud iam service-accounts create orchestrator-sa \
  --display-name="Orchestrator A2A Service Account"

# Grant permissions (example for Cloud Run)
gcloud run services add-iam-policy-binding dev-nexus \
  --member="serviceAccount:orchestrator-sa@project.iam.gserviceaccount.com" \
  --role="roles/run.invoker"

gcloud run services add-iam-policy-binding dependency-orchestrator \
  --member="serviceAccount:dev-nexus-sa@project.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

#### 4. Testing Integration

```bash
# Test dev-nexus → orchestrator
curl -X POST $DEV_NEXUS_URL/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "health_check_external",
    "input": {
      "agent": "dependency_orchestrator"
    }
  }'

# Test orchestrator → dev-nexus
curl -X POST $ORCHESTRATOR_URL/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "query_dev_nexus_patterns",
    "input": {
      "keywords": ["test"]
    }
  }'
```

---

## Integration Patterns

### Pattern 1: Event-Driven Notification

**When**: Pattern changes are detected

```
Dev-Nexus                          dependency-orchestrator
    │                                      │
    │ 1. Pattern change detected           │
    │                                      │
    │ 2. POST /a2a/execute                 │
    ├─────────────────────────────────────>│
    │    skill: notify_pattern_change      │
    │                                      │
    │                                      │ 3. Process notification
    │                                      │    - Query dev-nexus
    │                                      │    - Analyze impact
    │                                      │    - Create PRs
    │                                      │
    │ 4. POST /a2a/execute                 │
    │<─────────────────────────────────────┤
    │    skill: add_lesson_learned         │
    │                                      │
    │ 5. 200 OK, lesson stored             │
    ├─────────────────────────────────────>│
```

### Pattern 2: Query-Response

**When**: External agent needs pattern information

```
External Agent                    Dev-Nexus
    │                                │
    │ 1. POST /a2a/execute           │
    ├───────────────────────────────>│
    │    skill: query_patterns       │
    │                                │
    │                                │ 2. Search KB
    │                                │    - Match keywords
    │                                │    - Score similarity
    │                                │
    │ 3. 200 OK {patterns: [...]}    │
    │<───────────────────────────────┤
    │                                │
    │ 4. Process results              │
```

### Pattern 3: Health Check & Monitoring

**When**: Ensuring system health

```
Dev-Nexus                    Orchestrator            Pattern-Miner
    │                            │                        │
    │ Periodic health checks     │                        │
    │───────────────────────────>│                        │
    │                            │                        │
    │                            │────────────────────────>│
    │                            │                        │
    │<───────────────────────────│                        │
    │  200 OK {status: healthy}  │                        │
    │                            │<────────────────────────│
    │                            │  200 OK {status: healthy}
    │                            │                        │
```

---

## Use Cases

### Use Case 1: Dependency Update Cascade

**Problem**: When you update a library, all dependents need updates

**Solution**: Automated coordination

```
1. Developer updates library A
2. Dev-Nexus detects pattern/API changes
3. Dev-Nexus notifies orchestrator
4. Orchestrator queries dev-nexus for consumers
5. Orchestrator creates PRs for all consumers
6. Orchestrator records results in dev-nexus
```

**Benefits**:
- Updates propagate in minutes, not days
- No manual tracking of dependents
- Lessons learned captured automatically

### Use Case 2: Pattern Consistency Enforcement

**Problem**: Similar patterns implemented differently across repos

**Solution**: Proactive detection and guidance

```
1. Dev-Nexus detects new pattern in Repo A
2. Dev-Nexus finds similar pattern in Repo B
3. Pattern-miner performs deep comparison
4. Differences highlighted to developer
5. Recommendation provided for consistency
6. Developer chooses to align or document divergence
```

### Use Case 3: Breaking Change Impact Analysis

**Problem**: Need to understand impact before making breaking changes

**Solution**: Pre-change analysis

```
1. Developer asks: "What breaks if I change X?"
2. Query orchestrator for dependency graph
3. Query dev-nexus for pattern usage
4. Pattern-miner analyzes code dependencies
5. Combined report shows:
   - Number of affected repos
   - Critical vs non-critical impacts
   - Effort estimate for updates
```

---

## Benefits of Integration

### For Dev-Nexus

1. **Enhanced Intelligence**: Deeper insights from pattern-miner
2. **Action Capability**: Orchestrator executes on insights
3. **Feedback Loop**: Learns from orchestrator's update outcomes
4. **Reduced Alerts**: Orchestrator handles routine updates automatically

### For dependency-orchestrator

1. **Pattern Awareness**: Understands architectural patterns
2. **Historical Context**: Access to lessons learned
3. **Similarity Detection**: Finds similar patterns for better decisions
4. **Deployment Context**: Knows deployment setups

### For Users

1. **Reduced Manual Work**: Automated dependency updates
2. **Faster Propagation**: Changes reach dependents quickly
3. **Better Decisions**: More context for changes
4. **Institutional Memory**: Captured lessons prevent repeat mistakes

---

## Monitoring Integration Health

### Metrics to Track

```yaml
Dev-Nexus → Orchestrator:
  - notification_sent_count: 150/day
  - notification_success_rate: 98%
  - avg_notification_latency: 245ms

Orchestrator → Dev-Nexus:
  - query_pattern_requests: 300/day
  - add_lesson_requests: 45/day
  - avg_response_time: 180ms

Health Checks:
  - dev_nexus_health: UP (99.9% uptime)
  - orchestrator_health: UP (99.8% uptime)
  - pattern_miner_health: UP (99.7% uptime)
```

### Monitoring Dashboard

```bash
# Check integration health
curl $DEV_NEXUS_URL/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "health_check_external",
    "input": {
      "agent": "dependency_orchestrator"
    }
  }' | jq

# Expected output:
{
  "success": true,
  "agent": "dependency_orchestrator",
  "status": "healthy",
  "url": "https://orchestrator.run.app",
  "response_time_ms": 145,
  "last_interaction": "2025-01-10T12:30:00Z"
}
```

---

## Troubleshooting Integration Issues

### Issue 1: Orchestrator not receiving notifications

**Symptoms**: Pattern changes don't trigger orchestrator

**Diagnosis**:
```bash
# Check ORCHESTRATOR_URL is set
echo $ORCHESTRATOR_URL

# Test connectivity
curl $ORCHESTRATOR_URL/health

# Check dev-nexus logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=dev-nexus" --limit 50
```

**Fix**:
- Verify ORCHESTRATOR_URL in environment
- Check service account permissions
- Verify network connectivity

### Issue 2: Authentication failures

**Symptoms**: 401 Unauthorized errors

**Diagnosis**:
```bash
# Verify service accounts
gcloud run services get-iam-policy dev-nexus

# Test auth token
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  $DEV_NEXUS_URL/health
```

**Fix**:
- Add service account to ALLOWED_SERVICE_ACCOUNTS
- Grant Cloud Run invoker role
- Regenerate service account tokens

### Issue 3: Slow response times

**Symptoms**: Integration calls timeout

**Diagnosis**:
- Check Cloud Run cold starts
- Monitor knowledge base size
- Review query complexity

**Fix**:
- Increase min instances (reduce cold starts)
- Optimize KB queries
- Add caching layer

---

## Future Integration Plans

### Planned Integrations

1. **Testing Coordinator Agent**
   - Triggers tests when patterns change
   - Validates breaking changes
   - Reports test coverage

2. **Security Scanner Agent**
   - Scans patterns for vulnerabilities
   - Suggests security improvements
   - Tracks compliance

3. **Performance Analyzer Agent**
   - Profiles pattern performance
   - Suggests optimizations
   - Tracks performance regressions

4. **Documentation Generator Agent**
   - Auto-generates docs from patterns
   - Updates API documentation
   - Creates migration guides

---

## See Also

- [README.md](README.md) - Main documentation
- [API.md](API.md) - API reference
- [EXTENDING_DEV_NEXUS.md](EXTENDING_DEV_NEXUS.md) - Adding integrations
- [dependency-orchestrator](https://github.com/patelmm79/dependency-orchestrator) - Orchestrator documentation

---

**Questions about integration?** Open an issue on [GitHub](https://github.com/patelmm79/dev-nexus/issues)

**Last Updated**: 2025-01-10
