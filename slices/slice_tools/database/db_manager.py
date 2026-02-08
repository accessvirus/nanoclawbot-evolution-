"""Tools Slice Database Manager."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

from slices.slice_base import SliceDatabase


class ToolsDatabase(SliceDatabase):
    """Database manager for Tools Slice."""
    
    def __init__(self, db_path: str = "data/slice_tools.db"):
        super().__init__(db_path)
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.db_path)
        await self._connection.execute("PRAGMA foreign_keys = ON")
    
    async def initialize(self) -> None:
        if not self._connection:
            await self.connect()
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r") as f:
                schema = f.read()
            await self._connection.executescript(schema)
    
    async def create_tool(
        self,
        name: str,
        schema: Dict[str, Any],
        description: Optional[str] = None,
        category: Optional[str] = None,
        version: Optional[str] = None
    ) -> str:
        """Create a new tool."""
        tool_id = str(uuid.uuid4())
        await self._connection.execute(
            "INSERT INTO tools (id, name, description, schema, category, version) VALUES (?, ?, ?, ?, ?, ?)",
            (tool_id, name, description, json.dumps(schema), category, version)
        )
        await self._connection.commit()
        return tool_id
    
    async def get_tool(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a tool by name."""
        cursor = await self._connection.execute(
            "SELECT * FROM tools WHERE name = ? AND enabled = 1",
            (name,)
        )
        row = await cursor.fetchone()
        return self._row_to_tool(row) if row else None
    
    async def list_tools(self, category: Optional[str] = None, enabled: bool = True) -> List[Dict[str, Any]]:
        """List tools."""
        query = "SELECT * FROM tools WHERE enabled = ?"
        params = [1 if enabled else 0]
        if category:
            query += " AND category = ?"
            params.append(category)
        cursor = await self._connection.execute(query, tuple(params))
        rows = await cursor.fetchall()
        return [self._row_to_tool(row) for row in rows]
    
    async def execute_tool(
        self,
        tool_id: str,
        parameters: Dict[str, Any],
        result: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: int = 0
    ) -> str:
        """Record a tool execution."""
        execution_id = str(uuid.uuid4())
        await self._connection.execute(
            """INSERT INTO tool_executions 
            (id, tool_id, parameters, result, success, error_message, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (execution_id, tool_id, json.dumps(parameters), result, 1 if success else 0, error_message, duration_ms)
        )
        await self._connection.commit()
        return execution_id
    
    async def get_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get tool analytics."""
        cursor = await self._connection.execute(
            """SELECT tool_id, COUNT(*) as total, 
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success,
            AVG(duration_ms) as avg_duration
            FROM tool_executions 
            WHERE executed_at >= datetime('now', ?)
            GROUP BY tool_id""",
            (f"-{days} days",)
        )
        rows = await cursor.fetchall()
        return {"executions": [self._row_to_analytics(row) for row in rows]}
    
    def _row_to_tool(self, row: tuple) -> Dict[str, Any]:
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "schema": json.loads(row[3]) if row[3] else {},
            "category": row[4],
            "enabled": bool(row[5]),
            "version": row[6],
            "created_at": row[7],
            "updated_at": row[8]
        }
    
    def _row_to_analytics(self, row: tuple) -> Dict[str, Any]:
        return {
            "tool_id": row[0],
            "total": row[1],
            "success": row[2],
            "avg_duration": row[3]
        }
    
    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
