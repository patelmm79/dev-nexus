"""
Integration Service

Coordinates bidirectional A2A communication with external agents:
- dependency-orchestrator: Dependency triage and impact analysis
- pattern-miner: Deep pattern extraction and similarity analysis
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from a2a.client import ExternalAgentRegistry
from schemas.knowledge_base_v2 import PatternEntry, KnowledgeBaseV2


class IntegrationService:
    """
    Service for coordinating with external A2A agents

    Manages bidirectional communication with dependency-orchestrator
    and pattern-miner.
    """

    def __init__(self):
        """Initialize integration service with agent registry"""
        self.registry = ExternalAgentRegistry()

    # ==========================================
    # Dependency-Orchestrator Integration
    # ==========================================

    def notify_dependency_change(
        self,
        repository: str,
        patterns: PatternEntry,
        commit_sha: str
    ) -> Dict[str, Any]:
        """
        Notify dependency-orchestrator of pattern changes

        Args:
            repository: Repository name (owner/repo)
            patterns: Pattern analysis results
            commit_sha: Git commit SHA

        Returns:
            Notification result
        """
        orchestrator = self.registry.get_agent('dependency-orchestrator')
        if not orchestrator:
            return {"error": "dependency-orchestrator not configured"}

        # Call orchestrator's receive_change_notification skill
        result = orchestrator.execute_skill(
            skill_id="receive_change_notification",
            input_data={
                "repository": repository,
                "commit_sha": commit_sha,
                "timestamp": datetime.now().isoformat(),
                "patterns": patterns.patterns,
                "dependencies": patterns.dependencies,
                "keywords": patterns.keywords,
                "problem_domain": patterns.problem_domain
            }
        )

        return result

    def get_dependency_impact(
        self,
        repository: str,
        change_type: str = "pattern_change"
    ) -> Dict[str, Any]:
        """
        Get impact analysis from dependency-orchestrator

        Args:
            repository: Repository name
            change_type: Type of change (pattern_change, dependency_update, etc.)

        Returns:
            Impact analysis with affected repositories
        """
        orchestrator = self.registry.get_agent('dependency-orchestrator')
        if not orchestrator:
            return {"error": "dependency-orchestrator not configured", "affected_repos": []}

        result = orchestrator.execute_skill(
            skill_id="get_impact_analysis",
            input_data={
                "repository": repository,
                "change_type": change_type
            }
        )

        return result

    def get_repository_dependencies(self, repository: str) -> Dict[str, Any]:
        """
        Get dependency graph from orchestrator

        Args:
            repository: Repository name

        Returns:
            Dependency information (consumers, providers, etc.)
        """
        orchestrator = self.registry.get_agent('dependency-orchestrator')
        if not orchestrator:
            return {"error": "dependency-orchestrator not configured", "dependencies": []}

        result = orchestrator.execute_skill(
            skill_id="get_dependencies",
            input_data={"repository": repository}
        )

        return result

    # ==========================================
    # Pattern-Miner Integration
    # ==========================================

    def request_deep_pattern_analysis(
        self,
        repository: str,
        file_paths: Optional[List[str]] = None,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Request deep pattern analysis from pattern-miner

        Args:
            repository: Repository name
            file_paths: Specific files to analyze (optional)
            focus_areas: Areas to focus on (e.g., "error_handling", "api_design")

        Returns:
            Detailed pattern analysis
        """
        miner = self.registry.get_agent('pattern-miner')
        if not miner:
            return {"error": "pattern-miner not configured"}

        result = miner.execute_skill(
            skill_id="analyze_repository",
            input_data={
                "repository": repository,
                "file_paths": file_paths or [],
                "focus_areas": focus_areas or []
            }
        )

        return result

    def compare_implementations(
        self,
        repositories: List[str],
        pattern_type: str
    ) -> Dict[str, Any]:
        """
        Compare how different repositories implement a pattern

        Args:
            repositories: List of repository names
            pattern_type: Type of pattern (e.g., "retry_logic", "auth")

        Returns:
            Comparison analysis
        """
        miner = self.registry.get_agent('pattern-miner')
        if not miner:
            return {"error": "pattern-miner not configured"}

        result = miner.execute_skill(
            skill_id="compare_implementations",
            input_data={
                "repositories": repositories,
                "pattern_type": pattern_type
            }
        )

        return result

    def get_pattern_recommendations(
        self,
        repository: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get pattern recommendations from pattern-miner

        Args:
            repository: Repository name
            context: Context about current code (language, frameworks, etc.)

        Returns:
            Pattern recommendations
        """
        miner = self.registry.get_agent('pattern-miner')
        if not miner:
            return {"error": "pattern-miner not configured", "recommendations": []}

        result = miner.execute_skill(
            skill_id="get_recommendations",
            input_data={
                "repository": repository,
                "context": context
            }
        )

        return result

    # ==========================================
    # Cross-Agent Coordination
    # ==========================================

    def coordinate_pattern_update(
        self,
        repository: str,
        patterns: PatternEntry,
        commit_sha: str
    ) -> Dict[str, Any]:
        """
        Coordinate pattern update across all external agents

        This is called after dev-nexus updates its knowledge base
        to notify all relevant external agents.

        Args:
            repository: Repository name
            patterns: Updated patterns
            commit_sha: Git commit SHA

        Returns:
            Coordination results from all agents
        """
        results = {
            "repository": repository,
            "commit_sha": commit_sha,
            "timestamp": datetime.now().isoformat(),
            "notifications": {}
        }

        # Notify dependency-orchestrator
        orchestrator_result = self.notify_dependency_change(
            repository, patterns, commit_sha
        )
        results["notifications"]["dependency-orchestrator"] = orchestrator_result

        # Request impact analysis
        impact = self.get_dependency_impact(repository)
        results["impact_analysis"] = impact

        return results

    def health_check(self) -> Dict[str, Any]:
        """
        Check health of all external agents

        Returns:
            Health status for all registered agents
        """
        health_status = self.registry.health_check_all()

        return {
            "timestamp": datetime.now().isoformat(),
            "agents": health_status,
            "all_healthy": all(health_status.values())
        }

    # ==========================================
    # Component Consolidation Integration
    # ==========================================

    def query_consolidation_impact(
        self,
        component_name: str,
        from_repository: str,
        to_repository: str
    ) -> Dict[str, Any]:
        """
        Query consolidation impact from dependency-orchestrator

        Args:
            component_name: Name of component to consolidate
            from_repository: Source repository
            to_repository: Target repository

        Returns:
            Impact analysis with affected repositories, dependency chain, risk level
        """
        orchestrator = self.registry.get_agent('dependency-orchestrator')
        if not orchestrator:
            return {
                "error": "dependency-orchestrator not configured",
                "affected_repositories": [],
                "risk_level": "unknown"
            }

        try:
            result = orchestrator.execute_skill(
                skill_id="get_consolidation_impact",
                input_data={
                    "component_name": component_name,
                    "from_repository": from_repository,
                    "to_repository": to_repository,
                    "timestamp": datetime.now().isoformat()
                }
            )
            return result

        except Exception as e:
            return {
                "error": f"Impact analysis failed: {str(e)}",
                "affected_repositories": [],
                "risk_level": "unknown"
            }

    def trigger_component_analysis(
        self,
        repository: str,
        component_names: List[str],
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Trigger deep component analysis from pattern-miner

        Args:
            repository: Repository containing components
            component_names: Names of components to analyze
            focus_areas: Areas to focus on (e.g., "api_compatibility", "behavioral_differences")

        Returns:
            Deep analysis results including API compatibility, behavioral differences, feature gaps
        """
        miner = self.registry.get_agent('pattern-miner')
        if not miner:
            return {
                "error": "pattern-miner not configured",
                "api_compatibility": None,
                "behavioral_differences": []
            }

        try:
            result = miner.execute_skill(
                skill_id="analyze_component_consolidation",
                input_data={
                    "repository": repository,
                    "component_names": component_names,
                    "focus_areas": focus_areas or ["api_compatibility", "behavioral_differences"],
                    "timestamp": datetime.now().isoformat()
                }
            )
            return result

        except Exception as e:
            return {
                "error": f"Deep analysis failed: {str(e)}",
                "api_compatibility": None,
                "behavioral_differences": []
            }

    def notify_consolidation_plan(
        self,
        component_name: str,
        from_repository: str,
        to_repository: str,
        plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Notify dependency-orchestrator of consolidation plan

        Args:
            component_name: Name of component being consolidated
            from_repository: Source repository
            to_repository: Target repository
            plan: Consolidation plan with phases and estimates

        Returns:
            Acknowledgment from orchestrator
        """
        orchestrator = self.registry.get_agent('dependency-orchestrator')
        if not orchestrator:
            return {
                "error": "dependency-orchestrator not configured",
                "acknowledged": False
            }

        try:
            result = orchestrator.execute_skill(
                skill_id="notify_consolidation_plan",
                input_data={
                    "component_name": component_name,
                    "from_repository": from_repository,
                    "to_repository": to_repository,
                    "plan": plan,
                    "timestamp": datetime.now().isoformat()
                }
            )
            return result

        except Exception as e:
            return {
                "error": f"Notification failed: {str(e)}",
                "acknowledged": False
            }
