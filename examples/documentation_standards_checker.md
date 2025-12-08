# Documentation Standards Checker

This guide shows how to use the documentation standards checker skills to validate repository documentation conformity.

## Overview

The documentation standards checker enforces the standards defined in `docs/DOCUMENTATION_STANDARDS.md`. It provides two skills:

1. **`check_documentation_standards`** - Check repository documentation for standards conformity
2. **`validate_documentation_update`** - Validate that docs were updated after code changes

## Skill 1: Check Documentation Standards

### Description

Checks repository documentation files against comprehensive standards including:
- **Completeness**: Required sections present
- **Accuracy**: Valid file paths, working code examples
- **Consistency**: Terminology, code examples, commands
- **Up-to-date**: Version indicators, update stamps
- **Code Examples**: Proper formatting, language specifiers
- **Internal Links**: Valid markdown links

### Input Schema

```json
{
  "repository": "owner/repo",      // Required
  "check_all_docs": false          // Optional, default: false
}
```

**Parameters**:
- `repository` (string, required): Repository in format "owner/repo"
- `check_all_docs` (boolean, optional):
  - `false` (default): Check priority files only (README.md, CLAUDE.md, etc.)
  - `true`: Check all .md files in repository

### Output Schema

```json
{
  "success": true,
  "repository": "owner/repo",
  "status": "compliant|mostly_compliant|needs_improvement|non_compliant",
  "status_emoji": "✅|👍|⚠️|❌",
  "compliance_score": 0.95,
  "summary": {
    "total_files_checked": 5,
    "total_violations": 3,
    "critical_violations": 0,
    "high_violations": 1,
    "medium_violations": 2
  },
  "file_results": [...],
  "critical_violations": [...],
  "recommendations": [...]
}
```

**Status Values**:
- `compliant` (✅): No violations, documentation meets all standards
- `mostly_compliant` (👍): Minor violations, mostly good
- `needs_improvement` (⚠️): High-priority violations need attention
- `non_compliant` (❌): Critical violations, immediate action required

### Examples

#### Example 1: Check Priority Files Only

```bash
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "check_documentation_standards",
    "input": {
      "repository": "patelmm79/dev-nexus",
      "check_all_docs": false
    }
  }' | jq
```

**Response**:
```json
{
  "success": true,
  "repository": "patelmm79/dev-nexus",
  "status": "compliant",
  "status_emoji": "✅",
  "compliance_score": 0.98,
  "summary": {
    "total_files_checked": 3,
    "total_violations": 1,
    "critical_violations": 0,
    "high_violations": 0,
    "medium_violations": 1
  },
  "file_results": [
    {
      "file": "README.md",
      "priority": "critical",
      "violations": [],
      "checks_performed": 6,
      "violation_count": 0
    },
    {
      "file": "CLAUDE.md",
      "priority": "critical",
      "violations": [
        {
          "type": "missing_update_stamp",
          "severity": "medium",
          "message": "Critical-priority file missing version indicator or update stamp",
          "file": "CLAUDE.md",
          "recommendation": "Add 'Last Updated: YYYY-MM-DD' or version indicator"
        }
      ],
      "checks_performed": 6,
      "violation_count": 1
    }
  ],
  "critical_violations": [],
  "recommendations": [
    "📝 MEDIUM: Add version indicators and update stamps to documentation",
    "Add 'Last Updated' stamps to documentation files"
  ]
}
```

#### Example 2: Comprehensive Check (All Documentation)

```bash
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "check_documentation_standards",
    "input": {
      "repository": "patelmm79/dev-nexus",
      "check_all_docs": true
    }
  }' | jq
```

#### Example 3: Check External Repository

```bash
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "check_documentation_standards",
    "input": {
      "repository": "your-org/your-project"
    }
  }' | jq
```

## Skill 2: Validate Documentation Update

### Description

Validates that documentation has been updated after code changes. Checks commit history to ensure documentation changes accompany code modifications.

**Use Case**: Enforce the critical standard: "After major changes, ALL documentation must be updated."

### Input Schema

```json
{
  "repository": "owner/repo",      // Required
  "since_commit": "abc123",        // Optional
  "days": 7                        // Optional, default: 7
}
```

**Parameters**:
- `repository` (string, required): Repository in format "owner/repo"
- `since_commit` (string, optional): Check changes since this commit SHA
- `days` (integer, optional): Check last N days if since_commit not provided (default: 7)

### Output Schema

```json
{
  "success": true,
  "repository": "owner/repo",
  "timeframe": {
    "since_date": "2025-01-03T00:00:00",
    "since_commit": null
  },
  "validation": {
    "status": "compliant|non_compliant|no_changes",
    "message": "..."
  },
  "changes": {
    "code_files": 5,
    "doc_files": 3,
    "code_changes": [...],
    "doc_changes": [...]
  },
  "warnings": [...],
  "recommendations": [...]
}
```

