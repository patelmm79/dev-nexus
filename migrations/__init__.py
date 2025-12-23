"""
Migrations module for dev-nexus knowledge base

This module contains database migration scripts that extend and update
the PostgreSQL schema over time.

Each migration is idempotent (safe to run multiple times) and can be
rolled back if needed.
"""

import importlib
import logging

logger = logging.getLogger(__name__)


def load_migration(version: int):
    """Load a migration by version number"""
    try:
        # Dynamic import to work around numeric filename limitation
        module_name = f"_{version:03d}_*"
        # Instead, use importlib
        migration_module = importlib.import_module(
            f"migrations._{version:03d}"
        )
        return migration_module
    except ImportError as e:
        logger.error(f"Failed to load migration {version}: {e}")
        return None
