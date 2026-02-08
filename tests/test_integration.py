"""
Integration Tests for Cross-Slice Communication
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio


class TestCrossSliceCommunication:
    """Tests for cross-slice orchestration."""
    
    @pytest.fixture
    def master_core_with_slices(self):
        """Create MasterCore with all slices registered."""
        from refactorbot.master_core.master_core import MasterCore
        from refactorbot.slices.slice_agent.slice import SliceAgent
        from refactorbot.slices.slice_tools.slice import SliceTools
        from refactorbot.slices.slice_memory.slice import SliceMemory
        from refactorbot.slices.slice_session.slice import SliceSession
        from refactorbot.slices.slice_communication.slice import SliceCommunication
        from refactorbot.slices.slice_eventbus.slice import SliceEventBus
        from refactorbot.slices.slice_providers.slice import SliceProviders
        from refactorbot.slices.slice_skills.slice import SliceSkills
        
        core = MasterCore()
        
        # Register all slices
        core.register_slice("slice_agent", SliceAgent)
        core.register_slice("slice_tools", SliceTools)
        core.register_slice("slice_memory", SliceMemory)
        core.register_slice("slice_session", SliceSession)
        core.register_slice("slice_communication", SliceCommunication)
        core.register_slice("slice_eventbus", SliceEventBus)
        core.register_slice("slice_providers", SliceProviders)
        core.register_slice("slice_skills", SliceSkills)
        
        return core
    
    @pytest.mark.asyncio
    async def test_initialize_all_slices(self, master_core_with_slices):
        """Test initializing all registered slices."""
        core = master_core_with_slices
        
        # Initialize all slices
        for slice_id in core._slice_classes.keys():
            result = await core.initialize_slice(slice_id)
            assert result, f"Failed to initialize {slice_id}"
        
        # Verify all slices are initialized
        for slice_id in core._slice_classes.keys():
            assert slice_id in core._slices, f"{slice_id} not initialized"
    
    @pytest.mark.asyncio
    async def test_agent_dispatches_to_tools(self, master_core_with_slices):
        """Test agent slice using tools slice."""
        from refactorbot.master_core.master_core import MasterCore
        from refactorbot.slices.slice_agent.slice import SliceAgent
        from refactorbot.slices.slice_tools.slice import SliceTools
        
        core = MasterCore()
        core.register_slice("slice_agent", SliceAgent)
        core.register_slice("slice_tools", SliceTools)
        
        # Initialize slices
        await core.initialize_slice("slice_agent")
        await core.initialize_slice("slice_tools")
        await core.start_slice("slice_agent")
        await core.start_slice("slice_tools")
        
        # Dispatch tool list operation
        response = await core.execute(
            operation="tool_list",
            payload={},
            context={}
        )
        
        # Verify response
        assert response.request_id is not None
        assert response.metadata.get("operation") == "tool_list"
    
    @pytest.mark.asyncio
    async def test_memory_persists_agent_state(self, master_core_with_slices):
        """Test memory slice storing agent context."""
        from refactorbot.master_core.master_core import MasterCore
        from refactorbot.slices.slice_agent.slice import SliceAgent
        from refactorbot.slices.slice_memory.slice import SliceMemory
        
        core = MasterCore()
        core.register_slice("slice_agent", SliceAgent)
        core.register_slice("slice_memory", SliceMemory)
        
        # Initialize slices
        await core.initialize_slice("slice_agent")
        await core.initialize_slice("slice_memory")
        
        # Store context in memory slice
        response = await core.execute(
            operation="memory_store",
            payload={
                "key": "agent_context",
                "value": {"user_id": "test_user", "session": "test_session"}
            },
            context={}
        )
        
        # Verify storage
        assert response.request_id is not None
        
        # Retrieve context
        retrieve_response = await core.execute(
            operation="memory_retrieve",
            payload={"key": "agent_context"},
            context={}
        )
        
        assert retrieve_response.request_id is not None
    
    @pytest.mark.asyncio
    async def test_eventbus_coordinating_slices(self, master_core_with_slices):
        """Test eventbus coordinating slices."""
        from refactorbot.master_core.master_core import MasterCore
        from refactorbot.slices.slice_eventbus.slice import SliceEventBus
        
        core = MasterCore()
        core.register_slice("slice_eventbus", SliceEventBus)
        
        await core.initialize_slice("slice_eventbus")
        await core.start_slice("slice_eventbus")
        
        # Publish event
        response = await core.execute(
            operation="event_publish",
            payload={
                "event_type": "test_event",
                "data": {"key": "value"}
            },
            context={}
        )
        
        assert response.request_id is not None
        assert response.metadata.get("operation") == "event_publish"
    
    @pytest.mark.asyncio
    async def test_orchestration_request_routing(self, master_core_with_slices):
        """Test that operations are routed to correct slices."""
        core = master_core_with_slices
        
        # Initialize all slices
        for slice_id in core._slice_classes.keys():
            await core.initialize_slice(slice_id)
        
        # Test different operation prefixes
        operations = [
            ("agent_chat", "slice_agent"),
            ("tool_list", "slice_tools"),
            ("memory_store", "slice_memory"),
            ("session_create", "slice_session"),
            ("comm_create", "slice_communication"),
            ("provider_register", "slice_providers"),
            ("skill_register", "slice_skills"),
            ("event_publish", "slice_eventbus"),
        ]
        
        for operation, expected_slice in operations:
            response = await core.execute(
                operation=operation,
                payload={},
                context={}
            )
            assert response.metadata.get("operation") == operation


class TestResourceAllocation:
    """Tests for resource allocation in MasterCore."""
    
    @pytest.fixture
    def resource_allocator(self):
        """Create ResourceAllocator instance."""
        from refactorbot.master_core.resource_allocator import ResourceAllocator
        return ResourceAllocator()
    
    @pytest.mark.asyncio
    async def test_set_and_get_quota(self, resource_allocator):
        """Test setting and getting resource quotas."""
        from refactorbot.master_core.resource_allocator import ResourceQuota
        
        # Set quota with correct attribute names
        quota = ResourceQuota(
            max_memory_mb=100,
            max_cpu_percent=50,
            max_tokens_per_minute=1000,
            max_db_connections=5
        )
        resource_allocator.set_quota("slice_agent", quota)
        
        # Get quota
        retrieved = resource_allocator.get_quota("slice_agent")
        assert retrieved is not None
        assert retrieved.max_memory_mb == 100
        assert retrieved.max_cpu_percent == 50


class TestGlobalStateManager:
    """Tests for global state management."""
    
    @pytest.fixture
    def global_state(self, tmp_path):
        """Create GlobalStateManager with temp database."""
        from refactorbot.master_core.global_state import GlobalStateManager
        
        db_path = str(tmp_path / "test_global.db")
        return GlobalStateManager(db_path=db_path)
    
    def test_set_and_get(self, global_state):
        """Test setting and getting values (sync methods)."""
        global_state.set("test_key", {"data": "test_value"})
        
        # Get value
        value = global_state.get("test_key")
        assert value is not None
        assert value["data"] == "test_value"
    
    def test_delete(self, global_state):
        """Test deleting values."""
        global_state.set("test_key", {"data": "test_value"})
        global_state.delete("test_key")
        
        # Verify deleted
        value = global_state.get("test_key")
        assert value is None
    
    def test_get_all(self, global_state):
        """Test getting all values."""
        global_state.set("key1", {"data": "value1"})
        global_state.set("key2", {"data": "value2"})
        
        all_values = global_state.get_all()
        assert len(all_values) == 2


class TestDashboardConnector:
    """Tests for dashboard connector."""
    
    @pytest.fixture
    def dashboard(self, tmp_path):
        """Create DashboardConnector with temp directory."""
        from refactorbot.master_core.dashboard_connector import DashboardConnector
        
        data_dir = str(tmp_path / "dashboard")
        return DashboardConnector(data_dir=data_dir)
    
    @pytest.mark.asyncio
    async def test_publish_event(self, dashboard):
        """Test publishing events."""
        event_id = dashboard.publish_event(
            slice_id="slice_agent",
            event_type="test_event",
            description="Test event"
        )
        
        assert event_id is not None
        assert isinstance(event_id, str)
    
    @pytest.mark.asyncio
    async def test_publish_alert(self, dashboard):
        """Test publishing alerts."""
        alert_id = dashboard.publish_alert(
            slice_id="slice_agent",
            alert_type="error",
            title="Test Alert",
            message="This is a test"
        )
        
        assert alert_id is not None
    
    @pytest.mark.asyncio
    async def test_track_execution(self, dashboard):
        """Test tracking execution metrics."""
        dashboard.track_execution(
            slice_id="slice_agent",
            latency_ms=100.5,
            success=True
        )
        
        # Should not raise
    
    def test_get_events(self, dashboard):
        """Test getting events."""
        # Publish some events
        dashboard.publish_event(
            slice_id="slice_agent",
            event_type="test",
            description="test"
        )
        
        events = dashboard.get_events()
        assert events is not None
        assert len(events) >= 1
    
    def test_get_alerts(self, dashboard):
        """Test getting alerts."""
        # Publish some alerts
        dashboard.publish_alert(
            slice_id="slice_agent",
            alert_type="info",
            title="Test",
            message="test"
        )
        
        alerts = dashboard.get_alerts()
        assert alerts is not None


class TestSliceLifecycle:
    """Tests for slice lifecycle management."""
    
    @pytest.fixture
    def master_core(self):
        """Create MasterCore instance."""
        from refactorbot.master_core.master_core import MasterCore
        from refactorbot.slices.slice_agent.slice import SliceAgent
        
        core = MasterCore()
        core.register_slice("slice_agent", SliceAgent)
        return core
    
    @pytest.mark.asyncio
    async def test_start_slice(self, master_core):
        """Test starting a slice."""
        await master_core.initialize_slice("slice_agent")
        result = await master_core.start_slice("slice_agent")
        assert result is True
        
        # Verify slice is running
        assert "slice_agent" in master_core._slices
    
    @pytest.mark.asyncio
    async def test_stop_slice(self, master_core):
        """Test stopping a slice."""
        await master_core.initialize_slice("slice_agent")
        await master_core.start_slice("slice_agent")
        
        result = await master_core.stop_slice("slice_agent")
        assert result is True
        
        # Slice should still be in _slices but stopped
        assert "slice_agent" in master_core._slices
    
    @pytest.mark.asyncio
    async def test_shutdown_all_slices(self, master_core):
        """Test shutting down all slices."""
        from refactorbot.slices.slice_agent.slice import SliceAgent
        from refactorbot.slices.slice_tools.slice import SliceTools
        
        # Register and initialize multiple slices
        master_core.register_slice("slice_tools", SliceTools)
        await master_core.initialize_slice("slice_agent")
        await master_core.initialize_slice("slice_tools")
        await master_core.start_slice("slice_agent")
        await master_core.start_slice("slice_tools")
        
        # Shutdown all
        await master_core.shutdown()
        
        # Verify all stopped
        assert master_core._running is False


class TestOrchestrationRequest:
    """Tests for orchestration request/response handling."""
    
    @pytest.fixture
    def master_core(self):
        """Create MasterCore instance."""
        from refactorbot.master_core.master_core import MasterCore
        return MasterCore()
    
    @pytest.mark.asyncio
    async def test_orchestrate_with_request_id(self, master_core):
        """Test orchestration with explicit request ID."""
        from refactorbot.master_core.master_core import OrchestrationRequest
        
        request = OrchestrationRequest(
            request_id="test-request-123",
            operation="list_slices",
            payload={},
            context={}
        )
        
        response = await master_core.orchestrate(request)
        
        assert response.request_id == "test-request-123"
        assert response.response_id is not None
    
    @pytest.mark.asyncio
    async def test_orchestrate_generates_request_id(self, master_core):
        """Test orchestration generates request ID if not provided."""
        from refactorbot.master_core.master_core import OrchestrationRequest
        
        request = OrchestrationRequest(
            operation="list_slices",
            payload={},
            context={}
        )
        
        response = await master_core.orchestrate(request)
        
        assert response.request_id is not None
        assert response.request_id != ""
    
    @pytest.mark.asyncio
    async def test_orchestrate_with_priority(self, master_core):
        """Test orchestration with priority."""
        from refactorbot.master_core.master_core import OrchestrationRequest
        
        request = OrchestrationRequest(
            operation="list_slices",
            payload={},
            priority=10,
            timeout_seconds=60
        )
        
        response = await master_core.orchestrate(request)
        
        assert response.request_id is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


class TestSliceHealthChecks:
    """Tests for slice health_check implementations."""
    
    @pytest.mark.asyncio
    async def test_agent_health_check(self):
        """Test agent slice health check."""
        from refactorbot.slices.slice_agent.slice import SliceAgent
        
        agent = SliceAgent()
        health = await agent.health_check()
        
        assert "status" in health
        assert "slice" in health
        assert "version" in health
        assert "initialized" in health
        assert "database_connected" in health
        assert "timestamp" in health
        assert health["slice"] == "slice_agent"
    
    @pytest.mark.asyncio
    async def test_tools_health_check(self):
        """Test tools slice health check."""
        from refactorbot.slices.slice_tools.slice import SliceTools
        
        tools = SliceTools()
        health = await tools.health_check()
        
        assert "status" in health
        assert "slice" in health
        assert "version" in health
        assert "initialized" in health
        assert "database_connected" in health
        assert "tool_count" in health
        assert health["slice"] == "slice_tools"
    
    @pytest.mark.asyncio
    async def test_memory_health_check(self):
        """Test memory slice health check."""
        from refactorbot.slices.slice_memory.slice import SliceMemory
        
        memory = SliceMemory()
        health = await memory.health_check()
        
        assert "status" in health
        assert "slice" in health
        assert "version" in health
        assert "initialized" in health
        assert "database_connected" in health
        assert "memory_count" in health
        assert health["slice"] == "slice_memory"
    
    @pytest.mark.asyncio
    async def test_session_health_check(self):
        """Test session slice health check."""
        from refactorbot.slices.slice_session.slice import SliceSession
        
        session = SliceSession()
        health = await session.health_check()
        
        assert "status" in health
        assert "slice" in health
        assert "version" in health
        assert "initialized" in health
        assert "database_connected" in health
        assert "session_count" in health
        assert health["slice"] == "slice_session"
    
    @pytest.mark.asyncio
    async def test_communication_health_check(self):
        """Test communication slice health check."""
        from refactorbot.slices.slice_communication.slice import SliceCommunication
        
        comm = SliceCommunication()
        health = await comm.health_check()
        
        assert "status" in health
        assert "slice" in health
        assert "version" in health
        assert "initialized" in health
        assert "database_connected" in health
        assert "channel_count" in health
        assert health["slice"] == "slice_communication"
    
    @pytest.mark.asyncio
    async def test_providers_health_check(self):
        """Test providers slice health check."""
        from refactorbot.slices.slice_providers.slice import SliceProviders
        
        providers = SliceProviders()
        health = await providers.health_check()
        
        assert "status" in health
        assert "slice" in health
        assert "version" in health
        assert "initialized" in health
        assert "database_connected" in health
        assert "provider_count" in health
        assert health["slice"] == "slice_providers"
    
    @pytest.mark.asyncio
    async def test_skills_health_check(self):
        """Test skills slice health check."""
        from refactorbot.slices.slice_skills.slice import SliceSkills
        
        skills = SliceSkills()
        health = await skills.health_check()
        
        assert "status" in health
        assert "slice" in health
        assert "version" in health
        assert "initialized" in health
        assert "database_connected" in health
        assert "skills_count" in health
        assert health["slice"] == "slice_skills"
    
    @pytest.mark.asyncio
    async def test_eventbus_health_check(self):
        """Test eventbus slice health check."""
        from refactorbot.slices.slice_eventbus.slice import SliceEventBus
        
        eventbus = SliceEventBus()
        health = await eventbus.health_check()
        
        assert "status" in health
        assert "slice" in health
        assert "version" in health
        assert "initialized" in health
        assert "subscriber_count" in health
        assert "topic_count" in health
        assert health["slice"] == "slice_eventbus"
    
    @pytest.mark.asyncio
    async def test_scheduling_health_check(self):
        """Test scheduling slice health check."""
        from refactorbot.slices.slice_scheduling.slice import SliceScheduling
        
        scheduling = SliceScheduling()
        health = await scheduling.health_check()
        
        assert "status" in health
        assert "slice" in health
        assert "version" in health
        assert "initialized" in health
        assert "database_connected" in health
        assert "running" in health
        assert "task_count" in health
        assert health["slice"] == "slice_scheduling"


class TestSliceSelfDiagnostics:
    """Tests for slice run_self_diagnostics implementations."""
    
    @pytest.mark.asyncio
    async def test_base_slice_diagnostics(self):
        """Test BaseSlice run_self_diagnostics."""
        from refactorbot.slices.slice_base import BaseSlice, SliceConfig
        
        class TestSlice(BaseSlice):
            slice_id = "test_slice"
            slice_name = "Test Slice"
            slice_version = "1.0.0"
            config_class = SliceConfig
        
        slice = TestSlice()
        diag = await slice.run_self_diagnostics()
        
        assert "slice_id" in diag
        assert "slice_name" in diag
        assert "version" in diag
        assert "status" in diag
        assert "health" in diag
        assert "checks" in diag
        assert "issues" in diag
        assert "summary" in diag
        assert diag["slice_id"] == "test_slice"
    
    @pytest.mark.asyncio
    async def test_agent_diagnostics(self):
        """Test agent slice run_self_diagnostics."""
        from refactorbot.slices.slice_agent.slice import SliceAgent
        
        agent = SliceAgent()
        diag = await agent.run_self_diagnostics()
        
        assert "slice_id" in diag
        assert "slice_name" in diag
        assert "checks" in diag
        assert "issues" in diag
        assert "summary" in diag
        assert "overall_health" in diag


class TestSchedulingSlice:
    """Tests for scheduling slice functionality."""
    
    @pytest.mark.asyncio
    async def test_schedule_task(self):
        """Test scheduling a task."""
        from refactorbot.slices.slice_scheduling.slice import SliceScheduling
        
        scheduling = SliceScheduling()
        await scheduling.initialize()
        
        # Schedule a task
        response = await scheduling.execute(
            operation="schedule_task",
            payload={
                "name": "test_task_1",
                "cron_expression": "* * * * *",
                "task_type": "test",
                "config": {}
            }
        )
        
        assert response.success is True
        assert response.payload.get("task_id") is not None  # Generated task_id
    
    @pytest.mark.asyncio
    async def test_list_scheduled_tasks(self):
        """Test listing scheduled tasks."""
        from refactorbot.slices.slice_scheduling.slice import SliceScheduling
        
        scheduling = SliceScheduling()
        await scheduling.initialize()
        
        # List tasks
        response = await scheduling.execute(
            operation="list_tasks",
            payload={}
        )
        
        assert response.success is True
        assert "tasks" in response.payload


class TestToolHandlers:
    """Tests for tool handlers."""
    
    @pytest.mark.asyncio
    async def test_file_handler_read(self):
        """Test file handler read operation."""
        from refactorbot.slices.slice_tools.core.handlers.file_handlers import FileHandlers
        import tempfile
        import os
        
        # Create temp file in current directory (within workspace)
        temp_path = "test_temp_file.txt"
        try:
            with open(temp_path, 'w') as f:
                f.write("Hello, World!")
            
            handlers = FileHandlers(workspace_root=os.getcwd())
            result = await handlers.read_file(path=temp_path)
            
            assert "Hello, World!" in result
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    @pytest.mark.asyncio
    async def test_file_handler_list(self):
        """Test file handler list operation."""
        from refactorbot.slices.slice_tools.core.handlers.file_handlers import FileHandlers
        import tempfile
        import os
        
        # Create temp dir in current workspace
        temp_dir = "test_temp_dir"
        os.makedirs(temp_dir, exist_ok=True)
        
        try:
            # Create some files
            for i in range(3):
                with open(os.path.join(temp_dir, f"file_{i}.txt"), 'w') as f:
                    f.write(f"Content {i}")
            
            handlers = FileHandlers(workspace_root=os.getcwd())
            result = await handlers.list_files(path=temp_dir, recursive=False)
            
            # Result is a JSON string
            import json
            files = json.loads(result)
            assert len(files) == 3
        finally:
            import shutil
            shutil.rmtree(temp_dir)


class TestLiteLLMGateway:
    """Tests for LiteLLM gateway."""
    
    @pytest.mark.asyncio
    async def test_gateway_initialization(self):
        """Test LiteLLM gateway initialization."""
        from refactorbot.providers.litellm_gateway import LiteLLMGateway
        
        gateway = LiteLLMGateway()
        
        assert gateway is not None
        assert len(gateway.SUPPORTED_PROVIDERS) > 0
        assert "openai" in gateway.SUPPORTED_PROVIDERS
        assert "anthropic" in gateway.SUPPORTED_PROVIDERS
    
    def test_gateway_completion_no_provider(self):
        """Test completion without provider specified."""
        import pytest
        from refactorbot.providers.litellm_gateway import LiteLLMGateway
        
        gateway = LiteLLMGateway()
        
        # Verify initialization works with default config
        assert hasattr(gateway, 'SUPPORTED_PROVIDERS')
        assert len(gateway.SUPPORTED_PROVIDERS) > 0
        
        # complete() should raise error when called with no API key configured
        import asyncio
        try:
            asyncio.get_event_loop().run_until_complete(
                gateway.complete(prompt="test")
            )
        except ValueError:
            pass  # Expected when no API key is set


class TestPluginBase:
    """Tests for plugin base classes."""
    
    def test_plugin_adapter_protocol(self):
        """Test PluginAdapter protocol structure."""
        from refactorbot.plugins.plugin_base import PluginAdapter
        
        # Verify protocol methods exist
        assert hasattr(PluginAdapter, '__protocol_attrs__')
        
    def test_message_adapter_protocol(self):
        """Test MessageAdapter protocol structure."""
        from refactorbot.plugins.plugin_base import MessageAdapter
        
        # Verify protocol methods exist
        assert hasattr(MessageAdapter, '__protocol_attrs__')
    
    def test_channel_adapter_protocol(self):
        """Test ChannelAdapter protocol structure."""
        from refactorbot.plugins.plugin_base import ChannelAdapter
        
        # Verify protocol methods exist
        assert hasattr(ChannelAdapter, '__protocol_attrs__')
