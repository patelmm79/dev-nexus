# Dependency-Orchestrator A2A Conversion Plan

## Overview

Convert dependency-orchestrator from REST API + webhook service to A2A (Agent-to-Agent) protocol agent with bidirectional communication, PostgreSQL-based async task management, and backward compatibility.

**Estimated Time:** 7.5 hours (reduced from 8 hours - no Redis setup needed)
**Difficulty:** Medium-High
**Breaking Changes:** No (legacy webhooks supported)
**Prerequisites:**
- Pattern-miner A2A conversion complete (for reference)
- PostgreSQL database accessible (shared with dev-nexus at 10.8.0.2)

---

## Current State Analysis

### Existing Architecture

```
dependency-orchestrator/
├── orchestrator/          # Core package
│   ├── __init__.py
│   ├── api.py            # FastAPI REST endpoints (CONVERT)
│   ├── config.py         # Configuration (EXTEND)
│   ├── models.py         # Data models (REUSE)
│   ├── agents/           # Triage agents (INTEGRATE)
│   │   ├── consumer_triage.py
│   │   └── template_triage.py
│   ├── services/         # Business logic (REUSE)
│   │   ├── dependency_graph.py
│   │   └── impact_analyzer.py
│   └── storage/          # Persistence (EXTEND)
│       └── relationships.py
├── .env.example
├── Dockerfile
└── requirements.txt
```

### Current REST API Endpoints

1. **POST /api/webhook/change-notification**
   - Receives CI/CD notifications
   - Maps to: `receive_change_notification` A2A skill
   - Keep for backward compatibility

2. **GET /api/relationships**
   - Lists all dependencies
   - Maps to: Multiple query skills

3. **GET /api/relationships/{owner}/{repo}**
   - Get specific repo dependencies
   - Maps to: `get_dependencies` A2A skill

### Key Complexity Factors

| Factor | Complexity | Solution |
|--------|-----------|----------|
| **Bidirectional** | High | A2A client to call dev-nexus |
| **Async Tasks** | Medium | PostgreSQL-based task queue |
| **State Management** | Low | PostgreSQL (shared with dev-nexus) |
| **Webhook Compat** | Medium | Dual endpoints (webhook + A2A) |
| **Triage Agents** | Medium | Wrap as internal services |

---

## Conversion Plan

### Phase 1: Add A2A Foundation (45 min)

#### 1.1 Create Base A2A Structure

```python
# orchestrator/a2a/__init__.py
"""A2A Protocol Support for Dependency Orchestrator"""

# orchestrator/a2a/base.py
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from datetime import datetime

class BaseSkill(ABC):
    """Base class for Dependency Orchestrator A2A skills"""

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
        """
        Execute the skill

        Returns:
            Dict with at minimum:
            - success: bool
            - task_id: str (if async)
            - status: str (if async: "queued", "processing", "completed")
        """
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
# orchestrator/a2a/registry.py
from typing import Dict, List
from orchestrator.a2a.base import BaseSkill

class SkillRegistry:
    """Registry for all A2A skills"""

    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
        self._protected_skills: set = set()

    def register(self, skill: BaseSkill, protected: bool = False):
        """Register a skill, optionally marking it as protected (requires auth)"""
        self._skills[skill.skill_id] = skill
        if protected or skill.requires_authentication:
            self._protected_skills.add(skill.skill_id)

    def get_skill(self, skill_id: str) -> BaseSkill:
        return self._skills.get(skill_id)

    def is_protected(self, skill_id: str) -> bool:
        return skill_id in self._protected_skills

    def get_skill_ids(self) -> List[str]:
        return list(self._skills.keys())

    def to_agent_card_skills(self) -> List[Dict]:
        return [skill.to_agent_card_entry() for skill in self._skills.values()]

# Global registry
_registry = None

def get_registry() -> SkillRegistry:
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry
```

#### 1.3 Create A2A Client for Calling Dev-Nexus

```python
# orchestrator/a2a/client.py
import httpx
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class A2AClient:
    """Client for calling other A2A agents"""

    def __init__(self, agent_url: str, auth_token: Optional[str] = None):
        self.agent_url = agent_url.rstrip('/')
        self.auth_token = auth_token
        self.timeout = 60.0

    async def execute_skill(
        self,
        skill_id: str,
        input_data: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute a skill on a remote A2A agent

        Args:
            skill_id: The skill to execute
            input_data: Input parameters for the skill
            timeout: Request timeout (default: 60s)

        Returns:
            Skill execution result
        """
        url = f"{self.agent_url}/a2a/execute"
        headers = {"Content-Type": "application/json"}

        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        payload = {
            "skill_id": skill_id,
            "input": input_data
        }

        try:
            async with httpx.AsyncClient(timeout=timeout or self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"A2A call failed: {e}")
            return {
                "success": False,
                "error": f"A2A communication failed: {str(e)}"
            }

    async def get_agent_card(self) -> Dict[str, Any]:
        """Fetch the AgentCard from a remote agent"""
        url = f"{self.agent_url}/.well-known/agent.json"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch AgentCard: {e}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """Check health of remote agent"""
        url = f"{self.agent_url}/health"

        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Agent registry
class ExternalAgentRegistry:
    """Registry of external A2A agents"""

    def __init__(self):
        self._agents: Dict[str, A2AClient] = {}

    def register_agent(self, name: str, url: str, auth_token: Optional[str] = None):
        """Register an external agent"""
        self._agents[name] = A2AClient(url, auth_token)

    def get_agent(self, name: str) -> Optional[A2AClient]:
        """Get an agent by name"""
        return self._agents.get(name)

    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all registered agents"""
        results = {}
        for name, agent in self._agents.items():
            health = await agent.health_check()
            results[name] = health.get("status") == "healthy"
        return results
```

---

### Phase 2: Add Async Task Management (60 min)

#### 2.1 Task Queue Selection

**Decision: Use PostgreSQL** (same database as dev-nexus)

**Reasons:**
- ✅ **$0 additional cost** (PostgreSQL already deployed)
- ✅ **Persistent tasks** (survive restarts)
- ✅ **Unified database** (same as patterns/knowledge base)
- ✅ **Rich querying** (complex SQL queries on task state)
- ✅ **Transaction support** (consistent state updates)
- ✅ **Sufficient performance** (10-50 tasks/hour is moderate load)

**No additional dependencies needed** - uses existing PostgreSQL instance.

#### 2.2 Database Migration

