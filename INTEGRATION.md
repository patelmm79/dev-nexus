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
- **agentic-log-attacker**: Production monitoring and runtime issue tracking
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

## Integration with agentic-log-attacker

### Purpose

The **agentic-log-attacker** monitors production GCP services and creates a **complete feedback loop** from development to production:

- **Runtime Monitoring**: Monitors 6 GCP services (Cloud Run, Functions, Build, GCE, GKE, App Engine)
- **Automated Issue Detection**: AI-powered log analysis using Gemini and LangGraph
- **Issue Reporting**: Creates GitHub issues and PRs with suggested fixes
- **Pattern Learning**: Reports production issues back to dev-nexus for pattern health tracking

### Complete Feedback Loop

```
┌────────────────────────────────────────────────────────────────────┐
│                    Development → Production Feedback Loop          │
└────────────────────────────────────────────────────────────────────┘

STAGE 1: DEVELOPMENT
────────────────────
    ┌─────────────┐
    │  Developer  │  Writes code using patterns
    │  Commits    │
    └──────┬──────┘
           │
           ▼
    ┌─────────────────┐
    │  Dev-Nexus      │  Extracts patterns, stores in KB
    │                 │  Notifies dependency-orchestrator
    └──────┬──────────┘
           │
           │
STAGE 2: DEPLOYMENT
───────────────────
           │
           ▼
    ┌─────────────────────┐
    │  Orchestrator       │  Coordinates updates
    │  Creates PRs        │  Updates dependents
    └──────┬──────────────┘
           │
           ▼
    ┌─────────────────┐
    │  CI/CD Pipeline │  Tests, builds, deploys
    │  (GitHub Actions)│
    └──────┬──────────┘
           │
           │
STAGE 3: PRODUCTION MONITORING
───────────────────────────────
           │
           ▼
    ┌─────────────────────────┐
    │  GCP Services           │
    │  - Cloud Run            │  Application runs in production
    │  - Cloud Functions      │
    │  - Cloud Build, etc.    │
    └──────┬──────────────────┘
           │
           │ Logs
           ▼
    ┌─────────────────────────┐
    │  Log-Attacker           │  Monitors logs 24/7
    │  (Gemini + LangGraph)   │  - Detects errors
    │                         │  - Analyzes patterns
    │  Detects:               │  - Identifies root cause
    │  • Errors               │  - Suggests fixes
    │  • Performance issues   │
    │  • Security problems    │
    └──────┬──────────────────┘
           │
           │
STAGE 4: FEEDBACK & LEARNING
─────────────────────────────
           │
           ├──────────────────> GitHub Issue Created
           │                    (With context & fix)
           │
           │ (A) Reports issue to dev-nexus
           ▼
    ┌─────────────────────────┐
    │  Dev-Nexus              │  POST /a2a/execute
    │                         │  skill: add_runtime_issue
    │  Records:               │  {
    │  - Issue type           │    "repository": "user/api-service",
    │  - Severity             │    "issue_type": "error",
    │  - Log snippet          │    "pattern_reference": "Redis caching",
    │  - Root cause           │    "severity": "high",
    │  - Suggested fix        │    "metrics": {...}
    │  - Pattern reference    │  }
    │  - Metrics              │
    └──────┬──────────────────┘
           │
           │ (B) Queries similar issues
           │
           │ Returns: "This issue seen 3x before in 2 repos"
           │
           ▼
    ┌─────────────────────────┐
    │  Pattern Health         │  Tracks pattern reliability:
    │  Tracking               │  - Redis caching: 85% health
    │                         │  - JWT validation: 95% health
    │  Knowledge Base         │  - API retry: 70% health
    │  Enhanced with:         │
    │  • Runtime issues       │
    │  • Production metrics   │
    │  • Pattern health       │
    └──────┬──────────────────┘
           │
           │ (C) Orchestrator uses health data
           ▼
    ┌─────────────────────────┐
    │  Orchestrator           │  Smart decisions based on health:
    │  Decision Engine        │  - Avoid patterns with issues
    │                         │  - Prioritize stable patterns
    │  "Redis caching has     │  - Warn before using risky patterns
    │   recent issues, use    │
    │   alternative pattern"  │
    └─────────────────────────┘
           │
           │ Feedback informs next development cycle
           └────────> Back to STAGE 1 (Developer)

Result: Institutional memory from production → development
```

### Three-Way Communication

Dev-Nexus now coordinates with **both** dependency-orchestrator and agentic-log-attacker:

```
         ┌─────────────────────────┐
         │      Dev-Nexus          │
         │  (Pattern Intelligence) │
         │                         │
         │  • Pattern discovery    │
         │  • Knowledge base       │
         │  • Runtime tracking     │
         └────────┬────────────────┘
                  │
    ┌─────────────┴─────────────┐
    │                           │
    │ (1) Pattern changes       │ (4) Runtime issues
    │ (2) Query dependencies    │ (5) Pattern health
    │ (3) Record lessons        │ (6) Similar issues
    │                           │
    ▼                           ▼
┌─────────────────────┐  ┌────────────────────────┐
│ Orchestrator        │  │  Log-Attacker          │
│                     │  │                        │
│ • Dependency mgmt   │  │  • GCP log monitoring  │
│ • Impact analysis   │  │  • Issue detection     │
│ • PR creation       │  │  • GitHub integration  │
│ • Update coord.     │  │  • Fix suggestions     │
└─────────────────────┘  └────────────────────────┘
```

