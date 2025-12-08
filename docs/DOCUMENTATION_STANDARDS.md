# Documentation Standards

## Overview

This document defines standards for documentation in the dev-nexus project. These standards should be enforced by the documentation review agent and followed by all contributors.

---

## Critical Standard: Complete Documentation Updates

### Principle

> **"After major changes, ALL documentation must be updated - no exceptions."**

When making architectural changes, code refactoring, or feature additions, you must update:
- ✅ **All** guides and tutorials that reference the changed code
- ✅ **All** examples that demonstrate the changed functionality
- ✅ **All** architectural documentation
- ✅ **All** quick-start guides
- ✅ **README** and **CLAUDE.md** overview sections

### Why This Matters

**Partial documentation updates are worse than no updates:**
- Users follow outdated guides and get errors
- New contributors learn incorrect patterns
- Technical debt accumulates invisibly
- Trust in documentation erodes

### Real Example: Modular Refactoring

When we refactored from monolithic to modular architecture:

**What Changed:**
- Executor.py reduced 484 → 74 lines
- Server.py reduced 445 → 250 lines
- Skills moved to separate modules
- Adding skills changed from "edit 2-3 files" to "create 1 file"

**Documentation That Needed Updates:**
1. ✅ CLAUDE.md - System Components section
2. ✅ EXTENDING_DEV_NEXUS.md - Architecture overview
3. ✅ QUICK_START_EXTENDING.md - Skill addition process
4. ✅ examples/add_documentation_review_skill.md - Integration example
5. ✅ LESSONS_LEARNED_ARCHITECTURE.md - Added lessons
6. ✅ REFACTORING_COMPLETE.md - Created migration guide

**If we had skipped any of these**, users would:
- Follow old monolithic patterns
- Get confused by mismatched documentation
- Waste time debugging "broken" instructions
- Lose confidence in the documentation

---

## Core Standards

### 1. Consistency

**All documentation must use consistent:**
- Terminology (e.g., "skill" not "handler" or "capability")
- Code examples (matching current architecture)
- File paths and references
- Command syntax

**Bad Example:**
```markdown
# File A says:
Edit `a2a/executor.py` to add a skill

# File B says:
Create `a2a/skills/my_skill.py` for new skills

# Result: Confusion!
```

**Good Example:**
```markdown
# All files say:
Create a skill module in `a2a/skills/` using the BaseSkill interface
```

### 2. Completeness

Documentation must include:
- **Overview**: What it does
- **Prerequisites**: What's needed
- **Step-by-step**: How to do it
- **Examples**: Working code samples
- **Testing**: How to verify it works
- **Troubleshooting**: Common issues

**Missing any of these = incomplete documentation.**

### 3. Accuracy

- ✅ All code examples must be tested and work
- ✅ All file paths must be correct
- ✅ All commands must execute successfully
- ✅ All version numbers must be current

**Test your examples!** If the code doesn't run, fix it.

### 4. Clarity

- Use simple language
- Define jargon on first use
- Break complex topics into steps
- Use visual aids (diagrams, tables, examples)
- Be specific and complete in giving instructions

**Clarity test**: Can a new contributor follow this without asking questions?

### 5. Up-to-date

- **Version indicators**: Mark documentation with version (e.g., "v2.0", "Updated: 2025-01-10")
- **Deprecation notices**: Mark outdated docs clearly
- **Migration guides**: Provide upgrade paths
- **Update stamps**: Add "Last updated" dates

**Example:**
```markdown
> **📢 UPDATED for v2.0**: This guide now uses the modular architecture.
> See MIGRATION_GUIDE.md if upgrading from v1.0.
```
### 6. Organized for end users first.
- **Prioritise for consumption by end user persona**: main purpose of primary documents is to help the end user use the tools.  The next priority is to help the end user to deploy the tool.
- **Clear separation of concerns**: Technical details for developers should be separated into specific techical documents.
- **Table of contents**: Have a table of contents at the top of long documents, particularly README.md

