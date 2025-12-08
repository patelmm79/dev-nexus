# Integration Scenarios

> Real-world examples of Dev-Nexus integrating with dependency-orchestrator

**Last Updated**: 2025-01-10

---

## Scenario 1: Breaking API Change

### Context

You maintain an authentication library used by 5 different applications. You need to update the JWT validation logic with a breaking change.

### Without Integration

```
Manual Process (3-5 days):
──────────────────────────

Day 1:
  - Update auth library
  - Commit and push
  - Manually check which apps use this library
  - Create spreadsheet tracking dependents

Day 2:
  - For each dependent:
    - Clone repository
    - Review code to understand usage
    - Make necessary updates
    - Create PR
    - Wait for review

Day 3-5:
  - Chase down reviewers
  - Address PR feedback
  - Merge and deploy
  - Some apps get missed
  - Breaking changes discovered in production
```

### With Dev-Nexus + dependency-orchestrator

```
Automated Process (30 minutes):
───────────────────────────────

10:00 AM - Push auth library update
           ┌────────────────────────────────┐
           │ git commit -m "Update JWT v2"  │
           │ git push                       │
           └────────────────────────────────┘
                      │
                      ▼
10:01 AM - Dev-Nexus analyzes changes
           ┌────────────────────────────────┐
           │ Pattern: JWT validation        │
           │ Breaking: Yes                  │
           │ Severity: High                 │
           └────────────────────────────────┘
                      │
                      ▼
10:01 AM - Orchestrator notified
           ┌────────────────────────────────┐
           │ Orchestrator receives event    │
           │ Queries dev-nexus for deps     │
           │ Finds 5 dependent apps         │
           └────────────────────────────────┘
                      │
                      ▼
10:02 AM - AI Triage analyzes impact
           ┌────────────────────────────────┐
           │ App 1: Critical (prod traffic) │
           │ App 2: High (customer-facing)  │
           │ App 3: Medium (internal)       │
           │ App 4: Low (staging only)      │
           │ App 5: Info (deprecated)       │
           └────────────────────────────────┘
                      │
                      ▼
10:05 AM - PRs created automatically
           ┌────────────────────────────────┐
           │ PR #1: [URGENT] Update JWT     │
           │   Repo: mobile-app             │
           │   Tests: ✓ Passed              │
           │   Description: Breaking change │
           │                                │
           │ PR #2: Update JWT validation   │
           │   Repo: web-dashboard          │
           │   ...                          │
           └────────────────────────────────┘
                      │
                      ▼
10:10 AM - Team notified
           ┌────────────────────────────────┐
           │ Discord: 🚨 Breaking Change    │
           │                                │
           │ 5 PRs created automatically    │
           │ 2 urgent, 3 normal priority    │
           │                                │
           │ Review urgently: PR #1, PR #2  │
           └────────────────────────────────┘
                      │
                      ▼
10:30 AM - All dependents updated
           ┌────────────────────────────────┐
           │ 5/5 PRs reviewed and merged    │
           │ Lesson learned recorded        │
           │ Documentation auto-updated     │
           └────────────────────────────────┘

Result: 30 minutes vs 3-5 days ✅
```

---

## Scenario 2: Pattern Consistency Enforcement

### Context

Your team has 10 microservices. Some use Redis for caching, others use in-memory cache, and one uses memcached. You want to standardize on Redis.

### Implementation

