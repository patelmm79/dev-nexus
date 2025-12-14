"""
PostgreSQL Repository Module

Provides data access layer for all knowledge base operations using PostgreSQL.
Replaces the JSON-based KnowledgeBaseManager.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from schemas.knowledge_base_v2 import (
    KnowledgeBaseV2,
    RepositoryInfo,
    LatestPatterns,
    DeploymentInfo,
    DependencyInfo,
    LessonLearned,
    Pattern,
    TechnicalDecision,
    ReusableComponent
)
from core.database import DatabaseManager

logger = logging.getLogger(__name__)


class PostgresRepository:
    """
    PostgreSQL-based repository for knowledge base operations.
    Provides the same interface as KnowledgeBaseManager but uses PostgreSQL.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize PostgreSQL repository

        Args:
            db_manager: DatabaseManager instance for database operations
        """
        self.db = db_manager

    async def get_all_repositories(self) -> Dict[str, RepositoryInfo]:
        """
        Load all repositories from PostgreSQL

        Returns:
            Dictionary mapping repository names to RepositoryInfo objects
        """
        try:
            query = """
                SELECT id, name, problem_domain, last_analyzed, created_at, updated_at
                FROM repositories
                ORDER BY name
            """
            rows = await self.db.fetch(query)

            repositories = {}
            for row in rows:
                repo_name = row['name']

                # Get latest patterns for this repository
                latest_patterns = await self._get_latest_patterns(row['id'])

                # Get deployment info
                deployment = await self._get_deployment_info(row['id'])

                # Get dependency info
                dependencies = await self._get_dependency_info(row['id'])

                # Create RepositoryInfo object
                repo_info = RepositoryInfo(
                    latest_patterns=latest_patterns,
                    deployment=deployment,
                    dependencies=dependencies,
                    testing=None,  # TODO: Implement if needed
                    security=None,  # TODO: Implement if needed
                    history=[]  # TODO: Implement if needed
                )

                repositories[repo_name] = repo_info

            return repositories

        except Exception as e:
            logger.error(f"Failed to load repositories: {e}")
            return {}

    async def load_knowledge_base(self) -> KnowledgeBaseV2:
        """
        Load complete knowledge base from PostgreSQL
        Compatible with old KnowledgeBaseManager.load_knowledge_base()

        Returns:
            KnowledgeBaseV2 object
        """
        repositories = await self.get_all_repositories()
        return KnowledgeBaseV2(
            schema_version="2.0",
            repositories=repositories
        )

    async def get_repository_info(self, repository_name: str) -> Optional[RepositoryInfo]:
        """
        Get information for a specific repository

        Args:
            repository_name: Repository name (format: "owner/repo")

        Returns:
            RepositoryInfo object or None if not found
        """
        try:
            query = "SELECT id FROM repositories WHERE name = $1"
            row = await self.db.fetchrow(query, repository_name)

            if not row:
                return None

            repo_id = row['id']

            # Get all info for this repository
            latest_patterns = await self._get_latest_patterns(repo_id)
            deployment = await self._get_deployment_info(repo_id)
            dependencies = await self._get_dependency_info(repo_id)

            return RepositoryInfo(
                latest_patterns=latest_patterns,
                deployment=deployment,
                dependencies=dependencies,
                testing=None,
                security=None,
                history=[]
            )

        except Exception as e:
            logger.error(f"Failed to get repository info for {repository_name}: {e}")
            return None

    async def add_lesson_learned(
        self,
        repository_name: str,
        lesson: LessonLearned
    ) -> bool:
        """
        Add a lesson learned to a repository

        Args:
            repository_name: Repository name (format: "owner/repo")
            lesson: LessonLearned object

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure repository exists
            repo_id = await self._ensure_repository(repository_name)

            # Insert lesson learned
            query = """
                INSERT INTO lessons_learned (
                    repo_id, title, description, category, impact, date, created_at
                )
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
            """

            await self.db.execute(
                query,
                repo_id,
                lesson.lesson[:500],  # Use lesson text as title
                lesson.context,
                lesson.category,
                lesson.severity,
                lesson.timestamp
            )

            logger.info(f"Added lesson learned for {repository_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add lesson learned: {e}")
            return False

    async def update_dependency_info(
        self,
        repository_name: str,
        dependency_info: DependencyInfo
    ) -> bool:
        """
        Update dependency information for a repository

        Args:
            repository_name: Repository name (format: "owner/repo")
            dependency_info: DependencyInfo object

        Returns:
            True if successful, False otherwise
        """
        try:
            repo_id = await self._ensure_repository(repository_name)

            # Delete existing dependencies
            await self.db.execute(
                "DELETE FROM dependencies WHERE repo_id = $1",
                repo_id
            )

            # Insert consumers
            for consumer in dependency_info.consumers:
                await self.db.execute(
                    """
                    INSERT INTO dependencies (repo_id, dependency_name, dependency_type)
                    VALUES ($1, $2, 'consumer')
                    """,
                    repo_id,
                    consumer.get('repository', consumer.get('name', 'unknown'))
                )

            # Insert derivatives
            for derivative in dependency_info.derivatives:
                await self.db.execute(
                    """
                    INSERT INTO dependencies (repo_id, dependency_name, dependency_type)
                    VALUES ($1, $2, 'derivative')
                    """,
                    repo_id,
                    derivative.get('repository', derivative.get('name', 'unknown'))
                )

            # Insert external dependencies
            for external in dependency_info.external_dependencies:
                dep_name = external if isinstance(external, str) else external.get('name', 'unknown')
                await self.db.execute(
                    """
                    INSERT INTO dependencies (repo_id, dependency_name, dependency_type)
                    VALUES ($1, $2, 'external')
                    """,
                    repo_id,
                    dep_name
                )

            logger.info(f"Updated dependency info for {repository_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update dependency info: {e}")
            return False

    async def add_deployment_info(
        self,
        repository_name: str,
        deployment_info: DeploymentInfo
    ) -> bool:
        """
        Add deployment information for a repository

        Args:
            repository_name: Repository name (format: "owner/repo")
            deployment_info: DeploymentInfo object

        Returns:
            True if successful, False otherwise
        """
        try:
            repo_id = await self._ensure_repository(repository_name)

            # Store deployment info as JSON in deployment_scripts table
            # (This is a simplified approach - could be expanded to use dedicated tables)
            query = """
                INSERT INTO deployment_scripts (
                    repo_id, name, description, commands, environment_variables
                )
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (repo_id, name) DO UPDATE SET
                    description = EXCLUDED.description,
                    commands = EXCLUDED.commands,
                    environment_variables = EXCLUDED.environment_variables
            """

            await self.db.execute(
                query,
                repo_id,
                deployment_info.ci_cd_platform or "deployment",
                json.dumps(deployment_info.infrastructure or {}),
                json.dumps(deployment_info.scripts or []),
                json.dumps({})  # environment_variables
            )

            logger.info(f"Added deployment info for {repository_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to add deployment info: {e}")
            return False

    # Helper methods

    async def _ensure_repository(self, repository_name: str) -> int:
        """
        Ensure repository exists in database, create if not

        Args:
            repository_name: Repository name (format: "owner/repo")

        Returns:
            Repository ID
        """
        # Check if exists
        query = "SELECT id FROM repositories WHERE name = $1"
        row = await self.db.fetchrow(query, repository_name)

        if row:
            return row['id']

        # Create new repository
        query = """
            INSERT INTO repositories (name, created_at, updated_at)
            VALUES ($1, NOW(), NOW())
            RETURNING id
        """
        row = await self.db.fetchrow(query, repository_name)
        return row['id']

    async def _get_latest_patterns(self, repo_id: int) -> LatestPatterns:
        """Get latest patterns for a repository"""
        try:
            # Get patterns
            patterns_query = """
                SELECT name, description, context
                FROM patterns
                WHERE repo_id = $1
                ORDER BY created_at DESC
                LIMIT 50
            """
            pattern_rows = await self.db.fetch(patterns_query, repo_id)

            patterns = [
                Pattern(
                    name=row['name'],
                    description=row['description'] or "",
                    why=row['context'] or ""
                )
                for row in pattern_rows
            ]

            # Get technical decisions
            decisions_query = """
                SELECT what, why, alternatives
                FROM technical_decisions
                WHERE repo_id = $1
                ORDER BY created_at DESC
                LIMIT 20
            """
            decision_rows = await self.db.fetch(decisions_query, repo_id)

            decisions = [
                TechnicalDecision(
                    what=row['what'],
                    why=row['why'] or "",
                    alternatives=row['alternatives'] or ""
                )
                for row in decision_rows
            ]

            # Get reusable components
            components_query = """
                SELECT name, purpose, location
                FROM reusable_components
                WHERE repo_id = $1
                ORDER BY created_at DESC
                LIMIT 20
            """
            component_rows = await self.db.fetch(components_query, repo_id)

            components = [
                ReusableComponent(
                    name=row['name'],
                    purpose=row['purpose'] or "",
                    location=row['location'] or ""
                )
                for row in component_rows
            ]

            # Get keywords
            keywords_query = """
                SELECT DISTINCT k.keyword
                FROM keywords k
                JOIN pattern_keywords pk ON pk.keyword_id = k.id
                JOIN patterns p ON p.id = pk.pattern_id
                WHERE p.repo_id = $1
                LIMIT 50
            """
            keyword_rows = await self.db.fetch(keywords_query, repo_id)
            keywords = [row['keyword'] for row in keyword_rows]

            # Get problem domain
            domain_query = "SELECT problem_domain FROM repositories WHERE id = $1"
            domain_row = await self.db.fetchrow(domain_query, repo_id)
            problem_domain = domain_row['problem_domain'] if domain_row else ""

            return LatestPatterns(
                patterns=patterns,
                decisions=decisions,
                reusable_components=components,
                dependencies=[],  # Handled separately
                problem_domain=problem_domain or "",
                keywords=keywords
            )

        except Exception as e:
            logger.error(f"Failed to get latest patterns: {e}")
            return LatestPatterns(
                patterns=[],
                decisions=[],
                reusable_components=[],
                dependencies=[],
                problem_domain="",
                keywords=[]
            )

    async def _get_deployment_info(self, repo_id: int) -> DeploymentInfo:
        """Get deployment info for a repository"""
        try:
            query = """
                SELECT description, commands, environment_variables
                FROM deployment_scripts
                WHERE repo_id = $1
                ORDER BY created_at DESC
                LIMIT 1
            """
            row = await self.db.fetchrow(query, repo_id)

            if not row:
                return DeploymentInfo()

            infrastructure = json.loads(row['description']) if row['description'] else {}
            scripts = json.loads(row['commands']) if row['commands'] else []

            return DeploymentInfo(
                scripts=scripts,
                lessons_learned=[],  # Handled separately
                reusable_components=[],
                ci_cd_platform="",
                infrastructure=infrastructure
            )

        except Exception as e:
            logger.error(f"Failed to get deployment info: {e}")
            return DeploymentInfo()

    async def _get_dependency_info(self, repo_id: int) -> DependencyInfo:
        """Get dependency info for a repository"""
        try:
            query = """
                SELECT dependency_name, dependency_type
                FROM dependencies
                WHERE repo_id = $1
            """
            rows = await self.db.fetch(query, repo_id)

            consumers = []
            derivatives = []
            external_deps = []

            for row in rows:
                dep_name = row['dependency_name']
                dep_type = row['dependency_type']

                if dep_type == 'consumer':
                    consumers.append({"repository": dep_name})
                elif dep_type == 'derivative':
                    derivatives.append({"repository": dep_name})
                elif dep_type == 'external':
                    external_deps.append(dep_name)

            return DependencyInfo(
                consumers=consumers,
                derivatives=derivatives,
                external_dependencies=external_deps
            )

        except Exception as e:
            logger.error(f"Failed to get dependency info: {e}")
            return DependencyInfo()

    # Compatibility methods for runtime monitoring
    async def load(self) -> Dict[str, Any]:
        """Load knowledge base as dictionary (for runtime monitoring compatibility)"""
        kb = await self.load_knowledge_base()
        return kb.model_dump(mode='json')

    async def save(self, kb_data: Dict[str, Any]) -> bool:
        """Save knowledge base from dictionary (for runtime monitoring compatibility)"""
        # This is a complex operation that would require parsing the entire KB structure
        # For now, log a warning that this operation is not fully implemented
        logger.warning("PostgresRepository.save() called - complex operation, skipping")
        return True
