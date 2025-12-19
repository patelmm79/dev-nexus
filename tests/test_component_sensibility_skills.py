"""
Integration tests for Component Sensibility A2A Skills

Tests the three skills: detect_misplaced_components, analyze_component_centrality, recommend_consolidation_plan
"""

import unittest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from a2a.skills.component_sensibility import (
    DetectMisplacedComponentsSkill,
    AnalyzeComponentCentralitySkill,
    RecommendConsolidationPlanSkill,
    ComponentSensibilitySkills
)
from core.component_analyzer import VectorCacheManager, CentralityCalculator
from core.knowledge_base import KnowledgeBaseManager
from schemas.knowledge_base_v2 import (
    Component, KnowledgeBaseV2, RepositoryMetadata, PatternEntry,
    DeploymentInfo, DependencyInfo, TestingInfo, SecurityInfo
)


class TestDetectMisplacedComponentsSkill(unittest.TestCase):
    """Tests for DetectMisplacedComponentsSkill"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_vector_manager = Mock(spec=VectorCacheManager)
        self.mock_kb_manager = Mock(spec=KnowledgeBaseManager)
        self.skill = DetectMisplacedComponentsSkill(
            self.mock_vector_manager,
            self.mock_kb_manager
        )

    def test_skill_properties(self):
        """Test skill metadata"""
        self.assertEqual(self.skill.skill_id, "detect_misplaced_components")
        self.assertEqual(self.skill.skill_name, "Detect Misplaced Components")
        self.assertIn("detect", self.skill.skill_description.lower())
        self.assertIn("component-sensibility", self.skill.tags)

    def test_skill_authentication(self):
        """Test skill doesn't require authentication"""
        self.assertFalse(self.skill.requires_authentication)

    def test_input_schema(self):
        """Test input schema is properly defined"""
        schema = self.skill.input_schema
        self.assertEqual(schema["type"], "object")
        self.assertIn("properties", schema)
        self.assertIn("repository", schema["properties"])
        self.assertIn("component_types", schema["properties"])
        self.assertIn("min_similarity_score", schema["properties"])

    def test_examples_provided(self):
        """Test that usage examples are provided"""
        examples = self.skill.examples
        self.assertGreater(len(examples), 0)
        for example in examples:
            self.assertIn("input", example)
            self.assertIn("description", example)

    def test_execute_missing_required_params(self):
        """Test execution with missing parameters"""
        async def run_test():
            result = await self.skill.execute({})
            self.assertFalse(result["success"])
            self.assertIn("error", result)

        asyncio.run(run_test())

    def test_execute_with_invalid_repository(self):
        """Test execution with non-existent repository"""
        # Mock KB that doesn't have the requested repository
        kb = Mock(spec=KnowledgeBaseV2)
        kb.repositories = {"existing/repo": Mock()}
        self.mock_kb_manager.load_current.return_value = kb

        async def run_test():
            result = await self.skill.execute({"repository": "nonexistent/repo"})
            self.assertFalse(result["success"])
            self.assertIn("not found", result["error"].lower())

        asyncio.run(run_test())