```python
# Step 1: Dev-Nexus detects inconsistency
# ────────────────────────────────────────

# Service A commits Redis implementation
git commit -m "Add Redis caching for user sessions"

# Dev-Nexus extracts pattern:
{
  "pattern": "Distributed caching with Redis",
  "implementation": {
    "library": "redis-py",
    "connection_pooling": true,
    "ttl_strategy": "sliding_window"
  }
}

# Dev-Nexus finds similar patterns:
# - Service B: In-memory cache (dict)
# - Service C: Redis (different config)
# - Service D: Memcached


# Step 2: Orchestrator takes action
# ──────────────────────────────────

# For Service B (in-memory):
orchestrator.create_issue({
  "repo": "service-b",
  "title": "Consider migrating to Redis for caching",
  "body": """
  ## Pattern Inconsistency Detected

  Service A recently standardized on Redis for caching.

  **Your current implementation:** In-memory dict
  **Recommended:** Redis with connection pooling

  **Benefits:**
  - Distributed caching across instances
  - Persistence on restart
  - Better memory management

  **Reference implementation:**
  See service-a/cache/redis_cache.py

  **Related services also using Redis:**
  - service-a
  - service-c
  """
})

# For Service C (Redis different config):
orchestrator.create_issue({
  "repo": "service-c",
  "title": "Align Redis configuration with service-a",
  "body": """
  ## Configuration Drift Detected

  Both services use Redis but with different configs.

  **Differences:**
  - service-a: Connection pooling enabled
  - service-c: Single connection

  **Recommended:** Adopt service-a's config for better performance
  """
})


# Step 3: Tracking and enforcement
# ─────────────────────────────────

# Dev-nexus maintains architectural decisions:
{
  "architectural_decisions": {
    "caching_strategy": {
      "decision": "Use Redis for distributed caching",
      "rationale": "Consistency across services, better scalability",
      "exceptions": ["service-d: Legacy memcached during migration"],
      "enforced_since": "2025-01-10",
      "affected_repos": [
        "service-a",
        "service-b",
        "service-c"
      ]
    }
  }
}

# Future commits to any service are checked against this decision
# Divergence triggers notification
```

---

## Scenario 3: Dependency Update Cascade

### Context

A security vulnerability is discovered in the `requests` library. All services using it need urgent updates.

### Without Integration

```
Manual Security Update (2-3 days):
──────────────────────────────────

Hour 1-2:
  - Security team sends email
  - Manually grep for "requests" in all repos
  - Create tracking spreadsheet
  - Prioritize by criticality

Hour 3-8:
  - Update each repo manually
  - Run tests locally
  - Create PRs
  - Some repos missed

Day 2:
  - Follow up on missed repos
  - Chase reviewers
  - Emergency deploys

Day 3:
  - Security scan shows 2 repos still vulnerable
  - Repeat process
```

### With Dev-Nexus + dependency-orchestrator

```
Automated Security Update (1 hour):
───────────────────────────────────

09:00 AM - Security alert received
           ┌────────────────────────────────┐
           │ CVE: requests < 2.31.0         │
           │ Severity: HIGH                 │
           │ Fix: Upgrade to 2.31.0+        │
           └────────────────────────────────┘
                      │
                      ▼
09:01 AM - Query dev-nexus for affected repos
           ┌────────────────────────────────┐
           │ POST /a2a/execute              │
           │ {                              │
           │   "skill_id": "query_patterns",│
           │   "input": {                   │
           │     "keywords": ["requests"],  │
           │     "dependency": "requests"   │
           │   }                            │
           │ }                              │
           └────────────────────────────────┘
                      │
                      ▼
09:02 AM - Dev-nexus returns affected repos
           ┌────────────────────────────────┐
           │ Found 8 repos using requests:  │
           │                                │
           │ Critical (prod):               │
           │   - api-gateway (v2.28.0)      │
           │   - payment-service (v2.29.0)  │
           │                                │
           │ High (customer-facing):        │
           │   - web-scraper (v2.28.0)      │
           │   - notification-service       │
           │                                │
           │ Medium (internal):             │
           │   - admin-panel (v2.30.0)      │
           │   - analytics-service          │
           │                                │
           │ Low (dev):                     │
           │   - dev-tools (v2.27.0)        │
           │   - test-fixtures              │
           └────────────────────────────────┘
                      │
                      ▼
09:05 AM - Orchestrator creates PRs
           ┌────────────────────────────────┐
           │ 8 PRs created with:            │
           │                                │
           │ - Dependency update            │
           │ - Security context             │
           │ - Test results                 │
           │ - Priority labels              │
           │                                │
           │ Auto-merged if tests pass:     │
           │   - dev-tools ✓                │
           │   - test-fixtures ✓            │
           │                                │
           │ Requires review:               │
           │   - api-gateway (critical)     │
           │   - payment-service (critical) │
           └────────────────────────────────┘
                      │
                      ▼
09:10 AM - Deployments triggered
           ┌────────────────────────────────┐
           │ Auto-deployed (passed tests):  │
           │   - dev-tools                  │
           │   - test-fixtures              │
           │                                │
           │ Awaiting approval:             │
           │   - 6 critical/high services   │
           │                                │
           │ Slack notification sent:       │
           │ "🚨 SECURITY: 6 services need  │
           │  urgent review for CVE fix"    │
           └────────────────────────────────┘
                      │
                      ▼
10:00 AM - All services updated
           ┌────────────────────────────────┐
           │ 8/8 services patched           │
           │ Lesson learned recorded:       │
           │ "CVE response time: 1 hour"    │
           │                                │
           │ Security scan: ✓ All clear     │
           └────────────────────────────────┘

Result: 1 hour vs 2-3 days ✅
       100% coverage vs partial ✅
```

