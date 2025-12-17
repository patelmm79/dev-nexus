"""
Integration Skills

Skills for coordinating with external A2A agents:
- health_check_external: Check health status of external agents
"""

from typing import Dict, Any, List

from a2a.skills.base import BaseSkill, SkillGroup


class HealthCheckExternalSkill(BaseSkill):
    """Check health status of external A2A agents"""

    def __init__(self, integration_service):
        self.integration_service = integration_service

    @property
    def skill_id(self) -> str:
        return "health_check_external"

    @property
    def skill_name(self) -> str:
        return "Check External Agent Health"

    @property
    def skill_description(self) -> str:
        return "Check health status of external A2A agents (dependency-orchestrator, pattern-miner)"

    @property
    def tags(self) -> List[str]:
        return ["health", "monitoring", "agents"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {}
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {},
                "description": "Check health of all external agents"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check health status of external A2A agents

        Input:
            - None

        Output:
            - agents: dict - Health status for each external agent
            - all_healthy: bool - Whether all agents are healthy
            - timestamp: str
        """
        try:
            health_status = self.integration_service.health_check()
            return {
                "success": True,
                **health_status
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to check external agent health: {str(e)}",
                "agents": {},
                "all_healthy": False
            }


class IntegrationSkills(SkillGroup):
    """Group of integration and coordination skills"""

    def __init__(self, integration_service):
        super().__init__(integration_service=integration_service)
        self._skills = [
            HealthCheckExternalSkill(integration_service)
        ]

    def get_skills(self) -> List[BaseSkill]:
        return self._skills


# In dev-nexus: a2a/skills/integration.py
# Add new skills that call pattern-miner

class TriggerDeepAnalysisSkill(BaseSkill):
    """Trigger deep pattern analysis via pattern-miner"""

    def __init__(self, integration_service):
        self.integration_service = integration_service

    @property
    def skill_id(self) -> str:
        return "trigger_deep_analysis"

    @property
    def skill_name(self) -> str:
        return "Trigger Deep Pattern Analysis"

    @property
    def skill_description(self) -> str:
        return "Trigger deep pattern analysis on a repository using pattern-miner agent"

    @property
    def tags(self) -> List[str]:
        return ["analysis", "pattern-miner", "deep-dive"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository name in format 'owner/repo'"
                },
                "focus_areas": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Areas to focus analysis on"
                }
            },
            "required": ["repository"]
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger pattern-miner analysis"""
        try:
            result = self.integration_service.request_deep_pattern_analysis(
                repository=input_data["repository"],
                focus_areas=input_data.get("focus_areas", [])
            )

            return {
                "success": True,
                **result
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to trigger analysis: {str(e)}"
            }