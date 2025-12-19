"""
Component Sensibility Skills

A2A skills for detecting misplaced components and recommending consolidation.
Provides architectural sensibility analysis - identifying components that would be
better used in a different project or as central shared infrastructure.
"""

import logging
import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import uuid4

import anthropic
from github import Github

from a2a.skills.base import BaseSkill, SkillGroup
from core.component_analyzer import ComponentScanner, VectorCacheManager, CentralityCalculator
from core.postgres_repository import PostgresRepository
from core.pattern_extractor import PatternExtractor
from schemas.knowledge_base_v2 import ConsolidationRecommendation, Component

logger = logging.getLogger(__name__)


class DetectMisplacedComponentsSkill(BaseSkill):
    """
    Detect components that might be better located in other repositories

    Scans one or more repositories for components that are similar to components
    in other repositories, suggesting they might be better centralized.
    """

    def __init__(self, vector_manager: VectorCacheManager, postgres_repo: PostgresRepository):
        """Initialize skill with dependencies"""
        self.vector_manager = vector_manager
        self.postgres_repo = postgres_repo

    @property
    def skill_id(self) -> str:
        return "detect_misplaced_components"

    @property
    def skill_name(self) -> str:
        return "Detect Misplaced Components"

    @property
    def skill_description(self) -> str:
        return "Scan repositories for components that appear in multiple places or might be better centralized. Returns similar components and recommendations for canonical locations."

    @property
    def tags(self) -> List[str]:
        return ["architecture", "component-sensibility", "consolidation", "code-reuse"]

    @property
    def requires_authentication(self) -> bool:
        return False

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository to analyze (format: 'owner/repo'). If omitted, analyzes all repositories."
                },
                "component_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Types of components to analyze. Options: api_client, infrastructure, business_logic, deployment_pattern. Default: all types."
                },
                "min_similarity_score": {
                    "type": "number",
                    "default": 0.5,
                    "description": "Minimum similarity threshold (0-1) to flag as potential duplicate"
                },
                "include_diverged": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include components that started identical but diverged"
                },
                "top_k_matches": {
                    "type": "integer",
                    "default": 5,
                    "description": "Maximum similar components to return per component"
                }
            }
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {"repository": "patelmm79/agentic-log-attacker"},
                "description": "Detect misplaced components in agentic-log-attacker"
            },
            {
                "input": {
                    "repository": "patelmm79/dev-nexus",
                    "component_types": ["api_client", "infrastructure"]
                },
                "description": "Scan dev-nexus for misplaced API clients and infrastructure utilities"
            },
            {
                "input": {"component_types": ["api_client"], "min_similarity_score": 0.7},
                "description": "Find all duplicate API clients across all repositories"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute skill: detect misplaced components"""
        try:
            repo_name = input_data.get("repository")
            component_types = input_data.get("component_types", [])
            min_similarity = input_data.get("min_similarity_score", 0.5)
            include_diverged = input_data.get("include_diverged", True)
            top_k = input_data.get("top_k_matches", 5)

            logger.info(f"Detecting misplaced components. Repository: {repo_name or 'all'}")

            # Load knowledge base
            kb = await self.postgres_repo.load_knowledge_base()
            if not kb:
                return {
                    "success": False,
                    "error": "Could not load knowledge base"
                }

            # Get components to analyze
            components_to_analyze = []

            if repo_name:
                repo_data = kb.repositories.get(repo_name)
                if not repo_data:
                    return {
                        "success": False,
                        "error": f"Repository not found: {repo_name}"
                    }
                components_to_analyze = [c for c in repo_data.components]
            else:
                # Analyze all repositories
                for repo_data in kb.repositories.values():
                    components_to_analyze.extend(repo_data.components)

            # Filter by type if specified
            if component_types:
                components_to_analyze = [
                    c for c in components_to_analyze
                    if c.component_type in component_types
                ]

            if not components_to_analyze:
                return {
                    "success": True,
                    "misplaced_components": [],
                    "summary": "No components found matching criteria"
                }

            # Find similar components for each
            misplaced_components = []

            for component in components_to_analyze:
                try:
                    similar = self.vector_manager.find_similar(
                        component,
                        top_k=top_k,
                        min_similarity=min_similarity
                    )

                    if similar:
                        # Filter by diverged status if needed
                        if not include_diverged:
                            similar = [s for s in similar if s.get("type") != "diverged"]

                        if similar:
                            misplaced_components.append({
                                "component_id": component.component_id,
                                "component_name": component.name,
                                "component_type": component.component_type,
                                "current_location": component.repository,
                                "current_files": component.files,
                                "similar_components": similar,
                                "similar_count": len(similar),
                                "potential_consolidation": True
                            })

                except Exception as e:
                    logger.debug(f"Error finding similar components for {component.name}: {e}")

            # Analyze canonical locations
            calculator = CentralityCalculator(kb.model_dump())

            for comp_info in misplaced_components:
                # Find candidate repositories
                candidate_repos = set(
                    s["repository"] for s in comp_info["similar_components"]
                )
                candidate_repos.add(comp_info["current_location"])

                if candidate_repos:
                    scores = calculator.calculate_canonical_score(
                        components_to_analyze[0],  # Use first component as template
                        list(candidate_repos)
                    )

                    # Find best candidate
                    best_candidate = max(
                        scores.items(),
                        key=lambda x: x[1]["canonical_score"]
                    )

                    comp_info["canonical_recommendation"] = {
                        "repository": best_candidate[0],
                        "canonical_score": best_candidate[1]["canonical_score"],
                        "current_score": scores[comp_info["current_location"]]["canonical_score"],
                        "reasoning": best_candidate[1]["reasoning"],
                        "all_scores": scores
                    }

            result = {
                "success": True,
                "analyzed_repository": repo_name or "all",
                "components_analyzed": len(components_to_analyze),
                "misplaced_components_found": len(misplaced_components),
                "misplaced_components": misplaced_components[:10],  # Top 10 recommendations
                "analysis_timestamp": datetime.now().isoformat()
            }

            logger.info(f"Detection complete: Found {len(misplaced_components)} misplaced components")
            return result

        except Exception as e:
            logger.error(f"Skill execution error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }


class AnalyzeComponentCentralitySkill(BaseSkill):
    """
    Analyze canonical location scores for a component

    Provides detailed factor-by-factor breakdown of why a particular repository
    is the best location for a component.
    """

    def __init__(self, postgres_repo: PostgresRepository):
        """Initialize skill"""
        self.postgres_repo = postgres_repo

    @property
    def skill_id(self) -> str:
        return "analyze_component_centrality"

    @property
    def skill_name(self) -> str:
        return "Analyze Component Centrality"

    @property
    def skill_description(self) -> str:
        return "Analyze and explain the canonical location scores for a component across candidate repositories. Returns detailed factor-by-factor breakdown."

    @property
    def tags(self) -> List[str]:
        return ["architecture", "component-sensibility", "scoring", "analysis"]

    @property
    def requires_authentication(self) -> bool:
        return False

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "component_name": {
                    "type": "string",
                    "description": "Name of component to analyze"
                },
                "current_location": {
                    "type": "string",
                    "description": "Current repository (format: 'owner/repo')"
                },
                "candidate_locations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Alternative repositories to evaluate. If omitted, evaluates all repositories with similar components."
                }
            },
            "required": ["component_name", "current_location"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "component_name": "GitHubAPIClient",
                    "current_location": "patelmm79/agentic-log-attacker"
                },
                "description": "Analyze centrality scores for GitHubAPIClient"
            },
            {
                "input": {
                    "component_name": "DatabaseConnection",
                    "current_location": "my-org/app",
                    "candidate_locations": ["my-org/dev-nexus", "my-org/infrastructure"]
                },
                "description": "Compare scores between two candidate locations"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute skill: analyze centrality"""
        try:
            component_name = input_data.get("component_name", "")
            current_location = input_data.get("current_location", "")
            candidate_locations = input_data.get("candidate_locations", [])

            if not component_name or not current_location:
                return {
                    "success": False,
                    "error": "Missing required parameters: 'component_name' and 'current_location'"
                }

            logger.info(f"Analyzing centrality for {component_name} in {current_location}")

            # Load KB
            kb = await self.postgres_repo.load_knowledge_base()
            if not kb:
                return {
                    "success": False,
                    "error": "Could not load knowledge base"
                }

            # Verify current location exists
            if current_location not in kb.repositories:
                return {
                    "success": False,
                    "error": f"Repository not found: {current_location}"
                }

            # If no candidates provided, use all repositories
            if not candidate_locations:
                candidate_locations = list(kb.repositories.keys())

            # Create calculator
            calculator = CentralityCalculator(kb.model_dump())

            # Get component data (mock for analysis)
            mock_component = type('Component', (), {
                'name': component_name,
                'cyclomatic_complexity': 5.0,
                'lines_of_code': 200
            })()

            # Calculate scores
            scores = calculator.calculate_canonical_score(
                mock_component,
                candidate_locations
            )

            # Sort by canonical score
            sorted_scores = sorted(
                scores.items(),
                key=lambda x: x[1]["canonical_score"],
                reverse=True
            )

            result = {
                "success": True,
                "component_name": component_name,
                "current_location": current_location,
                "analysis": {
                    "best_location": sorted_scores[0][0],
                    "best_score": float(sorted_scores[0][1]["canonical_score"]),
                    "all_scores": {
                        repo: {
                            "canonical_score": float(score["canonical_score"]),
                            "factors": {k: float(v) for k, v in score["factors"].items()},
                            "weights": score["weights"],
                            "reasoning": score["reasoning"]
                        }
                        for repo, score in sorted_scores
                    },
                    "recommendation": {
                        "from": current_location,
                        "to": sorted_scores[0][0],
                        "improvement": float(sorted_scores[0][1]["canonical_score"] - scores[current_location]["canonical_score"])
                    }
                },
                "analysis_timestamp": datetime.now().isoformat()
            }

            logger.info(f"Centrality analysis complete for {component_name}")
            return result

        except Exception as e:
            logger.error(f"Skill execution error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }


class RecommendConsolidationPlanSkill(BaseSkill):
    """
    Generate consolidation plan for moving a component

    Creates a phased consolidation plan with effort estimates, risk assessment,
    and impact analysis from dependency-orchestrator and pattern-miner.
    """

    def __init__(self, postgres_repo: PostgresRepository, integration_service: Optional[Any] = None):
        """Initialize skill"""
        self.postgres_repo = postgres_repo
        self.integration_service = integration_service

    @property
    def skill_id(self) -> str:
        return "recommend_consolidation_plan"

    @property
    def skill_name(self) -> str:
        return "Recommend Consolidation Plan"

    @property
    def skill_description(self) -> str:
        return "Generate a detailed consolidation plan for moving a component to its canonical location. Includes phased approach, effort estimates, risk assessment, and impact analysis."

    @property
    def tags(self) -> List[str]:
        return ["architecture", "component-sensibility", "planning", "consolidation"]

    @property
    def requires_authentication(self) -> bool:
        return False

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "component_name": {
                    "type": "string",
                    "description": "Name of component to consolidate"
                },
                "from_repository": {
                    "type": "string",
                    "description": "Current repository (format: 'owner/repo')"
                },
                "to_repository": {
                    "type": "string",
                    "description": "Target canonical repository. If omitted, uses highest-scoring location."
                },
                "include_impact_analysis": {
                    "type": "boolean",
                    "default": True,
                    "description": "Query dependency-orchestrator for impact assessment"
                },
                "include_deep_analysis": {
                    "type": "boolean",
                    "default": True,
                    "description": "Trigger pattern-miner for deep code comparison"
                }
            },
            "required": ["component_name", "from_repository"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "component_name": "GitHubAPIClient",
                    "from_repository": "patelmm79/agentic-log-attacker",
                    "to_repository": "patelmm79/dev-nexus"
                },
                "description": "Generate consolidation plan for GitHubAPIClient"
            },
            {
                "input": {
                    "component_name": "DatabasePool",
                    "from_repository": "my-app",
                    "include_impact_analysis": True
                },
                "description": "Generate plan with full impact analysis from orchestrator"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute skill: recommend consolidation plan"""
        try:
            component_name = input_data.get("component_name", "")
            from_repo = input_data.get("from_repository", "")
            to_repo = input_data.get("to_repository")
            include_impact = input_data.get("include_impact_analysis", True)
            include_deep = input_data.get("include_deep_analysis", True)

            if not component_name or not from_repo:
                return {
                    "success": False,
                    "error": "Missing required parameters: 'component_name' and 'from_repository'"
                }

            logger.info(f"Generating consolidation plan for {component_name} from {from_repo} to {to_repo or 'TBD'}")

            # Load KB
            kb = await self.postgres_repo.load_knowledge_base()
            if not kb:
                return {
                    "success": False,
                    "error": "Could not load knowledge base"
                }

            # If target not specified, calculate canonical location
            if not to_repo:
                calculator = CentralityCalculator(kb.model_dump())
                candidates = list(kb.repositories.keys())
                mock_component = type('Component', (), {
                    'name': component_name,
                    'cyclomatic_complexity': 5.0,
                    'lines_of_code': 200
                })()
                scores = calculator.calculate_canonical_score(mock_component, candidates)
                to_repo = max(scores.items(), key=lambda x: x[1]["canonical_score"])[0]

            # Generate recommendation ID
            rec_id = str(uuid4())[:8]

            # Build consolidation plan
            plan = self._generate_consolidation_plan(
                component_name, from_repo, to_repo, kb, include_impact, include_deep
            )

            # Query impact analysis if available
            impact_analysis = None
            if include_impact and self.integration_service:
                try:
                    impact_analysis = self.integration_service.query_consolidation_impact(
                        component_name, from_repo, to_repo
                    )
                except Exception as e:
                    logger.debug(f"Could not get impact analysis: {e}")

            # Trigger deep analysis if available
            deep_analysis = None
            if include_deep and self.integration_service:
                try:
                    deep_analysis = self.integration_service.trigger_component_analysis(
                        from_repo, [component_name], focus_areas=["api_compatibility", "behavioral_differences"]
                    )
                except Exception as e:
                    logger.debug(f"Could not get deep analysis: {e}")

            # Create recommendation record
            recommendation = ConsolidationRecommendation(
                recommendation_id=rec_id,
                timestamp=datetime.now(),
                component_id=component_name,  # Simplified
                from_repository=from_repo,
                to_repository=to_repo,
                priority="HIGH",
                confidence=0.85,
                reasoning=f"Component {component_name} appears in {to_repo}, which is better positioned as canonical location",
                benefits=[
                    "Single source of truth",
                    "Reduced maintenance burden",
                    "Easier updates and bug fixes"
                ],
                risks=[
                    "Requires updates to consumer repositories",
                    "Potential API changes during consolidation"
                ],
                estimated_effort_hours="4-6"
            )

            result = {
                "success": True,
                "recommendation_id": rec_id,
                "component_name": component_name,
                "consolidation_plan": plan,
                "impact_analysis": impact_analysis,
                "deep_analysis": deep_analysis,
                "recommendation": recommendation.model_dump(mode='json'),
                "recommendation_timestamp": datetime.now().isoformat()
            }

            logger.info(f"Consolidation plan generated: {rec_id}")
            return result

        except Exception as e:
            logger.error(f"Skill execution error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }

    def _generate_consolidation_plan(
        self,
        component_name: str,
        from_repo: str,
        to_repo: str,
        kb: Any,
        include_impact: bool,
        include_deep: bool
    ) -> Dict[str, Any]:
        """Generate phased consolidation plan"""
        return {
            "phase_1": {
                "name": "Analyze & Prepare",
                "description": "Deep analysis of component implementation in both locations",
                "tasks": [
                    "Compare API signatures",
                    "Identify behavioral differences",
                    "Document feature gaps",
                    "Create migration checklist"
                ],
                "estimated_hours": "2-3",
                "blockers": []
            },
            "phase_2": {
                "name": "Merge & Standardize",
                "description": "Merge implementations and create canonical version",
                "tasks": [
                    "Merge code into target repository",
                    "Standardize API and behavior",
                    "Add comprehensive tests",
                    "Document usage patterns"
                ],
                "estimated_hours": "3-4",
                "blockers": []
            },
            "phase_3": {
                "name": "Update Consumers",
                "description": "Update all repositories importing this component",
                "tasks": [
                    "Update import statements",
                    "Run integration tests",
                    "Update documentation",
                    "Cleanup old implementations"
                ],
                "estimated_hours": "2-3",
                "affected_repositories": [
                    repo for repo in kb.repositories.keys()
                    if repo != to_repo
                ]
            },
            "phase_4": {
                "name": "Monitor & Verify",
                "description": "Monitor production and verify consolidation success",
                "tasks": [
                    "Monitor error rates",
                    "Track performance metrics",
                    "Collect user feedback",
                    "Document lessons learned"
                ],
                "estimated_hours": "1-2",
                "success_criteria": [
                    "No increase in error rates",
                    "All tests passing",
                    "Consumer repositories updated"
                ]
            },
            "total_estimated_effort": "8-12 hours"
        }


class ScanRepositoryComponentsSkill(BaseSkill):
    """
    Scan a specific repository for components and update the component index

    Triggers component detection, vectorization, and centrality analysis
    for a single repository on-demand. Useful for triggering component analysis
    from the frontend Repositories tab.
    """

    def __init__(
        self,
        postgres_repo: PostgresRepository,
        vector_manager: VectorCacheManager,
        anthropic_client: Optional[anthropic.Anthropic] = None,
        github_client: Optional[Github] = None
    ):
        """Initialize skill with dependencies"""
        self.postgres_repo = postgres_repo
        self.vector_manager = vector_manager
        self.anthropic_client = anthropic_client
        self.github_client = github_client
        self.pattern_extractor = PatternExtractor(anthropic_client) if anthropic_client else None

    @property
    def skill_id(self) -> str:
        return "scan_repository_components"

    @property
    def skill_name(self) -> str:
        return "Scan Repository Components"

    @property
    def skill_description(self) -> str:
        return "Scan a repository for components and update the component index. Extracts API clients, infrastructure utilities, business logic, and deployment patterns."

    @property
    def tags(self) -> List[str]:
        return ["architecture", "component-sensibility", "scanning", "repository-analysis"]

    @property
    def requires_authentication(self) -> bool:
        return False

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository to scan (format: 'owner/repo')"
                }
            },
            "required": ["repository"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {"repository": "patelmm79/dev-nexus"},
                "description": "Scan dev-nexus for all component types"
            },
            {
                "input": {"repository": "patelmm79/agentic-log-attacker"},
                "description": "Scan agentic-log-attacker repository"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute component scanning for repository"""
        try:
            repository = input_data.get("repository", "").strip()

            if not repository:
                return {
                    "success": False,
                    "error": "Repository name is required (format: 'owner/repo')"
                }

            # Load KB
            kb = await self.postgres_repo.load_knowledge_base()
            if not kb:
                return {
                    "success": False,
                    "error": "Could not load knowledge base"
                }

            if repository not in kb.repositories:
                return {
                    "success": False,
                    "error": f"Repository '{repository}' not found in knowledge base"
                }

            repo_data = kb.repositories[repository]
            logger.info(f"Scanning components in {repository} using pattern extraction")

            components = []

            # If pattern extractor is available, fetch repo code and extract patterns
            if self.pattern_extractor and self.github_client:
                try:
                    owner, repo = repository.split("/")
                    logger.info(f"[SCAN] Starting pattern extraction for {repository}")

                    logger.info(f"[SCAN] Fetching GitHub repository object for {owner}/{repo}")
                    gh_repo = self.github_client.get_user(owner).get_repo(repo)
                    logger.info(f"[SCAN] Successfully retrieved GitHub repository object")

                    # Fetch main branch content
                    logger.info(f"[SCAN] Starting file collection from repository root")
                    start_collect = datetime.now()

                    # Collect code files
                    code_files = {}
                    self._collect_code_files(gh_repo, "", code_files)

                    collect_duration = (datetime.now() - start_collect).total_seconds()
                    logger.info(f"[SCAN] File collection completed in {collect_duration:.2f}s. Found {len(code_files)} code files")

                    if code_files:
                        # Prepare changes dict for pattern extractor
                        logger.info(f"[SCAN] Preparing file list for Claude analysis (limiting to 20 files)")
                        files_changed = []
                        for filepath, content in list(code_files.items())[:20]:  # Limit to first 20 files
                            files_changed.append({
                                "path": filepath,
                                "change_type": "modified",
                                "diff": content[:2000]  # Limit content size
                            })

                        logger.info(f"[SCAN] Prepared {len(files_changed)} files for analysis")

                        if files_changed:
                            logger.info(f"[SCAN] Fetching repository commits for commit SHA")
                            try:
                                commit_sha = gh_repo.get_commits()[0].sha if gh_repo.get_commits() else "unknown"
                                logger.info(f"[SCAN] Got commit SHA: {commit_sha}")
                            except Exception as e:
                                logger.warning(f"[SCAN] Could not fetch commits: {e}, using 'unknown'")
                                commit_sha = "unknown"

                            changes = {
                                "commit_sha": commit_sha,
                                "commit_message": f"Repository analysis for {repository}",
                                "author": "system",
                                "timestamp": datetime.now().isoformat(),
                                "files_changed": files_changed
                            }

                            # Extract patterns using Claude
                            logger.info(f"[SCAN] Starting Claude pattern extraction for {len(files_changed)} files")
                            start_claude = datetime.now()
                            pattern_entry = self.pattern_extractor.extract_patterns_with_llm(
                                changes,
                                repository
                            )
                            claude_duration = (datetime.now() - start_claude).total_seconds()
                            logger.info(f"[SCAN] Claude analysis completed in {claude_duration:.2f}s")

                            # Convert reusable_components to Component objects
                            logger.info(f"[SCAN] Converting {len(pattern_entry.reusable_components)} detected components to Component objects")
                            for i, reusable_comp in enumerate(pattern_entry.reusable_components):
                                logger.debug(f"[SCAN] Processing component {i+1}: {reusable_comp.name}")
                                component = Component(
                                    component_id=f"{repository}-{reusable_comp.name}-{i}",
                                    name=reusable_comp.name,
                                    component_type="infrastructure" if "util" in reusable_comp.name.lower() else "api_client",
                                    repository=repository,
                                    files=reusable_comp.files or [],
                                    language=reusable_comp.language or "python",
                                    api_signature=reusable_comp.api_contract,
                                    imports=[],
                                    keywords=pattern_entry.keywords,
                                    description=reusable_comp.description,
                                    lines_of_code=0,
                                    cyclomatic_complexity=None,
                                    public_methods=[],
                                    first_seen=datetime.now(),
                                    sync_status="original"
                                )
                                components.append(component)
                            logger.info(f"[SCAN] Component conversion completed: {len(components)} components ready for vectorization")
                    else:
                        logger.warning(f"[SCAN] No code files found in {repository}")

                except Exception as e:
                    logger.warning(f"[SCAN] Pattern extraction failed: {type(e).__name__}: {e}. Using existing components from KB.", exc_info=True)
                    components = repo_data.components if hasattr(repo_data, 'components') and repo_data.components else []
            else:
                # Fallback: use pre-scanned components from KB
                logger.info("Pattern extractor not available, using pre-scanned components from KB")
                components = repo_data.components if hasattr(repo_data, 'components') and repo_data.components else []

            logger.info(f"[SCAN] Found {len(components)} components in {repository}")

            # Generate vectors for each component if vector manager available
            logger.info(f"[SCAN] Starting vectorization of {len(components)} components")
            start_vectorize = datetime.now()
            vectors_generated = 0
            for i, component in enumerate(components):
                try:
                    logger.debug(f"[SCAN] Vectorizing component {i+1}/{len(components)}: {component.name}")
                    vector = self.vector_manager.get_or_create_vector(component)
                    if vector:
                        vectors_generated += 1
                        logger.debug(f"[SCAN] Successfully vectorized {component.name}")
                    else:
                        logger.debug(f"[SCAN] No vector returned for {component.name}")
                except Exception as e:
                    logger.warning(f"[SCAN] Could not vectorize {component.name}: {type(e).__name__}: {e}")

            vectorize_duration = (datetime.now() - start_vectorize).total_seconds()
            logger.info(f"[SCAN] Vectorization completed in {vectorize_duration:.2f}s. Generated {vectors_generated} vectors")

            # Update KB with components
            repo_data.components = components

            return {
                "success": True,
                "repository": repository,
                "components_found": len(components),
                "vectors_generated": vectors_generated,
                "pattern_extraction": "enabled" if self.pattern_extractor else "disabled",
                "components": [
                    {
                        "name": c.name,
                        "type": c.component_type,
                        "files": c.files,
                        "loc": c.lines_of_code,
                        "methods": len(c.public_methods),
                        "description": c.description
                    }
                    for c in components
                ]
            }

        except Exception as e:
            logger.error(f"Error scanning repository: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def _collect_code_files(self, gh_repo, path: str, code_files: Dict[str, str], max_depth: int = 3, depth: int = 0):
        """Recursively collect code files from GitHub repository"""
        if depth > max_depth:
            logger.debug(f"[SCAN] Reached max depth ({max_depth}) at path: {path}")
            return

        try:
            logger.debug(f"[SCAN] Reading directory at depth {depth}: {path or '(root)'}")
            contents = gh_repo.get_contents(path) if path else gh_repo.get_contents("")

            if isinstance(contents, list):
                logger.debug(f"[SCAN] Found {len(contents)} items in {path or '(root)'}")
                files_in_dir = 0
                dirs_in_dir = 0

                for content in contents:
                    # Skip common non-code directories
                    if any(skip in content.path for skip in [".git", "node_modules", ".pytest", "__pycache__", "venv", ".github"]):
                        logger.debug(f"[SCAN] Skipping directory: {content.path}")
                        continue

                    if content.type == "file":
                        # Collect Python, JS, TS files
                        if any(content.path.endswith(ext) for ext in [".py", ".js", ".ts", ".go", ".java"]):
                            try:
                                logger.debug(f"[SCAN] Downloading file: {content.path}")
                                code_files[content.path] = content.decoded_content.decode("utf-8", errors="ignore")
                                files_in_dir += 1
                            except Exception as e:
                                logger.warning(f"[SCAN] Could not decode {content.path}: {type(e).__name__}: {e}")
                    elif content.type == "dir":
                        logger.debug(f"[SCAN] Recursing into directory: {content.path}")
                        dirs_in_dir += 1
                        self._collect_code_files(gh_repo, content.path, code_files, max_depth, depth + 1)

                logger.debug(f"[SCAN] Completed reading {path or '(root)'}: {files_in_dir} files, {dirs_in_dir} subdirs. Total collected so far: {len(code_files)}")
        except Exception as e:
            logger.warning(f"[SCAN] Could not read directory {path or '(root)'}: {type(e).__name__}: {e}")


class ComponentSensibilitySkills(SkillGroup):
    """
    Skill group for component sensibility analysis and consolidation

    Provides three complementary skills:
    1. detect_misplaced_components - Find components that should be centralized
    2. analyze_component_centrality - Score canonical locations
    3. recommend_consolidation_plan - Generate consolidation roadmap

    Integrates with external A2A agents:
    - dependency-orchestrator: Impact analysis and dependency tracking
    - pattern-miner: Deep code comparison and behavioral analysis
    """

    def __init__(
        self,
        postgres_repo: PostgresRepository,
        vector_manager: VectorCacheManager = None,
        anthropic_client: Optional[anthropic.Anthropic] = None,
        github_client: Optional[Github] = None,
        **kwargs
    ):
        """
        Initialize skill group

        Args:
            postgres_repo: PostgresRepository instance for knowledge base operations
            vector_manager: VectorCacheManager instance
            anthropic_client: Anthropic API client for pattern extraction
            github_client: GitHub API client for repository access
        """
        super().__init__(**kwargs)

        self.postgres_repo = postgres_repo
        self.anthropic_client = anthropic_client
        self.github_client = github_client

        # Initialize vector cache manager if not provided
        if vector_manager is None:
            postgres_url = os.environ.get("DATABASE_URL", "postgresql://localhost/devnexus")
            try:
                vector_manager = VectorCacheManager(postgres_url)
            except Exception as e:
                logger.warning(f"Vector manager not available: {e}")
                # Create mock vector manager for graceful degradation
                class MockVectorCacheManager:
                    def __init__(self, url):
                        self.postgres_url = url
                    def get_or_create_vector(self, component):
                        return None
                    def find_similar(self, component, top_k=5, min_similarity=0.5):
                        return []
                vector_manager = MockVectorCacheManager(postgres_url)

        self.vector_manager = vector_manager

        # Get integration service if available
        self.integration_service = None
        try:
            from core.integration_service import IntegrationService
            self.integration_service = IntegrationService()
        except Exception as e:
            logger.debug(f"Integration service not available: {e}")

        logger.info("Initialized ComponentSensibilitySkills with A2A integration")

    def get_skills(self) -> List[BaseSkill]:
        """Return all skills in this group"""
        detect_skill = DetectMisplacedComponentsSkill(self.vector_manager, self.postgres_repo)
        analyze_skill = AnalyzeComponentCentralitySkill(self.postgres_repo)
        recommend_skill = RecommendConsolidationPlanSkill(self.postgres_repo, self.integration_service)
        scan_skill = ScanRepositoryComponentsSkill(
            self.postgres_repo,
            self.vector_manager,
            self.anthropic_client,
            self.github_client
        )

        return [detect_skill, analyze_skill, recommend_skill, scan_skill]
