"""
Knowledge Base Schema V2

Enhanced schema with deployment, dependencies, testing, and security sections.
Uses Pydantic for data validation and serialization.
"""

from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class ReusableComponent(BaseModel):
    """Reusable code component that can be shared across projects"""
    name: str
    description: str
    files: List[str]
    language: str
    api_contract: Optional[str] = None
    usage_example: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class DeploymentScript(BaseModel):
    """Deployment automation script"""
    name: str
    description: str
    script_path: str
    platform: str  # "cloud_run", "kubernetes", "github_actions", "lambda", etc.
    triggers: List[str] = Field(default_factory=list)
    runtime: Optional[str] = None


class LessonLearned(BaseModel):
    """Recorded lesson from development experience"""
    timestamp: datetime
    category: str  # "performance", "security", "reliability", "cost", "observability"
    lesson: str
    context: str
    severity: str  # "info", "warning", "critical"
    recorded_by: Optional[str] = None
    related_files: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class DeploymentInfo(BaseModel):
    """Deployment and operational information"""
    scripts: List[DeploymentScript] = Field(default_factory=list)
    lessons_learned: List[LessonLearned] = Field(default_factory=list)
    reusable_components: List[ReusableComponent] = Field(default_factory=list)
    ci_cd_platform: Optional[str] = None
    infrastructure: Dict[str, str] = Field(default_factory=dict)
    deployment_frequency: Optional[str] = None  # "continuous", "daily", "weekly", etc.
    last_deployed: Optional[datetime] = None


class DependencyRelationship(BaseModel):
    """Dependency relationship between repositories"""
    target_repo: str
    relationship_type: str  # "consumer", "derivative", "shared_library", "upstream"
    dependency_strength: str  # "strong", "medium", "weak"
    sync_strategy: Optional[str] = None  # "auto", "manual", "monitored"
    notes: Optional[str] = None
    last_synced: Optional[datetime] = None


class DependencyInfo(BaseModel):
    """Dependency graph information"""
    consumers: List[DependencyRelationship] = Field(default_factory=list)
    derivatives: List[DependencyRelationship] = Field(default_factory=list)
    external_dependencies: List[str] = Field(default_factory=list)
    dependency_update_strategy: Optional[str] = None


class TestingInfo(BaseModel):
    """Testing metadata and quality metrics"""
    test_frameworks: List[str] = Field(default_factory=list)
    coverage_percentage: Optional[float] = None
    test_patterns: List[str] = Field(default_factory=list)
    ci_status: Optional[str] = None  # "passing", "failing", "unknown"
    test_count: Optional[int] = None
    last_test_run: Optional[datetime] = None


class SecurityInfo(BaseModel):
    """Security posture information"""
    vulnerability_scan_date: Optional[datetime] = None
    security_patterns: List[str] = Field(default_factory=list)
    authentication_methods: List[str] = Field(default_factory=list)
    compliance_standards: List[str] = Field(default_factory=list)
    known_vulnerabilities: List[str] = Field(default_factory=list)
    security_score: Optional[float] = None  # 0-100


class PatternEntry(BaseModel):
    """Core pattern information from code analysis"""
    patterns: List[str] = Field(default_factory=list)
    decisions: List[str] = Field(default_factory=list)
    reusable_components: List[ReusableComponent] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    problem_domain: str
    keywords: List[str] = Field(default_factory=list)
    analyzed_at: datetime
    commit_sha: str
    commit_message: Optional[str] = None
    author: Optional[str] = None


class RepositoryMetadata(BaseModel):
    """Complete repository metadata with all sections"""
    latest_patterns: PatternEntry
    deployment: DeploymentInfo = Field(default_factory=DeploymentInfo)
    dependencies: DependencyInfo = Field(default_factory=DependencyInfo)
    testing: TestingInfo = Field(default_factory=TestingInfo)
    security: SecurityInfo = Field(default_factory=SecurityInfo)
    history: List[PatternEntry] = Field(default_factory=list)
    repository_url: Optional[str] = None
    primary_language: Optional[str] = None
    created_at: Optional[datetime] = None
    last_updated: datetime


class KnowledgeBaseV2(BaseModel):
    """Complete knowledge base schema v2"""
    schema_version: str = "2.0"
    repositories: Dict[str, RepositoryMetadata] = Field(default_factory=dict)
    created_at: datetime
    last_updated: datetime
    metadata: Dict[str, str] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Helper functions for common operations

def create_empty_repository_metadata(commit_sha: str, problem_domain: str = "Unknown") -> RepositoryMetadata:
    """Create an empty repository metadata structure"""
    now = datetime.now()
    return RepositoryMetadata(
        latest_patterns=PatternEntry(
            patterns=[],
            decisions=[],
            reusable_components=[],
            dependencies=[],
            problem_domain=problem_domain,
            keywords=[],
            analyzed_at=now,
            commit_sha=commit_sha
        ),
        deployment=DeploymentInfo(),
        dependencies=DependencyInfo(),
        testing=TestingInfo(),
        security=SecurityInfo(),
        history=[],
        last_updated=now
    )


def create_lesson_learned(
    category: str,
    lesson: str,
    context: str,
    severity: str = "info",
    recorded_by: Optional[str] = None
) -> LessonLearned:
    """Create a new lesson learned entry"""
    return LessonLearned(
        timestamp=datetime.now(),
        category=category,
        lesson=lesson,
        context=context,
        severity=severity,
        recorded_by=recorded_by,
        related_files=[],
        tags=[]
    )


def create_dependency_relationship(
    target_repo: str,
    relationship_type: str,
    dependency_strength: str = "medium"
) -> DependencyRelationship:
    """Create a new dependency relationship"""
    return DependencyRelationship(
        target_repo=target_repo,
        relationship_type=relationship_type,
        dependency_strength=dependency_strength,
        sync_strategy=None,
        notes=None,
        last_synced=None
    )
