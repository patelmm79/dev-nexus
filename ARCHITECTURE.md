# Architecture Documentation: dev-nexus

> **System Design and Implementation Guide**

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Deployment Architecture](#deployment-architecture)
6. [Integration Architecture](#integration-architecture)
7. [Security Architecture](#security-architecture)
8. [Scalability](#scalability)
9. [Design Decisions](#design-decisions)

---

## System Overview

**dev-nexus** is an AI-powered pattern discovery and architectural consistency system that operates in two modes:

1. **GitHub Actions Mode** - Automated pattern analysis on every commit
2. **A2A Server Mode** - Agent-to-Agent API for programmatic access

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repositories                       │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│   │  Repo A  │  │  Repo B  │  │  Repo C  │  │  Repo D  │      │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘      │
└────────┼─────────────┼─────────────┼─────────────┼──────────────┘
         │             │             │             │
         │ Push Events │             │             │
         ▼             ▼             ▼             ▼
    ┌────────────────────────────────────────────────────┐
    │          GitHub Actions Workflows                  │
    │     (Reusable Workflow: .github/workflows/)        │
    └────────────────┬───────────────────────────────────┘
                     │
                     │ Triggers Pattern Analysis
                     ▼
         ┌───────────────────────────┐
         │      DEV-NEXUS CORE       │
         │                           │
         │  ┌─────────────────────┐  │
         │  │ Pattern Extractor   │  │ ← Claude API
         │  │ (LLM-based)         │  │
         │  └──────────┬──────────┘  │
         │             ▼              │
         │  ┌─────────────────────┐  │
         │  │ Knowledge Base      │  │ ← GitHub Storage
         │  │ (v2 Schema)         │  │
         │  └──────────┬──────────┘  │
         │             ▼              │
         │  ┌─────────────────────┐  │
         │  │ Similarity Finder   │  │
         │  └──────────┬──────────┘  │
         │             ▼              │
         │  ┌─────────────────────┐  │
         │  │ Notification Engine │  │ → Webhooks
         │  └─────────────────────┘  │
         └───────────┬───────────────┘
                     │
                     │ A2A Protocol
                     ▼
         ┌───────────────────────────┐
         │      A2A SERVER           │
         │   (FastAPI + Uvicorn)     │
         │                           │
         │  ┌─────────────────────┐  │
         │  │ 15 Skills           │  │
         │  │ (Modular)           │  │
         │  └──────────┬──────────┘  │
         │             │              │
         │  ┌──────────┴──────────┐  │
         │  │  Pattern Query      │  │ ← Public
         │  │  Repository Info    │  │ ← Public
         │  │  Knowledge Mgmt     │  │ ← Auth Required
         │  │  Integration        │  │ ← Public
         │  │  Doc Standards      │  │ ← Public
         │  │  Runtime Monitoring │  │ ← Auth Required
         │  └─────────────────────┘  │
         └───────────┬───────────────┘
                     │
                     │ Deployed on Cloud Run
                     │
         ┌───────────┴───────────────┐
         │                           │
         ▼                           ▼
┌────────────────────┐    ┌───────────────────────┐
│ dependency-        │    │ agentic-log-          │
│ orchestrator       │    │ attacker              │
│                    │    │                       │
│ • Dependency mgmt  │    │ • Runtime monitoring  │
│ • Impact analysis  │    │ • Issue detection     │
│ • PR creation      │    │ • Pattern health      │
└────────────────────┘    └───────────────────────┘
```

---

## Architecture Principles

### 1. **Separation of Concerns**

**Core Logic** (`core/`) - Reusable business logic
- Pattern extraction
- Knowledge base management
- Similarity detection
- Integration coordination

**A2A Server** (`a2a/`) - API layer
- FastAPI application
- Skill registry and execution
- Authentication and authorization
- Request/response handling

**Skills** (`a2a/skills/`) - Modular capabilities
- Self-contained skill modules
- Dynamic registration
- Independent testability

### 2. **Hybrid Architecture**

Two operational modes sharing core logic:

**Mode 1: GitHub Actions CLI**
```
GitHub Push → Workflow → Python Script → Core Logic → Update KB → Notify
```

**Mode 2: A2A Server**
```
External Agent → HTTP Request → A2A Server → Skill → Core Logic → Response
```

**Benefits:**
- No code duplication
- Consistent behavior
- Easy maintenance
- Flexible deployment

### 3. **Modularity**

**Modular Skills v2.0:**
- Each skill is a separate file
- BaseSkill interface for consistency
- SkillRegistry for dynamic discovery
- No central routing file to maintain

**Adding a new skill:**
```python
# 1. Create a2a/skills/my_skill.py
from a2a.skills.base import BaseSkill

class MySkill(BaseSkill):
    @property
    def skill_id(self) -> str:
        return "my_skill"

    async def execute(self, input_data):
        # Implementation
        pass

# 2. Register in a2a/server.py
from a2a.skills.my_skill import MySkillGroup
for skill in MySkillGroup(dependencies).get_skills():
    registry.register(skill)

# Done! No other changes needed.
```

### 4. **Cloud-Native Design**

- **Stateless**: No local state, all data in GitHub
- **Scalable**: Auto-scaling with Cloud Run
- **Observable**: Structured logging to Cloud Logging
- **Resilient**: Graceful degradation on errors
- **Secure**: Secret Manager for credentials

---

## Component Architecture

### Core Components

#### 1. Pattern Extractor (`core/pattern_extractor.py`)

**Purpose:** Extract semantic patterns from code changes using LLM

**Architecture:**
```
Git Diff → File Filter → LLM Prompt → Claude API → Structured JSON
```

**Key Design:**
- Limits to 10 files per analysis (token management)
- Truncates large diffs to 2000 chars
- Uses Claude Sonnet 4 for accuracy
- Returns: patterns, decisions, components, dependencies

**Example:**
```python
extractor = PatternExtractor(anthropic_client)
patterns = extractor.extract_patterns_with_llm(
    repo_name="user/repo",
    file_changes=[...],
    commit_sha="abc123"
)
# Returns:
# {
#   "patterns": ["Redis caching", "JWT auth"],
#   "decisions": ["Use connection pooling"],
#   "reusable_components": ["CacheManager class"],
#   ...
# }
```

#### 2. Knowledge Base Manager (`core/knowledge_base.py`)

**Purpose:** Manage centralized pattern knowledge stored in GitHub

**Architecture:**
```
┌──────────────────────────────────────────┐
│         GitHub Repository                │
│                                          │
│  knowledge_base.json                     │
│  {                                       │
│    "schema_version": "2.0",              │
│    "repositories": {                     │
│      "owner/repo": {                     │
│        "latest_patterns": {...},         │
│        "deployment": {...},              │
│        "dependencies": {...},            │
│        "testing": {...},                 │
│        "security": {...},                │
│        "runtime_issues": [...],  ← NEW   │
│        "production_metrics": {...}, ← NEW│
│        "history": [...]                  │
│      }                                   │
│    }                                     │
│  }                                       │
└──────────────────────────────────────────┘
         ↑                    ↓
         │                    │
    Read/Write via PyGithub
         │                    │
┌────────┴────────────────────┴──────────┐
│    KnowledgeBaseManager                │
│                                         │
│  • load() - Fetch from GitHub          │
│  • save() - Commit back to GitHub      │
│  • get_repository() - Get repo data    │
│  • update_repository() - Update repo   │
│  • migrate_v1_to_v2() - Auto-migrate   │
└─────────────────────────────────────────┘
```

**Schema v2 Enhancements:**
- `runtime_issues` - Production issues from log-attacker
- `production_metrics` - Live performance data
- `deployment` - CI/CD and infrastructure info
- `dependencies` - Consumers, derivatives, externals
- `testing` - Test frameworks and coverage
- `security` - Security patterns and compliance

**Storage Strategy:**
- Single JSON file (simple, versioned, auditable)
- Stored in separate GitHub repository
- Git history provides time-travel
- Atomic updates via GitHub API

#### 3. Similarity Finder (`core/similarity_finder.py`)

**Purpose:** Find similar patterns across repositories

**Algorithm:**
```python
def find_similar(target_repo, all_repos):
    for repo in all_repos:
        if repo == target_repo:
            continue

        # Set-based overlap scoring
        keyword_overlap = len(
            set(target_keywords) & set(repo_keywords)
        )
        pattern_overlap = len(
            set(target_patterns) & set(repo_patterns)
        )

        score = keyword_overlap + pattern_overlap
        if score > 0:
            similar.append((repo, score))

    return sorted(similar, key=lambda x: x[1], reverse=True)[:5]
```

**Future Enhancements:**
- Semantic similarity using embeddings
- Weighted scoring by importance
- Pattern evolution tracking
- Anti-pattern detection

#### 4. Integration Service (`core/integration_service.py`)

**Purpose:** Bidirectional communication with external agents

**Architecture:**
```
┌──────────────────────────────────────────┐
│      IntegrationService                  │
│                                          │
│  • notify_pattern_change()               │
│    → Call orchestrator webhook           │
│                                          │
│  • check_agent_health()                  │
│    → Query external agent /health        │
│                                          │
│  • coordinate_deployment()               │
│    → Multi-agent coordination            │
└──────────────────────────────────────────┘
         │                    │
         ▼                    ▼
┌────────────────┐  ┌──────────────────┐
│ Orchestrator   │  │ Log-Attacker     │
│                │  │                  │
│ POST /webhook  │  │ POST /monitor    │
└────────────────┘  └──────────────────┘
```

---

### A2A Server Architecture

#### FastAPI Application (`a2a/server.py`)

**Design:** Thin coordinator (250 lines, down from 445)

**Structure:**
```python
# 1. Initialize dependencies
anthropic_client = Anthropic(api_key=...)
github_client = Github(token=...)
kb_manager = KnowledgeBaseManager(...)

# 2. Initialize skill registry
registry = get_registry()

# 3. Register all skills (modular)
for skill in PatternQuerySkills(...).get_skills():
    registry.register(skill)

# 4. Initialize executor
executor = PatternDiscoveryExecutor(registry)

# 5. Create FastAPI app
app = FastAPI(...)

# 6. Define routes
@app.post("/a2a/execute")
async def execute_skill(request: ExecuteRequest):
    return await executor.execute(...)

@app.get("/.well-known/agent.json")
async def agent_card():
    return registry.get_agent_card()
```

**Benefits:**
- Declarative skill registration
- No routing logic in server
- Skills auto-discovered
- AgentCard auto-generated

#### Skill Architecture (`a2a/skills/`)

**BaseSkill Interface:**
```python
class BaseSkill(ABC):
    @property
    @abstractmethod
    def skill_id(self) -> str:
        """Unique skill identifier"""
        pass

    @property
    @abstractmethod
    def skill_name(self) -> str:
        """Human-readable name"""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """JSON Schema for input validation"""
        pass

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill"""
        pass

    @property
    def requires_authentication(self) -> bool:
        """Whether skill requires auth"""
        return False
```

**Skill Groups:**

1. **PatternQuerySkills** (Public)
   - `query_patterns` - Search by keywords
   - `get_cross_repo_patterns` - Find patterns across repos

2. **RepositoryInfoSkills** (Public)
   - `get_repository_list` - List all tracked repos
   - `get_deployment_info` - Get deployment metadata

3. **KnowledgeManagementSkills** (Authenticated)
   - `add_lesson_learned` - Record lessons
   - `update_dependency_info` - Update dependencies

4. **IntegrationSkills** (Public)
   - `health_check_external` - Check external agent health

5. **DocumentationStandardsSkills** (Public)
   - `check_documentation_standards` - Validate docs
   - `validate_documentation_update` - Ensure docs updated

6. **RuntimeMonitoringSkills** (Authenticated)
   - `add_runtime_issue` - Record production issues
   - `get_pattern_health` - Analyze pattern health
   - `query_known_issues` - Search historical issues

---

## Data Flow

### Scenario 1: Pattern Discovery (GitHub Actions Mode)

```
1. Developer pushes code
   └─> GitHub webhook triggers workflow

2. Reusable workflow runs
   └─> Checks out dev-nexus repo
   └─> Checks out target repo
   └─> Runs scripts/pattern_analyzer.py

3. Pattern Analyzer
   └─> Gets git diff for changed files
   └─> Filters meaningful files (ignores lock files, etc.)
   └─> Calls PatternExtractor.extract_patterns_with_llm()

4. Pattern Extractor
   └─> Constructs prompt with file changes
   └─> Calls Claude API (claude-sonnet-4-20250514)
   └─> Parses structured JSON response

5. Knowledge Base Update
   └─> KnowledgeBaseManager.load()
   └─> Adds new entry to history
   └─> Updates latest_patterns
   └─> KnowledgeBaseManager.save() → Commits to GitHub

6. Similarity Detection
   └─> SimilarityFinder.find_similar_patterns()
   └─> Returns top 5 similar repositories

7. Notifications
   └─> Sends to Discord/Slack webhook (if configured)
   └─> Notifies orchestrator (if configured)
   └─> Creates GitHub artifact with results
```

### Scenario 2: External Agent Query (A2A Server Mode)

```
1. External agent (log-attacker) detects production issue
   └─> Constructs A2A request

2. HTTP POST to /a2a/execute
   └─> {
         "skill_id": "add_runtime_issue",
         "input": {
           "repository": "user/api-service",
           "issue_type": "error",
           ...
         }
       }

3. FastAPI receives request
   └─> AuthMiddleware validates token (if authenticated skill)
   └─> Routes to executor.execute()

4. Executor
   └─> Registry.get_skill("add_runtime_issue")
   └─> Validates input against skill's input_schema
   └─> Calls skill.execute(input_data)

5. Skill Execution (AddRuntimeIssueSkill)
   └─> KnowledgeBaseManager.load()
   └─> Creates runtime_issue record
   └─> Updates pattern with issue link
   └─> Finds similar issues (_find_similar_issues)
   └─> KnowledgeBaseManager.save()

6. Response
   └─> Returns {
         "success": true,
         "issue_id": "2025-12-09T...",
         "similar_issues": [...]
       }

7. Log-attacker uses response
   └─> Enriches GitHub issue with similar issues
   └─> Shows historical context to developers
```

### Scenario 3: Pattern Health Query

```
1. Orchestrator planning to use a pattern
   └─> POST /a2a/execute
       skill_id: "get_pattern_health"
       input: {"pattern_name": "Redis caching"}

2. GetPatternHealthSkill executes
   └─> Find all repos using pattern
   └─> Get runtime_issues for each repo
   └─> Filter by time range (30 days)
   └─> Calculate health score:
       health = 1.0 - (repos_with_issues / total_repos)

3. Returns health data
   └─> {
         "health_score": 0.85,
         "total_repos": 4,
         "repos_with_issues": 1,
         "recommendation": "Pattern is mostly healthy..."
       }

4. Orchestrator makes decision
   └─> If health_score < 0.7: Warn user
   └─> If health_score < 0.5: Block deployment
   └─> If health_score >= 0.7: Proceed
```

---

## Deployment Architecture

### Cloud Run Deployment

```
┌─────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                 │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │          Cloud Build                           │    │
│  │                                                 │    │
│  │  1. Source from GitHub                         │    │
│  │  2. Build Docker image (multi-stage)           │    │
│  │  3. Push to Container Registry                 │    │
│  │  4. Deploy to Cloud Run                        │    │
│  └────────────────┬───────────────────────────────┘    │
│                   │                                      │
│                   ▼                                      │
│  ┌────────────────────────────────────────────────┐    │
│  │       Container Registry (gcr.io)              │    │
│  │                                                 │    │
│  │  pattern-discovery-agent:latest                │    │
│  │  pattern-discovery-agent:$COMMIT_SHA           │    │
│  └────────────────┬───────────────────────────────┘    │
│                   │                                      │
│                   ▼                                      │
│  ┌────────────────────────────────────────────────┐    │
│  │          Cloud Run Service                     │    │
│  │          pattern-discovery-agent               │    │
│  │                                                 │    │
│  │  • Region: us-central1                         │    │
│  │  • CPU: 1 vCPU                                 │    │
│  │  • Memory: 1 Gi                                │    │
│  │  • Min Instances: 0 (scale to zero)            │    │
│  │  • Max Instances: 10                           │    │
│  │  • Port: 8080                                  │    │
│  │  • Timeout: 300s                               │    │
│  └────────────────┬───────────────────────────────┘    │
│                   │                                      │
│                   │ Injects Secrets                      │
│                   ▼                                      │
│  ┌────────────────────────────────────────────────┐    │
│  │       Secret Manager                           │    │
│  │                                                 │    │
│  │  • GITHUB_TOKEN                                │    │
│  │  • ANTHROPIC_API_KEY                           │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │       Cloud Logging                            │    │
│  │                                                 │    │
│  │  • Structured logs from application            │    │
│  │  • Request/response logs                       │    │
│  │  • Error tracking                              │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │       Cloud Monitoring                         │    │
│  │                                                 │    │
│  │  • CPU/Memory utilization                      │    │
│  │  • Request count & latency                     │    │
│  │  • Error rates                                 │    │
│  └────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
         │                              ▲
         │ HTTPS Requests               │ Responses
         ▼                              │
┌───────────────────────────────────────────────────┐
│         External Agents                           │
│                                                   │
│  • agentic-log-attacker                          │
│  • dependency-orchestrator                        │
│  • pattern-miner                                  │
└───────────────────────────────────────────────────┘
```

### Auto-Scaling Behavior

```
Request Load          Instances
────────────────     ───────────
0 requests/sec       0 (scaled to zero)
1-10 req/sec         1 instance
11-80 req/sec        2-8 instances
80+ req/sec          9-10 instances (max)

Cold Start: ~3-5 seconds
Warm Start: ~50ms
```

---

## Integration Architecture

### Three-Agent Coordination

```
                    ┌──────────────┐
                    │  DEV-NEXUS   │
                    │              │
                    │ Pattern      │
                    │ Intelligence │
                    └───────┬──────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        │ (1) Pattern       │ (4) Runtime       │
        │     Changes       │     Issues        │
        │ (2) Query         │ (5) Pattern       │
        │     Deps          │     Health        │
        │ (3) Lessons       │ (6) Known         │
        │                   │     Issues        │
        ▼                   ▼                   │
┌───────────────┐   ┌───────────────────┐     │
│ Orchestrator  │   │ Log-Attacker      │     │
│               │   │                   │     │
│ • Triage      │   │ • GCP Monitoring  │     │
│ • Deps        │   │ • Issue Detection │     │
│ • PRs         │   │ • AI Analysis     │     │
│ • Updates     │   │ • GitHub Issues   │     │
└───────┬───────┘   └───────┬───────────┘     │
        │                   │                 │
        └───────────────────┴─────────────────┘
              Coordinated Actions
```

### Integration Patterns

**Pattern 1: Event-Driven**
```
Dev-Nexus → Webhook → Orchestrator → Action
```

**Pattern 2: Query-Response**
```
External Agent → A2A Request → Dev-Nexus → Response
```

**Pattern 3: Health Check**
```
Dev-Nexus → Periodic Poll → External Agent → Status
```

---

## Security Architecture

### Authentication Flow

```
1. External Agent Request
   └─> Includes Bearer token in Authorization header

2. Cloud Run Ingress
   └─> Verifies token is valid GCP identity token

3. AuthMiddleware (if authenticated skill)
   └─> Extracts service account email from token
   └─> Checks against ALLOWED_SERVICE_ACCOUNTS
   └─> Allows/Denies request

4. Skill Execution
   └─> Only authenticated skills require auth
   └─> Public skills accessible without token
```

**Service Account Strategy:**
```
┌──────────────────────────┐
│ Log-Attacker Service     │
│                          │
│ SA: log-attacker@...     │
└──────────┬───────────────┘
           │
           │ Uses Workload Identity
           │ to get GCP token
           ▼
┌──────────────────────────┐
│ Dev-Nexus Cloud Run      │
│                          │
│ Checks:                  │
│ - Token valid?           │
│ - SA in allowed list?    │
└──────────────────────────┘
```

### Secret Management

**Architecture:**
```
Application Code
    ↓ (References secret name)
Cloud Run Service
    ↓ (Mounts secret as env var)
Secret Manager
    ↓ (Retrieves secret)
Service Account
    ↓ (IAM permission check)
Secret Value (encrypted at rest)
```

**Permissions:**
- Cloud Run SA has `roles/secretmanager.secretAccessor`
- Secrets never logged or exposed
- Automatic rotation support

---

## Scalability

### Horizontal Scaling

**Cloud Run Auto-Scaling:**
- Scales to **0** when idle (cost optimization)
- Scales to **N** instances based on:
  - CPU utilization
  - Request concurrency
  - Memory usage

**Configuration:**
```yaml
min-instances: 0        # Scale to zero
max-instances: 10       # Handle bursts
concurrency: 80         # Requests per instance
```

### Vertical Scaling

**Resource Limits:**
```
CPU: 1-4 vCPU
Memory: 512Mi - 8Gi
```

**Right-Sizing:**
- Start: 1 vCPU, 1Gi (sufficient for most workloads)
- Scale up if:
  - Request latency > 5s
  - Memory usage > 80%
  - CPU throttling detected

### Knowledge Base Scalability

**Current:**
- Single JSON file
- Size: ~100KB - 10MB typical
- Bottleneck: GitHub API rate limits (5000/hour)

**Future Optimizations:**
- Pagination for large queries
- Caching with TTL
- Sharding by repository prefix
- Cloud Storage for large KBs

---

## Design Decisions

### Why Cloud Run?

**Chosen:** Cloud Run
**Alternatives Considered:** GKE, Cloud Functions, VM

**Reasons:**
1. ✅ Auto-scaling to zero (cost-effective)
2. ✅ No cluster management (unlike GKE)
3. ✅ Fast cold starts (3-5s vs 30s+ VMs)
4. ✅ Built-in load balancing
5. ✅ Integrated with Secret Manager
6. ✅ Per-request billing

**Trade-offs:**
- ❌ Cold starts (mitigated with min-instances)
- ❌ Request timeout limit (3600s max)
- ✅ Simple deployment model
- ✅ Automatic HTTPS and CDN

### Why GitHub for Knowledge Base Storage?

**Chosen:** GitHub JSON file
**Alternatives Considered:** Cloud SQL, Firestore, Cloud Storage

**Reasons:**
1. ✅ Version control (git history)
2. ✅ Simple (no DB management)
3. ✅ Auditable (all changes tracked)
4. ✅ Human-readable (JSON)
5. ✅ Free (no storage costs)

**Trade-offs:**
- ❌ Not optimized for high-frequency writes
- ❌ No complex queries
- ✅ Perfect for append-mostly workload
- ✅ Easy to backup/restore

### Why FastAPI?

**Chosen:** FastAPI
**Alternatives Considered:** Flask, Django, raw ASGI

**Reasons:**
1. ✅ Async support (better concurrency)
2. ✅ Automatic OpenAPI docs
3. ✅ Pydantic validation built-in
4. ✅ Modern Python (type hints)
5. ✅ High performance

### Why Modular Skills Architecture?

**Chosen:** BaseSkill interface + SkillRegistry
**Alternatives Considered:** Monolithic router, Plugin system

**Reasons:**
1. ✅ Easy to add skills (one file)
2. ✅ Independent testing
3. ✅ Clear separation of concerns
4. ✅ Dynamic AgentCard generation
5. ✅ No central routing logic

**Evolution:**
- **v1.0:** Monolithic server (445 lines, all skills in one file)
- **v2.0:** Modular architecture (250 line server, skills separate)

### Why Claude Sonnet 4?

**Chosen:** claude-sonnet-4-20250514
**Alternatives Considered:** GPT-4, Gemini, Claude 3.5

**Reasons:**
1. ✅ Best at code understanding
2. ✅ 200K context window
3. ✅ Structured output support
4. ✅ Cost-effective ($3/M input, $15/M output)
5. ✅ Fast response time (~2-3s)

---

## Future Architecture Enhancements

### Phase 1: Performance (Q1 2025)

1. **Caching Layer**
   - Redis for KB queries
   - TTL: 5 minutes
   - Invalidate on KB update

2. **Batch Processing**
   - Queue pattern extraction requests
   - Process in batches of 5-10
   - Reduce cold starts

### Phase 2: Reliability (Q2 2025)

1. **Multi-Region Deployment**
   - Primary: us-central1
   - Failover: europe-west1
   - Global load balancing

2. **Async Job Processing**
   - Cloud Tasks for long-running operations
   - Webhook callbacks for completion
   - Progress tracking

### Phase 3: Intelligence (Q3 2025)

1. **Embedding-Based Similarity**
   - Vector embeddings for patterns
   - Semantic similarity search
   - Pattern clustering

2. **Pattern Evolution Tracking**
   - Track how patterns change over time
   - Detect breaking changes
   - Migration path suggestions

---

**Last Updated:** 2025-12-09
**Version:** 1.0
**Authors:** System Architecture Team
