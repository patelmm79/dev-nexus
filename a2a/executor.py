"""
A2A Agent Executor

Handles A2A task execution and routes requests to appropriate skills.
"""

import json
from typing import Dict, Any
from datetime import datetime

from core.knowledge_base import KnowledgeBaseManager
from core.similarity_finder import SimilarityFinder
from schemas.knowledge_base_v2 import LessonLearned


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
        else:
            return {
                "error": f"Unknown skill: {skill_id}",
                "available_skills": ["query_patterns", "get_deployment_info", "add_lesson_learned"]
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
