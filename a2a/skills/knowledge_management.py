"""
Knowledge Management Skills

Skills for updating and managing the knowledge base:
- add_lesson_learned: Record lessons learned for a repository
- update_dependency_info: Update dependency graph information

Both skills require authentication as they modify the knowledge base.
"""

from typing import Dict, Any, List
from datetime import datetime

from a2a.skills.base import BaseSkill, SkillGroup
from schemas.knowledge_base_v2 import LessonLearned, DependencyInfo


class AddLessonLearnedSkill(BaseSkill):
    """Manually record a lesson learned or deployment insight"""

    def __init__(self, kb_manager):
        self.kb_manager = kb_manager

    @property
    def skill_id(self) -> str:
        return "add_lesson_learned"

    @property
    def skill_name(self) -> str:
        return "Add Lesson Learned"

    @property
    def skill_description(self) -> str:
        return "Manually record a lesson learned or deployment insight for a repository"

    @property
    def tags(self) -> List[str]:
        return ["knowledge", "documentation", "lessons"]

    @property
    def requires_authentication(self) -> bool:
        return True

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository name in format 'owner/repo'"
                },
                "category": {
                    "type": "string",
                    "enum": ["performance", "security", "reliability", "cost", "observability"],
                    "description": "Lesson category"
                },
                "lesson": {
                    "type": "string",
                    "description": "The lesson learned (clear, actionable statement)"
                },
                "context": {
                    "type": "string",
                    "description": "Context or background for this lesson"
                },
                "severity": {
                    "type": "string",
                    "enum": ["info", "warning", "critical"],
                    "default": "info"
                },
                "recorded_by": {
                    "type": "string",
                    "description": "Who recorded this lesson (optional)"
                }
            },
            "required": ["repository", "category", "lesson", "context"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "repository": "patelmm79/api-client",
                    "category": "performance",
                    "lesson": "Always use connection pooling for HTTP clients",
                    "context": "Experienced socket exhaustion under high load",
                    "severity": "warning"
                },
                "description": "Record a performance lesson learned"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manually record a lesson learned

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


class UpdateDependencyInfoSkill(BaseSkill):
    """Update dependency graph for a repository"""

    def __init__(self, kb_manager):
        self.kb_manager = kb_manager

    @property
    def skill_id(self) -> str:
        return "update_dependency_info"

    @property
    def skill_name(self) -> str:
        return "Update Dependency Information"

    @property
    def skill_description(self) -> str:
        return "Update dependency graph for a repository - consumers, derivatives, and external dependencies"

    @property
    def tags(self) -> List[str]:
        return ["dependencies", "graph", "orchestration"]

    @property
    def requires_authentication(self) -> bool:
        return True

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository name in format 'owner/repo'"
                },
                "dependency_info": {
                    "type": "object",
                    "description": "Dependency information",
                    "properties": {
                        "consumers": {
                            "type": "array",
                            "description": "List of repositories that depend on this one"
                        },
                        "derivatives": {
                            "type": "array",
                            "description": "List of forks or derivatives"
                        },
                        "external_dependencies": {
                            "type": "array",
                            "description": "List of external dependencies"
                        }
                    }
                }
            },
            "required": ["repository", "dependency_info"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "repository": "patelmm79/shared-lib",
                    "dependency_info": {
                        "consumers": [{"repository": "patelmm79/api-service", "relationship": "imports"}],
                        "external_dependencies": ["requests", "pydantic"]
                    }
                },
                "description": "Update dependency information for shared library"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update dependency information for a repository

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


class KnowledgeManagementSkills(SkillGroup):
    """Group of knowledge management skills"""

    def __init__(self, kb_manager):
        super().__init__(kb_manager=kb_manager)
        self._skills = [
            AddLessonLearnedSkill(kb_manager),
            UpdateDependencyInfoSkill(kb_manager)
        ]

    def get_skills(self) -> List[BaseSkill]:
        return self._skills
