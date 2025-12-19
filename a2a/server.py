"""
A2A Server - Pattern Discovery Agent (Modular)

FastAPI application serving the Pattern Discovery Agent via A2A protocol.
Uses modular skill architecture with dynamic skill registration.
"""

import os
import sys
import asyncio
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
import logging
import anthropic
from github import Github

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from a2a.config import load_config, validate_config
from a2a.auth import AuthConfig, AuthMiddleware, verify_a2a_auth
from a2a.executor import PatternDiscoveryExecutor
from a2a.registry import get_registry
from core.postgres_repository import PostgresRepository
from core.similarity_finder import SimilarityFinder
from core.integration_service import IntegrationService
from core.database import init_db, close_db, get_db, DatabaseManager

# Initialize logger for this module
logger = logging.getLogger(__name__)

# Import skill modules (they self-register)
from a2a.skills.pattern_query import PatternQuerySkills
from a2a.skills.repository_info import RepositoryInfoSkills
from a2a.skills.knowledge_management import KnowledgeManagementSkills
from a2a.skills.integration import IntegrationSkills
from a2a.skills.documentation_standards import DocumentationStandardsSkills
from a2a.skills.runtime_monitoring import RuntimeMonitoringSkills
from a2a.skills.activity import ActivitySkills
from a2a.skills.architectural_compliance import ArchitecturalComplianceSkills

# Load configuration
config = load_config()

# Validate configuration
try:
    validate_config(config)
except ValueError as e:
    print(f"Configuration error: {e}")
    print("Please check your environment variables")

# Initialize clients
anthropic_client = anthropic.Anthropic(api_key=config.anthropic_api_key)

# Initialize core services
# PostgreSQL database manager
db_manager = DatabaseManager()

# PostgreSQL repository (replaces JSON-based KnowledgeBaseManager)
postgres_repo = PostgresRepository(db_manager)

similarity_finder = SimilarityFinder()
integration_service = IntegrationService()

# Initialize skill registry
registry = get_registry()

# Register all skills
pattern_query_skills = PatternQuerySkills(postgres_repo, similarity_finder)
for skill in pattern_query_skills.get_skills():
    registry.register(skill)

repository_info_skills = RepositoryInfoSkills(postgres_repo)
for skill in repository_info_skills.get_skills():
    registry.register(skill)

knowledge_mgmt_skills = KnowledgeManagementSkills(postgres_repo)
for skill in knowledge_mgmt_skills.get_skills():
    registry.register(skill)

integration_skills = IntegrationSkills(integration_service)
for skill in integration_skills.get_skills():
    registry.register(skill)

# Register documentation standards skills
standards_file_path = Path(__file__).parent.parent / "docs" / "DOCUMENTATION_STANDARDS.md"
doc_standards_skills = DocumentationStandardsSkills(str(standards_file_path))
for skill in doc_standards_skills.get_skills():
    registry.register(skill)

# Register runtime monitoring skills
runtime_monitoring_skills = RuntimeMonitoringSkills(postgres_repo)
for skill in runtime_monitoring_skills.get_skills():
    registry.register(skill)

# Register activity timeline skills
activity_skills = ActivitySkills(postgres_repo)
for skill in activity_skills.get_skills():
    registry.register(skill)

# Register architectural compliance skills
try:
    arch_compliance_skills = ArchitecturalComplianceSkills()
    for skill in arch_compliance_skills.get_skills():
        registry.register(skill)
    logger.info("Registered architectural compliance skills")
except Exception as e:
    logger.warning(f"Failed to register architectural compliance skills: {e}")

# Register component sensibility skills
try:
    from a2a.skills.component_sensibility import ComponentSensibilitySkills
    from core.knowledge_base import KnowledgeBaseManager
    from core.component_analyzer import VectorCacheManager

    # Initialize KnowledgeBaseManager with GitHub client and KB repo
    github_client = Github(config.github_token)
    kb_manager = KnowledgeBaseManager(github_client, config.knowledge_base_repo)

    # Try to initialize VectorCacheManager with PostgreSQL
    # If PostgreSQL is not available, log warning but continue with graceful degradation
    postgres_url = os.environ.get("DATABASE_URL", "postgresql://localhost/devnexus")
    try:
        vector_manager = VectorCacheManager(postgres_url)
        logger.info("PostgreSQL backend initialized for component sensibility")
    except Exception as db_error:
        logger.warning(f"PostgreSQL not available for component sensibility: {db_error}. Skills will work with degraded functionality (no vector caching).")
        # Create a mock vector manager that doesn't require PostgreSQL
        class MockVectorCacheManager:
            def __init__(self, url):
                self.postgres_url = url
                self.vector_cache = {}
            def get_or_create_vector(self, component):
                return None
            def find_similar(self, component, top_k=5, min_similarity=0.5):
                return []
        vector_manager = MockVectorCacheManager(postgres_url)

    component_sensibility_skills = ComponentSensibilitySkills(kb_manager, vector_manager)
    for skill in component_sensibility_skills.get_skills():
        registry.register(skill)
    logger.info("Registered component sensibility skills")
