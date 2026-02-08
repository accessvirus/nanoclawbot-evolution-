"""
Plugins Package - Channel adapters for multi-channel communication.

Provides adapters for Telegram, Discord, WhatsApp, Feishu, and web channels.
"""

from .plugin_base import (
    PlatformType,
    MessageType,
    ChannelConfig,
    ChannelUser,
    ChannelMessage,
    AdapterMetrics,
    BaseChannelAdapter,
    PluginRegistry,
)

__all__ = [
    # Enums
    'PlatformType',
    'MessageType',
    # Config
    'ChannelConfig',
    # Data
    'ChannelUser',
    'ChannelMessage',
    'AdapterMetrics',
    # Base
    'BaseChannelAdapter',
    'PluginRegistry',
]
