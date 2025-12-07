"""
Knowledge Base Manager Module

Manages knowledge base CRUD operations with GitHub storage.
Supports both v1 and v2 schemas with automatic migration.
Shared by both GitHub Actions CLI and A2A server.
"""

import json
from typing import Dict, Optional
from datetime import datetime
from github import Github
from github.GithubException import UnknownObjectException

from schemas.knowledge_base_v2 import (
    KnowledgeBaseV2,
    RepositoryMetadata,
    PatternEntry,
    LessonLearned,
    DeploymentInfo,
    DependencyInfo,
    create_empty_repository_metadata
)
from schemas.migration import KnowledgeBaseMigration


class KnowledgeBaseManager:
    """Manage knowledge base operations with GitHub storage"""

    def __init__(self, github_client: Github, kb_repo_name: Optional[str]):
        """
        Initialize knowledge base manager

        Args:
            github_client: Initialized PyGithub client
            kb_repo_name: Knowledge base repository name (format: "owner/repo")
        """
        self.github_client = github_client
        self.kb_repo_name = kb_repo_name
        self.migrator = KnowledgeBaseMigration()

    def load_knowledge_base(self) -> KnowledgeBaseV2:
        """
        Load knowledge base from GitHub repository

        Returns:
            KnowledgeBaseV2 object (migrated from v1 if needed)
        """
        if not self.kb_repo_name:
            # Return empty KB if no repo configured
            return KnowledgeBaseV2(
                schema_version="2.0",
                repositories={},
                created_at=datetime.now(),
                last_updated=datetime.now()
            )

        try:
            kb_repo = self.github_client.get_repo(self.kb_repo_name)

            # Try to get the knowledge base file
            try:
                content_file = kb_repo.get_contents("knowledge_base.json")
                kb_data = json.loads(content_file.decoded_content.decode())

                # Check if migration is needed
                if not self.migrator.is_v2_schema(kb_data):
                    print("Migrating knowledge base from v1 to v2...")
                    kb_v2 = self.migrator.migrate_v1_to_v2(kb_data)
                    # Auto-save migrated version
                    self._save_kb_to_github(kb_v2, "Migrate knowledge base to v2 schema")
                    return kb_v2
                else:
                    # Already v2, parse it
                    return KnowledgeBaseV2(**kb_data)

            except UnknownObjectException:
                # KB doesn't exist yet - create empty v2 structure
                print("Knowledge base file not found, creating new v2 structure")
                return KnowledgeBaseV2(
                    schema_version="2.0",
                    repositories={},
                    created_at=datetime.now(),
                    last_updated=datetime.now()
                )

        except Exception as e:
            print(f"Error loading KB: {e}")
            return KnowledgeBaseV2(
                schema_version="2.0",
                repositories={},
                created_at=datetime.now(),
                last_updated=datetime.now()
            )

    def update_knowledge_base(
        self,
        repository_name: str,
        pattern_data: PatternEntry,
        commit_message: Optional[str] = None
    ):
        """
        Update knowledge base with new pattern analysis

        Args:
            repository_name: Repository name (format: "owner/repo")
            pattern_data: PatternEntry with analyzed patterns
            commit_message: Optional custom commit message
        """
        if not self.kb_repo_name:
            print("No knowledge base repo configured, skipping update")
            return

        try:
            kb = self.load_knowledge_base()

            # Initialize repo entry if doesn't exist
            if repository_name not in kb.repositories:
                kb.repositories[repository_name] = create_empty_repository_metadata(
                    commit_sha=pattern_data.commit_sha,
                    problem_domain=pattern_data.problem_domain
                )

            # Update latest patterns
            kb.repositories[repository_name].latest_patterns = pattern_data

            # Add to history
            kb.repositories[repository_name].history.append(pattern_data)

            # Update timestamps
            kb.repositories[repository_name].last_updated = datetime.now()
            kb.last_updated = datetime.now()

            # Save to GitHub
            default_message = f"Update KB: {repository_name} @ {pattern_data.commit_sha[:7]}"
            self._save_kb_to_github(kb, commit_message or default_message)

            print("Knowledge base updated successfully")

        except Exception as e:
            print(f"Error updating KB: {e}")

    def add_lesson_learned(
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
            kb = self.load_knowledge_base()

            # Ensure repository exists
            if repository_name not in kb.repositories:
                print(f"Repository {repository_name} not found in KB, creating entry")
                kb.repositories[repository_name] = create_empty_repository_metadata(
                    commit_sha="manual",
                    problem_domain="Unknown"
                )

            # Add lesson to deployment section
            kb.repositories[repository_name].deployment.lessons_learned.append(lesson)

            # Update timestamps
            kb.repositories[repository_name].last_updated = datetime.now()
            kb.last_updated = datetime.now()

            # Save to GitHub
            self._save_kb_to_github(
                kb,
                f"Add lesson learned for {repository_name}: {lesson.category}"
            )

            print(f"Lesson learned added for {repository_name}")
            return True

        except Exception as e:
            print(f"Error adding lesson learned: {e}")
            return False

    def add_deployment_info(
        self,
        repository_name: str,
        deployment_info: DeploymentInfo
    ) -> bool:
        """
        Add or update deployment information for a repository

        Args:
            repository_name: Repository name (format: "owner/repo")
            deployment_info: DeploymentInfo object

        Returns:
            True if successful, False otherwise
        """
        try:
            kb = self.load_knowledge_base()

            if repository_name not in kb.repositories:
                kb.repositories[repository_name] = create_empty_repository_metadata(
                    commit_sha="manual",
                    problem_domain="Unknown"
                )

            kb.repositories[repository_name].deployment = deployment_info
            kb.repositories[repository_name].last_updated = datetime.now()
            kb.last_updated = datetime.now()

            self._save_kb_to_github(kb, f"Update deployment info for {repository_name}")

            print(f"Deployment info updated for {repository_name}")
            return True

        except Exception as e:
            print(f"Error updating deployment info: {e}")
            return False

    def add_dependency_info(
        self,
        repository_name: str,
        dependency_info: DependencyInfo
    ) -> bool:
        """
        Add or update dependency information for a repository

        Args:
            repository_name: Repository name (format: "owner/repo")
            dependency_info: DependencyInfo object

        Returns:
            True if successful, False otherwise
        """
        try:
            kb = self.load_knowledge_base()

            if repository_name not in kb.repositories:
                kb.repositories[repository_name] = create_empty_repository_metadata(
                    commit_sha="manual",
                    problem_domain="Unknown"
                )

            kb.repositories[repository_name].dependencies = dependency_info
            kb.repositories[repository_name].last_updated = datetime.now()
            kb.last_updated = datetime.now()

            self._save_kb_to_github(kb, f"Update dependency info for {repository_name}")

            print(f"Dependency info updated for {repository_name}")
            return True

        except Exception as e:
            print(f"Error updating dependency info: {e}")
            return False

    def get_repository_info(self, repository_name: str) -> Optional[RepositoryMetadata]:
        """
        Get complete repository metadata

        Args:
            repository_name: Repository name (format: "owner/repo")

        Returns:
            RepositoryMetadata if found, None otherwise
        """
        kb = self.load_knowledge_base()
        return kb.repositories.get(repository_name)

    def _save_kb_to_github(self, kb: KnowledgeBaseV2, commit_message: str):
        """
        Save knowledge base to GitHub

        Args:
            kb: KnowledgeBaseV2 object
            commit_message: Commit message for the update
        """
        try:
            kb_repo = self.github_client.get_repo(self.kb_repo_name)
            kb_json = json.dumps(kb.model_dump(mode='json'), indent=2)

            try:
                # Try to update existing file
                content_file = kb_repo.get_contents("knowledge_base.json")
                kb_repo.update_file(
                    "knowledge_base.json",
                    commit_message,
                    kb_json,
                    content_file.sha,
                    branch="main"
                )
            except UnknownObjectException:
                # Create new file
                kb_repo.create_file(
                    "knowledge_base.json",
                    f"Initialize KB v2: {commit_message}",
                    kb_json,
                    branch="main"
                )

        except Exception as e:
            print(f"Error saving KB to GitHub: {e}")
            raise
