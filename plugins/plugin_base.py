"""
Plugin Base Module - Base classes and interfaces for channel adapters.

This module defines the abstract base classes that all channel adapters must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar

import asyncio


class PlatformType(Enum):
    """Supported platform types."""
    TELEGRAM = "telegram"
    DISCORD = "discord"
    WHATSAPP = "whatsapp"
    FEISHU = "feishu"
    WEB = "web"
    API = "api"


class MessageType(Enum):
    """Message types supported by the system."""
    TEXT = "text"
    IMAGE = "image"
    FILE = "file"
    AUDIO = "audio"
    VIDEO = "video"
    LOCATION = "location"
    CONTACT = "contact"
    STICKER = "sticker"
    EDIT = "edit"
    CALLBACK = "callback"
    SYSTEM = "system"


@dataclass
class ChannelConfig:
    """Base configuration for channel adapters."""
    platform: PlatformType = PlatformType.WEB
    api_key: str = ""
    api_secret: str = ""
    webhook_url: Optional[str] = None
    webhook_path: str = "/webhook"
    max_message_length: int = 4096
    rate_limit_per_second: int = 30
    enabled: bool = True


@dataclass
class ChannelUser:
    """Base user information from channels."""
    id: str = ""
    username: str = ""
    display_name: str = ""
    avatar_url: Optional[str] = None
    is_bot: bool = False
    is_premium: bool = False
    language_code: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChannelMessage:
    """Base message structure for all channels."""
    id: str = ""
    platform: PlatformType = PlatformType.WEB
    type: MessageType = MessageType.TEXT
    content: str = ""
    user: Optional[ChannelUser] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Reply context
    reply_to_id: Optional[str] = None
    reply_to_message: Optional["ChannelMessage"] = None
    
    # Channel-specific fields
    chat_id: str = ""
    message_id: str = ""


@dataclass
class AdapterMetrics:
    """Metrics for adapter performance tracking."""
    messages_received: int = 0
    messages_sent: int = 0
    errors: int = 0
    last_message_at: Optional[datetime] = None
    uptime_seconds: float = 0.0


class BaseChannelAdapter(ABC):
    """
    Abstract base class for all channel adapters.
    
    All channel adapters must implement these methods.
    """
    
    PLATFORM: PlatformType
    CONFIG_CLASS: type
    MESSAGE_CLASS: type
    USER_CLASS: type
    
    def __init__(self, config: ChannelConfig):
        self.config = config
        self._running = False
        self._metrics = AdapterMetrics()
        self._message_handlers: List[callable] = []
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the adapter and establish connection."""
        pass
    
    @abstractmethod
    async def send_message(
        self,
        chat_id: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Send a message to the channel."""
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health status."""
        pass
    
    # Optional methods with default implementations
    
    async def start(self) -> bool:
        """Start the adapter."""
        if self._running:
            return True
        self._running = True
        return await self.initialize()
    
    async def stop(self) -> bool:
        """Stop the adapter."""
        self._running = False
        return True
    
    async def is_running(self) -> bool:
        """Check if adapter is running."""
        return self._running
    
    def add_message_handler(self, handler: callable) -> None:
        """Add a message handler callback."""
        self._message_handlers.append(handler)
    
    def remove_message_handler(self, handler: callable) -> None:
        """Remove a message handler callback."""
        if handler in self._message_handlers:
            self._message_handlers.remove(handler)
    
    async def _emit_message(
        self,
        message: ChannelMessage,
        event_type: str = "message_received"
    ) -> None:
        """Emit a message to all handlers."""
        for handler in self._message_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message, event_type)
                else:
                    handler(message, event_type)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error in message handler: {e}")
    
    async def get_metrics(self) -> AdapterMetrics:
        """Get adapter metrics."""
        self._metrics.uptime_seconds = (
            datetime.utcnow() - self._metrics.last_message_at
        ).total_seconds() if self._metrics.last_message_at else 0
        return self._metrics
    
    # Default implementations for common operations
    
    async def send_typing_indicator(self, chat_id: str) -> None:
        """Send typing indicator (optional)."""
        pass
    
    async def get_message(
        self,
        chat_id: str,
        message_id: str
    ) -> Optional[ChannelMessage]:
        """Get a specific message (optional)."""
        return None
    
    async def get_chat_history(
        self,
        chat_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[ChannelMessage]:
        """Get chat history (optional)."""
        return []
    
    async def get_user(self, user_id: str) -> Optional[ChannelUser]:
        """Get user information (optional)."""
        return None
    
    async def delete_message(
        self,
        chat_id: str,
        message_id: str
    ) -> bool:
        """Delete a message (optional)."""
        return False
    
    async def edit_message(
        self,
        chat_id: str,
        message_id: str,
        content: str
    ) -> bool:
        """Edit a message (optional)."""
        return False


# Type variable for generic adapter
AdapterType = TypeVar("AdapterType", bound=BaseChannelAdapter)


class PluginRegistry(Generic[AdapterType]):
    """
    Registry for managing channel adapters.
    """
    
    def __init__(self):
        self._adapters: Dict[str, AdapterType] = {}
        self._plugins: Dict[str, type] = {}
    
    def register_adapter(self, name: str, adapter_class: type) -> None:
        """Register an adapter class."""
        self._plugins[name] = adapter_class
    
    def create_adapter(
        self,
        name: str,
        config: ChannelConfig
    ) -> Optional[AdapterType]:
        """Create an adapter instance."""
        adapter_class = self._plugins.get(name)
        if adapter_class:
            return adapter_class(config)
        return None
    
    def get_adapter(self, name: str) -> Optional[AdapterType]:
        """Get a registered adapter instance."""
        return self._adapters.get(name)
    
    def register_instance(self, name: str, adapter: AdapterType) -> None:
        """Register an adapter instance."""
        self._adapters[name] = adapter
    
    def list_adapters(self) -> List[str]:
        """List all registered adapter names."""
        return list(self._plugins.keys())
    
    async def start_all(self) -> Dict[str, bool]:
        """Start all registered adapters."""
        results = {}
        for name, adapter in self._adapters.items():
            results[name] = await adapter.start()
        return results
    
    async def stop_all(self) -> Dict[str, bool]:
        """Stop all registered adapters."""
        results = {}
        for name, adapter in self._adapters.items():
            results[name] = await adapter.stop()
        return results


# =============================================================================
# Protocol Definitions (for structural subtyping)
# =============================================================================

class PluginAdapter(Protocol):
    """Protocol for plugin adapters."""
    
    PLATFORM: PlatformType
    CONFIG_CLASS: type
    MESSAGE_CLASS: type
    USER_CLASS: type
    
    @property
    def config(self) -> ChannelConfig: ...
    
    async def initialize(self) -> bool: ...
    
    async def send_message(
        self,
        chat_id: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str: ...
    
    async def health_check(self) -> Dict[str, Any]: ...
    
    __protocol_attrs__ = {
        'config', 'initialize', 'send_message', 'health_check',
        'PLATFORM', 'CONFIG_CLASS', 'MESSAGE_CLASS', 'USER_CLASS'
    }


class MessageAdapter(Protocol):
    """Protocol for message handling adapters."""
    
    async def send_message(
        self,
        chat_id: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str: ...
    
    async def get_message(
        self,
        chat_id: str,
        message_id: str
    ) -> Optional[ChannelMessage]: ...
    
    async def delete_message(
        self,
        chat_id: str,
        message_id: str
    ) -> bool: ...
    
    async def edit_message(
        self,
        chat_id: str,
        message_id: str,
        content: str
    ) -> bool: ...
    
    __protocol_attrs__ = {
        'send_message', 'get_message', 'delete_message', 'edit_message'
    }


class ChannelAdapter(Protocol):
    """Protocol for channel adapters."""
    
    PLATFORM: PlatformType
    
    @property
    def config(self) -> ChannelConfig: ...
    
    async def initialize(self) -> bool: ...
    
    async def start(self) -> bool: ...
    
    async def stop(self) -> bool: ...
    
    async def is_running(self) -> bool: ...
    
    async def health_check(self) -> Dict[str, Any]: ...
    
    async def get_user(self, user_id: str) -> Optional[ChannelUser]: ...
    
    async def get_chat_history(
        self,
        chat_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[ChannelMessage]: ...
    
    __protocol_attrs__ = {
        'config', 'initialize', 'start', 'stop', 'is_running',
        'health_check', 'get_user', 'get_chat_history', 'PLATFORM'
    }
