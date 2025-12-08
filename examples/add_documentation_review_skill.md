# Adding the Documentation Review Skill

This guide shows exactly how to integrate the documentation review skill into dev-nexus.

## Prerequisites

The `core/documentation_service.py` file has already been created. Now you just need to integrate it into the A2A server.

## Step 1: Update AgentCard in server.py

Add this skill definition to the `skills` array in `a2a/server.py` (around line 321, before the closing bracket):

```python
,  # Don't forget the comma before adding this!
{
    "id": "review_documentation",
    "name": "Review Documentation",
    "description": "Analyze documentation for quality, consistency, and adherence to standards. Checks completeness, clarity, examples, structure, accuracy, and formatting.",
    "tags": ["documentation", "quality", "standards", "review"],
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
                "description": "Specific documentation files to review. If empty, reviews common docs (README.md, CLAUDE.md, etc.)",
                "default": []
            },
            "standards": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["completeness", "clarity", "examples", "structure", "accuracy", "formatting"]
                },
                "description": "Standards to check against",
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
            "description": "Review main documentation files for dev-nexus"
        },
        {
            "input": {
                "repository": "patelmm79/my-project",
                "standards": ["completeness", "clarity", "examples", "structure", "accuracy", "formatting"]
            },
            "description": "Comprehensive review of all documentation with all standards"
        }
    ]
}
```

## Step 2: Add Executor Handler

Add this method to the `PatternDiscoveryExecutor` class in `a2a/executor.py`:

```python
async def _handle_review_documentation(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Review documentation for quality and standards compliance

    Input:
        - repository: str - Repository name (format: "owner/repo")
        - doc_paths: List[str] - Documentation files to review (optional)
        - standards: List[str] - Standards to check (optional)

    Output:
        - reviews: List of review results for each document
        - overall_assessment: Summary of documentation quality
    """
    try:
        import os
        import anthropic
        from github import Github
        from core.documentation_service import DocumentationReviewer

        repository = input_data.get('repository')
        doc_paths = input_data.get('doc_paths', [])
        standards = input_data.get('standards', ['completeness', 'clarity', 'examples', 'structure'])

        if not repository:
            return {
                "success": False,
                "error": "Missing required parameter: 'repository'"
            }

        # Validate standards
        valid_standards = ["completeness", "clarity", "examples", "structure", "accuracy", "formatting"]
        invalid_standards = [s for s in standards if s not in valid_standards]
        if invalid_standards:
            return {
                "success": False,
                "error": f"Invalid standards: {', '.join(invalid_standards)}. Valid options: {', '.join(valid_standards)}"
            }

        # Initialize reviewer
        anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not anthropic_api_key:
            return {
                "success": False,
                "error": "ANTHROPIC_API_KEY not configured"
            }

        reviewer = DocumentationReviewer(
            anthropic_client=anthropic.Anthropic(api_key=anthropic_api_key),
            kb_manager=self.kb_manager
        )

        # Get GitHub client
        github_token = os.environ.get('GITHUB_TOKEN')
        if not github_token:
            return {
                "success": False,
                "error": "GITHUB_TOKEN not configured"
            }

        github_client = Github(github_token)

        # Get repository
        try:
            repo = github_client.get_repo(repository)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to access repository '{repository}': {str(e)}"
            }

        # If no paths specified, review common docs
        if not doc_paths:
            doc_paths = []
            common_files = ['README.md', 'CLAUDE.md', 'CONTRIBUTING.md', 'docs/README.md', 'docs/API.md']

            for filename in common_files:
                try:
                    repo.get_contents(filename)
                    doc_paths.append(filename)
                except:
                    pass  # File doesn't exist

            if not doc_paths:
                return {
                    "success": False,
                    "error": "No documentation files found. Specify doc_paths explicitly."
                }

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
                    "error": f"Failed to review: {str(e)}",
                    "overall_score": 0.0
                })

        # Calculate overall assessment
        successful_reviews = [r for r in reviews if 'overall_score' in r and 'error' not in r]

        if not successful_reviews:
            return {
                "success": False,
                "error": "All document reviews failed",
                "reviews": reviews
            }

        total_score = sum(r['overall_score'] for r in successful_reviews)
        avg_score = total_score / len(successful_reviews)

        # Determine rating
        if avg_score >= 0.8:
            rating = "Excellent"
            rating_emoji = "✅"
        elif avg_score >= 0.6:
            rating = "Good"
            rating_emoji = "👍"
        elif avg_score >= 0.4:
            rating = "Fair"
            rating_emoji = "⚠️"
        else:
            rating = "Needs Improvement"
            rating_emoji = "❌"

        # Collect all recommendations
        all_recommendations = []
        for review in successful_reviews:
            if 'recommendations' in review:
                all_recommendations.extend(review['recommendations'])

        return {
            "success": True,
            "repository": repository,
            "reviews": reviews,
            "overall_assessment": {
                "average_score": round(avg_score, 2),
                "rating": rating,
                "rating_emoji": rating_emoji,
                "documents_reviewed": len(successful_reviews),
                "documents_failed": len(reviews) - len(successful_reviews),
                "standards_checked": standards
            },
            "top_recommendations": all_recommendations[:10]  # Top 10 across all docs
        }

    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"Failed to review documentation: {str(e)}",
            "traceback": traceback.format_exc()
        }
```

