"""
Skill Registry

Manages skill discovery, registration, and routing for the A2A server.
Skills are automatically discovered and registered when imported.
"""

from typing import Dict, List, Any, Optional
from a2a.skills.base import BaseSkill


class SkillRegistry:
    """
    Central registry for all A2A skills

    Skills register themselves on instantiation and can be
    queried by ID or retrieved as a group for AgentCard generation.
    """

    def __init__(self):
        """Initialize empty registry"""
        self._skills: Dict[str, BaseSkill] = {}
        self._protected_skills: List[str] = []

    def register(self, skill: BaseSkill) -> None:
        """
        Register a skill

        Args:
            skill: BaseSkill instance to register

        Raises:
            ValueError: If skill_id already registered
        """
        if skill.skill_id in self._skills:
            raise ValueError(f"Skill '{skill.skill_id}' is already registered")

        self._skills[skill.skill_id] = skill

        # Track protected skills
        if skill.requires_authentication:
            self._protected_skills.append(skill.skill_id)

    def get_skill(self, skill_id: str) -> Optional[BaseSkill]:
        """
        Get a skill by ID

        Args:
            skill_id: Skill identifier

        Returns:
            BaseSkill instance or None if not found
        """
        return self._skills.get(skill_id)

    def get_all_skills(self) -> List[BaseSkill]:
        """
        Get all registered skills

        Returns:
            List of all BaseSkill instances
        """
        return list(self._skills.values())

    def get_skill_ids(self) -> List[str]:
        """
        Get all registered skill IDs

        Returns:
            List of skill IDs
        """
        return list(self._skills.keys())

    def is_protected(self, skill_id: str) -> bool:
        """
        Check if a skill requires authentication

        Args:
            skill_id: Skill identifier

        Returns:
            True if skill requires authentication
        """
        return skill_id in self._protected_skills

    def to_agent_card_skills(self) -> List[Dict[str, Any]]:
        """
        Convert all skills to AgentCard format

        Returns:
            List of skill entries for AgentCard
        """
        return [skill.to_agent_card_entry() for skill in self._skills.values()]

    async def execute_skill(self, skill_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a skill by ID

        Args:
            skill_id: Skill identifier
            input_data: Input parameters

        Returns:
            Skill execution result or error dict
        """
        skill = self.get_skill(skill_id)

        if not skill:
            return {
                "error": f"Unknown skill: {skill_id}",
                "available_skills": self.get_skill_ids()
            }

        # Validate input
        validation_error = skill.validate_input(input_data)
        if validation_error:
            return {
                "success": False,
                "error": validation_error,
                "skill_id": skill_id
            }

        # Execute skill
        try:
            result = await skill.execute(input_data)
            return result
        except Exception as e:
            # Skills should not raise exceptions, but catch just in case
            return {
                "success": False,
                "error": f"Skill execution failed: {str(e)}",
                "skill_id": skill_id
            }

    def __len__(self) -> int:
        """Return number of registered skills"""
        return len(self._skills)

    def __contains__(self, skill_id: str) -> bool:
        """Check if skill is registered"""
        return skill_id in self._skills


# Global registry instance
_global_registry = SkillRegistry()


def get_registry() -> SkillRegistry:
    """
    Get the global skill registry

    Returns:
        Global SkillRegistry instance
    """
    return _global_registry


def register_skill(skill: BaseSkill) -> None:
    """
    Register a skill with the global registry

    Args:
        skill: BaseSkill instance to register
    """
    _global_registry.register(skill)
