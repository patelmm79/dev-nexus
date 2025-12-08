"""
A2A Skills Package

Contains all skill implementations for the Pattern Discovery Agent.
Skills are organized by category and automatically registered on import.

Skill Categories:
- pattern_query: Search and analyze patterns across repositories
- repository_info: Retrieve repository information and metadata
- knowledge_management: Update and manage knowledge base
- integration: Coordinate with external agents
"""

from a2a.skills.base import BaseSkill, SkillGroup
from a2a.registry import get_registry, register_skill

__all__ = [
    'BaseSkill',
    'SkillGroup',
    'get_registry',
    'register_skill'
]
