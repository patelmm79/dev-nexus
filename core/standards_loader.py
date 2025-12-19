"""
Standards Loader

Loads and parses architectural standards documents for validation.
Standards are loaded once at server initialization and cached in memory.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import os
import requests

logger = logging.getLogger(__name__)


@dataclass
class ValidationRule:
    """Single validation rule extracted from a standards document"""
    rule_id: str
    category: str
    severity: str  # critical, high, medium, low
    description: str
    check_type: str  # file_exists, file_contains, file_size, section_exists, etc.
    check_params: Dict[str, Any] = field(default_factory=dict)
    recommendation: str = ""


@dataclass
class ParsedStandard:
    """Parsed standard document with validation rules"""
    category: str
    title: str
    required_files: List[str] = field(default_factory=list)
    required_sections: Dict[str, List[str]] = field(default_factory=dict)  # file -> sections
    validation_rules: List[ValidationRule] = field(default_factory=list)
    documentation_content: str = ""


class StandardsLoader:
    """
    Load and parse all architectural standards documents

    Loads standards files at initialization (read-only filesystem access).
    Standards are then used by validators via GitHub API to check repositories.
    """

    # Mapping of standard category to file path
    STANDARDS_MAPPING = {
        "documentation": "docs/DOCUMENTATION_STANDARDS.md",
        "license": "docs/LICENSE_STANDARD.md",
        "terraform_init": "TERRAFORM_UNIFIED_INIT.md",
        "multi_env": "MULTI_ENV_SETUP.md",
        "terraform_state": "TERRAFORM_STATE_MANAGEMENT.md",
        "disaster_recovery": "DISASTER_RECOVERY.md",
        "deployment": "DEPLOYMENT.md",
        "postgresql": "docs/POSTGRESQL_SETUP.md",
        "ci_cd": "cloudbuild.yaml",
        "containerization": "Dockerfile",
    }

    def __init__(self, repo_root: str):
        """
        Initialize standards loader

        Args:
            repo_root: Path to repository root directory
        """
        self.repo_root = Path(repo_root)
        self.standards: Dict[str, ParsedStandard] = {}

        logger.info(f"Loading standards from {self.repo_root}")
        self._load_all_standards()
        logger.info(f"Loaded {len(self.standards)} standard categories")

    def _load_all_standards(self) -> None:
        """Load and parse all standards documents"""
        for category, filepath in self.STANDARDS_MAPPING.items():
            try:
                file_path = self.repo_root / filepath
                content = None

                # Try local file first
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                    logger.info(f"Loaded local standard: {category}")
                else:
                    # Fall back to GitHub for Cloud Run deployments
                    logger.info(f"Local file not found, fetching from GitHub: {filepath}")
                    content = self._fetch_standard_from_github(filepath)

                if content:
                    parsed = self._parse_standard(category, content)
                    self.standards[category] = parsed
                    logger.info(f"Loaded standard: {category} ({len(parsed.validation_rules)} rules)")
                else:
                    logger.warning(f"Could not load standard {category} from local or GitHub")
            except Exception as e:
                logger.error(f"Failed to load standard {category}: {e}")

    def _fetch_standard_from_github(self, filepath: str) -> Optional[str]:
        """
        Fetch standard document from GitHub repository

        Used as fallback when local files aren't available (e.g., Cloud Run deployment).
        Fetches from patelmm79/dev-nexus main branch.

        Args:
            filepath: Path to file in repository (e.g., "DEPLOYMENT.md" or "docs/LICENSE_STANDARD.md")

        Returns:
            File content as string, or None if fetch fails
        """
        try:
            github_token = os.environ.get("GITHUB_TOKEN")
            if not github_token:
                logger.warning("GITHUB_TOKEN not set, cannot fetch standards from GitHub")
                return None

            url = f"https://raw.githubusercontent.com/patelmm79/dev-nexus/main/{filepath}"
            headers = {"Authorization": f"token {github_token}"}

            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                logger.info(f"Successfully fetched {filepath} from GitHub")
                return response.text
            else:
                logger.warning(f"Failed to fetch {filepath} from GitHub: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching {filepath} from GitHub: {e}")
            return None

    def _parse_standard(self, category: str, content: str) -> ParsedStandard:
        """
        Parse standard document into validation rules

        Each standard is parsed to extract:
        - Required files
        - Required sections
        - Validation rules with specific checks

        Args:
            category: Standard category name
            content: File content

        Returns:
            ParsedStandard with extracted validation rules
        """
        parsed = ParsedStandard(
            category=category,
            title=self._extract_title(content),
            documentation_content=content
        )

        # Category-specific parsing
        if category == "license":
            parsed.required_files = ["LICENSE", "README.md"]
            parsed.validation_rules = self._parse_license_standard(content)

        elif category == "documentation":
            parsed.required_files = ["README.md", "CLAUDE.md"]
            parsed.validation_rules = self._parse_documentation_standard(content)

        elif category == "terraform_init":
            parsed.required_files = ["terraform/scripts/terraform-init-unified.sh", "terraform/main.tf"]
            parsed.validation_rules = self._parse_terraform_init_standard(content)

        elif category == "multi_env":
            parsed.required_files = ["terraform/dev.tfvars", "terraform/staging.tfvars", "terraform/prod.tfvars"]
            parsed.validation_rules = self._parse_multi_env_standard(content)

        elif category == "terraform_state":
            parsed.required_files = ["terraform/main.tf", "terraform/scripts/backup-terraform-state.sh"]
            parsed.validation_rules = self._parse_terraform_state_standard(content)

        elif category == "disaster_recovery":
            parsed.required_files = ["DISASTER_RECOVERY.md", "scripts/backup-postgres.sh"]
            parsed.validation_rules = self._parse_disaster_recovery_standard(content)

        elif category == "deployment":
            parsed.required_files = ["DEPLOYMENT.md", "scripts/setup-secrets.sh"]
            parsed.validation_rules = self._parse_deployment_standard(content)

        elif category == "postgresql":
            parsed.required_files = ["docs/POSTGRESQL_SETUP.md", "terraform/postgres.tf"]
            parsed.validation_rules = self._parse_postgresql_standard(content)

        elif category == "ci_cd":
            parsed.required_files = ["cloudbuild.yaml"]
            parsed.validation_rules = self._parse_ci_cd_standard(content)

        elif category == "containerization":
            parsed.required_files = ["Dockerfile"]
            parsed.validation_rules = self._parse_containerization_standard(content)

        return parsed

    def _extract_title(self, content: str) -> str:
        """Extract title from markdown content"""
        for line in content.split('\n'):
            if line.startswith('# '):
                return line[2:].strip()
        return "Unknown"

    def _parse_license_standard(self, content: str) -> List[ValidationRule]:
        """Parse GPL v3.0 license standard"""
        return [
            ValidationRule(
                rule_id="license_001",
                category="license",
                severity="critical",
                description="LICENSE file must exist in repository root",
                check_type="file_exists",
                check_params={"path": "LICENSE"},
                recommendation="Add LICENSE file with complete GPL v3.0 text (minimum 30KB)"
            ),
            ValidationRule(
                rule_id="license_002",
                category="license",
                severity="high",
                description="LICENSE file must be at least 30KB (complete GPL v3.0 text)",
                check_type="file_size",
                check_params={"path": "LICENSE", "min_size": 30000},
                recommendation="Replace with complete GPL v3.0 LICENSE text (at least 30KB)"
            ),
            ValidationRule(
                rule_id="license_003",
                category="license",
                severity="critical",
                description="LICENSE must contain GNU GPL v3.0 text",
                check_type="file_contains",
                check_params={"path": "LICENSE", "pattern": "GNU GENERAL PUBLIC LICENSE"},
                recommendation="Ensure LICENSE contains full GPL v3.0 text with 'GNU GENERAL PUBLIC LICENSE'"
            ),
            ValidationRule(
                rule_id="license_004",
                category="license",
                severity="medium",
                description="README.md should include GPL v3.0 badge",
                check_type="file_contains",
                check_params={"path": "README.md", "pattern": "GPL|GPLv3|GPL-3.0"},
                recommendation="Add GPL v3.0 license badge to README.md"
            ),
        ]

    def _parse_documentation_standard(self, content: str) -> List[ValidationRule]:
        """Parse documentation standards"""
        return [
            ValidationRule(
                rule_id="docs_001",
                category="documentation",
                severity="high",
                description="All documentation must be updated after major changes",
                check_type="section_exists",
                check_params={"path": "CLAUDE.md", "section": "Overview"},
                recommendation="Ensure CLAUDE.md has complete Overview section"
            ),
            ValidationRule(
                rule_id="docs_002",
                category="documentation",
                severity="high",
                description="README must have clear project description",
                check_type="section_exists",
                check_params={"path": "README.md", "section": "Overview"},
                recommendation="Add Overview section to README.md"
            ),
            ValidationRule(
                rule_id="docs_003",
                category="documentation",
                severity="medium",
                description="Documentation should include command context (WHERE, WHAT, OUTPUT)",
                check_type="file_contains",
                check_params={"path": "CLAUDE.md", "pattern": "commands"},
                recommendation="Add command context documentation (WHERE to run, WHAT it does, EXPECTED output)"
            ),
        ]

    def _parse_terraform_init_standard(self, content: str) -> List[ValidationRule]:
        """Parse Terraform unified initialization standard"""
        return [
            ValidationRule(
                rule_id="tf_init_001",
                category="terraform_init",
                severity="high",
                description="Unified terraform initialization script must exist",
                check_type="file_exists",
                check_params={"path": "terraform/scripts/terraform-init-unified.sh"},
                recommendation="Create terraform/scripts/terraform-init-unified.sh per TERRAFORM_UNIFIED_INIT.md"
            ),
            ValidationRule(
                rule_id="tf_init_002",
                category="terraform_init",
                severity="critical",
                description="main.tf must have GCS backend configuration",
                check_type="file_contains",
                check_params={"path": "terraform/main.tf", "pattern": 'backend "gcs"'},
                recommendation="Configure GCS backend in terraform/main.tf"
            ),
            ValidationRule(
                rule_id="tf_init_003",
                category="terraform_init",
                severity="medium",
                description="Backend bucket should not be hardcoded (use CLI flags)",
                check_type="file_contains",
                check_params={"path": "terraform/main.tf", "pattern": "bucket\\s*="},
                recommendation="Remove hardcoded bucket value from backend block, use CLI configuration"
            ),
        ]

    def _parse_multi_env_standard(self, content: str) -> List[ValidationRule]:
        """Parse multi-environment terraform standard"""
        return [
            ValidationRule(
                rule_id="multi_env_001",
                category="multi_env",
                severity="high",
                description="dev.tfvars must exist for development environment",
                check_type="file_exists",
                check_params={"path": "terraform/dev.tfvars"},
                recommendation="Create terraform/dev.tfvars per MULTI_ENV_SETUP.md"
            ),
            ValidationRule(
                rule_id="multi_env_002",
                category="multi_env",
                severity="high",
                description="staging.tfvars must exist for staging environment",
                check_type="file_exists",
                check_params={"path": "terraform/staging.tfvars"},
                recommendation="Create terraform/staging.tfvars per MULTI_ENV_SETUP.md"
            ),
            ValidationRule(
                rule_id="multi_env_003",
                category="multi_env",
                severity="high",
                description="prod.tfvars must exist for production environment",
                check_type="file_exists",
                check_params={"path": "terraform/prod.tfvars"},
                recommendation="Create terraform/prod.tfvars per MULTI_ENV_SETUP.md"
            ),
        ]

    def _parse_terraform_state_standard(self, content: str) -> List[ValidationRule]:
        """Parse Terraform state management standard"""
        return [
            ValidationRule(
                rule_id="tf_state_001",
                category="terraform_state",
                severity="critical",
                description="Remote state backend must be configured",
                check_type="file_contains",
                check_params={"path": "terraform/main.tf", "pattern": "backend"},
                recommendation="Configure remote terraform backend per TERRAFORM_STATE_MANAGEMENT.md"
            ),
            ValidationRule(
                rule_id="tf_state_002",
                category="terraform_state",
                severity="high",
                description="Backup script should exist for disaster recovery",
                check_type="file_exists",
                check_params={"path": "scripts/backup-terraform-state.sh"},
                recommendation="Create terraform state backup script per TERRAFORM_STATE_MANAGEMENT.md"
            ),
        ]

    def _parse_disaster_recovery_standard(self, content: str) -> List[ValidationRule]:
        """Parse disaster recovery standard"""
        return [
            ValidationRule(
                rule_id="dr_001",
                category="disaster_recovery",
                severity="high",
                description="DISASTER_RECOVERY.md documentation must exist",
                check_type="file_exists",
                check_params={"path": "DISASTER_RECOVERY.md"},
                recommendation="Create DISASTER_RECOVERY.md with recovery procedures"
            ),
            ValidationRule(
                rule_id="dr_002",
                category="disaster_recovery",
                severity="high",
                description="Database backup script must exist",
                check_type="file_exists",
                check_params={"path": "scripts/backup-postgres.sh"},
                recommendation="Create backup-postgres.sh script per DISASTER_RECOVERY.md"
            ),
        ]

    def _parse_deployment_standard(self, content: str) -> List[ValidationRule]:
        """Parse deployment standard"""
        return [
            ValidationRule(
                rule_id="deploy_001",
                category="deployment",
                severity="high",
                description="DEPLOYMENT.md documentation must exist",
                check_type="file_exists",
                check_params={"path": "DEPLOYMENT.md"},
                recommendation="Create DEPLOYMENT.md with deployment procedures"
            ),
            ValidationRule(
                rule_id="deploy_002",
                category="deployment",
                severity="high",
                description="Secrets setup script must exist",
                check_type="file_exists",
                check_params={"path": "scripts/setup-secrets.sh"},
                recommendation="Create scripts/setup-secrets.sh for secret management setup"
            ),
        ]

    def _parse_postgresql_standard(self, content: str) -> List[ValidationRule]:
        """Parse PostgreSQL standard"""
        return [
            ValidationRule(
                rule_id="pg_001",
                category="postgresql",
                severity="high",
                description="POSTGRESQL_SETUP.md documentation must exist",
                check_type="file_exists",
                check_params={"path": "docs/POSTGRESQL_SETUP.md"},
                recommendation="Create docs/POSTGRESQL_SETUP.md with PostgreSQL setup procedures"
            ),
            ValidationRule(
                rule_id="pg_002",
                category="postgresql",
                severity="high",
                description="Terraform PostgreSQL configuration must exist",
                check_type="file_exists",
                check_params={"path": "terraform/postgres.tf"},
                recommendation="Create terraform/postgres.tf for PostgreSQL infrastructure"
            ),
            ValidationRule(
                rule_id="pg_003",
                category="postgresql",
                severity="medium",
                description="PostgreSQL documentation should mention pgvector extension",
                check_type="file_contains",
                check_params={"path": "docs/POSTGRESQL_SETUP.md", "pattern": "pgvector"},
                recommendation="Document pgvector extension requirement in POSTGRESQL_SETUP.md"
            ),
        ]

    def _parse_ci_cd_standard(self, content: str) -> List[ValidationRule]:
        """Parse CI/CD standard (Cloud Build)"""
        return [
            ValidationRule(
                rule_id="cicd_001",
                category="ci_cd",
                severity="high",
                description="Cloud Build configuration must exist",
                check_type="file_exists",
                check_params={"path": "cloudbuild.yaml"},
                recommendation="Create cloudbuild.yaml per Cloud Build standards"
            ),
            ValidationRule(
                rule_id="cicd_002",
                category="ci_cd",
                severity="medium",
                description="Cloud Build should use multi-stage deployment",
                check_type="file_contains",
                check_params={"path": "cloudbuild.yaml", "pattern": "steps|substitutions"},
                recommendation="Implement multi-stage build in cloudbuild.yaml"
            ),
        ]

    def _parse_containerization_standard(self, content: str) -> List[ValidationRule]:
        """Parse containerization (Docker) standard"""
        return [
            ValidationRule(
                rule_id="docker_001",
                category="containerization",
                severity="high",
                description="Dockerfile must exist",
                check_type="file_exists",
                check_params={"path": "Dockerfile"},
                recommendation="Create Dockerfile for containerization"
            ),
            ValidationRule(
                rule_id="docker_002",
                category="containerization",
                severity="medium",
                description="Dockerfile should use multi-stage build",
                check_type="file_contains",
                check_params={"path": "Dockerfile", "pattern": "FROM.*AS|as builder"},
                recommendation="Implement multi-stage Docker build to minimize image size"
            ),
            ValidationRule(
                rule_id="docker_003",
                category="containerization",
                severity="medium",
                description="Dockerfile should expose port 8080 for Cloud Run",
                check_type="file_contains",
                check_params={"path": "Dockerfile", "pattern": "EXPOSE.*8080|8080"},
                recommendation="Expose port 8080 in Dockerfile for Cloud Run compatibility"
            ),
        ]

    def get_standard(self, category: str) -> Optional[ParsedStandard]:
        """
        Get a parsed standard by category

        Args:
            category: Standard category name

        Returns:
            ParsedStandard or None if not found
        """
        return self.standards.get(category)

    def get_all_standards(self) -> Dict[str, ParsedStandard]:
        """Get all loaded standards"""
        return self.standards.copy()

    def list_categories(self) -> List[str]:
        """Get list of available standard categories"""
        return list(self.standards.keys())
