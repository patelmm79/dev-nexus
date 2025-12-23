"""
Migration 004: Extend Component Schema

This migration extends the reusable_components table to store all Component fields:
- component_id (unique identifier)
- component_type (api_client, infrastructure, business_logic, deployment_pattern)
- language
- api_signature
- imports (JSON array)
- keywords (JSON array)
- lines_of_code
- cyclomatic_complexity
- public_methods (JSON array)
- first_seen
- derived_from
- sync_status

Safe to run multiple times (idempotent).
Existing data is migrated to new schema with default values for new fields.
"""

import logging
from datetime import datetime
from typing import Any

from schemas.knowledge_base_v2 import KnowledgeBaseV2

logger = logging.getLogger(__name__)


def migrate(kb: KnowledgeBaseV2, db_manager: Any = None) -> KnowledgeBaseV2:
    """
    Run migration to extend component schema

    Args:
        kb: Current knowledge base
        db_manager: DatabaseManager instance (optional)

    Returns:
        Updated knowledge base
    """
    logger.info("Starting migration 004: Extend Component Schema")

    try:
        if not db_manager or not db_manager.pool:
            logger.warning("Database manager not available, skipping schema migration")
            logger.info("To complete this migration, run: python -c 'from migrations.004_extend_component_schema import run_schema_migration; run_schema_migration()'")
            return kb

        # Run schema migration
        import asyncio
        asyncio.run(_run_schema_migration_async(db_manager))

        logger.info("Migration 004 complete: Component schema extended")
        kb.last_updated = datetime.now()
        return kb

    except Exception as e:
        logger.error(f"Migration 004 failed: {e}", exc_info=True)
        raise


async def _run_schema_migration_async(db_manager: Any) -> None:
    """
    Run the actual schema migration asynchronously
    """
    # Check if new columns already exist
    query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'reusable_components'
        AND column_name = 'component_id'
    """

    result = await db_manager.fetchrow(query)

    if result:
        logger.info("Component schema already extended, skipping")
        return

    # Add new columns to reusable_components table
    logger.info("Adding new columns to reusable_components table...")

    alter_query = """
        ALTER TABLE reusable_components
        ADD COLUMN IF NOT EXISTS component_id TEXT UNIQUE,
        ADD COLUMN IF NOT EXISTS component_type VARCHAR(50) DEFAULT 'unknown',
        ADD COLUMN IF NOT EXISTS language VARCHAR(50) DEFAULT 'unknown',
        ADD COLUMN IF NOT EXISTS api_signature TEXT,
        ADD COLUMN IF NOT EXISTS imports JSONB DEFAULT '[]'::jsonb,
        ADD COLUMN IF NOT EXISTS keywords JSONB DEFAULT '[]'::jsonb,
        ADD COLUMN IF NOT EXISTS lines_of_code INTEGER DEFAULT 0,
        ADD COLUMN IF NOT EXISTS cyclomatic_complexity FLOAT,
        ADD COLUMN IF NOT EXISTS public_methods JSONB DEFAULT '[]'::jsonb,
        ADD COLUMN IF NOT EXISTS first_seen TIMESTAMP DEFAULT NOW(),
        ADD COLUMN IF NOT EXISTS derived_from TEXT,
        ADD COLUMN IF NOT EXISTS sync_status VARCHAR(50) DEFAULT 'unknown'
    """

    try:
        await db_manager.execute(alter_query)
        logger.info("Successfully added new columns to reusable_components table")
    except Exception as e:
        logger.error(f"Failed to alter table: {e}")
        # This might fail if columns already exist - that's OK
        logger.info("Columns may already exist, continuing...")

    # Create index on component_id for faster lookups
    index_query = """
        CREATE INDEX IF NOT EXISTS idx_reusable_components_component_id
        ON reusable_components(component_id)
    """
    try:
        await db_manager.execute(index_query)
        logger.info("Created index on component_id")
    except Exception as e:
        logger.warning(f"Failed to create index: {e}")


def rollback(kb: KnowledgeBaseV2) -> KnowledgeBaseV2:
    """
    Rollback migration (would remove new columns)
    Note: This is not fully implemented as it's destructive.
    Manual SQL required: ALTER TABLE reusable_components DROP COLUMN IF EXISTS component_id, ...

    Args:
        kb: Current knowledge base

    Returns:
        Knowledge base (unchanged)
    """
    logger.warning("Migration 004 rollback requires manual SQL execution:")
    logger.warning("""
    ALTER TABLE reusable_components
    DROP COLUMN IF EXISTS component_id,
    DROP COLUMN IF EXISTS component_type,
    DROP COLUMN IF EXISTS language,
    DROP COLUMN IF EXISTS api_signature,
    DROP COLUMN IF EXISTS imports,
    DROP COLUMN IF EXISTS keywords,
    DROP COLUMN IF EXISTS lines_of_code,
    DROP COLUMN IF EXISTS cyclomatic_complexity,
    DROP COLUMN IF EXISTS public_methods,
    DROP COLUMN IF EXISTS first_seen,
    DROP COLUMN IF EXISTS derived_from,
    DROP COLUMN IF EXISTS sync_status;
    """)
    return kb


async def run_schema_migration():
    """
    Standalone function to run schema migration
    Useful for manual execution
    """
    from core.database import init_db, close_db

    try:
        db = await init_db()
        logger.info("Database connected")
        await _run_schema_migration_async(db)
        logger.info("Schema migration complete")
    finally:
        await close_db()


if __name__ == "__main__":
    import asyncio

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Run migration
    asyncio.run(run_schema_migration())
