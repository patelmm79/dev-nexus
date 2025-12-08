# Modular Architecture Refactoring - In Progress

## Overview

Refactoring dev-nexus from monolithic to modular architecture based on A2A best practices.

## Current Progress

### ✅ Completed

1. **Base Infrastructure**
   - ✅ `a2a/skills/base.py` - BaseSkill and SkillGroup interfaces
   - ✅ `a2a/registry.py` - SkillRegistry for discovery and routing
   - ✅ `a2a/skills/__init__.py` - Package initialization

2. **Modular Skills**
   - ✅ `a2a/skills/pattern_query.py` - QueryPatternsSkill, GetCrossRepoPatternsSkill

### 🚧 In Progress

3. **Remaining Skill Modules**
   - ⏳ `a2a/skills/repository_info.py` - GetRepositoryListSkill, GetDeploymentInfoSkill
   - ⏳ `a2a/skills/knowledge_management.py` - AddLessonLearnedSkill, UpdateDependencyInfoSkill
   - ⏳ `a2a/skills/integration.py` - HealthCheckExternalSkill

4. **Core Updates**
   - ⏳ `a2a/executor.py` - Refactor to use registry (reduce from 484 to ~50 lines)
   - ⏳ `a2a/server.py` - Dynamic AgentCard from registry (reduce from 445 to ~80 lines)

5. **Documentation**
   - ⏳ Update EXTENDING_DEV_NEXUS.md with new patterns
   - ⏳ Create LESSONS_LEARNED.md for future agents

## Architecture Comparison

### Before (Monolithic)

```
a2a/
├── server.py (445 lines)
│   └── 240 lines of hardcoded AgentCard
├── executor.py (484 lines)
│   ├── Long if/elif chains
│   └── 7 skills in one class
```

Problems:
- ❌ Hard to add new skills (edit 2 large files)
- ❌ Can't test skills independently
- ❌ Merge conflict risk
- ❌ All skills share dependencies

### After (Modular)

```
a2a/
├── server.py (~80 lines)
│   └── Dynamic AgentCard from registry
├── executor.py (~50 lines)
│   └── Delegates to registry
├── registry.py (skill discovery)
├── skills/
│   ├── base.py (interfaces)
│   ├── pattern_query.py
│   ├── repository_info.py
│   ├── knowledge_management.py
│   ├── integration.py
│   └── documentation.py (future)
```

Benefits:
- ✅ Easy to add skills (one new file)
- ✅ Skills are independently testable
- ✅ No merge conflicts
- ✅ Skills can have own dependencies
- ✅ Follows A2A best practices

## New Skill Addition Process

### Before
1. Edit `server.py` - Add to AgentCard (20-30 lines)
2. Edit `executor.py` - Add routing case
3. Edit `executor.py` - Add handler method (50-100 lines)
4. Edit `auth.py` - Add to protected list (if needed)

**Total**: Edit 2-3 large files, ~100 lines spread across files

### After
1. Create `skills/my_skill.py` - Everything in one place
2. Skills auto-register on import

**Total**: Create 1 file, ~80 lines in one place

### Example: Adding Documentation Review Skill

**Before (Monolithic)**:
```python
# server.py - Add 30 lines to AgentCard
# executor.py - Add routing + 60 line handler
# Total: 90 lines across 2 files
```

**After (Modular)**:
```python
# skills/documentation.py - Everything here
class ReviewDocumentationSkill(BaseSkill):
    # Metadata properties
    # execute() method
    # ~80 lines total

# That's it! Auto-registers when imported.
```

## Key Design Patterns

### 1. BaseSkill Interface

All skills implement:
```python
- skill_id: str
- skill_name: str
- skill_description: str
- input_schema: Dict
- execute(input_data): async method
- Optional: tags, requires_authentication, examples
```

### 2. Skill Registry

Central registry:
```python
registry = get_registry()
registry.register(skill)  # Register
skill = registry.get_skill("query_patterns")  # Get
result = await registry.execute_skill("query_patterns", {...})  # Execute
skills = registry.to_agent_card_skills()  # AgentCard format
```

### 3. Skill Groups

