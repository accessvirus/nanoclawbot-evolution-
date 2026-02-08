"""
Tools Slice - Vertical Slice for Tool Management

This slice handles tool registration and execution.
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


class ToolsDatabase(SliceDatabase):
    """Database manager for tools slice."""
    
    def __init__(self, db_path: str):
        super().__init__(db_path)
    
    async def initialize(self) -> None:
        """Initialize tools database schema."""
        await self.connect()
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS tools (
                id TEXT PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                parameters TEXT DEFAULT '{}',
                handler TEXT,
                category TEXT,
                enabled BOOLEAN DEFAULT 1,
                version TEXT DEFAULT '1.0.0',
                created_at TEXT,
                updated_at TEXT
            )
        """)
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS tool_executions (
                id TEXT PRIMARY KEY,
                tool_id TEXT NOT NULL,
                arguments TEXT DEFAULT '{}',
                output TEXT,
                success BOOLEAN DEFAULT 0,
                execution_time REAL DEFAULT 0,
                created_at TEXT,
                FOREIGN KEY (tool_id) REFERENCES tools(id)
            )
        """)
        await self._connection.execute("""CREATE INDEX IF NOT EXISTS idx_tool_executions_tool ON tool_executions(tool_id)""")
        await self._connection.commit()


class SliceTools(BaseSlice):
    """
    Tools slice for managing agent tools.
    
    Responsibilities:
    - Tool registration
    - Tool execution
    - Tool validation
    """
    
    # Protocol properties
    @property
    def slice_id(self) -> str:
        return "slice_tools"
    
    @property
    def slice_name(self) -> str:
        return "Tools Slice"
    
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
        self._database = ToolsDatabase(str(data_dir / "tools.db"))
    
    @property
    def config(self) -> SliceConfig:
        return self._config
    
    async def execute(self, request: SliceRequest) -> SliceResponse:
        """Public execute method for slice."""
        return await self._execute_core(request)
    
    async def _execute_core(self, request: SliceRequest) -> SliceResponse:
        """Execute tool operation."""
        self._current_request_id = request.request_id
        operation = request.operation
        
        if operation == "register_tool":
            return await self._register_tool(request.payload)
        elif operation == "execute_tool":
            return await self._execute_tool(request.payload)
        elif operation == "list_tools":
            return await self._list_tools(request.payload)
        elif operation == "validate_tool":
            return await self._validate_tool(request.payload)
        elif operation == "delete_tool":
            return await self._delete_tool(request.payload)
        else:
            return SliceResponse(request_id=request.request_id, success=False, payload={"error": f"Unknown operation: {operation}"})
    
    async def _register_tool(self, payload: Dict[str, Any]) -> SliceResponse:
        """Register a new tool."""
        try:
            from .core.services import ToolRegistrationServices
            if self._services is None:
                self._services = ToolRegistrationServices(self)
            
            tool_id = await self._services.register_tool(
                name=payload.get("name", ""),
                description=payload.get("description", ""),
                parameters=payload.get("parameters", {})
            )
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=True,
                payload={"tool_id": tool_id}
            )
        except Exception as e:
            logger.error(f"Failed to register tool: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _execute_tool(self, payload: Dict[str, Any]) -> SliceResponse:
        """Execute a tool."""
        try:
            from .core.services import ToolExecutionServices
            if self._services is None:
                self._services = ToolExecutionServices(self)
            
            result = await self._services.execute_tool(
                tool_id=payload.get("tool_id", ""),
                arguments=payload.get("arguments", {})
            )
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=True,
                payload={"result": result}
            )
        except Exception as e:
            logger.error(f"Failed to execute tool: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _list_tools(self, payload: Dict[str, Any]) -> SliceResponse:
        """List all registered tools."""
        try:
            from .core.services import ToolQueryServices
            if self._services is None:
                self._services = ToolQueryServices(self)
            
            tools = await self._services.list_tools(category=payload.get("category"))
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=True,
                payload={"tools": tools}
            )
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _validate_tool(self, payload: Dict[str, Any]) -> SliceResponse:
        """Validate a tool's parameters."""
        try:
            from .core.services import ToolValidationServices
            if self._services is None:
                self._services = ToolValidationServices(self)
            
            is_valid = await self._services.validate_tool(
                tool_id=payload.get("tool_id", ""),
                parameters=payload.get("parameters", {})
            )
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=True,
                payload={"valid": is_valid}
            )
        except Exception as e:
            logger.error(f"Failed to validate tool: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _delete_tool(self, payload: Dict[str, Any]) -> SliceResponse:
        """Delete a tool."""
        try:
            from .core.services import ToolManagementServices
            if self._services is None:
                self._services = ToolManagementServices(self)
            
            success = await self._services.delete_tool(tool_id=payload.get("tool_id", ""))
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=success,
                payload={"deleted": success}
            )
        except Exception as e:
            logger.error(f"Failed to delete tool: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def self_improve(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Self-improvement for tools slice."""
        improver = SelfImprovementServices(self)
        improvements = await improver.analyze_and_improve(feedback)
        return {
            "improvements": improvements,
            "message": "Tools slice self-improvement complete"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for tools slice."""
        return {
            "status": "healthy",
            "slice": self.slice_id
        }
