"""
A2A Client Module

Client for calling external A2A agents (dependency-orchestrator, pattern-miner, etc.)
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime
import logging


class A2AClient:
    """
    Client for calling external A2A agents

    Handles authentication, request formatting, and error handling
    for A2A protocol communication.
    """

    def __init__(self, agent_url: str, auth_token: Optional[str] = None):
        """
        Initialize A2A client

        Args:
            agent_url: Base URL of the A2A agent
            auth_token: Optional authentication token
        """
        self.agent_url = agent_url.rstrip('/')
        self.auth_token = auth_token
        self.timeout = 30  # seconds

    def get_agent_card(self) -> Optional[Dict[str, Any]]:
        """
        Fetch AgentCard from remote agent

        Returns:
            AgentCard dictionary or None if failed
        """
        try:
            url = f"{self.agent_url}/.well-known/agent.json"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to fetch AgentCard from {self.agent_url}: {e}")
            return None

    def execute_skill(
        self,
        skill_id: str,
        input_data: Dict[str, Any],
        require_auth: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a skill on the remote agent

        Args:
            skill_id: Skill identifier
            input_data: Input parameters for the skill
            require_auth: Whether to include auth token

        Returns:
            Skill execution result
        """
        try:
            url = f"{self.agent_url}/a2a/execute"

            payload = {
                "skill_id": skill_id,
                "input": input_data
            }

            headers = {"Content-Type": "application/json"}

            if require_auth and self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"

            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            return {
                "error": f"Request to {skill_id} timed out after {self.timeout}s",
                "skill_id": skill_id
            }
        except requests.exceptions.RequestException as e:
            return {
                "error": f"Failed to execute {skill_id}: {str(e)}",
                "skill_id": skill_id
            }
        except Exception as e:
            return {
                "error": f"Unexpected error calling {skill_id}: {str(e)}",
                "skill_id": skill_id
            }

    def health_check(self) -> bool:
        """
        Check if remote agent is healthy

        Returns:
            True if healthy, False otherwise
        """
        try:
            url = f"{self.agent_url}/health"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False


class ExternalAgentRegistry:
    """
    Registry for managing connections to external A2A agents
    """

    def __init__(self):
        """Initialize registry from environment variables"""
        self.agents = {}

        # Logger for external agent discovery and health checks
        self._logger = logging.getLogger("a2a.external_agent_registry")

        # Register dependency-orchestrator
        orchestrator_url = os.environ.get('ORCHESTRATOR_URL')
        if orchestrator_url:
            self.agents['dependency-orchestrator'] = A2AClient(
                agent_url=orchestrator_url,
                auth_token=os.environ.get('ORCHESTRATOR_TOKEN')
            )

        # Register pattern-miner
        pattern_miner_url = os.environ.get('PATTERN_MINER_URL')
        if pattern_miner_url:
            self.agents['pattern-miner'] = A2AClient(
                agent_url=pattern_miner_url,
                auth_token=os.environ.get('PATTERN_MINER_TOKEN')
            )

        # Log discovered agents for debugging
        if self.agents:
            for name, client in self.agents.items():
                try:
                    self._logger.info(
                        "Registered external agent '%s' -> %s (auth=%s)",
                        name,
                        getattr(client, 'agent_url', 'unknown'),
                        bool(getattr(client, 'auth_token', None))
                    )
                except Exception:
                    # Don't raise on logging
                    pass
        else:
            self._logger.info("No external agents configured (ORCHESTRATOR_URL/PATTERN_MINER_URL unset)")

    def get_agent(self, agent_name: str) -> Optional[A2AClient]:
        """
        Get A2A client for an agent

        Args:
            agent_name: Agent identifier

        Returns:
            A2AClient instance or None
        """
        return self.agents.get(agent_name)

    def list_agents(self) -> list:
        """
        List all registered agents

        Returns:
            List of agent names
        """
        return list(self.agents.keys())

    def health_check_all(self) -> Dict[str, bool]:
        """
        Check health of all registered agents

        Returns:
            Dictionary mapping agent name to health status
        """
        status: Dict[str, bool] = {}
        for name, client in self.agents.items():
            try:
                healthy = client.health_check()
                status[name] = healthy
                self._logger.info("Health check for external agent '%s': %s", name, healthy)
            except Exception as e:
                status[name] = False
                self._logger.warning("Health check for external agent '%s' failed: %s", name, e)

        return status
