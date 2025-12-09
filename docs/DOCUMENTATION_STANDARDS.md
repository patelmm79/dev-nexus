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

### 6. Licensed Properly

**All projects must include a LICENSE file with GNU General Public License v3.0 (GPL-3.0).**

**Requirements:**
- ✅ **LICENSE file** must exist in repository root
- ✅ Must contain the full **GNU GPL v3.0** text
- ✅ **README.md** must include GPL-3.0 badge
- ✅ Source files should include license header where appropriate

**Why GPL v3:**
- Ensures software freedom (free as in freedom)
- Copyleft protection (derivative works must be open source)
- Patent protection for users
- Compatible with other GPL projects
- Aligns with project values of openness and collaboration

**README Badge:**
```markdown
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
```

**Source File Header (optional but recommended):**
```python
# Copyright (C) 2025  Your Name
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
```

**Non-Compliance:**
- ❌ Missing LICENSE file
- ❌ Wrong license (MIT, Apache, proprietary)
- ❌ Modified GPL text (must be verbatim)
- ❌ No license indication in README

**License Checker:**
The documentation standards checker will verify:
1. LICENSE file exists
2. Contains "GNU GENERAL PUBLIC LICENSE" and "Version 3"
3. README includes GPL-3.0 badge or reference
4. License is consistent across all documentation

### 7. Organized for end users first.
- **Prioritise for consumption by end user persona**: main purpose of primary documents is to help the end user use the tools.  The next priority is to help the end user to deploy the tool.
- **Clear separation of concerns**: Technical details for developers should be separated into specific techical documents.
- **Table of contents**: Have a table of contents at the top of long documents, particularly README.md

### 8. Navigation and Findability

**Users should be able to find information quickly without searching.**

#### Required Navigation Elements

**README.md must have:**
- ✅ **Table of contents** at the top with quick links
- ✅ **Documentation index** section near the end
- ✅ **Task-based quick links** ("I want to deploy..." → link)
- ✅ **Clear separation** between overview and detailed content
- ✅ **Links to detailed guides** instead of including everything in README

**Example TOC Structure:**
```markdown
## 📚 Table of Contents

### Quick Links
- **[🚀 Quick Start](#-quick-start)** - Get started in 5 minutes
- **[☁️ Cloud Deployment](#️-deployment-to-cloud-run)** - Deploy to Cloud
- **[📖 Documentation Index](#-documentation-index)** - All documentation

### Main Sections
1. [Overview](#overview)
2. [Installation](#installation)
...
```

**Documentation Index Section:**
```markdown
## 📖 Documentation Index

### Quick Navigation by Task

**"I want to deploy to Cloud Run"**
→ [DEPLOYMENT.md](DEPLOYMENT.md)

**"Something is broken"**
→ [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### Getting Started
| Document | Purpose | Audience |
|----------|---------|----------|
| **[README.md](README.md)** | Project overview | Everyone |
| **[DEPLOYMENT.md](DEPLOYMENT.md)** | Deploy guide | DevOps |
```

#### DOCUMENTATION_INDEX.md

**Required:** Create `DOCUMENTATION_INDEX.md` as central navigation hub

**Must include:**
- ✅ Complete list of all documentation files
- ✅ Purpose and audience for each document
- ✅ Task-based navigation ("I want to..." → docs)
- ✅ Documentation by audience (DevOps, Developers, etc.)
- ✅ Reading order for common workflows
- ✅ Estimated time to complete tasks
- ✅ Documentation metrics (total docs, coverage)

**See:** [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) for example

#### Documentation Structure

**Organize by concern:**

**Root directory** (high-level, user-facing):
- `README.md` - Overview and quick start
- `DEPLOYMENT.md` - Production deployment
- `TROUBLESHOOTING.md` - Problem solving
- `INTEGRATION.md` - Integration guides
- `API.md` - API reference

**docs/ directory** (contributor-facing, standards):
- `DOCUMENTATION_STANDARDS.md` - This file
- `LICENSE_STANDARD.md` - Licensing requirements
- `LESSONS_LEARNED_ARCHITECTURE.md` - Architectural lessons

**examples/ directory** (learning by example):
- Real-world examples
- Step-by-step tutorials
- Integration scenarios

**terraform/ directory** (infrastructure):
- Infrastructure as code
- Deployment configurations

#### Cross-Linking

**Every document should link to related documents:**

**Bad Example:**
```markdown
To deploy, you need to set up secrets first.
```

**Good Example:**
```markdown
To deploy, you need to set up secrets first. See the
[Prerequisites](DEPLOYMENT.md#prerequisites) section
of the Deployment Guide for instructions.
```

**Link patterns:**
- Use descriptive link text (not "click here")
- Link to specific sections when possible
- Provide context for why user should follow link
- Keep links up to date when files move

#### Task-Based Organization

**Organize content by user tasks, not system components:**

**Bad: Component-based**
```markdown
## Server Component
The server runs the API...

## Database Component
The database stores patterns...
```

**Good: Task-based**
```markdown
## Deploying to Production
To deploy your service:
1. Set up infrastructure (see DEPLOYMENT.md#prerequisites)
2. Configure secrets (see DEPLOYMENT.md#secrets)
3. Deploy container (see DEPLOYMENT.md#deployment)
```

#### Audience-Specific Paths

**Provide clear paths for different audiences:**

**For New Users:**
1. README.md → Overview
2. QUICK_START.md → Get started
3. Examples → Learn by doing

**For DevOps:**
1. DEPLOYMENT.md → Deploy
2. TROUBLESHOOTING.md → Fix issues
3. PRODUCTION_READY.md → Go live

**For Developers:**
1. ARCHITECTURE.md → Understand system
2. EXTENDING_DEV_NEXUS.md → Add features
3. API.md → API reference

**Document these paths clearly in DOCUMENTATION_INDEX.md**

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

### Licensing
- [ ] LICENSE file exists in repository root
- [ ] LICENSE contains full GNU GPL v3.0 text
- [ ] README.md includes GPL-3.0 badge
- [ ] License is mentioned in documentation

### Navigation & Structure
- [ ] README.md has table of contents at top
- [ ] README.md has Documentation Index section
- [ ] README.md has task-based quick links
- [ ] DOCUMENTATION_INDEX.md exists and is current
- [ ] Proper headings hierarchy
- [ ] Prerequisites section
- [ ] Examples section
- [ ] Troubleshooting section

### Cross-Linking
- [ ] Links to related documents
- [ ] Descriptive link text (not "click here")
- [ ] Links to specific sections when useful
- [ ] All internal links work
- [ ] All external links work

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
