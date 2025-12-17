import json
import os
import shutil
import tempfile
import unittest

from agents.architectural_agent.agent import ArchitecturalAgent


class TestArchitecturalAgent(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix='arch-agent-test-')
        # Create fake repo structure with a few files
        os.makedirs(os.path.join(self.tmp, 'deploy', 'k8s'), exist_ok=True)
        os.makedirs(os.path.join(self.tmp, 'terraform'), exist_ok=True)
        with open(os.path.join(self.tmp, 'Dockerfile'), 'w') as f:
            f.write('FROM python:3.11')
        with open(os.path.join(self.tmp, 'deploy', 'k8s', 'deployment.yaml'), 'w') as f:
            f.write('apiVersion: v1\nkind: Pod')
        with open(os.path.join(self.tmp, 'terraform', 'main.tf'), 'w') as f:
            f.write('resource "null_resource" "r" {}')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_analyze_local_repo_detects_artifacts(self):
        agent = ArchitecturalAgent()
        report = agent.analyze_repo(self.tmp, clone_if_url=False)
        self.assertIn('recommendations', report)
        types = [r['type'] for r in report['recommendations']]
        self.assertIn('terraform', types)
        self.assertIn('kubernetes', types)
        self.assertIn('docker', types)


if __name__ == '__main__':
    unittest.main()
