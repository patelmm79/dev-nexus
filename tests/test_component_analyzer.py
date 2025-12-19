"""
Unit tests for Component Analysis Engine

Tests ComponentScanner, VectorCacheManager, and CentralityCalculator classes.
"""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime

from core.component_analyzer import ComponentScanner, CentralityCalculator
from schemas.knowledge_base_v2 import Component, KnowledgeBaseV2, RepositoryMetadata, PatternEntry


class TestComponentScanner(unittest.TestCase):
    """Tests for ComponentScanner class"""

    def setUp(self):
        """Set up test fixtures"""
        self.scanner = ComponentScanner(min_loc=10)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_root = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up temp directory"""
        self.temp_dir.cleanup()

    def create_python_file(self, filename: str, content: str):
        """Helper to create a Python file for testing"""
        file_path = self.repo_root / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w') as f:
            f.write(content)
        return file_path

    def test_scanner_initialization(self):
        """Test scanner initializes with min_loc"""
        self.assertEqual(self.scanner.min_loc, 10)

    def test_detect_api_client_component(self):
        """Test detection of API client component"""
        client_code = '''
"""GitHub API Client"""

import requests

class GitHubClient:
    def get_user(self, username):
        return requests.get(f"https://api.github.com/users/{username}")

    def create_issue(self, repo, title, body):
        return requests.post(f"https://api.github.com/repos/{repo}/issues", json={
            "title": title,
            "body": body
        })
'''
        self.create_python_file("github_client.py", client_code)
        components = self.scanner.scan_repository(str(self.repo_root), "test/repo")

        self.assertGreater(len(components), 0)
        api_clients = [c for c in components if c.component_type == "api_client"]
        self.assertGreater(len(api_clients), 0)

    def test_detect_infrastructure_component(self):
        """Test detection of infrastructure component"""
        utils_code = '''
"""Retry logic utility"""

class RetryHandler:
    def __init__(self, max_retries=3):
        self.max_retries = max_retries

    def retry_on_failure(self, func, *args):
        for attempt in range(self.max_retries):
            try:
                return func(*args)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
'''
        self.create_python_file("utils/retry.py", utils_code)
        components = self.scanner.scan_repository(str(self.repo_root), "test/repo")

        infrastructure = [c for c in components if c.component_type == "infrastructure"]
        self.assertGreater(len(infrastructure), 0)

    def test_component_metadata_extraction(self):
        """Test that component metadata is correctly extracted"""
        code = '''
"""Test Component"""

class TestClass:
    def public_method(self):
        pass

    def _private_method(self):
        pass

    def another_method(self, x, y):
        return x + y
'''
        self.create_python_file("test_module.py", code)
        components = self.scanner.scan_repository(str(self.repo_root), "test/repo")

        self.assertGreater(len(components), 0)
        comp = components[0]
        self.assertIsNotNone(comp.name)
        self.assertIsNotNone(comp.component_type)
        self.assertGreater(len(comp.files), 0)
        self.assertIn("python", comp.language.lower())

    def test_lines_of_code_calculation(self):
        """Test LOC is calculated correctly"""
        code = '\n'.join([f"line {i}" for i in range(50)])
        self.create_python_file("big_file.py", code)
        components = self.scanner.scan_repository(str(self.repo_root), "test/repo")

        self.assertGreater(len(components), 0)
        self.assertGreater(components[0].lines_of_code, 40)

    def test_ignore_small_files(self):
        """Test that small files (below min_loc) are ignored"""
        small_code = "# Small file\nprint('hello')"
        self.create_python_file("small.py", small_code)
        components = self.scanner.scan_repository(str(self.repo_root), "test/repo")

        # Should be empty or very small
        self.assertEqual(len(components), 0)

    def test_ignore_special_directories(self):
        """Test that __pycache__, venv, etc. are ignored"""
        venv_code = "# Should be ignored"
        self.create_python_file("venv/lib/test.py", venv_code)
        components = self.scanner.scan_repository(str(self.repo_root), "test/repo")

        # Should not find components in venv
        self.assertEqual(len(components), 0)

    def test_deployment_component_extraction(self):
        """Test extraction of Terraform files as deployment components"""
        tf_code = '''
resource "google_cloud_run_service" "api" {
  name = "api-service"
  location = "us-central1"
}
'''
        self.create_python_file("main.tf", tf_code)
        components = self.scanner.scan_repository(str(self.repo_root), "test/repo")

        deployment = [c for c in components if c.component_type == "deployment_pattern"]
        self.assertGreater(len(deployment), 0)


class TestCentralityCalculator(unittest.TestCase):
    """Tests for CentralityCalculator class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create mock KB data
        self.kb_data = {
            "patelmm79/dev-nexus": {
                "problem_domain": "infrastructure and architectural tooling",
                "dependencies": {"consumers": ["repo1", "repo2", "repo3", "repo4"]},
                "latest_patterns": {}
            },
            "patelmm79/agentic-log-attacker": {
                "problem_domain": "log analysis service",
                "dependencies": {"consumers": []},
                "latest_patterns": {}
            }
        }
        self.calculator = CentralityCalculator(self.kb_data)

    def test_calculator_initialization(self):
        """Test calculator initializes with KB data"""
        self.assertIsNotNone(self.calculator.kb_data)
        self.assertEqual(len(self.calculator.kb_data), 2)

    def test_repository_purpose_scoring(self):
        """Test repository purpose scoring"""
        dev_nexus_score = self.calculator._score_repository_purpose("patelmm79/dev-nexus")
        app_score = self.calculator._score_repository_purpose("patelmm79/agentic-log-attacker")

        # Infrastructure repo should score higher than application repo
        self.assertGreater(dev_nexus_score, app_score)
        self.assertGreaterEqual(dev_nexus_score, 0.7)
        self.assertLess(app_score, 0.5)

    def test_usage_count_scoring(self):
        """Test usage count scoring"""
        mock_comp = type('Component', (), {})()
        score = self.calculator._score_usage_count(mock_comp, "patelmm79/dev-nexus")

        # dev-nexus should score high
        self.assertGreater(score, 0.7)

    def test_dependency_centrality_scoring(self):
        """Test dependency centrality scoring"""
        dev_nexus_centrality = self.calculator._score_dependency_centrality("patelmm79/dev-nexus")
        app_centrality = self.calculator._score_dependency_centrality("patelmm79/agentic-log-attacker")

        # dev-nexus is central, app is peripheral
        self.assertGreater(dev_nexus_centrality, app_centrality)

    def test_canonical_score_calculation(self):
        """Test canonical score calculation across candidates"""
        mock_component = type('Component', (), {
            'cyclomatic_complexity': 5.0,
            'lines_of_code': 200
        })()

        scores = self.calculator.calculate_canonical_score(
            mock_component,
            ["patelmm79/dev-nexus", "patelmm79/agentic-log-attacker"]
        )

        self.assertEqual(len(scores), 2)
        self.assertIn("patelmm79/dev-nexus", scores)
        self.assertIn("patelmm79/agentic-log-attacker", scores)

        # dev-nexus should score higher as canonical location
        dev_nexus_score = scores["patelmm79/dev-nexus"]["canonical_score"]
        app_score = scores["patelmm79/agentic-log-attacker"]["canonical_score"]
        self.assertGreater(dev_nexus_score, app_score)

    def test_scoring_transparency(self):
        """Test that scoring includes factor breakdown"""
        mock_component = type('Component', (), {
            'cyclomatic_complexity': 5.0,
            'lines_of_code': 200
        })()

        scores = self.calculator.calculate_canonical_score(
            mock_component,
            ["patelmm79/dev-nexus"]
        )

        result = scores["patelmm79/dev-nexus"]
        self.assertIn("factors", result)
        self.assertIn("weights", result)
        self.assertIn("reasoning", result)

        # All factors should be present
        factors = result["factors"]
        self.assertIn("repository_purpose", factors)
        self.assertIn("usage_count", factors)
        self.assertIn("dependency_centrality", factors)
        self.assertIn("maintenance_activity", factors)
        self.assertIn("component_complexity", factors)
        self.assertIn("first_implementation", factors)

    def test_scoring_weights_sum_to_one(self):
        """Test that scoring weights sum to 1.0"""
        mock_component = type('Component', (), {
            'cyclomatic_complexity': 5.0,
            'lines_of_code': 200
        })()

        scores = self.calculator.calculate_canonical_score(
            mock_component,
            ["patelmm79/dev-nexus"]
        )

        weights = scores["patelmm79/dev-nexus"]["weights"]
        total_weight = sum(weights.values())
        self.assertAlmostEqual(total_weight, 1.0, places=5)