### Real-World Scenario

**Scenario**: Redis connection pool exhaustion in production

```
Timeline:
─────────

12:00 PM - Production Error
           ┌────────────────────────────────────┐
           │ Cloud Run Service: api-service     │
           │ Error: "Redis connection pool      │
           │        exhausted after 45 retries" │
           │ Frequency: 150 errors/min          │
           └────────────────────────────────────┘
                          │
                          ▼

12:01 PM - Log-Attacker detects issue
           ┌────────────────────────────────────┐
           │ Log-Attacker Analysis:             │
           │                                    │
           │ Issue Type: Connection pool error  │
           │ Root Cause: Pool size (10) too     │
           │            small for traffic       │
           │ Pattern: "Redis session caching"   │
           │ Suggested Fix: Increase pool_size  │
           │               to 50, max_overflow   │
           │               to 20                 │
           └────────────────────────────────────┘
                          │
                          ▼

12:02 PM - Queries dev-nexus for similar issues
           ┌────────────────────────────────────┐
           │ POST /a2a/execute                  │
           │ skill: query_known_issues          │
           │ {                                  │
           │   "issue_type": "error",           │
           │   "pattern": "Redis session caching"│
           │ }                                  │
           │                                    │
           │ Response:                          │
           │ "Similar issues found: 3           │
           │  - user/web-app: same issue        │
           │  - user/mobile-backend: similar    │
           │  - user/admin-api: resolved"       │
           └────────────────────────────────────┘
                          │
                          ▼

12:03 PM - Creates GitHub issue with context
           ┌────────────────────────────────────┐
           │ GitHub Issue #234 Created:         │
           │                                    │
           │ Title: [PRODUCTION] Redis pool     │
           │        exhaustion in api-service   │
           │                                    │
           │ Description:                       │
           │ - Error details                    │
           │ - Root cause analysis              │
           │ - Suggested fix (from AI)          │
           │ - Historical context (3 similar)   │
           │ - Metrics (error rate, latency)    │
           │                                    │
           │ Labels: production, high, redis    │
           └────────────────────────────────────┘
                          │
                          ▼

12:04 PM - Reports to dev-nexus
           ┌────────────────────────────────────┐
           │ POST /a2a/execute                  │
           │ skill: add_runtime_issue           │
           │ {                                  │
           │   "repository": "user/api-service",│
           │   "service_type": "cloud_run",     │
           │   "issue_type": "error",           │
           │   "severity": "high",              │
           │   "pattern_reference":             │
           │     "Redis session caching",       │
           │   "github_issue_url":              │
           │     "github.com/.../issues/234",   │
           │   "metrics": {                     │
           │     "error_rate": 0.15,            │
           │     "latency_p95": 2500            │
           │   }                                │
           │ }                                  │
           └────────────────────────────────────┘
                          │
                          ▼

12:05 PM - Dev-Nexus updates pattern health
           ┌────────────────────────────────────┐
           │ Pattern Health Updated:            │
           │                                    │
           │ "Redis session caching"            │
           │ Previous health: 95%               │
           │ New health: 85%                    │
           │                                    │
           │ Repositories affected: 1           │
           │ Total repositories using: 4        │
           │                                    │
           │ Recommendation:                    │
           │ "Review pool configuration in      │
           │  all services using this pattern"  │
           └────────────────────────────────────┘
                          │
                          ▼

12:10 PM - Orchestrator queries pattern health
           ┌────────────────────────────────────┐
           │ Orchestrator planning Redis update │
           │ for another service...             │
           │                                    │
           │ Queries dev-nexus:                 │
           │ POST /a2a/execute                  │
           │ skill: get_pattern_health          │
           │ {"pattern": "Redis session caching"}│
           │                                    │
           │ Response shows 85% health          │
           │                                    │
           │ Decision: Include pool size review │
           │          in all Redis updates      │
           └────────────────────────────────────┘

Result: Production issue → Pattern learning → Prevents future issues
```

### Integration Code

Dev-Nexus provides **3 new skills** for log-attacker integration:

```python
1. add_runtime_issue (Authenticated)
   - Records production issues from logs
   - Links issues to patterns
   - Tracks metrics (error rate, latency, etc.)
   - Returns similar historical issues

2. query_known_issues (Public)
   - Search for previously seen issues
   - Filter by pattern, severity, service type
   - Helps log-attacker add context to new issues

3. get_pattern_health (Public)
   - Calculates health score (0-1) for patterns
   - Shows which repos have issues
   - Provides recommendations
```

**Example Integration** (from log-attacker):

```python
from examples.log_attacker_integration import DevNexusIntegration

integration = DevNexusIntegration(
    dev_nexus_url=os.getenv("DEV_NEXUS_URL"),
    token=os.getenv("DEV_NEXUS_TOKEN")
)

# Report runtime issue
await integration.report_runtime_issue(
    repository="user/api-service",
    service_type="cloud_run",
    issue_type="error",
    severity="high",
    log_snippet="Redis connection pool exhausted",
    root_cause="Pool size too small",
    suggested_fix="Increase pool_size to 50",
    pattern_reference="Redis session caching",
    github_issue_url="https://github.com/.../issues/234",
    metrics={"error_rate": 0.15, "latency_p95": 2500}
)

# Check pattern health before deployment
health = await integration.get_pattern_health(
    pattern_name="Redis session caching"
)
# Returns: {"health_score": 0.85, "recommendation": "Review pool config"}
```

