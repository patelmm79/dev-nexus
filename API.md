# API Reference

> Complete API documentation for the Pattern Discovery Agent A2A Server

**Last Updated**: 2025-01-10
**Version**: 2.0.0
**Base URL**: `https://your-service.run.app` (or `http://localhost:8080` for local)

---

## Overview

The Pattern Discovery Agent exposes an Agent-to-Agent (A2A) protocol API for programmatic access to pattern analysis, knowledge base management, and repository information.

**Key Features:**
- RESTful API with A2A protocol support
- Dynamic skill discovery via AgentCard
- Optional authentication for write operations
- JSON request/response format
- Cloud Run deployment ready

---

## Authentication

### Public Endpoints

These endpoints do not require authentication:
- `GET /` - Service information
- `GET /health` - Health check
- `GET /.well-known/agent.json` - AgentCard discovery
- `POST /a2a/execute` - For public skills (read-only operations)

### Authenticated Endpoints

Write operations require A2A authentication:
- `POST /a2a/execute` - For protected skills (modifications)

**Authentication Header:**
```
Authorization: Bearer <SERVICE_ACCOUNT_TOKEN>
```

**Service Account Configuration:**
```bash
export ALLOWED_SERVICE_ACCOUNTS=your-service@project.iam.gserviceaccount.com
```

---

## Core Endpoints

### GET /

Get service information and available endpoints.

**Response:**
```json
{
  "service": "Pattern Discovery Agent A2A Server",
  "version": "2.0.0",
  "architecture": "modular",
  "agent_card": "https://your-service.run.app/.well-known/agent.json",
  "health": "https://your-service.run.app/health",
  "endpoints": {
    "execute": "/a2a/execute",
    "cancel": "/a2a/cancel",
    "agent_card": "/.well-known/agent.json",
    "health": "/health"
  },
  "skills_registered": 9,
  "skills": ["query_patterns", "get_deployment_info", "..."]
}
```

---

### GET /health

Health check endpoint for monitoring and Cloud Run.

**Response:**
```json
{
  "status": "healthy",
  "service": "pattern-discovery-agent",
  "version": "2.0.0",
  "knowledge_base_repo": "patelmm79/dev-nexus",
  "skills_registered": 9,
  "skills": ["query_patterns", "get_deployment_info", "..."]
}
```

---

### GET /.well-known/agent.json

Discover agent capabilities via AgentCard (A2A protocol standard).

**Response:**
```json
{
  "name": "pattern_discovery_agent",
  "description": "Automated architectural consistency and pattern discovery",
  "version": "2.0.0",
  "url": "https://your-service.run.app",
  "capabilities": {
    "streaming": false,
    "multimodal": false,
    "authentication": "optional"
  },
  "skills": [
    {
      "id": "query_patterns",
      "name": "Query Patterns",
      "description": "Search for patterns by keywords, repository, or domain",
      "tags": ["patterns", "search", "knowledge"],
      "requires_authentication": false,
      "input_schema": { "..." },
      "examples": [ "..." ]
    }
  ],
  "metadata": {
    "repository": "patelmm79/dev-nexus",
    "documentation": "https://github.com/patelmm79/dev-nexus#readme",
    "knowledge_base": "patelmm79/dev-nexus",
    "skill_count": 9
  }
}
```

---

### POST /a2a/execute

Execute a skill by ID with input parameters.

**Request:**
```json
{
  "skill_id": "query_patterns",
  "input": {
    "keywords": ["retry", "exponential backoff"],
    "limit": 5
  }
}
```

**Response (Success):**
```json
{
  "success": true,
  "patterns": [
    {
      "repository": "username/repo",
      "patterns": ["Retry logic with exponential backoff"],
      "problem_domain": "API resilience"
    }
  ],
  "count": 1
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Invalid skill_id: unknown_skill",
  "available_skills": ["query_patterns", "..."]
}
```