```sql
-- Create orchestration_tasks table
CREATE TABLE orchestration_tasks (
    task_id VARCHAR(20) PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL,
    repository VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- queued, processing, completed, failed
    input_data JSONB NOT NULL,
    result JSONB,
    error TEXT,
    worker_id VARCHAR(50),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_tasks_status_created ON orchestration_tasks(status, created_at)
    WHERE status = 'queued';  -- Partial index for fast dequeue

CREATE INDEX idx_tasks_repository ON orchestration_tasks(repository);

CREATE INDEX idx_tasks_completed_at ON orchestration_tasks(completed_at)
    WHERE status IN ('completed', 'failed');  -- For cleanup
```

#### 2.3 Create PostgreSQL Task Manager

```python
# orchestrator/tasks/postgres_queue.py
import uuid
import json
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class PostgresTaskQueue:
    """
    PostgreSQL-based task queue for orchestration

    Uses SELECT FOR UPDATE SKIP LOCKED for atomic dequeue
    """

    def __init__(self, db_manager):
        self.db = db_manager

    async def create_task(
        self,
        task_type: str,
        repository: str,
        input_data: Dict[str, Any]
    ) -> str:
        """
        Create a new task and add to queue

        Returns:
            task_id: Unique task identifier
        """
        task_id = f"orch_{uuid.uuid4().hex[:12]}"

        query = """
            INSERT INTO orchestration_tasks (
                task_id, task_type, repository, status,
                input_data, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $6)
            RETURNING task_id
        """

        await self.db.execute(
            query,
            task_id, task_type, repository, TaskStatus.QUEUED.value,
            json.dumps(input_data), datetime.now()
        )

        return task_id

    async def dequeue_task(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """
        Atomic dequeue - get next pending task and mark as processing

        Uses SELECT FOR UPDATE SKIP LOCKED for safe concurrent dequeuing
        Multiple workers can call this simultaneously without conflicts
        """
        query = """
            UPDATE orchestration_tasks
            SET
                status = $1,
                worker_id = $2,
                started_at = $3,
                updated_at = $3
            WHERE task_id = (
                SELECT task_id
                FROM orchestration_tasks
                WHERE status = $4
                ORDER BY created_at ASC
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            RETURNING task_id, task_type, repository, input_data
        """

        row = await self.db.fetchrow(
            query,
            TaskStatus.PROCESSING.value,
            worker_id,
            datetime.now(),
            TaskStatus.QUEUED.value
        )

        if row:
            return {
                "task_id": row["task_id"],
                "task_type": row["task_type"],
                "repository": row["repository"],
                "input_data": json.loads(row["input_data"])
            }
        return None

    async def update_task(
        self,
        task_id: str,
        status: TaskStatus,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        """Update task status and result"""
        query = """
            UPDATE orchestration_tasks
            SET
                status = $1,
                result = $2,
                error = $3,
                completed_at = $4,
                updated_at = $5
            WHERE task_id = $6
        """

        now = datetime.now()
        completed_at = now if status in [TaskStatus.COMPLETED, TaskStatus.FAILED] else None

        await self.db.execute(
            query,
            status.value,
            json.dumps(result) if result else None,
            error,
            completed_at,
            now,
            task_id
        )

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        query = """
            SELECT
                task_id, task_type, repository, status,
                input_data, result, error,
                created_at, started_at, completed_at, updated_at,
                worker_id
            FROM orchestration_tasks
            WHERE task_id = $1
        """

        row = await self.db.fetchrow(query, task_id)
        if row:
            task_dict = dict(row)
            # Parse JSON fields
            if task_dict.get("input_data"):
                task_dict["input_data"] = json.loads(task_dict["input_data"])
            if task_dict.get("result"):
                task_dict["result"] = json.loads(task_dict["result"])
            return task_dict
        return None

    async def cleanup_old_tasks(self, days: int = 7):
        """Delete completed tasks older than N days"""
        query = """
            DELETE FROM orchestration_tasks
            WHERE
                status IN ($1, $2)
                AND completed_at < NOW() - INTERVAL '%s days'
        """ % days

        result = await self.db.execute(
            query,
            TaskStatus.COMPLETED.value,
            TaskStatus.FAILED.value
        )

        return result

    async def get_task_stats(self) -> Dict[str, int]:
        """Get task queue statistics"""
        query = """
            SELECT
                status,
                COUNT(*) as count
            FROM orchestration_tasks
            GROUP BY status
        """

        rows = await self.db.fetch(query)
        stats = {row["status"]: row["count"] for row in rows}

        return {
            "queued": stats.get(TaskStatus.QUEUED.value, 0),
            "processing": stats.get(TaskStatus.PROCESSING.value, 0),
            "completed": stats.get(TaskStatus.COMPLETED.value, 0),
            "failed": stats.get(TaskStatus.FAILED.value, 0),
            "total": sum(stats.values())
        }
```

#### 2.4 Create Worker Loop

