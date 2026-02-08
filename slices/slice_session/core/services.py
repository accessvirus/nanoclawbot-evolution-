"""
Session System Services for slice_session

Core business logic for session management.
"""

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..slice_base import AtomicSlice

logger = logging.getLogger(__name__)


class SessionServices:
    """Services for session management."""
    
    def __init__(self, slice: "AtomicSlice"):
        self.slice = slice
        self.db = slice.database
    
    async def create_session(
        self,
        user_id: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create a new session."""
        session_id = f"sess_{secrets.token_urlsafe(16)}"
        token = secrets.token_urlsafe(32)
        
        async with self.db.transaction():
            await self.db.execute(
                """INSERT INTO sessions (id, user_id, token, metadata, created_at, last_active)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                session_id, user_id, token, str(metadata or {}), 
                datetime.utcnow().isoformat(), datetime.utcnow().isoformat()
            )
        
        return {"session_id": session_id, "token": token}
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID."""
        row = await self.db.fetchone(
            "SELECT * FROM sessions WHERE id = ? AND is_active = 1",
            (session_id,)
        )
        return dict(row) if row else None
    
    async def validate_session(self, session_id: str, token: str) -> bool:
        """Validate session token."""
        row = await self.db.fetchone(
            "SELECT * FROM sessions WHERE id = ? AND token = ? AND is_active = 1",
            (session_id, token)
        )
        return row is not None
    
    async def update_session(
        self,
        session_id: str,
        **updates
    ) -> bool:
        """Update session."""
        updates["last_active"] = datetime.utcnow().isoformat()
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [session_id]
        
        await self.db.execute(
            f"UPDATE sessions SET {set_clause} WHERE id = ?",
            values
        )
        return True
    
    async def end_session(self, session_id: str) -> bool:
        """End a session."""
        await self.db.execute(
            "UPDATE sessions SET is_active = 0, ended_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), session_id)
        )
        return True
    
    async def get_user_sessions(
        self,
        user_id: str,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all sessions for a user."""
        if active_only:
            rows = await self.db.fetchall(
                """SELECT * FROM sessions 
                   WHERE user_id = ? AND is_active = 1
                   ORDER BY created_at DESC""",
                (user_id,)
            )
        else:
            rows = await self.db.fetchall(
                """SELECT * FROM sessions 
                   WHERE user_id = ?
                   ORDER BY created_at DESC""",
                (user_id,)
            )
        
        return [dict(row) for row in rows]
    
    async def cleanup_expired_sessions(self, max_inactive_minutes: int = 60) -> int:
        """Clean up expired sessions."""
        cutoff = datetime.utcnow() - timedelta(minutes=max_inactive_minutes)
        result = await self.db.execute(
            """UPDATE sessions SET is_active = 0 
               WHERE is_active = 1 AND last_active < ?""",
            (cutoff.isoformat(),)
        )
        return result


class ConversationServices:
    """Services for conversation management."""
    
    def __init__(self, slice: "AtomicSlice"):
        self.slice = slice
        self.db = slice.database
    
    async def create_conversation(
        self,
        session_id: str,
        title: str = None
    ) -> str:
        """Create a new conversation."""
        conv_id = f"conv_{int(datetime.utcnow().timestamp() * 1000)}"
        
        async with self.db.transaction():
            await self.db.execute(
                """INSERT INTO conversations (id, session_id, title, created_at)
                   VALUES (?, ?, ?, ?)""",
                conv_id, session_id, title or "New Conversation", datetime.utcnow().isoformat()
            )
        
        return conv_id
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Add a message to a conversation."""
        message_id = f"msg_{int(datetime.utcnow().timestamp() * 1000)}"
        
        async with self.db.transaction():
            await self.db.execute(
                """INSERT INTO messages (id, conversation_id, role, content, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                message_id, conversation_id, role, content, 
                str(metadata or {}), datetime.utcnow().isoformat()
            )
        
        return message_id
    
    async def get_conversation(
        self,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get conversation by ID."""
        row = await self.db.fetchone(
            "SELECT * FROM conversations WHERE id = ?",
            (conversation_id,)
        )
        return dict(row) if row else None
    
    async def get_messages(
        self,
        conversation_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get messages from a conversation."""
        rows = await self.db.fetchall(
            """SELECT * FROM messages 
               WHERE conversation_id = ?
               ORDER BY created_at ASC LIMIT ?""",
            (conversation_id, limit)
        )
        return [dict(row) for row in rows]
    
    async def get_session_conversations(
        self,
        session_id: str
    ) -> List[Dict[str, Any]]:
        """Get all conversations for a session."""
        rows = await self.db.fetchall(
            """SELECT * FROM conversations 
               WHERE session_id = ?
               ORDER BY created_at DESC""",
            (session_id,)
        )
        return [dict(row) for row in rows]
