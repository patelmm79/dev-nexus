"""
Unit tests for StandardsLoader

Tests standards loading, parsing, and data structure creation.
"""

import pytest
from pathlib import Path
from core.standards_loader import StandardsLoader, ParsedStandard, ValidationRule


@pytest.fixture
def repo_root():
    """Get project root directory"""
    return str(Path(__file__).parent.parent)


class TestStandardsLoader:
    """Test StandardsLoader class"""

    def test_loader_initialization(self, repo_root):
        """Test that StandardsLoader initializes successfully"""
        loader = StandardsLoader(repo_root)
        assert loader.repo_root == Path(repo_root)
        assert len(loader.standards) > 0

    def test_loader_loads_all_standards(self, repo_root):
        """Test that all expected standards are loaded"""
        loader = StandardsLoader(repo_root)
        expected_categories = [
            "documentation",
            "license",
            "terraform_init",
            "multi_env",
            "terraform_state",
            "disaster_recovery",
            "deployment",
            "postgresql",
            "ci_cd",
            "containerization",
        ]

        categories = loader.list_categories()
        for category in expected_categories:
            assert category in categories, f"Missing standard: {category}"

    def test_license_standard_loaded(self, repo_root):
        """Test that license standard is properly loaded"""
        loader = StandardsLoader(repo_root)
        license_std = loader.get_standard("license")

        assert license_std is not None
        assert license_std.category == "license"
        assert len(license_std.validation_rules) > 0
        assert "LICENSE" in license_std.required_files
        assert "README.md" in license_std.required_files

    def test_license_standard_has_critical_rule(self, repo_root):
        """Test that license standard has critical validation rules"""
        loader = StandardsLoader(repo_root)
        license_std = loader.get_standard("license")

        critical_rules = [r for r in license_std.validation_rules if r.severity == "critical"]
        assert len(critical_rules) > 0

        # Check for LICENSE file existence rule
        rule_ids = [r.rule_id for r in critical_rules]
        assert "license_001" in rule_ids or "license_003" in rule_ids

    def test_terraform_init_standard_loaded(self, repo_root):
        """Test that terraform init standard is loaded"""
        loader = StandardsLoader(repo_root)
        tf_std = loader.get_standard("terraform_init")

        assert tf_std is not None
        assert tf_std.category == "terraform_init"
        assert "terraform/scripts/terraform-init-unified.sh" in tf_std.required_files
        assert "terraform/main.tf" in tf_std.required_files

    def test_multi_env_standard_has_three_tfvars(self, repo_root):
        """Test that multi-env standard requires all three environment tfvars"""
        loader = StandardsLoader(repo_root)
        multi_env_std = loader.get_standard("multi_env")

        required_files = multi_env_std.required_files
        assert "terraform/dev.tfvars" in required_files
        assert "terraform/staging.tfvars" in required_files
        assert "terraform/prod.tfvars" in required_files

    def test_validation_rule_structure(self, repo_root):
        """Test that validation rules have required fields"""
        loader = StandardsLoader(repo_root)
        license_std = loader.get_standard("license")

        for rule in license_std.validation_rules:
            assert rule.rule_id
            assert rule.category == "license"
            assert rule.severity in ["critical", "high", "medium", "low"]
            assert rule.description
            assert rule.check_type
            assert rule.check_params
            assert rule.recommendation

    def test_get_all_standards(self, repo_root):
        """Test retrieving all standards"""
        loader = StandardsLoader(repo_root)
        all_standards = loader.get_all_standards()

        assert isinstance(all_standards, dict)
        assert len(all_standards) == len(loader.list_categories())

        for category, standard in all_standards.items():
            assert standard.category == category
            assert isinstance(standard, ParsedStandard)

    def test_get_nonexistent_standard(self, repo_root):
        """Test retrieving nonexistent standard returns None"""
        loader = StandardsLoader(repo_root)
        result = loader.get_standard("nonexistent_standard")
        assert result is None

    def test_list_categories(self, repo_root):
        """Test listing all categories"""
        loader = StandardsLoader(repo_root)
        categories = loader.list_categories()

        assert isinstance(categories, list)
        assert len(categories) > 0
        assert "license" in categories
        assert "terraform_init" in categories

    def test_documentation_standard_loaded(self, repo_root):
        """Test that documentation standard is loaded"""
        loader = StandardsLoader(repo_root)
        docs_std = loader.get_standard("documentation")

        assert docs_std is not None
        assert "README.md" in docs_std.required_files
        assert "CLAUDE.md" in docs_std.required_files

    def test_disaster_recovery_standard_loaded(self, repo_root):
        """Test that disaster recovery standard is loaded"""
        loader = StandardsLoader(repo_root)
        dr_std = loader.get_standard("disaster_recovery")

        assert dr_std is not None
        assert "DISASTER_RECOVERY.md" in dr_std.required_files
        assert "scripts/backup-postgres.sh" in dr_std.required_files

    def test_postgresql_standard_loaded(self, repo_root):
        """Test that PostgreSQL standard is loaded"""
        loader = StandardsLoader(repo_root)
        pg_std = loader.get_standard("postgresql")

        assert pg_std is not None
        assert "docs/POSTGRESQL_SETUP.md" in pg_std.required_files
        assert "terraform/postgres.tf" in pg_std.required_files

    def test_ci_cd_standard_loaded(self, repo_root):
        """Test that CI/CD standard is loaded"""
        loader = StandardsLoader(repo_root)
        cicd_std = loader.get_standard("ci_cd")

        assert cicd_std is not None
        assert "cloudbuild.yaml" in cicd_std.required_files

    def test_containerization_standard_loaded(self, repo_root):
        """Test that containerization standard is loaded"""
        loader = StandardsLoader(repo_root)
        docker_std = loader.get_standard("containerization")

        assert docker_std is not None
        assert "Dockerfile" in docker_std.required_files


class TestValidationRule:
    """Test ValidationRule dataclass"""

    def test_validation_rule_creation(self):
        """Test creating a validation rule"""
        rule = ValidationRule(
            rule_id="test_001",
            category="test",
            severity="high",
            description="Test rule",
            check_type="file_exists",
            check_params={"path": "test.txt"},
            recommendation="Fix test"
        )

        assert rule.rule_id == "test_001"
        assert rule.category == "test"
        assert rule.severity == "high"
        assert rule.check_type == "file_exists"

    def test_validation_rule_defaults(self):
        """Test validation rule with default values"""
        rule = ValidationRule(
            rule_id="test_001",
            category="test",
            severity="medium",
            description="Test",
            check_type="file_contains"
        )

        assert rule.check_params == {}
        assert rule.recommendation == ""


class TestParsedStandard:
    """Test ParsedStandard dataclass"""

    def test_parsed_standard_creation(self):
        """Test creating a parsed standard"""
        rule = ValidationRule(
            rule_id="test_001",
            category="test",
            severity="high",
            description="Test",
            check_type="file_exists",
            check_params={}
        )

        std = ParsedStandard(
            category="test",
            title="Test Standard",
            required_files=["test.txt"],
            validation_rules=[rule]
        )

        assert std.category == "test"
        assert std.title == "Test Standard"
        assert len(std.required_files) == 1
        assert len(std.validation_rules) == 1

    def test_parsed_standard_defaults(self):
        """Test ParsedStandard with default values"""
        std = ParsedStandard(category="test", title="Test")

        assert std.required_files == []
        assert std.validation_rules == []
        assert std.required_sections == {}
        assert std.documentation_content == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
