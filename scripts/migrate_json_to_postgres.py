#!/usr/bin/env python3
"""
Migrate Knowledge Base from GitHub JSON to PostgreSQL

This script migrates existing knowledge base data from the GitHub JSON format
to the new PostgreSQL database with pgvector support.

Usage:
    python scripts/migrate_json_to_postgres.py \\
        --json-url https://raw.githubusercontent.com/user/repo/main/knowledge_base.json \\
        --db-host 10.8.0.2 \\
        --db-name devnexus \\
        --generate-embeddings

Or with environment variables:
    POSTGRES_HOST=10.8.0.2 \\
    POSTGRES_DB=devnexus \\
    POSTGRES_USER=devnexus \\
    POSTGRES_PASSWORD=your-password \\
    OPENAI_API_KEY=sk-xxx \\
    python scripts/migrate_json_to_postgres.py --json-url URL
"""

import asyncio
import argparse
import json
import logging
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime
import aiohttp
import asyncpg

# Add parent directory to path
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

from core.database import DatabaseManager
from core.embeddings import EmbeddingGenerator

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class KnowledgeBaseMigrator:
    """Migrates knowledge base from JSON to PostgreSQL"""

    def __init__(
        self,
        db_manager: DatabaseManager,
        embedding_generator: Optional[EmbeddingGenerator] = None,
    ):
        self.db = db_manager
        self.embedding_gen = embedding_generator
        self.stats = {
            "repositories": 0,
            "patterns": 0,
            "decisions": 0,
            "components": 0,
            "dependencies": 0,
            "lessons": 0,
            "embeddings_generated": 0,
            "errors": 0,
        }

    async def load_json_from_url(self, url: str) -> Dict[str, Any]:
        """Load knowledge base JSON from URL"""
        logger.info(f"Fetching knowledge base from: {url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status != 200:
                    raise Exception(
                        f"Failed to fetch JSON: HTTP {response.status}"
                    )

                content = await response.text()
                data = json.loads(content)

                logger.info(
                    f"Loaded knowledge base with {len(data.get('repositories', {}))} repositories"
                )
                return data

    async def get_or_create_repository(self, repo_name: str, repo_data: Dict[str, Any]) -> int:
        """
        Get or create repository

        Returns:
            Repository ID
        """
        # Check if repository exists
        existing = await self.db.fetchrow(
            "SELECT id FROM repositories WHERE name = $1", repo_name
        )

        if existing:
            return existing["id"]

        # Create new repository
        latest_patterns = repo_data.get("latest_patterns", {})
        problem_domain = latest_patterns.get("problem_domain", "")

        repo_id = await self.db.fetchval(
            """
            INSERT INTO repositories (name, problem_domain, last_analyzed)
            VALUES ($1, $2, $3)
            RETURNING id
            """,
            repo_name,
            problem_domain,
            datetime.now(),
        )

        logger.info(f"Created repository: {repo_name} (ID: {repo_id})")
        self.stats["repositories"] += 1

        return repo_id

    async def migrate_patterns(
        self, repo_id: int, patterns: List[Dict[str, Any]], generate_embeddings: bool
    ) -> None:
        """Migrate patterns for a repository"""
        for pattern in patterns:
            try:
                name = pattern.get("name", "")
                description = pattern.get("description", "")
                context = pattern.get("context", "")

                if not name:
                    continue

                # Generate embedding if requested
                embedding = None
                if generate_embeddings and self.embedding_gen and self.embedding_gen.enabled:
                    embedding = self.embedding_gen.generate_pattern_embedding(pattern)
                    if embedding:
                        self.stats["embeddings_generated"] += 1

                # Insert pattern
                await self.db.insert_pattern_with_embedding(
                    repo_id, name, description, context, embedding
                )

                self.stats["patterns"] += 1

            except Exception as e:
                logger.error(f"Failed to migrate pattern '{pattern.get('name')}': {e}")
                self.stats["errors"] += 1

    async def migrate_decisions(
        self, repo_id: int, decisions: List[Dict[str, Any]]
    ) -> None:
        """Migrate technical decisions"""
        for decision in decisions:
            try:
                await self.db.execute(
                    """
                    INSERT INTO technical_decisions (repo_id, what, why, alternatives)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT DO NOTHING
                    """,
                    repo_id,
                    decision.get("what", ""),
                    decision.get("why", ""),
                    decision.get("alternatives", ""),
                )

                self.stats["decisions"] += 1

            except Exception as e:
                logger.error(f"Failed to migrate decision: {e}")
                self.stats["errors"] += 1

    async def migrate_components(
        self, repo_id: int, components: List[Dict[str, Any]]
    ) -> None:
        """Migrate reusable components"""
        for component in components:
            try:
                await self.db.execute(
                    """
                    INSERT INTO reusable_components (repo_id, name, purpose, location)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT DO NOTHING
                    """,
                    repo_id,
                    component.get("name", ""),
                    component.get("purpose", ""),
                    component.get("location", ""),
                )

                self.stats["components"] += 1

            except Exception as e:
                logger.error(f"Failed to migrate component: {e}")
                self.stats["errors"] += 1

    async def migrate_dependencies(
        self, repo_id: int, dependencies: List[str]
    ) -> None:
        """Migrate dependencies"""
        for dep in dependencies:
            try:
                await self.db.execute(
                    """
                    INSERT INTO dependencies (repo_id, dependency_name, dependency_type)
                    VALUES ($1, $2, $3)
                    ON CONFLICT DO NOTHING
                    """,
                    repo_id,
                    dep,
                    "external",
                )

                self.stats["dependencies"] += 1

            except Exception as e:
                logger.error(f"Failed to migrate dependency: {e}")
                self.stats["errors"] += 1

    async def migrate_lessons_learned(
        self, repo_id: int, lessons: List[Dict[str, Any]]
    ) -> None:
        """Migrate lessons learned"""
        for lesson in lessons:
            try:
                # Parse date if available
                date = lesson.get("date")
                if isinstance(date, str):
                    try:
                        date = datetime.fromisoformat(date.replace("Z", "+00:00"))
                    except:
                        date = datetime.now()
                else:
                    date = datetime.now()

                await self.db.execute(
                    """
                    INSERT INTO lessons_learned (repo_id, title, description, category, impact, date)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT DO NOTHING
                    """,
                    repo_id,
                    lesson.get("title", ""),
                    lesson.get("description", ""),
                    lesson.get("category", "general"),
                    lesson.get("impact", "medium"),
                    date,
                )

                self.stats["lessons"] += 1

            except Exception as e:
                logger.error(f"Failed to migrate lesson: {e}")
                self.stats["errors"] += 1

    async def migrate_repository(
        self, repo_name: str, repo_data: Dict[str, Any], generate_embeddings: bool
    ) -> None:
        """Migrate single repository"""
        logger.info(f"Migrating repository: {repo_name}")

        # Get or create repository
        repo_id = await self.get_or_create_repository(repo_name, repo_data)

        # Migrate latest patterns
        latest_patterns = repo_data.get("latest_patterns", {})

        if "patterns" in latest_patterns:
            await self.migrate_patterns(
                repo_id, latest_patterns["patterns"], generate_embeddings
            )

        if "decisions" in latest_patterns:
            await self.migrate_decisions(repo_id, latest_patterns["decisions"])

        if "reusable_components" in latest_patterns:
            await self.migrate_components(
                repo_id, latest_patterns["reusable_components"]
            )

        if "dependencies" in latest_patterns:
            await self.migrate_dependencies(repo_id, latest_patterns["dependencies"])

        # Migrate deployment lessons learned
        deployment = repo_data.get("deployment", {})
        if "lessons_learned" in deployment:
            await self.migrate_lessons_learned(repo_id, deployment["lessons_learned"])

        logger.info(f"✓ Migrated repository: {repo_name}")

    async def migrate(
        self, json_data: Dict[str, Any], generate_embeddings: bool = False
    ) -> Dict[str, int]:
        """
        Migrate entire knowledge base

        Args:
            json_data: Knowledge base JSON data
            generate_embeddings: Whether to generate embeddings during migration

        Returns:
            Migration statistics
        """
        repositories = json_data.get("repositories", {})

        if not repositories:
            logger.warning("No repositories found in JSON data")
            return self.stats

        logger.info(
            f"Starting migration of {len(repositories)} repositories"
            + (
                " (with embedding generation)"
                if generate_embeddings
                else " (without embeddings)"
            )
        )

        # Migrate each repository
        for repo_name, repo_data in repositories.items():
            try:
                await self.migrate_repository(repo_name, repo_data, generate_embeddings)
            except Exception as e:
                logger.error(f"Failed to migrate repository {repo_name}: {e}")
                self.stats["errors"] += 1

        return self.stats


async def main():
    parser = argparse.ArgumentParser(
        description="Migrate knowledge base from JSON to PostgreSQL"
    )

    parser.add_argument(
        "--json-url",
        required=True,
        help="URL to knowledge_base.json (GitHub raw URL)",
    )
    parser.add_argument(
        "--json-file", help="Or path to local JSON file (alternative to URL)"
    )
    parser.add_argument("--db-host", help="PostgreSQL host (default: POSTGRES_HOST env)")
    parser.add_argument("--db-port", type=int, help="PostgreSQL port (default: 5432)")
    parser.add_argument(
        "--db-name", help="Database name (default: POSTGRES_DB env)"
    )
    parser.add_argument("--db-user", help="Database user (default: POSTGRES_USER env)")
    parser.add_argument(
        "--db-password", help="Database password (default: POSTGRES_PASSWORD env)"
    )
    parser.add_argument(
        "--generate-embeddings",
        action="store_true",
        help="Generate OpenAI embeddings during migration (requires OPENAI_API_KEY)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform dry run without writing to database",
    )

    args = parser.parse_args()

    # Initialize database manager
    db = DatabaseManager(
        host=args.db_host,
        port=args.db_port,
        database=args.db_name,
        user=args.db_user,
        password=args.db_password,
    )

    # Force enable PostgreSQL for migration
    db.enabled = True

    try:
        # Connect to database
        logger.info("Connecting to PostgreSQL...")
        await db.connect()

        # Health check
        health = await db.health_check()
        if health["status"] != "healthy":
            logger.error(f"Database unhealthy: {health}")
            return 1

        logger.info(f"✓ Connected to PostgreSQL {health.get('version', 'unknown')}")

        if health.get("pgvector_version"):
            logger.info(f"✓ pgvector v{health['pgvector_version']} available")

        # Load JSON data
        if args.json_file:
            logger.info(f"Loading JSON from file: {args.json_file}")
            with open(args.json_file, "r") as f:
                json_data = json.load(f)
        else:
            migrator = KnowledgeBaseMigrator(db)
            json_data = await migrator.load_json_from_url(args.json_url)

        # Initialize embedding generator if requested
        embedding_gen = None
        if args.generate_embeddings:
            embedding_gen = EmbeddingGenerator()
            if not embedding_gen.enabled:
                logger.warning(
                    "Embedding generation requested but OPENAI_API_KEY not set. Skipping embeddings."
                )
                args.generate_embeddings = False

        # Create migrator
        migrator = KnowledgeBaseMigrator(db, embedding_gen)

        if args.dry_run:
            logger.info("DRY RUN MODE - No changes will be made")
            # TODO: Implement dry run logic
            return 0

        # Run migration
        logger.info("=" * 60)
        logger.info("Starting migration...")
        logger.info("=" * 60)

        stats = await migrator.migrate(json_data, args.generate_embeddings)

        # Print summary
        logger.info("=" * 60)
        logger.info("Migration complete!")
        logger.info("=" * 60)
        logger.info(f"Repositories:       {stats['repositories']}")
        logger.info(f"Patterns:           {stats['patterns']}")
        logger.info(f"Technical decisions: {stats['decisions']}")
        logger.info(f"Reusable components: {stats['components']}")
        logger.info(f"Dependencies:        {stats['dependencies']}")
        logger.info(f"Lessons learned:     {stats['lessons']}")
        if args.generate_embeddings:
            logger.info(f"Embeddings generated: {stats['embeddings_generated']}")
        logger.info(f"Errors:              {stats['errors']}")
        logger.info("=" * 60)

        return 0 if stats["errors"] == 0 else 1

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return 1

    finally:
        await db.disconnect()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