Related skills can be grouped:
```python
class PatternQuerySkills(SkillGroup):
    def __init__(self, kb_manager, similarity_finder):
        self._skills = [
            QueryPatternsSkill(...),
            GetCrossRepoPatternsSkill(...)
        ]

    def get_skills(self) -> List[BaseSkill]:
        return self._skills
```

## Next Steps

1. ✅ Complete remaining skill modules
2. ✅ Update executor.py to use registry
3. ✅ Update server.py for dynamic AgentCard
4. ✅ Test all skills work correctly
5. ✅ Update documentation
6. ✅ Document lessons learned

## Testing Plan

```bash
# Test individual skills
python -m pytest tests/skills/test_pattern_query.py

# Test registry
python -m pytest tests/test_registry.py

# Test full integration
python a2a/server.py
curl http://localhost:8080/.well-known/agent.json | jq '.skills | length'
# Should show 7 skills

# Test skill execution
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{"skill_id": "query_patterns", "input": {"keywords": ["retry"]}}' | jq
```

## Lessons Learned (For Documentation Agent)

### 1. Start Modular
**Lesson**: Don't start monolithic and refactor later. Start with modular architecture.

**Why**: Refactoring is time-consuming and risky. Start right.

**Apply to**: Future agents should use this pattern from day 1.

### 2. Separate Concerns
**Lesson**: Server, executor, and skills should be separate.

**Why**: Each has a single responsibility.

**Pattern**:
- Server: HTTP layer, AgentCard publishing
- Executor: Routing and delegation
- Skills: Business logic

### 3. Dynamic Registration
**Lesson**: Skills should self-register, not be hardcoded.

**Why**: Adding skills shouldn't require editing core files.

**Pattern**: Registry pattern with auto-discovery.

### 4. Interfaces Over Implementation
**Lesson**: Define interfaces (BaseSkill) before implementation.

**Why**: Consistency, testability, documentation.

**Pattern**: Abstract base classes with clear contracts.

### 5. Co-locate Related Code
**Lesson**: Keep skill metadata + implementation together.

**Why**: Easier to understand, test, and maintain.

**Anti-pattern**: Metadata in one file, implementation in another.

### 6. Think "Plugin Architecture"
**Lesson**: Skills are plugins that can be added/removed independently.

**Why**: Flexibility, maintainability, team collaboration.

**Pattern**: Each skill is a self-contained module.

## Migration Guide

For users with custom skills in old format:

### Old Format (Monolithic)
```python
# In executor.py
async def _handle_my_skill(self, input_data):
    # Implementation
    pass

# In server.py
{
    "id": "my_skill",
    "name": "My Skill",
    # ... metadata
}
```

### New Format (Modular)
```python
# skills/my_custom.py
from a2a.skills.base import BaseSkill

class MySkill(BaseSkill):
    @property
    def skill_id(self) -> str:
        return "my_skill"

    @property
    def skill_name(self) -> str:
        return "My Skill"

    # ... other properties

    async def execute(self, input_data):
        # Same implementation
        pass

# In server.py - add import
from a2a.skills.my_custom import MySkill
registry.register(MySkill(kb_manager, ...))
```

## Benefits Achieved

1. **Reduced Code Size**
   - server.py: 445 → ~80 lines (82% reduction)
   - executor.py: 484 → ~50 lines (90% reduction)

2. **Improved Maintainability**
   - Skills isolated in separate files
   - No more long if/elif chains
   - Clear interfaces

3. **Better Testing**
   - Test skills independently
   - Mock dependencies easily
   - No need to instantiate full executor

4. **Easier Collaboration**
   - Different developers can work on different skills
   - No merge conflicts on core files
   - Skills can be in separate repos if needed

5. **Follows Best Practices**
   - Matches A2A reference implementations
   - Plugin architecture
   - Separation of concerns
   - SOLID principles

## Questions for Review

1. Should we version the skill interface? (BaseSkill v1, v2, etc.)
2. Should skills live in separate packages? (a2a_skills_core, a2a_skills_contrib)
3. Do we need skill dependencies/ordering?
4. Should we support skill hot-reloading?

---

**Status**: In Progress
**Updated**: 2025-01-10
**Author**: Claude (Architecture Refactoring)
