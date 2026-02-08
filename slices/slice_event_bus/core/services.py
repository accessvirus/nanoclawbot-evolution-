"""
Event Bus Services for slice_event_bus

Core business logic for event handling.
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ..slice_base import AtomicSlice

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """Event data structure."""
    id: str
    type: str
    payload: Dict[str, Any]
    source: str
    timestamp: datetime = None
    correlation_id: str = None
    metadata: Dict[str, Any] = None


class EventBusServices:
    """Services for event bus management."""
    
    def __init__(self, slice: "AtomicSlice"):
        self.slice = slice
        self.db = slice.database
        self._handlers: Dict[str, List[Callable]] = {}
        self._event_queues: Dict[str, asyncio.Queue] = {}
        self._max_queue_size = 1000  # Fixed for audit compliance
    
    async def publish(
        self,
        event_type: str,
        payload: Dict[str, Any],
        source: str,
        correlation_id: str = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Publish an event."""
        event_id = f"evt_{int(datetime.utcnow().timestamp() * 1000)}"
        
        # Store event in database
        async with self.db.transaction():
            await self.db.execute(
                """INSERT INTO events 
                   (id, type, payload, source, correlation_id, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                event_id, event_type, str(payload), source,
                correlation_id, str(metadata or {}), datetime.utcnow().isoformat()
            )
        
        # Add to subscriber queues
        await self._dispatch(event_id, event_type, payload)
        
        logger.info(f"Event published: {event_type} ({event_id})")
        return event_id
    
    async def subscribe(
        self,
        event_type: str,
        handler: Callable,
        queue_size: int = 100
    ) -> str:
        """Subscribe to an event type."""
        subscription_id = f"sub_{int(datetime.utcnow().timestamp() * 1000)}"
        
        if event_type not in self._handlers:
            self._handlers[event_type] = []
            self._event_queues[event_type] = asyncio.Queue(max_size=self._max_queue_size)
        
        self._handlers[event_type].append(handler)
        
        # Store subscription
        await self.db.execute(
            """INSERT INTO subscriptions (id, event_type, handler_name, created_at)
               VALUES (?, ?, ?, ?)""",
            subscription_id, event_type, handler.__name__, datetime.utcnow().isoformat()
        )
        
        logger.info(f"Subscribed to: {event_type}")
        return subscription_id
    
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        # Remove from handlers
        row = await self.db.fetchone(
            "SELECT event_type FROM subscriptions WHERE id = ?",
            (subscription_id,)
        )
        
        if row:
            event_type = row["event_type"]
            await self.db.execute(
                "DELETE FROM subscriptions WHERE id = ?",
                (subscription_id,)
            )
            return True
        
        return False
    
    async def _dispatch(
        self,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any]
    ):
        """Dispatch event to handlers."""
        event = Event(
            id=event_id,
            type=event_type,
            payload=payload,
            source="",
            timestamp=datetime.utcnow()
        )
        
        # Direct handlers
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
        
        # Queue subscribers
        queue = self._event_queues.get(event_type)
        if queue:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"Event queue full for {event_type}")
    
    async def get_events(
        self,
        event_type: str = None,
        limit: int = 100,
        start_time: datetime = None
    ) -> List[Dict[str, Any]]:
        """Get events from database."""
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND type = ?"
            params.append(event_type)
        if start_time:
            query += " AND created_at >= ?"
            params.append(start_time.isoformat())
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        rows = await self.db.fetchall(query, params)
        return [dict(row) for row in rows]
    
    async def get_event_stats(self) -> Dict[str, Any]:
        """Get event statistics."""
        total = await self.db.fetchone("SELECT COUNT(*) as count FROM events")
        by_type = await self.db.fetchall(
            """SELECT type, COUNT(*) as count FROM events 
               GROUP BY type ORDER BY count DESC"""
        )
        
        return {
            "total_events": total["count"] if total else 0,
            "by_type": {row["type"]: row["count"] for row in by_type},
            "active_subscriptions": len(self._handlers)
        }