**Validation Status**:
- `compliant`: Documentation updates found with code changes
- `non_compliant`: Code changes without documentation updates
- `no_changes`: No code changes in timeframe

### Examples

#### Example 1: Check Last 7 Days

```bash
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "validate_documentation_update",
    "input": {
      "repository": "patelmm79/dev-nexus",
      "days": 7
    }
  }' | jq
```

**Response** (Non-compliant):
```json
{
  "success": true,
  "repository": "patelmm79/dev-nexus",
  "timeframe": {
    "since_date": "2025-01-03T00:00:00",
    "since_commit": null
  },
  "validation": {
    "status": "non_compliant",
    "message": "Code changes without corresponding documentation updates"
  },
  "changes": {
    "code_files": 5,
    "doc_files": 0,
    "code_changes": [
      {
        "file": "a2a/server.py",
        "commit": "a605963",
        "date": "2025-01-09T10:30:00",
        "message": "Add bidirectional A2A integration"
      },
      {
        "file": "core/pattern_extractor.py",
        "commit": "b123456",
        "date": "2025-01-08T14:20:00",
        "message": "Refactor pattern extraction"
      }
    ],
    "doc_changes": []
  },
  "warnings": [
    {
      "severity": "high",
      "message": "Code changes detected (5 files) but no documentation updates found",
      "recommendation": "Review and update documentation to reflect code changes"
    },
    {
      "severity": "critical",
      "message": "Core architecture changes detected (2 files) with no documentation updates",
      "recommendation": "Update ALL documentation per DOCUMENTATION_STANDARDS.md"
    }
  ],
  "recommendations": [
    "⚠️ Review DOCUMENTATION_STANDARDS.md for update requirements",
    "📝 Update documentation to reflect recent code changes",
    "✅ Add version indicators or 'Last Updated' stamps",
    "🔴 CRITICAL: Update ALL documentation after architecture changes"
  ]
}
```

#### Example 2: Check Since Specific Commit

```bash
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "validate_documentation_update",
    "input": {
      "repository": "patelmm79/dev-nexus",
      "since_commit": "a605963"
    }
  }' | jq
```

## Integration Patterns

### Pattern 1: CI/CD Pre-merge Check

Add to GitHub Actions workflow:

```yaml
name: Documentation Standards Check
on: pull_request

jobs:
  check-docs:
    runs-on: ubuntu-latest
    steps:
      - name: Check Documentation Standards
        run: |
          curl -X POST https://your-a2a-server/a2a/execute \
            -H "Content-Type: application/json" \
            -d '{
              "skill_id": "check_documentation_standards",
              "input": {
                "repository": "${{ github.repository }}",
                "check_all_docs": true
              }
            }' | jq '.status' | grep -q "compliant" || exit 1

      - name: Validate Docs Updated
        run: |
          curl -X POST https://your-a2a-server/a2a/execute \
            -H "Content-Type: application/json" \
            -d '{
              "skill_id": "validate_documentation_update",
              "input": {
                "repository": "${{ github.repository }}",
                "days": 1
              }
            }' | jq '.validation.status' | grep -q "compliant" || exit 1
```

### Pattern 2: Scheduled Audit

Run weekly documentation audit:

```yaml
name: Weekly Documentation Audit
on:
  schedule:
    - cron: '0 0 * * 0'  # Every Sunday

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - name: Audit Documentation
        run: |
          curl -X POST https://your-a2a-server/a2a/execute \
            -H "Content-Type: application/json" \
            -d '{
              "skill_id": "check_documentation_standards",
              "input": {
                "repository": "${{ github.repository }}",
                "check_all_docs": true
              }
            }' > audit-results.json

      - name: Post Results to Slack
        if: always()
        run: |
          # Send audit-results.json to Slack webhook
```

### Pattern 3: Agent-to-Agent Integration

Use from other A2A agents:

```python
import requests

def check_docs_before_deploy(repository: str) -> bool:
    """Check docs compliance before deploying"""
    response = requests.post(
        "https://pattern-discovery-agent/a2a/execute",
        json={
            "skill_id": "check_documentation_standards",
            "input": {
                "repository": repository,
                "check_all_docs": False  # Priority files only
            }
        }
    )

    result = response.json()

    if not result["success"]:
        print(f"Documentation check failed: {result['error']}")
        return False

    if result["status"] in ["non_compliant", "needs_improvement"]:
        print(f"Documentation issues found: {result['recommendations']}")
        return False

    return True
```

## Understanding Violations

### Violation Severity Levels

**Critical** (🔴):
- Missing critical-priority files (README.md, CLAUDE.md)
- Core architecture changes without documentation updates

**High** (⚠️):
- Missing high-priority files or required sections
- Code changes without any documentation updates
- Broken internal links in critical files

**Medium** (📝):
- Missing update stamps or version indicators
- Missing recommended sections
- Invalid file path references
- Code examples without language specifiers

