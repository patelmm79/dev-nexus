# Extending Dev-Nexus

> Guide to adding new features, skills, and customizations to the Pattern Discovery Agent

**Last Updated**: 2025-01-10
**Version**: 2.0 (Modular Architecture)

---

## Overview

Dev-Nexus is built with extensibility in mind. This guide covers how to:

- Add new A2A skills
- Customize pattern extraction
- Add new notification channels
- Extend the knowledge base schema
- Integrate with external services

The system uses a **modular architecture** where adding new features requires minimal changes to existing code.

---

## Prerequisites

Before extending Dev-Nexus, ensure you have:

- Python 3.11+ installed
- Development dependencies: `pip install -r requirements-dev.txt`
- Understanding of the core architecture (see [CLAUDE.md](CLAUDE.md))
- Local development environment set up

---

## Architecture Overview

### Modular Structure (v2.0)

```
dev-nexus/
├── a2a/
│   ├── server.py              # Thin coordinator (250 lines)
│   ├── executor.py            # Skill executor (74 lines)
│   ├── registry.py            # Skill registry
│   └── skills/                # Modular skills
│       ├── base.py            # BaseSkill interface
│       ├── pattern_query.py   # Pattern search skills
│       ├── repository_info.py # Repository skills
│       ├── knowledge_management.py # KB update skills
│       ├── integration.py     # External agent skills
│       └── documentation_standards.py # Doc checking skills
├── core/
│   ├── pattern_extractor.py   # Claude API integration
│   ├── knowledge_base.py      # KB management (v2 schema)
│   ├── similarity_finder.py   # Pattern matching
│   ├── integration_service.py # A2A coordination
│   └── documentation_standards_checker.py # Doc checker
└── scripts/
    └── pattern_analyzer.py     # CLI analyzer
```

**Key Principles:**
- **Skills are self-contained modules** - add new features by creating a single file
- **Dynamic AgentCard** - automatically generated from skill registry
- **Shared core logic** - GitHub Actions and A2A server use same modules

---

## Adding New A2A Skills

### Step 1: Create Skill Module

Create a new file in `a2a/skills/`:

```python
# a2a/skills/my_new_skill.py
"""
My New Feature Skill

Description of what this skill does.
"""

from typing import Dict, Any, List
from a2a.skills.base import BaseSkill


class MyNewSkill(BaseSkill):
    """Brief description of the skill"""

    @property
    def skill_id(self) -> str:
        """Unique identifier for this skill"""
        return "my_new_skill"

    @property
    def skill_name(self) -> str:
        """Human-readable name"""
        return "My New Skill"

    @property
    def skill_description(self) -> str:
        """What this skill does"""
        return "Performs some useful operation on the knowledge base"

    @property
    def tags(self) -> List[str]:
        """Tags for categorization"""
        return ["category", "feature", "action"]

    @property
    def requires_authentication(self) -> bool:
        """Whether this skill requires authentication"""
        return False  # Set to True if modifying data

    @property
    def input_schema(self) -> Dict[str, Any]:
        """JSON schema for input validation"""
        return {
            "type": "object",
            "properties": {
                "parameter1": {
                    "type": "string",
                    "description": "Description of parameter"
                },
                "parameter2": {
                    "type": "boolean",
                    "description": "Optional boolean parameter",
                    "default": False
                }
            },
            "required": ["parameter1"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        """Usage examples"""
        return [
            {
                "input": {
                    "parameter1": "example value",
                    "parameter2": True
                },
                "description": "Example usage description"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the skill

        Args:
            input_data: Validated input matching input_schema

        Returns:
            Dictionary with success status and results
        """
        try:
            # Extract parameters
            param1 = input_data.get('parameter1')
            param2 = input_data.get('parameter2', False)

            # Perform your logic here
            result = self._do_something(param1, param2)

            return {
                "success": True,
                "result": result,
                "message": "Operation completed successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _do_something(self, param1: str, param2: bool):
        """Helper method - implement your logic"""
        # Your implementation here
        return {"data": "example"}
```

### Step 2: Register the Skill

Edit `a2a/skills/__init__.py` to register your skill:

```python
from a2a.skills.my_new_skill import MyNewSkill

# Add to the registration list
def get_all_skills():
    return [
        # ... existing skills ...
        MyNewSkill(),
    ]
```

### Step 3: Test the Skill

```bash
# Start dev server
bash scripts/dev-server.sh

# Test your skill
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "my_new_skill",
    "input": {
      "parameter1": "test value"
    }
  }'
```

**That's it!** The skill is now:
- Available at `/a2a/execute`
- Listed in the AgentCard at `/.well-known/agent.json`
- Automatically validated and executed

---

## Examples

### Example 1: Pattern Statistics Skill

