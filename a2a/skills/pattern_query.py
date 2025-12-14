"""
Pattern Query Skills

Skills for searching and analyzing patterns across repositories:
- query_patterns: Search for similar patterns by keywords or pattern names
- get_cross_repo_patterns: Find patterns used across multiple repositories
"""

from typing import Dict, Any, List
from datetime import datetime

from a2a.skills.base import BaseSkill, SkillGroup


class QueryPatternsSkill(BaseSkill):
    """Search for similar architectural patterns across repositories"""

    def __init__(self, postgres_repo, similarity_finder):
        self.postgres_repo = postgres_repo
        self.similarity_finder = similarity_finder

    @property
    def skill_id(self) -> str:
        return "query_patterns"

    @property
    def skill_name(self) -> str:
        return "Query Similar Patterns"

    @property
    def skill_description(self) -> str:
        return "Search for similar architectural patterns across all repositories in the knowledge base"

    @property
    def tags(self) -> List[str]:
        return ["search", "patterns", "similarity"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Keywords to search for (e.g., ['retry', 'exponential backoff'])"
                },
                "patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Specific pattern names to match"
                },
                "min_matches": {
                    "type": "integer",
                    "description": "Minimum number of matches required",
                    "default": 1
                }
            }
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {"keywords": ["retry", "exponential backoff"]},
                "description": "Find repositories using retry logic with exponential backoff"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query similar patterns across repositories

        Input:
            - keywords: List[str] - Keywords to search for
            - patterns: List[str] - Pattern names to match (optional)
            - min_matches: int - Minimum similarity score (optional)

        Output:
            - matches: List of matching repositories with similarity scores
            - total_matches: Total number of matches found
        """
        try:
            keywords = input_data.get('keywords', [])
            patterns = input_data.get('patterns', [])
            min_matches = input_data.get('min_matches', 1)

            # Load knowledge base from PostgreSQL
            kb = await self.postgres_repo.load_knowledge_base()

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
                    "success": False,
                    "error": "Must provide either 'keywords' or 'patterns' to search",
                    "matches": [],
                    "total_matches": 0
                }

            return {
                "success": True,
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
                "success": False,
                "error": f"Failed to query patterns: {str(e)}",
                "matches": [],
                "total_matches": 0
            }


class GetCrossRepoPatternsSkill(BaseSkill):
    """Find patterns that exist across multiple repositories"""

    def __init__(self, postgres_repo):
        self.postgres_repo = postgres_repo

    @property
    def skill_id(self) -> str:
        return "get_cross_repo_patterns"

    @property
    def skill_name(self) -> str:
        return "Get Cross-Repository Patterns"

    @property
    def skill_description(self) -> str:
        return "Find patterns that exist across multiple repositories, useful for identifying common architectural decisions"

    @property
    def tags(self) -> List[str]:
        return ["patterns", "cross-repo", "analysis"]

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "min_repos": {
                    "type": "integer",
                    "description": "Minimum number of repositories a pattern must appear in",
                    "default": 2
                },
                "pattern_type": {
                    "type": "string",
                    "description": "Filter by pattern type (optional)"
                }
            }
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {"min_repos": 3},
                "description": "Find patterns used in 3 or more repositories"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find patterns that exist across multiple repositories

        Input:
            - min_repos: int - Minimum number of repos a pattern must appear in (default: 2)
            - pattern_type: str - Filter by pattern type (optional)

        Output:
            - cross_repo_patterns: List of patterns with repos that use them
            - total_patterns: Number of cross-repo patterns found
        """
        try:
            min_repos = input_data.get('min_repos', 2)
            pattern_type = input_data.get('pattern_type')

            kb = await self.postgres_repo.load_knowledge_base()

            # Aggregate patterns across all repos
            pattern_to_repos = {}

            for repo_name, repo_info in kb.repositories.items():
                for pattern in repo_info.latest_patterns.patterns:
                    if pattern_type and pattern_type.lower() not in pattern.lower():
                        continue

                    if pattern not in pattern_to_repos:
                        pattern_to_repos[pattern] = []
                    pattern_to_repos[pattern].append(repo_name)

            # Filter to patterns appearing in min_repos or more
            cross_repo_patterns = [
                {
                    "pattern": pattern,
                    "repositories": repos,
                    "repo_count": len(repos)
                }
                for pattern, repos in pattern_to_repos.items()
                if len(repos) >= min_repos
            ]

            # Sort by repo count (most common first)
            cross_repo_patterns.sort(key=lambda x: x['repo_count'], reverse=True)

            return {
                "success": True,
                "cross_repo_patterns": cross_repo_patterns,
                "total_patterns": len(cross_repo_patterns),
                "min_repos": min_repos,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get cross-repo patterns: {str(e)}",
                "cross_repo_patterns": [],
                "total_patterns": 0
            }


class PatternQuerySkills(SkillGroup):
    """Group of pattern query and analysis skills"""

    def __init__(self, postgres_repo, similarity_finder):
        super().__init__(postgres_repo=postgres_repo, similarity_finder=similarity_finder)
        self._skills = [
            QueryPatternsSkill(postgres_repo, similarity_finder),
            GetCrossRepoPatternsSkill(postgres_repo)
        ]

    def get_skills(self) -> List[BaseSkill]:
        return self._skills
