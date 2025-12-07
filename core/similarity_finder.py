"""
Similarity Finder Module

Finds similar patterns across repositories using keyword and pattern overlap.
Shared by both GitHub Actions CLI and A2A server.
"""

from typing import List, Dict, Set
from schemas.knowledge_base_v2 import KnowledgeBaseV2, PatternEntry


class SimilarityFinder:
    """Find similar patterns across repositories"""

    def __init__(self, min_similarity_score: float = 0.0):
        """
        Initialize similarity finder

        Args:
            min_similarity_score: Minimum similarity score to consider (0-1)
        """
        self.min_similarity_score = min_similarity_score

    def find_similar_patterns(
        self,
        current_patterns: PatternEntry,
        kb: KnowledgeBaseV2,
        current_repo: str = None,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find repositories with similar patterns

        Args:
            current_patterns: PatternEntry to compare
            kb: KnowledgeBaseV2 with all repository data
            current_repo: Current repository name to exclude from results
            top_k: Number of top results to return

        Returns:
            List of dictionaries with similarity information, sorted by relevance
        """
        similarities = []

        current_keywords = set(current_patterns.keywords)
        current_patterns_list = current_patterns.patterns

        for repo_name, repo_data in kb.repositories.items():
            # Skip self-comparison
            if current_repo and repo_name == current_repo:
                continue

            repo_patterns = repo_data.latest_patterns
            repo_keywords = set(repo_patterns.keywords)
            repo_patterns_list = repo_patterns.patterns

            # Calculate overlaps
            keyword_overlap = len(current_keywords & repo_keywords)
            pattern_overlap = len(set(current_patterns_list) & set(repo_patterns_list))

            # Calculate dependency overlap
            current_deps = set(current_patterns.dependencies)
            repo_deps = set(repo_patterns.dependencies)
            dependency_overlap = len(current_deps & repo_deps)

            # Combined similarity score
            total_overlap = keyword_overlap + pattern_overlap + dependency_overlap

            # Only include if there's overlap
            if total_overlap > 0:
                similarities.append({
                    'repository': repo_name,
                    'keyword_overlap': keyword_overlap,
                    'pattern_overlap': pattern_overlap,
                    'dependency_overlap': dependency_overlap,
                    'total_score': total_overlap,
                    'matching_patterns': list(set(current_patterns_list) & set(repo_patterns_list)),
                    'matching_keywords': list(current_keywords & repo_keywords),
                    'matching_dependencies': list(current_deps & repo_deps),
                    'repo_patterns': repo_patterns.model_dump(mode='json'),
                    'deployment_info': repo_data.deployment.model_dump(mode='json') if repo_data.deployment else None
                })

        # Sort by total similarity score (descending)
        similarities.sort(key=lambda x: x['total_score'], reverse=True)

        return similarities[:top_k]

    def find_by_keywords(
        self,
        keywords: List[str],
        kb: KnowledgeBaseV2,
        min_matches: int = 1,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Find repositories matching specific keywords

        Args:
            keywords: List of keywords to search for
            kb: KnowledgeBaseV2 with all repository data
            min_matches: Minimum number of keyword matches required
            top_k: Number of top results to return

        Returns:
            List of repositories matching the keywords
        """
        search_keywords = set(k.lower() for k in keywords)
        matches = []

        for repo_name, repo_data in kb.repositories.items():
            repo_keywords = set(k.lower() for k in repo_data.latest_patterns.keywords)
            keyword_matches = search_keywords & repo_keywords

            if len(keyword_matches) >= min_matches:
                matches.append({
                    'repository': repo_name,
                    'match_count': len(keyword_matches),
                    'matched_keywords': list(keyword_matches),
                    'all_keywords': list(repo_keywords),
                    'patterns': repo_data.latest_patterns.patterns,
                    'problem_domain': repo_data.latest_patterns.problem_domain,
                    'deployment_info': repo_data.deployment.model_dump(mode='json') if repo_data.deployment else None
                })

        # Sort by match count (descending)
        matches.sort(key=lambda x: x['match_count'], reverse=True)

        return matches[:top_k]

    def find_by_patterns(
        self,
        patterns: List[str],
        kb: KnowledgeBaseV2,
        min_matches: int = 1,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Find repositories using specific architectural patterns

        Args:
            patterns: List of pattern names to search for
            kb: KnowledgeBaseV2 with all repository data
            min_matches: Minimum number of pattern matches required
            top_k: Number of top results to return

        Returns:
            List of repositories using the patterns
        """
        search_patterns = set(p.lower() for p in patterns)
        matches = []

        for repo_name, repo_data in kb.repositories.items():
            repo_patterns = set(p.lower() for p in repo_data.latest_patterns.patterns)
            pattern_matches = search_patterns & repo_patterns

            if len(pattern_matches) >= min_matches:
                matches.append({
                    'repository': repo_name,
                    'match_count': len(pattern_matches),
                    'matched_patterns': list(pattern_matches),
                    'all_patterns': repo_data.latest_patterns.patterns,
                    'problem_domain': repo_data.latest_patterns.problem_domain,
                    'reusable_components': [
                        comp.model_dump(mode='json')
                        for comp in repo_data.latest_patterns.reusable_components
                    ]
                })

        # Sort by match count (descending)
        matches.sort(key=lambda x: x['match_count'], reverse=True)

        return matches[:top_k]

    def calculate_similarity_score(
        self,
        patterns1: PatternEntry,
        patterns2: PatternEntry
    ) -> float:
        """
        Calculate normalized similarity score between two pattern entries

        Args:
            patterns1: First PatternEntry
            patterns2: Second PatternEntry

        Returns:
            Similarity score between 0 and 1
        """
        # Keyword similarity (Jaccard)
        keywords1 = set(patterns1.keywords)
        keywords2 = set(patterns2.keywords)
        keyword_similarity = self._jaccard_similarity(keywords1, keywords2)

        # Pattern similarity (Jaccard)
        patterns_set1 = set(patterns1.patterns)
        patterns_set2 = set(patterns2.patterns)
        pattern_similarity = self._jaccard_similarity(patterns_set1, patterns_set2)

        # Dependency similarity (Jaccard)
        deps1 = set(patterns1.dependencies)
        deps2 = set(patterns2.dependencies)
        dependency_similarity = self._jaccard_similarity(deps1, deps2)

        # Weighted average
        weights = {'keywords': 0.4, 'patterns': 0.4, 'dependencies': 0.2}
        total_score = (
            weights['keywords'] * keyword_similarity +
            weights['patterns'] * pattern_similarity +
            weights['dependencies'] * dependency_similarity
        )

        return total_score

    def _jaccard_similarity(self, set1: Set, set2: Set) -> float:
        """
        Calculate Jaccard similarity coefficient

        Args:
            set1: First set
            set2: Second set

        Returns:
            Jaccard similarity (0-1)
        """
        if not set1 and not set2:
            return 0.0

        intersection = len(set1 & set2)
        union = len(set1 | set2)

        return intersection / union if union > 0 else 0.0

    def get_repositories_by_domain(
        self,
        kb: KnowledgeBaseV2,
        domain_keyword: str
    ) -> List[Dict]:
        """
        Get all repositories in a specific problem domain

        Args:
            kb: KnowledgeBaseV2 with all repository data
            domain_keyword: Keyword to search in problem_domain

        Returns:
            List of repositories in the domain
        """
        domain_keyword_lower = domain_keyword.lower()
        matches = []

        for repo_name, repo_data in kb.repositories.items():
            if domain_keyword_lower in repo_data.latest_patterns.problem_domain.lower():
                matches.append({
                    'repository': repo_name,
                    'problem_domain': repo_data.latest_patterns.problem_domain,
                    'patterns': repo_data.latest_patterns.patterns,
                    'keywords': repo_data.latest_patterns.keywords
                })

        return matches