## Step 3: Update Routing in Executor

In the `execute()` method of `PatternDiscoveryExecutor` (around line 62), add the routing case:

```python
elif skill_id == "health_check_external":
    return await self._handle_health_check_external(input_data)
elif skill_id == "review_documentation":  # Add this
    return await self._handle_review_documentation(input_data)  # Add this
else:
    return {
        "error": f"Unknown skill: {skill_id}",
        "available_skills": [
            "query_patterns", "get_deployment_info", "add_lesson_learned",
            "get_repository_list", "get_cross_repo_patterns",
            "update_dependency_info", "health_check_external",
            "review_documentation"  # Add to list
        ]
    }
```

## Step 4: Test Locally

```bash
# Start the server
python a2a/server.py

# Verify the skill is in the AgentCard
curl http://localhost:8080/.well-known/agent.json | jq '.skills[] | select(.id == "review_documentation")'

# Test with dev-nexus itself
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

## Step 5: Example Usage from Python

```python
from a2a.client import A2AClient

# Create client
client = A2AClient("http://localhost:8080")

# Review documentation
result = client.execute_skill(
    skill_id="review_documentation",
    input_data={
        "repository": "patelmm79/dev-nexus",
        "standards": ["completeness", "clarity", "examples", "structure", "accuracy", "formatting"]
    }
)

# Print results
if result.get("success"):
    assessment = result["overall_assessment"]
    print(f"Overall Rating: {assessment['rating']} ({assessment['average_score']}/1.0)")
    print(f"Documents Reviewed: {assessment['documents_reviewed']}")

    print("\nTop Recommendations:")
    for i, rec in enumerate(result.get("top_recommendations", [])[:5], 1):
        print(f"{i}. {rec}")

    print("\nDetailed Reviews:")
    for review in result["reviews"]:
        print(f"\n{review['doc_path']}:")
        print(f"  Score: {review.get('overall_score', 0):.2f}")
        if 'checks' in review:
            for standard, check_result in review['checks'].items():
                print(f"  - {standard}: {check_result['score']:.2f} - {check_result['message']}")
else:
    print(f"Error: {result.get('error')}")
