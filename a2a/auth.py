"""
Authentication Module

Flexible authentication supporting both Workload Identity and Service Account.
Handles A2A authentication for protected skills.
"""

import os
import json
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware


class AuthConfig:
    """Authentication configuration"""

    def __init__(self):
        self.auth_mode = os.environ.get("AUTH_MODE", "workload_identity")
        self.service_account_json = os.environ.get("SERVICE_ACCOUNT_JSON")
        self.allowed_service_accounts = [
            sa.strip() for sa in os.environ.get("ALLOWED_SERVICE_ACCOUNTS", "").split(",")
            if sa.strip()
        ]
        self.require_auth_for_write = os.environ.get("REQUIRE_AUTH_FOR_WRITE", "true").lower() == "true"

    def get_credentials(self):
        """Get credentials based on auth mode"""
        if self.auth_mode == "service_account" and self.service_account_json:
            from google.oauth2 import service_account

            # Load from JSON string or file path
            if self.service_account_json.startswith("{"):
                # JSON string
                creds_dict = json.loads(self.service_account_json)
                return service_account.Credentials.from_service_account_info(creds_dict)
            else:
                # File path
                return service_account.Credentials.from_service_account_file(
                    self.service_account_json
                )
        else:
            # Workload Identity Federation (default on Cloud Run)
            from google.auth import default as get_default_credentials
            credentials, project = get_default_credentials()
            return credentials


def verify_a2a_auth(auth_header: Optional[str], config: AuthConfig) -> bool:
    """
    Verify A2A authentication

    For authenticated skills:
    1. Extract token from Authorization header
    2. Verify token signature
    3. Check service account is in allowed list

    Args:
        auth_header: Authorization header value
        config: AuthConfig object

    Returns:
        True if authenticated, False otherwise
    """

    if not config.require_auth_for_write:
        return True  # Auth disabled

    if not auth_header:
        return False

    if not auth_header.startswith("Bearer "):
        return False

    token = auth_header[7:]  # Remove "Bearer "

    try:
        # Verify Google ID token
        from google.oauth2 import id_token
        from google.auth.transport import requests

        request = requests.Request()
        claims = id_token.verify_oauth2_token(token, request)

        # Check if service account is allowed
        email = claims.get("email")

        # If no allowed list specified, allow all authenticated requests
        if not config.allowed_service_accounts:
            print(f"Auth: Allowing authenticated request from {email} (no allowlist configured)")
            return True

        if email in config.allowed_service_accounts:
            print(f"Auth: Allowed service account: {email}")
            return True

        print(f"Auth: Service account {email} not in allowed list")
        return False

    except Exception as e:
        print(f"Auth verification failed: {e}")
        return False


class AuthMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for authentication

    Checks authentication for protected endpoints.
    """

    def __init__(self, app, config: AuthConfig):
        super().__init__(app)
        self.config = config

    async def dispatch(self, request: Request, call_next):
        # Allow health checks and agent card without auth
        if request.url.path in ["/health", "/.well-known/agent.json"]:
            return await call_next(request)

        # For A2A execute endpoint, check skill-specific auth
        if request.url.path == "/a2a/execute":
            # Authentication will be checked in the handler based on skill_id
            pass

        # Continue to next middleware/handler
        response = await call_next(request)
        return response


def require_auth(skill_id: str, config: AuthConfig):
    """
    Decorator to require authentication for specific skills

    Args:
        skill_id: Skill identifier
        config: AuthConfig object

    Returns:
        Decorator function
    """
    # Skills that require authentication
    PROTECTED_SKILLS = ["add_lesson_learned"]

    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Check if this skill requires auth
            if skill_id in PROTECTED_SKILLS:
                auth_header = request.headers.get("Authorization")

                if not verify_a2a_auth(auth_header, config):
                    return JSONResponse(
                        status_code=401,
                        content={
                            "error": "Authentication required",
                            "message": f"Skill '{skill_id}' requires A2A authentication",
                            "skill": skill_id
                        }
                    )

            return await func(request, *args, **kwargs)

        return wrapper

    return decorator


def is_skill_protected(skill_id: str) -> bool:
    """
    Check if a skill requires authentication

    Args:
        skill_id: Skill identifier

    Returns:
        True if skill requires authentication
    """
    PROTECTED_SKILLS = ["add_lesson_learned"]
    return skill_id in PROTECTED_SKILLS
