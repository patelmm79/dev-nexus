# Quick Start Guide

> Get Dev-Nexus pattern monitoring running in under 10 minutes

**Last Updated**: 2025-01-10

---

## Overview

This guide will walk you through setting up automated pattern discovery for your GitHub repositories. By the end, every commit will be analyzed for architectural patterns and checked for consistency across your projects.

## Prerequisites

Before you begin, you'll need:

- **GitHub account** with at least one repository
- **Anthropic API key** (get one at [console.anthropic.com](https://console.anthropic.com))
- **10 minutes** of your time

**Optional but recommended:**
- Discord or Slack webhook URL for notifications
- Basic understanding of GitHub Actions

---

## Step 1: Create Your Knowledge Base Repository

This repository will store all discovered patterns across your projects.

```bash
# Create a new private repository
gh repo create dev-nexus --private

# Initialize it
cd dev-nexus
echo "# Architecture Knowledge Base" > README.md
git add . && git commit -m "Initialize knowledge base" && git push
```

**Don't have GitHub CLI?** Create the repo through GitHub's web interface instead.

---

## Step 2: Get Your API Keys

### Anthropic API Key (Required)

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Navigate to **API Keys**
4. Click **Create Key**
5. Copy the key (starts with `sk-ant-`)

### Discord Webhook (Optional)

1. Open your Discord server
2. Go to **Server Settings** → **Integrations** → **Webhooks**
3. Click **New Webhook**
4. Copy the webhook URL

---

## Step 3: Configure Repository Secrets

For **each repository** you want to monitor:

1. Go to repository **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add the following:

| Secret Name | Value | Required? |
|------------|-------|-----------|
| `ANTHROPIC_API_KEY` | Your API key from Step 2 | ✅ Required |
| `KNOWLEDGE_BASE_REPO` | Format: `username/dev-nexus` | ✅ Required |
| `DISCORD_WEBHOOK_URL` | Your webhook URL | ⚠️ Optional |

**Example:**
- Secret name: `ANTHROPIC_API_KEY`
- Secret value: `sk-ant-api03-xxxxxxxxxxx`

---

## Step 4: Add Pattern Monitoring Workflow

In your project repository, create a workflow file:

```bash
# Navigate to your project
cd my-project

# Create workflow directory
mkdir -p .github/workflows

# Create the workflow file
cat > .github/workflows/pattern-monitoring.yml << 'EOF'
name: Pattern Monitoring

on:
  push:
    branches: [main, master, develop]
  pull_request:
    types: [opened, synchronize]

jobs:
  analyze-patterns:
    uses: patelmm79/dev-nexus/.github/workflows/analyze-reusable.yml@main
    secrets:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
      KNOWLEDGE_BASE_REPO: ${{ secrets.KNOWLEDGE_BASE_REPO }}
EOF

# Commit and push
git add .github/workflows/pattern-monitoring.yml
git commit -m "Add pattern monitoring"
git push
```

**That's it!** No other files needed. The workflow automatically pulls the analyzer from the dev-nexus repository.

---

## Step 5: Test It Out

Make a test commit to trigger pattern analysis:

```bash
# Make any change
echo "# Test" >> README.md

# Commit and push
git add README.md
git commit -m "Test pattern monitoring"
git push
```

### What Happens Next

1. **GitHub Actions triggers** the workflow
2. **Pattern analyzer** examines your changes using Claude AI
3. **Patterns are extracted** and stored in your knowledge base
4. **Similarity check** runs against other monitored repos
5. **Notification sent** (if webhook configured) when patterns match

### Check the Results

1. Go to **Actions** tab in your repository
2. Click on the latest workflow run
3. View the **pattern-analysis** job
4. Download artifacts to see detailed analysis

---

## Step 6: View Your Patterns (Optional)

### Option A: View Knowledge Base Directly

1. Go to your `dev-nexus` repository
2. Open `knowledge_base.json`
3. See all extracted patterns in JSON format

### Option B: Use the Dashboard

1. Download `pattern_dashboard.html` from the dev-nexus repo
2. Download `knowledge_base.json` from your KB repo
3. Open the HTML file in your browser
4. Load the JSON file
5. Explore the interactive visualization

---

## Examples

### Example 1: Single Repository

```bash
# Day 1: First commit
git commit -m "Add retry logic with exponential backoff"
git push
```

**Result:** Pattern recorded in knowledge base

### Example 2: Pattern Detection

```bash
# Day 7: Similar pattern in another repo
cd another-project
git commit -m "Add API client with retry logic"
git push
```

**Result:** Discord notification: "Found similar pattern in **first-repo**: 'Retry logic with exponential backoff'"

### Example 3: Multiple Repositories

After monitoring 3+ repos, open the dashboard to see:
- Pattern similarity network graph
- Which repos share patterns
- Opportunities for code reuse
- Architectural consistency metrics

---

## Testing

### Verify Workflow is Active

```bash
# Check GitHub Actions
gh workflow list

# Should show: Pattern Monitoring
```

### Test Notification

```bash
# Test Discord webhook
curl -X POST $DISCORD_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"content": "Test notification from dev-nexus"}'
```

### Manual Analysis

```bash
# Run analyzer locally (optional)
git clone https://github.com/patelmm79/dev-nexus
cd dev-nexus
pip install -r requirements.txt

export ANTHROPIC_API_KEY="your-key"
export GITHUB_TOKEN="your-token"
export KNOWLEDGE_BASE_REPO="username/dev-nexus"

python scripts/pattern_analyzer.py
```

---

## Next Steps

### Add More Repositories

Repeat Steps 3-4 for each repository you want to monitor.

### Deploy A2A Server (Optional)

Enable agent-to-agent communication for programmatic access.

**Option 1: Bash Scripts (Quick)**
```bash
# Simple deployment with bash scripts
export GCP_PROJECT_ID="your-project-id"
bash scripts/setup-secrets.sh
bash scripts/deploy.sh

# See full guide
cat DEPLOYMENT.md
```

**Option 2: Terraform (Production)**
```bash
# Infrastructure as code approach
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply

# See full guide
cat terraform/README.md
```

**Choose Terraform if you:**
- Need production-grade infrastructure
- Want infrastructure as code (version control, rollback)
- Are deploying PostgreSQL infrastructure
- Work in a team that needs state management

### Enable Pre-commit Hooks (Optional)

Check patterns before committing:

```bash
# Copy pre-commit script
cp scripts/precommit_checker.py .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Set environment
export ANTHROPIC_API_KEY="your-key"
export KNOWLEDGE_BASE_URL="https://raw.githubusercontent.com/username/dev-nexus/main/knowledge_base.json"
```

### Integrate with Dependency Orchestrator (Optional)

For automated dependency coordination:

See: [dependency-orchestrator](https://github.com/patelmm79/dependency-orchestrator)

---

## Troubleshooting

### Workflow Fails

**Problem**: Action fails with "Secret not found"
**Solution**: Check that secrets are added to the correct repository (not the dev-nexus repo)

**Problem**: "Permission denied" when updating knowledge base
**Solution**: Ensure `GITHUB_TOKEN` has `repo` scope and KB repo exists

### No Notifications

**Problem**: Analysis completes but no Discord message
**Solution**:
- Verify webhook URL is correct
- Test webhook manually: `curl -X POST $DISCORD_WEBHOOK_URL -d '{"content":"test"}'`
- Check Discord channel permissions

### No Patterns Detected

**Problem**: Knowledge base is empty after commits
**Solution**:
- Check Actions logs for errors
- Verify ANTHROPIC_API_KEY is valid
- Ensure commits contain meaningful code changes (not just markdown)

### Pattern Analysis Incomplete

**Problem**: Only some files analyzed
**Solution**: Analyzer limits to 10 files per commit. This is expected behavior to avoid token overflow.

---

## Common Questions

**Q: Does this work with private repositories?**
A: Yes! All pattern data stays in your private knowledge base repo.

**Q: How much does this cost?**
A: ~$0.01-0.05 per commit analyzed. For 50 commits/month, expect $0.50-2.50 in API costs.

**Q: Can I use this with GitLab/Bitbucket?**
A: The GitHub Actions version is GitHub-only, but you can run the analyzer in any CI/CD system.

**Q: Will this slow down my CI/CD?**
A: No, pattern analysis runs in parallel with your other jobs.

**Q: Can I customize what patterns are detected?**
A: Yes! Edit `scripts/pattern_analyzer.py` to adjust the Claude prompts and detection logic.

---

## Getting Help

- **Documentation**: See [README.md](README.md) for complete documentation
- **Setup Details**: See [SETUP_MONITORING.md](SETUP_MONITORING.md)
- **A2A Server**: See [A2A_QUICKSTART.md](A2A_QUICKSTART.md)
- **Issues**: Report bugs at [GitHub Issues](https://github.com/patelmm79/dev-nexus/issues)
- **Architecture**: See [CLAUDE.md](CLAUDE.md) for system internals

---

## Success Checklist

After completing this guide, you should have:

- ✅ Knowledge base repository created
- ✅ API keys obtained and configured
- ✅ Secrets added to monitored repository
- ✅ Workflow file created and committed
- ✅ Test commit made successfully
- ✅ Pattern analysis visible in Actions tab
- ✅ Knowledge base JSON file exists in dev-nexus repo

**If you have all of these, you're done! 🎉**

---

**Remember**: Start with one repository, verify it works, then add more. The system gets more valuable as you monitor more repos and build up your pattern knowledge base.

**Questions or issues?** Open an issue on GitHub or check the troubleshooting guides.
