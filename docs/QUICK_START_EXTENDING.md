# Quick Start: Extending Dev-Nexus (Modular v2.0)

> **📢 UPDATED for v2.0**: This guide now uses the **modular architecture**.
> Skills are now separate files that auto-register - much simpler!

This quick start guide helps you add new functionality to dev-nexus in 10 minutes or less.

## What You'll Learn

- How to add a new skill using the modular architecture
- Where to put business logic
- How skills auto-register
- How to test your changes

## Prerequisites

- Dev-nexus repository cloned
- Python 3.11+ installed
- Virtual environment activated
- Required environment variables set:
  - `ANTHROPIC_API_KEY`
  - `GITHUB_TOKEN`
  - `KNOWLEDGE_BASE_REPO`

## 5-Minute Skill Addition (New Modular Way!)

### 1. Create Your Skill Module (3 minutes)

Create `a2a/skills/my_skill.py`:

```python
"""My Skill Module"""

from typing import Dict, Any, List
from a2a.skills.base import BaseSkill

class MySkill(BaseSkill):
    """My custom skill description"""

    def __init__(self, kb_manager):
        self.kb_manager = kb_manager

    @property
    def skill_id(self) -> str:
        return "my_skill"

    @property
    def skill_name(self) -> str:
        return "My Skill Name"

    @property
    def skill_description(self) -> str:
        return "What my skill does"

    @property
    def tags(self) -> List[str]:
        return ["tag1", "tag2"]

    @property
    def requires_authentication(self) -> bool:
        return False  # Set True if skill modifies data

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_param": {
                    "type": "string",
                    "description": "What this parameter does"
                }
            },
            "required": ["input_param"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {"input_param": "example"},
                "description": "Example description"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill"""
        try:
            input_param = input_data.get('input_param')

            if not input_param:
                return {
                    "success": False,
                    "error": "Missing required parameter: 'input_param'"
                }

            # Your logic here
            result = f"Processed: {input_param}"

            return {
                "success": True,
                "result": result
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed: {str(e)}"
            }
```

### 2. Register in Server (1 minute)

Edit `a2a/server.py` and add these 3 lines after the other skill imports (around line 72):

```python
from a2a.skills.my_skill import MySkill

# ... after other skill registrations (around line 72) ...
my_skill = MySkill(kb_manager)
registry.register(my_skill)
```

### 3. Test It! (1 minute)

**That's it!** No routing changes needed, no executor edits - the registry handles everything!

```bash
# Start server
python a2a/server.py

# Test skill
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{"skill_id": "my_skill", "input": {"input_param": "test"}}' | jq
```

## Real Example: Documentation Review Skill

We've created a complete documentation review agent as an example. Here's how to add it:

### Files Created

1. **`core/documentation_service.py`** - Business logic for reviewing docs
2. **`examples/add_documentation_review_skill.md`** - Step-by-step integration guide
3. **`docs/EXTENDING_DEV_NEXUS.md`** - Comprehensive extension guide

### Quick Integration (10 minutes)

Follow the steps in `examples/add_documentation_review_skill.md`:

1. Copy the skill definition to `a2a/server.py`
2. Copy the handler method to `a2a/executor.py`
3. Add routing
4. Test with your own repository

```bash
# Test the documentation review
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "review_documentation",
    "input": {
      "repository": "patelmm79/dev-nexus",
      "standards": ["completeness", "clarity", "examples"]
    }
  }' | jq
```

## Architecture Patterns

### Pattern 1: Simple Skill (No External Logic)

**When:** Skill logic is < 50 lines, no complex dependencies

**Where:** Directly in `executor.py` handler method

```python
async def _handle_simple_skill(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simple skill with inline logic"""
    param = input_data.get('param')

    # All logic here (< 50 lines)
    result = self._simple_processing(param)

    return {"success": True, "result": result}

def _simple_processing(self, param):
    """Private helper if needed"""
    return f"Processed: {param}"
```

### Pattern 2: Complex Skill (External Service)

**When:** Skill logic is > 50 lines, needs testing, or reusable

**Where:** Create `core/your_service.py`

```python
# core/my_service.py
class MyService:
    def __init__(self, kb_manager, similarity_finder):
        self.kb_manager = kb_manager
        self.similarity_finder = similarity_finder

    def process(self, input_data):
        """Complex logic here"""
        # ... 100+ lines of logic ...
        return result
```

Then use in executor:

```python
# In executor.py
async def _handle_complex_skill(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Complex skill using external service"""
    from core.my_service import MyService

    service = MyService(self.kb_manager, self.similarity_finder)
    result = service.process(input_data)

    return {"success": True, "result": result}
```

### Pattern 3: Authenticated Skill

**When:** Skill modifies data or is sensitive

**Steps:**

1. Set `requires_authentication: true` in AgentCard
2. Add skill_id to `PROTECTED_SKILLS` in `a2a/auth.py`:

```python
def is_skill_protected(skill_id: str) -> bool:
    PROTECTED_SKILLS = [
        "add_lesson_learned",
        "update_dependency_info",
        "my_protected_skill"  # Add here
    ]
    return skill_id in PROTECTED_SKILLS
```

3. Authentication is checked automatically before handler is called

## Common Tasks

### Access Knowledge Base

