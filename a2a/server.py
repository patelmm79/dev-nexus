"""
A2A Server - Pattern Discovery Agent (Modular)

FastAPI application serving the Pattern Discovery Agent via A2A protocol.
Uses modular skill architecture with dynamic skill registration.
"""

import os
import sys
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import anthropic
from github import Github

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from a2a.config import load_config, validate_config
from a2a.auth import AuthConfig, AuthMiddleware, verify_a2a_auth
from a2a.executor import PatternDiscoveryExecutor
from a2a.registry import get_registry
from core.knowledge_base import KnowledgeBaseManager
from core.similarity_finder import SimilarityFinder
from core.integration_service import IntegrationService

# Import skill modules (they self-register)
from a2a.skills.pattern_query import PatternQuerySkills
from a2a.skills.repository_info import RepositoryInfoSkills
from a2a.skills.knowledge_management import KnowledgeManagementSkills
from a2a.skills.integration import IntegrationSkills
from a2a.skills.documentation_standards import DocumentationStandardsSkills

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
github_client = Github(config.github_token)

# Initialize core services
kb_manager = KnowledgeBaseManager(github_client, config.knowledge_base_repo)
similarity_finder = SimilarityFinder()
integration_service = IntegrationService()

# Initialize skill registry
registry = get_registry()

# Register all skills
pattern_query_skills = PatternQuerySkills(kb_manager, similarity_finder)
for skill in pattern_query_skills.get_skills():
    registry.register(skill)

repository_info_skills = RepositoryInfoSkills(kb_manager)
for skill in repository_info_skills.get_skills():
    registry.register(skill)

knowledge_mgmt_skills = KnowledgeManagementSkills(kb_manager)
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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.add_middleware(AuthMiddleware, config=auth_config)


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
    return {
        "status": "healthy",
        "service": "pattern-discovery-agent",
        "version": "2.0.0",
        "knowledge_base_repo": config.knowledge_base_repo,
        "skills_registered": len(registry),
        "skills": registry.get_skill_ids()
    }


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
