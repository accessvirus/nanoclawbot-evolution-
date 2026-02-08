"""
Test Configuration and Fixtures for RefactorBot V2

Provides comprehensive test infrastructure for all slices.
"""

import asyncio
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator, List, Optional
import pytest
import pytest_asyncio

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as end-to-end test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection."""
    for item in items:
        # Add asyncio marker to async tests
        if hasattr(item, "obj") and asyncio.iscoroutinefunction(getattr(item, "obj", None)):
            item.add_marker(pytest.mark.asyncio)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for tests."""
    return asyncio.get_event_loop_policy()


@pytest.fixture(scope="session")
def loop(event_loop_policy) -> Generator:
    """Create event loop for session."""
    loop = event_loop_policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def temp_db_path(temp_dir) -> Path:
    """Create temporary database path."""
    return temp_dir / "test.db"


@pytest.fixture
def sample_slice_config(temp_dir) -> Dict[str, Any]:
    """Create sample slice configuration."""
    return {
        "name": "test_slice",
        "version": "1.0.0",
        "database_path": str(temp_dir / "slice.db"),
        "llm_provider": "openrouter",
        "enabled_features": ["dashboard", "analytics"],
        "settings": {
            "max_queue_size": 100,
            "timeout": 30
        }
    }


@pytest.fixture
def mock_llm_response() -> Dict[str, Any]:
    """Mock LLM response for testing."""
    return {
        "id": "test-123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-4",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "This is a test response from the LLM."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "total_tokens": 30
        }
    }


@pytest.fixture
def mock_stream_response() -> List[Dict[str, Any]]:
    """Mock streaming LLM response."""
    return [
        {"id": "test-123", "choices": [{"delta": {"content": "Hello"}}]},
        {"id": "test-123", "choices": [{"delta": {"content": " world"}}]},
        {"id": "test-123", "choices": [{"delta": {"content": "!"}}]},
    ]


# =============================================================================
# Slice Fixtures
# =============================================================================

@pytest.fixture
def slice_base():
    """Import slice base module."""
    from slices.slice_base import AtomicSlice, SliceContext, SliceRequest, SliceResponse
    return AtomicSlice, SliceContext, SliceRequest, SliceResponse


@pytest_asyncio.fixture
async def slice_context(sample_slice_config) -> AsyncGenerator:
    """Create slice context for testing."""
    from slices.slice_base import SliceContext
    
    context = SliceContext(
        slice_id="test-slice-001",
        config=sample_slice_config,
        state={}
    )
    yield context
    # Cleanup handled by context


@pytest_asyncio.fixture
async def mock_slice_instance(slice_context):
    """Create a mock slice instance for testing."""
    from slices.slice_base import AtomicSlice, SliceContext
    from typing import Protocol
    
    class MockSlice(AtomicSlice):
        name = "mock_slice"
        
        async def _execute_core(self, request):
            return {"status": "success", "data": request.payload}
    
    slice = MockSlice(context=slice_context)
    return slice


# =============================================================================
# Database Fixtures
# =============================================================================

@pytest.fixture
def sqlite_connection(temp_db_path):
    """Create SQLite connection for testing."""
    import sqlite3
    conn = sqlite3.connect(str(temp_db_path))
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest_asyncio.fixture
async def async_sqlite_connection(temp_db_path):
    """Create async SQLite connection for testing."""
    import aiosqlite
    conn = await aiosqlite.connect(str(temp_db_path))
    conn.row_factory = sqlite3.Row
    yield conn
    await conn.close()


@pytest.fixture
def sample_schema() -> str:
    """Sample database schema for testing."""
    return """
    CREATE TABLE IF NOT EXISTS test_table (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_test_table_name ON test_table(name);
    """


@pytest.fixture
def sample_data() -> List[Dict[str, Any]]:
    """Sample data for testing."""
    return [
        {"name": "item1", "value": "value1"},
        {"name": "item2", "value": "value2"},
        {"name": "item3", "value": "value3"},
    ]


# =============================================================================
# LLM Provider Fixtures
# =============================================================================

@pytest.fixture
def mock_openrouter_response() -> Dict[str, Any]:
    """Mock OpenRouter API response."""
    return {
        "id": "gen-123456",
        "object": "chat.completion",
        "created": 1699999999,
        "model": "anthropic/claude-2",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Test response"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 25,
            "total_tokens": 40
        }
    }