### Benefits

**For Dev-Nexus:**
- Real production data enhances pattern intelligence
- Pattern health tracking prevents bad patterns from spreading
- Complete feedback loop from code to production

**For Log-Attacker:**
- Historical context enriches issue reports
- Pattern recognition improves root cause analysis
- Cross-repository learning (avoid mistakes others made)

**For Orchestrator:**
- Health data informs dependency update decisions
- Avoids propagating problematic patterns
- Prioritizes updates based on production stability

**For Developers:**
- Issues come with historical context and solutions
- Learn from production failures across all repos
- Proactive warnings about pattern problems

### Detailed Documentation

See [INTEGRATION_LOG_ATTACKER.md](INTEGRATION_LOG_ATTACKER.md) for:
- Complete integration assessment (⭐⭐⭐⭐⭐ rating)
- 3-phase implementation plan (3 weeks)
- Enhanced knowledge base schema
- 3 detailed scenarios with timelines
- Configuration and deployment guides

### Implementation Status

**Phase 1: Core Integration** ✅ COMPLETE
- `add_runtime_issue` skill
- `query_known_issues` skill
- `get_pattern_health` skill
- Runtime issue tracking in KB
- Integration client code examples

**Phase 2: Smart Correlation** (Week 2)
- Pattern-runtime correlation
- Historical data integration
- Trend analysis

**Phase 3: Proactive Monitoring** (Week 3)
- Deployment notifications
- Enhanced monitoring after deploys
- Automated health checks

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

The following agents are planned for future integration, extending dev-nexus's capabilities across testing, security, performance, and documentation domains.

---

### 1. Testing Coordinator Agent

**Status**: 📋 Planned
**Timeline**: Q2 2025
**Complexity**: Medium

#### Purpose

Automates testing orchestration across repositories when patterns change, ensuring breaking changes are caught before reaching production.

**Core Capabilities**:
- Triggers targeted test suites when patterns are modified
- Validates breaking changes across dependent repositories
- Reports test coverage for pattern implementations
- Coordinates cross-repository integration tests
- Generates test recommendations based on pattern complexity

#### Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Testing Coordinator Flow                   │
└─────────────────────────────────────────────────────────┘

Step 1: Pattern Change Detection
─────────────────────────────────
    Dev-Nexus detects pattern change
           │
           │ (A) Notifies Testing Coordinator
           ▼
    ┌──────────────────────┐
    │ Testing Coordinator  │  Receives notification:
    │                      │  - Repository
    │ Analyzes:            │  - Pattern changed
    │ - Pattern type       │  - Change type (major/minor)
    │ - Affected repos     │  - Test requirements
    └──────┬───────────────┘
           │
           │
Step 2: Test Planning
──────────────────────
           │ (B) Queries dev-nexus for dependents
           ▼
    ┌──────────────────────┐
    │ Dev-Nexus            │  Returns:
    │                      │  - Dependent repos
    │ Provides:            │  - Pattern usage details
    │ - Consumer list      │  - Previous test results
    │ - Pattern details    │
    └──────┬───────────────┘
           │
           ▼
    ┌──────────────────────┐
    │ Testing Coordinator  │  Creates test plan:
    │                      │
    │ Test Plan:           │  Repo A (source):
    │ - Unit tests         │    ✓ Unit tests for pattern
    │ - Integration tests  │    ✓ Integration tests
    │ - E2E tests          │
    └──────┬───────────────┘  Repo B (consumer):
           │                    ✓ Integration tests
           │                    ✓ Contract tests
           │
Step 3: Test Execution
──────────────────────
           │ (C) Triggers GitHub Actions workflows
           ▼
    ┌─────────────────────────────────┐
    │ GitHub Actions (Parallel)       │
    │                                 │
    │ Repo A:                         │
    │   → pytest --pattern=auth       │
    │   → pytest --integration        │
    │                                 │
    │ Repo B:                         │
    │   → npm test -- --pattern=auth  │
    │   → cypress run --spec=auth     │
    └──────┬──────────────────────────┘
           │
           │ (D) Collects results
           ▼
    ┌──────────────────────┐
    │ Testing Coordinator  │  Aggregates results:
    │                      │
    │ Results:             │  Repo A: ✅ 45/45 passed
    │ - Pass/fail status   │  Repo B: ❌ 3/50 failed
    │ - Coverage delta     │
    │ - Failed tests       │  Coverage: 85% → 82%
    └──────┬───────────────┘
           │
           │
Step 4: Report & Act
────────────────────
           │ (E) Reports to dev-nexus
           ▼
    ┌──────────────────────┐
    │ Dev-Nexus            │  POST /a2a/execute
    │                      │  skill: add_test_results
    │ Records:             │
    │ - Test outcomes      │  Creates GitHub issue if
    │ - Coverage data      │  tests fail in dependents
    │ - Failure details    │
    └──────────────────────┘
           │
           │ (F) Notifies via webhook
           ▼
    Developer receives notification with test report
```

#### A2A Skills

**Exposed by Testing Coordinator**:
```python
1. trigger_pattern_tests (Authenticated)
   Input: {repository, pattern_name, test_scope}
   Output: {test_run_id, status, estimated_duration}

