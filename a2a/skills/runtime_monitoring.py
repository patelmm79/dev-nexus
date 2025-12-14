"""
Runtime Monitoring Skills

Skills for tracking and analyzing runtime issues from production monitoring systems
like agentic-log-attacker.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from a2a.skills.base import BaseSkill


class AddRuntimeIssueSkill(BaseSkill):
    """Record runtime issues from production monitoring"""

    def __init__(self, postgres_repo):
        self.postgres_repo = postgres_repo

    @property
    def skill_id(self) -> str:
        return "add_runtime_issue"

    @property
    def skill_name(self) -> str:
        return "Add Runtime Issue"

    @property
    def skill_description(self) -> str:
        return "Record runtime issues detected in production by monitoring systems. Links issues to patterns and tracks resolution."

    @property
    def tags(self) -> List[str]:
        return ["runtime", "monitoring", "issues", "production", "operations"]

    @property
    def requires_authentication(self) -> bool:
        return True  # Only monitoring systems can add issues

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "repository": {
                    "type": "string",
                    "description": "Repository name in format 'owner/repo'"
                },
                "service_type": {
                    "type": "string",
                    "enum": ["cloud_run", "cloud_functions", "cloud_build", "gce", "gke", "app_engine", "other"],
                    "description": "Type of GCP service"
                },
                "issue_type": {
                    "type": "string",
                    "enum": ["error", "performance", "crash", "timeout", "memory", "security", "other"],
                    "description": "Category of issue"
                },
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Issue severity level"
                },
                "log_snippet": {
                    "type": "string",
                    "description": "Relevant log excerpt (max 1000 chars)"
                },
                "root_cause": {
                    "type": "string",
                    "description": "Identified or suspected root cause"
                },
                "suggested_fix": {
                    "type": "string",
                    "description": "Recommended fix or mitigation"
                },
                "pattern_reference": {
                    "type": "string",
                    "description": "Name of pattern this issue relates to (optional)"
                },
                "github_issue_url": {
                    "type": "string",
                    "description": "URL of created GitHub issue (optional)"
                },
                "metrics": {
                    "type": "object",
                    "description": "Performance metrics at time of issue",
                    "properties": {
                        "error_rate": {"type": "number"},
                        "latency_p95": {"type": "number"},
                        "throughput": {"type": "number"}
                    }
                }
            },
            "required": ["repository", "service_type", "issue_type", "severity", "log_snippet"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "repository": "user/api-service",
                    "service_type": "cloud_run",
                    "issue_type": "error",
                    "severity": "high",
                    "log_snippet": "ERROR: Redis connection pool exhausted",
                    "root_cause": "Connection pool size too small for traffic",
                    "suggested_fix": "Increase pool_size from 10 to 50",
                    "pattern_reference": "Redis session caching",
                    "metrics": {
                        "error_rate": 0.15,
                        "latency_p95": 2500
                    }
                },
                "description": "Report Redis connection pool issue"
            },
            {
                "input": {
                    "repository": "user/webhook-service",
                    "service_type": "cloud_functions",
                    "issue_type": "timeout",
                    "severity": "medium",
                    "log_snippet": "Function timeout after 60s",
                    "root_cause": "External API call hanging"
                },
                "description": "Report function timeout issue"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record runtime issue in knowledge base

        Returns:
            success: bool
            issue_id: str (timestamp-based ID)
            pattern_updated: bool (if pattern was updated)
            similar_issues: List (other repos with similar issues)
        """
        try:
            repository = input_data['repository']

            # Load knowledge base
            kb_data = await self.postgres_repo.load()

            # Ensure repository exists
            if repository not in kb_data.get('repositories', {}):
                kb_data.setdefault('repositories', {})[repository] = {
                    'latest_patterns': {},
                    'deployment': {},
                    'dependencies': {},
                    'testing': {},
                    'security': {},
                    'runtime_issues': [],
                    'production_metrics': {},
                    'history': []
                }

            repo_data = kb_data['repositories'][repository]

            # Create runtime issue record
            issue_id = datetime.now().isoformat()
            runtime_issue = {
                "issue_id": issue_id,
                "detected_at": issue_id,
                "issue_type": input_data['issue_type'],
                "severity": input_data['severity'],
                "service_type": input_data['service_type'],
                "logs": input_data['log_snippet'][:1000],  # Limit size
                "root_cause": input_data.get('root_cause'),
                "suggested_fix": input_data.get('suggested_fix'),
                "pattern_reference": input_data.get('pattern_reference'),
                "github_issue": input_data.get('github_issue_url'),
                "status": "open",
                "metrics": input_data.get('metrics', {}),
                "resolution_time": None
            }

            # Add to repository's runtime issues
            if 'runtime_issues' not in repo_data:
                repo_data['runtime_issues'] = []
            repo_data['runtime_issues'].append(runtime_issue)

            # Update pattern if referenced
            pattern_updated = False
            if pattern_ref := input_data.get('pattern_reference'):
                pattern_updated = self._update_pattern_with_issue(
                    repo_data, pattern_ref, runtime_issue
                )

            # Find similar issues in other repos
            similar_issues = self._find_similar_issues(
                kb_data, input_data['issue_type'], input_data.get('pattern_reference')
            )

            # Update production metrics
            if metrics := input_data.get('metrics'):
                repo_data['production_metrics'] = {
                    **repo_data.get('production_metrics', {}),
                    **metrics,
                    'last_updated': issue_id
                }

            # Save knowledge base
            await self.postgres_repo.save(kb_data)

            return {
                "success": True,
                "issue_id": issue_id,
                "repository": repository,
                "severity": input_data['severity'],
                "pattern_updated": pattern_updated,
                "similar_issues": similar_issues[:5],  # Top 5
                "message": f"Runtime issue recorded for {repository}"
            }

        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _update_pattern_with_issue(self, repo_data: Dict, pattern_name: str, issue: Dict) -> bool:
        """Update pattern with runtime issue information"""
        try:
            patterns = repo_data.get('latest_patterns', {}).get('patterns', [])

            # Find matching pattern
            for pattern in patterns:
                if isinstance(pattern, dict) and pattern.get('name') == pattern_name:
                    if 'runtime_issues' not in pattern:
                        pattern['runtime_issues'] = []
                    pattern['runtime_issues'].append({
                        'issue_id': issue['issue_id'],
                        'severity': issue['severity'],
                        'issue_type': issue['issue_type']
                    })
                    return True
                elif isinstance(pattern, str) and pattern == pattern_name:
                    # Convert string pattern to dict
                    idx = patterns.index(pattern)
                    patterns[idx] = {
                        'name': pattern,
                        'runtime_issues': [{
                            'issue_id': issue['issue_id'],
                            'severity': issue['severity'],
                            'issue_type': issue['issue_type']
                        }]
                    }
                    return True

            return False
        except Exception:
            return False

    def _find_similar_issues(self, kb_data: Dict, issue_type: str, pattern: Optional[str]) -> List[Dict]:
        """Find similar issues in other repositories"""
        similar = []

        for repo_name, repo_data in kb_data.get('repositories', {}).items():
            for issue in repo_data.get('runtime_issues', []):
                if issue['issue_type'] == issue_type:
                    if pattern and issue.get('pattern_reference') == pattern:
                        similar.append({
                            'repository': repo_name,
                            'issue_id': issue['issue_id'],
                            'severity': issue['severity'],
                            'root_cause': issue.get('root_cause')
                        })

        return similar