```python
# orchestrator/tasks/worker.py
import asyncio
import logging
from typing import Dict, Any
from orchestrator.services.impact_analyzer import ImpactAnalyzer
from orchestrator.services.dependency_graph import DependencyGraph
from orchestrator.agents.consumer_triage import ConsumerTriageAgent
from orchestrator.agents.template_triage import TemplateTriageAgent
from orchestrator.tasks.postgres_queue import PostgresTaskQueue, TaskStatus
from orchestrator.a2a.client import ExternalAgentRegistry

logger = logging.getLogger(__name__)

async def run_impact_analysis(
    task_id: str,
    repository: str,
    change_data: Dict[str, Any],
    queue: PostgresTaskQueue
) -> Dict[str, Any]:
    """
    Core orchestration logic for impact analysis

    Steps:
    1. Loads dependency graph
    2. Queries dev-nexus for pattern details
    3. Runs triage agents
    4. Creates GitHub issues
    5. Reports back to dev-nexus
    """

    try:
        # 1. Load dependency graph
        dep_graph = DependencyGraph()
        consumers = dep_graph.get_consumers(repository)

        logger.info(f"Found {len(consumers)} consumers for {repository}")

        # 2. Query dev-nexus for full pattern details
        agent_registry = ExternalAgentRegistry()
        dev_nexus = agent_registry.get_agent("dev-nexus")

        if dev_nexus:
            pattern_details = await dev_nexus.execute_skill(
                skill_id="get_deployment_info",
                input_data={"repository": repository}
            )
        else:
            pattern_details = {}

        # 3. Run consumer triage
        consumer_agent = ConsumerTriageAgent()
        triage_results = []

        for consumer in consumers:
            result = await consumer_agent.analyze_impact(
                provider_repo=repository,
                consumer_repo=consumer["repository"],
                change_data=change_data,
                pattern_details=pattern_details
            )
            triage_results.append(result)

        # 4. Create GitHub issues in affected repos
        issues_created = []
        for triage in triage_results:
            if triage["has_breaking_changes"]:
                issue = await create_github_issue(
                    repository=triage["consumer_repo"],
                    title=f"⚠️ Breaking change detected in {repository}",
                    body=triage["issue_body"]
                )
                issues_created.append(issue)

        # 5. Report back to dev-nexus (add lesson learned)
        if dev_nexus and issues_created:
            await dev_nexus.execute_skill(
                skill_id="add_lesson_learned",
                input_data={
                    "repository": repository,
                    "category": "reliability",
                    "lesson": f"Change affected {len(consumers)} downstream consumers",
                    "context": f"Breaking changes detected. Created {len(issues_created)} issues.",
                    "severity": "warning"
                }
            )

        # 6. Update task with results
        result = {
            "repository": repository,
            "consumers_analyzed": len(consumers),
            "issues_created": len(issues_created),
            "triage_results": triage_results,
            "affected_repos": [t["consumer_repo"] for t in triage_results if t["has_breaking_changes"]]
        }

        await queue.update_task(task_id, TaskStatus.COMPLETED, result=result)
        return result

    except Exception as e:
        logger.error(f"Impact analysis failed: {e}", exc_info=True)
        await queue.update_task(task_id, TaskStatus.FAILED, error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


async def create_github_issue(
    repository: str,
    title: str,
    body: str
) -> Dict[str, Any]:
    """Create a GitHub issue (placeholder - implement with PyGithub)"""
    # TODO: Implement with PyGithub
    return {
        "repository": repository,
        "issue_url": f"https://github.com/{repository}/issues/1",
        "title": title
    }


async def worker_loop(
    worker_id: str,
    queue: PostgresTaskQueue,
    poll_interval: int = 5
):
    """
    Async worker loop - continuously processes tasks from PostgreSQL queue

    Args:
        worker_id: Unique identifier for this worker
        queue: PostgresTaskQueue instance
        poll_interval: Seconds to wait between polling (default: 5)
    """
    logger.info(f"Worker {worker_id} starting...")

    while True:
        try:
            # Dequeue next task (atomic operation)
            task = await queue.dequeue_task(worker_id)

            if task:
                logger.info(f"Worker {worker_id} processing task {task['task_id']}")

                # Route to appropriate handler based on task_type
                if task["task_type"] == "impact_analysis":
                    await run_impact_analysis(
                        task_id=task["task_id"],
                        repository=task["repository"],
                        change_data=task["input_data"],
                        queue=queue
                    )
                else:
                    logger.warning(f"Unknown task type: {task['task_type']}")
                    await queue.update_task(
                        task["task_id"],
                        TaskStatus.FAILED,
                        error=f"Unknown task type: {task['task_type']}"
                    )
            else:
                # No tasks available, wait before polling again
                await asyncio.sleep(poll_interval)

        except Exception as e:
            logger.error(f"Worker {worker_id} error: {e}", exc_info=True)
            await asyncio.sleep(poll_interval)


async def start_workers(num_workers: int = 2):
    """
    Start multiple async workers

    Args:
        num_workers: Number of concurrent workers (default: 2)
    """
    from orchestrator.database import get_db_manager

    db_manager = get_db_manager()
    queue = PostgresTaskQueue(db_manager)

    # Create worker tasks
    workers = [
        asyncio.create_task(worker_loop(f"worker-{i}", queue))
        for i in range(num_workers)
    ]

    logger.info(f"Started {num_workers} workers")

    # Run forever
    await asyncio.gather(*workers)
```

---

### Phase 3: Create A2A Skills (90 min)

#### 3.1 Event Handler Skill (Primary Entry Point)

```python
# orchestrator/a2a/skills/events.py
from typing import Dict, Any, List
from orchestrator.a2a.base import BaseSkill
from orchestrator.tasks.postgres_queue import PostgresTaskQueue

class ReceiveChangeNotificationSkill(BaseSkill):
    """Receive and process change notifications from dev-nexus"""

    def __init__(self, task_queue: PostgresTaskQueue):
        self.task_queue = task_queue

    @property
    def skill_id(self) -> str:
        return "receive_change_notification"

    @property
    def skill_name(self) -> str:
        return "Receive Change Notification"

    @property
    def skill_description(self) -> str:
        return "Receive notification of repository changes and trigger impact analysis"

    @property
    def tags(self) -> List[str]:
        return ["events", "coordination", "async"]

    @property
    def requires_authentication(self) -> bool:
        return True  # Only dev-nexus should call this

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository that changed (owner/repo)"
                },
                "commit_sha": {
                    "type": "string",
                    "description": "Git commit SHA"
                },
                "timestamp": {
                    "type": "string",
                    "description": "ISO 8601 timestamp"
                },
                "patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Pattern names that changed"
                },
                "dependencies": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Dependencies that changed"
                },
                "change_type": {
                    "type": "string",
                    "enum": ["pattern_change", "dependency_update", "breaking_change"],
                    "description": "Type of change"
                }
            },
            "required": ["repository", "commit_sha", "timestamp"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "repository": "patelmm79/api-service",
                    "commit_sha": "abc123def",
                    "timestamp": "2025-01-15T10:30:00Z",
                    "patterns": ["retry_with_exponential_backoff"],
                    "change_type": "pattern_change"
                },
                "description": "Notify of pattern change in API service"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Receive change notification and queue impact analysis

        Returns immediately with task_id for async processing
        """
        try:
            repository = input_data.get("repository")
            commit_sha = input_data.get("commit_sha")

            if not repository or not commit_sha:
                return {
                    "success": False,
                    "error": "Missing required fields: repository, commit_sha"
                }

            # Create task in PostgreSQL queue
            task_id = await self.task_queue.create_task(
                task_type="impact_analysis",
                repository=repository,
                input_data=input_data
            )

            return {
                "success": True,
                "task_id": task_id,
                "status": "queued",
                "message": f"Impact analysis queued for {repository}",
                "estimated_completion": "2-5 minutes"
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process notification: {str(e)}"
            }
```

#### 3.2 Query Skills

