"""
Architectural Validator

GitHub API-based repository validation against architectural standards.
Uses pure API access (no filesystem operations, no git cloning).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from abc import ABC, abstractmethod
import logging
import re
import yaml
from github import Github, GithubException

from core.standards_loader import ParsedStandard, ValidationRule

logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a repository file"""
    path: str
    type: str  # "file" or "dir"
    size: Optional[int] = None
    sha: Optional[str] = None


@dataclass
class RepoStructure:
    """Repository structure scanned via GitHub API"""
    repository: str
    files: Dict[str, FileInfo] = field(default_factory=dict)  # path -> FileInfo
    directories: Set[str] = field(default_factory=set)


@dataclass
class Violation:
    """A standards violation found during validation"""
    severity: str  # critical, high, medium, low
    rule_id: str
    category: str
    message: str
    recommendation: str
    file_path: Optional[str] = None
    standard_reference: str = ""


@dataclass
class CategoryResult:
    """Result of validating a single standards category"""
    category: str
    passed: bool
    violations: List[Violation] = field(default_factory=list)
    checks_performed: int = 0
    compliance_score: float = 1.0


@dataclass
class ValidationReport:
    """Complete validation report for a repository"""
    repository: str
    overall_compliance_score: float
    compliance_grade: str
    summary: Dict[str, int]
    categories: Dict[str, CategoryResult]
    critical_violations: List[Violation]
    recommendations: List[Dict[str, Any]]
    scan_metadata: Dict[str, Any]


class RepositoryScanner:
    """
    Scan repository structure using GitHub API (no git clone)

    Uses PyGithub to fetch repository structure and file contents.
    Caches file content to minimize API calls.
    """

    def __init__(self, github_client: Github):
        """
        Initialize scanner

        Args:
            github_client: PyGithub Github client instance
        """
        self.github = github_client
        self._file_cache: Dict[str, Optional[str]] = {}
        self._structure_cache: Dict[str, RepoStructure] = {}

    def scan_repository_structure(self, repo_name: str) -> RepoStructure:
        """
        Scan repository structure using GitHub API

        Args:
            repo_name: Repository name in format 'owner/repo'

        Returns:
            RepoStructure with all files and directories

        Raises:
            GithubException: If repository not found or API error occurs
        """
        # Check cache first
        if repo_name in self._structure_cache:
            logger.debug(f"Using cached structure for {repo_name}")
            return self._structure_cache[repo_name]

        try:
            repo = self.github.get_repo(repo_name)
            structure = RepoStructure(repository=repo_name)

            # Recursively traverse repository tree
            self._traverse_tree(repo, "", structure)

            # Cache result
            self._structure_cache[repo_name] = structure
            logger.info(f"Scanned {repo_name}: {len(structure.files)} files, {len(structure.directories)} directories")

            return structure
        except GithubException as e:
            logger.error(f"Failed to scan {repo_name}: {e}")
            raise

    def _traverse_tree(
        self,
        repo,
        path: str,
        structure: RepoStructure,
        depth: int = 0
    ) -> None:
        """
        Recursively traverse repository tree via GitHub API

        Args:
            repo: PyGithub Repository object
            path: Current path (empty for root)
            structure: RepoStructure to populate
            depth: Current recursion depth (limit to prevent infinite loops)
        """
        # Limit recursion depth to avoid excessive API calls
        if depth > 20:
            logger.warning(f"Max recursion depth reached at {path}")
            return

        try:
            contents = repo.get_contents(path if path else "")

            # Handle both single file and list of contents
            if not isinstance(contents, list):
                contents = [contents]

            for item in contents:
                file_info = FileInfo(
                    path=item.path,
                    type="dir" if item.type == "dir" else "file",
                    size=item.size if item.type == "file" else None,
                    sha=item.sha
                )

                if item.type == "dir":
                    structure.directories.add(item.path)
                    # Recursively scan subdirectory
                    self._traverse_tree(repo, item.path, structure, depth + 1)
                else:
                    structure.files[item.path] = file_info

        except GithubException as e:
            if e.status == 404:
                logger.debug(f"Path not found: {path}")
            else:
                logger.warning(f"Error traversing {path}: {e}")

    def get_file_content(self, repo_name: str, filepath: str) -> Optional[str]:
        """
        Get file content via GitHub API with caching

        Args:
            repo_name: Repository name in format 'owner/repo'
            filepath: Path to file in repository

        Returns:
            File content as string, or None if file not found

        Raises:
            GithubException: If repository not found
        """
        cache_key = f"{repo_name}:{filepath}"

        # Check cache first
        if cache_key in self._file_cache:
            return self._file_cache[cache_key]

        try:
            repo = self.github.get_repo(repo_name)
            file_obj = repo.get_contents(filepath)

            # Only decode if it's a file (not a directory)
            if file_obj.type == "file":
                content = file_obj.decoded_content.decode('utf-8', errors='ignore')
                self._file_cache[cache_key] = content
                logger.debug(f"Fetched {filepath} from {repo_name}")
                return content
            else:
                self._file_cache[cache_key] = None
                return None

        except GithubException as e:
            if e.status == 404:
                logger.debug(f"File not found: {filepath} in {repo_name}")
                self._file_cache[cache_key] = None
                return None
            else:
                logger.warning(f"Error fetching {filepath}: {e}")
                self._file_cache[cache_key] = None
                return None

    def file_exists(self, repo_name: str, filepath: str) -> bool:
        """
        Check if file exists in repository

        Args:
            repo_name: Repository name
            filepath: Path to file

        Returns:
            True if file exists, False otherwise
        """
        try:
            repo = self.github.get_repo(repo_name)
            repo.get_contents(filepath)
            return True
        except GithubException:
            return False

    def clear_cache(self) -> None:
        """Clear file content cache (useful for testing or memory management)"""
        self._file_cache.clear()
        self._structure_cache.clear()
        logger.debug("Cleared scanner cache")


