"""
Database manager for Agent Core Slice.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

from slices.slice_base import SliceDatabase


class AgentCoreDatabase(SliceDatabase):
    """
    Database manager for Agent Core Slice.
    Manages sessions, executions, and analytics.
    """
    
    def __init__(self, db_path: str = "data/slice_agent_core.db"):
        super().__init__(db_path)
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self) -> None:
        """Establish database connection"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.db_path)
        await self._connection.execute("PRAGMA foreign_keys = ON")
        await self._connection.execute("PRAGMA journal_mode=WAL")
    
    async def initialize(self) -> None:
        """Initialize database schema"""
        if not self._connection:
            await self.connect()
        
        # Read and execute schema
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r") as f:
                schema = f.read()
            await self._connection.executescript(schema)
    
    # -------------------------------------------------------------------------
    # Session Management
    # -------------------------------------------------------------------------
    
    async def create_session(
        self,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new agent session"""
        session_id = str(uuid.uuid4())
        
        await self._connection.execute(
            """
            INSERT INTO agent_sessions (id, user_id, context, state, metadata)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user_id,
                json.dumps(context or {}),
                "active",
                json.dumps(metadata or {})
            )
        )
        
        await self._connection.commit()
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by ID"""
        cursor = await self._connection.execute(
            "SELECT * FROM agent_sessions WHERE id = ?",
            (session_id,)
        )
        row = await cursor.fetchone()
        
        if row:
            return self._row_to_session(row)
        return None
    
    async def update_session(
        self,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        state: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a session"""
        updates = []
        params = []
        
        if context is not None:
            updates.append("context = ?")
            params.append(json.dumps(context))
        if state is not None:
            updates.append("state = ?")
            params.append(state)
        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata))
        
        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(session_id)
        
        if not updates:
            return False
        
        await self._connection.execute(
            f"UPDATE agent_sessions SET {', '.join(updates)} WHERE id = ?",
            params
        )
        await self._connection.commit()
        
        return True
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List sessions with optional filters"""
        query = "SELECT * FROM agent_sessions WHERE 1=1"
        params = []
        
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        if state:
            query += " AND state = ?"
            params.append(state)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = await self._connection.execute(query, tuple(params))
        rows = await cursor.fetchall()
        
        return [self._row_to_session(row) for row in rows]
    
    # -------------------------------------------------------------------------
    # Execution Management
    # -------------------------------------------------------------------------
    
    async def create_execution(
        self,
        session_id: str,
        request: str,
        response: Optional[str] = None,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        duration_ms: int = 0,
        success: bool = True,
        error_message: Optional[str] = None,
        model_used: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a new execution record"""
        execution_id = str(uuid.uuid4())
        total_tokens = prompt_tokens + completion_tokens
        
        await self._connection.execute(
            """
            INSERT INTO agent_executions 
            (id, session_id, request, response, prompt_tokens, completion_tokens,
             total_tokens, duration_ms, success, error_message, model_used, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                execution_id,
                session_id,
                request,
                response,
                prompt_tokens,
                completion_tokens,
                total_tokens,
                duration_ms,
                1 if success else 0,
                error_message,
                model_used,
                json.dumps(metadata or {})
            )
        )
        
        await self._connection.commit()
        return execution_id
    
    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get an execution by ID"""
        cursor = await self._connection.execute(
            "SELECT * FROM agent_executions WHERE id = ?",
            (execution_id,)
        )
        row = await cursor.fetchone()
        
        if row:
            return self._row_to_execution(row)
        return None
    
    async def list_executions(
        self,
        session_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List executions with optional session filter"""
        query = "SELECT * FROM agent_executions WHERE 1=1"
        params = []
        
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        
        query += " ORDER BY executed_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = await self._connection.execute(query, tuple(params))
        rows = await cursor.fetchall()
        
        return [self._row_to_execution(row) for row in rows]
    
    # -------------------------------------------------------------------------
    # Prompt Templates
    # -------------------------------------------------------------------------
    
    async def create_template(
        self,
        name: str,
        template: str,
        description: Optional[str] = None,
        variables: Optional[List[str]] = None,
        is_default: bool = False
    ) -> str:
        """Create a prompt template"""
        template_id = str(uuid.uuid4())
        
        await self._connection.execute(
            """
            INSERT INTO prompt_templates (id, name, description, template, variables, is_default)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                template_id,
                name,
                description,
                template,
                json.dumps(variables or []),
                1 if is_default else 0
            )
        )
        
        await self._connection.commit()
        return template_id
    
    async def get_template(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a template by name"""
        cursor = await self._connection.execute(
            "SELECT * FROM prompt_templates WHERE name = ?",
            (name,)
        )
        row = await cursor.fetchone()
        
        if row:
            return self._row_to_template(row)
        return None
    
    async def list_templates(self) -> List[Dict[str, Any]]:
        """List all templates"""
        cursor = await self._connection.execute(
            "SELECT * FROM prompt_templates ORDER BY created_at DESC"
        )
        rows = await cursor.fetchall()
        
        return [self._row_to_template(row) for row in rows]
    
    # -------------------------------------------------------------------------
    # Memory Cache
    # -------------------------------------------------------------------------
    
    async def cache_set(
        self,
        session_id: str,
        key: str,
        value: Any,
        expires_in_seconds: Optional[int] = None
    ) -> None:
        """Set a cache value"""
        expires_at = None
        if expires_in_seconds:
            expires_at = (datetime.utcnow() + timedelta(seconds=expires_in_seconds)).isoformat()
        
        await self._connection.execute(
            """
            INSERT OR REPLACE INTO memory_cache (id, session_id, key, value, expires_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(uuid.uuid4()), session_id, key, json.dumps(value), expires_at)
        )
        
        await self._connection.commit()
    
    async def cache_get(self, session_id: str, key: str) -> Optional[Any]:
        """Get a cache value"""
        cursor = await self._connection.execute(
            """
            SELECT value, expires_at FROM memory_cache 
            WHERE session_id = ? AND key = ?
            """,
            (session_id, key)
        )
        row = await cursor.fetchone()
        
        if row:
            expires_at = row[1]
            if expires_at:
                if datetime.fromisoformat(expires_at) < datetime.utcnow():
                    # Expired, delete it
                    await self._connection.execute(
                        "DELETE FROM memory_cache WHERE session_id = ? AND key = ?",
                        (session_id, key)
                    )
                    await self._connection.commit()
                    return None
            
            return json.loads(row[0])
        return None
    
    async def cache_delete(self, session_id: str, key: str) -> None:
        """Delete a cache value"""
        await self._connection.execute(
            "DELETE FROM memory_cache WHERE session_id = ? AND key = ?",
            (session_id, key)
        )
        await self._connection.commit()
    
    async def cache_clear(self, session_id: str) -> None:
        """Clear all cache for a session"""
        await self._connection.execute(
            "DELETE FROM memory_cache WHERE session_id = ?",
            (session_id,)
        )
        await self._connection.commit()
    
    # -------------------------------------------------------------------------
    # Analytics
    # -------------------------------------------------------------------------
    
    async def update_analytics(
        self,
        date: Optional[str] = None,
        success: bool = True,
        latency_ms: int = 0,
        tokens: int = 0,
        cost: float = 0.0
    ) -> None:
        """Update execution analytics"""
        date_str = date or datetime.utcnow().strftime("%Y-%m-%d")
        
        cursor = await self._connection.execute(
            """
            SELECT id FROM execution_analytics WHERE slice_id = 'slice_agent_core' AND date = ?
            """,
            (date_str,)
        )
        row = await cursor.fetchone()
        
        if row:
            await self._connection.execute(
                """
                UPDATE execution_analytics 
                SET total_executions = total_executions + 1,
                    successful_executions = successful_executions + ?,
                    failed_executions = failed_executions + ?,
                    avg_latency_ms = ((avg_latency_ms * ?) + ?) / (total_executions),
                    total_tokens = total_tokens + ?,
                    total_cost = total_cost + ?,
                    updated_at = ?
                WHERE id = ?
                """,
                (
                    1 if success else 0,
                    0 if success else 1,
                    await self._get_total_executions(date_str),
                    latency_ms,
                    tokens,
                    cost,
                    datetime.utcnow().isoformat(),
                    row[0]
                )
            )
        else:
            await self._connection.execute(
                """
                INSERT INTO execution_analytics 
                (id, slice_id, date, total_executions, successful_executions, 
                 failed_executions, avg_latency_ms, total_tokens, total_cost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(uuid.uuid4()),
                    "slice_agent_core",
                    date_str,
                    1,
                    1 if success else 0,
                    0 if success else 1,
                    latency_ms,
                    tokens,
                    cost
                )
            )
        
        await self._connection.commit()
    
    async def get_analytics(
        self,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """Get analytics for the last N days"""
        cursor = await self._connection.execute(
            """
            SELECT * FROM execution_analytics 
            WHERE date >= date('now', ?)
            ORDER BY date DESC
            """,
            (f"-{days} days",)
        )
        rows = await cursor.fetchall()
        
        return [self._row_to_analytics(row) for row in rows]
    
    async def _get_total_executions(self, date: str) -> int:
        """Get total executions for a date"""
        cursor = await self._connection.execute(
            "SELECT total_executions FROM execution_analytics WHERE date = ?",
            (date,)
        )
        row = await cursor.fetchone()
        return row[0] if row else 1
    
    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------
    
    def _row_to_session(self, row: tuple) -> Dict[str, Any]:
        """Convert session row to dict"""
        return {
            "id": row[0],
            "user_id": row[1],
            "context": json.loads(row[2]),
            "state": row[3],
            "metadata": json.loads(row[4]) if row[4] else {},
            "created_at": row[5],
            "updated_at": row[6]
        }
    
    def _row_to_execution(self, row: tuple) -> Dict[str, Any]:
        """Convert execution row to dict"""
        return {
            "id": row[0],
            "session_id": row[1],
            "request": row[2],
            "response": row[3],
            "prompt_tokens": row[4],
            "completion_tokens": row[5],
            "total_tokens": row[6],
            "duration_ms": row[7],
            "success": bool(row[8]),
            "error_message": row[9],
            "model_used": row[10],
            "metadata": json.loads(row[11]) if row[11] else {},
            "executed_at": row[12]
        }
    
    def _row_to_template(self, row: tuple) -> Dict[str, Any]:
        """Convert template row to dict"""
        return {
            "id": row[0],
            "name": row[1],
            "description": row[2],
            "template": row[3],
            "variables": json.loads(row[4]) if row[4] else [],
            "version": row[5],
            "is_default": bool(row[6]),
            "created_at": row[7],
            "updated_at": row[8]
        }
    
    def _row_to_analytics(self, row: tuple) -> Dict[str, Any]:
        """Convert analytics row to dict"""
        return {
            "id": row[0],
            "slice_id": row[1],
            "date": row[2],
            "total_executions": row[3],
            "successful_executions": row[4],
            "failed_executions": row[5],
            "avg_latency_ms": row[6],
            "total_tokens": row[7],
            "total_cost": row[8],
            "created_at": row[9],
            "updated_at": row[10]
        }
    
    async def close(self) -> None:
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None
