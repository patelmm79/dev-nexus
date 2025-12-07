"""
Pattern Extractor Module

Extracts architectural patterns from code changes using Claude AI.
Shared by both GitHub Actions CLI and A2A server.
"""

import json
import re
from typing import Dict, List
from datetime import datetime
import anthropic
from schemas.knowledge_base_v2 import PatternEntry, ReusableComponent


class PatternExtractor:
    """Extract semantic patterns from code changes using Claude AI"""

    def __init__(self, anthropic_client: anthropic.Anthropic):
        """
        Initialize pattern extractor

        Args:
            anthropic_client: Initialized Anthropic client
        """
        self.client = anthropic_client

    def is_meaningful_file(self, filepath: str) -> bool:
        """
        Filter out noise files that don't contain architectural patterns

        Args:
            filepath: Path to the file

        Returns:
            True if file should be analyzed, False otherwise
        """
        ignore_patterns = [
            r'\.lock$',
            r'package-lock\.json$',
            r'yarn\.lock$',
            r'\.min\.js$',
            r'\.map$',
            r'__pycache__',
            r'\.pyc$',
            r'\.git/',
            r'node_modules/',
            r'\.DS_Store'
        ]
        return not any(re.search(pattern, filepath) for pattern in ignore_patterns)

    def extract_patterns_with_llm(
        self,
        changes: Dict,
        repository_name: str
    ) -> PatternEntry:
        """
        Use Claude to extract semantic patterns from code changes

        Args:
            changes: Dictionary containing commit changes with structure:
                {
                    'commit_sha': str,
                    'commit_message': str,
                    'author': str,
                    'timestamp': str,
                    'files_changed': [
                        {
                            'path': str,
                            'change_type': str,
                            'diff': str
                        }
                    ]
                }
            repository_name: Name of the repository being analyzed

        Returns:
            PatternEntry with extracted patterns, decisions, components, etc.
        """

        # Prepare concise summary of changes for LLM
        files_summary = []
        for file in changes.get('files_changed', [])[:10]:  # Limit to avoid token overflow
            files_summary.append({
                'path': file['path'],
                'change_type': file['change_type'],
                'diff': file['diff'][:2000]  # Truncate large diffs
            })

        prompt = f"""Analyze this code commit and extract architectural patterns and decisions.

Repository: {repository_name}
Commit: {changes.get('commit_message', 'Unknown')}

Files changed:
{json.dumps(files_summary, indent=2)}

Please identify:
1. **Core Patterns**: What architectural patterns are being used or introduced? (e.g., "error handling with custom exceptions", "API client with retry logic", "authentication middleware")

2. **Technical Decisions**: What technical choices were made? (e.g., "using requests library for HTTP", "storing config in environment variables")

3. **Reusable Components**: What parts of this code might be useful across multiple projects? Be specific about the abstraction.

4. **Dependencies**: What external libraries or services does this rely on?

5. **Problem Domain**: What business/technical problem does this solve in one sentence?

Respond ONLY with valid JSON in this exact format:
{{
  "patterns": ["pattern1", "pattern2"],
  "decisions": ["decision1", "decision2"],
  "reusable_components": [
    {{"name": "component_name", "description": "what it does", "files": ["file1.py"], "language": "python"}}
  ],
  "dependencies": ["dep1", "dep2"],
  "problem_domain": "brief description",
  "keywords": ["keyword1", "keyword2"]
}}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract JSON from response
            content = response.content[0].text
            # Remove markdown code blocks if present
            content = re.sub(r'```json\n?|\n?```', '', content).strip()

            pattern_data = json.loads(content)

            # Convert reusable_components to Pydantic models
            reusable_components = []
            for comp_data in pattern_data.get('reusable_components', []):
                reusable_components.append(ReusableComponent(
                    name=comp_data.get('name', 'Unknown'),
                    description=comp_data.get('description', ''),
                    files=comp_data.get('files', []),
                    language=comp_data.get('language', 'unknown'),
                    api_contract=comp_data.get('api_contract'),
                    usage_example=comp_data.get('usage_example'),
                    tags=comp_data.get('tags', [])
                ))

            # Create PatternEntry
            return PatternEntry(
                patterns=pattern_data.get('patterns', []),
                decisions=pattern_data.get('decisions', []),
                reusable_components=reusable_components,
                dependencies=pattern_data.get('dependencies', []),
                problem_domain=pattern_data.get('problem_domain', 'Unknown'),
                keywords=pattern_data.get('keywords', []),
                analyzed_at=datetime.now(),
                commit_sha=changes.get('commit_sha', 'unknown'),
                commit_message=changes.get('commit_message'),
                author=changes.get('author')
            )

        except Exception as e:
            print(f"Error in LLM analysis: {e}")
            # Return empty pattern entry with error information
            return PatternEntry(
                patterns=[],
                decisions=[],
                reusable_components=[],
                dependencies=[],
                problem_domain=f"Error during analysis: {str(e)}",
                keywords=[],
                analyzed_at=datetime.now(),
                commit_sha=changes.get('commit_sha', 'unknown'),
                commit_message=changes.get('commit_message'),
                author=changes.get('author')
            )

    def extract_patterns_from_text(
        self,
        code_snippet: str,
        context: str = ""
    ) -> Dict:
        """
        Extract patterns from arbitrary code snippet (for A2A use cases)

        Args:
            code_snippet: Code to analyze
            context: Additional context about the code

        Returns:
            Dictionary with extracted patterns
        """
        prompt = f"""Analyze this code snippet and extract architectural patterns.

Context: {context}

Code:
{code_snippet[:5000]}  # Limit to 5000 characters

Identify patterns, technical decisions, and reusable abstractions.

Respond ONLY with valid JSON in this format:
{{
  "patterns": ["pattern1", "pattern2"],
  "decisions": ["decision1", "decision2"],
  "keywords": ["keyword1", "keyword2"]
}}"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text
            content = re.sub(r'```json\n?|\n?```', '', content).strip()

            return json.loads(content)

        except Exception as e:
            print(f"Error in pattern extraction: {e}")
            return {
                "patterns": [],
                "decisions": [],
                "keywords": []
            }
