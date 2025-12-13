"""
Configuration Management Module

Centralized configuration with Secret Manager integration for Cloud Run.
Supports both local development and production deployment.
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Application configuration"""

    # Core settings
    agent_url: str
    port: int

    # GitHub settings
    github_token: str
    knowledge_base_repo: str

    # Anthropic settings
    anthropic_api_key: str

    # Authentication
    auth_mode: str  # "workload_identity" or "service_account"
    service_account_json: Optional[str]
    allowed_service_accounts: list
    require_auth_for_write: bool

    # GCP settings
    gcp_project_id: Optional[str]
    gcp_region: str

    # CORS settings
    cors_origins: list


def load_config() -> Config:
    """
    Load configuration from environment variables or Secret Manager

    Priority:
    1. Environment variables (for local dev)
    2. Secret Manager (for Cloud Run)
    3. Defaults

    Returns:
        Config object with all settings
    """

    # Check if running on Cloud Run
    is_cloud_run = os.environ.get("K_SERVICE") is not None

    if is_cloud_run:
        # Running on Cloud Run - load secrets from Secret Manager
        try:
            github_token = get_secret("GITHUB_TOKEN")
            anthropic_api_key = get_secret("ANTHROPIC_API_KEY")
            service_account_json = get_secret("SERVICE_ACCOUNT_JSON", required=False)
        except Exception as e:
            print(f"Warning: Failed to load secrets from Secret Manager: {e}")
            # Fall back to environment variables
            github_token = os.environ.get("GITHUB_TOKEN", "")
            anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
            service_account_json = os.environ.get("SERVICE_ACCOUNT_JSON")
    else:
        # Local development - load from environment
        github_token = os.environ.get("GITHUB_TOKEN", "")
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        service_account_json = os.environ.get("SERVICE_ACCOUNT_JSON")

    # Determine agent URL
    if is_cloud_run:
        # Use Cloud Run service URL
        agent_url = f"https://{os.environ.get('K_SERVICE')}-{os.environ.get('K_REVISION')}.run.app"
    else:
        agent_url = os.environ.get("HOST_OVERRIDE", f"http://localhost:{os.environ.get('PORT', 8080)}")

    # Load CORS origins (comma-separated list)
    cors_origins_str = os.environ.get("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173,https://*.vercel.app")
    cors_origins = [origin.strip() for origin in cors_origins_str.split(",") if origin.strip()]

    return Config(
        agent_url=agent_url,
        port=int(os.environ.get("PORT", 8080)),
        github_token=github_token,
        knowledge_base_repo=os.environ.get("KNOWLEDGE_BASE_REPO", ""),
        anthropic_api_key=anthropic_api_key,
        auth_mode=os.environ.get("AUTH_MODE", "workload_identity"),
        service_account_json=service_account_json,
        allowed_service_accounts=os.environ.get("ALLOWED_SERVICE_ACCOUNTS", "").split(","),
        require_auth_for_write=os.environ.get("REQUIRE_AUTH_FOR_WRITE", "true").lower() == "true",
        gcp_project_id=os.environ.get("GCP_PROJECT_ID"),
        gcp_region=os.environ.get("GCP_REGION", "us-central1"),
        cors_origins=cors_origins
    )


def get_secret(secret_name: str, required: bool = True) -> Optional[str]:
    """
    Fetch secret from Google Cloud Secret Manager

    Args:
        secret_name: Name of the secret
        required: Whether the secret is required

    Returns:
        Secret value as string, or None if not required and not found
    """
    try:
        from google.cloud import secretmanager

        client = secretmanager.SecretManagerServiceClient()
        project_id = os.environ.get("GCP_PROJECT_ID")

        if not project_id:
            if required:
                raise ValueError("GCP_PROJECT_ID environment variable not set")
            return None

        name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
        response = client.access_secret_version(request={"name": name})

        return response.payload.data.decode("UTF-8")

    except Exception as e:
        if required:
            raise Exception(f"Failed to load required secret {secret_name}: {e}")
        print(f"Warning: Optional secret {secret_name} not found: {e}")
        return None


def validate_config(config: Config) -> bool:
    """
    Validate configuration

    Args:
        config: Config object to validate

    Returns:
        True if valid, raises ValueError otherwise
    """
    if not config.github_token:
        raise ValueError("GITHUB_TOKEN is required")

    if not config.anthropic_api_key:
        raise ValueError("ANTHROPIC_API_KEY is required")

    if not config.knowledge_base_repo:
        raise ValueError("KNOWLEDGE_BASE_REPO is required")

    if config.auth_mode not in ["workload_identity", "service_account"]:
        raise ValueError("AUTH_MODE must be 'workload_identity' or 'service_account'")

    if config.auth_mode == "service_account" and not config.service_account_json:
        print("Warning: AUTH_MODE is 'service_account' but SERVICE_ACCOUNT_JSON not set")

    return True
