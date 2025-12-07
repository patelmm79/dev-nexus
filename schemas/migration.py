"""
Knowledge Base Migration Utilities

Handles migration from v1 schema to v2 schema.
Non-destructive: preserves all existing data while adding new structure.
"""

from typing import Dict, Any
from datetime import datetime
from schemas.knowledge_base_v2 import (
    KnowledgeBaseV2,
    RepositoryMetadata,
    PatternEntry,
    ReusableComponent,
    DeploymentInfo,
    DependencyInfo,
    TestingInfo,
    SecurityInfo
)


class KnowledgeBaseMigration:
    """Migrate knowledge base from v1 to v2 schema"""

    def __init__(self):
        self.migration_timestamp = datetime.now()

    def migrate_v1_to_v2(self, old_kb: Dict[str, Any]) -> KnowledgeBaseV2:
        """
        Migrate from v1 (flat patterns) to v2 (structured metadata)

        V1 Structure:
        {
          "repositories": {
            "repo": {
              "patterns": {...},
              "history": [...]
            }
          },
          "last_updated": "..."
        }

        V2 Structure: Full RepositoryMetadata with deployment/dependencies/testing/security
        """
        migrated_repos = {}

        for repo_name, repo_data in old_kb.get('repositories', {}).items():
            migrated_repos[repo_name] = self._migrate_repository(repo_name, repo_data)

        return KnowledgeBaseV2(
            schema_version="2.0",
            repositories=migrated_repos,
            created_at=self._parse_datetime(old_kb.get('created_at', datetime.now().isoformat())),
            last_updated=self.migration_timestamp,
            metadata={
                "migrated_from": "v1",
                "migration_date": self.migration_timestamp.isoformat(),
                "original_last_updated": old_kb.get('last_updated', '')
            }
        )

    def _migrate_repository(self, repo_name: str, repo_data: Dict[str, Any]) -> RepositoryMetadata:
        """Migrate a single repository from v1 to v2"""

        # Migrate latest patterns
        latest_patterns_data = repo_data.get('patterns', {})
        latest_patterns = self._migrate_pattern_entry(latest_patterns_data)

        # Migrate history
        history = []
        for hist_entry in repo_data.get('history', []):
            pattern_data = hist_entry.get('patterns', {})
            pattern_entry = self._migrate_pattern_entry(
                pattern_data,
                commit_sha=hist_entry.get('commit_sha', ''),
                timestamp=hist_entry.get('timestamp')
            )
            history.append(pattern_entry)

        # Initialize empty new sections
        deployment = self._initialize_deployment_from_patterns(latest_patterns_data)
        dependencies = self._initialize_dependencies_from_patterns(latest_patterns_data)
        testing = TestingInfo()
        security = SecurityInfo()

        return RepositoryMetadata(
            latest_patterns=latest_patterns,
            deployment=deployment,
            dependencies=dependencies,
            testing=testing,
            security=security,
            history=history,
            repository_url=f"https://github.com/{repo_name}",
            last_updated=self.migration_timestamp
        )

    def _migrate_pattern_entry(
        self,
        pattern_data: Dict[str, Any],
        commit_sha: str = None,
        timestamp: str = None
    ) -> PatternEntry:
        """Migrate a pattern entry from v1 to v2"""

        # Migrate reusable_components
        reusable_components = []
        for component_data in pattern_data.get('reusable_components', []):
            if isinstance(component_data, dict):
                reusable_components.append(ReusableComponent(
                    name=component_data.get('name', 'Unknown'),
                    description=component_data.get('description', ''),
                    files=component_data.get('files', []),
                    language=component_data.get('language', 'unknown'),
                    api_contract=component_data.get('api_contract'),
                    usage_example=component_data.get('usage_example'),
                    tags=component_data.get('tags', [])
                ))

        return PatternEntry(
            patterns=pattern_data.get('patterns', []),
            decisions=pattern_data.get('decisions', []),
            reusable_components=reusable_components,
            dependencies=pattern_data.get('dependencies', []),
            problem_domain=pattern_data.get('problem_domain', 'Unknown'),
            keywords=pattern_data.get('keywords', []),
            analyzed_at=self._parse_datetime(timestamp or pattern_data.get('analyzed_at', datetime.now().isoformat())),
            commit_sha=commit_sha or pattern_data.get('commit_sha', 'unknown'),
            commit_message=pattern_data.get('commit_message'),
            author=pattern_data.get('author')
        )

    def _initialize_deployment_from_patterns(self, pattern_data: Dict[str, Any]) -> DeploymentInfo:
        """Initialize deployment section with data from patterns"""

        # Convert reusable_components from patterns to deployment.reusable_components
        reusable_components = []
        for component_data in pattern_data.get('reusable_components', []):
            if isinstance(component_data, dict):
                reusable_components.append(ReusableComponent(
                    name=component_data.get('name', 'Unknown'),
                    description=component_data.get('description', ''),
                    files=component_data.get('files', []),
                    language=component_data.get('language', 'unknown'),
                    api_contract=component_data.get('api_contract'),
                    usage_example=component_data.get('usage_example')
                ))

        return DeploymentInfo(
            scripts=[],
            lessons_learned=[],
            reusable_components=reusable_components,
            ci_cd_platform=None,
            infrastructure={}
        )

    def _initialize_dependencies_from_patterns(self, pattern_data: Dict[str, Any]) -> DependencyInfo:
        """Initialize dependency section with external dependencies from patterns"""
        return DependencyInfo(
            consumers=[],
            derivatives=[],
            external_dependencies=pattern_data.get('dependencies', []),
            dependency_update_strategy=None
        )

    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Parse datetime string to datetime object"""
        try:
            # Try ISO format first
            return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            # Fall back to current time if parsing fails
            return datetime.now()

    def is_v2_schema(self, kb_data: Dict[str, Any]) -> bool:
        """Check if knowledge base is already v2 schema"""
        return kb_data.get('schema_version') == '2.0'

    def backfill_deployment_info(
        self,
        kb: KnowledgeBaseV2,
        repo_name: str,
        deployment_info: DeploymentInfo
    ) -> KnowledgeBaseV2:
        """Manually backfill deployment information for a specific repository"""
        if repo_name in kb.repositories:
            kb.repositories[repo_name].deployment = deployment_info
            kb.repositories[repo_name].last_updated = datetime.now()
            kb.last_updated = datetime.now()
        return kb

    def backfill_dependency_info(
        self,
        kb: KnowledgeBaseV2,
        repo_name: str,
        dependency_info: DependencyInfo
    ) -> KnowledgeBaseV2:
        """Manually backfill dependency information for a specific repository"""
        if repo_name in kb.repositories:
            kb.repositories[repo_name].dependencies = dependency_info
            kb.repositories[repo_name].last_updated = datetime.now()
            kb.last_updated = datetime.now()
        return kb

    def add_lesson_learned_to_repo(
        self,
        kb: KnowledgeBaseV2,
        repo_name: str,
        lesson: Any  # LessonLearned type
    ) -> KnowledgeBaseV2:
        """Add a lesson learned to a specific repository"""
        if repo_name in kb.repositories:
            kb.repositories[repo_name].deployment.lessons_learned.append(lesson)
            kb.repositories[repo_name].last_updated = datetime.now()
            kb.last_updated = datetime.now()
        return kb


def migrate_knowledge_base_file(old_kb_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to migrate a knowledge base dictionary

    Args:
        old_kb_dict: V1 knowledge base as dictionary

    Returns:
        V2 knowledge base as dictionary (JSON-serializable)
    """
    migrator = KnowledgeBaseMigration()

    # Check if already v2
    if migrator.is_v2_schema(old_kb_dict):
        print("Knowledge base is already v2 schema")
        return old_kb_dict

    # Migrate to v2
    kb_v2 = migrator.migrate_v1_to_v2(old_kb_dict)

    # Convert to dictionary
    return kb_v2.model_dump(mode='json')