2. get_test_results (Public)
   Input: {test_run_id}
   Output: {status, passed, failed, coverage, duration}

3. get_test_coverage (Public)
   Input: {repository, pattern_name}
   Output: {coverage_percentage, uncovered_lines, recommendations}
```

**Consumed from Dev-Nexus**:
```python
1. get_repository_list - Find all repos
2. query_patterns - Find pattern implementations
3. add_test_results (new) - Report test outcomes
```

#### Real-World Scenario

**Scenario**: Authentication pattern updated in shared library

```
Timeline:
─────────

09:00 AM - Developer updates auth pattern
           Pattern: "JWT with refresh tokens"
           Change: Add token rotation logic

09:01 AM - Dev-Nexus detects change
           → Notifies Testing Coordinator

09:02 AM - Testing Coordinator creates test plan
           Source repo: auth-library
           Dependent repos:
             - mobile-app (critical)
             - web-dashboard (critical)
             - admin-panel (medium)
             - analytics-service (low)

09:03 AM - Triggers parallel test runs
           ✅ auth-library: 120/120 tests pass
           ✅ mobile-app: 85/85 tests pass
           ❌ web-dashboard: 3/92 tests fail
           ✅ admin-panel: 45/45 tests pass
           ✅ analytics-service: 30/30 tests pass

09:15 AM - Creates GitHub issue
           Title: [TEST FAILURE] Auth pattern update breaks web-dashboard
           Labels: breaking-change, test-failure, urgent

           Description:
           Auth pattern change in auth-library causes 3 test failures:
           - test_token_refresh_flow (timeout)
           - test_logout_with_rotation (assertion)
           - test_concurrent_requests (race condition)

           Impact: HIGH (critical service)
           Action: Fix required before merge

09:20 AM - Developer fixes issues in web-dashboard

09:45 AM - Re-runs tests
           ✅ All 92 tests pass

09:50 AM - Testing Coordinator updates dev-nexus
           Pattern change validated ✓
           All dependents passing ✓

Result: Breaking change caught before production
```

#### Benefits

**For Developers**:
- Automated test execution across repositories
- Early detection of breaking changes
- Clear test failure reports with context

**For Dev-Nexus**:
- Test coverage data enhances pattern quality scores
- Historical test data improves recommendations
- Validates pattern changes before propagation

**For Organizations**:
- Reduced production incidents from untested changes
- Faster feedback loops (minutes vs hours)
- Confidence in cross-repository refactoring

#### Implementation Plan

**Phase 1** (2 weeks):
- Basic test triggering via GitHub Actions
- Test result aggregation
- dev-nexus integration for result storage

**Phase 2** (2 weeks):
- Smart test selection (only affected tests)
- Coverage tracking and reporting
- Parallel test execution optimization

**Phase 3** (1 week):
- Test recommendations based on pattern complexity
- Historical test data analysis
- Integration with CI/CD pipelines

---

### 2. Security Scanner Agent

**Status**: 📋 Planned
**Timeline**: Q3 2025
**Complexity**: High

#### Purpose

Continuously scans patterns for security vulnerabilities, ensuring consistent security posture across all repositories using dev-nexus.

**Core Capabilities**:
- Scans patterns for OWASP Top 10 vulnerabilities
- Detects insecure pattern implementations
- Tracks security compliance (SOC2, PCI-DSS, HIPAA)
- Suggests security improvements and alternatives
- Monitors for newly disclosed CVEs affecting patterns

#### Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Security Scanner Flow                      │
└─────────────────────────────────────────────────────────┘

Pattern Security Analysis
─────────────────────────
    Dev-Nexus detects new/updated pattern
           │
           │ (A) Triggers security scan
           ▼
    ┌──────────────────────┐
    │ Security Scanner     │  Analyzes:
    │                      │  - SQL injection risks
    │ Scans for:           │  - XSS vulnerabilities
    │ - Code vulnerabilities│ - Auth/authz issues
    │ - Dependency CVEs    │  - Secrets exposure
    │ - Config issues      │  - CSRF protection
    │ - Compliance gaps    │  - Data validation
    └──────┬───────────────┘
           │
           │ Uses: Semgrep, Bandit, npm audit
           │
           ▼
    ┌──────────────────────┐
    │ Vulnerability DB     │  Checks against:
    │                      │  - NVD database
    │ Cross-references:    │  - GitHub advisories
    │ - Known CVEs         │  - OWASP patterns
    │ - Security patterns  │  - Custom rules
    └──────┬───────────────┘
           │
           │
Severity Assessment
───────────────────
           │
           ▼
    ┌──────────────────────┐
    │ Security Scanner     │  Risk scoring:
    │                      │
    │ Calculates:          │  🔴 Critical: SQL injection
    │ - Severity (0-10)    │     in auth pattern
    │ - Exploitability     │  🟡 Medium: Weak crypto
    │ - Impact scope       │     in encryption util
    │ - CVSS score         │  🟢 Low: Outdated comment
    └──────┬───────────────┘
           │
           │
Reporting & Action
──────────────────
           │ (B) Reports to dev-nexus
           ▼
    ┌──────────────────────┐
    │ Dev-Nexus            │  POST /a2a/execute
    │                      │  skill: add_security_finding
    │ Records:             │
    │ - Vulnerability type │  Updates pattern metadata:
    │ - Severity           │  - Security score: 85/100
    │ - Affected repos     │  - Vulnerabilities: 2 medium
    │ - Remediation        │  - Compliance: ⚠️ Review
    └──────┬───────────────┘
           │
           │ (C) Notifies high severity
           ▼
    Creates security advisory + GitHub issue
    Blocks PR merge if critical findings
```

