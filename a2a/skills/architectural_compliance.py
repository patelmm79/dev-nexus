"""
Architectural Compliance Skills

A2A skills for validating repositories against architectural standards.
Provides comprehensive compliance checking with scoring and recommendations.
"""

import logging
import os
from typing import Dict, List, Any, Optional
from github import Github

from a2a.skills.base import BaseSkill, SkillGroup
from core.standards_loader import StandardsLoader
from core.architectural_validator import ArchitecturalValidator
from core.compliance_integration import ComplianceIntegrationService

logger = logging.getLogger(__name__)


class ValidateRepositoryArchitectureSkill(BaseSkill):
    """
    Comprehensive repository validation against all architectural standards

    Validates a repository and returns detailed compliance report with:
    - Overall compliance score and grade
    - Violations by category with severity levels
    - Critical issues that require immediate attention
    - Prioritized improvement recommendations
    """

    def __init__(self, validator: ArchitecturalValidator):
        """Initialize skill with validator"""
        self.validator = validator

    @property
    def skill_id(self) -> str:
        return "validate_repository_architecture"

    @property
    def skill_name(self) -> str:
        return "Validate Repository Architecture"

    @property
    def skill_description(self) -> str:
        return "Comprehensive validation of repository against all architectural standards (license, documentation, terraform, deployment, etc.). Returns compliance score, violations, and improvement recommendations."

    @property
    def tags(self) -> List[str]:
        return ["architecture", "standards", "validation", "compliance", "quality"]

    @property
    def requires_authentication(self) -> bool:
        return False

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository name in format 'owner/repo' (e.g., 'patelmm79/dev-nexus')"
                },
                "validation_scope": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional: Specific standards to validate. If omitted, validates all standards. Options: license, documentation, terraform_init, multi_env, terraform_state, disaster_recovery, deployment, postgresql, ci_cd, containerization"
                },
                "include_recommendations": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include actionable improvement recommendations in response"
                }
            },
            "required": ["repository"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {"repository": "patelmm79/dev-nexus"},
                "description": "Full validation of dev-nexus repository against all standards"
            },
            {
                "input": {
                    "repository": "patelmm79/dev-nexus",
                    "validation_scope": ["license", "documentation", "terraform_init"]
                },
                "description": "Validate only license, documentation, and terraform initialization standards"
            },
            {
                "input": {
                    "repository": "my-org/my-service",
                    "include_recommendations": True
                },
                "description": "Full validation with detailed improvement recommendations"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute skill: validate repository"""
        try:
            repo_name = input_data.get("repository", "")
            if not repo_name:
                return {
                    "success": False,
                    "error": "Missing required parameter: 'repository'"
                }

            # Extract optional parameters
            scope = input_data.get("validation_scope")
            include_recommendations = input_data.get("include_recommendations", True)
            notify_agents = input_data.get("notify_agents", True)

            logger.info(f"Validating repository: {repo_name}")

            # Run validation
            report = self.validator.validate_repository(repo_name, scope=scope)

            # Convert report to dictionary
            result = {
                "success": True,
                "repository": report.repository,
                "overall_compliance_score": report.overall_compliance_score,
                "compliance_grade": report.compliance_grade,
                "summary": report.summary,
                "categories": {
                    cat_name: {
                        "compliance_score": cat_result.compliance_score,
                        "passed": cat_result.passed,
                        "checks_performed": cat_result.checks_performed,
                        "violations": [
                            {
                                "severity": v.severity,
                                "rule_id": v.rule_id,
                                "message": v.message,
                                "recommendation": v.recommendation,
                                "file_path": v.file_path
                            }
                            for v in cat_result.violations
                        ]
                    }
                    for cat_name, cat_result in report.categories.items()
                },
                "critical_violations": [
                    {
                        "severity": v.severity,
                        "rule_id": v.rule_id,
                        "category": v.category,
                        "message": v.message,
                        "recommendation": v.recommendation,
                        "file_path": v.file_path
                    }
                    for v in report.critical_violations
                ]
            }

            if include_recommendations:
                result["recommendations"] = report.recommendations

            # Coordinate with external agents via A2A protocol
            if notify_agents and hasattr(self, 'integration_service'):
                integration_results = self.integration_service.process_compliance_report(
                    repo_name, report, auto_notify=True
                )
                result["a2a_integration"] = integration_results.get("integrations", {})
                logger.info(f"Coordinated with external agents: {result['a2a_integration']}")

            logger.info(f"Validation complete: {report.repository} - Score: {report.overall_compliance_score}")
            return result

        except Exception as e:
            logger.error(f"Validation error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }


class CheckSpecificStandardSkill(BaseSkill):
    """
    Check repository against a specific architectural standard

    Validates a single standard category and returns detailed results.
    Useful for focused compliance audits on specific domains.
    """

    def __init__(self, validator: ArchitecturalValidator):
        """Initialize skill with validator"""
        self.validator = validator

    @property
    def skill_id(self) -> str:
        return "check_specific_standard"

    @property
    def skill_name(self) -> str:
        return "Check Specific Architectural Standard"

    @property
    def skill_description(self) -> str:
        return "Check a repository against a specific architectural standard (e.g., license, terraform, deployment). Returns compliance status and violations for that category only."

    @property
    def tags(self) -> List[str]:
        return ["architecture", "standards", "validation", "focused-check"]

    @property
    def requires_authentication(self) -> bool:
        return False

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository name in format 'owner/repo'"
                },
                "standard_category": {
                    "type": "string",
                    "enum": [
                        "license",
                        "documentation",
                        "terraform_init",
                        "multi_env",
                        "terraform_state",
                        "disaster_recovery",
                        "deployment",
                        "postgresql",
                        "ci_cd",
                        "containerization"
                    ],
                    "description": "The standard category to check"
                }
            },
            "required": ["repository", "standard_category"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "repository": "patelmm79/dev-nexus",
                    "standard_category": "license"
                },
                "description": "Check if repository is GPL v3.0 compliant"
            },
            {
                "input": {
                    "repository": "my-org/my-service",
                    "standard_category": "terraform_init"
                },
                "description": "Check if terraform follows unified initialization pattern"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute skill: check specific standard"""
        try:
            repo_name = input_data.get("repository", "")
            category = input_data.get("standard_category", "")

            if not repo_name or not category:
                return {
                    "success": False,
                    "error": "Missing required parameters: 'repository' and 'standard_category'"
                }

            logger.info(f"Checking {category} standard for {repo_name}")

            # Run scoped validation
            report = self.validator.validate_repository(repo_name, scope=[category])

            # Extract category result
            if category not in report.categories:
                return {
                    "success": False,
                    "error": f"Standard category '{category}' not found"
                }

            cat_result = report.categories[category]

            result = {
                "success": True,
                "repository": repo_name,
                "standard_category": category,
                "passed": cat_result.passed,
                "compliance_score": cat_result.compliance_score,
                "checks_performed": cat_result.checks_performed,
                "violations": [
                    {
                        "severity": v.severity,
                        "rule_id": v.rule_id,
                        "message": v.message,
                        "recommendation": v.recommendation,
                        "file_path": v.file_path
                    }
                    for v in cat_result.violations
                ]
            }

            logger.info(f"Check complete: {category} - Passed: {cat_result.passed}")
            return result

        except Exception as e:
            logger.error(f"Check error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }


class SuggestImprovementsSkill(BaseSkill):
    """
    Suggest architectural improvements for a repository

    Analyzes compliance violations and provides prioritized,
    actionable improvement recommendations with effort estimates.
    """

    def __init__(self, validator: ArchitecturalValidator):
        """Initialize skill with validator"""
        self.validator = validator

    @property
    def skill_id(self) -> str:
        return "suggest_improvements"

    @property
    def skill_name(self) -> str:
        return "Suggest Architectural Improvements"

    @property
    def skill_description(self) -> str:
        return "Analyze repository compliance violations and provide prioritized improvement suggestions. Recommendations are ranked by severity and include effort estimates."

    @property
    def tags(self) -> List[str]:
        return ["architecture", "recommendations", "improvements", "planning"]

    @property
    def requires_authentication(self) -> bool:
        return False

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository name in format 'owner/repo'"
                },
                "max_recommendations": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of recommendations to return (sorted by priority)"
                }
            },
            "required": ["repository"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {"repository": "patelmm79/dev-nexus"},
                "description": "Get all improvement suggestions for dev-nexus"
            },
            {
                "input": {
                    "repository": "my-org/my-service",
                    "max_recommendations": 5
                },
                "description": "Get top 5 priority improvement suggestions"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute skill: suggest improvements"""
        try:
            repo_name = input_data.get("repository", "")
            max_recommendations = input_data.get("max_recommendations", 10)

            if not repo_name:
                return {
                    "success": False,
                    "error": "Missing required parameter: 'repository'"
                }

            logger.info(f"Generating improvement suggestions for {repo_name}")

            # Run full validation
            report = self.validator.validate_repository(repo_name)

            # Prioritize recommendations
            recommendations = report.recommendations[:max_recommendations]

            # Organize by priority level
            priority_levels = {}
            for rec in recommendations:
                priority = rec.get("priority", "MEDIUM")
                if priority not in priority_levels:
                    priority_levels[priority] = []
                priority_levels[priority].append(rec)

            result = {
                "success": True,
                "repository": repo_name,
                "overall_compliance_score": report.overall_compliance_score,
                "total_violations": report.summary.get("failed_checks", 0),
                "critical_violations_count": report.summary.get("critical_violations", 0),
                "recommendations_count": len(recommendations),
                "recommendations_by_priority": priority_levels,
                "summary": {
                    "critical_actions": [
                        r for r in recommendations if r.get("priority") == "CRITICAL"
                    ],
                    "high_priority_actions": [
                        r for r in recommendations if r.get("priority") == "HIGH"
                    ]
                }
            }

            logger.info(f"Generated {len(recommendations)} improvement suggestions")
            return result

        except Exception as e:
            logger.error(f"Suggestion error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }


class ArchitecturalComplianceSkills(SkillGroup):
    """
    Skill group for architectural compliance validation

    Provides three complementary skills:
    1. validate_repository_architecture - Full validation with all standards
    2. check_specific_standard - Focused validation on single standard
    3. suggest_improvements - Prioritized improvement recommendations

    Integrates with external A2A agents:
    - dependency-orchestrator: Notifies of compliance violations affecting dependencies
    - pattern-miner: Triggers deep analysis on violations
    - monitoring-system: Records compliance metrics and trends
    """

    def __init__(self, github_client: Github = None, standards_loader: StandardsLoader = None, **kwargs):
        """
        Initialize skill group

        Args:
            github_client: PyGithub Github client (will use GITHUB_TOKEN from env if not provided)
            standards_loader: StandardsLoader instance (will create if not provided)
        """
        super().__init__(**kwargs)

        # Initialize GitHub client if not provided
        if github_client is None:
            github_token = os.environ.get("GITHUB_TOKEN")
            if not github_token:
                raise ValueError("GITHUB_TOKEN environment variable not set")
            github_client = Github(github_token)

        # Initialize standards loader if not provided
        if standards_loader is None:
            import pathlib
            repo_root = pathlib.Path(__file__).parent.parent.parent
            standards_loader = StandardsLoader(str(repo_root))

        # Create validator
        self.validator = ArchitecturalValidator(github_client, standards_loader)

        # Initialize integration service for A2A coordination
        self.integration_service = ComplianceIntegrationService()

        logger.info("Initialized ArchitecturalComplianceSkills with A2A integration")

    def get_skills(self) -> List[BaseSkill]:
        """Return all skills in this group"""
        # Create skill instances
        validate_skill = ValidateRepositoryArchitectureSkill(self.validator)
        validate_skill.integration_service = self.integration_service

        check_skill = CheckSpecificStandardSkill(self.validator)
        suggest_skill = SuggestImprovementsSkill(self.validator)

        return [
            validate_skill,
            check_skill,
            suggest_skill,
        ]
