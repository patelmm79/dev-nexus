"""
Architectural Compliance A2A Integration

Coordinates with external agents when compliance violations are detected:
- dependency-orchestrator: Notifies of architectural changes affecting dependencies
- pattern-miner: Triggers deep analysis on compliance violations
- Monitoring systems: Records compliance issues for tracking
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from a2a.client import ExternalAgentRegistry
from core.architectural_validator import ValidationReport, Violation

logger = logging.getLogger(__name__)


class ComplianceIntegrationService:
    """
    Coordinate A2A communication for architectural compliance validation

    Integrates with external agents to:
    1. Notify dependency-orchestrator of critical compliance failures
    2. Trigger pattern-miner for deep code analysis
    3. Alert monitoring systems of compliance drift
    4. Track compliance issues over time
    """

    def __init__(self):
        """Initialize integration service with external agent registry"""
        self.registry = ExternalAgentRegistry()
        logger.info("Initialized ComplianceIntegrationService")

    # ================================================
    # Dependency-Orchestrator Integration
    # ================================================

    def notify_compliance_violation(
        self,
        repository: str,
        report: ValidationReport,
        violation_type: str = "architectural_drift"
    ) -> Dict[str, Any]:
        """
        Notify dependency-orchestrator of compliance violations

        Alerts the orchestrator when critical compliance issues are found
        that might affect dependent services.

        Args:
            repository: Repository name (owner/repo)
            report: ValidationReport from compliance check
            violation_type: Type of violation (architectural_drift, standards_mismatch, etc.)

        Returns:
            Notification result from orchestrator
        """
        orchestrator = self.registry.get_agent('dependency-orchestrator')
        if not orchestrator:
            logger.debug("dependency-orchestrator not configured")
            return {"status": "skipped", "reason": "agent_not_configured"}

        try:
            # Filter for critical violations only
            critical_violations = [
                v for v in report.critical_violations
                if v.severity == "critical"
            ]

            if not critical_violations:
                logger.debug(f"No critical violations to report for {repository}")
                return {"status": "no_critical_violations"}

            result = orchestrator.execute_skill(
                skill_id="notify_compliance_violation",
                input_data={
                    "repository": repository,
                    "violation_type": violation_type,
                    "timestamp": datetime.now().isoformat(),
                    "compliance_score": report.overall_compliance_score,
                    "compliance_grade": report.compliance_grade,
                    "critical_violations_count": len(critical_violations),
                    "violations": [
                        {
                            "rule_id": v.rule_id,
                            "category": v.category,
                            "severity": v.severity,
                            "message": v.message,
                            "recommendation": v.recommendation,
                            "file_path": v.file_path
                        }
                        for v in critical_violations
                    ],
                    "affected_categories": list(set(v.category for v in critical_violations))
                }
            )

            logger.info(f"Notified orchestrator of violations in {repository}: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to notify orchestrator: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def query_dependency_context(
        self,
        repository: str
    ) -> Dict[str, Any]:
        """
        Query dependency-orchestrator for repository context

        Gets information about dependent services and their compliance needs.

        Args:
            repository: Repository name (owner/repo)

        Returns:
            Dependency context from orchestrator
        """
        orchestrator = self.registry.get_agent('dependency-orchestrator')
        if not orchestrator:
            logger.debug("dependency-orchestrator not configured")
            return {}

        try:
            result = orchestrator.execute_skill(
                skill_id="get_repository_dependencies",
                input_data={
                    "repository": repository,
                    "include_consumers": True,
                    "include_providers": True
                }
            )

            logger.debug(f"Retrieved dependency context for {repository}")
            return result

        except Exception as e:
            logger.warning(f"Failed to query dependency context: {e}")
            return {}

    # ================================================
    # Pattern-Miner Integration (Deep Analysis)
    # ================================================

    def trigger_deep_analysis(
        self,
        repository: str,
        report: ValidationReport,
        focus_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Trigger pattern-miner for deep code analysis on compliance violations

        When critical compliance issues are found, request pattern-miner
        to perform detailed code analysis to identify root causes and patterns.

        Args:
            repository: Repository name (owner/repo)
            report: ValidationReport from compliance check
            focus_areas: Optional list of specific areas to analyze deeply

        Returns:
            Deep analysis result from pattern-miner
        """
        pattern_miner = self.registry.get_agent('pattern-miner')
        if not pattern_miner:
            logger.debug("pattern-miner not configured")
            return {"status": "skipped", "reason": "agent_not_configured"}

        try:
            # Determine focus areas based on violations
            if not focus_areas:
                focus_areas = list(set(v.category for v in report.critical_violations))

            if not focus_areas:
                logger.debug(f"No focus areas for deep analysis of {repository}")
                return {"status": "no_violations"}

            result = pattern_miner.execute_skill(
                skill_id="trigger_deep_analysis",
                input_data={
                    "repository": repository,
                    "timestamp": datetime.now().isoformat(),
                    "focus_areas": focus_areas,
                    "compliance_score": report.overall_compliance_score,
                    "violations_summary": {
                        "total": len(report.critical_violations),
                        "by_category": {
                            cat: len([v for v in report.critical_violations if v.category == cat])
                            for cat in focus_areas
                        }
                    },
                    "analysis_objectives": [
                        "Identify architectural patterns contributing to violations",
                        "Find similar patterns in other projects",
                        "Recommend refactoring strategies",
                        "Suggest reusable solutions"
                    ]
                }
            )

            logger.info(f"Triggered deep analysis for {repository}: {result}")
            return result

        except Exception as e:
            logger.error(f"Failed to trigger deep analysis: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    # ================================================
    # Monitoring Systems Integration
    # ================================================

    def record_compliance_snapshot(
        self,
        repository: str,
        report: ValidationReport
    ) -> Dict[str, Any]:
        """
        Record compliance snapshot for monitoring systems

        Sends compliance metrics to monitoring systems for tracking trends
        and alerting on compliance drift.

        Args:
            repository: Repository name (owner/repo)
            report: ValidationReport from compliance check

        Returns:
            Recording result
        """
        monitoring = self.registry.get_agent('monitoring-system')
        if not monitoring:
            logger.debug("monitoring-system not configured")
            return {"status": "skipped", "reason": "agent_not_configured"}

        try:
            result = monitoring.execute_skill(
                skill_id="record_compliance_metric",
                input_data={
                    "repository": repository,
                    "timestamp": datetime.now().isoformat(),
                    "compliance_score": report.overall_compliance_score,
                    "compliance_grade": report.compliance_grade,
                    "summary": {
                        "total_checks": report.summary.get("total_checks", 0),
                        "passed_checks": report.summary.get("passed_checks", 0),
                        "failed_checks": report.summary.get("failed_checks", 0),
                        "critical_violations": report.summary.get("critical_violations", 0),
                        "high_violations": report.summary.get("high_violations", 0),
                        "medium_violations": report.summary.get("medium_violations", 0),
                        "low_violations": report.summary.get("low_violations", 0)
                    },
                    "categories": {
                        cat: {
                            "score": cat_result.compliance_score,
                            "passed": cat_result.passed
                        }
                        for cat, cat_result in report.categories.items()
                    }
                }
            )

            logger.info(f"Recorded compliance snapshot for {repository}")
            return result

        except Exception as e:
            logger.warning(f"Failed to record compliance snapshot: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    # ================================================
    # Coordinated Workflows
    # ================================================

    def process_compliance_report(
        self,
        repository: str,
        report: ValidationReport,
        auto_notify: bool = True
    ) -> Dict[str, Any]:
        """
        Process compliance report and coordinate with external agents

        Orchestrates the full integration workflow:
        1. Records compliance snapshot
        2. Notifies orchestrator of critical violations
        3. Triggers pattern-miner for deep analysis
        4. Updates dependency context

        Args:
            repository: Repository name (owner/repo)
            report: ValidationReport from compliance check
            auto_notify: Whether to automatically notify agents

        Returns:
            Coordination results
        """
        logger.info(f"Processing compliance report for {repository}")

        results = {
            "repository": repository,
            "compliance_score": report.overall_compliance_score,
            "integrations": {}
        }

        if not auto_notify:
            return results

        # Record compliance metric
        results["integrations"]["monitoring"] = self.record_compliance_snapshot(
            repository, report
        )

        # Notify orchestrator only if there are critical violations
        if report.critical_violations:
            results["integrations"]["orchestrator"] = self.notify_compliance_violation(
                repository, report
            )

            # Trigger deep analysis for critical violations
            results["integrations"]["pattern_miner"] = self.trigger_deep_analysis(
                repository, report
            )

        # Query dependency context
        results["integrations"]["dependency_context"] = self.query_dependency_context(
            repository
        )

        logger.info(f"Compliance report processing complete for {repository}")
        return results

    def get_integration_status(self) -> Dict[str, Any]:
        """
        Get status of external agent integrations

        Returns:
            Status of each configured external agent
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "agents": {
                agent_name: {
                    "configured": agent is not None,
                    "url": agent.url if agent else None,
                    "authenticated": agent.authenticated if agent else False
                }
                for agent_name, agent in [
                    ("dependency-orchestrator", self.registry.get_agent("dependency-orchestrator")),
                    ("pattern-miner", self.registry.get_agent("pattern-miner")),
                    ("monitoring-system", self.registry.get_agent("monitoring-system"))
                ]
            }
        }
