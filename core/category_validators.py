"""
Category-Specific Validators

Implements validation logic for each architectural standard category.
Each validator checks specific requirements from its standards document.
"""

import logging
from typing import Optional

from core.architectural_validator import (
    CategoryValidator,
    CategoryResult,
    RepoStructure,
    Violation,
    ValidationUtils,
)
from core.standards_loader import ParsedStandard, ValidationRule

logger = logging.getLogger(__name__)


class LicenseValidator(CategoryValidator):
    """Validate GPL v3.0 license compliance"""

    def validate(
        self,
        repo_name: str,
        repo_structure: RepoStructure,
        standard: ParsedStandard
    ) -> CategoryResult:
        """Validate license standard"""
        violations = []

        # Check 1: LICENSE file exists
        license_exists = self._check_file_exists(repo_name, "LICENSE")
        if not license_exists:
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="license_001",
                    category="license",
                    severity="critical",
                    description="LICENSE file must exist in repository root",
                    check_type="file_exists",
                    check_params={"path": "LICENSE"},
                    recommendation="Add LICENSE file with complete GPL v3.0 text (minimum 30KB)"
                ),
                file_path="LICENSE"
            ))
        else:
            # Check 2: LICENSE file size >= 30KB
            license_content = self._get_file_content(repo_name, "LICENSE")
            if license_content and len(license_content) < 30000:
                violations.append(self._create_violation(
                    ValidationRule(
                        rule_id="license_002",
                        category="license",
                        severity="high",
                        description="LICENSE file must be at least 30KB (complete GPL v3.0 text)",
                        check_type="file_size",
                        check_params={"path": "LICENSE", "min_size": 30000},
                        recommendation="Replace with complete GPL v3.0 LICENSE text (minimum 30KB)"
                    ),
                    file_path="LICENSE"
                ))

            # Check 3: LICENSE contains GNU GPL v3.0 text
            if license_content and "GNU GENERAL PUBLIC LICENSE" not in license_content:
                violations.append(self._create_violation(
                    ValidationRule(
                        rule_id="license_003",
                        category="license",
                        severity="critical",
                        description="LICENSE must contain GNU GPL v3.0 text",
                        check_type="file_contains",
                        check_params={"path": "LICENSE", "pattern": "GNU GENERAL PUBLIC LICENSE"},
                        recommendation="Ensure LICENSE contains full GPL v3.0 text with 'GNU GENERAL PUBLIC LICENSE'"
                    ),
                    file_path="LICENSE"
                ))

        # Check 4: README has GPL badge
        readme_content = self._get_file_content(repo_name, "README.md")
        if readme_content:
            if not ValidationUtils.check_file_pattern(readme_content, r"GPL|GPLv3|GPL-3\.0"):
                violations.append(self._create_violation(
                    ValidationRule(
                        rule_id="license_004",
                        category="license",
                        severity="medium",
                        description="README.md should include GPL v3.0 badge",
                        check_type="file_contains",
                        check_params={"path": "README.md", "pattern": "GPL|GPLv3|GPL-3.0"},
                        recommendation="Add GPL v3.0 license badge to README.md"
                    ),
                    file_path="README.md"
                ))

        compliance_score = ValidationUtils.calculate_compliance_score(4, violations)

        return CategoryResult(
            category="license",
            passed=len(violations) == 0,
            violations=violations,
            checks_performed=4,
            compliance_score=compliance_score
        )


