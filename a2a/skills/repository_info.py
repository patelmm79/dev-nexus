"""
Repository Information Skills

Skills for retrieving repository information and metadata:
- get_repository_list: Get list of all tracked repositories
- get_deployment_info: Get deployment and infrastructure information
"""

from typing import Dict, Any, List
from datetime import datetime

from a2a.skills.base import BaseSkill, SkillGroup


class GetRepositoryListSkill(BaseSkill):
    """Get list of all tracked repositories with optional metadata"""

    def __init__(self, postgres_repo):
        self.postgres_repo = postgres_repo

    @property
    def skill_id(self) -> str:
        return "get_repository_list"

    @property
    def skill_name(self) -> str:
        return "Get Repository List"

    @property
    def skill_description(self) -> str:
        return "Get list of all tracked repositories with optional metadata"

    @property
    def tags(self) -> List[str]:
        return ["repositories", "list", "metadata"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "include_metadata": {
                    "type": "boolean",
                    "description": "Include pattern counts and last updated timestamps",
                    "default": True
                }
            }
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {"include_metadata": True},
                "description": "Get all repositories with metadata"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get list of all tracked repositories

        Input:
            - include_metadata: bool - Include pattern counts and last updated (default: True)

        Output:
            - repositories: List of repository names with optional metadata
            - total_count: Total number of repositories
        """
        try:
            include_metadata = input_data.get('include_metadata', True)

            kb = await self.postgres_repo.load_knowledge_base()

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
                "success": True,
                "repositories": repositories,
                "total_count": len(repositories),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get repository list: {str(e)}",
                "repositories": [],
                "total_count": 0
            }


class GetDeploymentInfoSkill(BaseSkill):
    """Get deployment information for a specific repository"""

    def __init__(self, postgres_repo):
        self.postgres_repo = postgres_repo

    @property
    def skill_id(self) -> str:
        return "get_deployment_info"

    @property
    def skill_name(self) -> str:
        return "Get Deployment Information"

    @property
    def skill_description(self) -> str:
        return "Retrieve deployment scripts, infrastructure details, and lessons learned for a specific repository"

    @property
    def tags(self) -> List[str]:
        return ["deployment", "infrastructure", "devops"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository name in format 'owner/repo'"
                },
                "include_lessons": {
                    "type": "boolean",
                    "description": "Include lessons learned",
                    "default": True
                },
                "include_history": {
                    "type": "boolean",
                    "description": "Include pattern history",
                    "default": False
                }
            },
            "required": ["repository"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {"repository": "patelmm79/my-api", "include_lessons": True},
                "description": "Get deployment info and lessons for my-api repository"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get deployment information for a repository

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
                return {
                    "success": False,
                    "error": "Missing required parameter: 'repository'"
                }

            # Get repository info
            repo_info = await self.postgres_repo.get_repository_info(repository)

            if not repo_info:
                kb = await self.postgres_repo.load_knowledge_base()
                return {
                    "success": False,
                    "error": f"Repository '{repository}' not found in knowledge base",
                    "available_repositories": list(kb.repositories.keys())
                }

            # Build response
            response = {
                "success": True,
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
            return {
                "success": False,
                "error": f"Failed to get deployment info: {str(e)}"
            }


class AddRepositorySkill(BaseSkill):
    """Add a new repository to the tracked repositories"""

    def __init__(self, postgres_repo):
        self.postgres_repo = postgres_repo

    @property
    def skill_id(self) -> str:
        return "add_repository"

    @property
    def skill_name(self) -> str:
        return "Add Repository"

    @property
    def skill_description(self) -> str:
        return "Add a new repository to the tracked repositories list"

    @property
    def tags(self) -> List[str]:
        return ["repositories", "management", "add"]

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
                    "description": "Repository name in format 'owner/repo' (e.g., 'patelmm79/dev-nexus')"
                },
                "problem_domain": {
                    "type": "string",
                    "description": "Problem domain or project description (optional)"
                }
            },
            "required": ["repository"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {"repository": "patelmm79/my-api", "problem_domain": "REST API service"},
                "description": "Add a new repository to track"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new repository to tracked repositories

        Input:
            - repository: str - Repository name (format: "owner/repo")
            - problem_domain: str - Problem domain/description (optional)

        Output:
            - success: bool - Whether the repository was added
            - repository: str - Repository name
            - message: str - Status message
        """
        try:
            repository = input_data.get('repository')
            problem_domain = input_data.get('problem_domain', '')

            if not repository:
                return {
                    "success": False,
                    "error": "Missing required parameter: 'repository'"
                }

            if '/' not in repository:
                return {
                    "success": False,
                    "error": "Invalid repository format. Use 'owner/repo'"
                }

            # Add repository to database
            repo_id = await self.postgres_repo.add_repository(
                name=repository,
                problem_domain=problem_domain
            )

            return {
                "success": True,
                "repository": repository,
                "repository_id": repo_id,
                "message": f"Repository '{repository}' added successfully",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to add repository: {str(e)}"
            }


class RepositoryInfoSkills(SkillGroup):
    """Group of repository information skills"""

    def __init__(self, postgres_repo):
        super().__init__(postgres_repo=postgres_repo)
        self._skills = [
            GetRepositoryListSkill(postgres_repo),
            GetDeploymentInfoSkill(postgres_repo),
            AddRepositorySkill(postgres_repo)
        ]

    def get_skills(self) -> List[BaseSkill]:
        return self._skills