@pytest.fixture
def mock_openrouter_error() -> Dict[str, Any]:
    """Mock OpenRouter API error response."""
    return {
        "error": {
            "message": "Invalid API key",
            "type": "authentication_error",
            "code": 401
        }
    }


@pytest_asyncio.fixture
async def mock_llm_provider():
    """Create mock LLM provider for testing."""
    from providers.openrouter_gateway import OpenRouterGateway, LLMRequest
    
    class MockProvider(OpenRouterGateway):
        async def _make_request(self, request: LLMRequest) -> Dict[str, Any]:
            return {
                "id": "mock-123",
                "object": "chat.completion",
                "created": datetime.utcnow().timestamp(),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": "Mock response"},
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 10,
                    "total_tokens": 20
                }
            }
    
    provider = MockProvider(api_key="test-key")
    return provider


# =============================================================================
# Master Core Fixtures
# =============================================================================

@pytest.fixture
def master_core_config() -> Dict[str, Any]:
    """Master Core configuration for testing."""
    return {
        "state_db_path": ":memory:",
        "max_concurrent_tasks": 10,
        "task_timeout": 300,
        "heartbeat_interval": 30
    }


@pytest_asyncio.fixture
async def master_core_instance(master_core_config):
    """Create Master Core instance for testing."""
    from master_core.master_core import MasterCoreAI, MasterCoreConfig
    
    config = MasterCoreConfig(**master_core_config)
    core = MasterCoreAI(config)
    await core.start()
    yield core
    await core.shutdown()


# =============================================================================
# Adapter Fixtures
# =============================================================================

@pytest.fixture
def discord_config() -> Dict[str, Any]:
    """Discord adapter configuration for testing."""
    return {
        "bot_token": "test-token",
        "guild_id": "123456789",
        "channel_ids": ["111111111"],
        "command_prefix": "!",
        "max_message_length": 2000
    }


@pytest.fixture
def telegram_config() -> Dict[str, Any]:
    """Telegram adapter configuration for testing."""
    return {
        "bot_token": "test-token",
        "chat_ids": ["123456789"],
        "parse_mode": "HTML",
        "max_message_length": 4096
    }


@pytest.fixture
def whatsapp_config() -> Dict[str, Any]:
    """WhatsApp adapter configuration for testing."""
    return {
        "phone_number_id": "123456789",
        "business_account_id": "abcdef",
        "access_token": "test-token",
        "app_secret": "test-secret"
    }


@pytest.fixture
def feishu_config() -> Dict[str, Any]:
    """Feishu adapter configuration for testing."""
    return {
        "app_id": "test-app-id",
        "app_secret": "test-app-secret",
        "base_url": "https://open.feishu.cn/open-apis"
    }


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_messages() -> List[Dict[str, Any]]:
    """Sample messages for testing."""
    return [
        {
            "id": "msg-001",
            "role": "user",
            "content": "Hello, how are you?",
            "timestamp": datetime.utcnow().isoformat()
        },
        {
            "id": "msg-002",
            "role": "assistant",
            "content": "I'm doing well, thank you!",
            "timestamp": datetime.utcnow().isoformat()
        }
    ]


@pytest.fixture
def sample_session() -> Dict[str, Any]:
    """Sample session data for testing."""
    return {
        "session_id": "sess-123",
        "user_id": "user-456",
        "start_time": datetime.utcnow().isoformat(),
        "state": {
            "messages": [],
            "context": {}
        }
    }


@pytest.fixture
def sample_tool_definition() -> Dict[str, Any]:
    """Sample tool definition for testing."""
    return {
        "name": "test_tool",
        "description": "A test tool",
        "parameters": {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input parameter"}
            },
            "required": ["input"]
        },
        "handler": "test_handler"
    }


# =============================================================================
# Async Helpers
# =============================================================================

@pytest_asyncio.fixture
async def async_timeout():
    """Helper for testing async timeouts."""
    import async_timeout
    return async_timeout


@pytest.fixture
def run_async():
    """Helper to run async code in sync tests."""
    def _run(coro):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()
    return _run
