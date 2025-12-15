# Pattern-Miner A2A Conversion Plan

## Overview

Convert pattern-miner from REST API service to A2A (Agent-to-Agent) protocol agent for seamless integration with dev-nexus and future agents.

**Estimated Time:** 2-3 hours
**Difficulty:** Medium
**Breaking Changes:** Yes (REST API endpoints will be replaced)

---

## Current State Analysis

### Existing Pattern-Miner Structure

```
pattern-miner/
├── pattern_miner/          # Core package
│   ├── __init__.py
│   ├── analyzer.py         # Pattern analysis logic (KEEP)
│   ├── api.py             # FastAPI REST endpoints (CONVERT)
│   ├── config.py          # Configuration (EXTEND)
│   └── models.py          # Data models (REUSE)
├── config/
│   └── repositories.json   # Repository definitions
├── .env.example           # Environment variables
├── Dockerfile             # Container config (UPDATE)
├── requirements.txt       # Dependencies (ADD a2a libs)
└── deploy-gcp.sh         # GCP deployment (UPDATE)
```

### Current REST API Endpoints

1. **POST /api/mine-patterns**
   - Input: `{"repository": "owner/repo", "focus_areas": [...]}`
   - Output: Pattern analysis results
   - Maps to: `analyze_repository` A2A skill

2. **GET /api/patterns**
   - Input: Query params
   - Output: Stored patterns
   - Maps to: `get_analysis_results` A2A skill

3. **GitHub issue creation** (internal)
   - Keep as internal function

---

## Conversion Plan

### Phase 1: Add A2A Foundation (30 min)

#### 1.1 Create Base Skill Structure

Create `pattern_miner/a2a/` directory:

```python
# pattern_miner/a2a/__init__.py
"""A2A Protocol Support for Pattern Miner"""

# pattern_miner/a2a/base.py
from typing import Dict, Any, List
from abc import ABC, abstractmethod

class BaseSkill(ABC):
    """Base class for Pattern Miner A2A skills"""

    @property
    @abstractmethod
    def skill_id(self) -> str:
        pass

    @property
    @abstractmethod
    def skill_name(self) -> str:
        pass

    @property
    @abstractmethod
    def skill_description(self) -> str:
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        pass

    @property
    def tags(self) -> List[str]:
        return []

    @property
    def requires_authentication(self) -> bool:
        return False

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return []

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def to_agent_card_entry(self) -> Dict[str, Any]:
        return {
            "id": self.skill_id,
            "name": self.skill_name,
            "description": self.skill_description,
            "tags": self.tags,
            "requires_authentication": self.requires_authentication,
            "input_schema": self.input_schema,
            "examples": self.examples
        }
```

#### 1.2 Create Skill Registry

```python
# pattern_miner/a2a/registry.py
from typing import Dict, List
from pattern_miner.a2a.base import BaseSkill

class SkillRegistry:
    """Registry for all A2A skills"""

    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}

    def register(self, skill: BaseSkill):
        self._skills[skill.skill_id] = skill

    def get_skill(self, skill_id: str) -> BaseSkill:
        return self._skills.get(skill_id)

    def get_skill_ids(self) -> List[str]:
        return list(self._skills.keys())

    def to_agent_card_skills(self) -> List[Dict]:
        return [skill.to_agent_card_entry() for skill in self._skills.values()]

# Global registry instance
_registry = None

def get_registry() -> SkillRegistry:
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry
```

---

### Phase 2: Create A2A Skills (60 min)

#### 2.1 Analyze Repository Skill

