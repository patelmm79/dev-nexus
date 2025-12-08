# Extending Dev-Nexus: Adding New Agents and Skills

> **📢 UPDATED**: This guide has been updated to reflect the new **modular architecture** (v2.0).
> The system now uses a plugin-style architecture with skills in separate modules.
> See [REFACTORING_COMPLETE.md](./REFACTORING_COMPLETE.md) for migration details.

## Overview

This guide explains how to extend the dev-nexus Pattern Discovery Agent System with new functionality. The system now uses a **modular architecture** where skills are self-contained modules that auto-register.

There are two primary approaches:

1. **Adding Skills to the Existing A2A Server** - Extend the current agent with new capabilities (EASIER with new architecture!)
2. **Creating Standalone Agents** - Build new independent agents that coordinate with dev-nexus

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Adding Skills to Dev-Nexus](#adding-skills-to-dev-nexus)
3. [Creating Standalone Agents](#creating-standalone-agents)
4. [Best Practices](#best-practices)
5. [Example: Documentation Review Agent](#example-documentation-review-agent)

---

## Architecture Overview

### Current System Components (Modular v2.0)

```
dev-nexus/
├── a2a/
│   ├── server.py (250 lines) # FastAPI app with dynamic AgentCard
│   ├── executor.py (74 lines) # Thin coordinator (delegates to registry)
│   ├── registry.py           # NEW: Skill discovery and routing
│   ├── skills/              # NEW: Modular skill modules
│   │   ├── base.py          # BaseSkill interface
│   │   ├── pattern_query.py         # Query patterns skills
│   │   ├── repository_info.py       # Repository info skills
│   │   ├── knowledge_management.py  # Knowledge base skills
│   │   └── integration.py           # External agent integration
│   ├── client.py            # A2A client for external agents
│   ├── auth.py              # Authentication middleware
│   └── config.py            # Configuration management
├── core/
│   ├── pattern_extractor.py      # Claude API pattern extraction
│   ├── knowledge_base.py          # GitHub storage operations
│   ├── similarity_finder.py      # Pattern matching
│   ├── integration_service.py    # External agent coordination
│   └── documentation_service.py  # NEW: Documentation review
├── schemas/
│   ├── knowledge_base_v2.py      # Pydantic data models
│   └── migration.py              # Schema migration
└── scripts/
    └── pattern_analyzer.py       # GitHub Actions CLI mode
```

**Key Changes in v2.0**:
- ✅ Skills are now in separate modules (`a2a/skills/`)
- ✅ Executor reduced from 484 → 74 lines (85% reduction)
- ✅ Server reduced from 445 → 250 lines (44% reduction)
- ✅ Dynamic AgentCard generation from registry
- ✅ Skills auto-register on import
- ✅ Adding skill = create one file (not edit 2-3 files)

### Key Concepts

**A2A Protocol**: Agent-to-Agent protocol for machine-to-machine communication
- **AgentCard**: Published at `/.well-known/agent.json`, describes agent capabilities
- **Skills**: Individual functions/operations the agent can perform
- **Executor**: Routes incoming requests to skill handlers

**Authentication Levels**:
- **Public Skills**: No authentication required (e.g., query_patterns, get_deployment_info)
- **Protected Skills**: Require A2A authentication (e.g., add_lesson_learned, update_dependency_info)

---

## Adding Skills to Dev-Nexus

Follow these steps to add a new skill to the existing Pattern Discovery Agent:

### Step 1: Define the Skill in AgentCard

Edit `a2a/server.py` and add your skill definition to the `skills` array in the `get_agent_card()` function:

```python
{
    "id": "your_skill_id",
    "name": "Human-Readable Skill Name",
    "description": "Clear description of what this skill does",
    "tags": ["tag1", "tag2", "tag3"],
    "requires_authentication": False,  # or True
    "input_schema": {
        "type": "object",
        "properties": {
            "parameter1": {
                "type": "string",
                "description": "Description of parameter1"
            },
            "parameter2": {
                "type": "integer",
                "description": "Description of parameter2",
                "default": 10
            }
        },
        "required": ["parameter1"]
    },
    "examples": [
        {
            "input": {"parameter1": "example_value", "parameter2": 5},
            "description": "What this example demonstrates"
        }
    ]
}
```

### Step 2: Update Authentication (if needed)

If your skill requires authentication, add it to the protected skills list in `a2a/auth.py`:

```python
def is_skill_protected(skill_id: str) -> bool:
    """Check if a skill requires authentication"""
    PROTECTED_SKILLS = [
        "add_lesson_learned",
        "update_dependency_info",
        "your_skill_id"  # Add your skill here
    ]
    return skill_id in PROTECTED_SKILLS
```

### Step 3: Add Routing in Executor

Edit `a2a/executor.py` and add a routing case in the `execute()` method:

```python
async def execute(self, skill_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a skill based on skill_id"""

    if skill_id == "query_patterns":
        return await self._handle_query_patterns(input_data)
    # ... existing skills ...
    elif skill_id == "your_skill_id":
        return await self._handle_your_skill(input_data)
    else:
        return {
            "error": f"Unknown skill: {skill_id}",
            "available_skills": [
                "query_patterns", "get_deployment_info",
                "your_skill_id"  # Add to list
            ]
        }
```

### Step 4: Implement the Skill Handler

Add your skill handler method to the `PatternDiscoveryExecutor` class in `a2a/executor.py`:

```python
async def _handle_your_skill(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Your skill description

    Input:
        - parameter1: Description
        - parameter2: Description

    Output:
        - result: Description
        - metadata: Additional info
    """
    try:
        # 1. Validate input
        parameter1 = input_data.get('parameter1')
        parameter2 = input_data.get('parameter2', 10)

        if not parameter1:
            return {
                "error": "Missing required parameter: 'parameter1'",
                "success": False
            }

        # 2. Perform the operation
        # Access knowledge base: self.kb_manager.load_knowledge_base()
        # Access similarity finder: self.similarity_finder.find_by_keywords(...)
        # Access external agents: self.integration_service.get_agent(...)

        result = f"Processed {parameter1} with parameter2={parameter2}"

        # 3. Return response
        return {
            "success": True,
            "result": result,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "parameter1": parameter1,
                "parameter2": parameter2
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to execute skill: {str(e)}"
        }
```

### Step 5: Add Core Logic (if needed)

If your skill requires complex business logic, add it to the `core/` module:

```python
# core/your_module.py

class YourService:
    """Service for your skill's business logic"""

    def __init__(self, kb_manager, similarity_finder):
        self.kb_manager = kb_manager
        self.similarity_finder = similarity_finder

    def process_data(self, input_data):
        """Your core logic here"""
        # Access knowledge base
        kb = self.kb_manager.load_knowledge_base()

        # Perform operations
        result = self._internal_processing(input_data, kb)

        return result

    def _internal_processing(self, data, kb):
        """Private helper method"""
        pass
```

Then instantiate it in `a2a/server.py`:

```python
from core.your_module import YourService

# In server.py
your_service = YourService(kb_manager, similarity_finder)
executor = PatternDiscoveryExecutor(kb_manager, similarity_finder, your_service)
```

### Step 6: Test Your Skill

```bash
# Start the server locally
python a2a/server.py

# Test the AgentCard
curl http://localhost:8080/.well-known/agent.json | jq '.skills[] | select(.id == "your_skill_id")'

# Test skill execution
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "your_skill_id",
    "input": {
      "parameter1": "test_value",
      "parameter2": 42
    }
  }' | jq
```

---

## Creating Standalone Agents

For more complex functionality, create a new standalone agent that coordinates with dev-nexus.

### Step 1: Create Agent Structure

```bash
mkdir -p your-agent/{a2a,core,schemas}
cd your-agent

# Create basic structure
touch a2a/{__init__.py,server.py,executor.py,config.py}
touch core/{__init__.py,your_logic.py}
touch schemas/{__init__.py,models.py}
```

### Step 2: Implement A2A Server

```python
# a2a/server.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Your Agent Name",
    description="What your agent does",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/.well-known/agent.json")
async def get_agent_card():
    """Publish AgentCard"""
    return {
        "name": "your_agent_name",
        "description": "Your agent description",
        "version": "1.0.0",
        "url": os.environ.get("AGENT_URL", "http://localhost:8080"),
        "capabilities": {
            "streaming": False,
            "multimodal": False,
            "authentication": "optional"
        },
        "skills": [
            {
                "id": "skill_one",
                "name": "Skill One",
                "description": "What skill one does",
                "tags": ["tag1", "tag2"],
                "requires_authentication": False,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "input_param": {
                            "type": "string",
                            "description": "Input parameter description"
                        }
                    },
                    "required": ["input_param"]
                }
            }
        ],
        "metadata": {
            "repository": "your-github/your-agent",
            "documentation": "https://github.com/your-github/your-agent#readme"
        }
    }

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

        # Route to executor
        from a2a.executor import YourAgentExecutor
        executor = YourAgentExecutor()
        result = await executor.execute(skill_id, input_data)

        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Execution failed: {str(e)}"}
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "your-agent-name",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
```

### Step 3: Implement Executor

```python
# a2a/executor.py

from typing import Dict, Any
from datetime import datetime

class YourAgentExecutor:
    """Executor for your agent's skills"""

    def __init__(self):
        # Initialize your services
        from core.your_logic import YourService
        self.service = YourService()

    async def execute(self, skill_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Route to appropriate skill handler"""

        if skill_id == "skill_one":
            return await self._handle_skill_one(input_data)
        else:
            return {
                "error": f"Unknown skill: {skill_id}",
                "available_skills": ["skill_one"]
            }

    async def _handle_skill_one(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle skill one execution"""
        try:
            input_param = input_data.get('input_param')

            if not input_param:
                return {"error": "Missing required parameter: 'input_param'"}

            # Process with your service
            result = self.service.process(input_param)

            return {
                "success": True,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to execute skill: {str(e)}"
            }
```

### Step 4: Integrate with Dev-Nexus

To allow dev-nexus to call your agent, configure the agent registry:

```bash
# In dev-nexus environment
export YOUR_AGENT_URL="https://your-agent.run.app"
export YOUR_AGENT_TOKEN="optional-auth-token"
```

Update `core/integration_service.py` in dev-nexus:

```python
class IntegrationService:
    def __init__(self):
        self.registry = ExternalAgentRegistry()

        # Register your agent
        your_agent_url = os.environ.get('YOUR_AGENT_URL')
        if your_agent_url:
            self.registry.agents['your-agent'] = A2AClient(
                agent_url=your_agent_url,
                auth_token=os.environ.get('YOUR_AGENT_TOKEN')
            )

    def call_your_agent(self, skill_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Call your agent's skill"""
        agent = self.registry.get_agent('your-agent')
        if not agent:
            return {"error": "your-agent not configured"}

        return agent.execute_skill(skill_id, input_data)
```

### Step 5: Allow Your Agent to Call Dev-Nexus

```python
# In your agent's code
from a2a.client import A2AClient

class YourService:
    def __init__(self):
        dev_nexus_url = os.environ.get('DEV_NEXUS_URL', 'https://pattern-discovery-agent.run.app')
        self.dev_nexus = A2AClient(dev_nexus_url)

    def query_patterns(self, keywords):
        """Query dev-nexus for similar patterns"""
        result = self.dev_nexus.execute_skill(
            skill_id="query_patterns",
            input_data={"keywords": keywords}
        )
        return result
```

---

## Best Practices

### 1. Skill Design

**DO:**
- Keep skills focused and single-purpose
- Use clear, descriptive names
- Provide comprehensive input validation
- Return structured, consistent responses
- Include helpful error messages

**DON'T:**
- Create skills that do multiple unrelated things
- Use vague parameter names
- Return different response structures based on conditions
- Raise exceptions (catch and return error objects instead)

### 2. Input/Output Schemas

```python
# GOOD: Clear schema with validation
"input_schema": {
    "type": "object",
    "properties": {
        "repository": {
            "type": "string",
            "description": "Repository name in format 'owner/repo'",
            "pattern": "^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$"
        },
        "min_similarity": {
            "type": "number",
            "description": "Minimum similarity score (0.0-1.0)",
            "minimum": 0.0,
            "maximum": 1.0,
            "default": 0.5
        }
    },
    "required": ["repository"]
}

# BAD: Vague schema
"input_schema": {
    "type": "object",
    "properties": {
        "data": {"type": "string"}  # What data? What format?
    }
}
```

### 3. Error Handling

```python
# GOOD: Structured error responses
try:
    result = process_data(input_data)
    return {
        "success": True,
        "result": result
    }
except ValueError as e:
    return {
        "success": False,
        "error": f"Invalid input: {str(e)}",
        "error_type": "validation_error"
    }
except Exception as e:
    return {
        "success": False,
        "error": f"Internal error: {str(e)}",
        "error_type": "internal_error"
    }

# BAD: Unhandled exceptions
def handle_skill(input_data):
    result = process_data(input_data)  # May raise exception
    return result  # Crashes the server
```

### 4. Authentication

- **Public skills**: Read-only operations (queries, getting info)
- **Protected skills**: Write operations (updating KB, modifying data)

```python
# Protected skill example
async def _handle_update_data(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Update data (AUTHENTICATED)"""
    # Authentication is checked before this method is called
    # Just implement the logic

    repository = input_data.get('repository')
    data = input_data.get('data')

    success = self.kb_manager.update_repository_data(repository, data)

    return {
        "success": success,
        "message": f"Updated data for {repository}"
    }
```

### 5. Logging and Observability

```python
import logging

logger = logging.getLogger(__name__)

async def _handle_skill(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Handle skill with logging"""
    logger.info(f"Executing skill with input: {input_data}")

    try:
        result = self._process(input_data)
        logger.info(f"Skill execution successful")
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Skill execution failed: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
```

### 6. Testing

```python
# test_executor.py

import pytest
from a2a.executor import YourAgentExecutor

@pytest.fixture
def executor():
    return YourAgentExecutor()

@pytest.mark.asyncio
async def test_skill_one_success(executor):
    """Test successful skill execution"""
    result = await executor.execute(
        "skill_one",
        {"input_param": "test_value"}
    )

    assert result["success"] == True
    assert "result" in result

@pytest.mark.asyncio
async def test_skill_one_missing_param(executor):
    """Test error handling for missing parameter"""
    result = await executor.execute("skill_one", {})

    assert result["success"] == False
    assert "error" in result
    assert "Missing required parameter" in result["error"]

@pytest.mark.asyncio
async def test_unknown_skill(executor):
    """Test unknown skill handling"""
    result = await executor.execute("nonexistent_skill", {})

    assert "error" in result
    assert "Unknown skill" in result["error"]
```

---

## Example: Documentation Review Agent

Here's a complete example of a documentation review agent that integrates with dev-nexus.

### Overview

The Documentation Review Agent:
- Analyzes documentation quality and consistency
- Checks for common documentation issues
- Compares docs against technical standards
- Integrates with dev-nexus to learn from other projects

### Implementation

#### 1. Define the Skill in Dev-Nexus

Add to `a2a/server.py`:

```python
{
    "id": "review_documentation",
    "name": "Review Documentation",
    "description": "Analyze documentation for quality, consistency, and adherence to standards",
    "tags": ["documentation", "quality", "standards"],
    "requires_authentication": False,
    "input_schema": {
        "type": "object",
        "properties": {
            "repository": {
                "type": "string",
                "description": "Repository name in format 'owner/repo'"
            },
            "doc_paths": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific documentation files to review (optional)",
                "default": []
            },
            "standards": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Standards to check against (optional)",
                "default": ["completeness", "clarity", "examples", "structure"]
            }
        },
        "required": ["repository"]
    },
    "examples": [
        {
            "input": {
                "repository": "patelmm79/dev-nexus",
                "doc_paths": ["README.md", "CLAUDE.md"],
                "standards": ["completeness", "clarity", "examples"]
            },
            "description": "Review main documentation files"
        }
    ]
}
```

#### 2. Create Core Documentation Service

```python
# core/documentation_service.py

import re
from typing import List, Dict, Any
from datetime import datetime
import anthropic

class DocumentationReviewer:
    """Service for reviewing documentation quality"""

    def __init__(self, anthropic_client, kb_manager):
        self.anthropic_client = anthropic_client
        self.kb_manager = kb_manager

        self.standards = {
            "completeness": self._check_completeness,
            "clarity": self._check_clarity,
            "examples": self._check_examples,
            "structure": self._check_structure,
            "accuracy": self._check_accuracy
        }

    def review_documentation(
        self,
        repository: str,
        doc_content: str,
        doc_path: str,
        standards: List[str]
    ) -> Dict[str, Any]:
        """
        Review documentation against specified standards

        Args:
            repository: Repository name
            doc_content: Documentation content
            doc_path: Path to documentation file
            standards: Standards to check

        Returns:
            Review results with scores and recommendations
        """
        results = {
            "repository": repository,
            "doc_path": doc_path,
            "reviewed_at": datetime.now().isoformat(),
            "standards_checked": standards,
            "checks": {},
            "overall_score": 0.0,
            "recommendations": []
        }

        # Run each standard check
        total_score = 0
        for standard in standards:
            if standard in self.standards:
                check_result = self.standards[standard](doc_content, doc_path)
                results["checks"][standard] = check_result
                total_score += check_result["score"]

        # Calculate overall score
        results["overall_score"] = total_score / len(standards) if standards else 0

        # Get recommendations from Claude
        recommendations = self._get_ai_recommendations(
            doc_content,
            doc_path,
            results["checks"]
        )
        results["recommendations"] = recommendations

        # Compare with similar projects
        similar_projects = self._find_similar_project_docs(repository)
        if similar_projects:
            results["similar_projects"] = similar_projects

        return results

    def _check_completeness(self, content: str, path: str) -> Dict[str, Any]:
        """Check if documentation is complete"""
        required_sections = {
            "README.md": ["overview", "installation", "usage", "examples"],
            "CLAUDE.md": ["overview", "commands", "examples"],
            "API.md": ["endpoints", "authentication", "examples"]
        }

        filename = path.split("/")[-1]
        required = required_sections.get(filename, [])

        found_sections = []
        missing_sections = []

        for section in required:
            # Check for section headings (## Section or # Section)
            pattern = rf'#+\s+{section}'
            if re.search(pattern, content, re.IGNORECASE):
                found_sections.append(section)
            else:
                missing_sections.append(section)

        score = len(found_sections) / len(required) if required else 1.0

        return {
            "score": score,
            "found_sections": found_sections,
            "missing_sections": missing_sections,
            "message": f"Found {len(found_sections)}/{len(required)} required sections"
        }

    def _check_clarity(self, content: str, path: str) -> Dict[str, Any]:
        """Check documentation clarity"""
        issues = []

        # Check for overly long sentences
        sentences = re.split(r'[.!?]+', content)
        long_sentences = [s for s in sentences if len(s.split()) > 40]
        if long_sentences:
            issues.append(f"Found {len(long_sentences)} sentences over 40 words")

        # Check for jargon without explanation
        jargon_words = ["A2A", "AgentCard", "executor", "skill"]
        undefined_jargon = []
        for word in jargon_words:
            if word in content:
                # Check if word is defined (followed by explanation)
                pattern = rf'{word}.*?:.*?'
                if not re.search(pattern, content):
                    undefined_jargon.append(word)

        if undefined_jargon:
            issues.append(f"Jargon used without definition: {', '.join(undefined_jargon[:3])}")

        # Calculate score
        score = max(0, 1.0 - (len(issues) * 0.2))

        return {
            "score": score,
            "issues": issues,
            "message": f"Clarity score: {score:.2f}"
        }

    def _check_examples(self, content: str, path: str) -> Dict[str, Any]:
        """Check for code examples"""
        # Count code blocks
        code_blocks = re.findall(r'```[\s\S]*?```', content)

        # Check for example sections
        has_examples_section = bool(re.search(r'#+\s+examples?', content, re.IGNORECASE))

        score = 0.0
        if len(code_blocks) >= 3:
            score += 0.7
        elif len(code_blocks) >= 1:
            score += 0.4

        if has_examples_section:
            score += 0.3

        return {
            "score": min(1.0, score),
            "code_blocks_count": len(code_blocks),
            "has_examples_section": has_examples_section,
            "message": f"Found {len(code_blocks)} code examples"
        }

    def _check_structure(self, content: str, path: str) -> Dict[str, Any]:
        """Check document structure"""
        # Extract all headings
        headings = re.findall(r'^(#+)\s+(.+)$', content, re.MULTILINE)

        issues = []

        # Check heading hierarchy
        prev_level = 0
        for heading_marks, heading_text in headings:
            level = len(heading_marks)
            if level > prev_level + 1:
                issues.append(f"Heading hierarchy skipped level: {heading_text}")
            prev_level = level

        # Check for table of contents (if long doc)
        lines = content.split('\n')
        if len(lines) > 200:
            has_toc = bool(re.search(r'table of contents', content, re.IGNORECASE))
            if not has_toc:
                issues.append("Long document missing table of contents")

        score = max(0, 1.0 - (len(issues) * 0.3))

        return {
            "score": score,
            "headings_count": len(headings),
            "issues": issues,
            "message": f"Structure score: {score:.2f}"
        }

    def _check_accuracy(self, content: str, path: str) -> Dict[str, Any]:
        """Check for potential accuracy issues"""
        issues = []

        # Check for outdated dates
        current_year = datetime.now().year
        old_years = [str(y) for y in range(current_year - 3, current_year - 1)]
        for year in old_years:
            if year in content:
                issues.append(f"May contain outdated information from {year}")
                break

        # Check for broken internal links
        internal_links = re.findall(r'\[([^\]]+)\]\(#([^\)]+)\)', content)
        for link_text, anchor in internal_links:
            # Convert anchor to heading format
            expected_heading = anchor.replace('-', ' ')
            if not re.search(rf'#+\s+{expected_heading}', content, re.IGNORECASE):
                issues.append(f"Potentially broken link: #{anchor}")

        score = max(0, 1.0 - (len(issues) * 0.25))

        return {
            "score": score,
            "issues": issues,
            "message": f"Accuracy score: {score:.2f}"
        }

    def _get_ai_recommendations(
        self,
        content: str,
        path: str,
        checks: Dict[str, Any]
    ) -> List[str]:
        """Get AI-powered recommendations from Claude"""

        # Build prompt with check results
        check_summary = "\n".join([
            f"- {standard}: {result['message']}"
            for standard, result in checks.items()
        ])

        prompt = f"""You are a technical documentation expert. Review this documentation and provide 3-5 specific, actionable recommendations for improvement.

Documentation file: {path}

Automated checks found:
{check_summary}

Content preview (first 1000 chars):
{content[:1000]}

Provide specific recommendations in this format:
1. [Category] Recommendation text
2. [Category] Recommendation text

Focus on: structure, clarity, completeness, and developer experience."""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract recommendations from response
            recommendations_text = response.content[0].text
            recommendations = [
                line.strip()
                for line in recommendations_text.split('\n')
                if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith('-'))
            ]

            return recommendations[:5]

        except Exception as e:
            return [f"Error getting AI recommendations: {str(e)}"]

    def _find_similar_project_docs(self, repository: str) -> List[Dict[str, Any]]:
        """Find similar projects with good documentation"""
        try:
            # Load knowledge base
            kb = self.kb_manager.load_knowledge_base()

            # Get repository info
            if repository not in kb.repositories:
                return []

            repo_info = kb.repositories[repository]
            keywords = repo_info.latest_patterns.keywords

            # Find similar repositories
            similar_repos = []
            for repo_name, other_info in kb.repositories.items():
                if repo_name == repository:
                    continue

                # Check keyword overlap
                common_keywords = set(keywords) & set(other_info.latest_patterns.keywords)
                if len(common_keywords) >= 2:
                    similar_repos.append({
                        "repository": repo_name,
                        "common_keywords": list(common_keywords),
                        "problem_domain": other_info.latest_patterns.problem_domain
                    })

            return similar_repos[:3]  # Top 3 similar projects

        except Exception as e:
            return []
```

#### 3. Add Executor Handler

```python
# In a2a/executor.py

async def _handle_review_documentation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Review documentation for quality and standards compliance

    Input:
        - repository: str - Repository name
        - doc_paths: List[str] - Documentation files to review
        - standards: List[str] - Standards to check

    Output:
        - reviews: List of review results for each document
        - overall_assessment: Summary of documentation quality
    """
    try:
        from core.documentation_service import DocumentationReviewer
        from github import Github

        repository = input_data.get('repository')
        doc_paths = input_data.get('doc_paths', [])
        standards = input_data.get('standards', ['completeness', 'clarity', 'examples', 'structure'])

        if not repository:
            return {"error": "Missing required parameter: 'repository'"}

        # Initialize reviewer
        reviewer = DocumentationReviewer(
            anthropic_client=anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY')),
            kb_manager=self.kb_manager
        )

        # Get GitHub client
        github_client = Github(os.environ.get('GITHUB_TOKEN'))
        repo = github_client.get_repo(repository)

        # If no paths specified, review common docs
        if not doc_paths:
            doc_paths = []
            try:
                # Try common documentation files
                for filename in ['README.md', 'CLAUDE.md', 'CONTRIBUTING.md', 'docs/API.md']:
                    try:
                        repo.get_contents(filename)
                        doc_paths.append(filename)
                    except:
                        pass
            except Exception as e:
                return {"error": f"Failed to find documentation files: {str(e)}"}

        # Review each document
        reviews = []
        for doc_path in doc_paths:
            try:
                # Fetch document content
                file_content = repo.get_contents(doc_path)
                content = file_content.decoded_content.decode('utf-8')

                # Review document
                review = reviewer.review_documentation(
                    repository=repository,
                    doc_content=content,
                    doc_path=doc_path,
                    standards=standards
                )
                reviews.append(review)

            except Exception as e:
                reviews.append({
                    "doc_path": doc_path,
                    "error": f"Failed to review document: {str(e)}"
                })

        # Calculate overall assessment
        total_score = sum(r.get('overall_score', 0) for r in reviews if 'overall_score' in r)
        avg_score = total_score / len(reviews) if reviews else 0

        # Determine rating
        if avg_score >= 0.8:
            rating = "Excellent"
        elif avg_score >= 0.6:
            rating = "Good"
        elif avg_score >= 0.4:
            rating = "Fair"
        else:
            rating = "Needs Improvement"

        return {
            "success": True,
            "repository": repository,
            "reviews": reviews,
            "overall_assessment": {
                "average_score": round(avg_score, 2),
                "rating": rating,
                "documents_reviewed": len(reviews),
                "standards_checked": standards
            }
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to review documentation: {str(e)}"
        }
```

#### 4. Test the Skill

```bash
# Start server
python a2a/server.py

# Test documentation review
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "review_documentation",
    "input": {
      "repository": "patelmm79/dev-nexus",
      "doc_paths": ["README.md", "CLAUDE.md"],
      "standards": ["completeness", "clarity", "examples", "structure"]
    }
  }' | jq
```

#### Expected Output

```json
{
  "success": true,
  "repository": "patelmm79/dev-nexus",
  "reviews": [
    {
      "repository": "patelmm79/dev-nexus",
      "doc_path": "README.md",
      "reviewed_at": "2025-01-10T10:30:00",
      "standards_checked": ["completeness", "clarity", "examples", "structure"],
      "checks": {
        "completeness": {
          "score": 0.75,
          "found_sections": ["overview", "installation", "usage"],
          "missing_sections": ["examples"],
          "message": "Found 3/4 required sections"
        },
        "clarity": {
          "score": 0.9,
          "issues": [],
          "message": "Clarity score: 0.90"
        },
        "examples": {
          "score": 0.7,
          "code_blocks_count": 5,
          "has_examples_section": true,
          "message": "Found 5 code examples"
        },
        "structure": {
          "score": 1.0,
          "headings_count": 12,
          "issues": [],
          "message": "Structure score: 1.00"
        }
      },
      "overall_score": 0.84,
      "recommendations": [
        "1. [Completeness] Add dedicated Examples section with common use cases",
        "2. [Clarity] Define A2A protocol terminology in overview section",
        "3. [Structure] Consider adding troubleshooting section for common issues"
      ],
      "similar_projects": [
        {
          "repository": "patelmm79/dependency-orchestrator",
          "common_keywords": ["agent", "coordination", "architecture"],
          "problem_domain": "Dependency management and orchestration"
        }
      ]
    }
  ],
  "overall_assessment": {
    "average_score": 0.84,
    "rating": "Excellent",
    "documents_reviewed": 1,
    "standards_checked": ["completeness", "clarity", "examples", "structure"]
  }
}
```

---

## Deployment

### Local Development

```bash
# Set environment variables
export ANTHROPIC_API_KEY="your-key"
export GITHUB_TOKEN="your-token"
export KNOWLEDGE_BASE_REPO="username/dev-nexus"

# Run server
python a2a/server.py
```

### Cloud Run Deployment

```bash
# Build and deploy
gcloud builds submit --tag gcr.io/$PROJECT_ID/your-agent
gcloud run deploy your-agent \
  --image gcr.io/$PROJECT_ID/your-agent \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY,GITHUB_TOKEN=$GITHUB_TOKEN"
```

---

## Next Steps

1. **Implement Your Skill**: Use this guide to add your documentation review agent or any other agent
2. **Test Thoroughly**: Use the testing patterns shown above
3. **Document Your Agent**: Update CLAUDE.md with your new skills
4. **Deploy**: Deploy to Cloud Run for 24/7 availability
5. **Integrate**: Connect with external agents via the A2A protocol

## Additional Resources

- [A2A Protocol Specification](https://github.com/anthropics/anthropic-a2a)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Models](https://docs.pydantic.dev/)
- [Google Cloud Run](https://cloud.google.com/run/docs)