class DocumentationValidator(CategoryValidator):
    """Validate documentation standards compliance"""

    def validate(
        self,
        repo_name: str,
        repo_structure: RepoStructure,
        standard: ParsedStandard
    ) -> CategoryResult:
        """Validate documentation standard"""
        violations = []

        # Check 1: README.md exists and has content
        readme_content = self._get_file_content(repo_name, "README.md")
        if not readme_content:
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="docs_001",
                    category="documentation",
                    severity="high",
                    description="README.md must exist",
                    check_type="file_exists",
                    check_params={"path": "README.md"},
                    recommendation="Create README.md with project overview"
                ),
                file_path="README.md"
            ))

        # Check 2: CLAUDE.md exists
        claude_content = self._get_file_content(repo_name, "CLAUDE.md")
        if not claude_content:
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="docs_002",
                    category="documentation",
                    severity="high",
                    description="CLAUDE.md must exist",
                    check_type="file_exists",
                    check_params={"path": "CLAUDE.md"},
                    recommendation="Create CLAUDE.md with architecture documentation"
                ),
                file_path="CLAUDE.md"
            ))
        else:
            # Check CLAUDE.md has Overview section
            if not ValidationUtils.check_section_exists(claude_content, "Overview"):
                violations.append(self._create_violation(
                    ValidationRule(
                        rule_id="docs_003",
                        category="documentation",
                        severity="medium",
                        description="CLAUDE.md should have Overview section",
                        check_type="section_exists",
                        check_params={"path": "CLAUDE.md", "section": "Overview"},
                        recommendation="Add Overview section to CLAUDE.md"
                    ),
                    file_path="CLAUDE.md"
                ))

        # Check 3: README has Overview section
        if readme_content and not ValidationUtils.check_section_exists(readme_content, "Overview"):
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="docs_004",
                    category="documentation",
                    severity="medium",
                    description="README should have Overview section",
                    check_type="section_exists",
                    check_params={"path": "README.md", "section": "Overview"},
                    recommendation="Add Overview section to README.md"
                ),
                file_path="README.md"
            ))

        compliance_score = ValidationUtils.calculate_compliance_score(4, violations)

        return CategoryResult(
            category="documentation",
            passed=len(violations) == 0,
            violations=violations,
            checks_performed=4,
            compliance_score=compliance_score
        )


class TerraformInitValidator(CategoryValidator):
    """Validate Terraform unified initialization pattern"""

    def validate(
        self,
        repo_name: str,
        repo_structure: RepoStructure,
        standard: ParsedStandard
    ) -> CategoryResult:
        """Validate terraform init standard"""
        violations = []

        # Check 1: terraform-init-unified.sh exists
        script_exists = self._check_file_exists(repo_name, "terraform/scripts/terraform-init-unified.sh")
        if not script_exists:
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="tf_init_001",
                    category="terraform_init",
                    severity="high",
                    description="Unified terraform initialization script must exist",
                    check_type="file_exists",
                    check_params={"path": "terraform/scripts/terraform-init-unified.sh"},
                    recommendation="Create terraform/scripts/terraform-init-unified.sh per TERRAFORM_UNIFIED_INIT.md"
                ),
                file_path="terraform/scripts/terraform-init-unified.sh"
            ))

        # Check 2: main.tf has GCS backend
        main_tf = self._get_file_content(repo_name, "terraform/main.tf")
        if not main_tf:
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="tf_init_002",
                    category="terraform_init",
                    severity="critical",
                    description="main.tf must exist",
                    check_type="file_exists",
                    check_params={"path": "terraform/main.tf"},
                    recommendation="Create terraform/main.tf"
                ),
                file_path="terraform/main.tf"
            ))
        else:
            if 'backend "gcs"' not in main_tf:
                violations.append(self._create_violation(
                    ValidationRule(
                        rule_id="tf_init_003",
                        category="terraform_init",
                        severity="critical",
                        description="main.tf must have GCS backend configuration",
                        check_type="file_contains",
                        check_params={"path": "terraform/main.tf", "pattern": 'backend "gcs"'},
                        recommendation="Configure GCS backend in terraform/main.tf"
                    ),
                    file_path="terraform/main.tf"
                ))
            else:
                # Check 3: Backend bucket should not be hardcoded
                if ValidationUtils.check_file_pattern(main_tf, r'bucket\s*='):
                    violations.append(self._create_violation(
                        ValidationRule(
                            rule_id="tf_init_004",
                            category="terraform_init",
                            severity="medium",
                            description="Backend bucket should not be hardcoded",
                            check_type="file_contains",
                            check_params={"path": "terraform/main.tf", "pattern": "bucket\\s*="},
                            recommendation="Remove hardcoded bucket value, use CLI configuration"
                        ),
                        file_path="terraform/main.tf"
                    ))

        compliance_score = ValidationUtils.calculate_compliance_score(4, violations)

        return CategoryResult(
            category="terraform_init",
            passed=len(violations) == 0,
            violations=violations,
            checks_performed=4,
            compliance_score=compliance_score
        )