#### A2A Skills

**Exposed by Security Scanner**:
```python
1. scan_pattern_security (Authenticated)
   Input: {repository, pattern_name, scan_depth}
   Output: {scan_id, findings_count, severity_breakdown}

2. get_security_score (Public)
   Input: {repository, pattern_name}
   Output: {score, vulnerabilities, compliance_status}

3. check_compliance (Public)
   Input: {repository, standards: ["SOC2", "PCI-DSS"]}
   Output: {compliant, gaps, recommendations}

4. get_remediation_guidance (Public)
   Input: {vulnerability_id}
   Output: {description, fix_steps, code_examples}
```

**Consumed from Dev-Nexus**:
```python
1. query_patterns - Find patterns to scan
2. get_cross_repo_patterns - Scan across repos
3. add_security_finding (new) - Report vulnerabilities
4. update_pattern_metadata (new) - Update security scores
```

#### Real-World Scenario

**Scenario**: SQL injection vulnerability in ORM pattern

```
Timeline:
─────────

10:00 AM - Security Scanner runs daily scan
           Scanning 45 patterns across 12 repositories

10:15 AM - Critical finding detected
           Pattern: "Dynamic query builder"
           Issue: SQL injection via string concatenation
           Severity: CRITICAL (CVSS 9.8)

           Vulnerable code:
           def get_user(username):
               query = f"SELECT * FROM users WHERE name = '{username}'"
               return db.execute(query)

           Affected repositories:
           - api-service (HIGH risk - public endpoint)
           - admin-backend (MEDIUM risk - internal)
           - reporting-tool (LOW risk - limited access)

10:16 AM - Security Scanner reports to dev-nexus
           POST /a2a/execute
           skill: add_security_finding

10:17 AM - Dev-Nexus updates pattern
           Pattern security score: 95 → 35
           Status: ⚠️ SECURITY ISSUE - DO NOT USE

10:18 AM - Creates security advisory
           GitHub Security Advisory created
           Title: [CRITICAL] SQL Injection in Dynamic Query Pattern
           CVE requested

10:20 AM - Notifies all affected teams
           Slack/Discord notification:
           🚨 CRITICAL SECURITY ISSUE
           Pattern: Dynamic query builder
           Issue: SQL injection vulnerability
           Affected: 3 repositories
           Action: Immediate remediation required

10:30 AM - dependency-orchestrator queries health
           Orchestrator planning to use this pattern...
           Queries: get_pattern_health("Dynamic query builder")
           Response: health_score: 0.35, security_critical: true
           Decision: ❌ Block usage, suggest alternative

11:00 AM - Developers apply fixes
           Remediation:
           def get_user(username):
               query = "SELECT * FROM users WHERE name = ?"
               return db.execute(query, [username])

11:30 AM - Re-scan confirms fix
           ✅ Vulnerability resolved
           Pattern security score: 35 → 95

12:00 PM - Dev-Nexus updates pattern status
           Status: ✅ SECURE
           Note: "Fixed SQL injection, uses parameterized queries"

Result: Critical vulnerability fixed within 2 hours across all repos
```

#### Benefits

**For Security Teams**:
- Automated vulnerability scanning across all patterns
- Centralized security posture visibility
- Compliance tracking and reporting

**For Developers**:
- Security guidance at pattern adoption time
- Clear remediation steps for vulnerabilities
- Prevents insecure patterns from spreading

**For Dev-Nexus**:
- Security scores enhance pattern recommendations
- Blocks problematic patterns from propagation
- Historical vulnerability data improves prevention

#### Implementation Plan

**Phase 1** (3 weeks):
- Basic static analysis integration (Semgrep, Bandit)
- Vulnerability detection and scoring
- dev-nexus integration for finding storage

**Phase 2** (3 weeks):
- Dependency CVE scanning
- Compliance checking (OWASP, CWE)
- Automated remediation suggestions

**Phase 3** (2 weeks):
- Security advisory creation
- Integration with GitHub Security
- Pattern blocking for critical findings

---

### 3. Performance Analyzer Agent

**Status**: 📋 Planned
**Timeline**: Q4 2025
**Complexity**: High

#### Purpose

Profiles pattern performance across repositories, identifying performance regressions and optimization opportunities.

**Core Capabilities**:
- Profiles pattern performance (CPU, memory, latency)
- Detects performance regressions in pattern updates
- Suggests optimizations based on profiling data
- Tracks performance metrics over time
- Compares pattern implementations for efficiency

#### Architecture

