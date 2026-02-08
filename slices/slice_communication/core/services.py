"""
Communication System Services for slice_communication

Core business logic for messaging and channels.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..slice_base import AtomicSlice

logger = logging.getLogger(__name__)


class CommunicationServices:
    """Services for communication management."""
    
    def __init__(self, slice: "AtomicSlice"):
        self.slice = slice
        self.db = slice.database
    
    async def create_channel(
        self,
        name: str,
        channel_type: str = "text",
        metadata: Dict[str, Any] = None
    ) -> str:
        """Create a new channel."""
        channel_id = f"chan_{int(datetime.utcnow().timestamp() * 1000)}"
        
        async with self.db.transaction():
            await self.db.execute(
                """INSERT INTO channels (id, name, type, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                channel_id, name, channel_type, str(metadata or {}), datetime.utcnow().isoformat()
            )
        
        logger.info(f"Channel created: {name} ({channel_id})")
        return channel_id
    
    async def get_channel(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """Get channel by ID."""
        row = await self.db.fetchone(
            "SELECT * FROM channels WHERE id = ?",
            (channel_id,)
        )
        return dict(row) if row else None
    
    async def list_channels(self, channel_type: str = None) -> List[Dict[str, Any]]:
        """List all channels."""
        if channel_type:
            rows = await self.db.fetchall(
                "SELECT * FROM channels WHERE type = ? ORDER BY name",
                (channel_type,)
            )
        else:
            rows = await self.db.fetchall("SELECT * FROM channels ORDER BY name")
        
        return [dict(row) for row in rows]
    
    async def send_message(
        self,
        channel_id: str,
        user_id: str,
        content: str,
        message_type: str = "text"
    ) -> str:
        """Send a message to a channel."""
        message_id = f"msg_{int(datetime.utcnow().timestamp() * 1000)}"
        
        async with self.db.transaction():
            await self.db.execute(
                """INSERT INTO messages (id, channel_id, user_id, content, type, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                message_id, channel_id, user_id, content, message_type, datetime.utcnow().isoformat()
            )
        
        return message_id
    
    async def get_messages(
        self,
        channel_id: str,
        limit: int = 100,
        before: str = None
    ) -> List[Dict[str, Any]]:
        """Get messages from a channel."""
        if before:
            rows = await self.db.fetchall(
                """SELECT * FROM messages 
                   WHERE channel_id = ? AND id < ?
                   ORDER BY created_at DESC LIMIT ?""",
                (channel_id, before, limit)
            )
        else:
            rows = await self.db.fetchall(
                """SELECT * FROM messages 
                   WHERE channel_id = ?
                   ORDER BY created_at DESC LIMIT ?""",
                (channel_id, limit)
            )
        
        return [dict(row) for row in rows]
    
    async def delete_message(self, message_id: str) -> bool:
        """Delete a message."""
        await self.db.execute(
            "UPDATE messages SET is_deleted = 1 WHERE id = ?",
            (message_id,)
        )
        return True
    
    async def get_channel_stats(self, channel_id: str) -> Dict[str, Any]:
        """Get statistics for a channel."""
        total = await self.db.fetchone(
            "SELECT COUNT(*) as count FROM messages WHERE channel_id = ?",
            (channel_id,)
        )
        users = await self.db.fetchone(
            """SELECT COUNT(DISTINCT user_id) as count 
               FROM messages WHERE channel_id = ?""",
            (channel_id,)
        )
        
        return {
            "total_messages": total["count"] if total else 0,
            "unique_users": users["count"] if users else 0
        }