class MultiEnvValidator(CategoryValidator):
    """Validate multi-environment terraform setup"""

    def validate(
        self,
        repo_name: str,
        repo_structure: RepoStructure,
        standard: ParsedStandard
    ) -> CategoryResult:
        """Validate multi-env standard"""
        violations = []

        required_tfvars = ["terraform/dev.tfvars", "terraform/staging.tfvars", "terraform/prod.tfvars"]

        for tfvar_file in required_tfvars:
            if not self._check_file_exists(repo_name, tfvar_file):
                severity = "high" if "dev" in tfvar_file else "high"
                violations.append(self._create_violation(
                    ValidationRule(
                        rule_id=f"multi_env_{required_tfvars.index(tfvar_file) + 1:03d}",
                        category="multi_env",
                        severity=severity,
                        description=f"{tfvar_file} must exist for environment configuration",
                        check_type="file_exists",
                        check_params={"path": tfvar_file},
                        recommendation=f"Create {tfvar_file} per MULTI_ENV_SETUP.md"
                    ),
                    file_path=tfvar_file
                ))

        compliance_score = ValidationUtils.calculate_compliance_score(len(required_tfvars), violations)

        return CategoryResult(
            category="multi_env",
            passed=len(violations) == 0,
            violations=violations,
            checks_performed=len(required_tfvars),
            compliance_score=compliance_score
        )


class TerraformStateValidator(CategoryValidator):
    """Validate Terraform state management"""

    def validate(
        self,
        repo_name: str,
        repo_structure: RepoStructure,
        standard: ParsedStandard
    ) -> CategoryResult:
        """Validate terraform state standard"""
        violations = []

        # Check 1: Remote state backend configured
        main_tf = self._get_file_content(repo_name, "terraform/main.tf")
        if not main_tf or "backend" not in main_tf:
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="tf_state_001",
                    category="terraform_state",
                    severity="critical",
                    description="Remote state backend must be configured",
                    check_type="file_contains",
                    check_params={"path": "terraform/main.tf", "pattern": "backend"},
                    recommendation="Configure remote terraform backend per TERRAFORM_STATE_MANAGEMENT.md"
                ),
                file_path="terraform/main.tf"
            ))

        # Check 2: Backup script exists
        backup_exists = self._check_file_exists(repo_name, "scripts/backup-terraform-state.sh")
        if not backup_exists:
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="tf_state_002",
                    category="terraform_state",
                    severity="high",
                    description="Backup script should exist for disaster recovery",
                    check_type="file_exists",
                    check_params={"path": "scripts/backup-terraform-state.sh"},
                    recommendation="Create terraform state backup script per TERRAFORM_STATE_MANAGEMENT.md"
                ),
                file_path="scripts/backup-terraform-state.sh"
            ))

        compliance_score = ValidationUtils.calculate_compliance_score(2, violations)

        return CategoryResult(
            category="terraform_state",
            passed=len(violations) == 0,
            violations=violations,
            checks_performed=2,
            compliance_score=compliance_score
        )


class DisasterRecoveryValidator(CategoryValidator):
    """Validate disaster recovery setup"""

    def validate(
        self,
        repo_name: str,
        repo_structure: RepoStructure,
        standard: ParsedStandard
    ) -> CategoryResult:
        """Validate disaster recovery standard"""
        violations = []

        # Check 1: DISASTER_RECOVERY.md exists
        dr_doc = self._check_file_exists(repo_name, "DISASTER_RECOVERY.md")
        if not dr_doc:
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="dr_001",
                    category="disaster_recovery",
                    severity="high",
                    description="DISASTER_RECOVERY.md documentation must exist",
                    check_type="file_exists",
                    check_params={"path": "DISASTER_RECOVERY.md"},
                    recommendation="Create DISASTER_RECOVERY.md with recovery procedures"
                ),
                file_path="DISASTER_RECOVERY.md"
            ))

        # Check 2: Backup script exists
        backup_exists = self._check_file_exists(repo_name, "scripts/backup-postgres.sh")
        if not backup_exists:
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="dr_002",
                    category="disaster_recovery",
                    severity="high",
                    description="Database backup script must exist",
                    check_type="file_exists",
                    check_params={"path": "scripts/backup-postgres.sh"},
                    recommendation="Create backup-postgres.sh script per DISASTER_RECOVERY.md"
                ),
                file_path="scripts/backup-postgres.sh"
            ))

        compliance_score = ValidationUtils.calculate_compliance_score(2, violations)

        return CategoryResult(
            category="disaster_recovery",
            passed=len(violations) == 0,
            violations=violations,
            checks_performed=2,
            compliance_score=compliance_score
        )