---

## Documentation Hierarchy

### Priority 1: CRITICAL (Must Always Be Current)

These docs are the first thing users see:

1. **README.md** - Project overview
2. **CLAUDE.md** - AI assistant guidance
3. **QUICK_START.md** - Getting started guide

**Update immediately** after any change affecting:
- Core architecture
- Installation process
- Primary use cases

### Priority 2: HIGH (Update with Feature Changes)

Feature-specific documentation:

4. **EXTENDING_DEV_NEXUS.md** - How to add features
5. **API.md** / **AgentCard** - Public interfaces
6. **examples/** - Working examples

**Update when:**
- Adding/removing features
- Changing APIs
- Modifying patterns

### Priority 3: MEDIUM (Update with Architecture Changes)

Deep-dive documentation:

7. **ARCHITECTURE.md** - System design
8. **LESSONS_LEARNED.md** - Best practices
9. **TROUBLESHOOTING.md** - Common issues

**Update when:**
- Refactoring code
- Changing patterns
- Learning lessons

### Priority 4: LOW (Nice to Have)

Supplementary docs:

10. **CONTRIBUTING.md** - Contribution guidelines
11. **CHANGELOG.md** - Version history
12. **FAQ.md** - Frequently asked questions

**Update opportunistically.**

---

## Documentation Checklist

Use this checklist for major changes:

### Before Making Changes
- [ ] Identify all documentation that references the code being changed
- [ ] Create a list of files that will need updates
- [ ] Consider what new documentation might be needed

### While Making Changes
- [ ] Update inline code comments
- [ ] Update docstrings
- [ ] Note breaking changes for migration guide

### After Making Changes
- [ ] Update all identified documentation files
- [ ] Add version indicators (e.g., "v2.0") where appropriate
- [ ] Test all code examples
- [ ] Verify all file paths are correct
- [ ] Check internal links work
- [ ] Add migration guide if breaking changes
- [ ] Update CHANGELOG

### Before Committing
- [ ] Review diff of documentation changes
- [ ] Ensure consistency across all updated docs
- [ ] Verify examples work
- [ ] Check for orphaned references to old code

---

## Anti-Patterns to Avoid

### ❌ "I'll update docs later"
**Problem**: "Later" never comes
**Solution**: Update docs in the same commit as code changes

### ❌ "This is just a small change"
**Problem**: Small changes cascade
**Solution**: Even small changes need doc updates if they affect user-facing behavior

### ❌ "The code is self-documenting"
**Problem**: Code shows "what", not "why" or "how to use"
**Solution**: Code + documentation work together

### ❌ "Just update the main docs"
**Problem**: Examples and tutorials become outdated
**Solution**: Update ALL documentation

### ❌ "We can fix it if someone complains"
**Problem**: Users lose trust before complaining
**Solution**: Prevent problems proactively

---

## Standards for Specific Document Types

### Code Examples

```markdown
## Good Example Structure

### Step 1: Setup
Brief explanation of what we're doing.

### Step 2: Implementation
\`\`\`python
# Actual working code
# With helpful comments
\`\`\`

### Step 3: Testing
\`\`\`bash
# Command that users can copy-paste
python test_example.py
\`\`\`

### Expected Output
\`\`\`
Success! (actual output shown here)
\`\`\`
```

### Architecture Diagrams

Use ASCII art or Mermaid for diagrams:

```
Good:
dev-nexus/
├── a2a/
│   ├── server.py
│   └── skills/
│       ├── pattern_query.py
│       └── repository_info.py
```

### API Documentation

```markdown
### skill_name

**Description**: What it does

**Authentication**: Required/Optional

**Input Schema**:
\`\`\`json
{
  "parameter": "description"
}
\`\`\`

**Output Schema**:
\`\`\`json
{
  "result": "description"
}
\`\`\`

**Example**:
\`\`\`bash
curl -X POST http://...
\`\`\`
```

---

## Review Process

### Self-Review

Before committing, ask:
1. Is this accurate? (Test it!)
2. Is this complete? (All steps included?)
3. Is this consistent? (Matches other docs?)
4. Is this clear? (Can others follow it?)
5. Is this current? (Reflects latest code?)

### Automated Checks

The documentation review agent should check:
- ✅ All code examples compile/execute
- ✅ All file paths exist
- ✅ All internal links work
- ✅ All required sections present
- ✅ Update stamps are recent
- ✅ Version indicators match

### Manual Review

Peer reviewers should verify:
- Technical accuracy
- Completeness
- Clarity for target audience
- Consistent terminology

---

## Metrics of Good Documentation

### Quantitative
- **Coverage**: % of features documented
- **Accuracy**: % of examples that work
- **Freshness**: Days since last update
- **Completeness**: % of required sections present

### Qualitative
- **Usability**: Can users follow without help?
- **Findability**: Can users find the right doc?
- **Clarity**: Is it understandable?
- **Trustworthiness**: Are users confident in it?

---

## Special Cases

### Breaking Changes

When making breaking changes:
1. Mark old docs with deprecation notice
2. Create migration guide
3. Update examples to new way
4. Show old way → new way comparison
5. Provide timeline for removal

### Experimental Features

Mark as experimental:
```markdown
> **⚠️ EXPERIMENTAL**: This feature is experimental and may change.
> Not recommended for production use.
```

### Platform-Specific

Clearly mark platform differences:
```markdown
# Windows
\`\`\`bash
venv\Scripts\activate
\`\`\`

# Unix/Mac
\`\`\`bash
source venv/bin/activate
\`\`\`
```

---

## Documentation Standards Checklist

Use this for documentation review:

### Content
- [ ] Accurate (all information correct)
- [ ] Complete (all necessary information included)
- [ ] Current (reflects latest code)
- [ ] Clear (easy to understand)
- [ ] Consistent (matches other docs)

### Structure
- [ ] Proper headings hierarchy
- [ ] Table of contents (if long)
- [ ] Prerequisites section
- [ ] Examples section
- [ ] Troubleshooting section

### Code Examples
- [ ] All examples tested
- [ ] All examples work
- [ ] Syntax highlighting correct
- [ ] Input/output shown
- [ ] Platform differences noted

### Links & References
- [ ] All internal links work
- [ ] All external links work
- [ ] All file paths correct
- [ ] All API references accurate

### Maintenance
- [ ] Version indicator present
- [ ] Last updated stamp present
- [ ] Deprecation notices if applicable
- [ ] Migration guide if breaking changes

---

## Enforcement

### For Contributors

- Documentation updates are **required** in the same PR as code changes
- PRs with outdated docs will be rejected
- Use the checklist above for all documentation changes

### For Reviewers

- Verify all documentation in checklist is updated
- Test code examples work
- Check consistency with other docs
- Ensure version indicators are present

### For Documentation Agent

The future documentation review agent should:
- Automatically check these standards
- Flag violations in PRs
- Suggest fixes
- Track documentation quality metrics
- Alert when docs become stale

---

## Summary

**The Golden Rule of Documentation:**

> **"When you change the code, change the docs. When you change the architecture, change ALL the docs."**

**No exceptions.** Outdated documentation is worse than no documentation because it actively misleads users and erodes trust.

---

**Document Status**: Living Standard
**Last Updated**: 2025-01-10
**Review Cycle**: After each major change
**Owner**: All contributors
**Enforced By**: Code review + Documentation agent (future)

---

## See Also

- [LESSONS_LEARNED_ARCHITECTURE.md](./LESSONS_LEARNED_ARCHITECTURE.md) - Architectural lessons
- [REFACTORING_COMPLETE.md](./REFACTORING_COMPLETE.md) - Example of complete doc updates
- [EXTENDING_DEV_NEXUS.md](./EXTENDING_DEV_NEXUS.md) - Extension guide
