# AgentCard Documentation

> Understanding the Pattern Discovery Agent's A2A AgentCard

**Last Updated**: 2025-01-10
**AgentCard URL**: `/.well-known/agent.json`

---

## Overview

The **AgentCard** is a standardized JSON document published at `/.well-known/agent.json` that describes the Pattern Discovery Agent's capabilities, skills, and how to interact with it. It follows the Agent-to-Agent (A2A) protocol specification.

**Purpose:**
- **Discovery**: Other agents can find and understand this agent's capabilities
- **Self-documentation**: Dynamically generated from the skill registry
- **Standardization**: Follows A2A protocol conventions

---

## Accessing the AgentCard

### Production

```bash
curl https://your-service.run.app/.well-known/agent.json | jq
```

### Local Development

```bash
curl http://localhost:8080/.well-known/agent.json | jq
```

---

## AgentCard Structure

### Full Example

```json
{
  "name": "pattern_discovery_agent",
  "description": "Automated architectural consistency and pattern discovery across GitHub repositories using Claude AI",
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
      "description": "Search for patterns by keywords, repository, or problem domain",
      "tags": ["patterns", "search", "knowledge"],
      "requires_authentication": false,
      "input_schema": {
        "type": "object",
        "properties": {
          "keywords": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Keywords to search for in patterns"
          },
          "limit": {
            "type": "integer",
            "description": "Maximum number of results to return",
            "default": 10
          }
        }
      },
      "examples": [
        {
          "input": {
            "keywords": ["retry", "exponential backoff"],
            "limit": 5
          },
          "description": "Search for retry patterns"
        }
      ]
    }
  ],
  "metadata": {
    "repository": "patelmm79/dev-nexus",
    "documentation": "https://github.com/patelmm79/dev-nexus#readme",
    "authentication_note": "Read operations are public. Write operations require A2A authentication.",
    "knowledge_base": "patelmm79/dev-nexus",
    "external_agents": {
      "dependency_orchestrator": "Coordinates dependency updates and impact analysis",
      "pattern_miner": "Deep pattern extraction and code comparison"
    },
    "architecture": "modular",
    "skill_count": 9
  }
}
```

---

## Field Descriptions

### Top-Level Fields

#### name
- **Type**: String
- **Description**: Unique identifier for the agent
- **Value**: `"pattern_discovery_agent"`

#### description
- **Type**: String
- **Description**: Human-readable description of what the agent does
- **Value**: Brief explanation of pattern discovery functionality

#### version
- **Type**: String
- **Description**: Semantic version of the agent
- **Value**: `"2.0.0"` (current)

#### url
- **Type**: String
- **Description**: Base URL where the agent is accessible
- **Example**: `"https://pattern-agent-xyz.run.app"`

### Capabilities Object

#### streaming
- **Type**: Boolean
- **Description**: Whether the agent supports streaming responses
- **Value**: `false`

#### multimodal
- **Type**: Boolean
- **Description**: Whether the agent can process multiple input types (text, images, etc.)
- **Value**: `false`