```

## Example Output

```json
{
  "success": true,
  "repository": "patelmm79/dev-nexus",
  "reviews": [
    {
      "repository": "patelmm79/dev-nexus",
      "doc_path": "CLAUDE.md",
      "reviewed_at": "2025-01-10T15:30:00",
      "standards_checked": ["completeness", "clarity", "examples", "structure"],
      "checks": {
        "completeness": {
          "score": 1.0,
          "found_sections": ["overview", "commands", "examples"],
          "missing_sections": [],
          "message": "Found 3/3 required sections"
        },
        "clarity": {
          "score": 0.85,
          "issues": ["Found 3 sentences over 40 words"],
          "message": "Clarity score: 0.85 - 1 issues found"
        },
        "examples": {
          "score": 0.95,
          "code_blocks_count": 12,
          "has_examples_section": true,
          "example_types": {
            "bash": 5,
            "python": 4,
            "json": 2,
            "inline": 45
          },
          "message": "Found 12 code blocks with 3 different types"
        },
        "structure": {
          "score": 1.0,
          "headings_count": 25,
          "issues": [],
          "warnings": [],
          "message": "Structure score: 1.00"
        }
      },
      "overall_score": 0.95,
      "recommendations": [
        "[Clarity] Break down the longer sentences in the 'Pattern Extraction Logic' section into shorter, more digestible statements",
        "[Examples] Add a troubleshooting section with examples of common issues and solutions",
        "[Structure] Consider adding a quick reference card or cheat sheet section for common commands"
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
    "average_score": 0.95,
    "rating": "Excellent",
    "rating_emoji": "✅",
    "documents_reviewed": 1,
    "documents_failed": 0,
    "standards_checked": ["completeness", "clarity", "examples", "structure"]
  },
  "top_recommendations": [
    "[Clarity] Break down the longer sentences in the 'Pattern Extraction Logic' section",
    "[Examples] Add a troubleshooting section with examples of common issues",
    "[Structure] Consider adding a quick reference card or cheat sheet section"
  ]
}
```

## Advanced: Create a Standalone Script

Create `scripts/review_docs.py`:

```python
#!/usr/bin/env python3
"""
Standalone script to review documentation

Usage:
    python scripts/review_docs.py patelmm79/dev-nexus
    python scripts/review_docs.py patelmm79/dev-nexus --files README.md CLAUDE.md
    python scripts/review_docs.py patelmm79/dev-nexus --all-standards
"""

import os
import sys
import argparse
import anthropic
from github import Github

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.documentation_service import DocumentationReviewer
from core.knowledge_base import KnowledgeBaseManager


def main():
    parser = argparse.ArgumentParser(description='Review repository documentation')
    parser.add_argument('repository', help='Repository in format owner/repo')
    parser.add_argument('--files', nargs='+', help='Specific files to review')
    parser.add_argument('--all-standards', action='store_true', help='Check all standards')
    parser.add_argument('--standards', nargs='+', choices=['completeness', 'clarity', 'examples', 'structure', 'accuracy', 'formatting'],
                        help='Specific standards to check')
    args = parser.parse_args()

    # Get credentials
    anthropic_api_key = os.environ.get('ANTHROPIC_API_KEY')
    github_token = os.environ.get('GITHUB_TOKEN')
    kb_repo = os.environ.get('KNOWLEDGE_BASE_REPO', 'patelmm79/dev-nexus')

    if not anthropic_api_key or not github_token:
        print("Error: Set ANTHROPIC_API_KEY and GITHUB_TOKEN environment variables")
        sys.exit(1)

    # Initialize services
    anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
    github_client = Github(github_token)
    kb_manager = KnowledgeBaseManager(github_client, kb_repo)
    reviewer = DocumentationReviewer(anthropic_client, kb_manager)

    # Determine standards
    if args.all_standards:
        standards = ['completeness', 'clarity', 'examples', 'structure', 'accuracy', 'formatting']
    elif args.standards:
        standards = args.standards
    else:
        standards = ['completeness', 'clarity', 'examples', 'structure']

    # Determine files
    repo = github_client.get_repo(args.repository)
    if args.files:
        doc_paths = args.files
    else:
        doc_paths = []
        for filename in ['README.md', 'CLAUDE.md', 'CONTRIBUTING.md', 'docs/API.md']:
            try:
                repo.get_contents(filename)
                doc_paths.append(filename)
            except:
                pass

    if not doc_paths:
        print("No documentation files found")
        sys.exit(1)

    print(f"📚 Reviewing {len(doc_paths)} documents in {args.repository}...")
    print(f"📋 Standards: {', '.join(standards)}\n")

    # Review each document
    total_score = 0
    for doc_path in doc_paths:
        print(f"📄 {doc_path}")
        try:
            file_content = repo.get_contents(doc_path)
            content = file_content.decoded_content.decode('utf-8')

            review = reviewer.review_documentation(
                repository=args.repository,
                doc_content=content,
                doc_path=doc_path,
                standards=standards
            )

            score = review['overall_score']
            total_score += score

            print(f"   Score: {score:.2f}/1.0")

            # Print check results
            for standard, result in review['checks'].items():
                emoji = "✅" if result['score'] >= 0.8 else "⚠️" if result['score'] >= 0.5 else "❌"
                print(f"   {emoji} {standard}: {result['score']:.2f}")

            # Print recommendations
            if review.get('recommendations'):
                print("   Recommendations:")
                for rec in review['recommendations'][:3]:
                    print(f"     • {rec}")

            print()

        except Exception as e:
            print(f"   ❌ Error: {str(e)}\n")

    # Overall summary
    avg_score = total_score / len(doc_paths)
    if avg_score >= 0.8:
        emoji = "✅"
        rating = "Excellent"
    elif avg_score >= 0.6:
        emoji = "👍"
        rating = "Good"
    elif avg_score >= 0.4:
        emoji = "⚠️"
        rating = "Fair"
    else:
        emoji = "❌"
        rating = "Needs Improvement"

    print(f"{emoji} Overall Rating: {rating} ({avg_score:.2f}/1.0)")


if __name__ == '__main__':
    main()
```

Make it executable:
```bash
chmod +x scripts/review_docs.py
```

Use it:
```bash
python scripts/review_docs.py patelmm79/dev-nexus
python scripts/review_docs.py patelmm79/dev-nexus --files README.md CLAUDE.md --all-standards
```

## Next Steps

1. **Test the integration** - Verify the skill works correctly
2. **Update CLAUDE.md** - Document the new skill
3. **Deploy to Cloud Run** - Make it available 24/7
4. **Create a GitHub Action** - Automatically review docs on PRs
5. **Build a dashboard** - Visualize documentation quality across all projects

## Troubleshooting

**Skill not appearing in AgentCard**
- Check for JSON syntax errors (missing commas, brackets)
- Restart the server after making changes

**"Unknown skill" error**
- Ensure routing is added in both `execute()` method and the error message list
- Check for typos in skill_id

**Authentication errors accessing GitHub**
- Verify GITHUB_TOKEN has repo read access
- Check repository name format (owner/repo)

**Claude API errors**
- Verify ANTHROPIC_API_KEY is set correctly
- Check API quota and rate limits
