"""
A2A Agent Executor

Handles A2A task execution and routes requests to appropriate skills.
"""

import json
from typing import Dict, Any
from datetime import datetime

from core.knowledge_base import KnowledgeBaseManager
from core.similarity_finder import SimilarityFinder
from core.integration_service import IntegrationService
from schemas.knowledge_base_v2 import LessonLearned, DependencyInfo


class PatternDiscoveryExecutor:
    """
    A2A AgentExecutor for Pattern Discovery Agent

    Routes incoming A2A requests to appropriate skill handlers.
    """

    def __init__(self, kb_manager: KnowledgeBaseManager, similarity_finder: SimilarityFinder):
        """
        Initialize executor

        Args:
            kb_manager: KnowledgeBaseManager instance
            similarity_finder: SimilarityFinder instance
        """
        self.kb_manager = kb_manager
        self.similarity_finder = similarity_finder
        self.integration_service = IntegrationService()

    async def execute(self, skill_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a skill based on skill_id

        Args:
            skill_id: Skill identifier
            input_data: Input parameters for the skill

        Returns:
            Dictionary with execution results
        """

        # Route to appropriate skill handler
        if skill_id == "query_patterns":
            return await self._handle_query_patterns(input_data)
        elif skill_id == "get_deployment_info":
            return await self._handle_get_deployment_info(input_data)
        elif skill_id == "add_lesson_learned":
            return await self._handle_add_lesson_learned(input_data)
        elif skill_id == "get_repository_list":
            return await self._handle_get_repository_list(input_data)
        elif skill_id == "get_cross_repo_patterns":
            return await self._handle_get_cross_repo_patterns(input_data)
        elif skill_id == "update_dependency_info":
            return await self._handle_update_dependency_info(input_data)
        elif skill_id == "health_check_external":
            return await self._handle_health_check_external(input_data)
        else:
            return {
                "error": f"Unknown skill: {skill_id}",
                "available_skills": [
                    "query_patterns", "get_deployment_info", "add_lesson_learned",
                    "get_repository_list", "get_cross_repo_patterns",
                    "update_dependency_info", "health_check_external"
                ]
            }

    async def _handle_query_patterns(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query similar patterns across repositories (PUBLIC)

        Input:
            - keywords: List[str] - Keywords to search for
            - patterns: List[str] - Pattern names to match (optional)
            - min_similarity: float - Minimum similarity score (optional)

        Output:
            - matches: List of matching repositories with similarity scores
            - total_matches: Total number of matches found
        """
        try:
            keywords = input_data.get('keywords', [])
            patterns = input_data.get('patterns', [])
            min_matches = input_data.get('min_matches', 1)

            # Load knowledge base
            kb = self.kb_manager.load_knowledge_base()

            # Search by keywords if provided
            if keywords:
                matches = self.similarity_finder.find_by_keywords(
                    keywords=keywords,
                    kb=kb,
                    min_matches=min_matches,
                    top_k=10
                )
            # Search by patterns if provided
            elif patterns:
                matches = self.similarity_finder.find_by_patterns(
                    patterns=patterns,
                    kb=kb,
                    min_matches=min_matches,
                    top_k=10
                )
            else:
                return {
                    "error": "Must provide either 'keywords' or 'patterns' to search",
                    "matches": [],
                    "total_matches": 0
                }

            return {
                "matches": matches,
                "total_matches": len(matches),
                "search_criteria": {
                    "keywords": keywords,
                    "patterns": patterns,
                    "min_matches": min_matches
                }
            }

        except Exception as e:
            return {
                "error": f"Failed to query patterns: {str(e)}",
                "matches": [],
                "total_matches": 0
            }

    async def _handle_get_deployment_info(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get deployment information for a repository (PUBLIC)

        Input:
            - repository: str - Repository name (format: "owner/repo")
            - include_lessons: bool - Include lessons learned (default: True)
            - include_history: bool - Include pattern history (default: False)

        Output:
            - repository: str - Repository name
            - deployment: Deployment information
            - lessons_learned: List of lessons (if requested)
            - patterns: Latest patterns
        """
        try:
            repository = input_data.get('repository')
            include_lessons = input_data.get('include_lessons', True)
            include_history = input_data.get('include_history', False)

            if not repository:
                return {"error": "Missing required parameter: 'repository'"}

            # Get repository info
            repo_info = self.kb_manager.get_repository_info(repository)

            if not repo_info:
                return {
                    "error": f"Repository '{repository}' not found in knowledge base",
                    "available_repositories": list(self.kb_manager.load_knowledge_base().repositories.keys())
                }

            # Build response
            response = {
                "repository": repository,
                "deployment": repo_info.deployment.model_dump(mode='json'),
                "dependencies": repo_info.dependencies.model_dump(mode='json'),
                "testing": repo_info.testing.model_dump(mode='json'),
                "security": repo_info.security.model_dump(mode='json'),
                "latest_patterns": {
                    "patterns": repo_info.latest_patterns.patterns,
                    "problem_domain": repo_info.latest_patterns.problem_domain,
                    "keywords": repo_info.latest_patterns.keywords,
                    "analyzed_at": repo_info.latest_patterns.analyzed_at.isoformat()
                }
            }

            # Add lessons if requested
            if include_lessons:
                response["lessons_learned"] = [
                    lesson.model_dump(mode='json')
                    for lesson in repo_info.deployment.lessons_learned
                ]

            # Add history if requested
            if include_history:
                response["history"] = [
                    {
                        "commit_sha": entry.commit_sha,
                        "analyzed_at": entry.analyzed_at.isoformat(),
                        "patterns": entry.patterns,
                        "problem_domain": entry.problem_domain
                    }
                    for entry in repo_info.history[-10:]  # Last 10 entries
                ]

            return response

        except Exception as e:
            return {"error": f"Failed to get deployment info: {str(e)}"}

    async def _handle_add_lesson_learned(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manually record a lesson learned (AUTHENTICATED)

        Input:
            - repository: str - Repository name (format: "owner/repo")
            - category: str - Lesson category (performance, security, reliability, cost, observability)
            - lesson: str - The lesson learned (clear, actionable statement)
            - context: str - Context or background for this lesson
            - severity: str - Severity level (info, warning, critical) [default: info]
            - recorded_by: str - Who recorded this lesson (optional)

        Output:
            - success: bool
            - message: str
            - lesson_id: str (timestamp)
            - kb_url: str
        """
        try:
            # Validate required fields
            repository = input_data.get('repository')
            category = input_data.get('category')
            lesson_text = input_data.get('lesson')
            context = input_data.get('context')

            if not all([repository, category, lesson_text, context]):
                return {
                    "success": False,
                    "error": "Missing required fields: repository, category, lesson, context"
                }

            # Validate category
            valid_categories = ["performance", "security", "reliability", "cost", "observability"]
            if category not in valid_categories:
                return {
                    "success": False,
                    "error": f"Invalid category. Must be one of: {', '.join(valid_categories)}"
                }

            # Validate severity
            severity = input_data.get('severity', 'info')
            valid_severities = ["info", "warning", "critical"]
            if severity not in valid_severities:
                return {
                    "success": False,
                    "error": f"Invalid severity. Must be one of: {', '.join(valid_severities)}"
                }

            # Create lesson learned object
            lesson = LessonLearned(
                timestamp=datetime.now(),
                category=category,
                lesson=lesson_text,
                context=context,
                severity=severity,
                recorded_by=input_data.get('recorded_by'),
                related_files=input_data.get('related_files', []),
                tags=input_data.get('tags', [])
            )

            # Add to knowledge base
            success = self.kb_manager.add_lesson_learned(repository, lesson)

            if success:
                return {
                    "success": True,
                    "message": f"Lesson learned recorded for {repository}",
                    "lesson_id": lesson.timestamp.isoformat(),
                    "repository": repository,
                    "category": category,
                    "severity": severity,
                    "kb_url": f"https://github.com/{self.kb_manager.kb_repo_name}/blob/main/knowledge_base.json"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to add lesson to knowledge base"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to add lesson learned: {str(e)}"
            }

    async def _handle_get_repository_list(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get list of all tracked repositories (PUBLIC)

        Input:
            - include_metadata: bool - Include pattern counts and last updated (default: True)

        Output:
            - repositories: List of repository names with optional metadata
            - total_count: Total number of repositories
        """
        try:
            include_metadata = input_data.get('include_metadata', True)

            kb = self.kb_manager.load_knowledge_base()

            if include_metadata:
                repositories = [
                    {
                        "name": repo_name,
                        "pattern_count": len(repo_info.latest_patterns.patterns),
                        "last_updated": repo_info.latest_patterns.analyzed_at.isoformat(),
                        "problem_domain": repo_info.latest_patterns.problem_domain,
                        "keywords": repo_info.latest_patterns.keywords[:5]  # Top 5 keywords
                    }
                    for repo_name, repo_info in kb.repositories.items()
                ]
            else:
                repositories = list(kb.repositories.keys())

            return {
                "repositories": repositories,
                "total_count": len(repositories),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "error": f"Failed to get repository list: {str(e)}",
                "repositories": [],
                "total_count": 0
            }

    async def _handle_get_cross_repo_patterns(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find patterns that exist across multiple repositories (PUBLIC)

        Input:
            - min_repos: int - Minimum number of repos a pattern must appear in (default: 2)
            - pattern_type: str - Filter by pattern type (optional)

        Output:
            - cross_repo_patterns: List of patterns with repos that use them
            - total_patterns: Number of cross-repo patterns found
        """
        try:
            min_repos = input_data.get('min_repos', 2)
            pattern_type = input_data.get('pattern_type')

            kb = self.kb_manager.load_knowledge_base()

            # Aggregate patterns across all repos
            pattern_to_repos = {}

            for repo_name, repo_info in kb.repositories.items():
                for pattern in repo_info.latest_patterns.patterns:
                    if pattern_type and pattern_type.lower() not in pattern.lower():
                        continue

                    if pattern not in pattern_to_repos:
                        pattern_to_repos[pattern] = []
                    pattern_to_repos[pattern].append(repo_name)

            # Filter to patterns appearing in min_repos or more
            cross_repo_patterns = [
                {
                    "pattern": pattern,
                    "repositories": repos,
                    "repo_count": len(repos)
                }
                for pattern, repos in pattern_to_repos.items()
                if len(repos) >= min_repos
            ]

            # Sort by repo count (most common first)
            cross_repo_patterns.sort(key=lambda x: x['repo_count'], reverse=True)

            return {
                "cross_repo_patterns": cross_repo_patterns,
                "total_patterns": len(cross_repo_patterns),
                "min_repos": min_repos,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "error": f"Failed to get cross-repo patterns: {str(e)}",
                "cross_repo_patterns": [],
                "total_patterns": 0
            }

    async def _handle_update_dependency_info(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update dependency information for a repository (AUTHENTICATED)

        Input:
            - repository: str - Repository name (format: "owner/repo")
            - dependency_info: dict - Dependency information to update
                - consumers: List[dict] - Repos that depend on this one
                - derivatives: List[dict] - Forks/derivatives
                - external_dependencies: List[str] - External dependencies

        Output:
            - success: bool
            - message: str
            - repository: str
        """
        try:
            repository = input_data.get('repository')
            dependency_info = input_data.get('dependency_info', {})

            if not repository:
                return {
                    "success": False,
                    "error": "Missing required parameter: 'repository'"
                }

            # Create DependencyInfo object
            dep_info = DependencyInfo(
                consumers=dependency_info.get('consumers', []),
                derivatives=dependency_info.get('derivatives', []),
                external_dependencies=dependency_info.get('external_dependencies', [])
            )

            # Update in knowledge base
            success = self.kb_manager.update_dependency_info(repository, dep_info)

            if success:
                return {
                    "success": True,
                    "message": f"Dependency info updated for {repository}",
                    "repository": repository,
                    "kb_url": f"https://github.com/{self.kb_manager.kb_repo_name}/blob/main/knowledge_base.json"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to update dependency info in knowledge base"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to update dependency info: {str(e)}"
            }

    async def _handle_health_check_external(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check health status of external A2A agents (PUBLIC)

        Input:
            - None

        Output:
            - agents: dict - Health status for each external agent
            - all_healthy: bool - Whether all agents are healthy
            - timestamp: str
        """
        try:
            health_status = self.integration_service.health_check()
            return health_status

        except Exception as e:
            return {
                "error": f"Failed to check external agent health: {str(e)}",
                "agents": {},
                "all_healthy": False
            }

    async def cancel(self, task_id: str) -> Dict[str, Any]:
        """
        Handle task cancellation

        Args:
            task_id: Task identifier

        Returns:
            Cancellation status
        """
        return {
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task cancelled successfully"
        }
