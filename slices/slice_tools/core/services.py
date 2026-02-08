"""
Tool System Services for slice_tools

Core business logic for tool management and execution.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..slice_base import AtomicSlice, SliceDatabase

logger = logging.getLogger(__name__)


@dataclass
class ToolExecutionResult:
    """Result of tool execution."""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    tool_name: str = ""


class ToolServices:
    """Services for tool management."""
    
    def __init__(self, slice: "AtomicSlice"):
        self.slice = slice
        self.context = slice.context
        self.db = slice.database
    
    async def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: str
    ) -> str:
        """Register a new tool."""
        tool_id = f"tool_{int(time.time() * 1000)}"
        
        async with self.db.transaction():
            await self.db.execute(
                """INSERT INTO tools (id, name, description, parameters, handler, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                tool_id, name, description, str(parameters), handler, datetime.utcnow().isoformat()
            )
        
        logger.info(f"Tool registered: {name} ({tool_id})")
        return tool_id
    
    async def get_tool(self, tool_id: str) -> Optional[Dict[str, Any]]:
        """Get tool by ID."""
        row = await self.db.fetchone(
            "SELECT * FROM tools WHERE id = ?",
            (tool_id,)
        )
        return dict(row) if row else None
    
    async def list_tools(self, category: str = None) -> List[Dict[str, Any]]:
        """List all tools."""
        if category:
            rows = await self.db.fetchall(
                "SELECT * FROM tools WHERE category = ? ORDER BY name",
                (category,)
            )
        else:
            rows = await self.db.fetchall("SELECT * FROM tools ORDER BY name")
        
        return [dict(row) for row in rows]
    
    async def update_tool(self, tool_id: str, **updates) -> bool:
        """Update tool."""
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [tool_id]
        
        result = await self.db.execute(
            f"UPDATE tools SET {set_clause}, updated_at = ? WHERE id = ?",
            values + [datetime.utcnow().isoformat(), tool_id]
        )
        
        return result > 0
    
    async def delete_tool(self, tool_id: str) -> bool:
        """Delete tool."""
        result = await self.db.execute(
            "UPDATE tools SET is_active = 0 WHERE id = ?",
            (tool_id,)
        )
        return result > 0
    
    async def execute_tool(
        self,
        tool_id: str,
        arguments: Dict[str, Any]
    ) -> ToolExecutionResult:
        """Execute a tool."""
        start_time = time.perf_counter()
        
        tool = await self.get_tool(tool_id)
        if not tool:
            return ToolExecutionResult(
                success=False,
                output="",
                error=f"Tool not found: {tool_id}",
                tool_name=tool_id
            )
        
        try:
            # Import and call handler
            handler_module = self._import_handler(tool["handler"])
            if handler_module:
                output = await handler_module.execute(arguments)
                execution_time = time.perf_counter() - start_time
                
                # Log execution
                await self._log_execution(tool_id, arguments, output, True, execution_time)
                
                return ToolExecutionResult(
                    success=True,
                    output=output,
                    execution_time=execution_time,
                    tool_name=tool["name"]
                )
            else:
                return ToolExecutionResult(
                    success=False,
                    output="",
                    error="Handler not found",
                    execution_time=time.perf_counter() - start_time,
                    tool_name=tool["name"]
                )
                
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            await self._log_execution(tool_id, arguments, str(e), False, execution_time)
            
            return ToolExecutionResult(
                success=False,
                output="",
                error=str(e),
                execution_time=execution_time,
                tool_name=tool["name"]
            )
    
    def _import_handler(self, handler_path: str):
        """Import handler module."""
        try:
            parts = handler_path.rsplit(".", 1)
            if len(parts) == 2:
                module = __import__(parts[0], fromlist=[parts[1]])
                return getattr(module, parts[1])()
        except Exception as e:
            logger.error(f"Error importing handler {handler_path}: {e}")
        return None
    
    async def _log_execution(
        self,
        tool_id: str,
        arguments: Dict[str, Any],
        output: str,
        success: bool,
        execution_time: float
    ):
        """Log tool execution."""
        await self.db.execute(
            """INSERT INTO tool_executions (tool_id, arguments, output, success, execution_time, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            tool_id, str(arguments), output, success, execution_time, datetime.utcnow().isoformat()
        )
    
    async def get_tool_stats(self) -> Dict[str, Any]:
        """Get tool execution statistics."""
        total = await self.db.fetchone("SELECT COUNT(*) as count FROM tool_executions")
        successful = await self.db.fetchone(
            "SELECT COUNT(*) as count FROM tool_executions WHERE success = 1"
        )
        failed = await self.db.fetchone(
            "SELECT COUNT(*) as count FROM tool_executions WHERE success = 0"
        )
        
        return {
            "total_executions": total["count"] if total else 0,
            "successful": successful["count"] if successful else 0,
            "failed": failed["count"] if failed else 0,
            "success_rate": (successful["count"] / total["count"] * 100) if total and total["count"] > 0 else 0
        }
    
    async def search_tools(self, query: str) -> List[Dict[str, Any]]:
        """Search tools by name or description."""
        rows = await self.db.fetchall(
            """SELECT * FROM tools 
               WHERE (name LIKE ? OR description LIKE ?) AND is_active = 1
               ORDER BY name""",
            (f"%{query}%", f"%{query}%")
        )
        return [dict(row) for row in rows]
