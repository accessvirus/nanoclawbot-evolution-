"""
Event Bus Slice - Vertical Slice for Event Bus Management
"""

import logging
from typing import Any, Dict, Optional

from ..slice_base import AtomicSlice, SliceConfig, SliceRequest, SliceResponse, SelfImprovementServices

logger = logging.getLogger(__name__)


class SliceEventBus(AtomicSlice):
    @property
    def slice_id(self) -> str:
        return "slice_eventbus"
    
    @property
    def slice_name(self) -> str:
        return "Event Bus Slice"
    
    @property
    def slice_version(self) -> str:
        return "1.0.0"
    
    def __init__(self, config: Optional[SliceConfig] = None):
        self._config = config or SliceConfig(slice_id="slice_eventbus")
        self._services: Optional[Any] = None
        self._current_request_id: str = ""
    
    @property
    def config(self) -> SliceConfig:
        return self._config
    
    async def execute(self, request: SliceRequest) -> SliceResponse:
        """Public execute method for slice."""
        return await self._execute_core(request)
    
    async def _execute_core(self, request: SliceRequest) -> SliceResponse:
        self._current_request_id = request.request_id
        operation = request.operation
        
        if operation == "publish":
            return await self._publish_event(request.payload)
        elif operation == "subscribe":
            return await self._subscribe(request.payload)
        elif operation == "unsubscribe":
            return await self._unsubscribe(request.payload)
        elif operation == "get_events":
            return await self._get_events(request.payload)
        elif operation == "create_topic":
            return await self._create_topic(request.payload)
        elif operation == "list_topics":
            return await self._list_topics(request.payload)
        else:
            return SliceResponse(request_id=request.request_id, success=False, payload={"error": f"Unknown operation: {operation}"})
    
    async def _publish_event(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import EventPublishingServices
            if self._services is None:
                self._services = EventPublishingServices(self)
            event_id = await self._services.publish_event(
                topic=payload.get("topic", ""),
                event_type=payload.get("event_type", ""),
                data=payload.get("data", {})
            )
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"event_id": event_id})
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _subscribe(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import SubscriptionServices
            if self._services is None:
                self._services = SubscriptionServices(self)
            subscription_id = await self._services.subscribe(
                topic=payload.get("topic", ""),
                callback=payload.get("callback", "")
            )
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"subscription_id": subscription_id})
        except Exception as e:
            logger.error(f"Failed to subscribe: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _unsubscribe(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import SubscriptionServices
            if self._services is None:
                self._services = SubscriptionServices(self)
            success = await self._services.unsubscribe(subscription_id=payload.get("subscription_id", ""))
            return SliceResponse(request_id=self._current_request_id, success=success, payload={"unsubscribed": success})
        except Exception as e:
            logger.error(f"Failed to unsubscribe: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _get_events(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import EventQueryServices
            if self._services is None:
                self._services = EventQueryServices(self)
            events = await self._services.get_events(
                topic=payload.get("topic", ""),
                limit=payload.get("limit", 100)
            )
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"events": events})
        except Exception as e:
            logger.error(f"Failed to get events: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _create_topic(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import TopicManagementServices
            if self._services is None:
                self._services = TopicManagementServices(self)
            topic_id = await self._services.create_topic(
                name=payload.get("name", ""),
                description=payload.get("description", "")
            )
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"topic_id": topic_id})
        except Exception as e:
            logger.error(f"Failed to create topic: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _list_topics(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import TopicQueryServices
            if self._services is None:
                self._services = TopicQueryServices(self)
            topics = await self._services.list_topics()
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"topics": topics})
        except Exception as e:
            logger.error(f"Failed to list topics: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def self_improve(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        improver = SelfImprovementServices(self)
        improvements = await improver.analyze_and_improve(feedback)
        return {"improvements": improvements, "message": "Event Bus slice self-improvement complete"}
    
    async def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "slice": self.slice_id}