class DeploymentValidator(CategoryValidator):
    """Validate deployment standards"""

    def validate(
        self,
        repo_name: str,
        repo_structure: RepoStructure,
        standard: ParsedStandard
    ) -> CategoryResult:
        """Validate deployment standard"""
        violations = []

        # Check 1: DEPLOYMENT.md exists
        deploy_doc = self._check_file_exists(repo_name, "DEPLOYMENT.md")
        if not deploy_doc:
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="deploy_001",
                    category="deployment",
                    severity="high",
                    description="DEPLOYMENT.md documentation must exist",
                    check_type="file_exists",
                    check_params={"path": "DEPLOYMENT.md"},
                    recommendation="Create DEPLOYMENT.md with deployment procedures"
                ),
                file_path="DEPLOYMENT.md"
            ))

        # Check 2: Secrets setup script exists
        setup_secrets = self._check_file_exists(repo_name, "scripts/setup-secrets.sh")
        if not setup_secrets:
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="deploy_002",
                    category="deployment",
                    severity="high",
                    description="Secrets setup script must exist",
                    check_type="file_exists",
                    check_params={"path": "scripts/setup-secrets.sh"},
                    recommendation="Create scripts/setup-secrets.sh for secret management setup"
                ),
                file_path="scripts/setup-secrets.sh"
            ))

        compliance_score = ValidationUtils.calculate_compliance_score(2, violations)

        return CategoryResult(
            category="deployment",
            passed=len(violations) == 0,
            violations=violations,
            checks_performed=2,
            compliance_score=compliance_score
        )


class PostgreSQLValidator(CategoryValidator):
    """Validate PostgreSQL setup"""

    def validate(
        self,
        repo_name: str,
        repo_structure: RepoStructure,
        standard: ParsedStandard
    ) -> CategoryResult:
        """Validate PostgreSQL standard"""
        violations = []

        # Check 1: POSTGRESQL_SETUP.md exists
        pg_doc = self._check_file_exists(repo_name, "docs/POSTGRESQL_SETUP.md")
        if not pg_doc:
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="pg_001",
                    category="postgresql",
                    severity="high",
                    description="POSTGRESQL_SETUP.md documentation must exist",
                    check_type="file_exists",
                    check_params={"path": "docs/POSTGRESQL_SETUP.md"},
                    recommendation="Create docs/POSTGRESQL_SETUP.md with PostgreSQL setup"
                ),
                file_path="docs/POSTGRESQL_SETUP.md"
            ))

        # Check 2: Terraform PostgreSQL config exists
        postgres_tf = self._check_file_exists(repo_name, "terraform/postgres.tf")
        if not postgres_tf:
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="pg_002",
                    category="postgresql",
                    severity="high",
                    description="Terraform PostgreSQL configuration must exist",
                    check_type="file_exists",
                    check_params={"path": "terraform/postgres.tf"},
                    recommendation="Create terraform/postgres.tf for PostgreSQL infrastructure"
                ),
                file_path="terraform/postgres.tf"
            ))

        # Check 3: Documentation mentions pgvector
        pg_content = self._get_file_content(repo_name, "docs/POSTGRESQL_SETUP.md")
        if pg_content and "pgvector" not in pg_content:
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="pg_003",
                    category="postgresql",
                    severity="medium",
                    description="PostgreSQL documentation should mention pgvector extension",
                    check_type="file_contains",
                    check_params={"path": "docs/POSTGRESQL_SETUP.md", "pattern": "pgvector"},
                    recommendation="Document pgvector extension requirement in POSTGRESQL_SETUP.md"
                ),
                file_path="docs/POSTGRESQL_SETUP.md"
            ))

        compliance_score = ValidationUtils.calculate_compliance_score(3, violations)

        return CategoryResult(
            category="postgresql",
            passed=len(violations) == 0,
            violations=violations,
            checks_performed=3,
            compliance_score=compliance_score
        )


