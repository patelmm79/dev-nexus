"""
Documentation Standards Checker Service

Checks repositories for conformity to documentation standards defined in DOCUMENTATION_STANDARDS.md.
This service enforces the standards established for the dev-nexus project.
"""

import re
from typing import Dict, Any, List, Optional
from pathlib import Path
from github import Github
from github.Repository import Repository


class DocumentationStandardsChecker:
    """Check repositories for conformity to documentation standards"""

    def __init__(self, github_client: Github, standards_content: Optional[str] = None):
        """
        Initialize the checker

        Args:
            github_client: Authenticated GitHub client
            standards_content: Content of DOCUMENTATION_STANDARDS.md (optional, will fetch if not provided)
        """
        self.github_client = github_client
        self.standards_content = standards_content

        # Priority files from DOCUMENTATION_STANDARDS.md
        self.priority_files = {
            "critical": ["README.md", "CLAUDE.md", "QUICK_START.md"],
            "high": ["EXTENDING_DEV_NEXUS.md", "API.md", "AgentCard"],
            "medium": ["ARCHITECTURE.md", "LESSONS_LEARNED.md", "TROUBLESHOOTING.md"],
            "low": ["CONTRIBUTING.md", "CHANGELOG.md", "FAQ.md"]
        }

    def check_repository(self, repository: str, check_all_docs: bool = False) -> Dict[str, Any]:
        """
        Check a repository for documentation standards conformity

        Args:
            repository: Repository in format 'owner/repo'
            check_all_docs: If True, check all .md files; if False, check priority files only

        Returns:
            Dictionary with check results
        """
        try:
            repo = self.github_client.get_repo(repository)

            # Get documentation files to check
            doc_files = self._get_documentation_files(repo, check_all_docs)

            if not doc_files:
                return {
                    "success": False,
                    "error": "No documentation files found",
                    "repository": repository
                }

            # Check each file
            results = []
            for file_path, content, priority in doc_files:
                file_result = self._check_file(file_path, content, priority, repo)
                results.append(file_result)

            # Calculate overall compliance
            total_violations = sum(len(r.get("violations", [])) for r in results)
            total_checks = sum(r.get("checks_performed", 0) for r in results)
            compliance_score = 1.0 - (total_violations / max(total_checks, 1))

            # Categorize by severity
            critical_violations = []
            high_violations = []
            medium_violations = []

            for result in results:
                for violation in result.get("violations", []):
                    if violation.get("severity") == "critical":
                        critical_violations.append(violation)
                    elif violation.get("severity") == "high":
                        high_violations.append(violation)
                    else:
                        medium_violations.append(violation)

            # Determine overall status
            if critical_violations:
                status = "non_compliant"
                status_emoji = "❌"
            elif high_violations:
                status = "needs_improvement"
                status_emoji = "⚠️"
            elif medium_violations:
                status = "mostly_compliant"
                status_emoji = "👍"
            else:
                status = "compliant"
                status_emoji = "✅"

            return {
                "success": True,
                "repository": repository,
                "status": status,
                "status_emoji": status_emoji,
                "compliance_score": round(compliance_score, 2),
                "summary": {
                    "total_files_checked": len(results),
                    "total_violations": total_violations,
                    "critical_violations": len(critical_violations),
                    "high_violations": len(high_violations),
                    "medium_violations": len(medium_violations)
                },
                "file_results": results,
                "critical_violations": critical_violations[:10],  # Top 10
                "recommendations": self._generate_recommendations(critical_violations, high_violations, medium_violations)
            }

        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": f"Failed to check repository: {str(e)}",
                "traceback": traceback.format_exc(),
                "repository": repository
            }

    def _get_documentation_files(self, repo: Repository, check_all: bool) -> List[tuple]:
        """
        Get documentation files to check

        Returns:
            List of tuples: (file_path, content, priority)
        """
        files = []

        if check_all:
            # Get all .md files
            contents = repo.get_contents("")
            while contents:
                file_content = contents.pop(0)
                if file_content.type == "dir":
                    contents.extend(repo.get_contents(file_content.path))
                elif file_content.path.endswith(".md"):
                    try:
                        content = file_content.decoded_content.decode('utf-8')
                        priority = self._get_file_priority(file_content.path)
                        files.append((file_content.path, content, priority))
                    except:
                        pass  # Skip files that can't be decoded
        else:
            # Check priority files only
            for priority_level, priority_files in self.priority_files.items():
                for file_path in priority_files:
                    try:
                        file_content = repo.get_contents(file_path)
                        content = file_content.decoded_content.decode('utf-8')
                        files.append((file_path, content, priority_level))
                    except:
                        # File doesn't exist, add as violation
                        files.append((file_path, None, priority_level))

        return files

    def _get_file_priority(self, file_path: str) -> str:
        """Determine priority level of a file"""
        filename = Path(file_path).name

        for priority_level, priority_files in self.priority_files.items():
            if filename in priority_files or file_path in priority_files:
                return priority_level

        # Check if in docs/ directory
        if file_path.startswith("docs/"):
            return "medium"

        # Examples directory
        if file_path.startswith("examples/"):
            return "high"

        return "low"

    def _check_file(self, file_path: str, content: Optional[str], priority: str, repo: Repository) -> Dict[str, Any]:
        """Check a single documentation file against standards"""
        violations = []
        checks_performed = 0

        # If file doesn't exist
        if content is None:
            if priority in ["critical", "high"]:
                violations.append({
                    "type": "missing_file",
                    "severity": "critical" if priority == "critical" else "high",
                    "message": f"Missing {priority}-priority documentation file: {file_path}",
                    "file": file_path
                })
            return {
                "file": file_path,
                "priority": priority,
                "violations": violations,
                "checks_performed": 1
            }

        # Check 1: Completeness - Required sections
        checks_performed += 1
        required_sections = self._check_completeness(content, file_path, priority)
        violations.extend(required_sections)

        # Check 2: Up-to-date - Version indicators and update stamps
        checks_performed += 1
        update_violations = self._check_update_stamps(content, file_path, priority)
        violations.extend(update_violations)

        # Check 3: Accuracy - Valid file paths
        checks_performed += 1
        path_violations = self._check_file_paths(content, file_path, repo)
        violations.extend(path_violations)

        # Check 4: Code examples - Proper formatting
        checks_performed += 1
        code_violations = self._check_code_examples(content, file_path)
        violations.extend(code_violations)

        # Check 5: Consistency - Terminology
        checks_performed += 1
        terminology_violations = self._check_terminology(content, file_path)
        violations.extend(terminology_violations)

        # Check 6: Internal links
        checks_performed += 1
        link_violations = self._check_internal_links(content, file_path, repo)
        violations.extend(link_violations)

        return {
            "file": file_path,
            "priority": priority,
            "violations": violations,
            "checks_performed": checks_performed,
            "violation_count": len(violations)
        }

    def _check_completeness(self, content: str, file_path: str, priority: str) -> List[Dict[str, Any]]:
        """Check for required sections based on file type"""
        violations = []

        # For README.md
        if file_path == "README.md":
            required = ["## Overview", "## Installation", "## Usage"]
            for section in required:
                if section.lower() not in content.lower():
                    violations.append({
                        "type": "missing_section",
                        "severity": "high",
                        "message": f"README.md missing required section: {section}",
                        "file": file_path,
                        "section": section
                    })

        # For guides (EXTENDING, QUICK_START, etc.)
        if "EXTENDING" in file_path or "QUICK_START" in file_path:
            required = ["## Prerequisites", "## Examples"]
            for section in required:
                if section.lower() not in content.lower():
                    violations.append({
                        "type": "missing_section",
                        "severity": "medium",
                        "message": f"Guide missing recommended section: {section}",
                        "file": file_path,
                        "section": section
                    })

        # All documentation should have overview
        if not re.search(r'##\s*(Overview|Introduction|About)', content, re.IGNORECASE):
            violations.append({
                "type": "missing_section",
                "severity": "medium",
                "message": "Documentation missing overview/introduction section",
                "file": file_path
            })

        return violations

    def _check_update_stamps(self, content: str, file_path: str, priority: str) -> List[Dict[str, Any]]:
        """Check for version indicators and update stamps"""
        violations = []

        # Check for update stamps in critical/high priority files
        if priority in ["critical", "high"]:
            # Look for update indicators
            has_update_stamp = bool(re.search(r'(Last Updated|Updated:|UPDATED|v\d+\.\d+)', content, re.IGNORECASE))

            if not has_update_stamp:
                violations.append({
                    "type": "missing_update_stamp",
                    "severity": "medium",
                    "message": f"{priority.title()}-priority file missing version indicator or update stamp",
                    "file": file_path,
                    "recommendation": "Add 'Last Updated: YYYY-MM-DD' or version indicator"
                })

        return violations

    def _check_file_paths(self, content: str, file_path: str, repo: Repository) -> List[Dict[str, Any]]:
        """Check that referenced file paths exist"""
        violations = []

        # Find file path references (basic patterns)
        # Matches: `path/to/file.py`, path/to/file.py, "path/to/file.py"
        path_patterns = [
            r'`([a-zA-Z0-9_\-/\.]+\.[a-zA-Z]{2,4})`',  # `file.py`
            r'"([a-zA-Z0-9_\-/\.]+\.[a-zA-Z]{2,4})"',  # "file.py"
            r'([a-zA-Z0-9_\-/]+\.py)',  # Simple .py references
        ]

        found_paths = set()
        for pattern in path_patterns:
            matches = re.findall(pattern, content)
            found_paths.update(matches)

        # Check a sample of paths (avoid too many API calls)
        sample_paths = list(found_paths)[:5]

        for path in sample_paths:
            # Skip URLs and special paths
            if path.startswith('http') or path.startswith('www') or '{{' in path:
                continue

            try:
                repo.get_contents(path)
            except:
                violations.append({
                    "type": "invalid_file_path",
                    "severity": "medium",
                    "message": f"Referenced file path may not exist: {path}",
                    "file": file_path,
                    "referenced_path": path
                })

        return violations

    def _check_code_examples(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Check code examples for proper formatting"""
        violations = []

        # Check for code blocks
        code_blocks = re.findall(r'```(\w*)\n(.*?)```', content, re.DOTALL)

        if code_blocks:
            for i, (language, code) in enumerate(code_blocks):
                # Check if language is specified
                if not language:
                    violations.append({
                        "type": "code_example_no_language",
                        "severity": "low",
                        "message": f"Code block #{i+1} missing language specifier",
                        "file": file_path,
                        "recommendation": "Add language after opening ``` (e.g., ```python)"
                    })

        # Check for inline code that should be blocks
        inline_code_with_newlines = re.findall(r'`([^`]*\n[^`]*)`', content)
        if inline_code_with_newlines:
            violations.append({
                "type": "code_formatting",
                "severity": "low",
                "message": "Inline code contains newlines - should use code block instead",
                "file": file_path,
                "count": len(inline_code_with_newlines)
            })

        return violations

    def _check_terminology(self, content: str, file_path: str) -> List[Dict[str, Any]]:
        """Check for consistent terminology"""
        violations = []

        # Define inconsistent terminology pairs
        # (wrong_term, correct_term, case_sensitive)
        terminology_rules = [
            (r'\bhandler\b', 'skill', False),  # Use "skill" not "handler"
            (r'\bcapability\b', 'skill', False),  # Use "skill" not "capability"
        ]

        for wrong_pattern, correct_term, case_sensitive in terminology_rules:
            flags = 0 if case_sensitive else re.IGNORECASE
            matches = re.findall(wrong_pattern, content, flags)

            if matches:
                violations.append({
                    "type": "inconsistent_terminology",
                    "severity": "low",
                    "message": f"Uses inconsistent term '{matches[0]}' instead of '{correct_term}'",
                    "file": file_path,
                    "count": len(matches),
                    "recommendation": f"Replace with '{correct_term}' for consistency"
                })

        return violations

    def _check_internal_links(self, content: str, file_path: str, repo: Repository) -> List[Dict[str, Any]]:
        """Check internal markdown links"""
        violations = []

        # Find markdown links: [text](link)
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)

        for link_text, link_url in links:
            # Skip external links
            if link_url.startswith('http://') or link_url.startswith('https://'):
                continue

            # Skip anchors only
            if link_url.startswith('#'):
                continue

            # Remove anchor from link
            link_path = link_url.split('#')[0]

            if not link_path:
                continue

            # Make relative to repository root
            if not link_path.startswith('/'):
                # Resolve relative to current file
                current_dir = str(Path(file_path).parent)
                if current_dir == '.':
                    resolved_path = link_path
                else:
                    resolved_path = str(Path(current_dir) / link_path)
            else:
                resolved_path = link_path.lstrip('/')

            # Check if file exists
            try:
                repo.get_contents(resolved_path)
            except:
                violations.append({
                    "type": "broken_internal_link",
                    "severity": "medium",
                    "message": f"Internal link may be broken: [{link_text}]({link_url})",
                    "file": file_path,
                    "link_url": link_url,
                    "resolved_path": resolved_path
                })

        return violations

    def _generate_recommendations(self, critical: List, high: List, medium: List) -> List[str]:
        """Generate actionable recommendations based on violations"""
        recommendations = []

        if critical:
            recommendations.append("🔴 CRITICAL: Address missing critical documentation files immediately")

        if high:
            recommendations.append("⚠️ HIGH PRIORITY: Update high-priority documentation files with missing sections")

        if medium:
            recommendations.append("📝 MEDIUM: Add version indicators and update stamps to documentation")

        # Specific recommendations
        violation_types = {}
        for v in critical + high + medium:
            vtype = v.get("type")
            violation_types[vtype] = violation_types.get(vtype, 0) + 1

        if violation_types.get("missing_section", 0) > 0:
            recommendations.append(f"Add {violation_types['missing_section']} missing required sections")

        if violation_types.get("missing_update_stamp", 0) > 0:
            recommendations.append("Add 'Last Updated' stamps to documentation files")

        if violation_types.get("broken_internal_link", 0) > 0:
            recommendations.append(f"Fix {violation_types['broken_internal_link']} broken internal links")

        if violation_types.get("invalid_file_path", 0) > 0:
            recommendations.append("Update file path references to match current structure")

        if not recommendations:
            recommendations.append("✅ Documentation meets all standards - great work!")

        return recommendations
