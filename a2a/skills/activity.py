"""
Activity Timeline Skills

Skills for tracking and displaying activity across the knowledge base:
- get_recent_actions: Get unified feed of all actions across repositories
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from a2a.skills.base import BaseSkill, SkillGroup

logger = logging.getLogger(__name__)


class GetRecentActionsSkill(BaseSkill):
    """Get unified activity feed across all repositories"""

    def __init__(self, postgres_repo):
        self.postgres_repo = postgres_repo

    @property
    def skill_id(self) -> str:
        return "get_recent_actions"

    @property
    def skill_name(self) -> str:
        return "Get Recent Actions"

    @property
    def skill_description(self) -> str:
        return "Get unified chronological feed of recent actions including pattern analysis, lessons learned, deployments, and runtime issues across all repositories."

    @property
    def tags(self) -> List[str]:
        return ["activity", "timeline", "feed", "history"]

    @property
    def requires_authentication(self) -> bool:
        return False  # Public skill

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of actions to return",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100
                },
                "offset": {
                    "type": "integer",
                    "description": "Number of actions to skip (for pagination)",
                    "default": 0,
                    "minimum": 0
                },
                "action_types": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["analysis", "lesson", "deployment", "runtime_issue"]
                    },
                    "description": "Filter by specific action types (default: all types)"
                },
                "repository": {
                    "type": "string",
                    "description": "Filter by repository name (format: 'owner/repo')"
                }
            }
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "limit": 10,
                    "offset": 0
                },
                "description": "Get first 10 recent actions across all repositories"
            },
            {
                "input": {
                    "limit": 20,
                    "action_types": ["runtime_issue", "analysis"],
                    "repository": "patelmm79/dev-nexus"
                },
                "description": "Get runtime issues and analyses for specific repository"
            },
            {
                "input": {
                    "limit": 10,
                    "offset": 10,
                    "action_types": ["lesson", "deployment"]
                },
                "description": "Get lessons and deployments, paginated (page 2)"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get recent actions from unified feed

        Returns:
            success: bool
            count: Total count matching filters
            returned: Number of actions in this response
            actions: List of action objects with type discriminator
            pagination: Pagination metadata
        """
        try:
            limit = input_data.get('limit', 20)
            offset = input_data.get('offset', 0)
            action_types = input_data.get('action_types')
            repository = input_data.get('repository')

            # Validate limit bounds
            if limit < 1 or limit > 100:
                return {
                    "success": False,
                    "error": "Limit must be between 1 and 100"
                }

            # Get actions from repository
            result = await self.postgres_repo.get_recent_actions(
                limit=limit,
                offset=offset,
                action_types=action_types,
                repository_filter=repository
            )

            # Check for errors
            if "error" in result:
                return {
                    "success": False,
                    "error": result["error"],
                    "count": 0,
                    "returned": 0,
                    "actions": []
                }

            # Calculate pagination metadata
            total_count = result["total_count"]
            returned = result["returned"]
            has_more = (offset + returned) < total_count
            next_offset = offset + returned if has_more else None

            return {
                "success": True,
                "count": total_count,
                "returned": returned,
                "actions": result["actions"],
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": has_more,
                    "next_offset": next_offset,
                    "total_pages": (total_count + limit - 1) // limit  # Ceiling division
                },
                "filters": {
                    "action_types": action_types,
                    "repository": repository
                },
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            import traceback
            logger.error(f"GetRecentActionsSkill execute failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc(),
                "count": 0,
                "returned": 0,
                "actions": []
            }


class ActivitySkills(SkillGroup):
    """Group of activity timeline skills"""

    def __init__(self, postgres_repo):
        super().__init__(postgres_repo=postgres_repo)
        self._skills = [
            GetRecentActionsSkill(postgres_repo)
        ]

    def get_skills(self) -> List[BaseSkill]:
        return self._skills
