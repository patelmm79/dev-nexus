"""
Documentation Standards Skills

Skills for checking repositories against documentation standards.
"""

import os
from typing import Dict, Any, List
from github import Github

from a2a.skills.base import BaseSkill


class CheckDocumentationStandardsSkill(BaseSkill):
    """Check repository documentation for conformity to standards"""

    def __init__(self, standards_file_path: str):
        """
        Initialize the skill

        Args:
            standards_file_path: Path to DOCUMENTATION_STANDARDS.md file
        """
        self.standards_file_path = standards_file_path

        # Load standards content
        try:
            with open(standards_file_path, 'r', encoding='utf-8') as f:
                self.standards_content = f.read()
        except Exception as e:
            print(f"Warning: Could not load standards file: {e}")
            self.standards_content = None

    @property
    def skill_id(self) -> str:
        return "check_documentation_standards"

    @property
    def skill_name(self) -> str:
        return "Check Documentation Standards"

    @property
    def skill_description(self) -> str:
        return "Check repository documentation for conformity to documentation standards. Validates completeness, accuracy, consistency, update stamps, code examples, and internal links."

    @property
    def tags(self) -> List[str]:
        return ["documentation", "standards", "quality", "compliance", "review"]

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
                "check_all_docs": {
                    "type": "boolean",
                    "description": "If true, check all .md files; if false, check priority files only (README, CLAUDE.md, etc.)",
                    "default": False
                }
            },
            "required": ["repository"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "repository": "patelmm79/dev-nexus",
                    "check_all_docs": False
                },
                "description": "Check priority documentation files in dev-nexus"
            },
            {
                "input": {
                    "repository": "patelmm79/dev-nexus",
                    "check_all_docs": True
                },
                "description": "Comprehensive check of all documentation files"
            },
            {
                "input": {
                    "repository": "my-org/my-project"
                },
                "description": "Check documentation standards for any repository"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check repository documentation standards

        Input:
            - repository: str - Repository name (format: "owner/repo")
            - check_all_docs: bool - Check all docs or priority only (optional, default: False)

        Output:
            - status: Compliance status (compliant, mostly_compliant, needs_improvement, non_compliant)
            - compliance_score: Float 0-1 indicating overall compliance
            - summary: Violation counts by severity
            - file_results: Per-file check results
            - critical_violations: Top 10 critical violations
            - recommendations: Actionable recommendations
        """
        try:
            from core.documentation_standards_checker import DocumentationStandardsChecker

            repository = input_data.get('repository')
            check_all_docs = input_data.get('check_all_docs', False)

            if not repository:
                return {
                    "success": False,
                    "error": "Missing required parameter: 'repository'"
                }

            # Validate repository format
            if '/' not in repository:
                return {
                    "success": False,
                    "error": "Invalid repository format. Expected 'owner/repo'"
                }

            # Get GitHub client
            github_token = os.environ.get('GITHUB_TOKEN')
            if not github_token:
                return {
                    "success": False,
                    "error": "GITHUB_TOKEN not configured"
                }

            github_client = Github(github_token)

            # Initialize checker
            checker = DocumentationStandardsChecker(
                github_client=github_client,
                standards_content=self.standards_content
            )

            # Check repository
            result = checker.check_repository(
                repository=repository,
                check_all_docs=check_all_docs
            )

            return result

        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": f"Failed to check documentation standards: {str(e)}",
                "traceback": traceback.format_exc()
            }


class ValidateDocumentationUpdateSkill(BaseSkill):
    """Validate that documentation has been updated after code changes"""

    def __init__(self):
        pass

    @property
    def skill_id(self) -> str:
        return "validate_documentation_update"

    @property
    def skill_name(self) -> str:
        return "Validate Documentation Update"

    @property
    def skill_description(self) -> str:
        return "Validate that documentation has been updated after code changes. Checks for recent documentation commits when code has been modified."

    @property
    def tags(self) -> List[str]:
        return ["documentation", "validation", "git", "compliance"]

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
                "since_commit": {
                    "type": "string",
                    "description": "Check changes since this commit SHA",
                    "default": None
                },
                "days": {
                    "type": "integer",
                    "description": "Check changes in last N days (if since_commit not provided)",
                    "default": 7
                }
            },
            "required": ["repository"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "repository": "patelmm79/dev-nexus",
                    "days": 7
                },
                "description": "Check if docs were updated in last 7 days when code changed"
            },
            {
                "input": {
                    "repository": "patelmm79/dev-nexus",
                    "since_commit": "abc123"
                },
                "description": "Check if docs were updated since specific commit"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate documentation updates

        Input:
            - repository: str - Repository name (format: "owner/repo")
            - since_commit: str - Check since this commit (optional)
            - days: int - Check last N days if since_commit not provided (default: 7)

        Output:
            - code_changes: List of code file changes
            - doc_changes: List of documentation changes
            - validation: Whether docs were updated appropriately
            - warnings: Any issues found
        """
        try:
            from datetime import datetime, timedelta

            repository = input_data.get('repository')
            since_commit = input_data.get('since_commit')
            days = input_data.get('days', 7)

            if not repository:
                return {
                    "success": False,
                    "error": "Missing required parameter: 'repository'"
                }

            # Get GitHub client
            github_token = os.environ.get('GITHUB_TOKEN')
            if not github_token:
                return {
                    "success": False,
                    "error": "GITHUB_TOKEN not configured"
                }

            github_client = Github(github_token)
            repo = github_client.get_repo(repository)

            # Determine time range
            if since_commit:
                # Get commit date
                commit = repo.get_commit(since_commit)
                since_date = commit.commit.author.date
            else:
                since_date = datetime.now() - timedelta(days=days)

            # Get commits since date
            commits = repo.get_commits(since=since_date)

            code_changes = []
            doc_changes = []

            for commit in commits:
                files = commit.files
                for file in files:
                    if file.filename.endswith('.md'):
                        doc_changes.append({
                            "file": file.filename,
                            "commit": commit.sha[:7],
                            "date": commit.commit.author.date.isoformat(),
                            "message": commit.commit.message.split('\n')[0]
                        })
                    elif self._is_code_file(file.filename):
                        code_changes.append({
                            "file": file.filename,
                            "commit": commit.sha[:7],
                            "date": commit.commit.author.date.isoformat(),
                            "message": commit.commit.message.split('\n')[0]
                        })

            # Validate
            warnings = []

            if code_changes and not doc_changes:
                warnings.append({
                    "severity": "high",
                    "message": f"Code changes detected ({len(code_changes)} files) but no documentation updates found",
                    "recommendation": "Review and update documentation to reflect code changes"
                })

            # Check if code changes are in core files
            core_changes = [c for c in code_changes if self._is_core_file(c["file"])]
            if core_changes and not doc_changes:
                warnings.append({
                    "severity": "critical",
                    "message": f"Core architecture changes detected ({len(core_changes)} files) with no documentation updates",
                    "recommendation": "Update ALL documentation per DOCUMENTATION_STANDARDS.md"
                })

            # Validation result
            if not code_changes:
                validation_status = "no_changes"
                validation_message = "No code changes detected in specified timeframe"
            elif doc_changes:
                validation_status = "compliant"
                validation_message = "Documentation updates found alongside code changes"
            else:
                validation_status = "non_compliant"
                validation_message = "Code changes without corresponding documentation updates"

            return {
                "success": True,
                "repository": repository,
                "timeframe": {
                    "since_date": since_date.isoformat(),
                    "since_commit": since_commit
                },
                "validation": {
                    "status": validation_status,
                    "message": validation_message
                },
                "changes": {
                    "code_files": len(code_changes),
                    "doc_files": len(doc_changes),
                    "code_changes": code_changes[:10],  # Top 10
                    "doc_changes": doc_changes[:10]  # Top 10
                },
                "warnings": warnings,
                "recommendations": self._generate_recommendations(code_changes, doc_changes, warnings)
            }

        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": f"Failed to validate documentation updates: {str(e)}",
                "traceback": traceback.format_exc()
            }

    def _is_code_file(self, filename: str) -> bool:
        """Check if file is a code file"""
        code_extensions = ['.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.h']
        return any(filename.endswith(ext) for ext in code_extensions)

    def _is_core_file(self, filename: str) -> bool:
        """Check if file is a core/critical file"""
        core_patterns = ['server.py', 'executor.py', 'registry.py', '/core/', '/a2a/']
        return any(pattern in filename for pattern in core_patterns)

    def _generate_recommendations(self, code_changes: List, doc_changes: List, warnings: List) -> List[str]:
        """Generate recommendations based on changes"""
        recommendations = []

        if warnings:
            recommendations.append("⚠️ Review DOCUMENTATION_STANDARDS.md for update requirements")

        if code_changes and not doc_changes:
            recommendations.append("📝 Update documentation to reflect recent code changes")
            recommendations.append("✅ Add version indicators or 'Last Updated' stamps")

        if any(w["severity"] == "critical" for w in warnings):
            recommendations.append("🔴 CRITICAL: Update ALL documentation after architecture changes")

        if not recommendations:
            recommendations.append("✅ Documentation update practices look good!")

        return recommendations


# Skill group for easy registration
class DocumentationStandardsSkills:
    """Group of documentation standards skills"""

    def __init__(self, standards_file_path: str):
        self.standards_file_path = standards_file_path

    def get_skills(self) -> List[BaseSkill]:
        """Get all documentation standards skills"""
        return [
            CheckDocumentationStandardsSkill(self.standards_file_path),
            ValidateDocumentationUpdateSkill()
        ]