```python
# In your handler
kb = self.kb_manager.load_knowledge_base()

# Get specific repository
if repository in kb.repositories:
    repo_info = kb.repositories[repository]
    patterns = repo_info.latest_patterns.patterns
    keywords = repo_info.latest_patterns.keywords
```

### Query Similar Patterns

```python
# In your handler
matches = self.similarity_finder.find_by_keywords(
    keywords=["retry", "exponential backoff"],
    kb=kb,
    min_matches=2,
    top_k=5
)
```

### Call External Agent

```python
# In your handler
from core.integration_service import IntegrationService

integration = IntegrationService()

# Call dependency-orchestrator
result = integration.get_dependency_impact(repository)

# Call pattern-miner
analysis = integration.request_deep_pattern_analysis(repository)
```

### Use Claude API

```python
# In your service class
import anthropic
import os

anthropic_client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

response = anthropic_client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1000,
    messages=[{
        "role": "user",
        "content": "Your prompt here"
    }]
)

result = response.content[0].text
```

### Access GitHub

```python
# In your handler
import os
from github import Github

github_client = Github(os.environ.get('GITHUB_TOKEN'))
repo = github_client.get_repo("owner/repo")

# Get file content
file_content = repo.get_contents("README.md")
content = file_content.decoded_content.decode('utf-8')

# List files
contents = repo.get_contents("src/")
for content in contents:
    print(content.path)
```

## Testing Patterns

### Unit Test

```python
# tests/test_my_service.py
import pytest
from core.my_service import MyService

@pytest.fixture
def service(mock_kb_manager, mock_similarity_finder):
    return MyService(mock_kb_manager, mock_similarity_finder)

def test_process_success(service):
    result = service.process({"input": "test"})
    assert result["success"] == True

def test_process_error(service):
    result = service.process({})
    assert result["success"] == False
    assert "error" in result
```

### Integration Test

```python
# tests/test_executor.py
import pytest
from a2a.executor import PatternDiscoveryExecutor

@pytest.mark.asyncio
async def test_my_skill(executor):
    result = await executor.execute(
        "my_skill",
        {"input_param": "test"}
    )

    assert result["success"] == True
    assert "result" in result
```

### Manual Test

```bash
# Test via curl
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{"skill_id": "my_skill", "input": {"input_param": "test"}}' | jq

# Test via Python
from a2a.client import A2AClient

client = A2AClient("http://localhost:8080")
result = client.execute_skill("my_skill", {"input_param": "test"})
print(result)
```

## Deployment Checklist

### Before Deploying

- [ ] Skill tested locally
- [ ] Error handling added
- [ ] Input validation complete
- [ ] Documentation updated (CLAUDE.md)
- [ ] Examples added to AgentCard
- [ ] Unit tests written (if complex logic)

### Deploy to Cloud Run

```bash
# Set up secrets (first time only)
bash scripts/setup-secrets.sh

# Deploy
bash scripts/deploy.sh

# Test deployed service
SERVICE_URL=$(gcloud run services describe pattern-discovery-agent \
  --region=us-central1 --format="value(status.url)")

curl ${SERVICE_URL}/.well-known/agent.json | jq '.skills[] | select(.id == "my_skill")'

curl -X POST ${SERVICE_URL}/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{"skill_id": "my_skill", "input": {"input_param": "test"}}' | jq
```

## Next Steps

### Option 1: Implement Documentation Review

Follow `examples/add_documentation_review_skill.md` to add the documentation review capability.

**Time:** 10-15 minutes
**Benefit:** Immediate value - review your own docs!

### Option 2: Create Your Own Skill

Use the patterns above to create a skill specific to your needs:

**Ideas:**
- Code quality analyzer
- Dependency vulnerability scanner
- Performance profiler
- Test coverage analyzer
- API compatibility checker
- Security pattern validator

### Option 3: Create a Standalone Agent

For more complex functionality, create a new agent:

**See:** `docs/EXTENDING_DEV_NEXUS.md` - "Creating Standalone Agents" section

**When to create standalone agent:**
- Needs its own data storage
- Has 5+ related skills
- Requires different authentication
- Needs separate scaling/deployment
- Has external dependencies

## Troubleshooting

### Skill not working

```bash
# Check server logs
python a2a/server.py

# Look for error messages when testing the skill
```

### AgentCard not updated

```bash
# Verify JSON syntax
curl http://localhost:8080/.well-known/agent.json | jq

# Look for parsing errors in server output
```

### Import errors

```bash
# Make sure you're in project root
cd /path/to/architecture-kb

# Activate virtual environment
source venv/bin/activate  # Unix
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Authentication issues

```bash
# Check environment variables
echo $ANTHROPIC_API_KEY
echo $GITHUB_TOKEN

# For protected skills, test with auth token
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"skill_id": "my_skill", "input": {}}' | jq
```

## Resources

- **Comprehensive Guide:** `docs/EXTENDING_DEV_NEXUS.md`
- **Example Implementation:** `examples/add_documentation_review_skill.md`
- **Documentation Service:** `core/documentation_service.py`
- **Main Documentation:** `CLAUDE.md`
- **A2A Protocol:** [Anthropic A2A Specification](https://github.com/anthropics/anthropic-a2a)

## Questions?

Check the main documentation or examine existing skills:
- `query_patterns` - Simple read-only skill
- `add_lesson_learned` - Authenticated write skill
- `get_cross_repo_patterns` - Complex aggregation skill
- `review_documentation` - AI-powered analysis skill (example)

Happy extending! 🚀
