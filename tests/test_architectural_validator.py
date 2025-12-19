"""
Unit tests for ArchitecturalValidator

Tests repository scanner, validators, and utilities.
Uses mocked GitHub client for isolated testing.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from github import GithubException

from core.architectural_validator import (
    RepositoryScanner,
    ValidationUtils,
    FileInfo,
    RepoStructure,
    Violation,
    CategoryResult,
    ValidationRule,
)


@pytest.fixture
def mock_github_client():
    """Create mocked GitHub client"""
    return MagicMock()


@pytest.fixture
def scanner(mock_github_client):
    """Create RepositoryScanner with mocked client"""
    return RepositoryScanner(mock_github_client)


class TestRepositoryScanner:
    """Test RepositoryScanner class"""

    def test_scanner_initialization(self, mock_github_client):
        """Test scanner initializes with GitHub client"""
        scanner = RepositoryScanner(mock_github_client)
        assert scanner.github == mock_github_client
        assert len(scanner._file_cache) == 0

    def test_file_exists_returns_true(self, scanner, mock_github_client):
        """Test file_exists returns True when file found"""
        mock_repo = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_repo.get_contents.return_value = MagicMock()

        result = scanner.file_exists("owner/repo", "README.md")
        assert result is True

    def test_file_exists_returns_false(self, scanner, mock_github_client):
        """Test file_exists returns False when file not found"""
        mock_repo = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_repo.get_contents.side_effect = GithubException(404, {"message": "Not Found"})

        result = scanner.file_exists("owner/repo", "nonexistent.txt")
        assert result is False

    def test_get_file_content_returns_content(self, scanner, mock_github_client):
        """Test get_file_content returns file content"""
        mock_repo = MagicMock()
        mock_file = MagicMock()
        mock_file.type = "file"
        mock_file.decoded_content = b"File content here"

        mock_github_client.get_repo.return_value = mock_repo
        mock_repo.get_contents.return_value = mock_file

        content = scanner.get_file_content("owner/repo", "README.md")
        assert content == "File content here"

    def test_get_file_content_caches_result(self, scanner, mock_github_client):
        """Test that file content is cached"""
        mock_repo = MagicMock()
        mock_file = MagicMock()
        mock_file.type = "file"
        mock_file.decoded_content = b"Content"

        mock_github_client.get_repo.return_value = mock_repo
        mock_repo.get_contents.return_value = mock_file

        # First call
        content1 = scanner.get_file_content("owner/repo", "README.md")
        # Second call (should use cache)
        content2 = scanner.get_file_content("owner/repo", "README.md")

        assert content1 == content2
        # GitHub API should only be called once
        assert mock_github_client.get_repo.call_count == 1

    def test_get_file_content_returns_none_for_directory(self, scanner, mock_github_client):
        """Test that get_file_content returns None for directories"""
        mock_repo = MagicMock()
        mock_dir = MagicMock()
        mock_dir.type = "dir"

        mock_github_client.get_repo.return_value = mock_repo
        mock_repo.get_contents.return_value = mock_dir

        content = scanner.get_file_content("owner/repo", "somedir")
        assert content is None

    def test_get_file_content_returns_none_for_404(self, scanner, mock_github_client):
        """Test that get_file_content returns None for 404 errors"""
        mock_repo = MagicMock()
        mock_github_client.get_repo.return_value = mock_repo
        mock_repo.get_contents.side_effect = GithubException(404, {"message": "Not Found"})

        content = scanner.get_file_content("owner/repo", "missing.txt")
        assert content is None

    def test_clear_cache(self, scanner, mock_github_client):
        """Test clearing scanner cache"""
        # Add something to cache
        scanner._file_cache["key"] = "value"
        assert len(scanner._file_cache) > 0

        # Clear cache
        scanner.clear_cache()
        assert len(scanner._file_cache) == 0


class TestValidationUtils:
    """Test ValidationUtils utility functions"""

    def test_check_file_pattern_found(self):
        """Test pattern found in file"""
        content = "This is a LICENSE file with GPL v3.0 text"
        pattern = "GPL v3"
        result = ValidationUtils.check_file_pattern(content, pattern)
        assert result is True

    def test_check_file_pattern_not_found(self):
        """Test pattern not found in file"""
        content = "This is a regular file"
        pattern = "GPL v3"
        result = ValidationUtils.check_file_pattern(content, pattern)
        assert result is False

    def test_check_file_pattern_case_insensitive(self):
        """Test pattern matching is case-insensitive"""
        content = "This contains GPL V3.0"
        pattern = "gpl v3"
        result = ValidationUtils.check_file_pattern(content, pattern)
        assert result is True

    def test_check_section_exists_found(self):
        """Test markdown section is found"""
        content = """# Overview
Some content