**Low**:
- Inconsistent terminology
- Code formatting issues

### Common Violation Types

| Type | Description | Severity | Fix |
|------|-------------|----------|-----|
| `missing_file` | Required documentation file missing | Critical/High | Create the file |
| `missing_section` | Required section not found | High/Medium | Add section |
| `missing_update_stamp` | No version/date indicator | Medium | Add "Last Updated: YYYY-MM-DD" |
| `invalid_file_path` | Referenced path doesn't exist | Medium | Update path or create file |
| `broken_internal_link` | Markdown link points to missing file | Medium | Fix link target |
| `code_example_no_language` | Code block without language | Low | Add \`\`\`python, etc. |
| `inconsistent_terminology` | Uses deprecated terms | Low | Update to standard terms |

## Best Practices

### 1. Check Before Merge

Always run standards check before merging:
```bash
# Quick check of priority files
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{"skill_id": "check_documentation_standards", "input": {"repository": "owner/repo"}}' | jq '.status'
```

### 2. Update Docs with Code

When modifying code:
1. Make code changes
2. Update relevant documentation
3. Add update stamps
4. Run validation:
```bash
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{"skill_id": "validate_documentation_update", "input": {"repository": "owner/repo", "days": 1}}' | jq
```

### 3. Regular Audits

Schedule periodic comprehensive checks:
```bash
# Monthly comprehensive audit
curl -X POST http://localhost:8080/a2a/execute \
  -H "Content-Type: application/json" \
  -d '{"skill_id": "check_documentation_standards", "input": {"repository": "owner/repo", "check_all_docs": true}}' \
  | jq '.summary'
```

### 4. Fix Critical First

Prioritize fixes by severity:
1. Critical violations (missing critical files)
2. High violations (missing sections, core changes)
3. Medium violations (update stamps, paths)
4. Low violations (formatting, terminology)

## Troubleshooting

### Issue: "GITHUB_TOKEN not configured"

**Solution**: Set GITHUB_TOKEN environment variable:
```bash
export GITHUB_TOKEN="ghp_xxxxx"
```

### Issue: "Failed to access repository"

**Possible Causes**:
1. Repository doesn't exist
2. Repository is private and token lacks access
3. Invalid repository format

**Solution**: Verify repository exists and token has access:
```bash
curl -H "Authorization: token ghp_xxxxx" https://api.github.com/repos/owner/repo
```

### Issue: False positives for file paths

**Explanation**: The checker samples file paths to avoid API rate limits. Some paths may be templates or examples.

**Solution**: This is expected behavior. Review violations manually and ignore false positives.

### Issue: "All document reviews failed"

**Cause**: Cannot access any documentation files in repository

**Solution**: Check:
1. Repository has .md files
2. Token has read access
3. Specify `doc_paths` explicitly if using non-standard names

## Technical Details

### Implementation

**Core Service**: `core/documentation_standards_checker.py`
- Checks 6 standards: completeness, accuracy, consistency, up-to-date, code examples, links
- Validates against `docs/DOCUMENTATION_STANDARDS.md`
- Returns structured violations with severity levels

**Skill Module**: `a2a/skills/documentation_standards.py`
- Two skills: check standards, validate updates
- Modular architecture (BaseSkill interface)
- Self-contained and independently testable

### Checked Standards

Based on `docs/DOCUMENTATION_STANDARDS.md`:

1. **Consistency**: Terminology, code examples, file paths, commands
2. **Completeness**: Overview, prerequisites, steps, examples, testing, troubleshooting
3. **Accuracy**: Code examples work, file paths correct, commands execute, versions current
4. **Clarity**: Simple language, defined jargon, clear steps, visual aids
5. **Up-to-date**: Version indicators, deprecation notices, migration guides, update stamps

### Priority Hierarchy

From `DOCUMENTATION_STANDARDS.md`:

**Priority 1 (Critical)**: README.md, CLAUDE.md, QUICK_START.md
**Priority 2 (High)**: EXTENDING_DEV_NEXUS.md, API.md, examples/
**Priority 3 (Medium)**: ARCHITECTURE.md, LESSONS_LEARNED.md, TROUBLESHOOTING.md
**Priority 4 (Low)**: CONTRIBUTING.md, CHANGELOG.md, FAQ.md

## See Also

- [DOCUMENTATION_STANDARDS.md](../docs/DOCUMENTATION_STANDARDS.md) - Complete standards definition
- [QUICK_START_EXTENDING.md](../docs/QUICK_START_EXTENDING.md) - How to add new skills
- [EXTENDING_DEV_NEXUS.md](../docs/EXTENDING_DEV_NEXUS.md) - Comprehensive extension guide

---

**Last Updated**: 2025-01-10
**Version**: 1.0
**Skills**: `check_documentation_standards`, `validate_documentation_update`