```python
# pattern_miner/a2a/skills/analysis.py
from typing import Dict, Any, List
from pattern_miner.a2a.base import BaseSkill
from pattern_miner.analyzer import PatternAnalyzer  # Existing logic

class AnalyzeRepositorySkill(BaseSkill):
    """Deep pattern analysis of a repository"""

    def __init__(self, analyzer: PatternAnalyzer):
        self.analyzer = analyzer

    @property
    def skill_id(self) -> str:
        return "analyze_repository"

    @property
    def skill_name(self) -> str:
        return "Analyze Repository Patterns"

    @property
    def skill_description(self) -> str:
        return "Perform deep pattern analysis on a GitHub repository to identify reusable code, common patterns, and architectural decisions"

    @property
    def tags(self) -> List[str]:
        return ["analysis", "patterns", "deep-dive"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository name in format 'owner/repo'"
                },
                "file_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific file paths to analyze (optional)"
                },
                "focus_areas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Areas to focus on: deployment, api_clients, config, github_actions"
                },
                "create_github_issue": {
                    "type": "boolean",
                    "description": "Create GitHub issue with findings (default: false)"
                }
            },
            "required": ["repository"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "repository": "patelmm79/web-scraper",
                    "focus_areas": ["deployment", "api_clients"]
                },
                "description": "Analyze deployment and API client patterns"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute pattern analysis"""
        try:
            repository = input_data.get("repository")
            file_paths = input_data.get("file_paths", [])
            focus_areas = input_data.get("focus_areas", [])
            create_issue = input_data.get("create_github_issue", False)

            if not repository:
                return {
                    "success": False,
                    "error": "Missing required field: repository"
                }

            # Use existing analyzer logic
            results = await self.analyzer.analyze(
                repository=repository,
                file_paths=file_paths,
                focus_areas=focus_areas
            )

            # Optionally create GitHub issue
            issue_url = None
            if create_issue and results.get("patterns"):
                issue_url = await self.analyzer.create_extraction_issue(
                    repository=repository,
                    patterns=results["patterns"]
                )

            return {
                "success": True,
                "repository": repository,
                "patterns": results.get("patterns", []),
                "extraction_opportunities": results.get("extraction_opportunities", []),
                "analysis_metadata": {
                    "files_analyzed": results.get("files_analyzed", 0),
                    "patterns_found": len(results.get("patterns", [])),
                    "timestamp": results.get("timestamp")
                },
                "github_issue": issue_url
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Analysis failed: {str(e)}"
            }
```

#### 2.2 Compare Implementations Skill

```python
# pattern_miner/a2a/skills/analysis.py (continued)

class CompareImplementationsSkill(BaseSkill):
    """Compare how different repositories implement a pattern"""

    def __init__(self, analyzer: PatternAnalyzer):
        self.analyzer = analyzer

    @property
    def skill_id(self) -> str:
        return "compare_implementations"

    @property
    def skill_name(self) -> str:
        return "Compare Pattern Implementations"

    @property
    def skill_description(self) -> str:
        return "Compare how multiple repositories implement the same pattern to identify best practices and differences"

    @property
    def tags(self) -> List[str]:
        return ["comparison", "patterns", "best-practices"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repositories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of repositories to compare"
                },
                "pattern_type": {
                    "type": "string",
                    "description": "Type of pattern to compare (e.g., 'retry_logic', 'error_handling', 'authentication')"
                }
            },
            "required": ["repositories", "pattern_type"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "repositories": ["patelmm79/web-scraper", "patelmm79/api-client"],
                    "pattern_type": "retry_logic"
                },
                "description": "Compare retry logic implementations across two repos"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare pattern implementations"""
        try:
            repositories = input_data.get("repositories", [])
            pattern_type = input_data.get("pattern_type")

            if not repositories or len(repositories) < 2:
                return {
                    "success": False,
                    "error": "At least 2 repositories required for comparison"
                }

            if not pattern_type:
                return {
                    "success": False,
                    "error": "Missing required field: pattern_type"
                }

            # Analyze each repository for the specific pattern
            implementations = []
            for repo in repositories:
                analysis = await self.analyzer.analyze(
                    repository=repo,
                    focus_areas=[pattern_type]
                )
                implementations.append({
                    "repository": repo,
                    "patterns": analysis.get("patterns", []),
                    "implementation_details": analysis.get("implementation_details", {})
                })

            # Compare implementations
            comparison = await self.analyzer.compare_patterns(
                implementations=implementations,
                pattern_type=pattern_type
            )

            return {
                "success": True,
                "pattern_type": pattern_type,
                "repositories": repositories,
                "implementations": implementations,
                "comparison": comparison,
                "recommendations": comparison.get("recommendations", [])
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Comparison failed: {str(e)}"
            }
```

#### 2.3 Get Pattern Recommendations Skill

