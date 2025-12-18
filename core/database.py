"""
Database Connection Module for PostgreSQL with pgvector

Handles:
- AsyncPG connection pooling
- Vector embedding operations
- Database initialization
- Health checks
"""

import os
import asyncpg
import logging
import asyncio
import ssl
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages PostgreSQL database connections with pgvector support"""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        min_size: int = 2,
        max_size: int = 10,
    ):
        """
        Initialize database manager

        Args:
            host: PostgreSQL host (defaults to POSTGRES_HOST env var)
            port: PostgreSQL port (defaults to POSTGRES_PORT env var)
            database: Database name (defaults to POSTGRES_DB env var)
            user: Database user (defaults to POSTGRES_USER env var)
            password: Database password (defaults to POSTGRES_PASSWORD env var)
            min_size: Minimum pool size
            max_size: Maximum pool size
        """
        self.host = host or os.getenv("POSTGRES_HOST", "localhost")
        self.port = port or int(os.getenv("POSTGRES_PORT", "5432"))
        self.database = database or os.getenv("POSTGRES_DB", "devnexus")
        self.user = user or os.getenv("POSTGRES_USER", "devnexus")
        self.password = password or os.getenv("POSTGRES_PASSWORD", "")

        self.min_size = min_size
        self.max_size = max_size
        self.pool: Optional[asyncpg.Pool] = None

        # Check if PostgreSQL should be used
        self.enabled = os.getenv("USE_POSTGRESQL", "false").lower() == "true"

    async def connect(self) -> None:
        """Establish connection pool to PostgreSQL"""
        if not self.enabled:
            logger.info("PostgreSQL is disabled (USE_POSTGRESQL=false)")
            return

        if self.pool is not None:
            logger.warning("Database pool already exists")
            return

        # Try connecting with exponential backoff to tolerate transient network/startup races
        max_attempts = 6
        delay = 1

        # Configure SSL behaviour from environment
        ssl_mode = os.getenv("POSTGRES_SSLMODE", "disable").lower()
        ssl_no_verify = os.getenv("POSTGRES_SSL_NO_VERIFY", "false").lower() in (
            "1",
            "true",
            "yes",
        )
        ssl_arg = None
        if ssl_mode in ("disable", "false", "0"):
            ssl_arg = False
        elif ssl_mode in ("require", "true", "1"):
            if ssl_no_verify:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                ssl_arg = ctx
            else:
                ssl_arg = ssl.create_default_context()
        else:
            # Let asyncpg default behaviour decide
            ssl_arg = None

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(
                    f"Connecting to PostgreSQL at {self.host}:{self.port}/{self.database} (attempt {attempt}/{max_attempts})"
                )
                logger.info(f"asyncpg ssl argument: {ssl_arg!r}")

                try:
                    self.pool = await asyncpg.create_pool(
                        host=self.host,
                        port=self.port,
                        database=self.database,
                        user=self.user,
                        password=self.password,
                        ssl=ssl_arg,
                        min_size=self.min_size,
                        max_size=self.max_size,
                        command_timeout=60,
                        server_settings={
                            "application_name": "dev-nexus-a2a",
                        },
                    )
                except Exception as e:
                    # If this looks like an SSL negotiation failure, try a one-time fallback without SSL
                    err_text = str(e).lower()
                    logger.error(f"asyncpg.create_pool failed (ssl={ssl_arg!r}): {e}")
                    if ssl_arg not in (False,) and ("ssl" in err_text or "certificate" in err_text or "tls" in err_text):
                        logger.warning("Detected SSL-related failure, retrying once with ssl=False")
                        try:
                            self.pool = await asyncpg.create_pool(
                                host=self.host,
                                port=self.port,
                                database=self.database,
                                user=self.user,
                                password=self.password,
                                ssl=False,
                                min_size=self.min_size,
                                max_size=self.max_size,
                                command_timeout=60,
                                server_settings={
                                    "application_name": "dev-nexus-a2a",
                                },
                            )
                        except Exception as e2:
                            logger.error(f"Fallback (ssl=False) also failed: {e2}")
                            raise
                    else:
                        raise
                    host=self.host,
                    port=self.port,
                    database=self.database,
                    user=self.user,
                    password=self.password,
                    ssl=ssl_arg,
                    min_size=self.min_size,
                    max_size=self.max_size,
                    command_timeout=60,
                    server_settings={
                        "application_name": "dev-nexus-a2a",
                    },
                )

                # Verify pgvector extension is available
                async with self.pool.acquire() as conn:
                    result = await conn.fetchrow(
                        "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
                    )
                    if result:
                        logger.info(f"pgvector extension detected: v{result['extversion']}")
                    else:
                        logger.warning("pgvector extension not found")

                logger.info("Database connection pool established")
                return

            except Exception as e:
                logger.error(f"Failed to connect to PostgreSQL (attempt {attempt}): {e}")
                # Close pool if partially created
                try:
                    if self.pool is not None:
                        await self.pool.close()
                        self.pool = None
                except Exception:
                    pass

                if attempt == max_attempts:
                    logger.error("Exceeded max connection attempts to PostgreSQL — giving up")
                    raise

                logger.info(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
                delay = min(delay * 2, 30)

    async def disconnect(self) -> None:
        """Close connection pool"""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            logger.info("Database connection pool closed")

    @asynccontextmanager
    async def acquire(self):
        """Context manager for acquiring a connection from pool"""
        if not self.enabled or self.pool is None:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as connection:
            yield connection

    async def health_check(self) -> Dict[str, Any]:
        """
        Check database health

        Returns:
            Dictionary with health status
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "PostgreSQL is not enabled",
            }

        if self.pool is None:
            return {
                "status": "disconnected",
                "message": "No active connection pool",
            }

        try:
            async with self.pool.acquire() as conn:
                # Test basic query
                version = await conn.fetchval("SELECT version()")

                # Check pgvector
                pgvector = await conn.fetchrow(
                    "SELECT extversion FROM pg_extension WHERE extname = 'vector'"
                )

                # Get pool stats
                pool_stats = {
                    "size": self.pool.get_size(),
                    "free": self.pool.get_idle_size(),
                    "min": self.pool.get_min_size(),
                    "max": self.pool.get_max_size(),
                }

                return {
                    "status": "healthy",
                    "version": version.split(",")[0],  # Shorten version string
                    "pgvector_version": pgvector["extversion"] if pgvector else None,
                    "pool": pool_stats,
                    "host": self.host,
                    "database": self.database,
                }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
            }

    async def execute(self, query: str, *args) -> str:
        """
        Execute a SQL command (INSERT, UPDATE, DELETE)

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Status message
        """
        if not self.enabled or self.pool is None:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query: str, *args) -> List[asyncpg.Record]:
        """
        Fetch multiple rows

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            List of records
        """
        if not self.enabled or self.pool is None:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def fetchrow(self, query: str, *args) -> Optional[asyncpg.Record]:
        """
        Fetch single row

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single record or None
        """
        if not self.enabled or self.pool is None:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        """
        Fetch single value

        Args:
            query: SQL query
            *args: Query parameters

        Returns:
            Single value
        """
        if not self.enabled or self.pool is None:
            raise RuntimeError("Database not connected")

        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    # ============================================
    # Vector Operations (pgvector)
    # ============================================

    async def insert_pattern_with_embedding(
        self,
        repo_id: int,
        name: str,
        description: str,
        context: str,
        embedding: Optional[List[float]] = None,
    ) -> int:
        """
        Insert pattern with optional embedding

        Args:
            repo_id: Repository ID
            name: Pattern name
            description: Pattern description
            context: Pattern context
            embedding: Vector embedding (1536 dimensions for OpenAI)

        Returns:
            Inserted pattern ID
        """
        query = """
            INSERT INTO patterns (repo_id, name, description, context, embedding)
            VALUES ($1, $2, $3, $4, $5::vector)
            ON CONFLICT (repo_id, name)
            DO UPDATE SET
                description = EXCLUDED.description,
                context = EXCLUDED.context,
                embedding = EXCLUDED.embedding
            RETURNING id
        """
        return await self.fetchval(
            query, repo_id, name, description, context, embedding
        )

    async def find_similar_patterns(
        self,
        embedding: List[float],
        limit: int = 10,
        threshold: float = 0.8,
        exclude_repo_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find similar patterns using vector similarity

        Args:
            embedding: Query embedding vector
            limit: Maximum number of results
            threshold: Minimum similarity threshold (0-1)
            exclude_repo_id: Optional repo ID to exclude

        Returns:
            List of similar patterns with similarity scores
        """
        query = """
            SELECT
                p.id,
                p.name,
                p.description,
                p.context,
                p.repo_id,
                r.name as repo_name,
                1 - (p.embedding <=> $1::vector) as similarity
            FROM patterns p
            JOIN repositories r ON p.repo_id = r.id
            WHERE p.embedding IS NOT NULL
                AND 1 - (p.embedding <=> $1::vector) >= $2
                AND ($3::integer IS NULL OR p.repo_id != $3)
            ORDER BY p.embedding <=> $1::vector
            LIMIT $4
        """

        rows = await self.fetch(query, embedding, threshold, exclude_repo_id, limit)

        return [
            {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "context": row["context"],
                "repo_id": row["repo_id"],
                "repo_name": row["repo_name"],
                "similarity": float(row["similarity"]),
            }
            for row in rows
        ]

    async def update_pattern_embedding(
        self, pattern_id: int, embedding: List[float]
    ) -> None:
        """
        Update embedding for existing pattern

        Args:
            pattern_id: Pattern ID
            embedding: Vector embedding
        """
        query = "UPDATE patterns SET embedding = $1::vector WHERE id = $2"
        await self.execute(query, embedding, pattern_id)

    async def get_patterns_without_embeddings(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get patterns that don't have embeddings yet

        Args:
            limit: Maximum number of patterns to return

        Returns:
            List of patterns without embeddings
        """
        query = """
            SELECT
                p.id,
                p.name,
                p.description,
                p.context,
                p.repo_id,
                r.name as repo_name
            FROM patterns p
            JOIN repositories r ON p.repo_id = r.id
            WHERE p.embedding IS NULL
            LIMIT $1
        """

        rows = await self.fetch(query, limit)

        return [
            {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "context": row["context"],
                "repo_id": row["repo_id"],
                "repo_name": row["repo_name"],
            }
            for row in rows
        ]


# Singleton instance
_db_manager: Optional[DatabaseManager] = None


def get_db() -> DatabaseManager:
    """Get database manager singleton"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


async def init_db() -> DatabaseManager:
    """Initialize database connection"""
    db = get_db()
    await db.connect()
    return db


async def close_db() -> None:
    """Close database connection"""
    db = get_db()
    await db.disconnect()
