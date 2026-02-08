"""
Unit Tests for RefactorBot Slices
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


class TestSliceBase:
    """Tests for slice_base module."""
    
    def test_slice_config_creation(self):
        """Test SliceConfig creation."""
        from refactorbot.slices.slice_base import SliceConfig
        
        config = SliceConfig(slice_id="test_slice")
        assert config.slice_id == "test_slice"
    
    def test_slice_request_creation(self):
        """Test SliceRequest creation."""
        from refactorbot.slices.slice_base import SliceRequest
        
        request = SliceRequest(
            request_id="req-123",
            operation="test",
            payload={"key": "value"}
        )
        assert request.request_id == "req-123"
        assert request.operation == "test"
        assert request.payload["key"] == "value"
    
    def test_slice_response_creation(self):
        """Test SliceResponse creation."""
        from refactorbot.slices.slice_base import SliceResponse
        
        response = SliceResponse(
            request_id="req-123",
            success=True,
            payload={"result": "ok"}
        )
        assert response.request_id == "req-123"
        assert response.success is True
        assert response.payload["result"] == "ok"


class TestSliceAgent:
    """Tests for Agent Slice."""
    
    @pytest.fixture
    def slice_agent(self):
        """Create a test instance of SliceAgent."""
        from refactorbot.slices.slice_agent.slice import SliceAgent
        return SliceAgent()
    
    @pytest.mark.asyncio
    async def test_agent_slice_properties(self, slice_agent):
        """Test slice properties."""
        assert slice_agent.slice_id == "slice_agent"
        assert slice_agent.slice_name == "Agent Core Slice"
        assert slice_agent.slice_version == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_agent_execute_chat(self, slice_agent):
        """Test chat operation."""
        from refactorbot.slices.slice_base import SliceRequest
        
        request = SliceRequest(
            request_id="test-1",
            operation="chat",
            payload={"message": "Hello", "context": {}}
        )
        response = await slice_agent.execute(request)
        assert response.request_id == "test-1"
    
    @pytest.mark.asyncio
    async def test_agent_execute_analyze(self, slice_agent):
        """Test analyze operation."""
        from refactorbot.slices.slice_base import SliceRequest
        
        request = SliceRequest(
            request_id="test-2",
            operation="analyze",
            payload={"code": "def hello(): pass"}
        )
        response = await slice_agent.execute(request)
        assert response.request_id == "test-2"
    
    @pytest.mark.asyncio
    async def test_agent_health_check(self, slice_agent):
        """Test health check operation."""
        result = await slice_agent.health_check()
        assert result["status"] == "healthy"
        assert result["slice"] == "slice_agent"


class TestSliceTools:
    """Tests for Tools Slice."""
    
    @pytest.fixture
    def slice_tools(self):
        """Create a test instance of SliceTools."""
        from refactorbot.slices.slice_tools.slice import SliceTools
        return SliceTools()
    
    @pytest.mark.asyncio
    async def test_tools_slice_properties(self, slice_tools):
        """Test slice properties."""
        assert slice_tools.slice_id == "slice_tools"
        assert slice_tools.slice_name == "Tools Slice"
    
    @pytest.mark.asyncio
    async def test_tools_execute_list(self, slice_tools):
        """Test list operation."""
        from refactorbot.slices.slice_base import SliceRequest
        
        request = SliceRequest(
            request_id="test-1",
            operation="list",
            payload={}
        )
        response = await slice_tools.execute(request)
        assert response.request_id == "test-1"
    
    @pytest.mark.asyncio
    async def test_tools_execute_register(self, slice_tools):
        """Test register operation."""
        from refactorbot.slices.slice_base import SliceRequest
        
        request = SliceRequest(
            request_id="test-2",
            operation="register",
            payload={"name": "test_tool", "description": "A test tool"}
        )
        response = await slice_tools.execute(request)
        assert response.request_id == "test-2"


class TestSliceMemory:
    """Tests for Memory Slice."""
    
    @pytest.fixture
    def slice_memory(self):
        """Create a test instance of SliceMemory."""
        from refactorbot.slices.slice_memory.slice import SliceMemory
        return SliceMemory()
    
    @pytest.mark.asyncio
    async def test_memory_slice_properties(self, slice_memory):
        """Test slice properties."""
        assert slice_memory.slice_id == "slice_memory"
        assert slice_memory.slice_name == "Memory Slice"
    
    @pytest.mark.asyncio
    async def test_memory_store(self, slice_memory):
        """Test store operation."""
        from refactorbot.slices.slice_base import SliceRequest
        
        request = SliceRequest(
            request_id="test-1",
            operation="store",
            payload={"key": "test_key", "value": "test_value"}
        )
        response = await slice_memory.execute(request)
        assert response.request_id == "test-1"
    
    @pytest.mark.asyncio
    async def test_memory_retrieve(self, slice_memory):
        """Test retrieve operation."""
        from refactorbot.slices.slice_base import SliceRequest
        
        request = SliceRequest(
            request_id="test-2",
            operation="retrieve",
            payload={"key": "test_key"}
        )
        response = await slice_memory.execute(request)
        assert response.request_id == "test-2"


class TestSliceCommunication:
    """Tests for Communication Slice."""
    
    @pytest.fixture
    def slice_communication(self):
        """Create a test instance of SliceCommunication."""
        from refactorbot.slices.slice_communication.slice import SliceCommunication
        return SliceCommunication()
    
    @pytest.mark.asyncio
    async def test_communication_slice_properties(self, slice_communication):
        """Test slice properties."""
        assert slice_communication.slice_id == "slice_communication"
        assert slice_communication.slice_name == "Communication Slice"
    
    @pytest.mark.asyncio
    async def test_communication_create_channel(self, slice_communication):
        """Test create_channel operation."""
        from refactorbot.slices.slice_base import SliceRequest
        
        request = SliceRequest(
            request_id="test-1",
            operation="create_channel",
            payload={"name": "test_channel", "type": "text"}
        )
        response = await slice_communication.execute(request)
        assert response.request_id == "test-1"


class TestSliceSession:
    """Tests for Session Slice."""
    
    @pytest.fixture
    def slice_session(self):
        """Create a test instance of SliceSession."""
        from refactorbot.slices.slice_session.slice import SliceSession
        return SliceSession()
    
    @pytest.mark.asyncio
    async def test_session_slice_properties(self, slice_session):
        """Test slice properties."""
        assert slice_session.slice_id == "slice_session"
        assert slice_session.slice_name == "Session Slice"
    
    @pytest.mark.asyncio
    async def test_session_create(self, slice_session):
        """Test create operation."""
        from refactorbot.slices.slice_base import SliceRequest
        
        request = SliceRequest(
            request_id="test-1",
            operation="create",
            payload={"user_id": "user-123"}
        )
        response = await slice_session.execute(request)
        assert response.request_id == "test-1"


class TestSliceProviders:
    """Tests for Providers Slice."""
    
    @pytest.fixture
    def slice_providers(self):
        """Create a test instance of SliceProviders."""
        from refactorbot.slices.slice_providers.slice import SliceProviders
        return SliceProviders()
    
    @pytest.mark.asyncio
    async def test_providers_slice_properties(self, slice_providers):
        """Test slice properties."""
        assert slice_providers.slice_id == "slice_providers"
        assert slice_providers.slice_name == "Providers Slice"
    
    @pytest.mark.asyncio
    async def test_providers_register(self, slice_providers):
        """Test register operation."""
        from refactorbot.slices.slice_base import SliceRequest
        
        request = SliceRequest(
            request_id="test-1",
            operation="register",
            payload={"type": "openai", "name": "OpenAI Provider"}
        )
        response = await slice_providers.execute(request)
        assert response.request_id == "test-1"


class TestSliceSkills:
    """Tests for Skills Slice."""
    
    @pytest.fixture
    def slice_skills(self):
        """Create a test instance of SliceSkills."""
        from refactorbot.slices.slice_skills.slice import SliceSkills
        return SliceSkills()
    
    @pytest.mark.asyncio
    async def test_skills_slice_properties(self, slice_skills):
        """Test slice properties."""
        assert slice_skills.slice_id == "slice_skills"
        assert slice_skills.slice_name == "Skills Slice"
    
    @pytest.mark.asyncio
    async def test_skills_register(self, slice_skills):
        """Test register operation."""
        from refactorbot.slices.slice_base import SliceRequest
        
        request = SliceRequest(
            request_id="test-1",
            operation="register",
            payload={"name": "test_skill", "description": "A test skill"}
        )
        response = await slice_skills.execute(request)
        assert response.request_id == "test-1"


class TestSliceEventBus:
    """Tests for Event Bus Slice."""
    
    @pytest.fixture
    def slice_eventbus(self):
        """Create a test instance of SliceEventBus."""
        from refactorbot.slices.slice_eventbus.slice import SliceEventBus
        return SliceEventBus()
    
    @pytest.mark.asyncio
    async def test_eventbus_slice_properties(self, slice_eventbus):
        """Test slice properties."""
        assert slice_eventbus.slice_id == "slice_eventbus"
        assert slice_eventbus.slice_name == "Event Bus Slice"
    
    @pytest.mark.asyncio
    async def test_eventbus_publish(self, slice_eventbus):
        """Test publish operation."""
        from refactorbot.slices.slice_base import SliceRequest
        
        request = SliceRequest(
            request_id="test-1",
            operation="publish",
            payload={"topic": "test_topic", "event_type": "test_event"}
        )
        response = await slice_eventbus.execute(request)
        assert response.request_id == "test-1"


class TestSelfImprovementServices:
    """Tests for SelfImprovementServices."""
    
    @pytest.mark.asyncio
    async def test_self_improvement_analyze_and_improve(self):
        """Test analyze_and_improve method."""
        from refactorbot.slices.slice_base import SliceConfig, SelfImprovementServices
        from refactorbot.slices.slice_agent.slice import SliceAgent
        
        slice = SliceAgent()
        services = SelfImprovementServices(slice)
        
        feedback = {"issue": "slow_response", "severity": "high"}
        result = await services.analyze_and_improve(feedback)
        
        assert "improvements" in result
        assert "code_quality_score" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
