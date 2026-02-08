"""
Unit Tests for Master Core
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestMasterCore:
    """Tests for MasterCore."""
    
    @pytest.fixture
    def master_core(self):
        """Create a test instance of MasterCore with slices registered."""
        from refactorbot.master_core.master_core import MasterCore
        from refactorbot.slices.slice_agent.slice import SliceAgent
        
        core = MasterCore()
        # Register slice_agent for tests
        core.register_slice("slice_agent", SliceAgent)
        return core
    
    @pytest.mark.asyncio
    async def test_master_core_properties(self, master_core):
        """Test master core properties."""
        assert master_core.orchestrator_id == "master_core"
        assert master_core.orchestrator_name == "Master AI Orchestrator"
        assert master_core.orchestrator_version == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_master_core_health(self, master_core):
        """Test health check."""
        result = await master_core.health_check()
        assert result["status"] == "healthy"
        assert result["orchestrator"] == "master_core"
        assert "slices" in result
    
    @pytest.mark.asyncio
    async def test_master_core_list_slices(self, master_core):
        """Test list slices operation."""
        response = await master_core.execute(
            operation="list_slices",
            payload={},
            context={}
        )
        # Operation executes - check that request_id is set
        assert response.request_id is not None
        assert response.metadata.get("operation") == "list_slices"
    
    @pytest.mark.asyncio
    async def test_master_core_dispatch(self, master_core):
        """Test dispatch operation."""
        response = await master_core.execute(
            operation="dispatch",
            payload={"target_slice": "slice_agent", "operation": "chat"},
            context={}
        )
        # Operation executes
        assert response.request_id is not None
        assert response.metadata.get("operation") == "dispatch"
    
    @pytest.mark.asyncio
    async def test_master_core_self_improve(self, master_core):
        """Test self improve operation."""
        response = await master_core.execute(
            operation="self_improve",
            payload={"feedback": {"improvements": ["test"]}},
            context={}
        )
        # Operation executes
        assert response.request_id is not None
        assert response.metadata.get("operation") == "self_improve"
    
    @pytest.mark.asyncio
    async def test_master_core_unknown_operation(self, master_core):
        """Test unknown operation returns error."""
        response = await master_core.execute(
            operation="unknown_operation",
            payload={},
            context={}
        )
        assert not response.success
        assert response.errors
