"""
A2A Agent Executor (Modular)

Thin coordinator that delegates skill execution to the skill registry.
Skills are defined in separate modules in a2a/skills/
"""

from typing import Dict, Any

from a2a.registry import SkillRegistry


class PatternDiscoveryExecutor:
    """
    A2A AgentExecutor for Pattern Discovery Agent

    This is a thin coordinator that delegates all skill execution
    to the SkillRegistry. Skills are self-contained modules that
    register themselves.

    Design Pattern: Coordinator Pattern
    - Executor coordinates (routes requests)
    - Skills operate (execute business logic)
    - Registry manages (discovers and invokes skills)
    """

    def __init__(self, registry: SkillRegistry):
        """
        Initialize executor with skill registry

        Args:
            registry: SkillRegistry instance with registered skills
        """
        self.registry = registry

    async def execute(self, skill_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a skill based on skill_id

        Args:
            skill_id: Skill identifier
            input_data: Input parameters for the skill

        Returns:
            Dictionary with execution results
        """
        # Delegate to registry
        return await self.registry.execute_skill(skill_id, input_data)

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

    def get_available_skills(self) -> list:
        """
        Get list of available skill IDs

        Returns:
            List of skill IDs
        """
        return self.registry.get_skill_ids()