class CICDValidator(CategoryValidator):
    """Validate CI/CD configuration"""

    def validate(
        self,
        repo_name: str,
        repo_structure: RepoStructure,
        standard: ParsedStandard
    ) -> CategoryResult:
        """Validate CI/CD standard"""
        violations = []

        # Check 1: Cloud Build config exists
        build_config = self._check_file_exists(repo_name, "cloudbuild.yaml")
        if not build_config:
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="cicd_001",
                    category="ci_cd",
                    severity="high",
                    description="Cloud Build configuration must exist",
                    check_type="file_exists",
                    check_params={"path": "cloudbuild.yaml"},
                    recommendation="Create cloudbuild.yaml per Cloud Build standards"
                ),
                file_path="cloudbuild.yaml"
            ))
        else:
            # Check 2: Multi-stage deployment
            config_content = self._get_file_content(repo_name, "cloudbuild.yaml")
            if config_content and "steps" not in config_content:
                violations.append(self._create_violation(
                    ValidationRule(
                        rule_id="cicd_002",
                        category="ci_cd",
                        severity="medium",
                        description="Cloud Build should use multi-stage deployment",
                        check_type="file_contains",
                        check_params={"path": "cloudbuild.yaml", "pattern": "steps"},
                        recommendation="Implement multi-stage build in cloudbuild.yaml"
                    ),
                    file_path="cloudbuild.yaml"
                ))

        compliance_score = ValidationUtils.calculate_compliance_score(2, violations)

        return CategoryResult(
            category="ci_cd",
            passed=len(violations) == 0,
            violations=violations,
            checks_performed=2,
            compliance_score=compliance_score
        )


class ContainerizationValidator(CategoryValidator):
    """Validate Docker/containerization setup"""

    def validate(
        self,
        repo_name: str,
        repo_structure: RepoStructure,
        standard: ParsedStandard
    ) -> CategoryResult:
        """Validate containerization standard"""
        violations = []

        # Check 1: Dockerfile exists
        dockerfile_exists = self._check_file_exists(repo_name, "Dockerfile")
        if not dockerfile_exists:
            violations.append(self._create_violation(
                ValidationRule(
                    rule_id="docker_001",
                    category="containerization",
                    severity="high",
                    description="Dockerfile must exist",
                    check_type="file_exists",
                    check_params={"path": "Dockerfile"},
                    recommendation="Create Dockerfile for containerization"
                ),
                file_path="Dockerfile"
            ))
        else:
            dockerfile_content = self._get_file_content(repo_name, "Dockerfile")
            if dockerfile_content:
                # Check 2: Multi-stage build
                if not ValidationUtils.check_file_pattern(dockerfile_content, r"FROM.*AS|as builder"):
                    violations.append(self._create_violation(
                        ValidationRule(
                            rule_id="docker_002",
                            category="containerization",
                            severity="medium",
                            description="Dockerfile should use multi-stage build",
                            check_type="file_contains",
                            check_params={"path": "Dockerfile", "pattern": "FROM.*AS|as builder"},
                            recommendation="Implement multi-stage Docker build to minimize image size"
                        ),
                        file_path="Dockerfile"
                    ))

                # Check 3: Exposes port 8080
                if "8080" not in dockerfile_content:
                    violations.append(self._create_violation(
                        ValidationRule(
                            rule_id="docker_003",
                            category="containerization",
                            severity="medium",
                            description="Dockerfile should expose port 8080 for Cloud Run",
                            check_type="file_contains",
                            check_params={"path": "Dockerfile", "pattern": "8080"},
                            recommendation="Expose port 8080 in Dockerfile for Cloud Run compatibility"
                        ),
                        file_path="Dockerfile"
                    ))

        compliance_score = ValidationUtils.calculate_compliance_score(3, violations)

        return CategoryResult(
            category="containerization",
            passed=len(violations) == 0,
            violations=violations,
            checks_performed=3,
            compliance_score=compliance_score
        )
