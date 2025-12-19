# Component Sensibility System

## Overview

The Component Sensibility System automatically detects components that are duplicated across repositories and recommends consolidation to canonical locations. It uses PostgreSQL vectorization (pgvector) with TF-IDF vectors for semantic similarity matching, smart multi-factor heuristics for canonical location scoring, and deep integration with pattern-miner for code analysis.

**Example**: Detect that both `agentic-log-attacker` and `dev-nexus` have GitHub API clients, recommend consolidating to `dev-nexus` as the central infrastructure hub, and provide a 4-phase consolidation plan.

## Features

✅ **Automatic Component Detection** - AST-based extraction of 4 component types
✅ **Semantic Similarity** - pgvector + TF-IDF for intelligent matching
✅ **Smart Canonical Scoring** - 6-factor heuristics (purpose, usage, centrality, maintenance, complexity, first-impl)
✅ **External Integration** - Coordinates with dependency-orchestrator and pattern-miner
✅ **Phased Planning** - 4-phase consolidation roadmaps with effort estimates
✅ **Transparent Scoring** - Factor-by-factor explanations for all recommendations
✅ **Graceful Degradation** - Works independently if external agents unavailable

## Architecture

```
┌─────────────────────────────────────────────────┐
│   Component Sensibility System                   │
├─────────────────────────────────────────────────┤
│                                                  │
│  1. ComponentScanner (AST Extraction)           │
│     └─ 4 component types                        │
│                                                  │
│  2. VectorCacheManager (pgvector)               │
│     ├─ TF-IDF vectors (300 dim)                 │
│     ├─ Cosine similarity queries                │
│     └─ Hybrid caching                           │
│                                                  │
│  3. CentralityCalculator (Heuristics)           │
│     └─ 6-factor scoring                         │
│                                                  │
│  4. A2A Skills                                  │
│     ├─ detect_misplaced_components              │
│     ├─ analyze_component_centrality             │
│     └─ recommend_consolidation_plan             │
│                                                  │
│  5. External Integration                        │
│     ├─ dependency-orchestrator                  │
│     └─ pattern-miner                            │
│                                                  │
└─────────────────────────────────────────────────┘
```

## Component Types

### 1. API Clients
- **Detection**: Files matching `*_client.py`, `*_api.py`
- **Examples**: GitHubAPIClient, SlackClient, AWSClient
- **Metadata**: API methods, imports, keywords

### 2. Infrastructure Utilities
- **Detection**: Files in `utils/`, `core/`, `lib/` directories
- **Examples**: RetryHandler, ConnectionPool, Logger
- **Metadata**: Public methods, dependencies, complexity

### 3. Business Logic
- **Detection**: Domain models with `validate()`, `transform()`, `process()`
- **Examples**: OrderProcessor, PaymentValidator, DataTransformer
- **Metadata**: Methods, keywords, dependencies

### 4. Deployment Patterns
- **Detection**: Terraform files, Dockerfiles, Cloud Build configs
- **Examples**: terraform modules, multi-stage Docker builds, CI/CD pipelines
- **Metadata**: Language, keywords, infrastructure type

## Canonical Location Scoring

The system uses 6 weighted factors to determine the best repository for a component:

### Factor 1: Repository Purpose (30%)
Scores how well a repository is designed as infrastructure/shared utilities

- Infrastructure repo: 0.70-0.90
- Mixed application: 0.40-0.60
- Pure application: 0.20-0.30

### Factor 2: Usage Count (30%)
Counts how many repositories would benefit from centralization

- 5+ repositories: 1.0
- 3-4 repositories: 0.8-0.9
- 2 repositories: 0.6
- 1 repository: 0.4
- Only local: 0.2

### Factor 3: Dependency Centrality (20%)
Analyzes repository position in dependency graph (betweenness centrality)

- Central hub (dev-nexus): 0.80-0.90
- Mid-level (core service): 0.60-0.70
- Leaf node (app service): 0.20-0.30

### Factor 4: Maintenance Activity (10%)
Evaluates commit frequency, recency, and active contributors

- High activity: 0.80-1.0
- Medium activity: 0.50-0.70
- Low activity: 0.20-0.40

### Factor 5: Component Complexity (5%)
Considers LOC, API surface, and cyclomatic complexity

- 200+ LOC, 8+ methods: 0.70-1.0
- 100-200 LOC, 4-8 methods: 0.40-0.70
- < 100 LOC, < 4 methods: 0.20-0.40

### Factor 6: First Implementation (5%)
Tie-breaker: prefers original repository if all else equal

- Oldest implementation: 1.0
- Middle: 0.5
- Newest: 0.0