---

## Scenario 4: Architectural Decision Tracking

### Context

Your team decides to migrate from REST to GraphQL for new services. You want to track adoption and ensure consistency.

### Implementation

```yaml
# Step 1: Record decision in dev-nexus
# ────────────────────────────────────

POST /a2a/execute
skill_id: add_lesson_learned
input:
  repository: architecture-decisions
  category: architecture
  lesson: |
    Adopt GraphQL for all new APIs

    Decision: 2025-01-10
    Rationale:
      - Better client flexibility
      - Type safety
      - Reduced over-fetching

    Guidelines:
      - Use Apollo Server
      - Share schema across services
      - Use DataLoader for batching

    Exceptions:
      - Legacy services remain REST
      - Webhooks remain REST
  severity: info


# Step 2: Dev-nexus monitors compliance
# ─────────────────────────────────────

# New service created with REST API
git commit -m "Add customer-service with REST endpoints"

# Dev-nexus detects:
{
  "pattern": "REST API endpoints",
  "repository": "customer-service",
  "created": "2025-01-15",
  "conflicts_with_decision": {
    "decision": "Adopt GraphQL for new APIs",
    "date": "2025-01-10"
  }
}

# Notification sent:
Discord: ⚠️ Architectural Decision Divergence

customer-service uses REST API
Team decision (2025-01-10): Use GraphQL for new services

Is this intentional? If yes, document exception.
If no, consider migrating to GraphQL.

Reference: architecture-decisions repo


# Step 3: Adoption tracking
# ─────────────────────────

# Dev-nexus tracks adoption:
{
  "decision_tracking": {
    "graphql_adoption": {
      "compliant_services": [
        "order-service",
        "product-service",
        "user-service"
      ],
      "non_compliant_services": [
        "customer-service (exception documented)"
      ],
      "legacy_services": [
        "old-api-v1",
        "legacy-monolith"
      ],
      "adoption_rate": "75%",
      "trend": "increasing"
    }
  }
}

# Monthly reports generated automatically
```

---

## Scenario 5: Performance Pattern Analysis

### Context

One service achieves 10x better performance than others. You want to identify and propagate the patterns.

### Implementation