class TestComponentModel(unittest.TestCase):
    """Tests for Component data model"""

    def test_component_creation(self):
        """Test creating a Component instance"""
        comp = Component(
            component_id="test-123",
            name="TestComponent",
            component_type="api_client",
            repository="test/repo",
            files=["test.py"],
            language="python",
            first_seen=datetime.now()
        )

        self.assertEqual(comp.component_id, "test-123")
        self.assertEqual(comp.name, "TestComponent")
        self.assertEqual(comp.component_type, "api_client")
        self.assertEqual(comp.repository, "test/repo")

    def test_component_optional_fields(self):
        """Test Component with optional fields"""
        comp = Component(
            component_id="test-123",
            name="TestComponent",
            component_type="infrastructure",
            repository="test/repo",
            files=["utils.py"],
            language="python",
            api_signature="retry(), backoff()",
            imports=["requests", "time"],
            keywords=["retry", "backoff", "resilience"],
            lines_of_code=150,
            cyclomatic_complexity=8.5,
            public_methods=["retry", "backoff"],
            first_seen=datetime.now()
        )

        self.assertEqual(comp.api_signature, "retry(), backoff()")
        self.assertEqual(len(comp.imports), 2)
        self.assertEqual(len(comp.keywords), 3)
        self.assertEqual(comp.lines_of_code, 150)
        self.assertEqual(comp.cyclomatic_complexity, 8.5)

    def test_component_default_values(self):
        """Test Component default values"""
        comp = Component(
            component_id="test-123",
            name="TestComponent",
            component_type="api_client",
            repository="test/repo",
            files=["test.py"],
            language="python",
            first_seen=datetime.now()
        )

        self.assertIsNone(comp.api_signature)
        self.assertEqual(comp.imports, [])
        self.assertEqual(comp.keywords, [])
        self.assertEqual(comp.lines_of_code, 0)
        self.assertEqual(comp.sync_status, "unknown")