class ValidationUtils:
    """Shared validation utilities used by category validators"""

    @staticmethod
    def check_file_pattern(content: str, pattern: str) -> bool:
        """
        Check if file content contains regex pattern

        Args:
            content: File content
            pattern: Regex pattern to search for

        Returns:
            True if pattern found, False otherwise
        """
        try:
            return bool(re.search(pattern, content, re.IGNORECASE | re.MULTILINE))
        except re.error as e:
            logger.warning(f"Invalid regex pattern: {pattern}: {e}")
            return False

    @staticmethod
    def check_section_exists(content: str, section_title: str) -> bool:
        """
        Check if markdown section exists

        Args:
            content: Markdown content
            section_title: Section title to find

        Returns:
            True if section found, False otherwise
        """
        pattern = rf"^#+\s+{re.escape(section_title)}"
        return bool(re.search(pattern, content, re.MULTILINE))

    @staticmethod
    def check_yaml_field(yaml_content: str, field_path: str) -> bool:
        """
        Check if YAML contains field at dot-notation path

        Args:
            yaml_content: YAML content
            field_path: Field path (e.g., "steps.0.args")

        Returns:
            True if field exists, False otherwise
        """
        try:
            data = yaml.safe_load(yaml_content)
            if not isinstance(data, dict):
                return False

            keys = field_path.split(".")
            current = data

            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                elif isinstance(current, list):
                    try:
                        idx = int(key)
                        if 0 <= idx < len(current):
                            current = current[idx]
                        else:
                            return False
                    except ValueError:
                        return False
                else:
                    return False

            return True
        except yaml.YAMLError as e:
            logger.warning(f"Invalid YAML: {e}")
            return False

    @staticmethod
    def calculate_compliance_score(
        total_checks: int,
        violations: List[Violation]
    ) -> float:
        """
        Calculate compliance score with severity weighting

        Severity penalties:
        - Critical: -10 points
        - High: -5 points
        - Medium: -2 points
        - Low: -1 point

        Args:
            total_checks: Total number of checks performed
            violations: List of violations found

        Returns:
            Compliance score from 0.0 to 1.0
        """
        if total_checks == 0:
            return 1.0

        penalty = sum(
            10 if v.severity == "critical" else
            5 if v.severity == "high" else
            2 if v.severity == "medium" else 1
            for v in violations
        )

        max_score = total_checks * 10
        score = max(0.0, (max_score - penalty) / max_score)
        return round(score, 2)

    @staticmethod
    def grade_compliance(score: float) -> str:
        """
        Assign letter grade based on compliance score

        Args:
            score: Compliance score from 0.0 to 1.0

        Returns:
            Letter grade: A, B, C, D, or F
        """
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"


class CategoryValidator(ABC):
    """Base class for category-specific validators"""

    def __init__(self, scanner: RepositoryScanner):
        """
        Initialize validator

        Args:
            scanner: RepositoryScanner instance
        """
        self.scanner = scanner

    @abstractmethod
    def validate(
        self,
        repo_name: str,
        repo_structure: RepoStructure,
        standard: ParsedStandard
    ) -> CategoryResult:
        """
        Validate repository against specific standard

        Args:
            repo_name: Repository name
            repo_structure: Repository structure scanned via API
            standard: Standard to validate against

        Returns:
            CategoryResult with violations and score
        """
        pass

    def _check_file_exists(self, repo_name: str, filepath: str) -> bool:
        """Check if file exists in repository"""
        return self.scanner.file_exists(repo_name, filepath)

    def _get_file_content(self, repo_name: str, filepath: str) -> Optional[str]:
        """Get file content from repository"""
        return self.scanner.get_file_content(repo_name, filepath)

    def _create_violation(
        self,
        rule: ValidationRule,
        file_path: Optional[str] = None
    ) -> Violation:
        """Create a violation from a validation rule"""
        return Violation(
            severity=rule.severity,
            rule_id=rule.rule_id,
            category=rule.category,
            message=rule.description,
            recommendation=rule.recommendation,
            file_path=file_path,
            standard_reference=""
        )