```
┌─────────────────────────────────────────────────────────┐
│            Performance Analyzer Flow                    │
└─────────────────────────────────────────────────────────┘

Continuous Profiling
────────────────────
    Production services (with profiling enabled)
           │
           │ Profiling data: traces, metrics, logs
           ▼
    ┌──────────────────────┐
    │ Performance Analyzer │  Collects:
    │                      │  - CPU profiles
    │ Ingests:             │  - Memory usage
    │ - GCP Cloud Trace    │  - Request latency
    │ - Cloud Profiler     │  - DB query times
    │ - Cloud Monitoring   │  - Cache hit rates
    └──────┬───────────────┘
           │
           │
Pattern Attribution
───────────────────
           │ (A) Queries dev-nexus for pattern mapping
           ▼
    ┌──────────────────────┐
    │ Dev-Nexus            │  Returns:
    │                      │  - Pattern implementations
    │ Provides:            │  - File locations
    │ - Pattern → code map │  - Pattern metadata
    └──────┬───────────────┘
           │
           ▼
    ┌──────────────────────┐
    │ Performance Analyzer │  Maps metrics to patterns:
    │                      │
    │ Pattern: Redis cache │  Pattern: JWT validation
    │ - Avg latency: 5ms   │  - Avg latency: 120ms ⚠️
    │ - Cache hits: 95%    │  - CPU usage: 15%
    │ - Memory: 50MB       │  - Calls: 10K/min
    └──────┬───────────────┘
           │
           │
Regression Detection
────────────────────
           │
           ▼
    ┌──────────────────────┐
    │ Performance Analyzer │  Analyzes trends:
    │                      │
    │ Detects:             │  v1.0: 50ms latency
    │ - Latency increases  │  v1.1: 55ms (+10%) ⚠️
    │ - Memory leaks       │  v1.2: 85ms (+70%) 🚨
    │ - CPU spikes         │
    │ - Throughput drops   │  REGRESSION DETECTED
    └──────┬───────────────┘
           │
           │
Optimization Suggestions
────────────────────────
           │ (B) Reports to dev-nexus
           ▼
    ┌──────────────────────┐
    │ Dev-Nexus            │  POST /a2a/execute
    │                      │  skill: add_performance_data
    │ Updates:             │
    │ - Pattern perf data  │  JWT validation:
    │ - Optimization tips  │  ⚠️ Performance regression
    │ - Efficiency scores  │  Recommendation: Cache decoded tokens
    └──────┬───────────────┘
           │
           │ (C) Creates issue if regression
           ▼
    GitHub issue with performance report
    Includes: profile data, comparison, suggestions
```

#### A2A Skills

**Exposed by Performance Analyzer**:
```python
1. profile_pattern (Authenticated)
   Input: {repository, pattern_name, duration_minutes}
   Output: {profile_id, metrics, baseline_comparison}

2. get_performance_data (Public)
   Input: {repository, pattern_name, time_range}
   Output: {latency_p50, latency_p95, latency_p99, cpu, memory}

3. compare_implementations (Public)
   Input: {pattern_name, repositories: []}
   Output: {comparison, fastest, recommendations}

4. detect_regressions (Public)
   Input: {repository, pattern_name, threshold_percent}
   Output: {has_regression, current_vs_baseline, severity}
```

**Consumed from Dev-Nexus**:
```python
1. query_patterns - Find patterns to profile
2. get_cross_repo_patterns - Compare across repos
3. add_performance_data (new) - Report profiling data
4. update_pattern_metadata (new) - Update performance scores
```

#### Real-World Scenario

**Scenario**: JWT validation performance regression

```
Timeline:
─────────

02:00 PM - v2.0 of auth-library deployed
           Pattern: JWT validation updated

02:30 PM - Performance Analyzer detects anomaly
           Service: api-service
           Endpoint: /api/v1/protected/*
           Latency P95: 50ms → 250ms (400% increase) 🚨

02:31 PM - Attributes to JWT validation pattern
           Root cause analysis:
           - New token rotation adds extra validation
           - Each request validates twice (old + new)
           - No caching of decoded tokens

02:32 PM - Reports to dev-nexus
           Pattern performance regression detected
           Severity: HIGH
           Impact: All services using JWT validation (8 repos)

02:35 PM - Creates GitHub issue
           Title: [PERF] JWT validation 400% slower in v2.0

           Performance comparison:
           v1.9: 50ms P95, 5% CPU
           v2.0: 250ms P95, 18% CPU

           Profile data:
           - Token decode: 30ms (was 15ms)
           - Signature verify: 180ms (was 30ms) ⚠️
           - Claims validation: 40ms (was 5ms)

           Optimization suggestions:
           1. Cache decoded tokens (TTL: token expiry)
           2. Verify signature once, not twice
           3. Batch claims validation

           Expected improvement: 250ms → 60ms

02:45 PM - Orchestrator queries pattern health
           Planning to update mobile-app to v2.0...
           Queries: get_pattern_health("JWT validation")
           Response:
           {
             "health_score": 0.45,
             "performance_regression": true,
             "recommendation": "Wait for v2.1 with perf fixes"
           }
           Decision: ❌ Delay update

03:30 PM - Developer implements optimizations
           Added token caching with Redis
           Reduced signature verifications

04:00 PM - v2.1 deployed with fixes

04:30 PM - Performance Analyzer re-profiles
           Latency P95: 250ms → 45ms (10% better than v1.9!) ✅
           CPU: 18% → 4%
           Memory: Stable

04:35 PM - Updates dev-nexus
           Pattern health score: 0.45 → 0.98
           Status: ✅ OPTIMIZED
           Note: "v2.1 adds caching, 10% faster than v1.9"

04:40 PM - Orchestrator proceeds with updates
           All 8 dependent repos updated to v2.1
           Overall API latency improved 10%

Result: Performance regression caught and fixed, overall improvement
```

#### Benefits

**For Performance Engineers**:
- Automated performance regression detection
- Pattern-level profiling across repositories
- Clear optimization recommendations