```python
# pattern_miner/a2a/skills/analysis.py (continued)

class GetPatternRecommendationsSkill(BaseSkill):
    """Get pattern recommendations for a repository"""

    def __init__(self, analyzer: PatternAnalyzer):
        self.analyzer = analyzer

    @property
    def skill_id(self) -> str:
        return "get_recommendations"

    @property
    def skill_name(self) -> str:
        return "Get Pattern Recommendations"

    @property
    def skill_description(self) -> str:
        return "Get recommendations for patterns to adopt based on repository context and existing patterns"

    @property
    def tags(self) -> List[str]:
        return ["recommendations", "best-practices"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository name in format 'owner/repo'"
                },
                "context": {
                    "type": "object",
                    "description": "Context about the repository",
                    "properties": {
                        "primary_language": {"type": "string"},
                        "frameworks": {"type": "array", "items": {"type": "string"}},
                        "deployment_target": {"type": "string"}
                    }
                }
            },
            "required": ["repository", "context"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "repository": "patelmm79/new-service",
                    "context": {
                        "primary_language": "python",
                        "frameworks": ["fastapi"],
                        "deployment_target": "cloud_run"
                    }
                },
                "description": "Get pattern recommendations for a new Python FastAPI service"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get pattern recommendations"""
        try:
            repository = input_data.get("repository")
            context = input_data.get("context", {})

            if not repository:
                return {
                    "success": False,
                    "error": "Missing required field: repository"
                }

            # Get recommendations based on context
            recommendations = await self.analyzer.get_recommendations(
                repository=repository,
                context=context
            )

            return {
                "success": True,
                "repository": repository,
                "recommendations": recommendations,
                "context": context
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get recommendations: {str(e)}"
            }
```

#### 2.4 Get Analysis Results Skill

```python
# pattern_miner/a2a/skills/results.py

class GetAnalysisResultsSkill(BaseSkill):
    """Retrieve stored analysis results"""

    def __init__(self, storage):
        self.storage = storage

    @property
    def skill_id(self) -> str:
        return "get_analysis_results"

    @property
    def skill_name(self) -> str:
        return "Get Analysis Results"

    @property
    def skill_description(self) -> str:
        return "Retrieve previously stored pattern analysis results"

    @property
    def tags(self) -> List[str]:
        return ["results", "history"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository name (optional, returns all if omitted)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 10
                }
            }
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get stored analysis results"""
        try:
            repository = input_data.get("repository")
            limit = input_data.get("limit", 10)

            if repository:
                results = await self.storage.get_by_repository(repository, limit)
            else:
                results = await self.storage.get_recent(limit)

            return {
                "success": True,
                "results": results,
                "count": len(results)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to retrieve results: {str(e)}"
            }
```

---

### Phase 3: Create A2A Server (45 min)

#### 3.1 Create A2A Server

