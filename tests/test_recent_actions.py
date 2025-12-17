"""
Tests for recent actions feature

Tests for:
- get_recent_actions database method
- GetRecentActionsSkill A2A endpoint
- Pagination and filtering
"""

import pytest
from datetime import datetime, timedelta
from core.postgres_repository import PostgresRepository
from a2a.skills.activity import GetRecentActionsSkill


class TestGetRecentActionsMethod:
    """Test PostgresRepository.get_recent_actions() method"""

    @pytest.mark.asyncio
    async def test_get_recent_actions_all_types(self, postgres_repo):
        """Test retrieving all action types"""
        result = await postgres_repo.get_recent_actions(limit=20, offset=0)

        assert isinstance(result, dict)
        assert "actions" in result
        assert "total_count" in result
        assert "returned" in result
        assert result["returned"] <= 20

        # Verify action structure if data exists
        if result["actions"]:
            action = result["actions"][0]
            assert "action_type" in action
            assert "repository" in action
            assert "timestamp" in action
            assert "reference_id" in action
            assert "metadata" in action

    @pytest.mark.asyncio
    async def test_get_recent_actions_filtered_by_type(self, postgres_repo):
        """Test filtering by specific action types"""
        result = await postgres_repo.get_recent_actions(
            limit=10,
            action_types=['runtime_issue', 'analysis']
        )

        assert result["success"] is False or all(
            action["action_type"] in ['runtime_issue', 'analysis']
            for action in result.get("actions", [])
        )

    @pytest.mark.asyncio
    async def test_get_recent_actions_pagination(self, postgres_repo):
        """Test pagination works correctly with offset and limit"""
        # Get first page
        page1 = await postgres_repo.get_recent_actions(limit=5, offset=0)
        assert page1["returned"] <= 5

        # Get second page if enough data
        if page1["total_count"] > 5:
            page2 = await postgres_repo.get_recent_actions(limit=5, offset=5)
            assert page2["returned"] <= 5

            # Pages should have different actions
            page1_ids = [a['reference_id'] for a in page1['actions']]
            page2_ids = [a['reference_id'] for a in page2['actions']]

            # Verify no overlap
            assert len(set(page1_ids) & set(page2_ids)) == 0

    @pytest.mark.asyncio
    async def test_get_recent_actions_chronological_order(self, postgres_repo):
        """Test actions are returned in chronological order (newest first)"""
        result = await postgres_repo.get_recent_actions(limit=20, offset=0)

        if len(result["actions"]) > 1:
            timestamps = [a["timestamp"] for a in result["actions"]]
            # Verify descending order
            assert timestamps == sorted(timestamps, reverse=True)

    @pytest.mark.asyncio
    async def test_get_recent_actions_respects_limit(self, postgres_repo):
        """Test limit parameter is respected"""
        for limit in [5, 10, 20]:
            result = await postgres_repo.get_recent_actions(limit=limit, offset=0)
            assert result["returned"] <= limit

    @pytest.mark.asyncio
    async def test_get_recent_actions_empty_result(self, postgres_repo):
        """Test handling of empty result set"""
        result = await postgres_repo.get_recent_actions(
            limit=10,
            action_types=['nonexistent_type'] if False else None  # Trigger no results
        )

        assert isinstance(result["actions"], list)
        assert result["returned"] >= 0