**Authentication Required (401):**
```json
{
  "error": "Authentication required",
  "message": "Skill 'add_lesson_learned' requires A2A authentication",
  "skill": "add_lesson_learned"
}
```

---

### POST /a2a/cancel

Cancel a running task (for future long-running operations).

**Request:**
```json
{
  "task_id": "task_123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Task cancelled",
  "task_id": "task_123"
}
```

---

## Skills

### Pattern Query Skills

#### query_patterns

Search for patterns across repositories.

**Authentication**: Not required

**Input:**
```json
{
  "keywords": ["retry", "exponential backoff"],
  "repository": "optional-owner/repo",
  "problem_domain": "optional domain",
  "limit": 10
}
```

**Output:**
```json
{
  "success": true,
  "patterns": [
    {
      "repository": "username/my-api",
      "patterns": ["Retry logic with exponential backoff", "Rate limiting"],
      "reusable_components": [
        {
          "name": "RetryClient",
          "description": "HTTP client with retry logic",
          "files": ["src/client.py"]
        }
      ],
      "problem_domain": "API resilience",
      "keywords": ["retry", "http", "resilience"]
    }
  ],
  "count": 1,
  "query": {
    "keywords": ["retry", "exponential backoff"],
    "limit": 10
  }
}
```

**Example:**
```bash
curl -X POST https://your-service.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "query_patterns",
    "input": {
      "keywords": ["authentication", "jwt"],
      "limit": 5
    }
  }'
```

---

### Repository Information Skills

#### get_deployment_info

Get deployment information for a repository.

**Authentication**: Not required

**Input:**
```json
{
  "repository": "username/repo",
  "include_lessons": true
}
```

**Output:**
```json
{
  "success": true,
  "repository": "username/repo",
  "deployment": {
    "scripts": ["deploy.sh", "setup-secrets.sh"],
    "lessons_learned": [
      {
        "category": "deployment",
        "lesson": "Always use Cloud Run revision tags",
        "context": "Rollback was difficult without tags",
        "severity": "warning",
        "date": "2025-01-05"
      }
    ],
    "reusable_components": [],
    "ci_cd_platform": "GitHub Actions",
    "infrastructure": {
      "platform": "Cloud Run",
      "region": "us-central1"
    }
  }
}
```

**Example:**
```bash
curl -X POST https://your-service.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "get_deployment_info",
    "input": {
      "repository": "patelmm79/dev-nexus",
      "include_lessons": true
    }
  }'
```

---

#### get_repository_list

List all tracked repositories in the knowledge base.

**Authentication**: Not required

**Input:**
```json
{
  "include_metadata": true
}
```

**Output:**
```json
{
  "success": true,
  "repositories": [
    {
      "name": "username/repo1",
      "pattern_count": 15,
      "last_updated": "2025-01-10T12:00:00",
      "problem_domain": "API development"
    }
  ],
  "count": 1
}
```

---

#### get_cross_repo_patterns

Find patterns that appear across multiple repositories.

**Authentication**: Not required

**Input:**
```json
{
  "min_repos": 2,
  "pattern_type": "all"
}
```

**Output:**
```json
{
  "success": true,
  "cross_repo_patterns": [
    {
      "pattern": "Retry logic with exponential backoff",
      "repositories": ["username/api", "username/scraper"],
      "count": 2
    }
  ],
  "total_patterns": 1
}
```

---

### Knowledge Management Skills

#### add_lesson_learned

Add a lesson learned to a repository's deployment section.

**Authentication**: **Required**

**Input:**
```json
{
  "repository": "username/repo",
  "category": "deployment",
  "lesson": "Always test rollback procedures",
  "context": "Production deployment failed without tested rollback",
  "severity": "critical"
}
```

**Output:**
```json
{
  "success": true,
  "message": "Lesson learned added successfully",
  "repository": "username/repo",
  "lesson_id": "lesson_123"
}
```