## Core Features
More content
"""
        result = ValidationUtils.check_section_exists(content, "Overview")
        assert result is True

    def test_check_section_exists_not_found(self):
        """Test markdown section not found"""
        content = "# Overview\nContent"
        result = ValidationUtils.check_section_exists(content, "Missing Section")
        assert result is False

    def test_check_yaml_field_found(self):
        """Test YAML field is found"""
        yaml_content = """
steps:
  - name: Build
    args:
      - build
"""
        result = ValidationUtils.check_yaml_field(yaml_content, "steps.0.args")
        assert result is True

    def test_check_yaml_field_not_found(self):
        """Test YAML field not found"""
        yaml_content = "steps:\n  - name: Build"
        result = ValidationUtils.check_yaml_field(yaml_content, "nonexistent.field")
        assert result is False

    def test_check_yaml_field_invalid_yaml(self):
        """Test YAML parsing with invalid YAML"""
        yaml_content = "invalid: yaml: content:"
        result = ValidationUtils.check_yaml_field(yaml_content, "field")
        assert result is False

    def test_calculate_compliance_score_no_violations(self):
        """Test compliance score with no violations"""
        score = ValidationUtils.calculate_compliance_score(10, [])
        assert score == 1.0

    def test_calculate_compliance_score_all_critical(self):
        """Test compliance score with all violations being critical"""
        violations = [
            Violation("critical", "c1", "cat", "msg", "rec"),
            Violation("critical", "c2", "cat", "msg", "rec"),
        ]
        score = ValidationUtils.calculate_compliance_score(10, violations)
        # 10 checks * 10 points = 100 max
        # 2 critical violations = -20 points
        # (100 - 20) / 100 = 0.8
        assert score == 0.8

    def test_calculate_compliance_score_partial_violations(self):
        """Test compliance score with partial violations"""
        violations = [
            Violation("high", "h1", "cat", "msg", "rec"),
        ]
        score = ValidationUtils.calculate_compliance_score(10, violations)
        # 10 checks * 10 points = 100 max
        # 1 high violation = -5 points
        # (100 - 5) / 100 = 0.95
        assert score == 0.95

    def test_grade_compliance_a(self):
        """Test grade A for score 0.9+"""
        assert ValidationUtils.grade_compliance(0.95) == "A"
        assert ValidationUtils.grade_compliance(1.0) == "A"

    def test_grade_compliance_b(self):
        """Test grade B for score 0.8-0.89"""
        assert ValidationUtils.grade_compliance(0.89) == "B"
        assert ValidationUtils.grade_compliance(0.80) == "B"

    def test_grade_compliance_c(self):
        """Test grade C for score 0.7-0.79"""
        assert ValidationUtils.grade_compliance(0.79) == "C"
        assert ValidationUtils.grade_compliance(0.70) == "C"

    def test_grade_compliance_d(self):
        """Test grade D for score 0.6-0.69"""
        assert ValidationUtils.grade_compliance(0.69) == "D"
        assert ValidationUtils.grade_compliance(0.60) == "D"

    def test_grade_compliance_f(self):
        """Test grade F for score below 0.6"""
        assert ValidationUtils.grade_compliance(0.59) == "F"
        assert ValidationUtils.grade_compliance(0.0) == "F"


class TestFileInfo:
    """Test FileInfo dataclass"""

    def test_file_info_creation(self):
        """Test creating FileInfo"""
        info = FileInfo(
            path="README.md",
            type="file",
            size=1024,
            sha="abc123"
        )
        assert info.path == "README.md"
        assert info.type == "file"
        assert info.size == 1024

    def test_file_info_defaults(self):
        """Test FileInfo with defaults"""
        info = FileInfo(path="dir", type="dir")
        assert info.size is None
        assert info.sha is None


class TestRepoStructure:
    """Test RepoStructure dataclass"""

    def test_repo_structure_creation(self):
        """Test creating RepoStructure"""
        info = FileInfo("README.md", "file")
        structure = RepoStructure(
            repository="owner/repo",
            files={"README.md": info},
            directories={"docs", "src"}
        )
        assert structure.repository == "owner/repo"
        assert len(structure.files) == 1
        assert len(structure.directories) == 2

    def test_repo_structure_defaults(self):
        """Test RepoStructure with defaults"""
        structure = RepoStructure(repository="owner/repo")
        assert structure.files == {}
        assert structure.directories == set()


class TestViolation:
    """Test Violation dataclass"""

    def test_violation_creation(self):
        """Test creating violation"""
        v = Violation(
            severity="high",
            rule_id="rule_001",
            category="license",
            message="Missing LICENSE file",
            recommendation="Add LICENSE file",
            file_path="LICENSE"
        )
        assert v.severity == "high"
        assert v.rule_id == "rule_001"
        assert v.file_path == "LICENSE"

    def test_violation_defaults(self):
        """Test Violation with defaults"""
        v = Violation(
            severity="medium",
            rule_id="r1",
            category="test",
            message="msg",
            recommendation="rec"
        )
        assert v.file_path is None
        assert v.standard_reference == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