```python
# a2a/skills/pattern_statistics.py
from typing import Dict, Any, List
from a2a.skills.base import BaseSkill
from core.knowledge_base import KnowledgeBase


class PatternStatisticsSkill(BaseSkill):
    """Get statistical analysis of patterns across repositories"""

    @property
    def skill_id(self) -> str:
        return "get_pattern_statistics"

    @property
    def skill_name(self) -> str:
        return "Get Pattern Statistics"

    @property
    def skill_description(self) -> str:
        return "Calculate statistics about pattern usage across all repositories"

    @property
    def tags(self) -> List[str]:
        return ["patterns", "statistics", "analytics"]

    @property
    def requires_authentication(self) -> bool:
        return False

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "min_repos": {
                    "type": "integer",
                    "description": "Minimum number of repos pattern must appear in",
                    "default": 1
                }
            }
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {"min_repos": 2},
                "description": "Get patterns used in at least 2 repos"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            min_repos = input_data.get('min_repos', 1)

            # Load knowledge base
            kb = KnowledgeBase(repo_name="patelmm79/dev-nexus")
            data = kb.load()

            # Calculate statistics
            pattern_counts = {}
            for repo_data in data.get('repositories', {}).values():
                patterns = repo_data.get('latest_patterns', {}).get('patterns', [])
                for pattern in patterns:
                    pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

            # Filter by min_repos
            popular_patterns = {
                pattern: count
                for pattern, count in pattern_counts.items()
                if count >= min_repos
            }

            return {
                "success": True,
                "statistics": {
                    "total_patterns": len(pattern_counts),
                    "popular_patterns": popular_patterns,
                    "total_repositories": len(data.get('repositories', {}))
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

### Example 2: Webhook Notification Skill

```python
# a2a/skills/webhook_notify.py
from typing import Dict, Any, List
import requests
from a2a.skills.base import BaseSkill