```python
# orchestrator/a2a/skills/queries.py

class GetImpactAnalysisSkill(BaseSkill):
    """Get impact analysis for a repository change"""

    def __init__(self, dependency_graph, impact_analyzer):
        self.dep_graph = dependency_graph
        self.impact_analyzer = impact_analyzer

    @property
    def skill_id(self) -> str:
        return "get_impact_analysis"

    @property
    def skill_name(self) -> str:
        return "Get Impact Analysis"

    @property
    def skill_description(self) -> str:
        return "Get immediate impact analysis of a repository change (synchronous, cached results)"

    @property
    def tags(self) -> List[str]:
        return ["query", "impact", "analysis"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository name (owner/repo)"
                },
                "change_type": {
                    "type": "string",
                    "description": "Type of change"
                }
            },
            "required": ["repository"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "repository": "patelmm79/api-service",
                    "change_type": "breaking_change"
                },
                "description": "Get impact of breaking changes"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get impact analysis (synchronous)"""
        try:
            repository = input_data.get("repository")
            change_type = input_data.get("change_type", "unknown")

            if not repository:
                return {
                    "success": False,
                    "error": "Missing required field: repository"
                }

            # Get consumers from dependency graph
            consumers = self.dep_graph.get_consumers(repository)

            # Get impact severity
            impact = await self.impact_analyzer.estimate_impact(
                repository=repository,
                change_type=change_type,
                consumers=consumers
            )

            return {
                "success": True,
                "repository": repository,
                "change_type": change_type,
                "affected_repos": [c["repository"] for c in consumers],
                "impact_severity": impact["severity"],
                "estimated_issues": impact["estimated_issues"],
                "recommendations": impact["recommendations"]
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get impact analysis: {str(e)}"
            }


class GetDependenciesSkill(BaseSkill):
    """Get dependency graph for a repository"""

    def __init__(self, dependency_graph):
        self.dep_graph = dependency_graph

    @property
    def skill_id(self) -> str:
        return "get_dependencies"

    @property
    def skill_name(self) -> str:
        return "Get Dependencies"

    @property
    def skill_description(self) -> str:
        return "Get full dependency graph (consumers, providers, templates) for a repository"

    @property
    def tags(self) -> List[str]:
        return ["query", "dependencies", "graph"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository name (owner/repo)"
                }
            },
            "required": ["repository"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {"repository": "patelmm79/api-service"},
                "description": "Get all dependencies for api-service"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get dependency graph"""
        try:
            repository = input_data.get("repository")

            if not repository:
                return {
                    "success": False,
                    "error": "Missing required field: repository"
                }

            # Get all relationships
            consumers = self.dep_graph.get_consumers(repository)
            providers = self.dep_graph.get_providers(repository)
            templates = self.dep_graph.get_template_relationships(repository)

            return {
                "success": True,
                "repository": repository,
                "consumers": consumers,
                "providers": providers,
                "template_relationships": templates,
                "total_dependencies": len(consumers) + len(providers)
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get dependencies: {str(e)}"
            }


class GetOrchestrationStatusSkill(BaseSkill):
    """Get status of async orchestration task"""

    def __init__(self, task_queue: PostgresTaskQueue):
        self.task_queue = task_queue

    @property
    def skill_id(self) -> str:
        return "get_orchestration_status"

    @property
    def skill_name(self) -> str:
        return "Get Orchestration Status"

    @property
    def skill_description(self) -> str:
        return "Check status and results of an async orchestration task"

    @property
    def tags(self) -> List[str]:
        return ["query", "status", "async"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Task ID returned from receive_change_notification"
                }
            },
            "required": ["task_id"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {"task_id": "orch_abc123"},
                "description": "Check status of impact analysis task"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get task status"""
        try:
            task_id = input_data.get("task_id")

            if not task_id:
                return {
                    "success": False,
                    "error": "Missing required field: task_id"
                }

            task = await self.task_queue.get_task(task_id)

            if not task:
                return {
                    "success": False,
                    "error": f"Task not found: {task_id}"
                }

            return {
                "success": True,
                "task_id": task_id,
                "status": task["status"],
                "created_at": str(task["created_at"]),
                "updated_at": str(task["updated_at"]),
                "result": task.get("result"),
                "error": task.get("error")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get task status: {str(e)}"
            }
```

#### 3.3 Action Skills (Triage Triggers)

```python
# orchestrator/a2a/skills/actions.py

class TriggerConsumerTriageSkill(BaseSkill):
    """Manually trigger consumer impact triage"""

    def __init__(self, consumer_triage_agent, task_manager):
        self.triage_agent = consumer_triage_agent
        self.task_manager = task_manager

    @property
    def skill_id(self) -> str:
        return "trigger_consumer_triage"

    @property
    def skill_name(self) -> str:
        return "Trigger Consumer Triage"

    @property
    def skill_description(self) -> str:
        return "Manually trigger consumer impact analysis for specific provider changes"

    @property
    def tags(self) -> List[str]:
        return ["action", "triage", "consumer"]

    @property
    def requires_authentication(self) -> bool:
        return True

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "provider_repo": {
                    "type": "string",
                    "description": "Provider repository (owner/repo)"
                },
                "consumer_repos": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Consumer repositories to analyze"
                },
                "change_description": {
                    "type": "string",
                    "description": "Description of the change"
                }
            },
            "required": ["provider_repo", "consumer_repos"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "provider_repo": "patelmm79/api-service",
                    "consumer_repos": ["patelmm79/web-app", "patelmm79/mobile-app"],
                    "change_description": "Breaking change in /auth endpoint"
                },
                "description": "Analyze impact on consumers"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger consumer triage"""
        try:
            provider_repo = input_data.get("provider_repo")
            consumer_repos = input_data.get("consumer_repos", [])
            change_desc = input_data.get("change_description", "Manual triage")

            if not provider_repo or not consumer_repos:
                return {
                    "success": False,
                    "error": "Missing required fields: provider_repo, consumer_repos"
                }

            # Run triage for each consumer
            triage_results = []
            for consumer_repo in consumer_repos:
                result = await self.triage_agent.analyze_impact(
                    provider_repo=provider_repo,
                    consumer_repo=consumer_repo,
                    change_data={"description": change_desc}
                )
                triage_results.append(result)

            return {
                "success": True,
                "provider_repo": provider_repo,
                "consumers_analyzed": len(consumer_repos),
                "triage_results": triage_results,
                "breaking_changes_found": sum(1 for r in triage_results if r.get("has_breaking_changes"))
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Triage failed: {str(e)}"
            }


class TriggerTemplateTriageSkill(BaseSkill):
    """Trigger template improvement propagation"""

    def __init__(self, template_triage_agent, task_manager):
        self.triage_agent = template_triage_agent
        self.task_manager = task_manager

    @property
    def skill_id(self) -> str:
        return "trigger_template_triage"

    @property
    def skill_name(self) -> str:
        return "Trigger Template Triage"

    @property
    def skill_description(self) -> str:
        return "Propagate template improvements to derivative repositories"

    @property
    def tags(self) -> List[str]:
        return ["action", "triage", "template"]

    @property
    def requires_authentication(self) -> bool:
        return True

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "template_repo": {
                    "type": "string",
                    "description": "Template repository (owner/repo)"
                },
                "derivative_repos": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Derivative repositories"
                },
                "improvement_description": {
                    "type": "string",
                    "description": "Description of improvement"
                }
            },
            "required": ["template_repo", "derivative_repos"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "template_repo": "patelmm79/service-template",
                    "derivative_repos": ["patelmm79/service-a", "patelmm79/service-b"],
                    "improvement_description": "New deployment pattern with health checks"
                },
                "description": "Propagate deployment pattern to services"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger template triage"""
        try:
            template_repo = input_data.get("template_repo")
            derivative_repos = input_data.get("derivative_repos", [])
            improvement_desc = input_data.get("improvement_description", "Template improvement")

            if not template_repo or not derivative_repos:
                return {
                    "success": False,
                    "error": "Missing required fields: template_repo, derivative_repos"
                }

            # Run triage for each derivative
            triage_results = []
            for derivative_repo in derivative_repos:
                result = await self.triage_agent.analyze_propagation(
                    template_repo=template_repo,
                    derivative_repo=derivative_repo,
                    improvement_data={"description": improvement_desc}
                )
                triage_results.append(result)

            return {
                "success": True,
                "template_repo": template_repo,
                "derivatives_analyzed": len(derivative_repos),
                "triage_results": triage_results,
                "propagation_recommended": sum(1 for r in triage_results if r.get("should_propagate"))
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Template triage failed: {str(e)}"
            }
```

