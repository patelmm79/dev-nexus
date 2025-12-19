"""
Component Sensibility Demo

Demonstrates how to use the component sensibility skills to:
1. Detect misplaced components across repositories
2. Analyze canonical locations for components
3. Generate consolidation plans

Usage:
    python examples/component_sensibility_demo.py
"""

import asyncio
import os
import json
from pathlib import Path

from core.component_analyzer import ComponentScanner, VectorCacheManager, CentralityCalculator
from core.knowledge_base import KnowledgeBaseManager
from a2a.skills.component_sensibility import ComponentSensibilitySkills
from schemas.knowledge_base_v2 import (
    Component, KnowledgeBaseV2, RepositoryMetadata, PatternEntry,
    DeploymentInfo, DependencyInfo, TestingInfo, SecurityInfo
)
from datetime import datetime


def create_mock_knowledge_base() -> KnowledgeBaseV2:
    """Create a mock knowledge base for demonstration"""
    now = datetime.now()

    # Create repositories
    dev_nexus = RepositoryMetadata(
        latest_patterns=PatternEntry(
            patterns=["A2A Server", "Skill Registry", "Knowledge Base"],
            decisions=[],
            reusable_components=[],
            dependencies=[],
            problem_domain="Infrastructure and Pattern Discovery",
            keywords=["architecture", "patterns", "A2A", "infrastructure"],
            analyzed_at=now,
            commit_sha="abc123"
        ),
        deployment=DeploymentInfo(),
        dependencies=DependencyInfo(consumers=[]),
        testing=TestingInfo(),
        security=SecurityInfo(),
        last_updated=now
    )

    # Add sample GitHub client component to dev-nexus
    github_client_dev_nexus = Component(
        component_id="github-client-dev-nexus",
        name="GitHubAPIClient",
        component_type="api_client",
        repository="patelmm79/dev-nexus",
        files=["core/github_client.py"],
        language="python",
        api_signature="get_repo(), list_issues(), create_pull_request()",
        imports=["requests", "json", "logging"],
        keywords=["github", "api", "rest", "client"],
        description="Central GitHub API client for dev-nexus",
        lines_of_code=250,
        cyclomatic_complexity=8.0,
        public_methods=["get_repo", "list_issues", "create_pull_request"],
        first_seen=now,
        sync_status="original"
    )
    dev_nexus.components = [github_client_dev_nexus]

    agentic_log_attacker = RepositoryMetadata(
        latest_patterns=PatternEntry(
            patterns=["Log Analysis", "GitHub Integration", "MCP Client"],
            decisions=[],
            reusable_components=[],
            dependencies=[],
            problem_domain="Production Monitoring and Log Analysis",
            keywords=["logs", "monitoring", "github", "mcp"],
            analyzed_at=now,
            commit_sha="def456"
        ),
        deployment=DeploymentInfo(),
        dependencies=DependencyInfo(consumers=[]),
        testing=TestingInfo(),
        security=SecurityInfo(),
        last_updated=now
    )

    # Add duplicate GitHub client to agentic-log-attacker
    github_client_ala = Component(
        component_id="github-client-ala",
        name="GitHubClient",
        component_type="api_client",
        repository="patelmm79/agentic-log-attacker",
        files=["github_integration/client.py"],
        language="python",
        api_signature="get_repo(), list_issues(), create_pr()",
        imports=["requests", "json"],
        keywords=["github", "api", "client"],
        description="GitHub integration for issue tracking",
        lines_of_code=280,  # Slightly different LOC
        cyclomatic_complexity=7.5,
        public_methods=["get_repo", "list_issues", "create_pr"],
        first_seen=now,
        sync_status="diverged"  # Diverged from original
    )
    agentic_log_attacker.components = [github_client_ala]

    # Create KB
    kb = KnowledgeBaseV2(
        repositories={
            "patelmm79/dev-nexus": dev_nexus,
            "patelmm79/agentic-log-attacker": agentic_log_attacker
        },
        created_at=now,
        last_updated=now
    )

    return kb