except Exception as e:
    logger.warning(f"Failed to register component sensibility skills: {e}", exc_info=True)

# Initialize executor with registry
executor = PatternDiscoveryExecutor(registry)

# Initialize auth config
auth_config = AuthConfig()

# Create FastAPI app
app = FastAPI(
    title="Pattern Discovery Agent A2A Server",
    description="Automated architectural consistency and pattern discovery across GitHub repositories",
    version="2.0.0"
)

# Temporary request-logging middleware (debug only)
logger = logging.getLogger("a2a.debug")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


@app.middleware("http")
async def request_logger(request: Request, call_next):
    try:
        headers = {
            "origin": request.headers.get("origin"),
            "authorization": "REDACTED" if request.headers.get("authorization") else None,
            "content-type": request.headers.get("content-type"),
            "acr-method": request.headers.get("access-control-request-method"),
            "acr-headers": request.headers.get("access-control-request-headers"),
        }
        logger.info(f"REQ {request.method} {request.url.path} headers={headers}")
    except Exception as e:
        logger.warning(f"Failed to log request: {e}")

    response = await call_next(request)
    try:
        logger.info(f"RESP {request.method} {request.url.path} status={response.status_code}")
    except Exception:
        pass
    return response

# Dynamic CORS middleware: validate and echo allowed origins
def origin_allowed(origin: str) -> bool:
    if not origin:
        return False
    # Exact matches from env-config
    if origin in config.cors_origins:
        return True
    # Allow vercel preview domains (conservative): https://<anything>.vercel.app
    if origin.startswith("https://") and origin.endswith(".vercel.app"):
        return True
    return False