#### 3.4 Management Skills

```python
# orchestrator/a2a/skills/management.py

class AddDependencyRelationshipSkill(BaseSkill):
    """Add or update dependency relationship"""

    def __init__(self, dependency_graph):
        self.dep_graph = dependency_graph

    @property
    def skill_id(self) -> str:
        return "add_dependency_relationship"

    @property
    def skill_name(self) -> str:
        return "Add Dependency Relationship"

    @property
    def skill_description(self) -> str:
        return "Register or update a dependency relationship between repositories"

    @property
    def tags(self) -> List[str]:
        return ["management", "dependencies"]

    @property
    def requires_authentication(self) -> bool:
        return True

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Source repository (consumer/derivative)"
                },
                "target": {
                    "type": "string",
                    "description": "Target repository (provider/template)"
                },
                "relationship_type": {
                    "type": "string",
                    "enum": ["consumer", "derivative", "template"],
                    "description": "Type of relationship"
                },
                "dependency_strength": {
                    "type": "string",
                    "enum": ["strong", "medium", "weak"],
                    "default": "medium"
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata"
                }
            },
            "required": ["source", "target", "relationship_type"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "source": "patelmm79/web-app",
                    "target": "patelmm79/api-service",
                    "relationship_type": "consumer",
                    "dependency_strength": "strong"
                },
                "description": "Register web-app as consumer of api-service"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add dependency relationship"""
        try:
            source = input_data.get("source")
            target = input_data.get("target")
            rel_type = input_data.get("relationship_type")
            strength = input_data.get("dependency_strength", "medium")

            if not all([source, target, rel_type]):
                return {
                    "success": False,
                    "error": "Missing required fields: source, target, relationship_type"
                }

            # Add to graph
            await self.dep_graph.add_relationship(
                source=source,
                target=target,
                relationship_type=rel_type,
                strength=strength,
                metadata=input_data.get("metadata", {})
            )

            return {
                "success": True,
                "message": f"Added {rel_type} relationship: {source} → {target}",
                "relationship": {
                    "source": source,
                    "target": target,
                    "type": rel_type,
                    "strength": strength
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to add relationship: {str(e)}"
            }
```

---

### Phase 4: Create A2A Server (60 min)

#### 4.1 Main A2A Server

