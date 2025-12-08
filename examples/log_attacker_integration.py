"""
Example Integration Code for agentic-log-attacker

This file shows how to integrate agentic-log-attacker with dev-nexus
for complete development-to-production feedback loop.

Add this code to your agentic-log-attacker project.
"""

import os
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime


class DevNexusIntegration:
    """
    Integration client for reporting issues to dev-nexus and querying pattern data.

    Usage:
        integration = DevNexusIntegration(
            dev_nexus_url=os.getenv("DEV_NEXUS_URL"),
            token=os.getenv("DEV_NEXUS_TOKEN")
        )

        # Report an issue
        await integration.report_runtime_issue(
            repository="user/api-service",
            issue_data={...}
        )
    """

    def __init__(self, dev_nexus_url: str, token: str):
        self.dev_nexus_url = dev_nexus_url.rstrip('/')
        self.token = token
        self.client = httpx.AsyncClient(
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )

    async def report_runtime_issue(
        self,
        repository: str,
        service_type: str,
        issue_type: str,
        severity: str,
        log_snippet: str,
        root_cause: Optional[str] = None,
        suggested_fix: Optional[str] = None,
        pattern_reference: Optional[str] = None,
        github_issue_url: Optional[str] = None,
        metrics: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Report a runtime issue to dev-nexus for pattern learning.

        Args:
            repository: Repository name (e.g., "user/api-service")
            service_type: GCP service type (cloud_run, cloud_functions, etc.)
            issue_type: Type of issue (error, performance, crash, etc.)
            severity: Severity level (critical, high, medium, low)
            log_snippet: Relevant log excerpt (max 1000 chars)
            root_cause: Identified root cause (optional)
            suggested_fix: Recommended fix (optional)
            pattern_reference: Related pattern name (optional)
            github_issue_url: URL of created GitHub issue (optional)
            metrics: Performance metrics (error_rate, latency_p95, etc.)

        Returns:
            Response from dev-nexus with issue_id and similar issues
        """
        try:
            response = await self.client.post(
                f"{self.dev_nexus_url}/a2a/execute",
                json={
                    "skill_id": "add_runtime_issue",
                    "input": {
                        "repository": repository,
                        "service_type": service_type,
                        "issue_type": issue_type,
                        "severity": severity,
                        "log_snippet": log_snippet[:1000],  # Limit size
                        "root_cause": root_cause,
                        "suggested_fix": suggested_fix,
                        "pattern_reference": pattern_reference,
                        "github_issue_url": github_issue_url,
                        "metrics": metrics or {}
                    }
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error reporting to dev-nexus: {e}")
            return {"success": False, "error": str(e)}

    async def query_patterns_for_service(
        self,
        repository: str
    ) -> Dict[str, Any]:
        """
        Query dev-nexus for known patterns in a service.
        Useful for adding context to log analysis.

        Args:
            repository: Repository name

        Returns:
            Patterns used in the repository
        """
        try:
            response = await self.client.post(
                f"{self.dev_nexus_url}/a2a/execute",
                json={
                    "skill_id": "get_deployment_info",
                    "input": {
                        "repository": repository,
                        "include_lessons": False
                    }
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error querying patterns: {e}")
            return {"success": False, "error": str(e)}

    async def check_known_issues(
        self,
        issue_type: str,
        pattern: Optional[str] = None,
        service_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if similar issues have been seen before.

        Args:
            issue_type: Type of issue (error, performance, etc.)
            pattern: Pattern name (optional)
            service_type: GCP service type (optional)

        Returns:
            List of similar issues found in other repos
        """
        try:
            query = {"issue_type": issue_type}
            if pattern:
                query["pattern"] = pattern
            if service_type:
                query["service_type"] = service_type

            response = await self.client.post(
                f"{self.dev_nexus_url}/a2a/execute",
                json={
                    "skill_id": "query_known_issues",
                    "input": query
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error checking known issues: {e}")
            return {"success": False, "error": str(e)}

    async def get_pattern_health(
        self,
        pattern_name: str,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """
        Get health score for a pattern across all repos.

        Args:
            pattern_name: Name of pattern to check
            time_range_days: Days to analyze (default: 30)

        Returns:
            Health score and issue breakdown
        """
        try:
            response = await self.client.post(
                f"{self.dev_nexus_url}/a2a/execute",
                json={
                    "skill_id": "get_pattern_health",
                    "input": {
                        "pattern_name": pattern_name,
                        "time_range_days": time_range_days
                    }
                }
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting pattern health: {e}")
            return {"success": False, "error": str(e)}

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()


# Example usage in agentic-log-attacker workflow

async def example_integration_workflow():
    """
    Example: How to use DevNexusIntegration in your log analysis workflow
    """

    # Initialize integration
    integration = DevNexusIntegration(
        dev_nexus_url=os.getenv("DEV_NEXUS_URL"),
        token=os.getenv("DEV_NEXUS_TOKEN")
    )

    try:
        # Step 1: Get patterns for the service being monitored
        repository = "user/api-service"
        patterns_response = await integration.query_patterns_for_service(repository)

        if patterns_response.get("success"):
            patterns = patterns_response.get("deployment", {}).get("patterns", [])
            print(f"Known patterns in {repository}: {patterns}")

        # Step 2: Analyze logs (your existing logic)
        # ... your log analysis code here ...

        # Simulated error detection
        error_detected = {
            "type": "error",
            "message": "Redis connection pool exhausted",
            "count": 45,
            "service_type": "cloud_run"
        }

        # Step 3: Check if this issue has been seen before
        known_issues = await integration.check_known_issues(
            issue_type="error",
            pattern="Redis session caching",
            service_type="cloud_run"
        )

        if known_issues.get("success") and known_issues.get("count", 0) > 0:
            print(f"Similar issues found: {known_issues['count']}")
            print("This issue has occurred before in:")
            for issue in known_issues.get("issues", []):
                print(f"  - {issue['repository']} (severity: {issue['severity']})")

        # Step 4: Report the issue to dev-nexus
        result = await integration.report_runtime_issue(
            repository=repository,
            service_type="cloud_run",
            issue_type="error",
            severity="high",
            log_snippet=error_detected["message"],
            root_cause="Connection pool size (10) too small for traffic volume",
            suggested_fix="Increase pool_size to 50 and max_overflow to 20",
            pattern_reference="Redis session caching",
            github_issue_url="https://github.com/user/api-service/issues/234",
            metrics={
                "error_rate": 0.15,
                "latency_p95": 2500,
                "throughput": 150
            }
        )

        if result.get("success"):
            print(f"Issue reported successfully: {result['issue_id']}")
            print(f"Similar issues in other repos: {len(result.get('similar_issues', []))}")

        # Step 5: Check pattern health
        health = await integration.get_pattern_health(
            pattern_name="Redis session caching",
            time_range_days=30
        )

        if health.get("success"):
            print(f"Pattern health score: {health['health_score']}")
            print(f"Repos with issues: {health['repos_with_issues']}/{health['total_repos']}")
            print(f"Recommendation: {health['recommendation']}")

    finally:
        await integration.close()


# Integration in Issue Creation Agent

class IssueCreationAgentWithDevNexus:
    """
    Enhanced Issue Creation Agent with dev-nexus integration.

    Add this to your agentic-log-attacker/src/agents/issue_creation.py
    """

    def __init__(self, github_client, dev_nexus_integration: DevNexusIntegration):
        self.github_client = github_client
        self.dev_nexus = dev_nexus_integration

    async def create_issue_with_context(
        self,
        repository: str,
        issue_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create GitHub issue with enhanced context from dev-nexus.

        Args:
            repository: Repository name
            issue_data: Issue information from log analysis

        Returns:
            Created issue details
        """

        # Step 1: Check for similar issues in history
        known_issues = await self.dev_nexus.check_known_issues(
            issue_type=issue_data["type"],
            service_type=issue_data.get("service_type")
        )

        # Step 2: Enhance issue description with historical context
        description = f"""## Issue Detected

{issue_data['description']}

## Analysis

{issue_data['analysis']}

## Recommended Fix

{issue_data['recommendation']}
"""

        # Add historical context if available
        if known_issues.get("success") and known_issues.get("count", 0) > 0:
            description += f"""

## Historical Context

This issue has been seen before in {known_issues['count']} instance(s):

"""
            for issue in known_issues.get("issues", [])[:3]:
                description += f"- **{issue['repository']}**: {issue.get('root_cause', 'N/A')} (severity: {issue['severity']})\n"

        # Step 3: Create GitHub issue
        issue = self.github_client.create_issue(
            repo=repository,
            title=issue_data['title'],
            body=description,
            labels=[issue_data['severity'], 'production', 'automated']
        )

        # Step 4: Report to dev-nexus
        await self.dev_nexus.report_runtime_issue(
            repository=repository,
            service_type=issue_data.get('service_type', 'cloud_run'),
            issue_type=issue_data['type'],
            severity=issue_data['severity'],
            log_snippet=issue_data.get('logs', '')[:1000],
            root_cause=issue_data.get('root_cause'),
            suggested_fix=issue_data['recommendation'],
            github_issue_url=issue.html_url,
            metrics=issue_data.get('metrics')
        )

        return {
            "issue_url": issue.html_url,
            "issue_number": issue.number,
            "reported_to_devnexus": True
        }


# Configuration for integration

def setup_devnexus_integration():
    """
    Add this to your agentic-log-attacker startup code.

    In your main.py or __init__.py:
    """

    # Check if dev-nexus integration is enabled
    if os.getenv("DEVNEXUS_INTEGRATION_ENABLED", "false").lower() == "true":
        dev_nexus_url = os.getenv("DEV_NEXUS_URL")
        dev_nexus_token = os.getenv("DEV_NEXUS_TOKEN")

        if not dev_nexus_url or not dev_nexus_token:
            print("WARNING: DEV_NEXUS_URL or DEV_NEXUS_TOKEN not set")
            return None

        print(f"Dev-Nexus integration enabled: {dev_nexus_url}")
        return DevNexusIntegration(dev_nexus_url, dev_nexus_token)
    else:
        print("Dev-Nexus integration disabled")
        return None


# Environment variables to add to agentic-log-attacker .env file:
"""
# Dev-Nexus Integration
DEVNEXUS_INTEGRATION_ENABLED=true
DEV_NEXUS_URL=https://dev-nexus-xyz.run.app
DEV_NEXUS_TOKEN=your-service-account-token

# Optional: Report all issues or only high severity
DEVNEXUS_REPORT_THRESHOLD=medium  # critical, high, medium, low
"""


if __name__ == "__main__":
    import asyncio

    # Run example
    asyncio.run(example_integration_workflow())
