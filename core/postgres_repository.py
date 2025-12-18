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
    RepositoryMetadata,
    PatternEntry,
    DeploymentInfo,
    DependencyInfo,
    LessonLearned,
    ReusableComponent,
    TestingInfo,
    SecurityInfo
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

    async def get_all_repositories(self) -> Dict[str, RepositoryMetadata]:
        """
        Load all repositories from PostgreSQL

        Returns:
            Dictionary mapping repository names to RepositoryMetadata objects
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

                # Create RepositoryMetadata object
                repo_info = RepositoryMetadata(
                    latest_patterns=latest_patterns,
                    deployment=deployment,
                    dependencies=dependencies,
                    testing=TestingInfo(),
                    security=SecurityInfo(),
                    history=[],
                    last_updated=row['updated_at']
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
        now = datetime.now()
        return KnowledgeBaseV2(
            schema_version="2.0",
            repositories=repositories,
            created_at=now,
            last_updated=now
        )

    async def get_repository_info(self, repository_name: str) -> Optional[RepositoryMetadata]:
        """
        Get information for a specific repository

        Args:
            repository_name: Repository name (format: "owner/repo")

        Returns:
            RepositoryMetadata object or None if not found
        """
        try:
            query = "SELECT id, updated_at FROM repositories WHERE name = $1"
            row = await self.db.fetchrow(query, repository_name)

            if not row:
                return None

            repo_id = row['id']
            updated_at = row['updated_at']

            # Get all info for this repository
            latest_patterns = await self._get_latest_patterns(repo_id)
            deployment = await self._get_deployment_info(repo_id)
            dependencies = await self._get_dependency_info(repo_id)

            return RepositoryMetadata(
                latest_patterns=latest_patterns,
                deployment=deployment,
                dependencies=dependencies,
                testing=TestingInfo(),
                security=SecurityInfo(),
                history=[],
                last_updated=updated_at
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
            logger.info(f"[ADD_DEPLOYMENT] Starting for repository: {repository_name}")
            logger.info(f"[ADD_DEPLOYMENT] Database manager enabled: {self.db.enabled}, pool: {self.db.pool is not None}")

            repo_id = await self._ensure_repository(repository_name)
            logger.info(f"[ADD_DEPLOYMENT] Repository ID: {repo_id}")

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

            logger.info(f"[ADD_DEPLOYMENT] Executing deployment info insert for repo_id {repo_id}")
            await self.db.execute(
                query,
                repo_id,
                deployment_info.ci_cd_platform or "deployment",
                json.dumps(deployment_info.infrastructure or {}),
                json.dumps(deployment_info.scripts or []),
                json.dumps({})  # environment_variables
            )

            logger.info(f"[ADD_DEPLOYMENT] Successfully added deployment info for {repository_name}")
            return True

        except Exception as e:
            logger.error(f"[ADD_DEPLOYMENT] Failed to add deployment info for {repository_name}: {e}", exc_info=True)
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
        try:
            # Check if exists
            query = "SELECT id FROM repositories WHERE name = $1"
            logger.info(f"[ENSURE_REPO] Checking if repository '{repository_name}' exists")
            row = await self.db.fetchrow(query, repository_name)

            if row:
                logger.info(f"[ENSURE_REPO] Repository '{repository_name}' already exists with ID {row['id']}")
                return row['id']

            # Create new repository
            logger.info(f"[ENSURE_REPO] Creating new repository '{repository_name}'")
            query = """
                INSERT INTO repositories (name, created_at, updated_at)
                VALUES ($1, NOW(), NOW())
                RETURNING id
            """
            row = await self.db.fetchrow(query, repository_name)
            logger.info(f"[ENSURE_REPO] Repository '{repository_name}' created with ID {row['id']}")
            return row['id']
        except Exception as e:
            logger.error(f"[ENSURE_REPO] Failed for '{repository_name}': {e}")
            raise

    async def _get_latest_patterns(self, repo_id: int) -> PatternEntry:
        """Get latest patterns for a repository"""
        try:
            # Get patterns as simple strings
            patterns_query = """
                SELECT name
                FROM patterns
                WHERE repo_id = $1
                ORDER BY created_at DESC
                LIMIT 50
            """
            pattern_rows = await self.db.fetch(patterns_query, repo_id)
            patterns = [row['name'] for row in pattern_rows]

            # Get technical decisions as simple strings
            decisions_query = """
                SELECT what
                FROM technical_decisions
                WHERE repo_id = $1
                ORDER BY created_at DESC
                LIMIT 20
            """
            decision_rows = await self.db.fetch(decisions_query, repo_id)
            decisions = [row['what'] for row in decision_rows]

            # Get reusable components (matching schema: name, description, files, language)
            components_query = """
                SELECT name, purpose as description, location, 'unknown' as language
                FROM reusable_components
                WHERE repo_id = $1
                ORDER BY created_at DESC
                LIMIT 20
            """
            component_rows = await self.db.fetch(components_query, repo_id)
            components = [
                ReusableComponent(
                    name=row['name'],
                    description=row['description'] or "",
                    files=[row['location']] if row['location'] else [],
                    language=row['language']
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

            # Get repository info for additional fields
            repo_query = "SELECT problem_domain, last_analyzed, last_commit_sha FROM repositories WHERE id = $1"
            repo_row = await self.db.fetchrow(repo_query, repo_id)
            problem_domain = repo_row['problem_domain'] if repo_row else ""
            analyzed_at = repo_row['last_analyzed'] if repo_row else datetime.now()
            commit_sha = repo_row['last_commit_sha'] if repo_row else ""

            return PatternEntry(
                patterns=patterns,
                decisions=decisions,
                reusable_components=components,
                dependencies=[],  # Handled separately
                problem_domain=problem_domain or "",
                keywords=keywords,
                analyzed_at=analyzed_at,
                commit_sha=commit_sha or "unknown"
            )

        except Exception as e:
            logger.error(f"Failed to get latest patterns: {e}")
            return PatternEntry(
                patterns=[],
                decisions=[],
                reusable_components=[],
                dependencies=[],
                problem_domain="",
                keywords=[],
                analyzed_at=datetime.now(),
                commit_sha="unknown"
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

    async def get_recent_actions(
        self,
        limit: int = 20,
        offset: int = 0,
        action_types: Optional[List[str]] = None,
        repository_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get recent actions across all activity types in chronological order

        Args:
            limit: Maximum number of actions to return
            offset: Number of actions to skip (for pagination)
            action_types: Filter by action types ['analysis', 'lesson', 'deployment', 'runtime_issue']
            repository_filter: Filter by repository name (optional)

        Returns:
            Dictionary with:
            - actions: List of normalized action objects
            - total_count: Total count matching filters (for pagination)
            - returned: Number of actions returned
        """
        try:
            # Default to all action types if not specified
            if action_types is None:
                action_types = ['analysis', 'lesson', 'deployment', 'runtime_issue']

            # Build UNION query to combine all action types
            union_parts = []

            # 1. Analysis History
            if 'analysis' in action_types:
                union_parts.append("""
                    SELECT
                        'analysis' as action_type,
                        r.name as repository,
                        ah.analyzed_at as timestamp,
                        ah.commit_sha as reference_id,
                        jsonb_build_object(
                            'commit_sha', ah.commit_sha,
                            'patterns_count', ah.patterns_count,
                            'decisions_count', ah.decisions_count,
                            'components_count', ah.components_count
                        ) as metadata
                    FROM analysis_history ah
                    JOIN repositories r ON ah.repo_id = r.id
                """)

            # 2. Lessons Learned
            if 'lesson' in action_types:
                union_parts.append("""
                    SELECT
                        'lesson' as action_type,
                        r.name as repository,
                        ll.date as timestamp,
                        ll.title as reference_id,
                        jsonb_build_object(
                            'category', ll.category,
                            'impact', ll.impact,
                            'description', ll.description
                        ) as metadata
                    FROM lessons_learned ll
                    JOIN repositories r ON ll.repo_id = r.id
                """)

            # 3. Deployment Scripts
            if 'deployment' in action_types:
                union_parts.append("""
                    SELECT
                        'deployment' as action_type,
                        r.name as repository,
                        ds.created_at as timestamp,
                        ds.name as reference_id,
                        jsonb_build_object(
                            'name', ds.name,
                            'description', ds.description
                        ) as metadata
                    FROM deployment_scripts ds
                    JOIN repositories r ON ds.repo_id = r.id
                """)

            # 4. Runtime Issues
            if 'runtime_issue' in action_types:
                union_parts.append("""
                    SELECT
                        'runtime_issue' as action_type,
                        r.name as repository,
                        ri.detected_at as timestamp,
                        ri.issue_id as reference_id,
                        jsonb_build_object(
                            'issue_type', ri.issue_type,
                            'severity', ri.severity,
                            'service_type', ri.service_type,
                            'pattern_reference', ri.pattern_reference,
                            'status', ri.status,
                            'log_snippet', SUBSTRING(ri.log_snippet, 1, 200)
                        ) as metadata
                    FROM runtime_issues ri
                    JOIN repositories r ON ri.repo_id = r.id
                """)

            if not union_parts:
                return {
                    "actions": [],
                    "total_count": 0,
                    "returned": 0
                }

            # Combine with UNION ALL
            union_query = " UNION ALL ".join(union_parts)

            # Add repository filter if specified
            where_clause = ""
            params = []
            if repository_filter:
                where_clause = "WHERE repository = $1"
                params.append(repository_filter)

            # Count query
            count_query = f"""
                SELECT COUNT(*) as total
                FROM ({union_query}) as combined_actions
                {where_clause}
            """

            # Get total count
            if params:
                count_row = await self.db.fetchrow(count_query, *params)
            else:
                count_row = await self.db.fetchrow(count_query)
            total_count = count_row['total'] if count_row else 0

            # Main query with ORDER BY and pagination
            main_query = f"""
                SELECT *
                FROM ({union_query}) as combined_actions
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
            """

            params.extend([limit, offset])

            # Execute query
            rows = await self.db.fetch(main_query, *params)

            # Convert to list of dicts
            actions = [
                {
                    "action_type": row['action_type'],
                    "repository": row['repository'],
                    "timestamp": row['timestamp'].isoformat() if row['timestamp'] else None,
                    "reference_id": row['reference_id'],
                    "metadata": row['metadata']
                }
                for row in rows
            ]

            return {
                "actions": actions,
                "total_count": total_count,
                "returned": len(actions)
            }

        except Exception as e:
            logger.error(f"Failed to get recent actions: {e}")
            return {
                "actions": [],
                "total_count": 0,
                "returned": 0,
                "error": str(e)
            }