```python
# orchestrator/a2a/server.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging
import asyncio

from orchestrator.a2a.registry import get_registry
from orchestrator.a2a.client import ExternalAgentRegistry
from orchestrator.a2a.skills.events import ReceiveChangeNotificationSkill
from orchestrator.a2a.skills.queries import (
    GetImpactAnalysisSkill,
    GetDependenciesSkill,
    GetOrchestrationStatusSkill
)
from orchestrator.a2a.skills.actions import (
    TriggerConsumerTriageSkill,
    TriggerTemplateTriageSkill
)
from orchestrator.a2a.skills.management import AddDependencyRelationshipSkill
from orchestrator.config import load_config
from orchestrator.tasks.postgres_queue import PostgresTaskQueue
from orchestrator.tasks.worker import start_workers
from orchestrator.database import DatabaseManager, get_db_manager
from orchestrator.services.dependency_graph import DependencyGraph
from orchestrator.services.impact_analyzer import ImpactAnalyzer
from orchestrator.agents.consumer_triage import ConsumerTriageAgent
from orchestrator.agents.template_triage import TemplateTriageAgent

# Load configuration
config = load_config()

# Initialize database manager (PostgreSQL)
db_manager = DatabaseManager()

# Initialize task queue (PostgreSQL-based)
task_queue = PostgresTaskQueue(db_manager)

# Initialize services
dependency_graph = DependencyGraph(config)
impact_analyzer = ImpactAnalyzer(config)
consumer_triage = ConsumerTriageAgent(config)
template_triage = TemplateTriageAgent(config)

# Initialize external agent registry
agent_registry = ExternalAgentRegistry()
agent_registry.register_agent(
    "dev-nexus",
    config.dev_nexus_url,
    config.dev_nexus_auth_token
)

# Initialize skill registry
registry = get_registry()

# Register all skills
registry.register(ReceiveChangeNotificationSkill(task_queue), protected=True)
registry.register(GetImpactAnalysisSkill(dependency_graph, impact_analyzer))
registry.register(GetDependenciesSkill(dependency_graph))
registry.register(GetOrchestrationStatusSkill(task_queue))
registry.register(TriggerConsumerTriageSkill(consumer_triage, task_queue), protected=True)
registry.register(TriggerTemplateTriageSkill(template_triage, task_queue), protected=True)
registry.register(AddDependencyRelationshipSkill(dependency_graph), protected=True)

# Create FastAPI app
app = FastAPI(
    title="Dependency Orchestrator A2A Agent",
    description="AI-powered dependency coordination and impact analysis",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("orchestrator")

# Background worker task (will be started in startup event)
worker_task = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global worker_task
    try:
        # Connect to PostgreSQL
        if db_manager.enabled:
            print("Initializing PostgreSQL connection...")
            await db_manager.connect()
            health = await db_manager.health_check()
            if health["status"] == "healthy":
                print(f"✓ PostgreSQL connected: {health.get('version', 'unknown')}")
            else:
                print(f"⚠ PostgreSQL health check failed: {health}")
                raise RuntimeError("PostgreSQL health check failed")
        else:
            print("ERROR: PostgreSQL is disabled")
            raise RuntimeError("PostgreSQL must be enabled")

        # Start background workers
        print("Starting background workers...")
        worker_task = asyncio.create_task(start_workers(num_workers=2))
        print("✓ Background workers started (2 workers)")

    except Exception as e:
        print(f"FATAL: Failed to initialize services: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global worker_task
    try:
        # Cancel worker tasks
        if worker_task:
            worker_task.cancel()
            try:
                await worker_task
            except asyncio.CancelledError:
                pass
            print("✓ Workers stopped")

        # Disconnect from database
        await db_manager.disconnect()
        print("✓ Database connections closed")

    except Exception as e:
        print(f"Error during shutdown: {e}")


@app.get("/.well-known/agent.json")
async def get_agent_card():
    """Publish AgentCard"""
    agent_card = {
        "name": "dependency_orchestrator",
        "description": "AI-powered dependency coordination and impact analysis across GitHub repositories",
        "version": "2.0.0",
        "url": config.agent_url,
        "capabilities": {
            "streaming": False,
            "multimodal": False,
            "authentication": "required_for_mutations"
        },
        "skills": registry.to_agent_card_skills(),
        "metadata": {
            "repository": "patelmm79/dependency-orchestrator",
            "triage_agents": {
                "consumer_triage": "Detects breaking changes in service providers",
                "template_triage": "Identifies improvements to propagate to derivatives"
            },
            "integration_partners": {
                "dev-nexus": "Receives change notifications, queries patterns, adds lessons",
                "github": "Creates issues and PRs in affected repositories"
            },
            "async_processing": True,
            "task_queue": "PostgreSQL (asyncpg)",
            "database_type": "postgresql"
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

        # Check authentication for protected skills
        if registry.is_protected(skill_id):
            auth_header = request.headers.get("Authorization")
            if not verify_auth(auth_header, config):
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "Authentication required",
                        "skill": skill_id
                    }
                )

        # Get skill
        skill = registry.get_skill(skill_id)
        if not skill:
            return JSONResponse(
                status_code=404,
                content={"error": f"Skill not found: {skill_id}"}
            )

        # Execute
        result = await skill.execute(input_data)

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": f"Execution failed: {str(e)}"}
        )


@app.post("/a2a/cancel")
async def cancel_task(request: Request):
    """Handle task cancellation"""
    try:
        body = await request.json()
        task_id = body.get("task_id")

        if not task_id:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing required field: task_id"}
            )

        # TODO: Implement RQ job cancellation
        return JSONResponse(
            content={
                "success": True,
                "message": "Task cancellation requested",
                "task_id": task_id
            }
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Cancellation failed: {str(e)}"}
        )


# Legacy webhook endpoint (backward compatibility)
@app.post("/api/webhook/change-notification")
async def legacy_webhook(request: Request):
    """
    Legacy webhook endpoint - converts to A2A format

    Maintains backward compatibility with existing CI/CD integrations
    """
    try:
        body = await request.json()

        # Convert webhook format to A2A skill input
        a2a_input = {
            "skill_id": "receive_change_notification",
            "input": {
                "repository": body.get("repository"),
                "commit_sha": body.get("commit_sha"),
                "timestamp": body.get("timestamp"),
                "patterns": body.get("patterns", []),
                "change_type": body.get("change_type", "unknown")
            }
        }

        # Execute via A2A
        skill = registry.get_skill("receive_change_notification")
        if not skill:
            return JSONResponse(
                status_code=500,
                content={"error": "Skill not available"}
            )

        result = await skill.execute(a2a_input["input"])

        return JSONResponse(content=result)

    except Exception as e:
        logger.error(f"Legacy webhook failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Webhook processing failed: {str(e)}"}
        )


@app.get("/health")
async def health_check():
    """Health check"""
    # Check PostgreSQL
    db_health = await db_manager.health_check()
    db_healthy = db_health.get("status") == "healthy"

    # Get task queue stats
    task_stats = await task_queue.get_task_stats()

    # Check external agents
    external_agents = await agent_registry.health_check_all()

    return {
        "status": "healthy" if db_healthy else "unhealthy",
        "service": "dependency-orchestrator",
        "version": "2.0.0",
        "skills_registered": len(registry.get_skill_ids()),
        "skills": registry.get_skill_ids(),
        "database": db_health,
        "database_type": "postgresql",
        "task_queue": task_stats,
        "external_agents": external_agents
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Dependency Orchestrator A2A Agent",
        "version": "2.0.0",
        "architecture": "event-driven",
        "agent_card": f"{config.agent_url}/.well-known/agent.json",
        "health": f"{config.agent_url}/health",
        "endpoints": {
            "execute": "/a2a/execute",
            "cancel": "/a2a/cancel",
            "agent_card": "/.well-known/agent.json",
            "health": "/health",
            "legacy_webhook": "/api/webhook/change-notification"
        },
        "skills_registered": len(registry.get_skill_ids()),
        "skills": registry.get_skill_ids()
    }


def verify_auth(auth_header: str, config) -> bool:
    """Verify authentication token"""
    if not auth_header:
        return False

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            return False

        return token == config.auth_token
    except:
        return False


if __name__ == "__main__":
    import uvicorn
    port = config.port
    print(f"Starting Dependency Orchestrator A2A Agent on port {port}")
    print(f"AgentCard: http://localhost:{port}/.well-known/agent.json")
    print(f"Skills: {', '.join(registry.get_skill_ids())}")
    uvicorn.run(app, host="0.0.0.0", port=port)
```

---

### Phase 5: Update Configuration & Dependencies (30 min)

#### 5.1 Update requirements.txt

```txt
# Add to requirements.txt

# A2A Protocol
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
httpx>=0.25.0  # For A2A client

# PostgreSQL Database & Task Queue
asyncpg>=0.29.0
psycopg2-binary>=2.9.0  # For migrations

# Existing dependencies
# ... (keep existing)
```

