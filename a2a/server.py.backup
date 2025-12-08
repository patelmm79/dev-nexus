"""
A2A Server - Pattern Discovery Agent

FastAPI application serving the Pattern Discovery Agent via A2A protocol.
Publishes AgentCard and handles A2A task execution.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import anthropic
from github import Github

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from a2a.config import load_config, validate_config
from a2a.auth import AuthConfig, AuthMiddleware, verify_a2a_auth, is_skill_protected
from a2a.executor import PatternDiscoveryExecutor
from core.knowledge_base import KnowledgeBaseManager
from core.similarity_finder import SimilarityFinder

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

# Initialize executor
executor = PatternDiscoveryExecutor(kb_manager, similarity_finder)

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

    Returns AgentCard with skill definitions and metadata.
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
        "skills": [
            {
                "id": "query_patterns",
                "name": "Query Similar Patterns",
                "description": "Search for similar architectural patterns across all repositories in the knowledge base",
                "tags": ["search", "patterns", "similarity"],
                "requires_authentication": False,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Keywords to search for (e.g., ['retry', 'exponential backoff'])"
                        },
                        "patterns": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific pattern names to match"
                        },
                        "min_matches": {
                            "type": "integer",
                            "description": "Minimum number of matches required",
                            "default": 1
                        }
                    }
                },
                "examples": [
                    {
                        "input": {"keywords": ["retry", "exponential backoff"]},
                        "description": "Find repositories using retry logic with exponential backoff"
                    }
                ]
            },
            {
                "id": "get_deployment_info",
                "name": "Get Deployment Information",
                "description": "Retrieve deployment scripts, infrastructure details, and lessons learned for a specific repository",
                "tags": ["deployment", "infrastructure", "devops"],
                "requires_authentication": False,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "repository": {
                            "type": "string",
                            "description": "Repository name in format 'owner/repo'"
                        },
                        "include_lessons": {
                            "type": "boolean",
                            "description": "Include lessons learned",
                            "default": True
                        },
                        "include_history": {
                            "type": "boolean",
                            "description": "Include pattern history",
                            "default": False
                        }
                    },
                    "required": ["repository"]
                },
                "examples": [
                    {
                        "input": {"repository": "patelmm79/my-api", "include_lessons": True},
                        "description": "Get deployment info and lessons for my-api repository"
                    }
                ]
            },
            {
                "id": "add_lesson_learned",
                "name": "Add Lesson Learned",
                "description": "Manually record a lesson learned or deployment insight for a repository",
                "tags": ["knowledge", "documentation", "lessons"],
                "requires_authentication": True,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "repository": {
                            "type": "string",
                            "description": "Repository name in format 'owner/repo'"
                        },
                        "category": {
                            "type": "string",
                            "enum": ["performance", "security", "reliability", "cost", "observability"],
                            "description": "Lesson category"
                        },
                        "lesson": {
                            "type": "string",
                            "description": "The lesson learned (clear, actionable statement)"
                        },
                        "context": {
                            "type": "string",
                            "description": "Context or background for this lesson"
                        },
                        "severity": {
                            "type": "string",
                            "enum": ["info", "warning", "critical"],
                            "default": "info"
                        },
                        "recorded_by": {
                            "type": "string",
                            "description": "Who recorded this lesson (optional)"
                        }
                    },
                    "required": ["repository", "category", "lesson", "context"]
                },
                "examples": [
                    {
                        "input": {
                            "repository": "patelmm79/api-client",
                            "category": "performance",
                            "lesson": "Always use connection pooling for HTTP clients",
                            "context": "Experienced socket exhaustion under high load",
                            "severity": "warning"
                        },
                        "description": "Record a performance lesson learned"
                    }
                ]
            },
            {
                "id": "get_repository_list",
                "name": "Get Repository List",
                "description": "Get list of all tracked repositories with optional metadata",
                "tags": ["repositories", "list", "metadata"],
                "requires_authentication": False,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "include_metadata": {
                            "type": "boolean",
                            "description": "Include pattern counts and last updated timestamps",
                            "default": True
                        }
                    }
                },
                "examples": [
                    {
                        "input": {"include_metadata": True},
                        "description": "Get all repositories with metadata"
                    }
                ]
            },
            {
                "id": "get_cross_repo_patterns",
                "name": "Get Cross-Repository Patterns",
                "description": "Find patterns that exist across multiple repositories, useful for identifying common architectural decisions",
                "tags": ["patterns", "cross-repo", "analysis"],
                "requires_authentication": False,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "min_repos": {
                            "type": "integer",
                            "description": "Minimum number of repositories a pattern must appear in",
                            "default": 2
                        },
                        "pattern_type": {
                            "type": "string",
                            "description": "Filter by pattern type (optional)"
                        }
                    }
                },
                "examples": [
                    {
                        "input": {"min_repos": 3},
                        "description": "Find patterns used in 3 or more repositories"
                    }
                ]
            },
            {
                "id": "update_dependency_info",
                "name": "Update Dependency Information",
                "description": "Update dependency graph for a repository - consumers, derivatives, and external dependencies",
                "tags": ["dependencies", "graph", "orchestration"],
                "requires_authentication": True,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "repository": {
                            "type": "string",
                            "description": "Repository name in format 'owner/repo'"
                        },
                        "dependency_info": {
                            "type": "object",
                            "description": "Dependency information",
                            "properties": {
                                "consumers": {
                                    "type": "array",
                                    "description": "List of repositories that depend on this one"
                                },
                                "derivatives": {
                                    "type": "array",
                                    "description": "List of forks or derivatives"
                                },
                                "external_dependencies": {
                                    "type": "array",
                                    "description": "List of external dependencies"
                                }
                            }
                        }
                    },
                    "required": ["repository", "dependency_info"]
                },
                "examples": [
                    {
                        "input": {
                            "repository": "patelmm79/shared-lib",
                            "dependency_info": {
                                "consumers": [{"repository": "patelmm79/api-service", "relationship": "imports"}],
                                "external_dependencies": ["requests", "pydantic"]
                            }
                        },
                        "description": "Update dependency information for shared library"
                    }
                ]
            },
            {
                "id": "health_check_external",
                "name": "Check External Agent Health",
                "description": "Check health status of external A2A agents (dependency-orchestrator, pattern-miner)",
                "tags": ["health", "monitoring", "agents"],
                "requires_authentication": False,
                "input_schema": {
                    "type": "object",
                    "properties": {}
                },
                "examples": [
                    {
                        "input": {},
                        "description": "Check health of all external agents"
                    }
                ]
            }
        ],
        "metadata": {
            "repository": "patelmm79/dev-nexus",
            "documentation": "https://github.com/patelmm79/dev-nexus#readme",
            "authentication_note": "Read operations are public. Write operations (add_lesson_learned, update_dependency_info) require A2A authentication.",
            "knowledge_base": config.knowledge_base_repo,
            "external_agents": {
                "dependency_orchestrator": "Coordinates dependency updates and impact analysis",
                "pattern_miner": "Deep pattern extraction and code comparison"
            }
        }
    }

    return JSONResponse(content=agent_card)


@app.post("/a2a/execute")
async def execute_task(request: Request):
    """
    Handle A2A task execution

    Routes requests to appropriate skill handlers based on skill_id.
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
        if is_skill_protected(skill_id):
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

        # Execute skill
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
        "knowledge_base_repo": config.knowledge_base_repo
    }


@app.get("/")
async def root():
    """
    Root endpoint with service information
    """
    return {
        "service": "Pattern Discovery Agent A2A Server",
        "version": "2.0.0",
        "agent_card": f"{config.agent_url}/.well-known/agent.json",
        "health": f"{config.agent_url}/health",
        "endpoints": {
            "execute": "/a2a/execute",
            "cancel": "/a2a/cancel",
            "agent_card": "/.well-known/agent.json",
            "health": "/health"
        }
    }


# For local development
if __name__ == "__main__":
    import uvicorn
    port = config.port
    print(f"Starting Pattern Discovery Agent A2A Server on port {port}")
    print(f"AgentCard: http://localhost:{port}/.well-known/agent.json")
    print(f"Health: http://localhost:{port}/health")
    uvicorn.run(app, host="0.0.0.0", port=port)
