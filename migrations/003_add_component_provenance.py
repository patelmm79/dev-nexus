"""
Migration 003: Add Component Provenance Tracking

This migration:
1. Extracts components from all repositories
2. Generates TF-IDF vectors using pattern-miner
3. Stores vectors in pgvector
4. Initializes component provenance tracking

Safe to run multiple times (idempotent).
"""

import logging
import json
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

from core.component_analyzer import ComponentScanner, VectorCacheManager, CentralityCalculator
from schemas.knowledge_base_v2 import KnowledgeBaseV2, ComponentProvenance, ComponentLocation
from a2a.client import ExternalAgentRegistry

logger = logging.getLogger(__name__)


def migrate(kb: KnowledgeBaseV2, pattern_miner_client: Any = None, postgres_url: str = None) -> KnowledgeBaseV2:
    """
    Run migration to add component provenance tracking

    Args:
        kb: Current knowledge base
        pattern_miner_client: Client for pattern-miner A2A agent (optional)
        postgres_url: PostgreSQL connection URL (required if pgvector enabled)

    Returns:
        Updated knowledge base with component data
    """
    logger.info("Starting migration 003: Add Component Provenance Tracking")

    try:
        # Initialize components
        scanner = ComponentScanner()
        vector_manager = None

        if postgres_url:
            vector_manager = VectorCacheManager(postgres_url, pattern_miner_client)
            logger.info("VectorCacheManager initialized")

        # Extract components from all repositories
        logger.info(f"Scanning {len(kb.repositories)} repositories for components...")
        all_components_by_repo = {}
        all_components_flat = {}

        for repo_name, repo_data in kb.repositories.items():
            try:
                # Get repository path - try common patterns
                repo_path = _get_repository_path(repo_name)
                if not repo_path:
                    logger.warning(f"Could not locate repository path for {repo_name}, skipping component extraction")
                    continue

                logger.info(f"Extracting components from {repo_name}...")
                components = scanner.scan_repository(str(repo_path), repo_name)

                if components:
                    all_components_by_repo[repo_name] = components
                    repo_data.components = components
                    logger.info(f"  Found {len(components)} components in {repo_name}")

                    # Flatten for provenance tracking
                    for comp in components:
                        all_components_flat[comp.component_id] = comp

            except Exception as e:
                logger.error(f"Error extracting components from {repo_name}: {e}", exc_info=True)
                continue

        # Generate vectors if pattern-miner is available
        if vector_manager and all_components_flat:
            logger.info(f"Generating vectors for {len(all_components_flat)} components...")

            # Batch update vectors
            components_list = list(all_components_flat.values())
            vector_results = vector_manager.update_vectors(components_list)

            success_count = sum(1 for v in vector_results.values() if v)
            logger.info(f"Vector generation complete: {success_count}/{len(components_list)} successful")

        # Build component provenance index
        logger.info("Building component provenance index...")
        component_index = _build_component_provenance(all_components_by_repo)

        kb.component_index = component_index
        kb.last_updated = datetime.now()

        logger.info(f"Migration complete. Indexed {len(component_index)} unique components")
        logger.info(f"Component extraction summary:")
        for repo, comps in all_components_by_repo.items():
            logger.info(f"  {repo}: {len(comps)} components")

        return kb

    except Exception as e:
        logger.error(f"Migration 003 failed: {e}", exc_info=True)
        raise


def _get_repository_path(repo_name: str) -> Path:
    """
    Locate repository path on disk

    Tries common patterns:
    - Sibling directories
    - ~/.local/share/dev-nexus/repos/
    - REPOS_PATH environment variable
    """
    import os

    # Try environment variable
    repos_base = os.environ.get("REPOS_PATH")
    if repos_base:
        repo_path = Path(repos_base) / repo_name.split("/")[-1]
        if repo_path.exists():
            return repo_path

    # Try sibling directory pattern
    current_dir = Path(__file__).parent.parent
    repo_dir = current_dir.parent / repo_name.split("/")[-1]
    if repo_dir.exists():
        return repo_dir

    # Try home directory pattern
    home_repos = Path.home() / ".local" / "share" / "dev-nexus" / "repos" / repo_name.split("/")[-1]
    if home_repos.exists():
        return home_repos

    return None


