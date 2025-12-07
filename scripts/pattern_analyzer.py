#!/usr/bin/env python3
"""
Pattern Discovery Agent - Main Analysis Script
Extracts patterns from commits and checks for cross-repo similarities

REFACTORED: Now uses core modules for business logic.
Shared logic with A2A server in core/ directory.
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import anthropic
import requests
from github import Github
import git

# Add parent directory to path to import core modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.pattern_extractor import PatternExtractor
from core.knowledge_base import KnowledgeBaseManager
from core.similarity_finder import SimilarityFinder
from core.integration_service import IntegrationService

class PatternAnalyzer:
    def __init__(self):
        # Initialize API clients
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.environ['ANTHROPIC_API_KEY']
        )
        self.github_token = os.environ['GITHUB_TOKEN']
        self.github_client = Github(self.github_token)
        self.webhook_url = os.environ.get('WEBHOOK_URL')
        self.kb_repo_name = os.environ.get('KNOWLEDGE_BASE_REPO')
        self.orchestrator_url = os.environ.get('ORCHESTRATOR_URL')
        self.repo = git.Repo('.')

        # Get current repository info
        self.current_repo = os.environ.get('GITHUB_REPOSITORY')
        self.current_sha = os.environ.get('GITHUB_SHA', self.repo.head.commit.hexsha)
        self.current_branch = os.environ.get('GITHUB_REF_NAME', 'main')

        # Initialize core modules (shared with A2A server)
        self.pattern_extractor = PatternExtractor(self.anthropic_client)
        self.kb_manager = KnowledgeBaseManager(self.github_client, self.kb_repo_name)
        self.similarity_finder = SimilarityFinder()
        self.integration_service = IntegrationService()

    def get_recent_changes(self) -> Dict:
        """Extract recent commit changes"""
        try:
            # Get the diff for the latest commit
            commit = self.repo.commit(self.current_sha)
            parent = commit.parents[0] if commit.parents else None

            if parent:
                diff = parent.diff(commit, create_patch=True)
            else:
                # First commit - get all files
                diff = commit.diff(git.NULL_TREE, create_patch=True)

            changes = {
                'commit_sha': self.current_sha,
                'commit_message': commit.message,
                'author': str(commit.author),
                'timestamp': commit.committed_datetime.isoformat(),
                'files_changed': []
            }

            for item in diff:
                file_info = {
                    'path': item.a_path or item.b_path,
                    'change_type': item.change_type,
                    'diff': item.diff.decode('utf-8', errors='ignore') if item.diff else ''
                }

                # Only include meaningful files
                if self.pattern_extractor.is_meaningful_file(file_info['path']):
                    changes['files_changed'].append(file_info)

            return changes
        except Exception as e:
            print(f"Error getting changes: {e}")
            return {'error': str(e)}


    def notify(self, message: str, similarities: List[Dict]):
        """Send notification via webhook"""
        if not self.webhook_url:
            print("No webhook URL configured")
            print(message)
            return

        # Format message for Discord/Slack
        notification = {
            "content": message,
            "embeds": []
        }

        # Add similarity embeds
        for sim in similarities[:3]:  # Top 3
            embed = {
                "title": f"Similar to: {sim['repository']}",
                "description": f"**Overlap**: {sim['keyword_overlap']} keywords, {sim['pattern_overlap']} patterns",
                "fields": []
            }

            if sim['matching_patterns']:
                embed['fields'].append({
                    "name": "Matching Patterns",
                    "value": "\n".join(f"• {p}" for p in sim['matching_patterns'][:5]),
                    "inline": False
                })

            notification['embeds'].append(embed)

        try:
            response = requests.post(self.webhook_url, json=notification)
            response.raise_for_status()
            print("Notification sent successfully")
        except Exception as e:
            print(f"Error sending notification: {e}")

    def notify_orchestrator(self, changes: Dict, patterns: Dict):
        """Notify orchestrator service of changes for dependency triage"""
        if not self.orchestrator_url:
            print("No orchestrator URL configured, skipping dependency notification")
            return

        try:
            # Prepare change event payload
            event_payload = {
                "source_repo": self.current_repo,
                "commit_sha": self.current_sha,
                "commit_message": changes.get('commit_message', ''),
                "branch": self.current_branch,
                "changed_files": changes.get('files_changed', []),
                "pattern_summary": patterns,
                "timestamp": datetime.now().isoformat()
            }

            # Send to orchestrator
            orchestrator_endpoint = f"{self.orchestrator_url}/api/webhook/change-notification"
            response = requests.post(orchestrator_endpoint, json=event_payload, timeout=10)
            response.raise_for_status()

            result = response.json()
            print(f"✓ Orchestrator notified successfully")
            print(f"  Consumers scheduled: {result.get('consumers_scheduled', [])}")
            print(f"  Derivatives scheduled: {result.get('derivatives_scheduled', [])}")

        except requests.exceptions.Timeout:
            print("⚠ Orchestrator notification timed out (continuing anyway)")
        except Exception as e:
            print(f"⚠ Error notifying orchestrator: {e}")
            print("  (Continuing with normal flow)")

    def run(self):
        """Main execution flow"""
        print(f"Analyzing patterns for {self.current_repo}...")

        # Step 1: Get changes
        changes = self.get_recent_changes()
        if 'error' in changes:
            print(f"Could not analyze changes: {changes['error']}")
            return

        if not changes['files_changed']:
            print("No meaningful file changes detected")
            return

        print(f"Found {len(changes['files_changed'])} changed files")

        # Step 2: Extract patterns with LLM (using core module)
        print("Extracting patterns with Claude...")
        patterns = self.pattern_extractor.extract_patterns_with_llm(changes, self.current_repo)

        # Save locally (convert Pydantic model to dict)
        with open('pattern_analysis.json', 'w') as f:
            json.dump({
                'changes': changes,
                'patterns': patterns.model_dump(mode='json')
            }, f, indent=2)

        # Step 3: Update knowledge base (using core module)
        print("Updating knowledge base...")
        self.kb_manager.update_knowledge_base(self.current_repo, patterns)

        # Step 4: Find similarities (using core module)
        print("Checking for similar patterns in other repos...")
        kb = self.kb_manager.load_knowledge_base()
        similarities = self.similarity_finder.find_similar_patterns(
            patterns,
            kb,
            current_repo=self.current_repo
        )

        # Step 5: Coordinate with external A2A agents
        print("Coordinating with external agents (orchestrator, pattern-miner)...")
        coordination_result = self.integration_service.coordinate_pattern_update(
            self.current_repo,
            patterns,
            self.current_sha
        )

        # Log coordination results
        if "error" not in coordination_result:
            print(f"✓ External agents notified successfully")
            if coordination_result.get("impact_analysis", {}).get("affected_repos"):
                affected = coordination_result["impact_analysis"]["affected_repos"]
                print(f"  Impact: {len(affected)} dependent repositories may be affected")
        else:
            print(f"⚠ External agent coordination: {coordination_result.get('error', 'Unknown error')}")

        # Step 6: Notify about pattern similarities
        if similarities:
            message = f"🔍 **Pattern Analysis: {self.current_repo}**\n\n"
            message += f"Found {len(similarities)} similar repositories!\n\n"
            message += f"**This commit introduces:**\n"
            for pattern in patterns.patterns[:3]:
                message += f"• {pattern}\n"

            self.notify(message, similarities)
        else:
            print("No similar patterns found in other repositories")

        print("\n✅ Analysis complete!")
        print(f"Patterns extracted: {len(patterns.patterns)}")
        print(f"Similar repos found: {len(similarities)}")


if __name__ == '__main__':
    analyzer = PatternAnalyzer()
    analyzer.run()