class TestAnalyzeComponentCentralitySkill(unittest.TestCase):
    """Tests for AnalyzeComponentCentralitySkill"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_kb_manager = Mock(spec=KnowledgeBaseManager)
        self.skill = AnalyzeComponentCentralitySkill(self.mock_kb_manager)

    def test_skill_properties(self):
        """Test skill metadata"""
        self.assertEqual(self.skill.skill_id, "analyze_component_centrality")
        self.assertEqual(self.skill.skill_name, "Analyze Component Centrality")
        self.assertIn("centrality", self.skill.skill_description.lower())

    def test_input_schema_required_fields(self):
        """Test input schema specifies required fields"""
        schema = self.skill.input_schema
        self.assertIn("required", schema)
        self.assertIn("component_name", schema["required"])
        self.assertIn("current_location", schema["required"])

    def test_execute_missing_required_params(self):
        """Test execution fails without required params"""
        async def run_test():
            result = await self.skill.execute({"component_name": "TestComp"})
            self.assertFalse(result["success"])
            self.assertIn("error", result)

        asyncio.run(run_test())

    def test_execute_invalid_repository(self):
        """Test execution with invalid current location"""
        kb = Mock(spec=KnowledgeBaseV2)
        kb.repositories = {}
        self.mock_kb_manager.load_current.return_value = kb

        async def run_test():
            result = await self.skill.execute({
                "component_name": "TestComp",
                "current_location": "nonexistent/repo"
            })
            self.assertFalse(result["success"])

        asyncio.run(run_test())


class TestRecommendConsolidationPlanSkill(unittest.TestCase):
    """Tests for RecommendConsolidationPlanSkill"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_kb_manager = Mock(spec=KnowledgeBaseManager)
        self.skill = RecommendConsolidationPlanSkill(self.mock_kb_manager)

    def test_skill_properties(self):
        """Test skill metadata"""
        self.assertEqual(self.skill.skill_id, "recommend_consolidation_plan")
        self.assertEqual(self.skill.skill_name, "Recommend Consolidation Plan")
        self.assertIn("consolidation", self.skill.skill_description.lower())

    def test_skill_tags(self):
        """Test skill has appropriate tags"""
        tags = self.skill.tags
        self.assertIn("consolidation", tags)
        self.assertIn("planning", tags)

    def test_generate_consolidation_plan_structure(self):
        """Test consolidation plan has required phases"""
        plan = self.skill._generate_consolidation_plan(
            "TestComponent",
            "from/repo",
            "to/repo",
            {},
            False,
            False
        )

        self.assertIn("phase_1", plan)
        self.assertIn("phase_2", plan)
        self.assertIn("phase_3", plan)
        self.assertIn("phase_4", plan)
        self.assertIn("total_estimated_effort", plan)

    def test_phase_structure(self):
        """Test each phase has required fields"""
        plan = self.skill._generate_consolidation_plan(
            "TestComponent",
            "from/repo",
            "to/repo",
            {},
            False,
            False
        )

        for phase_key in ["phase_1", "phase_2", "phase_3", "phase_4"]:
            phase = plan[phase_key]
            self.assertIn("name", phase)
            self.assertIn("description", phase)
            self.assertIn("tasks", phase)
            self.assertIn("estimated_hours", phase)

    def test_phase_tasks_are_actionable(self):
        """Test phases contain specific, actionable tasks"""
        plan = self.skill._generate_consolidation_plan(
            "TestComponent",
            "from/repo",
            "to/repo",
            {},
            False,
            False
        )

        phase_1 = plan["phase_1"]
        self.assertGreater(len(phase_1["tasks"]), 0)
        for task in phase_1["tasks"]:
            self.assertGreater(len(task), 0)  # Task is not empty

    def test_execute_missing_required_params(self):
        """Test execution fails without required params"""
        async def run_test():
            result = await self.skill.execute({"component_name": "TestComp"})
            self.assertFalse(result["success"])

        asyncio.run(run_test())