class GetPatternHealthSkill(BaseSkill):
    """Analyze runtime health of a pattern across repositories"""

    def __init__(self, postgres_repo):
        self.postgres_repo = postgres_repo

    @property
    def skill_id(self) -> str:
        return "get_pattern_health"

    @property
    def skill_name(self) -> str:
        return "Get Pattern Health"

    @property
    def skill_description(self) -> str:
        return "Analyze the production health of a pattern by examining runtime issues across all repositories using it."

    @property
    def tags(self) -> List[str]:
        return ["patterns", "health", "analysis", "runtime", "monitoring"]

    @property
    def requires_authentication(self) -> bool:
        return False

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "pattern_name": {
                    "type": "string",
                    "description": "Name of pattern to analyze"
                },
                "time_range_days": {
                    "type": "integer",
                    "description": "Number of days to analyze (default: 30)",
                    "default": 30
                },
                "severity_threshold": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Minimum severity to include",
                    "default": "low"
                }
            },
            "required": ["pattern_name"]
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "pattern_name": "Redis session caching",
                    "time_range_days": 30
                },
                "description": "Check health of Redis caching pattern"
            },
            {
                "input": {
                    "pattern_name": "JWT authentication",
                    "severity_threshold": "high"
                },
                "description": "Check for critical/high severity issues with JWT pattern"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze pattern health across all repositories

        Returns:
            health_score: float (0-1, where 1 is perfect)
            total_repos: int (repos using this pattern)
            repos_with_issues: int
            issues: List of issues found
            recommendation: str
        """
        try:
            pattern_name = input_data['pattern_name']
            time_range_days = input_data.get('time_range_days', 30)
            severity_threshold = input_data.get('severity_threshold', 'low')

            # Load knowledge base
            kb_data = await self.postgres_repo.load()

            # Find repos using this pattern
            repos_with_pattern = []
            repos_with_issues = []
            all_issues = []

            cutoff_date = (datetime.now() - timedelta(days=time_range_days)).isoformat()

            for repo_name, repo_data in kb_data.get('repositories', {}).items():
                # Check if repo uses this pattern
                patterns = repo_data.get('latest_patterns', {}).get('patterns', [])
                has_pattern = False

                for pattern in patterns:
                    if isinstance(pattern, dict) and pattern.get('name') == pattern_name:
                        has_pattern = True
                    elif isinstance(pattern, str) and pattern == pattern_name:
                        has_pattern = True

                if has_pattern:
                    repos_with_pattern.append(repo_name)

                    # Check for runtime issues related to this pattern
                    runtime_issues = repo_data.get('runtime_issues', [])
                    pattern_issues = [
                        issue for issue in runtime_issues
                        if issue.get('pattern_reference') == pattern_name
                        and issue.get('detected_at', '') >= cutoff_date
                        and self._meets_severity_threshold(issue.get('severity'), severity_threshold)
                    ]

                    if pattern_issues:
                        repos_with_issues.append(repo_name)
                        all_issues.extend([{
                            **issue,
                            'repository': repo_name
                        } for issue in pattern_issues])

            # Calculate health score
            total_repos = len(repos_with_pattern)
            repos_with_issues_count = len(repos_with_issues)

            if total_repos == 0:
                health_score = 1.0  # No repos = no issues
                recommendation = f"Pattern '{pattern_name}' is not currently in use."
            else:
                health_score = 1.0 - (repos_with_issues_count / total_repos)

                # Generate recommendation
                if health_score < 0.5:
                    recommendation = f"⚠️ CRITICAL: Pattern '{pattern_name}' has issues in {repos_with_issues_count}/{total_repos} repos. Immediate review recommended."
                elif health_score < 0.7:
                    recommendation = f"⚠️ WARNING: Pattern '{pattern_name}' has issues in {repos_with_issues_count}/{total_repos} repos. Monitor closely."
                elif health_score < 0.9:
                    recommendation = f"✓ Pattern '{pattern_name}' is mostly healthy with minor issues in {repos_with_issues_count}/{total_repos} repos."
                else:
                    recommendation = f"✅ Pattern '{pattern_name}' is healthy across all {total_repos} repositories."

            # Issue breakdown by severity
            issue_breakdown = {
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            }
            for issue in all_issues:
                severity = issue.get('severity', 'low')
                issue_breakdown[severity] = issue_breakdown.get(severity, 0) + 1

            return {
                "success": True,
                "pattern": pattern_name,
                "health_score": round(health_score, 2),
                "total_repos": total_repos,
                "repos_with_issues": repos_with_issues_count,
                "repos_with_issues_list": repos_with_issues,
                "issue_count": len(all_issues),
                "issue_breakdown": issue_breakdown,
                "issues": all_issues[:10],  # Top 10 most recent
                "recommendation": recommendation,
                "time_range_days": time_range_days
            }

        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _meets_severity_threshold(self, severity: str, threshold: str) -> bool:
        """Check if severity meets threshold"""
        severity_levels = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        return severity_levels.get(severity, 0) >= severity_levels.get(threshold, 0)


class QueryKnownIssuesSkill(BaseSkill):
    """Query for known runtime issues matching criteria"""

    def __init__(self, postgres_repo):
        self.postgres_repo = postgres_repo

    @property
    def skill_id(self) -> str:
        return "query_known_issues"

    @property
    def skill_name(self) -> str:
        return "Query Known Issues"

    @property
    def skill_description(self) -> str:
        return "Search for previously encountered runtime issues matching specified criteria. Useful for checking if an issue has been seen before."

    @property
    def tags(self) -> List[str]:
        return ["issues", "search", "runtime", "history"]

    @property
    def requires_authentication(self) -> bool:
        return False

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "issue_type": {
                    "type": "string",
                    "enum": ["error", "performance", "crash", "timeout", "memory", "security", "other"],
                    "description": "Type of issue to search for"
                },
                "pattern": {
                    "type": "string",
                    "description": "Pattern name (optional)"
                },
                "service_type": {
                    "type": "string",
                    "enum": ["cloud_run", "cloud_functions", "cloud_build", "gce", "gke", "app_engine", "other"],
                    "description": "Service type (optional)"
                },
                "severity": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Severity level (optional)"
                },
                "status": {
                    "type": "string",
                    "enum": ["open", "investigating", "fixed", "false_positive"],
                    "description": "Issue status (optional)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return",
                    "default": 10
                }
            }
        }

    @property
    def examples(self) -> List[Dict[str, Any]]:
        return [
            {
                "input": {
                    "issue_type": "timeout",
                    "service_type": "cloud_run"
                },
                "description": "Find timeout issues in Cloud Run"
            },
            {
                "input": {
                    "pattern": "Redis session caching",
                    "severity": "high"
                },
                "description": "Find high-severity issues with Redis pattern"
            }
        ]

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query for matching runtime issues

        Returns:
            issues: List of matching issues
            count: Total count
            repositories_affected: List of repos with these issues
        """
        try:
            # Load knowledge base
            kb_data = await self.postgres_repo.load()

            matching_issues = []
            repositories_affected = set()

            # Search all repositories
            for repo_name, repo_data in kb_data.get('repositories', {}).items():
                runtime_issues = repo_data.get('runtime_issues', [])

                for issue in runtime_issues:
                    if self._matches_criteria(issue, input_data):
                        matching_issues.append({
                            **issue,
                            'repository': repo_name
                        })
                        repositories_affected.add(repo_name)

            # Sort by detected_at (most recent first)
            matching_issues.sort(key=lambda x: x.get('detected_at', ''), reverse=True)

            # Apply limit
            limit = input_data.get('limit', 10)
            limited_issues = matching_issues[:limit]

            return {
                "success": True,
                "count": len(matching_issues),
                "returned": len(limited_issues),
                "issues": limited_issues,
                "repositories_affected": list(repositories_affected),
                "query": {
                    k: v for k, v in input_data.items()
                    if k not in ['limit']
                }
            }

        except Exception as e:
            import traceback
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def _matches_criteria(self, issue: Dict, criteria: Dict) -> bool:
        """Check if issue matches search criteria"""
        # Check issue_type
        if 'issue_type' in criteria:
            if issue.get('issue_type') != criteria['issue_type']:
                return False

        # Check pattern
        if 'pattern' in criteria:
            if issue.get('pattern_reference') != criteria['pattern']:
                return False

        # Check service_type
        if 'service_type' in criteria:
            if issue.get('service_type') != criteria['service_type']:
                return False

        # Check severity
        if 'severity' in criteria:
            if issue.get('severity') != criteria['severity']:
                return False

        # Check status
        if 'status' in criteria:
            if issue.get('status') != criteria['status']:
                return False

        return True


# Skill group for easy registration
class RuntimeMonitoringSkills:
    """Group of runtime monitoring skills"""

    def __init__(self, postgres_repo):
        self.postgres_repo = postgres_repo

    def get_skills(self) -> List[BaseSkill]:
        """Get all runtime monitoring skills"""
        return [
            AddRuntimeIssueSkill(self.postgres_repo),
            GetPatternHealthSkill(self.postgres_repo),
            QueryKnownIssuesSkill(self.postgres_repo)
        ]