@app.middleware("http")
async def dynamic_cors(request: Request, call_next):
    origin = request.headers.get("origin")
    # Handle preflight OPTIONS early
    if request.method == "OPTIONS":
        headers = {}
        if origin and origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
            headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
            headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        return Response(status_code=204, headers=headers)

    response = await call_next(request)
    if origin and origin_allowed(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    return response

# Add authentication middleware (after CORS handling)
app.add_middleware(AuthMiddleware, config=auth_config)


# ============================================
# Startup and Shutdown Events
# ============================================

async def initialize_database_background():
    """Initialize PostgreSQL connection in background (non-blocking)

    Runs asynchronously without blocking the server startup.
    If connection fails, the service still starts and retries on each request.
    """
    if not db_manager.enabled:
        print("PostgreSQL is disabled (USE_POSTGRESQL=false)")
        return

    try:
        print("[BACKGROUND] Initializing PostgreSQL connection...")
        await db_manager.connect()
        health = await db_manager.health_check()
        if health["status"] == "healthy":
            print(f"[BACKGROUND] ✓ PostgreSQL connected: {health.get('version', 'unknown')}")
            if health.get("pgvector_version"):
                print(f"[BACKGROUND] ✓ pgvector v{health['pgvector_version']} available")
            print("[BACKGROUND] ✓ PostgresRepository ready")
        else:
            print(f"[BACKGROUND] ⚠ PostgreSQL health check failed: {health}")
            print("[BACKGROUND] Will retry on next request")
    except Exception as e:
        print(f"[BACKGROUND] ⚠ PostgreSQL connection failed (will retry on requests): {e}")
        # Don't disable db_manager; let requests retry when they hit the pool


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup (fast, non-blocking)

    Spawns database initialization in background so app can start immediately.
    This allows health checks to work while PostgreSQL is initializing.
    """
    print("Starting Pattern Discovery Agent A2A Server...")
    print(f"✓ Skills registered: {len(registry)}")
    print(f"✓ Config loaded: CORS={len(config.cors_origins)} origins")
    print(f"✓ PostgreSQL enabled: {db_manager.enabled}")

    # Spawn background task to connect to PostgreSQL
    # This doesn't block the app from starting/listening on port 8080
    if db_manager.enabled:
        asyncio.create_task(initialize_database_background())

    print("✓ A2A Server ready - listening on port 8080")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    try:
        await db_manager.disconnect()
        print("✓ Database connections closed")
    except Exception as e:
        print(f"Error closing database: {e}")


@app.get("/.well-known/agent.json")
async def get_agent_card():
    """
    Publish AgentCard at well-known location

    Returns AgentCard with dynamically generated skill definitions from registry.
    """
    agent_card = {
        "name": "pattern_discovery_agent",
        "description": "Automated architectural consistency and pattern discovery across GitHub repositories using Claude AI",
        "version": "2.0.0",
        "url": config.agent_url,
        "capabilities": {
            "streaming": False,
            "multimodal": False,
            "authentication": "optional"
        },
        "skills": registry.to_agent_card_skills(),  # Dynamic skill generation
        "metadata": {
            "repository": "patelmm79/dev-nexus",
            "documentation": "https://github.com/patelmm79/dev-nexus#readme",
            "authentication_note": "Read operations are public. Write operations (add_lesson_learned, update_dependency_info) require A2A authentication.",
            "knowledge_base": config.knowledge_base_repo,
            "external_agents": {
                "dependency_orchestrator": "Coordinates dependency updates and impact analysis",
                "pattern_miner": "Deep pattern extraction and code comparison"
            },
            "architecture": "modular",
            "skill_count": len(registry)
        }
    }

    return JSONResponse(content=agent_card)


@app.post("/a2a/execute")
async def execute_task(request: Request):
    """
    Handle A2A task execution

    Routes requests to appropriate skill handlers via registry.
    """
    try:
        body = await request.json()
        skill_id = body.get("skill_id")
        input_data = body.get("input", {})

        if not skill_id:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing required field: skill_id"}
            )

        # Check authentication for protected skills
        if registry.is_protected(skill_id):
            auth_header = request.headers.get("Authorization")
            if not verify_a2a_auth(auth_header, auth_config):
                return JSONResponse(
                    status_code=401,
                    content={
                        "error": "Authentication required",
                        "message": f"Skill '{skill_id}' requires A2A authentication",
                        "skill": skill_id
                    }
                )

        # Execute skill via executor (which delegates to registry)
        result = await executor.execute(skill_id, input_data)

        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Execution failed: {str(e)}"}
        )


@app.post("/a2a/cancel")
async def cancel_task(request: Request):
    """
    Handle A2A task cancellation
    """
    try:
        body = await request.json()
        task_id = body.get("task_id")

        if not task_id:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing required field: task_id"}
            )

        result = await executor.cancel(task_id)
        return JSONResponse(content=result)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Cancellation failed: {str(e)}"}
        )


@app.get("/health")
async def health_check():
    """
    Health check endpoint for Cloud Run
    """
    health_data = {
        "status": "healthy",
        "service": "pattern-discovery-agent",
        "version": "2.0.0",
        "knowledge_base_repo": config.knowledge_base_repo,
        "skills_registered": len(registry),
        "skills": registry.get_skill_ids()
    }

    # Add database health if enabled (use the actual db_manager instance)
    if db_manager.enabled:
        db_health = await db_manager.health_check()
        health_data["database"] = db_health
        health_data["database_type"] = "postgresql"
        health_data["pgvector_enabled"] = db_health.get("pgvector_version") is not None
    else:
        health_data["database"] = "disabled"
        health_data["database_type"] = "json"

    return health_data


@app.get("/")
async def root():
    """
    Root endpoint with service information
    """
    return {
        "service": "Pattern Discovery Agent A2A Server",
        "version": "2.0.0",
        "architecture": "modular",
        "agent_card": f"{config.agent_url}/.well-known/agent.json",
        "health": f"{config.agent_url}/health",
        "endpoints": {
            "execute": "/a2a/execute",
            "cancel": "/a2a/cancel",
            "agent_card": "/.well-known/agent.json",
            "health": "/health"
        },
        "skills_registered": len(registry),
        "skills": registry.get_skill_ids()
    }


# For local development
if __name__ == "__main__":
    import uvicorn
    port = config.port
    print(f"Starting Pattern Discovery Agent A2A Server on port {port}")
    print(f"AgentCard: http://localhost:{port}/.well-known/agent.json")
    print(f"Health: http://localhost:{port}/health")
    print(f"Skills registered: {len(registry)}")
    print(f"Skills: {', '.join(registry.get_skill_ids())}")
    uvicorn.run(app, host="0.0.0.0", port=port)
