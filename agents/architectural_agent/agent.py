"""Simple architectural analysis agent.

The agent inspects a repository (local path or git URL) and produces
recommendations on which parts of that repository look like architectural
artifacts that might be better maintained in this repository (the
architecture-kb). This is a lightweight heuristic-based tool intended as
an initial assistant for architectural extraction and discovery.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ArchitecturalAgent:
    """Analyzes a repository and suggests which parts look like architecture docs/configs.

    Usage:
        agent = ArchitecturalAgent()
        report = agent.analyze_repo('/path/or/git/url')
    """

    def __init__(self, work_dir: Optional[str] = None):
        self.work_dir = work_dir

    def _clone_repo(self, repo: str) -> str:
        tmp = tempfile.mkdtemp(prefix="arch-agent-")
        logger.info("Cloning %s into %s", repo, tmp)
        try:
            subprocess.check_call(["git", "clone", "--depth", "1", repo, tmp])
        except Exception:
            shutil.rmtree(tmp, ignore_errors=True)
            raise
        return tmp

    def analyze_repo(self, repo: str, clone_if_url: bool = True) -> Dict[str, List[Dict]]:
        """Analyze `repo`, which may be a local path or a git URL.

        Returns a dict with `recommendations` key containing list of suggestions.
        """
        cleanup = False
        path = repo
        try:
            if (repo.startswith("http://") or repo.startswith("https://") or repo.endswith('.git')) and clone_if_url:
                path = self._clone_repo(repo)
                cleanup = True

            path_obj = Path(path)
            if not path_obj.exists():
                raise FileNotFoundError(path)

            findings = self._scan_tree(path_obj)

            recommendations = self._map_findings_to_targets(findings)

            return {"repository": str(path_obj), "recommendations": recommendations}
        finally:
            if cleanup:
                shutil.rmtree(path, ignore_errors=True)

    def _scan_tree(self, root: Path) -> Dict[str, List[Path]]:
        """Scan repository tree for architectural artifacts and return categorized findings."""
        findings: Dict[str, List[Path]] = {
            "infrastructure": [],
            "ci_cd": [],
            "kubernetes": [],
            "monitoring": [],
            "database": [],
            "docker": [],
            "docs": [],
            "frontend": [],
            "services": [],
            "terraform": [],
            "other": [],
        }

        for dirpath, dirnames, filenames in os.walk(root):
            rel = os.path.relpath(dirpath, root)
            if rel == ".":
                rel = ""

            # Quick filename checks
            for fn in filenames:
                fp = Path(dirpath) / fn
                lower = fn.lower()

                if lower in ("dockerfile",):
                    findings["docker"].append(fp)
                if lower.endswith(('.yml', '.yaml')):
                    # CI files
                    if fn.lower() in ("cloudbuild.yaml", "circleci.yml", "jenkinsfile") or ".github" in dirpath:
                        findings["ci_cd"].append(fp)
                    # Helm or Kubernetes manifests
                    if "k8s" in dirpath.lower() or "kubernetes" in dirpath.lower() or "helm" in dirpath.lower() or fn.lower().endswith(('.yaml',)):
                        # heuristic: look for typical k8s keys
                        try:
                            text = fp.read_text(encoding='utf-8', errors='ignore')
                            if "kind:" in text and "apiVersion:" in text:
                                findings["kubernetes"].append(fp)
                        except Exception:
                            pass
                if lower == 'cloudbuild.yaml':
                    findings['ci_cd'].append(fp)
                if 'terraform' in dirpath.lower() or fn.lower().endswith('.tf'):
                    findings['terraform'].append(fp)
                if 'monitor' in dirpath.lower() or 'prometheus' in dirpath.lower() or 'grafana' in dirpath.lower():
                    findings['monitoring'].append(fp)
                if 'docker' in dirpath.lower() or fn.lower().startswith('docker'):
                    findings['docker'].append(fp)
                if 'postgres' in dirpath.lower() or 'postgresql' in dirpath.lower() or fn.lower().startswith('migrate'):
                    findings['database'].append(fp)
                if fn.lower().endswith(('.md',)) and ('architecture' in fn.lower() or 'arch' in dirpath.lower() or 'design' in dirpath.lower()):
                    findings['docs'].append(fp)
                if any(p in dirpath.lower() for p in ('frontend', 'web', 'react', 'tsx', 'components')) or fn.lower().endswith(('.tsx', '.jsx')):
                    findings['frontend'].append(fp)
                if any(p in dirpath.lower() for p in ('service', 'services', 'api', 'server')) or fn.lower().endswith(('.py', '.go', '.java', '.js', '.ts')):
                    findings['services'].append(fp)

        # Deduplicate and sort
        for k, v in list(findings.items()):
            uniq = sorted(set(v))
            findings[k] = uniq

        return findings

    def _map_findings_to_targets(self, findings: Dict[str, List[Path]]) -> List[Dict]:
        """Map categorized findings to recommended target locations in the architecture-kb repository."""
        recs: List[Dict] = []

        # Infrastructure/terraform -> /terraform or docs/POSTGRESQL_SETUP.md
        if findings.get('terraform'):
            recs.append({
                "type": "terraform",
                "count": len(findings['terraform']),
                "suggested_target": "terraform/ (this repository)",
                "why": "Contains .tf files or terraform directories that define infra; centralizing Terraform modules helps reuse and governance",
                "examples": [str(p) for p in findings['terraform'][:10]]
            })

        if findings.get('ci_cd'):
            recs.append({
                "type": "ci_cd",
                "count": len(findings['ci_cd']),
                "suggested_target": ".github/workflows/ or docs/CI (this repository)",
                "why": "CI configuration and build pipelines are architectural artifacts useful to centralize for reproducible builds",
                "examples": [str(p) for p in findings['ci_cd'][:10]]
            })

        if findings.get('kubernetes'):
            recs.append({
                "type": "kubernetes",
                "count": len(findings['kubernetes']),
                "suggested_target": "deploy/k8s/ or docs/Kubernetes (this repository)",
                "why": "Kubernetes manifests and Helm charts are deployment architecture and should be reviewed for standardization",
                "examples": [str(p) for p in findings['kubernetes'][:10]]
            })

        if findings.get('monitoring'):
            recs.append({
                "type": "monitoring",
                "count": len(findings['monitoring']),
                "suggested_target": "config/monitoring.yaml or docs/monitoring (this repository)",
                "why": "Prometheus/Grafana configs belong in centralized monitoring practices",
                "examples": [str(p) for p in findings['monitoring'][:10]]
            })

        if findings.get('database'):
            recs.append({
                "type": "database",
                "count": len(findings['database']),
                "suggested_target": "migrations/ or docs/POSTGRESQL_SETUP.md",
                "why": "Database schema and migration scripts are critical infra artifacts",
                "examples": [str(p) for p in findings['database'][:10]]
            })

        if findings.get('docs'):
            recs.append({
                "type": "docs",
                "count": len(findings['docs']),
                "suggested_target": "docs/ or pattern_dashboard.html",
                "why": "Architecture/design docs should be curated in the architecture knowledge base",
                "examples": [str(p) for p in findings['docs'][:10]]
            })

        if findings.get('frontend'):
            recs.append({
                "type": "frontend",
                "count": len(findings['frontend']),
                "suggested_target": "frontend-components-to-add/ or docs/frontend-guidance",
                "why": "Frontend components and integration guides can be cataloged for reuse",
                "examples": [str(p) for p in findings['frontend'][:10]]
            })

        if findings.get('services'):
            recs.append({
                "type": "services",
                "count": len(findings['services']),
                "suggested_target": "a2a/ or core/ modules depending on runtime",
                "why": "Microservice code and server components may be better modularized as reusable skills/services",
                "examples": [str(p) for p in findings['services'][:10]]
            })

        if findings.get('docker'):
            recs.append({
                "type": "docker",
                "count": len(findings['docker']),
                "suggested_target": "docker/ or docs/CONTAINERIZATION.md",
                "why": "Containerization patterns and standard Dockerfiles are part of architecture",
                "examples": [str(p) for p in findings['docker'][:10]]
            })

        if not recs:
            recs.append({
                "type": "none",
                "count": 0,
                "suggested_target": "",
                "why": "No obvious architecture artifacts discovered by heuristics",
                "examples": []
            })

        return recs

    def save_json(self, output_path: str, report: Dict):
        Path(output_path).write_text(json.dumps(report, indent=2), encoding='utf-8')


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Run the architectural agent against a repository')
    parser.add_argument('repo', help='Local path or git URL to analyze')
    parser.add_argument('--out', help='Output JSON path', default='architectural_report.json')

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    agent = ArchitecturalAgent()
    report = agent.analyze_repo(args.repo)
    agent.save_json(args.out, report)
    print('Saved report to', args.out)
