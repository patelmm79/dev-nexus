"""
Authentication Proxy Server

Securely proxies requests from frontend to A2A server with service account authentication.
Frontend never sees service account credentials.

Architecture:
  Frontend (no creds) → Auth Proxy (with service account) → A2A Server

Usage:
  python auth-proxy/server.py

Environment Variables:
  - SERVICE_ACCOUNT_FILE: Path to service account JSON file
  - A2A_SERVER_URL: URL of the A2A server (default: http://localhost:8080)
  - PROXY_PORT: Port to run proxy on (default: 8000)
  - ALLOWED_ORIGINS: Comma-separated list of allowed CORS origins
"""

import os
import sys
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
SERVICE_ACCOUNT_FILE = os.environ.get("SERVICE_ACCOUNT_FILE", "service-account.json")
A2A_SERVER_URL = os.environ.get("A2A_SERVER_URL", "http://localhost:8080")
PROXY_PORT = int(os.environ.get("PROXY_PORT", 8000))
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://localhost:5174"
).split(",")

# Initialize FastAPI app
app = FastAPI(
    title="A2A Authentication Proxy",
    description="Secure proxy for authenticated A2A requests",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in ALLOWED_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_id_token() -> str:
    """
    Get ID token from service account

    Returns:
        ID token string

    Raises:
        Exception if service account file not found or token generation fails
    """
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import Request as GoogleRequest

        if not os.path.exists(SERVICE_ACCOUNT_FILE):
            raise FileNotFoundError(
                f"Service account file not found: {SERVICE_ACCOUNT_FILE}\n"
                f"Please set SERVICE_ACCOUNT_FILE environment variable"
            )

        # Create ID token credentials
        credentials = service_account.IDTokenCredentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE,
            target_audience=A2A_SERVER_URL
        )

        # Refresh to get token
        google_request = GoogleRequest()
        credentials.refresh(google_request)

        logger.info(f"Generated ID token for service account")
        return credentials.token

    except ImportError as e:
        raise Exception(
            f"Missing required Google auth libraries: {e}\n"
            f"Run: pip install google-auth"
        )
    except Exception as e:
        logger.error(f"Failed to get ID token: {e}")
        raise


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Verify we can generate tokens
        get_id_token()
        return {
            "status": "healthy",
            "service": "auth-proxy",
            "a2a_server": A2A_SERVER_URL
        }
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "A2A Authentication Proxy",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/execute": "Execute A2A skill (authenticated)",
            "GET /api/agent": "Get agent card from A2A server",
            "GET /health": "Health check"
        },
        "a2a_server": A2A_SERVER_URL
    }


@app.post("/api/execute")
async def proxy_execute(request: Request):
    """
    Proxy skill execution to A2A server with authentication

    Request body:
        {
            "skill_id": "skill_name",
            "input": { ... }
        }

    Returns:
        Response from A2A server
    """
    try:
        body = await request.json()

        # Validate request
        if "skill_id" not in body:
            raise HTTPException(
                status_code=400,
                detail="Missing required field: skill_id"
            )

        skill_id = body.get("skill_id")
        logger.info(f"Proxying request for skill: {skill_id}")

        # Get fresh ID token
        try:
            token = get_id_token()
        except Exception as e:
            logger.error(f"Failed to get auth token: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Authentication failed: {str(e)}"
            )

        # Forward to A2A server with authentication
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    f"{A2A_SERVER_URL}/a2a/execute",
                    json=body,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json"
                    }
                )

                logger.info(
                    f"A2A response: {response.status_code} for skill {skill_id}"
                )

                # Return response from A2A server
                return response.json()

            except httpx.TimeoutException:
                raise HTTPException(
                    status_code=504,
                    detail="Request to A2A server timed out"
                )
            except httpx.RequestError as e:
                logger.error(f"Request to A2A server failed: {e}")
                raise HTTPException(
                    status_code=502,
                    detail=f"Failed to connect to A2A server: {str(e)}"
                )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Proxy error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal proxy error: {str(e)}"
        )


@app.get("/api/agent")
async def proxy_agent_card():
    """
    Proxy agent card request to A2A server

    Returns:
        Agent card JSON from A2A server
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{A2A_SERVER_URL}/.well-known/agent.json"
            )
            return response.json()

    except Exception as e:
        logger.error(f"Failed to fetch agent card: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch agent card: {str(e)}"
        )


@app.get("/api/skills")
async def list_available_skills():
    """
    Get list of available skills from A2A server

    Returns:
        List of skills with authentication requirements
    """
    try:
        agent_card = await proxy_agent_card()

        skills = []
        for skill in agent_card.get("skills", []):
            skills.append({
                "skill_id": skill.get("id"),
                "name": skill.get("name"),
                "description": skill.get("description"),
                "requires_auth": skill.get("requiresAuthentication", False),
                "tags": skill.get("tags", [])
            })

        return {
            "skills": skills,
            "total": len(skills)
        }

    except Exception as e:
        logger.error(f"Failed to list skills: {e}")
        raise HTTPException(
            status_code=502,
            detail=f"Failed to list skills: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting auth proxy server")
    logger.info(f"  Proxy port: {PROXY_PORT}")
    logger.info(f"  A2A server: {A2A_SERVER_URL}")
    logger.info(f"  Service account: {SERVICE_ACCOUNT_FILE}")
    logger.info(f"  Allowed origins: {ALLOWED_ORIGINS}")

    # Verify configuration on startup
    try:
        token = get_id_token()
        logger.info("✓ Service account authentication verified")
    except Exception as e:
        logger.error(f"✗ Service account authentication failed: {e}")
        logger.error("  Please check SERVICE_ACCOUNT_FILE configuration")
        sys.exit(1)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PROXY_PORT,
        log_level="info"
    )
