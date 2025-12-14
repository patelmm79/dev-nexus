"""
Base Skill Interface

Defines the standard interface for all A2A skills in the Pattern Discovery Agent.
Each skill is a self-contained module with metadata and execution logic.
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


class BaseSkill(ABC):
    """
    Base class for all A2A skills

    Subclasses must implement:
    - skill_id: Unique identifier
    - skill_name: Human-readable name
    - skill_description: What the skill does
    - input_schema: JSON schema for inputs
    - execute(): Async method that performs the skill

    Optional:
    - tags: List of tags for categorization
    - requires_authentication: Whether skill requires auth
    - examples: Example inputs with descriptions
    """

    @property
    @abstractmethod
    def skill_id(self) -> str:
        """Unique skill identifier (e.g., 'query_patterns')"""
        pass

    @property
    @abstractmethod
    def skill_name(self) -> str:
        """Human-readable skill name (e.g., 'Query Similar Patterns')"""
        pass

    @property
    @abstractmethod
    def skill_description(self) -> str:
        """Description of what the skill does"""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """JSON schema defining expected inputs"""
        pass

    @property
    def tags(self) -> List[str]:
        """Tags for categorizing the skill (default: empty list)"""
        return []

    @property
    def requires_authentication(self) -> bool:
        """Whether this skill requires authentication (default: False)"""
        return False

    @property
    def examples(self) -> List[Dict[str, Any]]:
        """Example inputs and descriptions (default: empty list)"""
        return []

    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the skill with given input

        Args:
            input_data: Dictionary of input parameters

        Returns:
            Dictionary with execution results. Should include:
            - success: bool (whether execution succeeded)
            - error: str (if success is False)
            - Additional skill-specific fields

        Raises:
            Should NOT raise exceptions - catch and return error dict instead
        """
        pass

    def to_agent_card_entry(self) -> Dict[str, Any]:
        """
        Convert skill to AgentCard entry format

        Returns:
            Dictionary in AgentCard skill format
        """
        return {
            "id": self.skill_id,
            "name": self.skill_name,
            "description": self.skill_description,
            "tags": self.tags,
            "requires_authentication": self.requires_authentication,
            "input_schema": self.input_schema,
            "examples": self.examples
        }

    def validate_input(self, input_data: Dict[str, Any]) -> Optional[str]:
        """
        Validate input against schema

        Args:
            input_data: Input to validate

        Returns:
            None if valid, error message string if invalid
        """
        # Check required fields
        required = self.input_schema.get("required", [])
        for field in required:
            if field not in input_data:
                return f"Missing required parameter: '{field}'"

        return None


class SkillGroup(ABC):
    """
    Base class for a group of related skills

    Use this when multiple skills share dependencies or logic.
    Example: PatternQuerySkills might include both query_patterns
    and get_cross_repo_patterns.
    """

    def __init__(self, postgres_repo=None, similarity_finder=None, integration_service=None):
        """
        Initialize skill group with shared dependencies

        Args:
            postgres_repo: PostgreSQL repository (optional)
            similarity_finder: Similarity finder service (optional)
            integration_service: Integration service (optional)
        """
        self.postgres_repo = postgres_repo
        self.similarity_finder = similarity_finder
        self.integration_service = integration_service

    @abstractmethod
    def get_skills(self) -> List[BaseSkill]:
        """
        Get all skills in this group

        Returns:
            List of BaseSkill instances
        """
        pass