class WebhookNotifySkill(BaseSkill):
    """Send custom webhook notifications"""

    @property
    def skill_id(self) -> str:
        return "send_webhook_notification"

    @property
    def skill_name(self) -> str:
        return "Send Webhook Notification"

    @property
    def skill_description(self) -> str:
        return "Send a custom notification to a webhook URL (Slack, Discord, etc.)"

    @property
    def tags(self) -> List[str]:
        return ["notification", "webhook", "integration"]

    @property
    def requires_authentication(self) -> bool:
        return True  # Requires auth to prevent abuse

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "webhook_url": {
                    "type": "string",
                    "description": "Webhook URL to send notification to"
                },
                "message": {
                    "type": "string",
                    "description": "Message content"
                },
                "severity": {
                    "type": "string",
                    "enum": ["info", "warning", "error"],
                    "default": "info"
                }
            },
            "required": ["webhook_url", "message"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "webhook_url": "https://discord.com/api/webhooks/...",
                    "message": "Pattern drift detected in repository X",
                    "severity": "warning"
                },
                "description": "Send warning notification"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            webhook_url = input_data['webhook_url']
            message = input_data['message']
            severity = input_data.get('severity', 'info')

            # Format for Discord/Slack
            payload = {
                "content": f"[{severity.upper()}] {message}"
            }

            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            return {
                "success": True,
                "message": "Notification sent successfully"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
```

---

## Customizing Pattern Extraction

### Modify the Claude Prompt

Edit `core/pattern_extractor.py` to change what patterns are extracted:

```python
def extract_patterns_with_llm(self, diff_text: str, repository: str, commit_sha: str):
    # Customize the prompt
    prompt = """
    Analyze this code change and extract:

    1. Architectural patterns (e.g., MVC, Repository, Factory)
    2. Security patterns (authentication, authorization, encryption)
    3. Performance optimizations
    4. YOUR CUSTOM CATEGORY HERE

    Focus on reusable patterns that might appear in other projects.
    """

    # Rest of the method...
```

### Add Custom Pattern Detectors

```python
# core/custom_patterns.py
import re

class CustomPatternDetector:
    """Detect domain-specific patterns"""

    def detect_ml_patterns(self, code: str) -> List[str]:
        """Detect machine learning patterns"""
        patterns = []

        if re.search(r'sklearn|tensorflow|pytorch', code):
            patterns.append("ML Framework Usage")

        if re.search(r'train.*model|fit\(', code):
            patterns.append("Model Training")

        if re.search(r'pickle|joblib\.dump', code):
            patterns.append("Model Serialization")

        return patterns

    def detect_api_patterns(self, code: str) -> List[str]:
        """Detect API design patterns"""
        patterns = []

        if re.search(r'@app\.route|@router\.(get|post)', code):
            patterns.append("REST API Endpoint")

        if re.search(r'async def.*request', code):
            patterns.append("Async API Handler")

        return patterns
```

---

## Extending the Knowledge Base Schema

### Add New Sections to v2 Schema

Edit `schemas/knowledge_base_v2.py`:

```python
class RepositoryData(BaseModel):
    # Existing fields...
    latest_patterns: PatternData
    deployment: DeploymentInfo
    dependencies: DependencyInfo

    # Add your custom section
    custom_metrics: Optional[CustomMetrics] = None


class CustomMetrics(BaseModel):
    """Your custom metrics"""
    code_quality_score: float = 0.0
    test_coverage: float = 0.0
    performance_metrics: Dict[str, Any] = {}
    last_measured: str = ""
```

### Update Pattern Analyzer

Modify `scripts/pattern_analyzer.py` to populate your new fields:

```python
def update_knowledge_base(self, patterns, repo):
    # ... existing code ...

    # Add custom metrics
    custom_metrics = {
        "code_quality_score": self.calculate_quality(diff),
        "test_coverage": self.get_test_coverage(repo),
        "last_measured": datetime.now().isoformat()
    }

    repo_data["custom_metrics"] = custom_metrics
```

---

## Adding Notification Channels

### Create Custom Notifier

```python
# core/notifiers/teams_notifier.py
import requests

class TeamsNotifier:
    """Send notifications to Microsoft Teams"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def notify(self, title: str, message: str, facts: List[Dict]):
        """
        Send Teams notification

        Args:
            title: Card title
            message: Main message
            facts: List of {"name": "...", "value": "..."} dicts
        """
        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": title,
            "sections": [{
                "activityTitle": title,
                "activitySubtitle": message,
                "facts": facts
            }]
        }

        response = requests.post(self.webhook_url, json=payload)
        response.raise_for_status()
```

### Use in Pattern Analyzer

```python
# scripts/pattern_analyzer.py
from core.notifiers.teams_notifier import TeamsNotifier

# In your main function
if os.environ.get('TEAMS_WEBHOOK_URL'):
    teams = TeamsNotifier(os.environ['TEAMS_WEBHOOK_URL'])
    teams.notify(
        title="Pattern Analysis Complete",
        message=f"Repository: {repo_name}",
        facts=[
            {"name": "Patterns Found", "value": str(len(patterns))},
            {"name": "Similar Repos", "value": str(len(similar))}
        ]
    )
```

---

## Testing Your Extensions

### Unit Tests

Create tests in `tests/`:

```python
# tests/test_my_skill.py
import pytest
from a2a.skills.my_new_skill import MyNewSkill


@pytest.mark.asyncio
async def test_my_new_skill():
    skill = MyNewSkill()

    # Test execution
    result = await skill.execute({
        "parameter1": "test"
    })

    assert result["success"] == True
    assert "result" in result


def test_skill_properties():
    skill = MyNewSkill()

    assert skill.skill_id == "my_new_skill"
    assert skill.requires_authentication == False
    assert "parameter1" in skill.input_schema["properties"]
```

### Integration Tests

```bash
# Start test server
bash scripts/dev-server.sh

# Run integration tests
pytest tests/integration/test_a2a_skills.py -v
```

---

## Deployment

### Update Cloud Run Deployment

After adding skills, redeploy:

```bash
# Update secrets if needed
bash scripts/setup-secrets.sh

# Deploy
bash scripts/deploy.sh

# Verify AgentCard includes new skill
curl https://your-service.run.app/.well-known/agent.json | jq '.skills'
```

---

## Best Practices

### 1. Follow the BaseSkill Interface

Always extend `BaseSkill` and implement all required properties:
- `skill_id`: Unique identifier
- `skill_name`: Human-readable name
- `skill_description`: Clear description
- `input_schema`: JSON schema for validation
- `execute()`: Async method that returns `Dict[str, Any]`

### 2. Use Descriptive Error Messages

```python
return {
    "success": False,
    "error": "Repository not found",
    "error_code": "REPO_NOT_FOUND",
    "suggestion": "Check the repository name format (owner/repo)"
}
```

### 3. Add Examples

Include realistic examples in the `examples` property to help users understand usage.

### 4. Authentication for Mutations

Set `requires_authentication = True` for skills that modify data.

### 5. Validate Input

Use JSON schema to validate input automatically. The framework handles validation before calling `execute()`.

### 6. Document Everything

Add docstrings to classes and methods. Your skill description appears in the AgentCard.

---

## Common Patterns

### Accessing Knowledge Base

```python
from core.knowledge_base import KnowledgeBase

kb = KnowledgeBase(repo_name="patelmm79/dev-nexus")
data = kb.load()
repositories = data.get('repositories', {})
```

### Calling External APIs

```python
import httpx

async def call_external_api(self, url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        return response.json()
```

### Using GitHub API

```python
import os
from github import Github

github_token = os.environ.get('GITHUB_TOKEN')
client = Github(github_token)
repo = client.get_repo("owner/repo")
```

---

## Troubleshooting

### Skill Not Appearing in AgentCard

**Problem**: New skill doesn't show in `/.well-known/agent.json`
**Solution**:
- Ensure skill is registered in `a2a/skills/__init__.py`
- Restart the server
- Check logs for import errors

### Input Validation Failing

**Problem**: Valid input rejected
**Solution**: Check your `input_schema` matches JSON Schema spec. Test with:

```python
from jsonschema import validate
validate(instance=your_input, schema=skill.input_schema)
```

### Authentication Issues

**Problem**: Authenticated skill rejects valid tokens
**Solution**:
- Check `ALLOWED_SERVICE_ACCOUNTS` environment variable
- Verify token format in Authorization header
- Check logs for authentication details

---

## See Also

- [CLAUDE.md](CLAUDE.md) - Complete architecture documentation
- [API.md](API.md) - API reference
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design
- [BaseSkill source](a2a/skills/base.py) - Skill interface definition

---

**Questions or issues?** Open an issue on GitHub or check the troubleshooting guides.
