"""
Component Analysis Engine

Provides component detection, extraction, and similarity analysis for architectural sensibility.
Integrates with pattern-miner for TF-IDF vectorization and pgvector for similarity matching.
"""

import logging
import re
import ast
import os
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
import hashlib

from schemas.knowledge_base_v2 import (
    Component, ComponentLocation, ComponentProvenance, ComponentVector, ConsolidationRecommendation
)

logger = logging.getLogger(__name__)


class ComponentScanner:
    """Extracts and identifies components from repositories using AST parsing and pattern matching"""

    # File patterns for different component types
    COMPONENT_PATTERNS = {
        "api_client": [
            r".*_client\.py$",
            r".*_api\.py$",
            r".*client\.py$",
            r"api/.*\.py$",
        ],
        "infrastructure": [
            r"utils/.*\.py$",
            r"core/.*\.py$",
            r"lib/.*\.py$",
            r"common/.*\.py$",
        ],
        "business_logic": [
            r"models/.*\.py$",
            r"domain/.*\.py$",
            r"services/.*\.py$",
        ],
        "deployment_pattern": [
            r".*\.tf$",  # Terraform
            r"cloudbuild\.yaml$",
            r".*\.yml$",
            r"Dockerfile.*",
            r".*_test\.py$",
        ]
    }

    # Keywords that indicate component type
    TYPE_KEYWORDS = {
        "api_client": ["client", "request", "http", "api", "rest", "endpoint"],
        "infrastructure": ["retry", "logger", "connection", "pool", "cache", "config"],
        "business_logic": ["validate", "transform", "process", "compute", "calculate"],
        "deployment_pattern": ["deploy", "infrastructure", "terraform", "dockerfile", "build"]
    }

    def __init__(self, min_loc: int = 20):
        """
        Initialize scanner

        Args:
            min_loc: Minimum lines of code to consider a component
        """
        self.min_loc = min_loc

    def scan_repository(self, repo_path: str, repo_name: str) -> List[Component]:
        """
        Scan repository and extract components

        Args:
            repo_path: Local path to repository
            repo_name: Repository name (owner/repo)

        Returns:
            List of detected components
        """
        components = []

        try:
            repo_root = Path(repo_path)
            if not repo_root.exists():
                logger.warning(f"Repository path does not exist: {repo_path}")
                return components

            # Scan Python files
            py_files = list(repo_root.rglob("*.py"))
            for py_file in py_files:
                # Skip common non-component directories
                if any(part in py_file.parts for part in [".git", "venv", "__pycache__", ".pytest", "build", "dist"]):
                    continue

                try:
                    component = self._extract_component_from_file(py_file, repo_path, repo_name)
                    if component:
                        components.append(component)
                except Exception as e:
                    logger.debug(f"Could not extract component from {py_file}: {e}")

            # Scan deployment files (Terraform, Docker, etc.)
            deployment_components = self._extract_deployment_components(repo_root, repo_name)
            components.extend(deployment_components)

        except Exception as e:
            logger.error(f"Error scanning repository {repo_name}: {e}", exc_info=True)

        return components

    def _extract_component_from_file(self, file_path: Path, repo_path: str, repo_name: str) -> Optional[Component]:
        """
        Extract component from a Python file

        Args:
            file_path: Path to Python file
            repo_path: Repository root path
            repo_name: Repository name

        Returns:
            Component if found, None otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            lines = content.split('\n')
            loc = len(lines)

            if loc < self.min_loc:
                return None

            # Parse AST
            try:
                tree = ast.parse(content)
            except SyntaxError:
                logger.debug(f"Could not parse {file_path}, skipping AST analysis")
                return None

            # Extract component metadata
            rel_path = str(file_path.relative_to(repo_path))
            component_type = self._classify_component(rel_path, content)
            if not component_type:
                return None

            component_id = self._generate_component_id(repo_name, rel_path)
            public_methods = self._extract_public_methods(tree)
            imports = self._extract_imports(tree)
            keywords = self._extract_keywords(content, component_type)
            api_signature = self._generate_api_signature(tree)
            language = self._detect_language(file_path)

            return Component(
                component_id=component_id,
                name=file_path.stem,
                component_type=component_type,
                repository=repo_name,
                files=[rel_path],
                language=language,
                api_signature=api_signature,
                imports=imports,
                keywords=keywords,
                description=self._extract_docstring(tree),
                lines_of_code=loc,
                cyclomatic_complexity=self._calculate_complexity(tree),
                public_methods=public_methods,
                first_seen=datetime.now(),
                sync_status="original"
            )

        except Exception as e:
            logger.debug(f"Error extracting component from {file_path}: {e}")
            return None

    def _extract_deployment_components(self, repo_root: Path, repo_name: str) -> List[Component]:
        """Extract deployment-related components (Terraform, Docker, etc.)"""
        components = []

        # Terraform files
        for tf_file in repo_root.rglob("*.tf"):
            if ".git" in tf_file.parts or "build" in tf_file.parts:
                continue

            try:
                with open(tf_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                rel_path = str(tf_file.relative_to(repo_root))
                component_id = self._generate_component_id(repo_name, rel_path)

                component = Component(
                    component_id=component_id,
                    name=tf_file.stem,
                    component_type="deployment_pattern",
                    repository=repo_name,
                    files=[rel_path],
                    language="hcl",
                    keywords=["terraform", "infrastructure", "deployment"],
                    lines_of_code=len(content.split('\n')),
                    first_seen=datetime.now(),
                    sync_status="original"
                )
                components.append(component)
            except Exception as e:
                logger.debug(f"Error extracting Terraform component from {tf_file}: {e}")

        # Dockerfile
        for dockerfile in repo_root.rglob("Dockerfile*"):
            if ".git" in dockerfile.parts:
                continue

            try:
                with open(dockerfile, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                rel_path = str(dockerfile.relative_to(repo_root))
                component_id = self._generate_component_id(repo_name, rel_path)

                component = Component(
                    component_id=component_id,
                    name="dockerfile",
                    component_type="deployment_pattern",
                    repository=repo_name,
                    files=[rel_path],
                    language="dockerfile",
                    keywords=["docker", "containerization"],
                    lines_of_code=len(content.split('\n')),
                    first_seen=datetime.now(),
                    sync_status="original"
                )
                components.append(component)
            except Exception as e:
                logger.debug(f"Error extracting Dockerfile component: {e}")

        return components

    def _classify_component(self, file_path: str, content: str) -> Optional[str]:
        """Classify component type based on file path and content"""
        file_path_lower = file_path.lower()

        # Check file patterns
        for comp_type, patterns in self.COMPONENT_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, file_path_lower):
                    return comp_type

        # Check content keywords
        content_lower = content.lower()
        for comp_type, keywords in self.TYPE_KEYWORDS.items():
            keyword_matches = sum(1 for kw in keywords if kw in content_lower)
            if keyword_matches >= 2:  # At least 2 keywords match
                return comp_type

        return None

    def _extract_public_methods(self, tree: ast.AST) -> List[str]:
        """Extract public method names from AST"""
        methods = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not node.name.startswith('_'):  # Public methods
                    methods.append(node.name)
            elif isinstance(node, ast.ClassDef):
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and not item.name.startswith('_'):
                        methods.append(f"{node.name}.{item.name}")

        return methods[:20]  # Limit to first 20

    def _extract_imports(self, tree: ast.AST) -> List[str]:
        """Extract import statements"""
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        return list(set(imports))[:20]  # Unique imports, limit to 20

    def _extract_keywords(self, content: str, component_type: str) -> List[str]:
        """Extract keywords from code"""
        keywords = set(self.TYPE_KEYWORDS.get(component_type, []))

        # Extract common technical terms
        patterns = [
            r'\b[a-z_]+_client\b',
            r'\b[a-z_]+_service\b',
            r'\bclass\s+([A-Z][a-zA-Z]+)',
            r'\bdef\s+([a-z_]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            keywords.update(matches[:5])  # Add up to 5 matches per pattern

        return list(keywords)[:15]  # Limit to 15 keywords

    def _generate_api_signature(self, tree: ast.AST) -> str:
        """Generate API signature from public methods"""
        methods = self._extract_public_methods(tree)
        return ", ".join(methods[:10])  # Limit to 10 methods

    def _extract_docstring(self, tree: ast.AST) -> Optional[str]:
        """Extract module or class docstring"""
        return ast.get_docstring(tree)

    def _calculate_complexity(self, tree: ast.AST) -> float:
        """
        Estimate cyclomatic complexity
        Simple metric: number of if/for/while statements + 1
        """
        complexity = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1

        return float(complexity)

    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        ext = file_path.suffix.lower()
        language_map = {
            '.py': 'python',
            '.go': 'go',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.rb': 'ruby',
            '.tf': 'hcl',
            '.yml': 'yaml',
            '.yaml': 'yaml',
        }
        return language_map.get(ext, 'unknown')

    def _generate_component_id(self, repo_name: str, file_path: str) -> str:
        """Generate unique component ID"""
        content = f"{repo_name}:{file_path}".encode()
        return hashlib.sha256(content).hexdigest()[:16]


class VectorCacheManager:
    """Manages component vectors using pgvector for similarity search"""

    def __init__(self, postgres_url: str, pattern_miner_client: Optional[Any] = None):
        """
        Initialize vector cache manager

        Args:
            postgres_url: PostgreSQL connection string
            pattern_miner_client: Client for pattern-miner A2A agent
        """
        self.postgres_url = postgres_url
        self.pattern_miner_client = pattern_miner_client
        self.vector_cache: Dict[str, ComponentVector] = {}  # In-memory cache

        self._initialize_pgvector()

    def _initialize_pgvector(self):
        """Initialize pgvector extension and table"""
        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(self.postgres_url)
            with engine.connect() as conn:
                # Create pgvector extension
                try:
                    conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                    logger.info("pgvector extension initialized")
                except Exception as e:
                    logger.debug(f"pgvector extension might already exist: {e}")

                # Create component_vectors table
                create_table_sql = """
                    CREATE TABLE IF NOT EXISTS component_vectors (
                        vector_id VARCHAR(255) PRIMARY KEY,
                        component_id VARCHAR(255) UNIQUE,
                        repository VARCHAR(255),
                        component_name VARCHAR(255),
                        vector VECTOR(300),
                        embedding_dimension INT,
                        created_at TIMESTAMP DEFAULT NOW(),
                        last_updated TIMESTAMP DEFAULT NOW()
                    );
                """
                conn.execute(text(create_table_sql))
                conn.commit()
                logger.info("component_vectors table created/verified")

                # Create index for similarity search
                try:
                    conn.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_component_vector_cosine
                        ON component_vectors USING ivfflat (vector vector_cosine_ops)
                        WITH (lists = 100);
                    """))
                    conn.commit()
                except Exception as e:
                    logger.debug(f"Index creation skipped: {e}")

        except Exception as e:
            logger.error(f"Error initializing pgvector: {e}", exc_info=True)

    def get_or_create_vector(self, component: Component) -> Optional[ComponentVector]:
        """
        Get cached vector or request generation from pattern-miner

        Args:
            component: Component to get vector for

        Returns:
            ComponentVector or None if generation fails
        """
        # Check cache first
        if component.component_id in self.vector_cache:
            return self.vector_cache[component.component_id]

        # Check PostgreSQL
        vector_id = self._get_vector_from_db(component.component_id)
        if vector_id:
            return ComponentVector(
                vector_id=vector_id,
                component_id=component.component_id,
                vector_dimension=300,
                last_updated=datetime.now()
            )

        # Request from pattern-miner
        if self.pattern_miner_client:
            vector_result = self._request_vector_from_pattern_miner(component)
            if vector_result:
                return vector_result

        return None

    def _get_vector_from_db(self, component_id: str) -> Optional[str]:
        """Retrieve vector ID from PostgreSQL"""
        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(self.postgres_url)
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT vector_id FROM component_vectors WHERE component_id = :cid"),
                    {"cid": component_id}
                )
                row = result.fetchone()
                return row[0] if row else None
        except Exception as e:
            logger.debug(f"Error retrieving vector from DB: {e}")
            return None

    def _request_vector_from_pattern_miner(self, component: Component) -> Optional[ComponentVector]:
        """
        Request TF-IDF vector generation from pattern-miner

        Args:
            component: Component to generate vector for

        Returns:
            ComponentVector with generated vector or None
        """
        try:
            if not self.pattern_miner_client:
                logger.warning("pattern-miner client not configured")
                return None

            # Prepare component metadata for vectorization
            metadata = {
                "component_id": component.component_id,
                "name": component.name,
                "type": component.component_type,
                "api_signature": component.api_signature or "",
                "imports": component.imports,
                "keywords": component.keywords,
                "description": component.description or ""
            }

            # Request vector generation
            response = self.pattern_miner_client.execute_skill(
                skill_id="generate_component_vectors",
                input_data={"components": [metadata]}
            )

            if response.get("success") and response.get("vectors"):
                vector_data = response["vectors"][0]
                vector = vector_data.get("vector", [])
                vector_id = self._store_vector_in_db(component, vector)

                return ComponentVector(
                    vector_id=vector_id,
                    component_id=component.component_id,
                    vector_dimension=len(vector),
                    last_updated=datetime.now()
                )

        except Exception as e:
            logger.error(f"Error requesting vector from pattern-miner: {e}", exc_info=True)

        return None

    def _store_vector_in_db(self, component: Component, vector: List[float]) -> str:
        """Store vector in PostgreSQL"""
        try:
            from sqlalchemy import create_engine, text

            vector_id = component.component_id
            engine = create_engine(self.postgres_url)

            # Format vector for pgvector
            vector_str = "[" + ", ".join(str(v) for v in vector) + "]"

            with engine.connect() as conn:
                conn.execute(
                    text("""
                        INSERT INTO component_vectors
                        (vector_id, component_id, repository, component_name, vector, embedding_dimension)
                        VALUES (:vid, :cid, :repo, :name, :vec::vector, :dim)
                        ON CONFLICT (vector_id) DO UPDATE SET
                            vector = EXCLUDED.vector,
                            last_updated = NOW()
                    """),
                    {
                        "vid": vector_id,
                        "cid": component.component_id,
                        "repo": component.repository,
                        "name": component.name,
                        "vec": vector_str,
                        "dim": len(vector)
                    }
                )
                conn.commit()
                logger.debug(f"Stored vector for component {component.name}")

            return vector_id

        except Exception as e:
            logger.error(f"Error storing vector in DB: {e}", exc_info=True)
            return ""

    def find_similar(self, component: Component, top_k: int = 5, min_similarity: float = 0.5) -> List[Dict[str, Any]]:
        """
        Find similar components using pgvector cosine similarity

        Args:
            component: Component to find similar components for
            top_k: Number of results to return
            min_similarity: Minimum similarity score (0-1)

        Returns:
            List of similar components with scores
        """
        try:
            vector = self.get_or_create_vector(component)
            if not vector:
                logger.warning(f"Could not get vector for {component.name}")
                return []

            from sqlalchemy import create_engine, text

            engine = create_engine(self.postgres_url)
            with engine.connect() as conn:
                # Use pgvector cosine similarity
                query = text("""
                    SELECT component_id, component_name, repository,
                           1 - (vector <=> :vec::vector) as similarity
                    FROM component_vectors
                    WHERE component_id != :cid
                    AND (1 - (vector <=> :vec::vector)) >= :min_sim
                    ORDER BY similarity DESC
                    LIMIT :k
                """)

                # Convert vector to format for comparison
                vector_str = "[" + ", ".join(str(v) for v in [0.1] * 300) + "]"  # Placeholder

                results = conn.execute(
                    query,
                    {
                        "vec": vector_str,
                        "cid": component.component_id,
                        "min_sim": min_similarity,
                        "k": top_k
                    }
                )

                return [
                    {
                        "component_id": row[0],
                        "component_name": row[1],
                        "repository": row[2],
                        "similarity_score": float(row[3])
                    }
                    for row in results
                ]

        except Exception as e:
            logger.error(f"Error finding similar components: {e}", exc_info=True)
            return []

    def update_vectors(self, components: List[Component]) -> Dict[str, bool]:
        """
        Bulk update vectors for multiple components

        Args:
            components: List of components to generate vectors for

        Returns:
            Dict mapping component_id to success status
        """
        results = {}

        try:
            if not self.pattern_miner_client:
                logger.warning("pattern-miner client not configured, cannot update vectors")
                return {c.component_id: False for c in components}

            # Batch request to pattern-miner
            metadata_list = [
                {
                    "component_id": c.component_id,
                    "name": c.name,
                    "type": c.component_type,
                    "api_signature": c.api_signature or "",
                    "imports": c.imports,
                    "keywords": c.keywords,
                    "description": c.description or ""
                }
                for c in components
            ]

            response = self.pattern_miner_client.execute_skill(
                skill_id="generate_component_vectors",
                input_data={"components": metadata_list}
            )

            if response.get("success") and response.get("vectors"):
                for i, comp in enumerate(components):
                    if i < len(response["vectors"]):
                        vector_data = response["vectors"][i]
                        vector = vector_data.get("vector", [])
                        self._store_vector_in_db(comp, vector)
                        results[comp.component_id] = True
                    else:
                        results[comp.component_id] = False
            else:
                for comp in components:
                    results[comp.component_id] = False

        except Exception as e:
            logger.error(f"Error updating vectors: {e}", exc_info=True)
            for comp in components:
                results[comp.component_id] = False

        return results

    def cache_status(self) -> Dict[str, Any]:
        """Get cache status information"""
        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(self.postgres_url)
            with engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM component_vectors"))
                total_vectors = result.scalar()

                result = conn.execute(text("""
                    SELECT COUNT(DISTINCT repository) FROM component_vectors
                """))
                repos_with_vectors = result.scalar()

            return {
                "total_vectors_cached": total_vectors,
                "repositories_with_vectors": repos_with_vectors,
                "memory_cache_size": len(self.vector_cache),
                "status": "healthy"
            }

        except Exception as e:
            logger.error(f"Error getting cache status: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}


class CentralityCalculator:
    """Calculates canonical location scores using multi-factor heuristics"""

    def __init__(self, kb_data: Dict[str, Any]):
        """
        Initialize calculator

        Args:
            kb_data: Knowledge base data containing repository metadata
        """
        self.kb_data = kb_data

    def calculate_canonical_score(self, component: Component, candidate_repos: List[str]) -> Dict[str, Any]:
        """
        Calculate canonical location scores for component across candidate repositories

        Args:
            component: Component to score
            candidate_repos: List of candidate repository names

        Returns:
            Dict with scores and explanations
        """
        scores = {}

        for repo in candidate_repos:
            factors = {
                "repository_purpose": self._score_repository_purpose(repo),
                "usage_count": self._score_usage_count(component, repo),
                "dependency_centrality": self._score_dependency_centrality(repo),
                "maintenance_activity": self._score_maintenance_activity(repo),
                "component_complexity": self._score_component_complexity(component),
                "first_implementation": self._score_first_implementation(component)
            }

            # Calculate weighted score
            weights = {
                "repository_purpose": 0.30,
                "usage_count": 0.30,
                "dependency_centrality": 0.20,
                "maintenance_activity": 0.10,
                "component_complexity": 0.05,
                "first_implementation": 0.05
            }

            total_score = sum(factors[k] * weights[k] for k in factors)

            scores[repo] = {
                "canonical_score": total_score,
                "factors": factors,
                "weights": weights,
                "reasoning": self._generate_scoring_reasoning(repo, factors)
            }

        return scores

    def _score_repository_purpose(self, repo: str) -> float:
        """Score based on repository purpose (infrastructure vs. application)"""
        repo_data = self.kb_data.get(repo, {})
        if not repo_data:
            return 0.2

        # Infrastructure repos score higher
        is_infrastructure = (
            "infrastructure" in repo_data.get("problem_domain", "").lower()
            or "library" in repo_data.get("problem_domain", "").lower()
            or "utility" in repo_data.get("problem_domain", "").lower()
        )

        # Check consumer count (infrastructure repos have many consumers)
        consumer_count = len(repo_data.get("dependencies", {}).get("consumers", []))
        has_many_consumers = consumer_count > 2

        if is_infrastructure and has_many_consumers:
            return 0.90
        elif is_infrastructure:
            return 0.70
        elif has_many_consumers:
            return 0.50
        else:
            return 0.30

    def _score_usage_count(self, component: Component, repo: str) -> float:
        """Score based on how many repositories would use this component"""
        # Simplified: assume infrastructure repos score higher
        if "dev-nexus" in repo or "core" in repo or "common" in repo:
            return 0.85
        return 0.40

    def _score_dependency_centrality(self, repo: str) -> float:
        """Score based on repository's position in dependency graph"""
        # Simplified: central repos like dev-nexus score higher
        if "dev-nexus" in repo:
            return 0.88
        elif "pattern-miner" in repo or "core" in repo:
            return 0.70
        else:
            return 0.30

    def _score_maintenance_activity(self, repo: str) -> float:
        """Score based on maintenance activity"""
        repo_data = self.kb_data.get(repo, {})
        if not repo_data:
            return 0.5

        # Simplified: assume core/infrastructure repos are well-maintained
        if "dev-nexus" in repo:
            return 0.80
        return 0.50

    def _score_component_complexity(self, component: Component) -> float:
        """Score based on component complexity (higher complexity = better for central repos)"""
        complexity = component.cyclomatic_complexity or 1.0
        loc = component.lines_of_code

        # Normalize
        loc_score = min(1.0, loc / 500.0)
        complexity_score = min(1.0, complexity / 50.0)

        return (loc_score * 0.6 + complexity_score * 0.4)

    def _score_first_implementation(self, component: Component) -> float:
        """Score based on when component was first implemented (tie-breaker)"""
        # Simplified: return 0.5 as neutral tie-breaker
        return 0.5

    def _generate_scoring_reasoning(self, repo: str, factors: Dict[str, float]) -> str:
        """Generate human-readable explanation of scoring"""
        top_factors = sorted(factors.items(), key=lambda x: x[1], reverse=True)[:3]
        factor_strings = [f"{k.replace('_', ' ')}: {v:.2f}" for k, v in top_factors]

        return f"Repository {repo} scores well on: {', '.join(factor_strings)}"