def demo_component_detection():
    """Demo 1: Detect misplaced components"""
    print("\n" + "="*70)
    print("DEMO 1: Detect Misplaced Components")
    print("="*70)
    print("""
This demo shows how to detect components that appear in multiple
repositories and might be better consolidated.

Example: GitHub API client exists in both:
- dev-nexus (infrastructure repo)
- agentic-log-attacker (application repo)

We want to identify this duplication for consolidation.
""")

    kb = create_mock_knowledge_base()

    print("\nRepositories in knowledge base:")
    for repo_name, repo_data in kb.repositories.items():
        print(f"  - {repo_name}")
        print(f"    Components: {[c.name for c in repo_data.components]}")
        print(f"    Domain: {repo_data.latest_patterns.problem_domain}")


def demo_component_analysis():
    """Demo 2: Analyze component centrality"""
    print("\n" + "="*70)
    print("DEMO 2: Analyze Component Centrality")
    print("="*70)
    print("""
This demo shows how to score candidate repositories as canonical
locations for a component using multi-factor heuristics.

Factors considered (weighted):
- Repository purpose (30%)     → Infrastructure > Application
- Usage count (30%)            → Central repos score higher
- Dependency centrality (20%)  → Hub position in dependency graph
- Maintenance activity (10%)   → Recent activity preferred
- Component complexity (5%)    → Complex components need maintenance
- First implementation (5%)    → Tie-breaker

Example: Scoring GitHubAPIClient across candidates
""")

    kb = create_mock_knowledge_base()

    calculator = CentralityCalculator({
        "patelmm79/dev-nexus": {
            "problem_domain": "Infrastructure and Pattern Discovery",
            "dependencies": {"consumers": ["repo1", "repo2"]}
        },
        "patelmm79/agentic-log-attacker": {
            "problem_domain": "Production Monitoring",
            "dependencies": {"consumers": []}
        }
    })

    github_client = kb.repositories["patelmm79/agentic-log-attacker"].components[0]

    scores = calculator.calculate_canonical_score(
        github_client,
        ["patelmm79/dev-nexus", "patelmm79/agentic-log-attacker"]
    )

    print("\nCanonical Location Scores:")
    print("-" * 70)

    for repo, score_data in sorted(
        scores.items(),
        key=lambda x: x[1]["canonical_score"],
        reverse=True
    ):
        score = score_data["canonical_score"]
        print(f"\n{repo}: {score:.3f}")
        print(f"  Reasoning: {score_data['reasoning']}")
        print(f"  Factors:")
        for factor, value in score_data["factors"].items():
            weight = score_data["weights"][factor]
            contribution = value * weight
            print(f"    - {factor}: {value:.2f} × {weight} = {contribution:.3f}")


def demo_consolidation_plan():
    """Demo 3: Generate consolidation plan"""
    print("\n" + "="*70)
    print("DEMO 3: Generate Consolidation Plan")
    print("="*70)
    print("""
This demo shows how to generate a phased consolidation plan for
moving a component to its canonical location.

The plan includes:
- Phase 1: Analyze & Prepare (2-3 hrs)
- Phase 2: Merge & Standardize (3-4 hrs)
- Phase 3: Update Consumers (2-3 hrs)
- Phase 4: Monitor & Verify (1-2 hrs)

Each phase includes specific, actionable tasks.
""")

    kb = create_mock_knowledge_base()

    from a2a.skills.component_sensibility import RecommendConsolidationPlanSkill
    skill = RecommendConsolidationPlanSkill(None)

    plan = skill._generate_consolidation_plan(
        "GitHubAPIClient",
        "patelmm79/agentic-log-attacker",
        "patelmm79/dev-nexus",
        kb.model_dump(),
        False,
        False
    )

    print("\nConsolidation Plan: GitHubAPIClient")
    print(f"From: patelmm79/agentic-log-attacker")
    print(f"To: patelmm79/dev-nexus")
    print("-" * 70)

    for phase_key in ["phase_1", "phase_2", "phase_3", "phase_4"]:
        phase = plan[phase_key]
        print(f"\n{phase_key.upper()}: {phase['name']}")
        print(f"Description: {phase['description']}")
        print(f"Estimated effort: {phase['estimated_hours']}")
        print("Tasks:")
        for task in phase["tasks"]:
            print(f"  - {task}")

    print(f"\nTotal estimated effort: {plan['total_estimated_effort']}")