**For Developers**:
- Performance data at pattern adoption time
- Avoid slow patterns before they spread
- Optimization guidance with profiling data

**For Dev-Nexus**:
- Performance scores enhance recommendations
- Historical data shows pattern evolution
- Enables performance-aware dependency updates

#### Implementation Plan

**Phase 1** (3 weeks):
- GCP profiling integration (Cloud Trace, Profiler)
- Pattern attribution from profiling data
- Basic regression detection

**Phase 2** (3 weeks):
- Automated optimization suggestions using AI
- Cross-repository performance comparison
- Performance score calculation

**Phase 3** (2 weeks):
- Predictive performance modeling
- Load test automation
- Integration with dev-nexus pattern scoring

---

### 4. Documentation Generator Agent

**Status**: 📋 Planned
**Timeline**: Q1 2026
**Complexity**: Medium

#### Purpose

Automatically generates and maintains documentation from patterns, keeping docs synchronized with code changes.

**Core Capabilities**:
- Auto-generates pattern documentation from code
- Updates API documentation when patterns change
- Creates migration guides for breaking changes
- Generates architecture diagrams from pattern relationships
- Maintains changelog for pattern evolution

#### Architecture

```
┌─────────────────────────────────────────────────────────┐
│          Documentation Generator Flow                   │
└─────────────────────────────────────────────────────────┘

Documentation Generation
────────────────────────
    Dev-Nexus detects pattern change
           │
           │ (A) Triggers doc generation
           ▼
    ┌──────────────────────┐
    │ Documentation        │  Analyzes:
    │ Generator            │  - Code structure
    │                      │  - Function signatures
    │ Extracts:            │  - Type definitions
    │ - Docstrings         │  - Usage examples
    │ - Type hints         │  - Test cases
    │ - Function sigs      │
    └──────┬───────────────┘
           │
           │ Uses: Claude API for intelligent summarization
           │
           ▼
    ┌──────────────────────┐
    │ AI Documentation     │  Generates:
    │ Writer (Claude)      │
    │ Creates:             │  ## JWT Validation Pattern
    │ - Overview section   │
    │ - Usage examples     │  Validates JWT tokens with...
    │ - API reference      │
    │ - Best practices     │  ### Usage
    │ - Common pitfalls    │  ```python
    └──────┬───────────────┘  validate_token(token)
           │                  ```
           │
           │
Change Detection & Migration
────────────────────────────
           │ (B) Compares versions
           ▼
    ┌──────────────────────┐
    │ Documentation        │  Detects changes:
    │ Generator            │
    │ Compares:            │  v1.9 → v2.0:
    │ - Previous version   │  + Added token_rotation
    │ - Current version    │  - Removed legacy_mode
    │ - Breaking changes   │  ⚠️ signature_verify() API changed
    └──────┬───────────────┘
           │
           │ (C) Generates migration guide
           ▼
    ┌──────────────────────┐
    │ AI Documentation     │  Creates migration guide:
    │ Writer (Claude)      │
    │ Generates:           │  # Migrating from v1.9 to v2.0
    │ - What changed       │
    │ - Why it changed     │  ## Breaking Changes
    │ - How to migrate     │  `signature_verify()` now requires...
    │ - Code examples      │
    └──────┬───────────────┘  ## Migration Steps
           │                  1. Update function calls...
           │
           │
Documentation Update
────────────────────
           │ (D) Creates PR with docs
           ▼
    ┌──────────────────────┐
    │ GitHub PR            │  Auto-created PR:
    │                      │
    │ Title: Update docs   │  Files changed:
    │ for JWT pattern v2.0 │  - docs/patterns/jwt.md
    │                      │  - CHANGELOG.md
    │ Changes:             │  - MIGRATION_v1.9_to_v2.0.md
    │ ✓ Pattern docs       │
    │ ✓ Migration guide    │  Auto-assigned to pattern owner
    │ ✓ Changelog          │  Labels: documentation, automated
    └──────┬───────────────┘
           │
           │ (E) Reports to dev-nexus
           ▼
    ┌──────────────────────┐
    │ Dev-Nexus            │  Records documentation update:
    │                      │  - PR URL
    │ Updates metadata:    │  - Generated docs
    │ - Documentation URL  │  - Last updated
    │ - Changelog          │  - Doc completeness: 95%
    └──────────────────────┘
```

#### A2A Skills

**Exposed by Documentation Generator**:
```python
1. generate_pattern_docs (Authenticated)
   Input: {repository, pattern_name, doc_type}
   Output: {documentation_markdown, pr_url}

2. create_migration_guide (Authenticated)
   Input: {pattern_name, from_version, to_version}
   Output: {migration_guide_markdown, breaking_changes}

3. generate_architecture_diagram (Public)
   Input: {repositories, show_dependencies}
   Output: {diagram_url, mermaid_code}

4. check_doc_completeness (Public)
   Input: {repository, pattern_name}
   Output: {score, missing_sections, suggestions}
```

**Consumed from Dev-Nexus**:
```python
1. query_patterns - Find patterns to document
2. get_repository_list - Get all repos
3. update_pattern_metadata (new) - Update doc URLs
4. get_pattern_history (new) - Get version history for migration guides
```

#### Real-World Scenario

**Scenario**: OAuth2 pattern updated, docs auto-generated

