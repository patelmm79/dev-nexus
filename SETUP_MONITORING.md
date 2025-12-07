# Setup Pattern Monitoring for Your Projects

This guide explains how to enable pattern monitoring on your projects without copying any files.

## Quick Setup (2 minutes per project)

### 1. Add GitHub Secrets to Your Project

Go to your project's repository on GitHub:
- Navigate to: **Settings** → **Secrets and variables** → **Actions**
- Click **New repository secret** and add:

| Secret Name | Required? | Description | Example |
|-------------|-----------|-------------|---------|
| `ANTHROPIC_API_KEY` | ✅ Required | Get from [console.anthropic.com](https://console.anthropic.com) | `sk-ant-api03-...` |
| `DISCORD_WEBHOOK_URL` | Optional | Discord/Slack webhook for notifications | `https://discord.com/api/webhooks/...` |
| `KNOWLEDGE_BASE_REPO` | Optional | Your KB repo (defaults to this one) | `patelmm79/dev-nexus` |

### 2. Create Workflow File in Your Project

Create this single file in your project:

**`.github/workflows/pattern-monitoring.yml`**

```yaml
name: Pattern Monitoring

on:
  push:
    branches: [main, master, develop]
  pull_request:
    types: [opened, synchronize]

jobs:
  analyze-patterns:
    uses: patelmm79/dev-nexus/.github/workflows/main.yml@main
    secrets:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
      KNOWLEDGE_BASE_REPO: ${{ secrets.KNOWLEDGE_BASE_REPO }}
```

### 3. Commit and Push

```bash
git add .github/workflows/pattern-monitoring.yml
git commit -m "Enable pattern monitoring"
git push
```

That's it! The workflow will now run automatically on every push.

## How It Works

1. **Your project** has only the tiny workflow file above (~15 lines)
2. **This repository** (dev-nexus) contains:
   - The reusable workflow (`.github/workflows/main.yml`)
   - The pattern analyzer script (`scripts/pattern_analyzer.py`)
   - All the logic and dependencies

3. When you push to your project:
   - GitHub Actions calls the reusable workflow from dev-nexus
   - The workflow checks out your code
   - Downloads the pattern analyzer script
   - Runs the analysis using your secrets
   - Updates the knowledge base
   - Sends notifications if patterns match

## Customization Options

### Monitor Different Branches

```yaml
on:
  push:
    branches: [main, develop, staging]  # Add more branches
```

### Run on Schedule Instead of Every Push

```yaml
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
  workflow_dispatch:  # Allow manual triggering
```

### Run Only on Specific File Changes

```yaml
on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'lib/**'
      - '!**/*.md'  # Ignore markdown changes
```

## Verification

After setup, verify it's working:

1. **Check Actions Tab**: Go to your project → Actions tab → You should see "Pattern Monitoring" workflow
2. **Make a Test Commit**: Push a change and watch the workflow run
3. **View Results**:
   - Check the workflow logs for analysis results
   - Download the `pattern-analysis` artifact
   - Check for Discord/Slack notification (if configured)

## Troubleshooting

### Workflow doesn't appear
- Make sure the file is in `.github/workflows/` (with a dot)
- File must have `.yml` or `.yaml` extension
- Check the file is committed and pushed to GitHub

### Workflow fails with "Secret not found"
- Verify `ANTHROPIC_API_KEY` is set in repository secrets
- Check the secret name matches exactly (case-sensitive)
- Ensure you set it in the **project being monitored**, not in dev-nexus

### "Permission denied" errors
- The `GITHUB_TOKEN` is provided automatically
- If updating knowledge base fails, check that `KNOWLEDGE_BASE_REPO` secret is set correctly
- You may need to use a Personal Access Token with `repo` scope

### Pattern analysis finds nothing
- Workflow only analyzes meaningful file changes (see CLAUDE.md for filters)
- Lock files, minified files, and generated code are ignored by design
- Check workflow logs to see which files were analyzed

## Multiple Projects Setup

You can set up monitoring across all your projects:

```bash
# Script to add monitoring to multiple repos
repos=("myorg/project1" "myorg/project2" "myorg/project3")

for repo in "${repos[@]}"; do
  echo "Setting up monitoring for $repo"
  gh repo clone $repo temp-repo
  cd temp-repo
  mkdir -p .github/workflows

  # Copy the workflow template
  cat > .github/workflows/pattern-monitoring.yml << 'EOF'
name: Pattern Monitoring

on:
  push:
    branches: [main, master, develop]

jobs:
  analyze-patterns:
    uses: patelmm79/dev-nexus/.github/workflows/main.yml@main
    secrets:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
      KNOWLEDGE_BASE_REPO: ${{ secrets.KNOWLEDGE_BASE_REPO }}
EOF

  git add .github/workflows/pattern-monitoring.yml
  git commit -m "Enable pattern monitoring"
  git push
  cd ..
  rm -rf temp-repo
done
```

## Updating the System

When the pattern analyzer is updated in dev-nexus:
- **No action needed!** Your projects automatically use the latest version
- The workflow references `@main` which always pulls the latest code
- For stability, you can pin to a specific commit: `@7510cc4` instead of `@main`

## Disabling Monitoring

To disable monitoring for a project:
1. Delete `.github/workflows/pattern-monitoring.yml` from the project
2. Commit and push

The knowledge base will retain historical data, but new commits won't be analyzed.