def _build_component_provenance(components_by_repo: Dict[str, List[Any]]) -> Dict[str, ComponentProvenance]:
    """
    Build component provenance index from extracted components

    Identifies:
    - Original implementations
    - Duplicates/diverged copies
    - Usage patterns
    """
    provenance_index = {}
    component_signatures = {}  # Map signatures to component IDs for deduplication

    logger.info("Analyzing component signatures to identify provenance...")

    # First pass: collect all components and their signatures
    for repo_name, components in components_by_repo.items():
        for component in components:
            sig = _generate_component_signature(component)

            if sig not in component_signatures:
                component_signatures[sig] = []

            component_signatures[sig].append({
                "component_id": component.component_id,
                "component": component,
                "repository": repo_name
            })

    # Second pass: build provenance for each component
    for repo_name, components in components_by_repo.items():
        for component in components:
            sig = _generate_component_signature(component)
            instances = component_signatures[sig]

            # Determine if this is original or derived
            is_original = component.sync_status == "original" or len(instances) == 1
            origin_repo = repo_name

            if not is_original and instances:
                # Find oldest instance
                oldest = min(instances, key=lambda x: x["component"].first_seen)
                origin_repo = oldest["repository"]

            # Create provenance entry
            provenance = ComponentProvenance(
                component_id=component.component_id,
                component_name=component.name,
                component_type=component.component_type,
                origin_repository=origin_repo,
                first_seen=component.first_seen,
                locations=[
                    ComponentLocation(
                        repository=inst["repository"],
                        files=inst["component"].files,
                        sync_status="original" if inst["repository"] == origin_repo else "diverged",
                        usage_count=0  # Would be populated from dependency analysis
                    )
                    for inst in instances
                ],
                consolidation_status="unconsolidated"
            )

            provenance_index[component.component_id] = provenance

    logger.info(f"Built provenance for {len(provenance_index)} unique components")

    # Log duplicates discovered
    duplicates = [sigs for sigs in component_signatures.values() if len(sigs) > 1]
    if duplicates:
        logger.info(f"Found {len(duplicates)} component duplications:")
        for dup_group in duplicates:
            primary = dup_group[0]
            logger.info(f"  {primary['component'].name} ({primary['component'].component_type}):")
            for inst in dup_group:
                logger.info(f"    - {inst['repository']}")

    return provenance_index


def _generate_component_signature(component: Any) -> str:
    """
    Generate signature for component similarity detection

    Uses: name, type, public_methods, imports, keywords
    """
    import hashlib

    # Create normalized signature
    sig_parts = [
        component.name.lower(),
        component.component_type,
        "|".join(sorted(component.public_methods or [])),
        "|".join(sorted(component.imports or [])),
        "|".join(sorted(component.keywords or []))
    ]

    sig_str = ":".join(sig_parts)
    return hashlib.sha256(sig_str.encode()).hexdigest()[:16]


def rollback(kb: KnowledgeBaseV2) -> KnowledgeBaseV2:
    """
    Rollback migration (remove component data)

    Args:
        kb: Current knowledge base

    Returns:
        Knowledge base with component data cleared
    """
    logger.info("Rolling back migration 003...")

    # Clear component data
    kb.component_index = {}
    kb.consolidation_history = []

    for repo_data in kb.repositories.values():
        repo_data.components = []

    kb.last_updated = datetime.now()

    logger.info("Rollback complete")
    return kb


if __name__ == "__main__":
    # Testing script
    import os
    from core.knowledge_base import KnowledgeBaseManager

    # Load KB
    kb_path = os.environ.get("KNOWLEDGE_BASE_URL", "knowledge_base.json")
    kb_manager = KnowledgeBaseManager()
    kb = kb_manager.load_from_json(kb_path)

    # Run migration
    postgres_url = os.environ.get("DATABASE_URL", "postgresql://user:pass@localhost/devnexus")
    kb = migrate(kb, postgres_url=postgres_url)

    # Save updated KB
    kb_manager.save_to_json(kb, kb_path)
    logger.info(f"Knowledge base updated: {kb_path}")
