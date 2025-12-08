"""
Documentation Review Service

Analyzes documentation for quality, consistency, and adherence to standards.
Integrates with dev-nexus knowledge base to learn from similar projects.
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime


class DocumentationReviewer:
    """Service for reviewing documentation quality"""

    def __init__(self, anthropic_client, kb_manager):
        """
        Initialize documentation reviewer

        Args:
            anthropic_client: Anthropic API client
            kb_manager: Knowledge base manager
        """
        self.anthropic_client = anthropic_client
        self.kb_manager = kb_manager

        # Map standards to check methods
        self.standards = {
            "completeness": self._check_completeness,
            "clarity": self._check_clarity,
            "examples": self._check_examples,
            "structure": self._check_structure,
            "accuracy": self._check_accuracy,
            "formatting": self._check_formatting
        }

    def review_documentation(
        self,
        repository: str,
        doc_content: str,
        doc_path: str,
        standards: List[str]
    ) -> Dict[str, Any]:
        """
        Review documentation against specified standards

        Args:
            repository: Repository name
            doc_content: Documentation content
            doc_path: Path to documentation file
            standards: Standards to check

        Returns:
            Review results with scores and recommendations
        """
        results = {
            "repository": repository,
            "doc_path": doc_path,
            "reviewed_at": datetime.now().isoformat(),
            "standards_checked": standards,
            "checks": {},
            "overall_score": 0.0,
            "recommendations": []
        }

        # Run each standard check
        total_score = 0
        for standard in standards:
            if standard in self.standards:
                check_result = self.standards[standard](doc_content, doc_path)
                results["checks"][standard] = check_result
                total_score += check_result["score"]

        # Calculate overall score
        results["overall_score"] = total_score / len(standards) if standards else 0

        # Get recommendations from Claude
        recommendations = self._get_ai_recommendations(
            doc_content,
            doc_path,
            results["checks"]
        )
        results["recommendations"] = recommendations

        # Compare with similar projects
        similar_projects = self._find_similar_project_docs(repository)
        if similar_projects:
            results["similar_projects"] = similar_projects

        return results

    def _check_completeness(self, content: str, path: str) -> Dict[str, Any]:
        """Check if documentation is complete"""
        required_sections = {
            "README.md": ["overview", "installation", "usage", "examples"],
            "CLAUDE.md": ["overview", "commands", "examples"],
            "API.md": ["endpoints", "authentication", "examples"],
            "CONTRIBUTING.md": ["getting started", "guidelines", "pull request"]
        }

        filename = path.split("/")[-1]
        required = required_sections.get(filename, [])

        found_sections = []
        missing_sections = []

        for section in required:
            # Check for section headings (## Section or # Section)
            pattern = rf'#+\s+{section}'
            if re.search(pattern, content, re.IGNORECASE):
                found_sections.append(section)
            else:
                missing_sections.append(section)

        score = len(found_sections) / len(required) if required else 1.0

        return {
            "score": score,
            "found_sections": found_sections,
            "missing_sections": missing_sections,
            "message": f"Found {len(found_sections)}/{len(required)} required sections"
        }

    def _check_clarity(self, content: str, path: str) -> Dict[str, Any]:
        """Check documentation clarity"""
        issues = []

        # Check for overly long sentences
        sentences = re.split(r'[.!?]+', content)
        long_sentences = [s for s in sentences if len(s.split()) > 40]
        if len(long_sentences) > 5:
            issues.append(f"Found {len(long_sentences)} sentences over 40 words")

        # Check for paragraphs that are too long
        paragraphs = content.split('\n\n')
        long_paragraphs = [p for p in paragraphs if len(p.split()) > 200]
        if long_paragraphs:
            issues.append(f"Found {len(long_paragraphs)} paragraphs over 200 words")

        # Check for passive voice indicators
        passive_indicators = ['was', 'were', 'been', 'being']
        passive_count = sum(content.lower().count(word) for word in passive_indicators)
        word_count = len(content.split())
        if word_count > 0 and (passive_count / word_count) > 0.05:
            issues.append("High use of passive voice detected")

        # Check for jargon without explanation
        jargon_words = ["A2A", "AgentCard", "executor", "skill", "LLM", "API"]
        undefined_jargon = []
        for word in jargon_words:
            if word in content:
                # Check if word is defined (near colon or parenthesis)
                pattern = rf'{word}\s*[\(:]'
                if not re.search(pattern, content):
                    undefined_jargon.append(word)

        if len(undefined_jargon) > 2:
            issues.append(f"Jargon used without clear definition: {', '.join(undefined_jargon[:3])}")

        # Calculate score
        score = max(0, 1.0 - (len(issues) * 0.15))

        return {
            "score": score,
            "issues": issues,
            "message": f"Clarity score: {score:.2f}" + (f" - {len(issues)} issues found" if issues else "")
        }

    def _check_examples(self, content: str, path: str) -> Dict[str, Any]:
        """Check for code examples and practical demonstrations"""
        # Count code blocks
        code_blocks = re.findall(r'```[\s\S]*?```', content)

        # Check for example sections
        has_examples_section = bool(re.search(r'#+\s+examples?', content, re.IGNORECASE))

        # Check for inline code
        inline_code = re.findall(r'`[^`]+`', content)

        # Count different types of examples
        bash_examples = len([b for b in code_blocks if '```bash' in b or '```sh' in b])
        python_examples = len([b for b in code_blocks if '```python' in b or '```py' in b])
        json_examples = len([b for b in code_blocks if '```json' in b])

        score = 0.0

        # Score based on code block count
        if len(code_blocks) >= 5:
            score += 0.4
        elif len(code_blocks) >= 3:
            score += 0.3
        elif len(code_blocks) >= 1:
            score += 0.2

        # Score for having examples section
        if has_examples_section:
            score += 0.2

        # Score for variety of examples
        example_types = sum([bash_examples > 0, python_examples > 0, json_examples > 0])
        score += example_types * 0.15

        # Score for inline code usage
        if len(inline_code) > 10:
            score += 0.1

        score = min(1.0, score)

        return {
            "score": score,
            "code_blocks_count": len(code_blocks),
            "has_examples_section": has_examples_section,
            "example_types": {
                "bash": bash_examples,
                "python": python_examples,
                "json": json_examples,
                "inline": len(inline_code)
            },
            "message": f"Found {len(code_blocks)} code blocks with {example_types} different types"
        }

    def _check_structure(self, content: str, path: str) -> Dict[str, Any]:
        """Check document structure and organization"""
        # Extract all headings
        headings = re.findall(r'^(#+)\s+(.+)$', content, re.MULTILINE)

        issues = []
        warnings = []

        # Check heading hierarchy
        prev_level = 0
        for heading_marks, heading_text in headings:
            level = len(heading_marks)
            if level > prev_level + 1 and prev_level > 0:
                issues.append(f"Heading hierarchy skipped level: {heading_text}")
            prev_level = level

        # Check for table of contents (if long doc)
        lines = content.split('\n')
        if len(lines) > 200:
            has_toc = bool(re.search(r'table of contents|^#+\s+contents?$', content, re.IGNORECASE | re.MULTILINE))
            if not has_toc:
                warnings.append("Long document might benefit from a table of contents")

        # Check for consistent heading style
        title_case_headings = [h for _, h in headings if h[0].isupper()]
        if headings and len(title_case_headings) / len(headings) < 0.5:
            warnings.append("Inconsistent heading capitalization")

        # Check for empty sections
        sections = re.split(r'^#+\s+.+$', content, flags=re.MULTILINE)
        empty_sections = [s for s in sections if len(s.strip()) < 10]
        if empty_sections:
            issues.append(f"Found {len(empty_sections)} nearly empty sections")

        # Calculate score
        score = max(0, 1.0 - (len(issues) * 0.25) - (len(warnings) * 0.1))

        return {
            "score": score,
            "headings_count": len(headings),
            "issues": issues,
            "warnings": warnings,
            "message": f"Structure score: {score:.2f}"
        }

    def _check_accuracy(self, content: str, path: str) -> Dict[str, Any]:
        """Check for potential accuracy issues"""
        issues = []
        warnings = []

        # Check for outdated dates
        current_year = datetime.now().year
        old_years = [str(y) for y in range(current_year - 3, current_year - 1)]
        for year in old_years:
            if year in content:
                warnings.append(f"May contain outdated information from {year}")
                break

        # Check for broken internal links
        internal_links = re.findall(r'\[([^\]]+)\]\(#([^\)]+)\)', content)
        broken_links = []
        for link_text, anchor in internal_links:
            # Convert anchor to heading format (replace hyphens with spaces)
            expected_heading = anchor.replace('-', ' ')
            if not re.search(rf'#+\s+{re.escape(expected_heading)}', content, re.IGNORECASE):
                broken_links.append(f"#{anchor}")

        if broken_links:
            issues.append(f"Potentially broken links: {', '.join(broken_links[:3])}")

        # Check for TODO/FIXME markers
        todos = re.findall(r'TODO|FIXME|XXX', content, re.IGNORECASE)
        if todos:
            warnings.append(f"Found {len(todos)} TODO/FIXME markers")

        # Check for placeholder text
        placeholders = re.findall(r'your_\w+|<your[^>]+>|\[your[^\]]+\]', content, re.IGNORECASE)
        if placeholders:
            issues.append(f"Found {len(placeholders)} placeholder values")

        # Calculate score
        score = max(0, 1.0 - (len(issues) * 0.3) - (len(warnings) * 0.1))

        return {
            "score": score,
            "issues": issues,
            "warnings": warnings,
            "message": f"Accuracy score: {score:.2f}"
        }

    def _check_formatting(self, content: str, path: str) -> Dict[str, Any]:
        """Check markdown formatting quality"""
        issues = []
        warnings = []

        # Check for proper list formatting
        lists = re.findall(r'^(\s*)([-*+]|\d+\.)\s+', content, re.MULTILINE)
        if lists:
            # Check for consistent bullet style
            bullet_styles = set([m[1][0] for m in lists if m[1][0] in ['-', '*', '+']])
            if len(bullet_styles) > 1:
                warnings.append(f"Mixed bullet styles: {', '.join(bullet_styles)}")

        # Check for proper code block formatting
        unclosed_code_blocks = content.count('```') % 2
        if unclosed_code_blocks:
            issues.append("Unclosed code block detected")

        # Check for proper link formatting
        bad_links = re.findall(r'\]\s+\(', content)
        if bad_links:
            issues.append(f"Found {len(bad_links)} improperly formatted links (space before parenthesis)")

        # Check for proper line breaks
        triple_newlines = content.count('\n\n\n')
        if triple_newlines > 5:
            warnings.append("Excessive blank lines found")

        # Check for trailing whitespace
        trailing_spaces = len(re.findall(r' +$', content, re.MULTILINE))
        if trailing_spaces > 10:
            warnings.append(f"Many lines ({trailing_spaces}) have trailing whitespace")

        # Calculate score
        score = max(0, 1.0 - (len(issues) * 0.3) - (len(warnings) * 0.1))

        return {
            "score": score,
            "issues": issues,
            "warnings": warnings,
            "message": f"Formatting score: {score:.2f}"
        }

    def _get_ai_recommendations(
        self,
        content: str,
        path: str,
        checks: Dict[str, Any]
    ) -> List[str]:
        """Get AI-powered recommendations from Claude"""

        # Build prompt with check results
        check_summary = "\n".join([
            f"- {standard}: {result['message']}"
            for standard, result in checks.items()
        ])

        # Extract specific issues
        all_issues = []
        for standard, result in checks.items():
            if 'issues' in result:
                all_issues.extend([f"[{standard}] {issue}" for issue in result['issues'][:2]])

        issues_text = "\n".join(all_issues[:5]) if all_issues else "No specific issues found"

        prompt = f"""You are a technical documentation expert. Review this documentation and provide 3-5 specific, actionable recommendations for improvement.

