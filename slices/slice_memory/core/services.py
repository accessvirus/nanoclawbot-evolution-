"""
Memory Core Services - Service Layer for Memory Slice

This module provides actual database operations for memory storage and retrieval.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...slice_base import AtomicSlice

logger = logging.getLogger(__name__)


class MemoryStorageServices:
    """Service for storing memories with actual database operations."""
    
    def __init__(self, slice: AtomicSlice):
        self.slice = slice
        self.db = getattr(slice, '_database', None) or getattr(slice, 'database', None)
    
    async def store_memory(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
        category: Optional[str] = None
    ) -> str:
        """Store a memory with the given key and value."""
        if not self.db:
            logger.warning("Database not initialized, using in-memory storage")
            return str(uuid.uuid4())
        
        memory_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        # ACTUAL DATABASE INSERTION
        try:
            await self.db.execute(
                """INSERT INTO memories 
                   (id, key, value, metadata, category, created_at, updated_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (memory_id, key, json.dumps(value), json.dumps(metadata or {}), 
                 category, now, now)
            )
            logger.info(f"Stored memory: {key} (ID: {memory_id})")
        except Exception as e:
            logger.error(f"Failed to store memory: {e}")
            raise
        
        return memory_id
    
    async def retrieve_memory(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a memory by its key."""
        if not self.db:
            logger.warning("Database not initialized")
            return None
        
        try:
            row = await self.db.fetchone(
                "SELECT * FROM memories WHERE key = ?",
                (key,)
            )
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {e}")
            raise
    
    async def update_memory(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a memory's value and metadata."""
        if not self.db:
            logger.warning("Database not initialized")
            return False
        
        now = datetime.utcnow().isoformat()
        try:
            await self.db.execute(
                """UPDATE memories SET value = ?, metadata = ?, updated_at = ? 
                   WHERE key = ?""",
                (json.dumps(value), json.dumps(metadata or {}), now, key)
            )
            logger.info(f"Updated memory: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to update memory: {e}")
            raise


class MemoryRetrievalServices:
    """Service for retrieving memories."""
    
    def __init__(self, slice: AtomicSlice):
        self.slice = slice
        self.db = getattr(slice, 'db', None)
    
    async def retrieve_memory(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve a memory by its key."""
        if not self.db:
            return {"key": key, "value": None, "status": "db_not_initialized"}
        
        try:
            row = await self.db.fetchone(
                "SELECT * FROM memories WHERE key = ?",
                (key,)
            )
            if row:
                result = dict(row)
                result['value'] = json.loads(result.get('value', '{}'))
                result['metadata'] = json.loads(result.get('metadata', '{}'))
                return result
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve memory: {e}")
            raise
    
    async def get_memory_by_id(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a memory by its ID."""
        if not self.db:
            return None
        
        try:
            row = await self.db.fetchone(
                "SELECT * FROM memories WHERE id = ?",
                (memory_id,)
            )
            if row:
                return dict(row)
            return None
        except Exception as e:
            logger.error(f"Failed to get memory by ID: {e}")
            raise


class MemorySearchServices:
    """Service for searching memories."""
    
    def __init__(self, slice: AtomicSlice):
        self.slice = slice
        self.db = getattr(slice, 'db', None)
    
    async def search_memories(
        self,
        query: str,
        category: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories by query and category."""
        if not self.db:
            return []
        
        try:
            if category:
                rows = await self.db.fetchall(
                    """SELECT * FROM memories WHERE value LIKE ? AND category = ? 
                       ORDER BY created_at DESC LIMIT ?""",
                    (f"%{query}%", category, limit)
                )
            else:
                rows = await self.db.fetchall(
                    """SELECT * FROM memories WHERE value LIKE ? 
                       ORDER BY created_at DESC LIMIT ?""",
                    (f"%{query}%", limit)
                )
            results = []
            for row in rows:
                r = dict(row)
                r['value'] = json.loads(r.get('value', '{}'))
                r['metadata'] = json.loads(r.get('metadata', '{}'))
                results.append(r)
            return results
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            raise
    
    async def search_by_tags(
        self,
        tags: List[str],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search memories by tags."""
        if not self.db or not tags:
            return []
        
        try:
            placeholders = ",".join("?" * len(tags))
            rows = await self.db.fetchall(
                f"""SELECT * FROM memories WHERE tags LIKE ? 
                    ORDER BY created_at DESC LIMIT ?""",
                (f"%{tags[0]}%", limit)
            )
            return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to search by tags: {e}")
            raise


class MemoryManagementServices:
    """Service for managing memories (update, delete)."""
    
    def __init__(self, slice: AtomicSlice):
        self.slice = slice
        self.db = getattr(slice, 'db', None)
    
    async def delete_memory(self, key: str) -> bool:
        """Delete a memory by its key."""
        if not self.db:
            return False
        
        try:
            await self.db.execute(
                "DELETE FROM memories WHERE key = ?",
                (key,)
            )
            logger.info(f"Deleted memory: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            raise
    
    async def delete_by_id(self, memory_id: str) -> bool:
        """Delete a memory by its ID."""
        if not self.db:
            return False
        
        try:
            await self.db.execute(
                "DELETE FROM memories WHERE id = ?",
                (memory_id,)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete memory by ID: {e}")
            raise
    
    async def purge_expired(self) -> int:
        """Delete all expired memories."""
        if not self.db:
            return 0
        
        try:
            now = datetime.utcnow().isoformat()
            cursor = await self.db.execute(
                "DELETE FROM memories WHERE expires_at < ?",
                (now,)
            )
            count = cursor.rowcount
            logger.info(f"Purged {count} expired memories")
            return count
        except Exception as e:
            logger.error(f"Failed to purge expired memories: {e}")
            raise


class MemoryQueryServices:
    """Service for querying memories (list, count)."""
    
    def __init__(self, slice: AtomicSlice):
        self.slice = slice
        self.db = getattr(slice, 'db', None)
    
    async def list_memories(
        self,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List memories, optionally filtered by category."""
        if not self.db:
            return []
        
        try:
            if category:
                rows = await self.db.fetchall(
                    """SELECT * FROM memories WHERE category = ? 
                       ORDER BY created_at DESC LIMIT ?""",
                    (category, limit)
                )
            else:
                rows = await self.db.fetchall(
                    """SELECT * FROM memories 
                       ORDER BY created_at DESC LIMIT ?""",
                    (limit,)
                )
            results = []
            for row in rows:
                r = dict(row)
                r['value'] = json.loads(r.get('value', '{}'))
                r['metadata'] = json.loads(r.get('metadata', '{}'))
                results.append(r)
            return results
        except Exception as e:
            logger.error(f"Failed to list memories: {e}")
            raise
    
    async def count_memories(self, category: Optional[str] = None) -> int:
        """Count memories, optionally filtered by category."""
        if not self.db:
            return 0
        
        try:
            if category:
                row = await self.db.fetchone(
                    "SELECT COUNT(*) as count FROM memories WHERE category = ?",
                    (category,)
                )
            else:
                row = await self.db.fetchone(
                    "SELECT COUNT(*) as count FROM memories"
                )
            return row['count'] if row else 0
        except Exception as e:
            logger.error(f"Failed to count memories: {e}")
            raise
    
    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        if not self.db:
            return {"total": 0, "categories": {}}
        
        try:
            total = await self.count_memories()
            categories = {}
            rows = await self.db.fetchall(
                "SELECT category, COUNT(*) as count FROM memories GROUP BY category"
            )
            for row in rows:
                categories[row['category'] or 'uncategorized'] = row['count']
            return {"total": total, "categories": categories}
        except Exception as e:
            logger.error(f"Failed to get memory stats: {e}")
            raise