## Three A2A Skills

### Skill 1: `detect_misplaced_components`

Scans repositories for components that appear in multiple places or might be better centralized.

**Input**:
```json
{
  "repository": "patelmm79/agentic-log-attacker",
  "component_types": ["api_client"],
  "min_similarity_score": 0.7,
  "include_diverged": true,
  "top_k_matches": 5
}
```

**Output**:
```json
{
  "success": true,
  "misplaced_components": [
    {
      "component_name": "GitHubAPIClient",
      "current_location": "patelmm79/agentic-log-attacker",
      "similar_components": [
        {
          "component_name": "GitHubAPIClient",
          "repository": "patelmm79/dev-nexus",
          "similarity_score": 0.85
        }
      ],
      "canonical_recommendation": {
        "repository": "patelmm79/dev-nexus",
        "canonical_score": 0.82,
        "current_score": 0.45,
        "reasoning": "dev-nexus is infrastructure repo with 4 consumers"
      }
    }
  ]
}
```

### Skill 2: `analyze_component_centrality`

Explains canonical location scores for a component across candidates.

**Input**:
```json
{
  "component_name": "GitHubAPIClient",
  "current_location": "patelmm79/agentic-log-attacker",
  "candidate_locations": ["patelmm79/dev-nexus"]
}
```

**Output**:
```json
{
  "success": true,
  "analysis": {
    "best_location": "patelmm79/dev-nexus",
    "best_score": 0.82,
    "all_scores": {
      "patelmm79/dev-nexus": {
        "canonical_score": 0.82,
        "factors": {
          "repository_purpose": 0.90,
          "usage_count": 0.85,
          "dependency_centrality": 0.88,
          "maintenance_activity": 0.80,
          "component_complexity": 0.65,
          "first_implementation": 0.50
        },
        "reasoning": "dev-nexus scores well on repository purpose, usage count, and centrality"
      }
    }
  }
}
```

### Skill 3: `recommend_consolidation_plan`

Generates phased consolidation roadmap with effort estimates and impact analysis.

**Input**:
```json
{
  "component_name": "GitHubAPIClient",
  "from_repository": "patelmm79/agentic-log-attacker",
  "to_repository": "patelmm79/dev-nexus",
  "include_impact_analysis": true,
  "include_deep_analysis": true
}
```

**Output**:
```json
{
  "success": true,
  "recommendation_id": "a1b2c3d4",
  "consolidation_plan": {
    "phase_1": {
      "name": "Analyze & Prepare",
      "description": "Deep analysis of component implementation in both locations",
      "estimated_hours": "2-3",
      "tasks": [
        "Compare API signatures",
        "Identify behavioral differences",
        "Document feature gaps",
        "Create migration checklist"
      ]
    },
    "phase_2": {
      "name": "Merge & Standardize",
      "estimated_hours": "3-4"
    },
    "phase_3": {
      "name": "Update Consumers",
      "estimated_hours": "2-3",
      "affected_repositories": [
        "patelmm79/agentic-log-attacker",
        "patelmm79/pattern-miner"
      ]
    },
    "phase_4": {
      "name": "Monitor & Verify",
      "estimated_hours": "1-2",
      "success_criteria": [
        "No increase in error rates",
        "All tests passing",
        "Consumer repositories updated"
      ]
    },
    "total_estimated_effort": "8-12 hours"
  },
  "impact_analysis": {
    "affected_repositories": ["agentic-log-attacker", "pattern-miner"],
    "risk_level": "MEDIUM",
    "dependency_chain": ["dev-nexus", "agentic-log-attacker"]
  },
  "deep_analysis": {
    "api_compatibility": 0.85,
    "behavioral_differences": ["error handling style", "webhook support missing"],
    "feature_gaps": ["webhook support in dev-nexus version"]
  }
}
```

## Setup

### 1. Install Dependencies

```bash
pip install networkx sqlalchemy psycopg[binary]
```

### 2. Initialize PostgreSQL

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Tables are created automatically by VectorCacheManager on first use
```

### 3. Set Environment Variables

```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/devnexus"
export PATTERN_MINER_URL="https://pattern-miner.run.app"
export PATTERN_MINER_TOKEN="sk-xxx"
export ORCHESTRATOR_URL="https://orchestrator.run.app"
export ORCHESTRATOR_TOKEN="sk-xxx"
```

### 4. Run Migration

```bash
python migrations/003_add_component_provenance.py
```

This scans all repositories, extracts components, generates vectors, and builds the provenance index.

## Usage

### Via React Frontend (Recommended)

The Component Sensibility System is fully integrated into **dev-nexus-frontend** at `http://localhost:3000/components`:

**Features**:
- **Component Detection**: Select repository, adjust similarity threshold, view misplaced components
- **Canonical Scoring**: Interactive breakdown of 6-factor scoring with visual weights
- **Consolidation Planning**: 4-phase roadmap viewer with effort estimates and impact analysis
- **Dependency Graph**: Network visualization of component dependencies across repositories

**Setup**:
```bash
git clone https://github.com/patelmm79/dev-nexus-frontend.git
cd dev-nexus-frontend
npm install
npm start  # Opens http://localhost:3000
```

Then navigate to `/components` page.

**See [FRONTEND_INTEGRATION.md](./FRONTEND_INTEGRATION.md) for complete setup and development guide.**

### Via A2A Protocol

```bash
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "detect_misplaced_components",
    "input": {
      "repository": "patelmm79/agentic-log-attacker",
      "component_types": ["api_client"]
    }
  }'
```

### Via Python

```python
from a2a.skills.component_sensibility import ComponentSensibilitySkills
from core.knowledge_base import KnowledgeBaseManager
from core.component_analyzer import VectorCacheManager

# Initialize
kb_manager = KnowledgeBaseManager()
vector_manager = VectorCacheManager("postgresql://localhost/devnexus")
skills = ComponentSensibilitySkills(kb_manager, vector_manager)

# Get all skills
for skill in skills.get_skills():
    print(f"{skill.skill_id}: {skill.skill_description}")

# Use detect_misplaced_components skill
detect_skill = skills.get_skills()[0]
result = detect_skill.execute({
    "repository": "patelmm79/agentic-log-attacker"
})
```

### Demo Script

```bash
python examples/component_sensibility_demo.py
```

Shows all three skills in action with realistic examples.

## Testing

### Run Unit Tests

```bash
python -m pytest tests/test_component_analyzer.py -v
```

Tests ComponentScanner, VectorCacheManager, CentralityCalculator, and data models.

### Run Integration Tests

```bash
python -m pytest tests/test_component_sensibility_skills.py -v
```

Tests all three A2A skills with mocked dependencies.

### Test Coverage

```bash
python -m pytest tests/ --cov=core.component_analyzer --cov=a2a.skills.component_sensibility
```

## Integration with External Agents

### dependency-orchestrator Integration

The system calls `get_consolidation_impact` to understand:
- Which repositories would be affected
- Dependency chains that need updating
- Overall risk level

```python
impact = self.integration_service.query_consolidation_impact(
    "GitHubAPIClient",
    "patelmm79/agentic-log-attacker",
    "patelmm79/dev-nexus"
)
# Returns: affected_repos, dependency_chain, risk_level
```

### pattern-miner Integration

The system calls `analyze_component_consolidation` to analyze:
- API compatibility between versions
- Behavioral differences
- Feature gaps

```python
analysis = self.integration_service.trigger_component_analysis(
    "patelmm79/agentic-log-attacker",
    ["GitHubAPIClient"],
    focus_areas=["api_compatibility", "behavioral_differences"]
)
# Returns: compatibility score, differences, gaps
```

## Performance

- **Component Extraction**: ~100ms per repository (AST parsing)
- **Vector Generation**: ~500ms per component (via pattern-miner)
- **Similarity Search**: ~50ms per component (pgvector cosine similarity)
- **Full KB Scan**: ~5 seconds for 20+ repositories

## Troubleshooting

### pgvector Extension Not Found

```sql
-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

### Vector Generation Fails

Check that pattern-miner is available and has `generate_component_vectors` skill:

```bash
curl http://pattern-miner-url/.well-known/agent.json
```

### Slow Similarity Searches

Check pgvector index is created:

```sql
SELECT * FROM pg_indexes WHERE tablename = 'component_vectors';
```

If not found, rebuild:

```sql
REINDEX INDEX idx_component_vector_cosine;
```

## Future Enhancements

- [ ] Automatic consolidation PR creation
- [ ] Component health monitoring (test coverage, error rates)
- [ ] Divergence detection improvements (behavioral analytics)
- [ ] Dashboard for consolidation progress tracking
- [ ] Integration with GitHub Actions for automated workflows

## Contributing

See [CLAUDE.md](../CLAUDE.md) for development setup and guidelines.

## References

- [CLAUDE.md](../CLAUDE.md) - Main architecture documentation
- [INTEGRATION.md](./INTEGRATION.md) - External agent coordination
- [examples/component_sensibility_demo.py](../examples/component_sensibility_demo.py) - Usage examples
- [tests/](../tests/) - Comprehensive test suite