def demo_real_world_scenario():
    """Demo 4: Real-world scenario walkthrough"""
    print("\n" + "="*70)
    print("DEMO 4: Real-World Scenario - GitHub Integration Consolidation")
    print("="*70)
    print("""
Scenario: You notice that multiple services have GitHub integrations:
- agentic-log-attacker: Uses GitHub API for issue tracking
- pattern-miner: Uses GitHub for repository analysis
- dev-nexus: Central infrastructure service

Problem: GitHub integration code is duplicated across services,
making it hard to maintain and propagate improvements.

Solution: Consolidate GitHub integration to dev-nexus and have
other services import it.

Steps:
1. Detect duplicate GitHub clients across repositories
2. Analyze which repository is best positioned to be canonical
3. Generate consolidation plan with effort estimates
4. Execute plan in phases while maintaining backwards compatibility
""")

    kb = create_mock_knowledge_base()

    print("\nStep 1: Detect Duplicate Components")
    print("-" * 70)
    for repo_name, repo_data in kb.repositories.items():
        for comp in repo_data.components:
            if "github" in comp.name.lower():
                print(f"Found: {comp.name} in {repo_name}")
                print(f"  Type: {comp.component_type}")
                print(f"  LOC: {comp.lines_of_code}")
                print(f"  Status: {comp.sync_status}")

    print("\nStep 2: Determine Canonical Location")
    print("-" * 70)
    calculator = CentralityCalculator({
        "patelmm79/dev-nexus": {
            "problem_domain": "Infrastructure and Pattern Discovery",
            "dependencies": {"consumers": ["agentic-log-attacker", "pattern-miner"]}
        },
        "patelmm79/agentic-log-attacker": {
            "problem_domain": "Production Monitoring",
            "dependencies": {"consumers": []}
        }
    })

    github_client = kb.repositories["patelmm79/agentic-log-attacker"].components[0]
    scores = calculator.calculate_canonical_score(
        github_client,
        ["patelmm79/dev-nexus", "patelmm79/agentic-log-attacker"]
    )

    canonical = max(scores.items(), key=lambda x: x[1]["canonical_score"])
    print(f"Canonical location: {canonical[0]}")
    print(f"Score: {canonical[1]['canonical_score']:.3f}")
    print(f"Reasoning: {canonical[1]['reasoning']}")

    print("\nStep 3: Generate Consolidation Plan")
    print("-" * 70)

    from a2a.skills.component_sensibility import RecommendConsolidationPlanSkill
    skill = RecommendConsolidationPlanSkill(None)
    plan = skill._generate_consolidation_plan(
        "GitHubAPIClient",
        "patelmm79/agentic-log-attacker",
        "patelmm79/dev-nexus",
        kb.model_dump(),
        False,
        False
    )

    print(f"Phase 1: {plan['phase_1']['name']} ({plan['phase_1']['estimated_hours']})")
    print(f"Phase 2: {plan['phase_2']['name']} ({plan['phase_2']['estimated_hours']})")
    print(f"Phase 3: {plan['phase_3']['name']} ({plan['phase_3']['estimated_hours']})")
    print(f"Phase 4: {plan['phase_4']['name']} ({plan['phase_4']['estimated_hours']})")
    print(f"\nTotal effort: {plan['total_estimated_effort']}")

    print("\nExpected Benefits:")
    print("  ✓ Single source of truth for GitHub integration")
    print("  ✓ Easier to update and maintain")
    print("  ✓ Consistent behavior across services")
    print("  ✓ Reduced code duplication")


def main():
    """Run all demos"""
    print("\n" + "="*70)
    print("Component Sensibility System - Comprehensive Demo")
    print("="*70)

    # Run each demo
    demo_component_detection()
    demo_component_analysis()
    demo_consolidation_plan()
    demo_real_world_scenario()

    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("""
To use the component sensibility system in your project:

1. Install dependencies:
   pip install networkx sqlalchemy psycopg[binary]

2. Initialize pgvector:
   CREATE EXTENSION IF NOT EXISTS vector;

3. Run the migration:
   python migrations/003_add_component_provenance.py

4. Query skills via A2A protocol:
   POST /a2a/execute
   {
     "skill_id": "detect_misplaced_components",
     "input": {"repository": "owner/repo"}
   }

See CLAUDE.md for complete documentation.
""")


if __name__ == "__main__":
    main()