Documentation file: {path}

Automated checks found:
{check_summary}

Specific issues detected:
{issues_text}

Content preview (first 1200 chars):
{content[:1200]}

Provide specific recommendations in this format:
1. [Category] Clear, actionable recommendation
2. [Category] Clear, actionable recommendation

Focus on: structure, clarity, completeness, and developer experience.
Make recommendations concrete and specific, not generic."""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract recommendations from response
            recommendations_text = response.content[0].text

            # Parse numbered or bulleted list
            recommendations = []
            for line in recommendations_text.split('\n'):
                line = line.strip()
                # Match "1. ", "- ", "* ", etc.
                if line and (re.match(r'^\d+\.', line) or re.match(r'^[-*]', line)):
                    # Remove leading number/bullet
                    cleaned = re.sub(r'^\d+\.\s*|^[-*]\s*', '', line)
                    if cleaned:
                        recommendations.append(cleaned)

            return recommendations[:5]

        except Exception as e:
            return [f"Error getting AI recommendations: {str(e)}"]

    def _find_similar_project_docs(self, repository: str) -> List[Dict[str, Any]]:
        """Find similar projects with good documentation"""
        try:
            # Load knowledge base
            kb = self.kb_manager.load_knowledge_base()

            # Get repository info
            if repository not in kb.repositories:
                return []

            repo_info = kb.repositories[repository]
            keywords = repo_info.latest_patterns.keywords

            # Find similar repositories
            similar_repos = []
            for repo_name, other_info in kb.repositories.items():
                if repo_name == repository:
                    continue

                # Check keyword overlap
                common_keywords = set(keywords) & set(other_info.latest_patterns.keywords)
                if len(common_keywords) >= 2:
                    similar_repos.append({
                        "repository": repo_name,
                        "common_keywords": list(common_keywords),
                        "problem_domain": other_info.latest_patterns.problem_domain
                    })

            # Sort by number of common keywords
            similar_repos.sort(key=lambda x: len(x['common_keywords']), reverse=True)

            return similar_repos[:3]  # Top 3 similar projects

        except Exception as e:
            print(f"Error finding similar projects: {e}")
            return []

    def compare_with_standards(
        self,
        content: str,
        doc_type: str = "README"
    ) -> Dict[str, Any]:
        """
        Compare documentation against industry standards

        Args:
            content: Documentation content
            doc_type: Type of documentation (README, API, CONTRIBUTING, etc.)

        Returns:
            Comparison results with best practices
        """
        standards = {
            "README": {
                "required": ["title", "description", "installation", "usage", "license"],
                "recommended": ["examples", "contributing", "support", "acknowledgments"],
                "best_practices": [
                    "Clear project title and badges",
                    "Quick start section near the top",
                    "Visual examples (screenshots, GIFs)",
                    "Links to additional documentation"
                ]
            },
            "CLAUDE": {
                "required": ["overview", "commands", "context"],
                "recommended": ["examples", "patterns", "constraints"],
                "best_practices": [
                    "Clear description of codebase",
                    "Development commands",
                    "Important patterns to follow",
                    "What to avoid"
                ]
            },
            "API": {
                "required": ["endpoints", "authentication", "examples"],
                "recommended": ["rate limits", "errors", "versioning"],
                "best_practices": [
                    "Complete endpoint documentation",
                    "Request/response examples",
                    "Error code explanations",
                    "Authentication examples"
                ]
            }
        }

        standard = standards.get(doc_type, standards["README"])

        # Check required sections
        found_required = []
        missing_required = []
        for section in standard["required"]:
            if re.search(rf'#+\s+{section}', content, re.IGNORECASE):
                found_required.append(section)
            else:
                missing_required.append(section)

        # Check recommended sections
        found_recommended = []
        missing_recommended = []
        for section in standard["recommended"]:
            if re.search(rf'#+\s+{section}', content, re.IGNORECASE):
                found_recommended.append(section)
            else:
                missing_recommended.append(section)

        # Calculate compliance score
        required_score = len(found_required) / len(standard["required"]) if standard["required"] else 1.0
        recommended_score = len(found_recommended) / len(standard["recommended"]) if standard["recommended"] else 1.0
        overall_score = (required_score * 0.7) + (recommended_score * 0.3)

        return {
            "doc_type": doc_type,
            "overall_score": round(overall_score, 2),
            "required": {
                "found": found_required,
                "missing": missing_required,
                "score": round(required_score, 2)
            },
            "recommended": {
                "found": found_recommended,
                "missing": missing_recommended,
                "score": round(recommended_score, 2)
            },
            "best_practices": standard["best_practices"]
        }