#### 5.2 Update config.py

```python
# orchestrator/config.py

import os
from typing import List

class Config:
    # Existing fields...

    # A2A Configuration
    agent_url: str = os.getenv("AGENT_URL", "http://localhost:8080")
    port: int = int(os.getenv("PORT", "8080"))

    # Authentication
    auth_token: str = os.getenv("AUTH_TOKEN", "")

    # PostgreSQL (for data & task queue)
    use_postgresql: bool = os.getenv("USE_POSTGRESQL", "true").lower() == "true"
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db: str = os.getenv("POSTGRES_DB", "orchestrator")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "")

    # External Agents
    dev_nexus_url: str = os.getenv("DEV_NEXUS_URL", "")
    dev_nexus_auth_token: str = os.getenv("DEV_NEXUS_AUTH_TOKEN", "")

    # CORS
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "").split(",")
```

#### 5.3 Update .env.example

```bash
# Add to .env.example

# A2A Configuration
AGENT_URL=https://dependency-orchestrator-xxxxxxxxx.a.run.app
PORT=8080
AUTH_TOKEN=your-secret-token-here

# PostgreSQL (Database & Task Queue)
USE_POSTGRESQL=true
POSTGRES_HOST=10.8.0.2  # Internal VM IP (use same as dev-nexus)
POSTGRES_PORT=5432
POSTGRES_DB=devnexus  # Use same database as dev-nexus
POSTGRES_USER=devnexus
POSTGRES_PASSWORD=  # Set via Secret Manager

# External Agents
DEV_NEXUS_URL=https://pattern-discovery-agent-xxxxxxxxx.a.run.app
DEV_NEXUS_AUTH_TOKEN=

# CORS
CORS_ORIGINS=http://localhost:3000,https://*.vercel.app
```

---

### Phase 6: Deployment Updates (30 min)

#### 6.1 Update Dockerfile

```dockerfile
# Keep existing Dockerfile base
# No changes needed - workers run within the same FastAPI app using asyncio

FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY orchestrator/ ./orchestrator/

# Expose port
EXPOSE 8080

# Run FastAPI server (workers start automatically in background)
CMD ["uvicorn", "orchestrator.a2a.server:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Note:** No Supervisor needed - background workers start automatically via FastAPI startup event handlers.

#### 6.2 Update Cloud Run Deployment

```bash
# deploy-gcp.sh

gcloud run deploy dependency-orchestrator \
  --image gcr.io/${PROJECT_ID}/dependency-orchestrator:latest \
  --region ${REGION} \
  --platform managed \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --min-instances 0 \
  --max-instances 10 \
  --timeout 300 \
  --allow-unauthenticated \
  --vpc-connector projects/${PROJECT_ID}/locations/${REGION}/connectors/dev-nexus-connector \
  --vpc-egress all-traffic \
  --set-env-vars="AGENT_URL=https://dependency-orchestrator-${PROJECT_ID}.a.run.app" \
  --set-env-vars="DEV_NEXUS_URL=https://pattern-discovery-agent-${PROJECT_ID}.a.run.app" \
  --set-env-vars="USE_POSTGRESQL=true" \
  --set-env-vars="POSTGRES_HOST=10.8.0.2" \
  --set-env-vars="POSTGRES_PORT=5432" \
  --set-env-vars="POSTGRES_DB=devnexus" \
  --set-env-vars="POSTGRES_USER=devnexus" \
  --set-secrets="GITHUB_TOKEN=GITHUB_TOKEN:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,POSTGRES_PASSWORD=POSTGRES_PASSWORD:latest,AUTH_TOKEN=ORCHESTRATOR_AUTH_TOKEN:latest,DEV_NEXUS_AUTH_TOKEN=DEV_NEXUS_AUTH_TOKEN:latest"
```

**Key Changes:**
- ✅ Uses same PostgreSQL database as dev-nexus (10.8.0.2)
- ✅ Uses VPC connector for database access
- ✅ No Redis setup needed
- ✅ Workers run automatically inside the same container

#### 6.3 Database Migration

Run the migration to create `orchestration_tasks` table:

```bash
# Connect to PostgreSQL VM
gcloud compute ssh dev-nexus-postgres --zone=us-central1-a --project=${PROJECT_ID}

# Inside VM, run psql
sudo -u postgres psql -d devnexus

# Run the migration SQL from Phase 2.2
-- Copy and paste the CREATE TABLE statements
```

**Alternative:** Create a migration script in the orchestrator codebase that runs on startup.

---

### Phase 7: Testing Strategy (60 min)

#### 7.1 Unit Tests

```python
# tests/test_skills.py
import pytest
from orchestrator.a2a.skills.events import ReceiveChangeNotificationSkill
from orchestrator.tasks.postgres_queue import PostgresTaskQueue
from orchestrator.database import DatabaseManager

@pytest.mark.asyncio
async def test_receive_change_notification():
    # Setup test database
    db_manager = DatabaseManager()
    await db_manager.connect()
    task_queue = PostgresTaskQueue(db_manager)

    skill = ReceiveChangeNotificationSkill(task_queue)

    input_data = {
        "repository": "test/repo",
        "commit_sha": "abc123",
        "timestamp": "2025-01-15T10:00:00Z"
    }

    result = await skill.execute(input_data)

    assert result["success"] is True
    assert "task_id" in result
    assert result["status"] == "queued"

    # Cleanup
    await db_manager.disconnect()
```

#### 7.2 Integration Tests

```python
# tests/test_integration.py
import pytest
from orchestrator.a2a.client import A2AClient

@pytest.mark.asyncio
async def test_dev_nexus_integration():
    """Test calling dev-nexus from orchestrator"""
    client = A2AClient("http://localhost:8000")  # dev-nexus

    result = await client.execute_skill(
        skill_id="get_repository_list",
        input_data={"include_metadata": False}
    )

    assert result["success"] is True
    assert "repositories" in result
```

#### 7.3 End-to-End Test

```python
# tests/test_e2e.py
import pytest
from orchestrator.a2a.client import A2AClient