**Example:**
```bash
curl -X POST https://your-service.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SERVICE_ACCOUNT_TOKEN" \
  -d '{
    "skill_id": "add_lesson_learned",
    "input": {
      "repository": "patelmm79/my-api",
      "category": "performance",
      "lesson": "Use connection pooling for database clients",
      "context": "High load caused connection exhaustion",
      "severity": "warning"
    }
  }'
```

---

#### update_dependency_info

Update dependency graph information for a repository.

**Authentication**: **Required**

**Input:**
```json
{
  "repository": "username/repo",
  "consumers": ["username/api-gateway"],
  "derivatives": ["username/forked-version"],
  "external_dependencies": [
    {
      "name": "requests",
      "version": "2.31.0",
      "type": "direct"
    }
  ]
}
```

**Output:**
```json
{
  "success": true,
  "message": "Dependency information updated",
  "repository": "username/repo"
}
```

---

### Integration Skills

#### health_check_external

Check health of external A2A agents.

**Authentication**: Not required

**Input:**
```json
{
  "agent": "dependency_orchestrator"
}
```

**Output:**
```json
{
  "success": true,
  "agent": "dependency_orchestrator",
  "status": "healthy",
  "url": "https://orchestrator.run.app",
  "response_time_ms": 145
}
```

---

### Documentation Standards Skills

#### check_documentation_standards

Check repository documentation for conformity to standards.

**Authentication**: Not required

**Input:**
```json
{
  "repository": "username/repo",
  "check_all_docs": false
}
```

**Output:**
```json
{
  "success": true,
  "repository": "username/repo",
  "status": "compliant",
  "status_emoji": "✅",
  "compliance_score": 0.95,
  "summary": {
    "total_files_checked": 10,
    "total_violations": 2,
    "critical_violations": 0,
    "high_violations": 0,
    "medium_violations": 2
  },
  "file_results": [...],
  "recommendations": [
    "Add version indicators to documentation"
  ]
}
```

**Example:**
```bash
curl -X POST https://your-service.run.app/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "check_documentation_standards",
    "input": {
      "repository": "patelmm79/dev-nexus",
      "check_all_docs": false
    }
  }'
```

---

#### validate_documentation_update

Validate that documentation was updated after code changes.

**Authentication**: Not required

**Input:**
```json
{
  "repository": "username/repo",
  "days": 7
}
```

**Output:**
```json
{
  "success": true,
  "repository": "username/repo",
  "validation": {
    "status": "compliant",
    "message": "Documentation updates found alongside code changes"
  },
  "changes": {
    "code_files": 5,
    "doc_files": 3
  },
  "warnings": []
}
```

---

## Error Responses

### 400 Bad Request

Missing required fields or invalid input.

```json
{
  "error": "Missing required field: skill_id"
}
```

### 401 Unauthorized

Authentication required for protected skill.

```json
{
  "error": "Authentication required",
  "message": "Skill 'add_lesson_learned' requires A2A authentication",
  "skill": "add_lesson_learned"
}
```

### 404 Not Found

Unknown skill ID.

```json
{
  "success": false,
  "error": "Skill not found: unknown_skill",
  "available_skills": ["query_patterns", "get_deployment_info", "..."]
}
```

### 500 Internal Server Error

Execution failure.

```json
{
  "error": "Execution failed: Connection timeout"
}
```

---

## Rate Limiting

Currently no rate limiting is enforced, but recommended practices:

- **Read operations**: Unlimited
- **Write operations**: Limit to 100 requests/hour
- **Heavy queries**: Use pagination and filters

---

## Examples

### Python Client

```python
import httpx

BASE_URL = "https://your-service.run.app"

async def query_patterns(keywords: list[str], limit: int = 10):
    """Query patterns by keywords"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/a2a/execute",
            json={
                "skill_id": "query_patterns",
                "input": {
                    "keywords": keywords,
                    "limit": limit
                }
            }
        )
        response.raise_for_status()
        return response.json()

# Usage
result = await query_patterns(["authentication", "jwt"])
print(result)
```

