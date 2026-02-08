"""
Unit Tests for Master Core
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestMasterCore:
    """Tests for MasterCore."""
    
    @pytest.fixture
    def master_core(self):
        """Create a test instance of MasterCore."""
        from refactorbot.master_core.master_core import MasterCore
        return MasterCore()
    
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
        from refactorbot.slices.slice_base import SliceRequest
        
        request = SliceRequest(
            request_id="test-1",
            operation="list_slices",
            payload={}
        )
        response = await master_core.execute(request)
        assert response.request_id == "test-1"
        assert "slices" in @pytest.mark.as response.payload
    
   yncio
    async def test_master_core_dispatch(self, master_core):
        """Test dispatch operation."""
        from refactorbot.slices.slice_base import SliceRequest
        
        request = SliceRequest(
            request_id="test-2",
            operation="dispatch",
            payload={"target_slice": "slice_agent", "operation": "chat"}
        )
        response = await master_core.execute(request)
        assert response.request_id == "test-2"


class TestSliceOrchestration:
    """Tests for slice orchestration."""
    
    @pytest.mark.asyncio
    async def test_orchestrate_slices(self):
        """Test orchestrating multiple slices."""
        from refactorbot.master_core.master_core import MasterCore
        
        master = MasterCore()
        results = await master.orchestrate_slices(
            ["slice_agent", "slice_memory"],
            {"operation": "health_check"}
        )
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_coordinate_slices(self):
        """Test coordinating slices."""
        from refactorbot.master_core.master_core import MasterCore
        
        master = MasterCore()
        result = await master.coordinate_slices(
            "slice_agent",
            "slice_memory",
            "test_coordination"
        )
        assert "source" in result
        assert "target" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
