"""
Component Sensibility Skills

A2A skills for detecting misplaced components and recommending consolidation.
Provides architectural sensibility analysis - identifying components that would be
better used in a different project or as central shared infrastructure.
"""

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from uuid import uuid4

from a2a.skills.base import BaseSkill, SkillGroup
from core.component_analyzer import ComponentScanner, VectorCacheManager, CentralityCalculator
from core.knowledge_base import KnowledgeBaseManager
from schemas.knowledge_base_v2 import ConsolidationRecommendation

logger = logging.getLogger(__name__)


class DetectMisplacedComponentsSkill(BaseSkill):
    """
    Detect components that might be better located in other repositories

    Scans one or more repositories for components that are similar to components
    in other repositories, suggesting they might be better centralized.
    """

    def __init__(self, vector_manager: VectorCacheManager, kb_manager: KnowledgeBaseManager):
        """Initialize skill with dependencies"""
        self.vector_manager = vector_manager
        self.kb_manager = kb_manager

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
            kb = self.kb_manager.load_current()
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

    def __init__(self, kb_manager: KnowledgeBaseManager):
        """Initialize skill"""
        self.kb_manager = kb_manager

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
            kb = self.kb_manager.load_current()
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

    def __init__(self, kb_manager: KnowledgeBaseManager, integration_service: Optional[Any] = None):
        """Initialize skill"""
        self.kb_manager = kb_manager
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
            kb = self.kb_manager.load_current()
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

    def __init__(self, kb_manager: KnowledgeBaseManager = None, vector_manager: VectorCacheManager = None, **kwargs):
        """
        Initialize skill group

        Args:
            kb_manager: KnowledgeBaseManager instance
            vector_manager: VectorCacheManager instance
        """
        super().__init__(**kwargs)

        # Initialize knowledge base manager if not provided
        if kb_manager is None:
            kb_manager = KnowledgeBaseManager()

        # Initialize vector cache manager if not provided
        if vector_manager is None:
            postgres_url = os.environ.get("DATABASE_URL", "postgresql://localhost/devnexus")
            vector_manager = VectorCacheManager(postgres_url)

        self.kb_manager = kb_manager
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
        detect_skill = DetectMisplacedComponentsSkill(self.vector_manager, self.kb_manager)
        analyze_skill = AnalyzeComponentCentralitySkill(self.kb_manager)
        recommend_skill = RecommendConsolidationPlanSkill(self.kb_manager, self.integration_service)

        return [detect_skill, analyze_skill, recommend_skill]