### JavaScript Client

```javascript
const BASE_URL = "https://your-service.run.app";

async function queryPatterns(keywords, limit = 10) {
  const response = await fetch(`${BASE_URL}/a2a/execute`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      skill_id: "query_patterns",
      input: {
        keywords: keywords,
        limit: limit
      }
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}

// Usage
const result = await queryPatterns(["authentication", "jwt"]);
console.log(result);
```

### Bash/cURL

```bash
#!/bin/bash

# Set base URL
BASE_URL="https://your-service.run.app"

# Query patterns
curl -X POST "$BASE_URL/a2a/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "query_patterns",
    "input": {
      "keywords": ["docker", "containerization"],
      "limit": 5
    }
  }' | jq

# Add lesson learned (requires auth)
curl -X POST "$BASE_URL/a2a/execute" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SERVICE_ACCOUNT_TOKEN" \
  -d '{
    "skill_id": "add_lesson_learned",
    "input": {
      "repository": "username/my-repo",
      "category": "deployment",
      "lesson": "Always use health checks",
      "context": "Container crashed silently",
      "severity": "critical"
    }
  }' | jq
```

---

## Testing

### Local Development

```bash
# Start dev server
bash scripts/dev-server.sh

# Health check
curl http://localhost:8080/health

# Get AgentCard
curl http://localhost:8080/.well-known/agent.json | jq

# Test query
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "query_patterns",
    "input": {"keywords": ["test"]}
  }' | jq
```

### Production Testing

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe pattern-discovery-agent \
  --region=us-central1 --format="value(status.url)")

# Test endpoints
curl $SERVICE_URL/health
curl $SERVICE_URL/.well-known/agent.json
```

---

## Deployment

### Environment Variables

Required:
- `ANTHROPIC_API_KEY` - Claude API key
- `GITHUB_TOKEN` - GitHub personal access token
- `KNOWLEDGE_BASE_REPO` - Format: "username/dev-nexus"

Optional:
- `PORT` - Server port (default: 8080)
- `HOST_OVERRIDE` - Override agent URL
- `ALLOWED_SERVICE_ACCOUNTS` - Comma-separated service account emails
- `ORCHESTRATOR_URL` - dependency-orchestrator service URL
- `PATTERN_MINER_URL` - pattern-miner service URL

### Deploy to Cloud Run

```bash
# Set up secrets
bash scripts/setup-secrets.sh

# Deploy
bash scripts/deploy.sh

# Get URL
gcloud run services describe pattern-discovery-agent \
  --region=us-central1 --format="value(status.url)"
```

---

## Troubleshooting

### Skill not found

**Problem**: `{"error": "Skill not found: my_skill"}`

**Solution**: Check available skills at `/.well-known/agent.json` or `/health`

### Authentication failed

**Problem**: `{"error": "Authentication required"}`

**Solution**:
- Ensure service account is in `ALLOWED_SERVICE_ACCOUNTS`
- Check Authorization header format: `Bearer <token>`
- Verify token is valid

### Timeout errors

**Problem**: Request times out

**Solution**:
- Increase client timeout to 60s
- Check knowledge base repository size
- Verify GitHub token has correct permissions

---

## See Also

- [QUICK_START.md](QUICK_START.md) - Getting started guide
- [EXTENDING_DEV_NEXUS.md](EXTENDING_DEV_NEXUS.md) - Adding new skills
- [CLAUDE.md](CLAUDE.md) - System architecture
- [AgentCard Specification](https://github.com/anthropics/a2a) - A2A protocol

---

**Last Updated**: 2025-01-10
**API Version**: 2.0.0
**Questions?** Open an issue on [GitHub](https://github.com/patelmm79/dev-nexus/issues)