```python
# Step 1: Pattern-miner identifies optimization
# ─────────────────────────────────────────────

# High-performing service analyzed
pattern_miner.analyze({
  "repository": "fast-api-service",
  "focus": "performance"
})

# Results:
{
  "performance_patterns": [
    {
      "pattern": "Database connection pooling",
      "implementation": {
        "pool_size": 20,
        "max_overflow": 10,
        "pool_recycle": 3600,
        "pool_pre_ping": true
      },
      "impact": "10x throughput increase"
    },
    {
      "pattern": "Response caching with ETag",
      "implementation": {
        "cache_layer": "Redis",
        "ttl_strategy": "conditional",
        "etag_generation": "content_hash"
      },
      "impact": "70% cache hit rate"
    },
    {
      "pattern": "Async I/O with asyncio",
      "implementation": {
        "framework": "FastAPI",
        "async_db_driver": "asyncpg",
        "concurrent_requests": 1000
      },
      "impact": "5x concurrency"
    }
  ]
}


# Step 2: Dev-nexus compares with other services
# ───────────────────────────────────────────────

dev_nexus.compare_patterns({
  "baseline": "fast-api-service",
  "compare_to": ["service-a", "service-b", "service-c"]
})

# Results show gaps:
{
  "service-a": {
    "missing_patterns": [
      "Database connection pooling",
      "Response caching"
    ],
    "current_performance": "100 req/s",
    "potential_improvement": "10x"
  },
  "service-b": {
    "missing_patterns": [
      "Async I/O"
    ],
    "current_performance": "200 req/s",
    "potential_improvement": "5x"
  }
}


# Step 3: Orchestrator creates improvement tickets
# ─────────────────────────────────────────────────

# For service-a:
orchestrator.create_issue({
  "repo": "service-a",
  "title": "Performance optimization opportunity",
  "labels": ["performance", "optimization"],
  "body": """
  ## Performance Optimization Opportunity

  Analysis shows fast-api-service achieves 10x better throughput.

  **Key differences:**

  ### 1. Database Connection Pooling
  **Current:** Single connection
  **Recommended:** Pool size 20, max overflow 10
  **Expected Impact:** 10x throughput

  ```python
  # Example implementation from fast-api-service
  engine = create_engine(
      DATABASE_URL,
      pool_size=20,
      max_overflow=10,
      pool_recycle=3600,
      pool_pre_ping=True
  )
  ```

  ### 2. Response Caching
  **Current:** No caching
  **Recommended:** Redis with ETag support
  **Expected Impact:** 70% cache hit rate

  ### Priority
  High - Significant performance gains available

  ### References
  - fast-api-service/database/pool.py
  - fast-api-service/cache/redis_cache.py
  """
})


# Step 4: Track adoption and measure impact
# ──────────────────────────────────────────

# After service-a implements changes:
{
  "performance_tracking": {
    "service-a": {
      "before": "100 req/s",
      "after": "950 req/s",
      "improvement": "9.5x",
      "patterns_adopted": [
        "Database connection pooling",
        "Response caching"
      ]
    }
  }
}

# Lesson learned recorded:
dev_nexus.add_lesson({
  "repository": "service-a",
  "category": "performance",
  "lesson": "Connection pooling + caching = 9.5x improvement",
  "context": "Adopted patterns from fast-api-service",
  "metrics": {
    "throughput_before": "100 req/s",
    "throughput_after": "950 req/s",
    "implementation_time": "2 days"
  }
})
```

---

## Summary

These scenarios demonstrate how Dev-Nexus + dependency-orchestrator transform software engineering workflows:

| Scenario | Without Integration | With Integration | Time Saved |
|----------|-------------------|------------------|------------|
| Breaking API Change | 3-5 days | 30 minutes | 95% |
| Pattern Consistency | Manual, inconsistent | Automated detection | N/A |
| Security Update | 2-3 days, partial | 1 hour, complete | 90% |
| Architecture Tracking | Spreadsheets, outdated | Real-time, automated | 100% |
| Performance Optimization | Ad-hoc, missed opportunities | Systematic, measured | N/A |

**Key Benefits:**
- ⚡ **Speed**: Updates propagate in minutes, not days
- ✅ **Completeness**: No repositories missed
- 📊 **Visibility**: Real-time tracking and reporting
- 🎯 **Consistency**: Automated pattern enforcement
- 📚 **Learning**: Lessons captured automatically

---

**See Also:**
- [INTEGRATION.md](../INTEGRATION.md) - Complete integration guide
- [API.md](../API.md) - API reference
- [dependency-orchestrator](https://github.com/patelmm79/dependency-orchestrator) - Orchestrator documentation