#### authentication
- **Type**: String
- **Description**: Authentication requirement level
- **Value**: `"optional"` (some skills require auth, some don't)

### Skills Array

Each skill is an object with:

#### id
- **Type**: String
- **Description**: Unique identifier for the skill
- **Example**: `"query_patterns"`

#### name
- **Type**: String
- **Description**: Human-readable skill name
- **Example**: `"Query Patterns"`

#### description
- **Type**: String
- **Description**: What the skill does
- **Example**: `"Search for patterns by keywords..."`

#### tags
- **Type**: Array of strings
- **Description**: Categorization tags
- **Example**: `["patterns", "search", "knowledge"]`

#### requires_authentication
- **Type**: Boolean
- **Description**: Whether this skill requires authentication
- **Example**: `false` for reads, `true` for writes

#### input_schema
- **Type**: JSON Schema object
- **Description**: Defines required and optional input parameters
- **Example**: See schema below

#### examples
- **Type**: Array of example objects
- **Description**: Usage examples for the skill
- **Example**: See examples below

### Metadata Object

Custom metadata about the agent:

#### repository
- **Type**: String
- **Description**: GitHub repository
- **Value**: `"patelmm79/dev-nexus"`

#### documentation
- **Type**: String (URL)
- **Description**: Link to full documentation
- **Value**: GitHub README URL

#### authentication_note
- **Type**: String
- **Description**: Explanation of authentication requirements
- **Value**: Which operations need auth

#### knowledge_base
- **Type**: String
- **Description**: Knowledge base repository name
- **Value**: `"patelmm79/dev-nexus"`

#### external_agents
- **Type**: Object
- **Description**: Other agents this agent coordinates with
- **Value**: Map of agent names to descriptions

#### architecture
- **Type**: String
- **Description**: System architecture type
- **Value**: `"modular"`

#### skill_count
- **Type**: Integer
- **Description**: Total number of skills available
- **Value**: Number (dynamically calculated)

---

## Dynamic Generation

The AgentCard is **dynamically generated** from the skill registry, not hardcoded.

### How It Works

```python
# In a2a/server.py
@app.get("/.well-known/agent.json")
async def get_agent_card():
    agent_card = {
        "name": "pattern_discovery_agent",
        "description": "...",
        "version": "2.0.0",
        "url": config.agent_url,
        "capabilities": {...},
        "skills": registry.to_agent_card_skills(),  # ← Dynamic!
        "metadata": {...}
    }
    return JSONResponse(content=agent_card)
```

**Benefits:**
- Always up-to-date with current skills
- No manual updates needed when adding skills
- Skills auto-register on import

---

## Available Skills

The AgentCard includes 9 skills (as of v2.0):

### Pattern Query Skills (2)
1. `query_patterns` - Search patterns by keywords
2. (Future: `get_pattern_details`)

### Repository Info Skills (3)
3. `get_deployment_info` - Get deployment metadata
4. `get_repository_list` - List all tracked repos
5. `get_cross_repo_patterns` - Find patterns across repos

### Knowledge Management Skills (2)
6. `add_lesson_learned` (Auth) - Record lessons
7. `update_dependency_info` (Auth) - Update dependencies

### Integration Skills (1)
8. `health_check_external` - Check external agent health

### Documentation Standards Skills (2)
9. `check_documentation_standards` - Check doc conformity
10. `validate_documentation_update` - Validate doc updates

See [API.md](API.md) for complete skill documentation.

---

## Using the AgentCard

### 1. Agent Discovery

Other A2A agents can discover this agent:

```python
import httpx

async def discover_agent(agent_url: str):
    """Discover an A2A agent's capabilities"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{agent_url}/.well-known/agent.json")
        agent_card = response.json()

        print(f"Agent: {agent_card['name']}")
        print(f"Skills: {len(agent_card['skills'])}")

        for skill in agent_card['skills']:
            print(f"  - {skill['id']}: {skill['description']}")

        return agent_card

# Usage
agent = await discover_agent("https://pattern-agent.run.app")
```

### 2. Skill Validation

Validate input before calling:

```python
from jsonschema import validate

def validate_skill_input(agent_card, skill_id, input_data):
    """Validate input against skill's schema"""
    # Find skill in AgentCard
    skill = next(
        (s for s in agent_card['skills'] if s['id'] == skill_id),
        None
    )

    if not skill:
        raise ValueError(f"Skill {skill_id} not found")

    # Validate input
    validate(instance=input_data, schema=skill['input_schema'])

    return True

# Usage
validate_skill_input(agent_card, "query_patterns", {
    "keywords": ["test"],
    "limit": 5
})
```

### 3. Dynamic Client Generation

Generate client code from AgentCard:

```python
class PatternDiscoveryClient:
    """Auto-generated client from AgentCard"""

    def __init__(self, agent_url: str):
        self.agent_url = agent_url
        self.agent_card = self._fetch_agent_card()

        # Dynamically create methods for each skill
        for skill in self.agent_card['skills']:
            self._create_skill_method(skill)

    def _fetch_agent_card(self):
        response = httpx.get(f"{self.agent_url}/.well-known/agent.json")
        return response.json()

    def _create_skill_method(self, skill):
        """Create a method for each skill"""
        skill_id = skill['id']

        async def skill_method(**kwargs):
            return await self._execute_skill(skill_id, kwargs)

        setattr(self, skill_id, skill_method)

    async def _execute_skill(self, skill_id, input_data):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.agent_url}/a2a/execute",
                json={"skill_id": skill_id, "input": input_data}
            )
            return response.json()

# Usage
client = PatternDiscoveryClient("https://pattern-agent.run.app")
result = await client.query_patterns(keywords=["auth"], limit=5)
```

---

## Schema Examples

### Input Schema Example

```json
{
  "type": "object",
  "properties": {
    "keywords": {
      "type": "array",
      "items": {"type": "string"},
      "description": "Keywords to search for",
      "minItems": 1
    },
    "repository": {
      "type": "string",
      "description": "Optional repository filter (format: owner/repo)"
    },
    "limit": {
      "type": "integer",
      "description": "Maximum results",
      "default": 10,
      "minimum": 1,
      "maximum": 100
    }
  },
  "required": ["keywords"]
}
```

### Example Object Example

```json
{
  "input": {
    "keywords": ["retry", "exponential backoff"],
    "repository": "username/my-api",
    "limit": 5
  },
  "description": "Search for retry patterns in a specific repository"
}
```

---

## A2A Protocol Compliance

The Pattern Discovery Agent's AgentCard conforms to the [A2A Protocol Specification](https://github.com/anthropics/a2a).

**Required Fields** (per spec):
- ✅ `name` - Agent identifier
- ✅ `description` - Agent purpose
- ✅ `version` - Semantic version
- ✅ `url` - Base URL
- ✅ `skills` - Array of skill definitions

**Optional Fields** (per spec):
- ✅ `capabilities` - Feature flags
- ✅ `metadata` - Custom metadata

**Skill Requirements** (per spec):
- ✅ `id` - Unique identifier
- ✅ `name` - Human-readable name
- ✅ `description` - What it does
- ✅ `input_schema` - JSON Schema
- ✅ `requires_authentication` - Auth flag

---

## Versioning

The AgentCard version follows semantic versioning:

- **Major** (2.x.x): Breaking changes to skills or API
- **Minor** (x.0.x): New skills or non-breaking features
- **Patch** (x.x.0): Bug fixes, no API changes

**Current Version**: 2.0.0 (Modular architecture)

**Previous Versions**:
- 1.0.0 - Initial A2A support with 3 skills
- 2.0.0 - Modular architecture with 9 skills

---

## Extending the AgentCard

When you add a new skill, the AgentCard automatically updates. No manual changes needed!

**Example: Adding a new skill**

1. Create skill module: `a2a/skills/my_skill.py`
2. Implement `BaseSkill` interface
3. Register in `a2a/skills/__init__.py`
4. Restart server

The skill automatically appears in `/.well-known/agent.json`!

See [EXTENDING_DEV_NEXUS.md](EXTENDING_DEV_NEXUS.md) for details.

---

## Troubleshooting

### AgentCard returns 404

**Problem**: `curl /.well-known/agent.json` returns 404

**Solution**:
- Verify server is running: `curl /health`
- Check path: Must be `/.well-known/agent.json` (not `/agent.json`)

### Skills missing from AgentCard

**Problem**: New skill doesn't appear in AgentCard

**Solution**:
- Check skill is registered in `a2a/skills/__init__.py`
- Restart server
- Check logs for import errors

### Invalid schema errors

**Problem**: Clients report invalid input schema

**Solution**:
- Validate schema at [jsonschema.net](https://www.jsonschema.net/)
- Ensure schema follows JSON Schema Draft 7
- Test with `jsonschema.validate()`

---

## Testing

### Manual Testing

```bash
# Get AgentCard
curl http://localhost:8080/.well-known/agent.json | jq

# Check skill count
curl http://localhost:8080/.well-known/agent.json | jq '.skills | length'

# List skill IDs
curl http://localhost:8080/.well-known/agent.json | jq '.skills[].id'

# Get specific skill details
curl http://localhost:8080/.well-known/agent.json | \
  jq '.skills[] | select(.id=="query_patterns")'
```

### Automated Testing

```python
# tests/test_agent_card.py
import pytest
import httpx

@pytest.mark.asyncio
async def test_agent_card_structure():
    """Test AgentCard has required fields"""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8080/.well-known/agent.json")
        agent_card = response.json()

        # Check required fields
        assert "name" in agent_card
        assert "description" in agent_card
        assert "version" in agent_card
        assert "skills" in agent_card
        assert len(agent_card["skills"]) > 0

        # Check skill structure
        for skill in agent_card["skills"]:
            assert "id" in skill
            assert "name" in skill
            assert "description" in skill
            assert "input_schema" in skill
```

---

## See Also

- [API.md](API.md) - Complete API documentation
- [EXTENDING_DEV_NEXUS.md](EXTENDING_DEV_NEXUS.md) - Adding new skills
- [A2A Protocol Spec](https://github.com/anthropics/a2a) - Official specification
- [JSON Schema](https://json-schema.org/) - Schema specification

---

**Last Updated**: 2025-01-10
**AgentCard Version**: 2.0.0
**Questions?** Open an issue on [GitHub](https://github.com/patelmm79/dev-nexus/issues)