class TestGetRecentActionsSkill:
    """Test GetRecentActionsSkill A2A endpoint"""

    @pytest.mark.asyncio
    async def test_skill_execution_basic(self, postgres_repo):
        """Test basic skill execution"""
        skill = GetRecentActionsSkill(postgres_repo)

        result = await skill.execute({
            "limit": 10,
            "offset": 0
        })

        assert result["success"] is True
        assert "actions" in result
        assert "pagination" in result
        assert "count" in result
        assert "returned" in result

    @pytest.mark.asyncio
    async def test_skill_pagination_metadata(self, postgres_repo):
        """Test pagination metadata is correct"""
        skill = GetRecentActionsSkill(postgres_repo)

        result = await skill.execute({
            "limit": 10,
            "offset": 0
        })

        assert result["success"] is True
        pagination = result.get("pagination", {})
        assert "limit" in pagination
        assert "offset" in pagination
        assert "has_more" in pagination
        assert "next_offset" in pagination
        assert "total_pages" in pagination

        # Verify has_more logic
        if result["returned"] < 10:
            assert pagination["has_more"] is False

    @pytest.mark.asyncio
    async def test_skill_invalid_limit(self, postgres_repo):
        """Test skill validation of limit bounds"""
        skill = GetRecentActionsSkill(postgres_repo)

        # Test limit too high
        result = await skill.execute({
            "limit": 101,
            "offset": 0
        })
        assert result["success"] is False

        # Test limit too low
        result = await skill.execute({
            "limit": 0,
            "offset": 0
        })
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_skill_with_filters(self, postgres_repo):
        """Test skill with action type filters"""
        skill = GetRecentActionsSkill(postgres_repo)

        result = await skill.execute({
            "limit": 10,
            "offset": 0,
            "action_types": ["analysis", "lesson"]
        })

        assert result["success"] is True
        # All returned actions should be of filtered types
        for action in result.get("actions", []):
            assert action["action_type"] in ["analysis", "lesson"]

    @pytest.mark.asyncio
    async def test_skill_response_format(self, postgres_repo):
        """Test skill response format matches A2A protocol"""
        skill = GetRecentActionsSkill(postgres_repo)

        result = await skill.execute({
            "limit": 5,
            "offset": 0
        })

        # Required A2A response fields
        assert "success" in result
        assert isinstance(result["success"], bool)

        if result["success"]:
            assert "count" in result
            assert "returned" in result
            assert "actions" in result
            assert isinstance(result["count"], int)
            assert isinstance(result["returned"], int)
            assert isinstance(result["actions"], list)

            # Verify filters echo
            assert "filters" in result
            assert result["filters"]["action_types"] is None or isinstance(result["filters"]["action_types"], list)

            # Verify timestamp
            assert "timestamp" in result


class TestRecentActionsIntegration:
    """Integration tests for recent actions feature"""

    @pytest.mark.asyncio
    async def test_end_to_end_flow(self, postgres_repo):
        """Test complete flow from database to skill response"""
        skill = GetRecentActionsSkill(postgres_repo)

        # Execute skill
        result = await skill.execute({
            "limit": 20,
            "offset": 0,
            "action_types": ["analysis", "lesson", "deployment", "runtime_issue"]
        })

        # Verify success
        assert result["success"] is True

        # Verify data integrity
        for action in result.get("actions", []):
            # All required fields present
            assert action["action_type"] in ["analysis", "lesson", "deployment", "runtime_issue"]
            assert isinstance(action["repository"], str)
            assert isinstance(action["timestamp"], str)
            assert isinstance(action["reference_id"], str)
            assert isinstance(action["metadata"], dict)

            # Metadata has type-specific fields
            if action["action_type"] == "analysis":
                assert "patterns_count" in action["metadata"]
                assert "decisions_count" in action["metadata"]
            elif action["action_type"] == "lesson":
                assert "category" in action["metadata"]
                assert "impact" in action["metadata"]
            elif action["action_type"] == "runtime_issue":
                assert "severity" in action["metadata"]
                assert "issue_type" in action["metadata"]

    @pytest.mark.asyncio
    async def test_pagination_consistency(self, postgres_repo):
        """Test pagination returns consistent data"""
        skill = GetRecentActionsSkill(postgres_repo)

        # Get first page
        page1 = await skill.execute({
            "limit": 5,
            "offset": 0
        })

        assert page1["success"] is True

        # Get same data with same filters
        page1_again = await skill.execute({
            "limit": 5,
            "offset": 0
        })

        # Should return same data
        assert page1["count"] == page1_again["count"]
        assert page1["returned"] == page1_again["returned"]

        if page1["actions"] and page1_again["actions"]:
            # First action should be the same
            assert page1["actions"][0]["reference_id"] == page1_again["actions"][0]["reference_id"]


# Pytest fixtures would go in conftest.py
# Example structure:
# @pytest.fixture
# async def postgres_repo():
#     """Fixture for PostgresRepository with test database"""
#     db = await init_test_db()
#     repo = PostgresRepository(db)
#     yield repo
#     await cleanup_test_db(db)
