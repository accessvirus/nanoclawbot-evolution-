"""
Communication Slice - Vertical Slice for Communication Management
"""

import logging
from typing import Any, Dict, Optional

from ..slice_base import AtomicSlice, SliceConfig, SliceRequest, SliceResponse, SelfImprovementServices

logger = logging.getLogger(__name__)


class SliceCommunication(AtomicSlice):
    @property
    def slice_id(self) -> str:
        return "slice_communication"
    
    @property
    def slice_name(self) -> str:
        return "Communication Slice"
    
    @property
    def slice_version(self) -> str:
        return "1.0.0"
    
    def __init__(self, config: Optional[SliceConfig] = None):
        self._config = config or SliceConfig(slice_id="slice_communication")
        self._services: Optional[Any] = None
        self._current_request_id: str = ""  # Store request_id for internal methods
    
    @property
    def config(self) -> SliceConfig:
        return self._config
    
    async def _execute_core(self, request: SliceRequest) -> SliceResponse:
        # Store request_id for internal methods
        self._current_request_id = request.request_id
        operation = request.operation
        
        if operation == "create_channel":
            return await self._create_channel(request.payload)
        elif operation == "send_message":
            return await self._send_message(request.payload)
        elif operation == "get_messages":
            return await self._get_messages(request.payload)
        elif operation == "list_channels":
            return await self._list_channels(request.payload)
        elif operation == "delete_channel":
            return await self._delete_channel(request.payload)
        else:
            return SliceResponse(request_id=request.request_id, success=False, payload={"error": f"Unknown operation: {operation}"})
    
    async def _create_channel(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import ChannelManagementServices
            if self._services is None:
                self._services = ChannelManagementServices(self)
            channel_id = await self._services.create_channel(
                name=payload.get("name", ""),
                channel_type=payload.get("type", "text"),
                metadata=payload.get("metadata")
            )
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"channel_id": channel_id})
        except Exception as e:
            logger.error(f"Failed to create channel: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _send_message(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import MessageServices
            if self._services is None:
                self._services = MessageServices(self)
            message_id = await self._services.send_message(
                channel_id=payload.get("channel_id", ""),
                user_id=payload.get("user_id", ""),
                content=payload.get("content", ""),
                message_type=payload.get("message_type", "text")
            )
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"message_id": message_id})
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _get_messages(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import MessageServices
            if self._services is None:
                self._services = MessageServices(self)
            messages = await self._services.get_messages(
                channel_id=payload.get("channel_id", ""),
                limit=payload.get("limit", 100)
            )
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"messages": messages})
        except Exception as e:
            logger.error(f"Failed to get messages: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _list_channels(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import ChannelQueryServices
            if self._services is None:
                self._services = ChannelQueryServices(self)
            channels = await self._services.list_channels(channel_type=payload.get("type"))
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"channels": channels})
        except Exception as e:
            logger.error(f"Failed to list channels: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _delete_channel(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import ChannelManagementServices
            if self._services is None:
                self._services = ChannelManagementServices(self)
            success = await self._services.delete_channel(channel_id=payload.get("channel_id", ""))
            return SliceResponse(request_id=self._current_request_id, success=success, payload={"deleted": success})
        except Exception as e:
            logger.error(f"Failed to delete channel: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def self_improve(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        improver = SelfImprovementServices(self)
        improvements = await improver.analyze_and_improve(feedback)
        return {"improvements": improvements, "message": "Communication slice self-improvement complete"}
    
    async def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "slice": self.slice_id}