class ArchitecturalValidator:
    """
    Main validation engine

    Coordinates category validators and generates comprehensive reports.
    """

    def __init__(self, github_client: Github, standards_loader):
        """
        Initialize validator

        Args:
            github_client: PyGithub Github client
            standards_loader: StandardsLoader instance
        """
        self.github = github_client
        self.standards = standards_loader
        self.scanner = RepositoryScanner(github_client)
        self.validators: Dict[str, CategoryValidator] = {}

        # Register validators for each standard category
        self._register_validators()

        logger.info("Initializing ArchitecturalValidator with %d validators", len(self.validators))

    def _register_validators(self) -> None:
        """Register category-specific validators"""
        # Import validators here to avoid circular imports
        from core.category_validators import (
            LicenseValidator,
            DocumentationValidator,
            TerraformInitValidator,
            MultiEnvValidator,
            TerraformStateValidator,
            DisasterRecoveryValidator,
            DeploymentValidator,
            PostgreSQLValidator,
            CICDValidator,
            ContainerizationValidator,
        )

        self.validators = {
            "license": LicenseValidator(self.scanner),
            "documentation": DocumentationValidator(self.scanner),
            "terraform_init": TerraformInitValidator(self.scanner),
            "multi_env": MultiEnvValidator(self.scanner),
            "terraform_state": TerraformStateValidator(self.scanner),
            "disaster_recovery": DisasterRecoveryValidator(self.scanner),
            "deployment": DeploymentValidator(self.scanner),
            "postgresql": PostgreSQLValidator(self.scanner),
            "ci_cd": CICDValidator(self.scanner),
            "containerization": ContainerizationValidator(self.scanner),
        }

    def validate_repository(
        self,
        repo_name: str,
        scope: Optional[List[str]] = None
    ) -> ValidationReport:
        """
        Validate repository against architectural standards

        Args:
            repo_name: Repository name in format 'owner/repo'
            scope: Optional list of standard categories to check (default: all)

        Returns:
            ValidationReport with detailed results
        """
        logger.info(f"Starting validation of {repo_name}")

        try:
            # Scan repository structure
            repo_structure = self.scanner.scan_repository_structure(repo_name)

            # Determine which standards to check
            standards_to_check = scope or self.standards.list_categories()

            # Run validators
            results: Dict[str, CategoryResult] = {}
            total_checks = 0
            all_violations: List[Violation] = []

            for category in standards_to_check:
                std = self.standards.get_standard(category)
                if not std:
                    logger.warning(f"Standard not found: {category}")
                    continue

                # Use category-specific validator or generic validator
                try:
                    result = self._validate_category(repo_name, repo_structure, std)
                    results[category] = result
                    total_checks += result.checks_performed
                    all_violations.extend(result.violations)
                except Exception as e:
                    logger.error(f"Error validating {category}: {e}")
                    results[category] = CategoryResult(
                        category=category,
                        passed=False,
                        violations=[],
                        checks_performed=0,
                        compliance_score=0.0
                    )

            # Generate report
            return self._generate_report(repo_name, results, total_checks, all_violations)

        except Exception as e:
            logger.error(f"Validation failed for {repo_name}: {e}")
            # Return error report
            return self._generate_error_report(repo_name, str(e))

    def _validate_category(
        self,
        repo_name: str,
        repo_structure: RepoStructure,
        standard: ParsedStandard
    ) -> CategoryResult:
        """Validate single category using registered validator"""
        category = standard.category

        # Use category-specific validator if available
        if category in self.validators:
            validator = self.validators[category]
            return validator.validate(repo_name, repo_structure, standard)

        # Fallback to generic validation
        logger.warning(f"No specific validator for category {category}, using generic validation")
        violations = []
        checks_performed = len(standard.validation_rules)

        for rule in standard.validation_rules:
            if not self._check_rule(repo_name, rule):
                violations.append(Violation(
                    severity=rule.severity,
                    rule_id=rule.rule_id,
                    category=standard.category,
                    message=rule.description,
                    recommendation=rule.recommendation,
                    file_path=rule.check_params.get("path")
                ))

        compliance_score = ValidationUtils.calculate_compliance_score(checks_performed, violations)

        return CategoryResult(
            category=standard.category,
            passed=len(violations) == 0,
            violations=violations,
            checks_performed=checks_performed,
            compliance_score=compliance_score
        )

    def _check_rule(self, repo_name: str, rule: ValidationRule) -> bool:
        """Check if a validation rule passes"""
        check_type = rule.check_type
        params = rule.check_params

        try:
            if check_type == "file_exists":
                filepath = params.get("path")
                return self.scanner.file_exists(repo_name, filepath)

            elif check_type == "file_contains":
                filepath = params.get("path")
                pattern = params.get("pattern", "")
                content = self.scanner.get_file_content(repo_name, filepath)
                if content is None:
                    return False
                return ValidationUtils.check_file_pattern(content, pattern)

            elif check_type == "file_size":
                filepath = params.get("path")
                min_size = params.get("min_size", 0)
                content = self.scanner.get_file_content(repo_name, filepath)
                if content is None:
                    return False
                return len(content) >= min_size

            elif check_type == "section_exists":
                filepath = params.get("path")
                section = params.get("section", "")
                content = self.scanner.get_file_content(repo_name, filepath)
                if content is None:
                    return False
                return ValidationUtils.check_section_exists(content, section)

            elif check_type == "yaml_field":
                filepath = params.get("path")
                field_path = params.get("field", "")
                content = self.scanner.get_file_content(repo_name, filepath)
                if content is None:
                    return False
                return ValidationUtils.check_yaml_field(content, field_path)

            else:
                logger.warning(f"Unknown check type: {check_type}")
                return False

        except Exception as e:
            logger.warning(f"Error checking rule {rule.rule_id}: {e}")
            return False

    def _generate_report(
        self,
        repo_name: str,
        results: Dict[str, CategoryResult],
        total_checks: int,
        all_violations: List[Violation]
    ) -> ValidationReport:
        """Generate comprehensive validation report"""
        critical_violations = [v for v in all_violations if v.severity == "critical"]
        high_violations = [v for v in all_violations if v.severity == "high"]
        medium_violations = [v for v in all_violations if v.severity == "medium"]
        low_violations = [v for v in all_violations if v.severity == "low"]

        # Calculate overall score
        overall_score = ValidationUtils.calculate_compliance_score(total_checks, all_violations)

        return ValidationReport(
            repository=repo_name,
            overall_compliance_score=overall_score,
            compliance_grade=ValidationUtils.grade_compliance(overall_score),
            summary={
                "total_checks": total_checks,
                "passed_checks": total_checks - len(all_violations),
                "failed_checks": len(all_violations),
                "critical_violations": len(critical_violations),
                "high_violations": len(high_violations),
                "medium_violations": len(medium_violations),
                "low_violations": len(low_violations),
            },
            categories=results,
            critical_violations=critical_violations,
            recommendations=self._generate_recommendations(all_violations),
            scan_metadata={
                "files_scanned": 0,  # TODO: count from repo_structure
                "scan_duration_ms": 0,  # TODO: track timing
                "github_api_calls": 0  # TODO: track API calls
            }
        )

    def _generate_error_report(self, repo_name: str, error: str) -> ValidationReport:
        """Generate error report"""
        return ValidationReport(
            repository=repo_name,
            overall_compliance_score=0.0,
            compliance_grade="F",
            summary={
                "total_checks": 0,
                "passed_checks": 0,
                "failed_checks": 0,
                "critical_violations": 1,
                "high_violations": 0,
                "medium_violations": 0,
                "low_violations": 0,
            },
            categories={},
            critical_violations=[Violation(
                severity="critical",
                rule_id="scan_error",
                category="scan",
                message=f"Repository scan failed: {error}",
                recommendation="Verify repository exists and is accessible",
                file_path=None
            )],
            recommendations=[],
            scan_metadata={}
        )

    def _generate_recommendations(self, violations: List[Violation]) -> List[Dict[str, Any]]:
        """Generate prioritized improvement recommendations"""
        recommendations = []
        seen = set()

        # Sort by severity (critical first)
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_violations = sorted(violations, key=lambda v: severity_order.get(v.severity, 4))

        for violation in sorted_violations:
            if violation.rule_id not in seen:
                recommendations.append({
                    "priority": violation.severity.upper(),
                    "category": violation.category,
                    "rule_id": violation.rule_id,
                    "title": violation.message,
                    "description": violation.recommendation,
                    "file_path": violation.file_path
                })
                seen.add(violation.rule_id)

        return recommendations
