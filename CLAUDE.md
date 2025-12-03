# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Pattern Discovery Agent System - an automated architectural consistency and pattern discovery tool that analyzes code commits across GitHub repositories using Claude AI. The system acts as institutional memory, detecting similar patterns, architectural drift, and opportunities for code reuse across multiple projects.

**Key Features**:
1. **Pattern Discovery**: Detects similar patterns across repositories
2. **Knowledge Base Management**: Maintains centralized architectural memory
3. **Reusable Workflows**: Monitored projects only need a tiny 15-line workflow file
4. **Extensible**: Can notify external orchestration services (e.g., [dependency-orchestrator](https://github.com/patelmm79/dependency-orchestrator))

## Core Architecture

### Three-Tier System

1. **GitHub Actions Workflow** (`.github/workflows/main.yml`)
   - Triggers on push/PR to main/master/develop branches
   - Runs pattern analysis via Python script
   - Uploads analysis artifacts with 90-day retention

2. **Pattern Analyzer** (`scripts/pattern_analyzer.py`)
   - Core analysis engine using Anthropic Claude API
   - Extracts semantic patterns from git diffs using LLM
   - Manages knowledge base stored in separate GitHub repository
   - Compares patterns across repositories
   - Sends notifications via Discord/Slack webhooks
   - Can notify external orchestrator services (optional)

3. **Pre-commit Checker** (`scripts/precommit_checker.py`)
   - Optional local validation before commits
   - Fetches knowledge base from remote URL
   - Warns developers about pattern divergence interactively

### Data Flow

```
Monitored Project (Push) → Calls Reusable Workflow → Pattern Analyzer → Claude API
                                                            ↓
                                                     Extract Patterns
                                                            ↓
                                                  Knowledge Base Repo (JSON)
                                                            ↓
                                                  Find Similar Patterns
                                                            ↓
                                                  Webhook Notification
                                                            ↓
                                               (Optional) External Orchestrator
```

### Reusable Workflow Architecture

The workflow in `.github/workflows/main.yml` is configured with `workflow_call` trigger, allowing other repositories to call it without copying code:

1. **Monitored Project**: Contains only a small workflow file that calls this repository's workflow
2. **This Repository**: Contains all the logic, scripts, and dependencies
3. **Execution**: GitHub Actions checks out both repos and runs the analyzer on the monitored code

### Knowledge Base Structure

Stored as `knowledge_base.json` in a separate repository:
- Repository entries with pattern history
- Pattern metadata: patterns, decisions, reusable components, dependencies, problem domain, keywords
- Timestamp and commit SHA tracking

## Development Commands

### Setup for Local Development

```bash
# Install dependencies
pip install anthropic requests pygithub gitpython

# Activate virtual environment (if using venv)
venv\Scripts\activate  # Windows
source venv/bin/activate  # Unix
```

### Running Pattern Analysis Locally

```bash
# Requires environment variables:
# - ANTHROPIC_API_KEY (required)
# - GITHUB_TOKEN (required)
# - WEBHOOK_URL (optional, for Discord/Slack)
# - KNOWLEDGE_BASE_REPO (optional, format: "username/repo")

python scripts/pattern_analyzer.py
```

### Setting Up Monitoring for Other Projects

See `SETUP_MONITORING.md` for complete instructions. Quick version:

1. Add secrets to the target project (ANTHROPIC_API_KEY, etc.)
2. Create `.github/workflows/pattern-monitoring.yml` in the target project:
```yaml
name: Pattern Monitoring
on:
  push:
    branches: [main, master, develop]
jobs:
  analyze-patterns:
    uses: patelmm79/architecture-kb/.github/workflows/main.yml@main
    secrets:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
      KNOWLEDGE_BASE_REPO: ${{ secrets.KNOWLEDGE_BASE_REPO }}
```
3. Commit and push - monitoring is now active!

### Pre-commit Hook Setup

```bash
# Set environment variables
export ANTHROPIC_API_KEY="your-key"
export KNOWLEDGE_BASE_URL="https://raw.githubusercontent.com/username/architecture-kb/main/knowledge_base.json"

# Install hook (Unix)
chmod +x scripts/precommit_checker.py
cp scripts/precommit_checker.py .git/hooks/pre-commit
```

### Dashboard Usage

Open `pattern_dashboard.html` in a browser and load `knowledge_base.json` to visualize:
- Repository statistics
- Pattern similarity network graph
- Cross-repository relationships
- Redundancy metrics

## Key Implementation Details

### Pattern Extraction Logic

The `extract_patterns_with_llm()` method in `pattern_analyzer.py`:
- Limits to 10 files per analysis to avoid token overflow
- Truncates large diffs to 2000 characters
- Uses Claude Sonnet 4 (`claude-sonnet-4-20250514`)
- Extracts: patterns, technical decisions, reusable components, dependencies, problem domain, keywords
- Returns structured JSON with analyzed_at timestamp and commit SHA

### Similarity Detection

The `find_similar_patterns()` method uses simple set-based scoring:
- Keyword overlap: intersection of keyword sets
- Pattern overlap: intersection of pattern name lists
- Returns top 5 most similar repositories sorted by combined overlap score
- Excludes self-comparison

### File Filtering

Ignores noise files via `_is_meaningful_file()`:
- Lock files (`.lock`, `package-lock.json`, `yarn.lock`)
- Minified/map files (`.min.js`, `.map`)
- Python bytecode (`__pycache__`, `.pyc`)
- VCS/system files (`.git/`, `.DS_Store`)
- `node_modules/`

## Configuration

### GitHub Secrets Required

Each monitored repository needs:
- `ANTHROPIC_API_KEY` - From console.anthropic.com (required)
- `DISCORD_WEBHOOK_URL` - For notifications (optional)
- `KNOWLEDGE_BASE_REPO` - Format: "username/architecture-kb" (optional)
- `GITHUB_TOKEN` - Automatically provided by GitHub Actions

### Adjusting Sensitivity

In `pattern_analyzer.py:228`, modify `find_similar_patterns()`:
```python
# Current: Alert on any overlap
if keyword_overlap > 0 or pattern_overlap > 0:

# More selective: Require 2+ overlaps
if keyword_overlap > 1 or pattern_overlap > 1:
```

### Adding File Filters

Edit `pattern_analyzer.py:72` in `_is_meaningful_file()`:
```python
ignore_patterns = [
    r'\.lock$',
    r'test_.*\.py$',  # Ignore test files
    r'.*_generated\..*',  # Ignore generated code
]
```

## Important Patterns

### Knowledge Base Updates

The analyzer always tries to update the knowledge base after extracting patterns. It:
1. Loads existing KB from GitHub repo
2. Appends new entry to repository history
3. Updates latest patterns for the repository
4. Commits changes back to KB repo using PyGithub
5. Handles both file creation (first run) and updates (subsequent runs)

### Error Handling Philosophy

The system is designed to be non-blocking:
- Pattern extraction errors return empty/default structures with error field
- Missing knowledge base returns empty repositories dict
- Failed notifications print to console instead of raising
- Pre-commit hook exits with code 0 if API key missing (doesn't block commit)

### Notification Format

Discord/Slack notifications use embeds structure:
- Main message with repository name and pattern count
- Embed per similar repository (top 3 shown)
- Fields showing matching patterns (max 5 displayed)
- Includes overlap counts for quick assessment

## Python Environment

- Developed for Python 3.11+
- Uses PyCharm project structure (venv in project directory)
- Windows-compatible path handling
- Virtual environment in `venv/` directory (excluded from git)

## Notes

- The workflow file location differs slightly: actual path is `.github/workflows/main.yml` but pattern_analyzer.py is in `scripts/` not `.github/scripts/`
- Dashboard is client-side only (pure HTML/JavaScript, no backend)
- Knowledge base JSON can grow large over time - consider pruning old history entries
- LLM responses are parsed with markdown code block removal before JSON parsing