```
Timeline:
─────────

09:00 AM - Developer updates OAuth2 pattern
           Pattern: OAuth2 authentication flow
           Changes: Add PKCE support (RFC 7636)
           Files: auth/oauth2.py, auth/pkce.py (new)

09:01 AM - Dev-Nexus detects pattern change
           Breaking change: Yes
           New files: 1
           Modified files: 1

09:02 AM - Triggers Documentation Generator
           Pattern: OAuth2 authentication flow
           Version: v3.5 → v4.0
           Generate: Full docs + migration guide

09:03 AM - Documentation Generator analyzes code
           Extracted:
           - 3 new functions (generate_code_verifier, etc.)
           - 2 modified functions (authorize_url, exchange_code)
           - 15 docstrings
           - 8 type hints
           - 12 test cases

09:04 AM - Claude API generates documentation
           Created sections:
           ✓ Overview (what PKCE is, why it's needed)
           ✓ Quick Start (5-minute example)
           ✓ API Reference (all 5 functions)
           ✓ Configuration (environment variables)
           ✓ Security Best Practices
           ✓ Troubleshooting (common issues)

09:06 AM - Generates migration guide
           Detected breaking changes:
           - authorize_url() now requires code_challenge
           - State parameter now mandatory
           - Callback must verify code_verifier

           Created migration guide:
           # Migrating to OAuth2 v4.0 with PKCE

           ## Why Upgrade
           PKCE (RFC 7636) prevents authorization code
           interception attacks...

           ## Breaking Changes
           1. authorize_url() signature changed
           2. New required parameter: code_challenge

           ## Step-by-Step Migration
           ```python
           # Before (v3.5)
           url = authorize_url(client_id, redirect_uri)

           # After (v4.0)
           verifier = generate_code_verifier()
           challenge = generate_code_challenge(verifier)
           url = authorize_url(client_id, redirect_uri, challenge)
           ```

09:08 AM - Generates architecture diagram
           Created Mermaid diagram showing:
           - OAuth2 flow with PKCE
           - Client → Auth Server → Resource Server
           - Code verifier/challenge flow

09:10 AM - Creates PR with documentation
           PR #456: Update OAuth2 pattern documentation for v4.0

           Files changed:
           + docs/patterns/oauth2.md (comprehensive docs)
           + MIGRATION_v3.5_to_v4.0.md (step-by-step guide)
           + CHANGELOG.md (updated with v4.0 changes)
           + docs/diagrams/oauth2_pkce_flow.mmd (architecture)

           Assigned to: @oauth-team
           Labels: documentation, oauth2, breaking-change

09:15 AM - Reports to dev-nexus
           POST /a2a/execute
           skill: update_pattern_metadata

           Updated:
           - documentation_url: /docs/patterns/oauth2.md
           - migration_guide_url: /MIGRATION_v3.5_to_v4.0.md
           - last_documented: 2025-01-10T09:10:00Z
           - doc_completeness: 98%

09:30 AM - Team reviews and approves PR
           All sections complete ✓
           Migration guide tested ✓
           Diagrams accurate ✓

09:45 AM - PR merged
           Documentation updated ✓
           Pattern fully documented ✓

Result: Complete, accurate docs generated in 45 minutes (vs 3-4 hours manual)
```

#### Benefits

**For Technical Writers**:
- Automated first draft of documentation
- Focus time on refinement, not boilerplate
- Always-up-to-date docs

**For Developers**:
- Docs stay synchronized with code
- Clear migration guides for breaking changes
- Visual architecture diagrams

**For Dev-Nexus**:
- Documentation completeness scores
- Better pattern adoption (clear docs)
- Historical documentation for pattern evolution

#### Implementation Plan

**Phase 1** (2 weeks):
- Basic doc extraction from code
- Claude AI integration for doc generation
- Markdown output formatting

**Phase 2** (2 weeks):
- Migration guide generation
- Breaking change detection
- PR automation

**Phase 3** (1 week):
- Architecture diagram generation (Mermaid)
- Doc completeness scoring
- Integration with dev-nexus metadata

---

## Integration Summary

The following table summarizes all current and planned integrations:

| Agent | Status | Timeline | Complexity | Key Benefit |
|-------|--------|----------|------------|-------------|
| **dependency-orchestrator** | ✅ Active | Live | High | Automated dependency updates |
| **pattern-miner** | ✅ Active | Live | Medium | Deep code analysis |
| **agentic-log-attacker** | ✅ Phase 1 | Live | High | Production feedback loop |
| **Testing Coordinator** | 📋 Planned | Q2 2025 | Medium | Automated testing orchestration |
| **Security Scanner** | 📋 Planned | Q3 2025 | High | Vulnerability detection |
| **Performance Analyzer** | 📋 Planned | Q4 2025 | High | Performance regression detection |
| **Documentation Generator** | 📋 Planned | Q1 2026 | Medium | Automated documentation |

---

## See Also

- [README.md](README.md) - Main documentation
- [API.md](API.md) - API reference
- [EXTENDING_DEV_NEXUS.md](EXTENDING_DEV_NEXUS.md) - Adding integrations
- [dependency-orchestrator](https://github.com/patelmm79/dependency-orchestrator) - Orchestrator documentation

---

**Questions about integration?** Open an issue on [GitHub](https://github.com/patelmm79/dev-nexus/issues)

**Last Updated**: 2025-01-10