```python
# pattern_miner/a2a/server.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

from pattern_miner.a2a.registry import get_registry
from pattern_miner.a2a.skills.analysis import (
    AnalyzeRepositorySkill,
    CompareImplementationsSkill,
    GetPatternRecommendationsSkill
)
from pattern_miner.a2a.skills.results import GetAnalysisResultsSkill
from pattern_miner.analyzer import PatternAnalyzer
from pattern_miner.storage import Storage
from pattern_miner.config import load_config

# Load configuration
config = load_config()

# Initialize services
analyzer = PatternAnalyzer(config)
storage = Storage(config)

# Initialize skill registry
registry = get_registry()

# Register all skills
registry.register(AnalyzeRepositorySkill(analyzer))
registry.register(CompareImplementationsSkill(analyzer))
registry.register(GetPatternRecommendationsSkill(analyzer))
registry.register(GetAnalysisResultsSkill(storage))

# Create FastAPI app
app = FastAPI(
    title="Pattern Miner A2A Agent",
    description="Deep pattern analysis and comparison across GitHub repositories",
    version="2.0.0"
)

logger = logging.getLogger("pattern_miner")


@app.get("/.well-known/agent.json")
async def get_agent_card():
    """Publish AgentCard at well-known location"""
    agent_card = {
        "name": "pattern_miner",
        "description": "Deep pattern analysis and comparison across GitHub repositories using Claude AI",
        "version": "2.0.0",
        "url": config.agent_url,
        "capabilities": {
            "streaming": False,
            "multimodal": False,
            "authentication": "optional"
        },
        "skills": registry.to_agent_card_skills(),
        "metadata": {
            "repository": "patelmm79/pattern-miner",
            "focus_areas": [
                "deployment_patterns",
                "api_clients",
                "configuration_management",
                "github_actions",
                "error_handling",
                "retry_logic"
            ],
            "supported_languages": ["python", "javascript", "typescript", "go"],
            "integration_partners": {
                "dev-nexus": "Coordinates with Pattern Discovery Agent for knowledge base updates"
            }
        }
    }

    return JSONResponse(content=agent_card)


@app.post("/a2a/execute")
async def execute_task(request: Request):
    """Handle A2A task execution"""
    try:
        body = await request.json()
        skill_id = body.get("skill_id")
        input_data = body.get("input", {})

        if not skill_id:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing required field: skill_id"}
            )

        # Get skill from registry
        skill = registry.get_skill(skill_id)
        if not skill:
            return JSONResponse(
                status_code=404,
                content={"error": f"Skill not found: {skill_id}"}
            )

        # Execute skill
        result = await skill.execute(input_data)

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Execution failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Execution failed: {str(e)}"}
        )


@app.post("/a2a/cancel")
async def cancel_task(request: Request):
    """Handle A2A task cancellation"""
    try:
        body = await request.json()
        task_id = body.get("task_id")

        if not task_id:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing required field: task_id"}
            )

        # Pattern-miner doesn't support long-running tasks yet
        return JSONResponse(
            content={
                "success": False,
                "message": "Task cancellation not supported"
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Cancellation failed: {str(e)}"}
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "pattern-miner",
        "version": "2.0.0",
        "skills_registered": len(registry.get_skill_ids()),
        "skills": registry.get_skill_ids()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Pattern Miner A2A Agent",
        "version": "2.0.0",
        "agent_card": f"{config.agent_url}/.well-known/agent.json",
        "health": f"{config.agent_url}/health",
        "endpoints": {
            "execute": "/a2a/execute",
            "cancel": "/a2a/cancel",
            "agent_card": "/.well-known/agent.json",
            "health": "/health"
        },
        "skills_registered": len(registry.get_skill_ids()),
        "skills": registry.get_skill_ids()
    }


if __name__ == "__main__":
    import uvicorn
    port = config.port
    print(f"Starting Pattern Miner A2A Agent on port {port}")
    print(f"AgentCard: http://localhost:{port}/.well-known/agent.json")
    print(f"Skills: {', '.join(registry.get_skill_ids())}")
    uvicorn.run(app, host="0.0.0.0", port=port)
```

---

### Phase 4: Update Configuration (15 min)

#### 4.1 Update requirements.txt

```txt
# Add to requirements.txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
```

#### 4.2 Update config.py

```python
# pattern_miner/config.py (add these fields)

class Config:
    # Existing fields...

    # A2A Configuration
    agent_url: str = os.getenv("AGENT_URL", "http://localhost:8080")
    port: int = int(os.getenv("PORT", "8080"))

    # Authentication (optional)
    require_auth: bool = os.getenv("REQUIRE_AUTH", "false").lower() == "true"
    auth_token: str = os.getenv("AUTH_TOKEN", "")
```

#### 4.3 Update .env.example

```bash
# Add to .env.example

# A2A Configuration
AGENT_URL=https://pattern-miner-xxxxxxxxx.a.run.app
PORT=8080
REQUIRE_AUTH=false
AUTH_TOKEN=
```

---

### Phase 5: Update Deployment (15 min)

#### 5.1 Update Dockerfile

```dockerfile
# Keep existing Dockerfile, ensure it runs the A2A server

# Change the CMD to:
CMD ["python", "-m", "uvicorn", "pattern_miner.a2a.server:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### 5.2 Update deploy-gcp.sh

```bash
# deploy-gcp.sh - update environment variables

