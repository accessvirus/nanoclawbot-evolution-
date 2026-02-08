"""
Memory Slice - Vertical Slice for Memory Management

This slice handles memory storage and retrieval.
"""

import logging
import os
from pathlib import Path
from typing import Any, Optional

from ..slice_base import (
    AtomicSlice,
    BaseSlice,
    SliceConfig,
    SliceDatabase,
    SliceRequest,
    SliceResponse,
    SelfImprovementServices
)

logger = logging.getLogger(__name__)


class MemoryDatabase(SliceDatabase):
    """Database manager for memory slice."""
    
    def __init__(self, db_path: str):
        super().__init__(db_path)
    
    async def initialize(self) -> None:
        """Initialize memory database schema."""
        await self.connect()
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                key TEXT UNIQUE NOT NULL,
                value TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                category TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_key ON memories(key)
        """)
        await self._connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category)
        """)
        await self._connection.commit()


class SliceMemory(BaseSlice):
    """
    Memory slice for persistent memory storage.
    
    Responsibilities:
    - Memory storage
    - Memory retrieval
    - Memory search
    """
    
    @property
    def slice_id(self) -> str:
        return "slice_memory"
    
    @property
    def slice_name(self) -> str:
        return "Memory Slice"
    
    @property
    def slice_version(self) -> str:
        return "1.0.0"
    
    def __init__(self, config: Optional[SliceConfig] = None):
        super().__init__(config)
        self._services: Optional[Any] = None
        self._current_request_id: str = ""
        # Initialize database
        data_dir = Path("data")
        data_dir.mkdir(parents=True, exist_ok=True)
        self._database = MemoryDatabase(str(data_dir / "memory.db"))
    
    @property
    def config(self) -> SliceConfig:
        return self._config
    
    async def execute(self, request: SliceRequest) -> SliceResponse:
        """Public execute method for slice."""
        return await self._execute_core(request)
    
    async def _execute_core(self, request: SliceRequest) -> SliceResponse:
        self._current_request_id = request.request_id
        operation = request.operation
        
        if operation == "store":
            return await self._store_memory(request.payload)
        elif operation == "retrieve":
            return await self._retrieve_memory(request.payload)
        elif operation == "search":
            return await self._search_memory(request.payload)
        elif operation == "delete":
            return await self._delete_memory(request.payload)
        elif operation == "list":
            return await self._list_memories(request.payload)
        else:
            return SliceResponse(request_id=request.request_id, success=False, payload={"error": f"Unknown operation: {operation}"})
    
    async def _store_memory(self, payload: Dict[str, Any]) -> SliceResponse:
        """Store a new memory."""
        try:
            from .core.services import MemoryStorageServices
            if self._services is None:
                self._services = MemoryStorageServices(self)
            
            memory_id = await self._services.store_memory(
                key=payload.get("key", ""),
                value=payload.get("value", ""),
                metadata=payload.get("metadata")
            )
            
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"memory_id": memory_id})
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _retrieve_memory(self, payload: Dict[str, Any]) -> SliceResponse:
        """Retrieve a memory by key."""
        try:
            from .core.services import MemoryRetrievalServices
            if self._services is None:
                self._services = MemoryRetrievalServices(self)
            
            memory = await self._services.retrieve_memory(key=payload.get("key", ""))
            return SliceResponse(request_id=self._current_request_id, success=True, payload=memory)
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _search_memory(self, payload: Dict[str, Any]) -> SliceResponse:
        """Search memories by query."""
        try:
            from .core.services import MemorySearchServices
            if self._services is None:
                self._services = MemorySearchServices(self)
            
            results = await self._services.search_memories(
                query=payload.get("query", ""),
                limit=payload.get("limit", 10)
            )
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"results": results})
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _delete_memory(self, payload: Dict[str, Any]) -> SliceResponse:
        """Delete a memory by key."""
        try:
            from .core.services import MemoryManagementServices
            if self._services is None:
                self._services = MemoryManagementServices(self)
            
            success = await self._services.delete_memory(key=payload.get("key", ""))
            return SliceResponse(request_id=self._current_request_id, success=success, payload={"deleted": success})
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _list_memories(self, payload: Dict[str, Any]) -> SliceResponse:
        """List all memories."""
        try:
            from .core.services import MemoryQueryServices
            if self._services is None:
                self._services = MemoryQueryServices(self)
            
            memories = await self._services.list_memories(limit=payload.get("limit", 100))
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"memories": memories})
        except Exception as e:
            logger.error(f"Failed to list memories: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def self_improve(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Self-improvement for memory slice."""
        improver = SelfImprovementServices(self)
        improvements = await improver.analyze_and_improve(feedback)
        return {
            "improvements": improvements,
            "message": "Memory slice self-improvement complete"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for memory slice."""
        return {
            "status": "healthy",
            "slice": self.slice_id
        }
