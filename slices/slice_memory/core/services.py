"""
Memory System Services for slice_memory

Core business logic for memory storage and retrieval.
"""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..slice_base import AtomicSlice

logger = logging.getLogger(__name__)


@dataclass
class MemoryQuery:
    """Memory query parameters."""
    query: str
    limit: int = 10
    min_similarity: float = 0.7
    memory_type: Optional[str] = None
    tags: List[str] = None
    user_id: Optional[str] = None


@dataclass
class MemoryResult:
    """Memory retrieval result."""
    id: str
    content: str
    metadata: Dict[str, Any]
    similarity: float
    created_at: datetime


class MemoryServices:
    """Services for memory management."""
    
    def __init__(self, slice: "AtomicSlice"):
        self.slice = slice
        self.db = slice.database
    
    async def store_memory(
        self,
        content: str,
        memory_type: str = "conversation",
        metadata: Dict[str, Any] = None,
        user_id: str = None
    ) -> str:
        """Store a new memory."""
        memory_id = f"mem_{int(time.time() * 1000)}"
        
        async with self.db.transaction():
            await self.db.execute(
                """INSERT INTO memories 
                   (id, content, type, metadata, user_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                memory_id, content, memory_type, str(metadata or {}), 
                user_id, datetime.utcnow().isoformat()
            )
        
        logger.info(f"Memory stored: {memory_id}")
        return memory_id
    
    async def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get memory by ID."""
        row = await self.db.fetchone(
            "SELECT * FROM memories WHERE id = ? AND is_active = 1",
            (memory_id,)
        )
        return dict(row) if row else None
    
    async def search_memories(self, query: MemoryQuery) -> List[MemoryResult]:
        """Search memories by content."""
        # Basic text search for now (can be enhanced with vector search)
        sql = """SELECT * FROM memories 
                 WHERE is_active = 1 
                 AND content LIKE ?
                 AND (type = ? OR ? IS NULL)
                 ORDER BY created_at DESC
                 LIMIT ?"""
        
        rows = await self.db.fetchall(
            sql,
            (f"%{query.query}%", query.memory_type, query.memory_type, query.limit)
        )
        
        results = []
        for row in rows:
            results.append(MemoryResult(
                id=row["id"],
                content=row["content"],
                metadata=eval(row["metadata"] or "{}"),
                similarity=0.8,  # Placeholder for vector similarity
                created_at=datetime.fromisoformat(row["created_at"])
            ))
        
        return results
    
    async def get_user_memories(
        self,
        user_id: str,
        memory_type: str = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get all memories for a user."""
        if memory_type:
            rows = await self.db.fetchall(
                """SELECT * FROM memories 
                   WHERE user_id = ? AND type = ? AND is_active = 1
                   ORDER BY created_at DESC LIMIT ?""",
                (user_id, memory_type, limit)
            )
        else:
            rows = await self.db.fetchall(
                """SELECT * FROM memories 
                   WHERE user_id = ? AND is_active = 1
                   ORDER BY created_at DESC LIMIT ?""",
                (user_id, limit)
            )
        
        return [dict(row) for row in rows]
    
    async def update_memory(
        self,
        memory_id: str,
        content: str = None,
        metadata: Dict[str, Any] = None
    ) -> bool:
        """Update memory content or metadata."""
        if content and metadata:
            await self.db.execute(
                """UPDATE memories SET content = ?, metadata = ?, 
                   updated_at = ? WHERE id = ?""",
                content, str(metadata), datetime.utcnow().isoformat(), memory_id
            )
        elif content:
            await self.db.execute(
                """UPDATE memories SET content = ?, updated_at = ? 
                   WHERE id = ?""",
                content, datetime.utcnow().isoformat(), memory_id
            )
        elif metadata:
            await self.db.execute(
                """UPDATE memories SET metadata = ?, updated_at = ? 
                   WHERE id = ?""",
                str(metadata), datetime.utcnow().isoformat(), memory_id
            )
        
        return True
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Soft delete memory."""
        await self.db.execute(
            "UPDATE memories SET is_active = 0, updated_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), memory_id)
        )
        return True
    
    async def consolidate_memories(self, user_id: str) -> int:
        """Consolidate similar memories."""
        # Get all memories
        memories = await self.get_user_memories(user_id)
        
        # Group by similarity (simplified - would use embeddings in production)
        consolidated = 0
        
        # This is a placeholder - real consolidation would use vector similarity
        logger.info(f"Consolidated {consolidated} memories for user {user_id}")
        
        return consolidated
    
    async def get_memory_stats(self, user_id: str = None) -> Dict[str, Any]:
        """Get memory statistics."""
        if user_id:
            total = await self.db.fetchone(
                "SELECT COUNT(*) as count FROM memories WHERE user_id = ? AND is_active = 1",
                (user_id,)
            )
            by_type = await self.db.fetchall(
                """SELECT type, COUNT(*) as count FROM memories 
                   WHERE user_id = ? AND is_active = 1 GROUP BY type""",
                (user_id,)
            )
        else:
            total = await self.db.fetchone(
                "SELECT COUNT(*) as count FROM memories WHERE is_active = 1"
            )
            by_type = await self.db.fetchall(
                """SELECT type, COUNT(*) as count FROM memories 
                   WHERE is_active = 1 GROUP BY type"""
            )
        
        return {
            "total_memories": total["count"] if total else 0,
            "by_type": {row["type"]: row["count"] for row in by_type}
        }
    
    async def clear_user_memories(self, user_id: str, memory_type: str = None) -> int:
        """Clear all memories for a user."""
        if memory_type:
            result = await self.db.execute(
                """UPDATE memories SET is_active = 0, updated_at = ? 
                   WHERE user_id = ? AND type = ?""",
                (datetime.utcnow().isoformat(), user_id, memory_type)
            )
        else:
            result = await self.db.execute(
                """UPDATE memories SET is_active = 0, updated_at = ? 
                   WHERE user_id = ?""",
                (datetime.utcnow().isoformat(), user_id)
            )
        
        return result