class TestComponentIntegration(unittest.TestCase):
    """Integration tests combining multiple components"""

    def test_scan_and_score_workflow(self):
        """Test complete workflow: scan components, then score canonical locations"""
        # Create temp repo with multiple components
        temp_dir = tempfile.TemporaryDirectory()
        repo_root = Path(temp_dir.name)

        # Create a client component
        client_code = '''
import requests

class APIClient:
    def request(self, url):
        return requests.get(url)
''' + '\n' * 20

        client_file = repo_root / "api_client.py"
        client_file.write_text(client_code)

        # Scan
        scanner = ComponentScanner(min_loc=15)
        components = scanner.scan_repository(str(repo_root), "test/repo")

        self.assertGreater(len(components), 0)
        comp = components[0]

        # Score canonical locations
        kb_data = {
            "test/repo": {"problem_domain": "app"},
            "central/lib": {"problem_domain": "infrastructure", "dependencies": {"consumers": ["test/repo"]}}
        }
        calculator = CentralityCalculator(kb_data)
        scores = calculator.calculate_canonical_score(comp, list(kb_data.keys()))

        self.assertEqual(len(scores), 2)
        self.assertIn("canonical_score", scores["test/repo"])
        self.assertIn("canonical_score", scores["central/lib"])

        temp_dir.cleanup()


if __name__ == '__main__':
    unittest.main()