gcloud run deploy pattern-miner \
  --image gcr.io/${PROJECT_ID}/pattern-miner:latest \
  --region ${REGION} \
  --platform managed \
  --port 8080 \
  --memory 2Gi \
  --cpu 1 \
  --allow-unauthenticated \
  --set-env-vars="AGENT_URL=https://pattern-miner-${PROJECT_ID}.a.run.app" \
  --set-secrets="GITHUB_TOKEN=GITHUB_TOKEN:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest"
```

---

### Phase 6: Update Dev-Nexus Integration (15 min)

#### 6.1 Update dev-nexus integration service

```python
# In dev-nexus: core/integration_service.py

# Update ExternalAgentRegistry configuration
PATTERN_MINER_URL = os.getenv(
    "PATTERN_MINER_URL",
    "https://pattern-miner-xxxxxxxxx.a.run.app"
)

# The existing methods should now work with A2A protocol
# No changes needed - they already expect A2A skills!
```

#### 6.2 Add pattern-miner skills to dev-nexus

The integration skills can now call pattern-miner directly:

```python
# In dev-nexus: a2a/skills/integration.py
# Add new skills that call pattern-miner

class TriggerDeepAnalysisSkill(BaseSkill):
    """Trigger deep pattern analysis via pattern-miner"""

    def __init__(self, integration_service):
        self.integration_service = integration_service

    @property
    def skill_id(self) -> str:
        return "trigger_deep_analysis"

    @property
    def skill_name(self) -> str:
        return "Trigger Deep Pattern Analysis"

    @property
    def skill_description(self) -> str:
        return "Trigger deep pattern analysis on a repository using pattern-miner agent"

    @property
    def tags(self) -> List[str]:
        return ["analysis", "pattern-miner", "deep-dive"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository name in format 'owner/repo'"
                },
                "focus_areas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Areas to focus analysis on"
                }
            },
            "required": ["repository"]
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger pattern-miner analysis"""
        try:
            result = self.integration_service.request_deep_pattern_analysis(
                repository=input_data["repository"],
                focus_areas=input_data.get("focus_areas", [])
            )

            return {
                "success": True,
                **result
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to trigger analysis: {str(e)}"
            }
```

---

## Testing Plan

### Local Testing

1. **Start pattern-miner locally:**
   ```bash
   cd pattern-miner
   python -m pattern_miner.a2a.server
   ```

2. **Test AgentCard:**
   ```bash
   curl http://localhost:8080/.well-known/agent.json | jq
   ```

3. **Test analyze_repository skill:**
   ```bash
   curl -X POST http://localhost:8080/a2a/execute \
     -H "Content-Type: application/json" \
     -d '{
       "skill_id": "analyze_repository",
       "input": {
         "repository": "patelmm79/web-scraper",
         "focus_areas": ["deployment"]
       }
     }' | jq
   ```

4. **Test compare_implementations skill:**
   ```bash
   curl -X POST http://localhost:8080/a2a/execute \
     -H "Content-Type: application/json" \
     -d '{
       "skill_id": "compare_implementations",
       "input": {
         "repositories": ["patelmm79/web-scraper", "patelmm79/api-client"],
         "pattern_type": "retry_logic"
       }
     }' | jq
   ```

### Integration Testing with Dev-Nexus

1. **Test from dev-nexus integration service:**
   ```python
   # In dev-nexus
   from core.integration_service import IntegrationService

   service = IntegrationService()
   result = service.request_deep_pattern_analysis(
       repository="patelmm79/web-scraper"
   )
   print(result)
   ```

2. **Test from frontend via dev-nexus:**
   - Frontend calls dev-nexus skill: `trigger_deep_analysis`
   - Dev-nexus calls pattern-miner A2A skill: `analyze_repository`
   - Verify results flow back correctly

---

## Deployment Steps

### 1. Deploy Pattern-Miner to Cloud Run

```bash
cd pattern-miner
export GCP_PROJECT_ID=globalbiting-dev
bash deploy-gcp.sh
```

### 2. Update Dev-Nexus Environment Variable

```bash
# Add PATTERN_MINER_URL to dev-nexus Cloud Run
gcloud run services update pattern-discovery-agent \
  --region=us-central1 \
  --project=globalbiting-dev \
  --set-env-vars="PATTERN_MINER_URL=https://pattern-miner-globalbiting-dev.a.run.app"
```

### 3. Verify Integration

```bash
# Test pattern-miner health
SERVICE_URL=$(gcloud run services describe pattern-miner --region=us-central1 --format="value(status.url)")
curl ${SERVICE_URL}/health | jq

# Test AgentCard
curl ${SERVICE_URL}/.well-known/agent.json | jq

# Test from dev-nexus
DEV_NEXUS_URL=$(gcloud run services describe pattern-discovery-agent --region=us-central1 --format="value(status.url)")
curl -X POST ${DEV_NEXUS_URL}/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "trigger_deep_analysis",
    "input": {"repository": "patelmm79/web-scraper"}
  }' | jq
```

---

## Migration Notes

### Breaking Changes

- REST API endpoints (`/api/mine-patterns`, `/api/patterns`) will be removed
- New A2A protocol endpoints: `/a2a/execute`, `/.well-known/agent.json`
- Clients must update to use A2A protocol

### Backward Compatibility (Optional)

If you need to support old REST API temporarily:

```python
# pattern_miner/a2a/server.py (add legacy endpoints)

@app.post("/api/mine-patterns")
async def legacy_mine_patterns(request: Request):
    """Legacy REST API endpoint - redirects to A2A"""
    body = await request.json()

    # Convert REST request to A2A format
    a2a_request = {
        "skill_id": "analyze_repository",
        "input": body
    }

    # Call A2A endpoint internally
    return await execute_task(Request(
        scope={"type": "http", "method": "POST"},
        receive=lambda: {"body": json.dumps(a2a_request).encode()}
    ))
```

---

## Rollback Plan

If conversion fails:

1. **Revert to previous deployment:**
   ```bash
   gcloud run services update pattern-miner \
     --image gcr.io/${PROJECT_ID}/pattern-miner:previous-version
   ```

2. **Keep old REST API branch:**
   ```bash
   # Before starting conversion
   git checkout -b rest-api-backup
   git push origin rest-api-backup
   ```

3. **Feature flag for A2A:**
   ```python
   # config.py
   USE_A2A_PROTOCOL = os.getenv("USE_A2A", "true").lower() == "true"
   ```

---

## Success Criteria

- ✅ AgentCard accessible at `/.well-known/agent.json`
- ✅ All 4 skills working via `/a2a/execute`
- ✅ Dev-nexus can call pattern-miner successfully
- ✅ Frontend can trigger analysis via dev-nexus
- ✅ Health check shows all skills registered
- ✅ Existing pattern analysis logic still works
- ✅ GitHub issue creation still functions

---

## Next Steps After Conversion

1. **Add pattern-miner to frontend UI:**
   - Add "Deep Analysis" button in repository view
   - Show pattern-miner results in comparison view

2. **Convert dependency-orchestrator to A2A:**
   - Follow same pattern as pattern-miner
   - Create unified A2A agent ecosystem

3. **Add authentication:**
   - Implement A2A authentication tokens
   - Protect sensitive skills

4. **Add caching:**
   - Cache analysis results in Redis/PostgreSQL
   - Avoid re-analyzing same repository

5. **Add webhooks:**
   - Trigger analysis on git push
   - Automatic pattern discovery

---

## Estimated Timeline

| Phase | Task | Time | Total |
|-------|------|------|-------|
| 1 | Add A2A Foundation | 30 min | 30 min |
| 2 | Create A2A Skills | 60 min | 1.5 hrs |
| 3 | Create A2A Server | 45 min | 2.25 hrs |
| 4 | Update Configuration | 15 min | 2.5 hrs |
| 5 | Update Deployment | 15 min | 2.75 hrs |
| 6 | Update Dev-Nexus | 15 min | 3 hrs |
| Testing | Local + Integration | 30 min | 3.5 hrs |
| Deployment | Deploy + Verify | 15 min | 3.75 hrs |

**Total: ~4 hours** (including testing and deployment)

---

## Resources

- **A2A Protocol Spec:** Reference dev-nexus implementation
- **Dev-Nexus Skills:** See `a2a/skills/` for examples
- **Integration Service:** See `core/integration_service.py`
- **Agent Registry:** See `a2a/client.py`

---

## Questions?

Contact: Pattern Discovery Team
Repository: patelmm79/pattern-miner
Integration: patelmm79/dev-nexus
