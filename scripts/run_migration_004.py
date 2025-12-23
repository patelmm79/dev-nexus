#!/usr/bin/env python3
"""
Run Migration 004: Extend Component Schema

This script extends the reusable_components table with additional fields
to support full Component object persistence.

Usage:
    python scripts/run_migration_004.py
"""

import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import init_db, close_db
from migrations.extend_component_schema import _run_schema_migration_async

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Run migration 004"""
    try:
        logger.info("Initializing database connection...")
        db = await init_db()

        if not db.enabled:
            logger.error("PostgreSQL is not enabled. Set USE_POSTGRESQL=true")
            return False

        if not db.pool:
            logger.error("Database connection failed. Check credentials and network.")
            return False

        logger.info("Database connected successfully")

        # Run schema migration
        logger.info("Running migration 004: Extend Component Schema...")
        await _run_schema_migration_async(db)

        logger.info("Migration 004 completed successfully!")
        return True

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return False

    finally:
        await close_db()


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