@pytest.mark.asyncio
async def test_full_orchestration_flow():
    """
    Test complete flow:
    1. Dev-nexus notifies orchestrator
    2. Orchestrator analyzes impact
    3. Orchestrator reports back to dev-nexus
    """
    orchestrator = A2AClient("http://localhost:8080")

    # 1. Notify of change
    notify_result = await orchestrator.execute_skill(
        skill_id="receive_change_notification",
        input_data={
            "repository": "test/api-service",
            "commit_sha": "abc123",
            "timestamp": "2025-01-15T10:00:00Z"
        }
    )

    assert notify_result["success"] is True
    task_id = notify_result["task_id"]

    # 2. Poll for completion (simplified)
    import asyncio
    await asyncio.sleep(5)

    # 3. Check status
    status_result = await orchestrator.execute_skill(
        skill_id="get_orchestration_status",
        input_data={"task_id": task_id}
    )

    assert status_result["success"] is True
    assert status_result["status"] in ["processing", "completed"]
```

---

## Migration Strategy

### Week 1: Development & Testing
- Day 1-2: Implement Phases 1-3 (Foundation, Task Management, Skills)
- Day 3-4: Implement Phase 4 (A2A Server)
- Day 5: Testing (unit, integration)

### Week 2: Deployment & Verification
- Day 1: Setup Redis (Memorystore)
- Day 2: Deploy to Cloud Run (staging)
- Day 3: Integration testing with dev-nexus
- Day 4: Production deployment
- Day 5: Monitor & fix issues

---

## Success Criteria

- ✅ AgentCard accessible at `/.well-known/agent.json`
- ✅ All 7 skills working via `/a2a/execute`
- ✅ Legacy webhook endpoint still works
- ✅ Async task processing with PostgreSQL queue
- ✅ Background workers running (2 workers via asyncio)
- ✅ Orchestrator can call dev-nexus skills
- ✅ Dev-nexus can call orchestrator skills
- ✅ Triage agents integrated
- ✅ GitHub issues created correctly
- ✅ Lessons learned recorded in dev-nexus
- ✅ Task status queryable via `get_orchestration_status`
- ✅ PostgreSQL shared with dev-nexus (no additional infrastructure)

---

## Rollback Plan

1. **Keep current version running:**
   ```bash
   git tag v1.0-rest-api
   ```

2. **Feature flag for A2A:**
   ```python
   USE_A2A = os.getenv("USE_A2A", "false") == "true"
   ```

3. **Database migration (if needed):**
   - Test in staging first
   - Backup before migration

---

## Cost Considerations

### GCP Resources

| Resource | Monthly Cost | Notes |
|----------|-------------|-------|
| Cloud Run | ~$20 | Assuming 1M requests/month |
| PostgreSQL | **$0** | Shared with dev-nexus (10.8.0.2) |
| VPC Connector | ~$8 | Shared with dev-nexus |
| **Total** | ~$28/month | vs ~$50 for REST-only |

**Cost Savings vs Redis Approach:**
- ✅ **$45/month saved** - No Redis Memorystore needed
- ✅ **$0 additional infrastructure** - Reuses existing PostgreSQL
- ✅ **Simpler deployment** - Single container, no Supervisor

**Cost Optimization:**
- Scale to zero during low usage (min-instances=0)
- Workers run in same container (no separate worker costs)
- Shared PostgreSQL database with dev-nexus

---

## Next Steps After Conversion

1. **Add more triage agents:**
   - SecurityTriageAgent - Detect security vulnerabilities
   - PerformanceTriageAgent - Identify performance regressions

2. **Add PR auto-creation:**
   - Generate fix PRs for breaking changes
   - Auto-update dependency versions

3. **Add notification channels:**
   - Slack notifications for critical impacts
   - Email summaries

4. **Add metrics & monitoring:**
   - Track impact analysis success rate
   - Monitor task queue depths
   - Alert on failures

---

## Resources

- **Pattern-Miner Plan:** `PATTERN_MINER_A2A_CONVERSION_PLAN.md`
- **Dev-Nexus Skills:** Reference implementation
- **PostgreSQL Setup:** `POSTGRESQL_SETUP.md`
- **asyncpg Documentation:** https://magicstack.github.io/asyncpg/

---

## Timeline Summary

| Phase | Task | Time | Cumulative |
|-------|------|------|------------|
| 1 | A2A Foundation | 45 min | 45 min |
| 2 | PostgreSQL Task Queue | 60 min | 1h 45min |
| 3 | Create Skills | 90 min | 3h 15min |
| 4 | A2A Server + Startup | 60 min | 4h 15min |
| 5 | Config & Dependencies | 20 min | 4h 35min |
| 6 | Deployment (Simplified) | 20 min | 4h 55min |
| 7 | Testing | 60 min | 5h 55min |
| 8 | Database Migration | 15 min | 6h 10min |
| Deploy | Deploy & Verify | 30 min | 6h 40min |
| Buffer | Debugging & Fixes | 50 min | **7.5 hours** |

**Total: 7.5 hours** (including buffer)

**Time Savings vs Redis Approach:**
- ✅ **30 minutes saved** - No Redis/Supervisor setup
- ✅ **Simpler deployment** - Single container, fewer moving parts

---

---

## PostgreSQL vs Redis: Why PostgreSQL Won

**Decision Rationale:**

| Criterion | PostgreSQL | Redis (RQ) |
|-----------|-----------|------------|
| **Monthly Cost** | **$0** (shared) | $45 (Memorystore) |
| **Persistence** | ✅ Durable | ⚠️ In-memory (data loss risk) |
| **Setup Complexity** | ✅ Reuse existing | ❌ New Memorystore + config |
| **Deployment** | ✅ Single container | ❌ Supervisor or separate workers |
| **Performance** | ✅ Sufficient (10-50 tasks/hr) | Overkill (1000s tasks/sec) |
| **Querying** | ✅ Rich SQL queries | ❌ Limited key-value |
| **Transactions** | ✅ ACID guarantees | ❌ No transactions |
| **Monitoring** | ✅ SQL-based stats | ❌ Redis-specific tools |

**Key Benefits:**
- 🎯 **Right-sized solution** for moderate workload (10-50 orchestration tasks/hour)
- 💰 **Zero additional cost** by sharing dev-nexus PostgreSQL
- 🔒 **Data durability** - tasks survive container restarts
- 🔍 **Better observability** - SQL queries for task analytics
- 🏗️ **Simpler architecture** - fewer moving parts to maintain

**When Redis would be better:**
- High-throughput queues (>100 tasks/sec)
- Sub-millisecond dequeue latency requirements
- Separate orchestrator team with independent infrastructure

For dev-nexus ecosystem with shared PostgreSQL, **PostgreSQL task queue is the clear winner**.

---

## Questions?

Contact: Architecture Team
Repository: patelmm79/dependency-orchestrator
Integration: patelmm79/dev-nexus, patelmm79/pattern-miner
