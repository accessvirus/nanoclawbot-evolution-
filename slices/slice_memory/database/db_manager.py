"""Memory Slice Database Manager."""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiosqlite

from slices.slice_base import SliceDatabase


class MemoryDatabase(SliceDatabase):
    """Database manager for Memory Slice."""
    
    def __init__(self, db_path: str = "data/slice_memory.db"):
        super().__init__(db_path)
        self._connection: Optional[aiosqlite.Connection] = None
    
    async def connect(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = await aiosqlite.connect(self.db_path)
    
    async def initialize(self) -> None:
        if not self._connection:
            await self.connect()
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r") as f:
                await self._connection.executescript(f.read())
    
    async def store_memory(
        self,
        content: str,
        memory_type: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Store a new memory."""
        memory_id = str(uuid.uuid4())
        await self._connection.execute(
            """INSERT INTO memories (id, content, memory_type, user_id, session_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (memory_id, content, memory_type, user_id, session_id, json.dumps(metadata or {}))
        )
        await self._connection.commit()
        return memory_id
    
    async def retrieve_memories(
        self,
        query: Optional[str] = None,
        memory_type: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Retrieve memories based on query or filters."""
        conditions = []
        params = []
        
        if memory_type:
            conditions.append("memory_type = ?")
            params.append(memory_type)
        if user_id:
            conditions.append("user_id = ?")
            params.append(user_id)
        
        where = " AND ".join(conditions) if conditions else "1=1"
        params.append(limit)
        
        cursor = await self._connection.execute(
            f"""SELECT * FROM memories WHERE {where} ORDER BY created_at DESC LIMIT ?""",
            tuple(params)
        )
        rows = await cursor.fetchall()
        return [self._row_to_memory(row) for row in rows]
    
    async def store_long_term(self, key: str, value: Any, metadata: Optional[Dict] = None) -> None:
        """Store long-term memory."""
        await self._connection.execute(
            """INSERT OR REPLACE INTO long_term_memory (id, key, value, metadata, updated_at)
            VALUES (?, ?, ?, ?, ?)""",
            (str(uuid.uuid4()), key, json.dumps(value), json.dumps(metadata or {}), datetime.utcnow().isoformat())
        )
        await self._connection.commit()
    
    async def get_long_term(self, key: str) -> Optional[Any]:
        """Get long-term memory."""
        cursor = await self._connection.execute(
            "SELECT value FROM long_term_memory WHERE key = ?",
            (key,)
        )
        row = await cursor.fetchone()
        return json.loads(row[0]) if row else None
    
    async def consolidate_memories(self, source_ids: List[str], consolidated_content: str) -> str:
        """Consolidate multiple memories."""
        consolidation_id = str(uuid.uuid4())
        await self._connection.execute(
            "INSERT INTO memory_consolidation (id, source_ids, consolidated_content) VALUES (?, ?, ?)",
            (consolidation_id, json.dumps(source_ids), consolidated_content)
        )
        await self._connection.commit()
        return consolidation_id
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        cursor = await self._connection.execute("SELECT COUNT(*) FROM memories")
        total = (await cursor.fetchone())[0]
        
        cursor = await self._connection.execute("SELECT COUNT(*) FROM long_term_memory")
        ltm = (await cursor.fetchone())[0]
        
        return {"total_memories": total, "long_term_memories": ltm}
    
    def _row_to_memory(self, row: tuple) -> Dict[str, Any]:
        return {
            "id": row[0],
            "content": row[1],
            "memory_type": row[2],
            "user_id": row[4],
            "session_id": row[5],
            "created_at": row[6],
            "access_count": row[8]
        }
    
    async def close(self) -> None:
        if self._connection:
            await self._connection.close()