class TestComponentSensibilitySkillGroup(unittest.TestCase):
    """Tests for ComponentSensibilitySkills skill group"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_kb_manager = Mock(spec=KnowledgeBaseManager)
        self.mock_vector_manager = Mock(spec=VectorCacheManager)

    def test_skillgroup_initialization(self):
        """Test skill group initializes"""
        skill_group = ComponentSensibilitySkills(
            self.mock_kb_manager,
            self.mock_vector_manager
        )
        self.assertIsNotNone(skill_group)

    def test_get_skills_returns_three_skills(self):
        """Test skill group returns all three skills"""
        skill_group = ComponentSensibilitySkills(
            self.mock_kb_manager,
            self.mock_vector_manager
        )
        skills = skill_group.get_skills()

        self.assertEqual(len(skills), 3)
        skill_ids = [s.skill_id for s in skills]
        self.assertIn("detect_misplaced_components", skill_ids)
        self.assertIn("analyze_component_centrality", skill_ids)
        self.assertIn("recommend_consolidation_plan", skill_ids)

    def test_all_skills_have_metadata(self):
        """Test all skills have complete metadata"""
        skill_group = ComponentSensibilitySkills(
            self.mock_kb_manager,
            self.mock_vector_manager
        )
        skills = skill_group.get_skills()

        for skill in skills:
            self.assertIsNotNone(skill.skill_id)
            self.assertIsNotNone(skill.skill_name)
            self.assertIsNotNone(skill.skill_description)
            self.assertGreater(len(skill.tags), 0)
            self.assertIsNotNone(skill.input_schema)
            self.assertIsNotNone(skill.requires_authentication)


class TestConsolidationPlanContent(unittest.TestCase):
    """Tests for consolidation plan content quality"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_kb_manager = Mock(spec=KnowledgeBaseManager)
        self.skill = RecommendConsolidationPlanSkill(self.mock_kb_manager)

    def test_phase1_analyze_prepare(self):
        """Test Phase 1 covers analysis and preparation"""
        plan = self.skill._generate_consolidation_plan(
            "Component",
            "from",
            "to",
            {},
            False,
            False
        )

        phase1 = plan["phase_1"]
        self.assertEqual(phase1["name"], "Analyze & Prepare")
        tasks_str = " ".join(phase1["tasks"]).lower()
        self.assertIn("analyz", tasks_str)
        self.assertIn("compar", tasks_str)

    def test_phase2_merge_standardize(self):
        """Test Phase 2 covers merging and standardization"""
        plan = self.skill._generate_consolidation_plan(
            "Component",
            "from",
            "to",
            {},
            False,
            False
        )

        phase2 = plan["phase_2"]
        self.assertEqual(phase2["name"], "Merge & Standardize")
        tasks_str = " ".join(phase2["tasks"]).lower()
        self.assertIn("merg", tasks_str)
        self.assertIn("standard", tasks_str)

    def test_phase3_update_consumers(self):
        """Test Phase 3 covers updating consumers"""
        plan = self.skill._generate_consolidation_plan(
            "Component",
            "from",
            "to",
            {},
            False,
            False
        )

        phase3 = plan["phase_3"]
        self.assertEqual(phase3["name"], "Update Consumers")
        self.assertIn("affected_repositories", phase3)

    def test_phase4_monitor_verify(self):
        """Test Phase 4 covers monitoring and verification"""
        plan = self.skill._generate_consolidation_plan(
            "Component",
            "from",
            "to",
            {},
            False,
            False
        )

        phase4 = plan["phase_4"]
        self.assertEqual(phase4["name"], "Monitor & Verify")
        self.assertIn("success_criteria", phase4)
        self.assertGreater(len(phase4["success_criteria"]), 0)

    def test_effort_estimates_are_reasonable(self):
        """Test effort estimates are provided and reasonable"""
        plan = self.skill._generate_consolidation_plan(
            "Component",
            "from",
            "to",
            {},
            False,
            False
        )

        for phase_key in ["phase_1", "phase_2", "phase_3", "phase_4"]:
            hours_str = plan[phase_key]["estimated_hours"]
            self.assertIn("-", hours_str)  # Should be a range like "2-3"
            self.assertIn("hr", hours_str.lower())

        total_effort = plan["total_estimated_effort"]
        self.assertIn("hour", total_effort.lower())


class TestSkillErrorHandling(unittest.TestCase):
    """Tests for error handling in skills"""

    def test_detect_skill_handles_missing_kb(self):
        """Test detect skill handles missing KB gracefully"""
        mock_vector_manager = Mock(spec=VectorCacheManager)
        mock_kb_manager = Mock(spec=KnowledgeBaseManager)
        mock_kb_manager.load_current.return_value = None

        skill = DetectMisplacedComponentsSkill(mock_vector_manager, mock_kb_manager)

        async def run_test():
            result = await skill.execute({})
            self.assertFalse(result["success"])
            self.assertIn("error", result)

        asyncio.run(run_test())

    def test_analyze_skill_handles_missing_kb(self):
        """Test analyze skill handles missing KB gracefully"""
        mock_kb_manager = Mock(spec=KnowledgeBaseManager)
        mock_kb_manager.load_current.return_value = None

        skill = AnalyzeComponentCentralitySkill(mock_kb_manager)

        async def run_test():
            result = await skill.execute({
                "component_name": "Test",
                "current_location": "test/repo"
            })
            self.assertFalse(result["success"])

        asyncio.run(run_test())


if __name__ == '__main__':
    unittest.main()
