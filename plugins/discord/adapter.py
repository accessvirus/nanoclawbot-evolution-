"""
Discord Channel Adapter Plugin for RefactorBot V2

This plugin provides Discord integration for multi-channel communication.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import aiohttp
from discord import Intents, Client, Message as DiscordMessage, Embed

from ..plugin_base import (
    BaseChannelAdapter,
    ChannelMessage,
    ChannelUser,
    ChannelConfig,
    AdapterMetrics,
    MessageType,
    PlatformType
)

logger = logging.getLogger(__name__)


@dataclass
class DiscordConfig(ChannelConfig):
    """Discord-specific configuration."""
    bot_token: str = ""
    guild_id: str = ""
    channel_ids: List[str] = field(default_factory=list)
    intents: List[str] = field(default_factory=lambda: ["messages", "guilds", "members"])
    command_prefix: str = "!"
    max_message_length: int = 2000
    rate_limit_per_second: int = 20


@dataclass
class DiscordUser(ChannelUser):
    """Discord-specific user data."""
    discord_id: str = ""
    discriminator: str = ""
    is_bot: bool = False
    roles: List[str] = field(default_factory=list)
    avatar_url: str = ""


@dataclass
class DiscordMessageData(ChannelMessage):
    """Discord-specific message data."""
    discord_message_id: str = ""
    guild_id: str = ""
    channel_id: str = ""
    embeds: List[Dict[str, Any]] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    reactions: List[Dict[str, Any]] = field(default_factory=list)


class DiscordAdapter(BaseChannelAdapter):
    """
    Discord channel adapter for RefactorBot V2.
    
    Provides bidirectional communication with Discord servers,
    supporting text messages, embeds, and reactions.
    """
    
    PLATFORM = PlatformType.DISCORD
    CONFIG_CLASS = DiscordConfig
    MESSAGE_CLASS = DiscordMessageData
    USER_CLASS = DiscordUser
    
    def __init__(self, config: DiscordConfig):
        super().__init__(config)
        self.config: DiscordConfig = config
        self._client: Optional[Client] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._running = False
        self._metrics: AdapterMetrics = AdapterMetrics()
        
    async def initialize(self) -> bool:
        """Initialize Discord client and connection."""
        try:
            # Create Discord client with intents
            intents = Intents.default()
            if "messages" in self.config.intents:
                intents.message_content = True
            if "guilds" in self.config.intents:
                intents.guilds = True
            if "members" in self.config.intents:
                intents.members = True
                
            self._client = Client(intents=intents)
            self._session = aiohttp.ClientSession()
            
            # Register event handlers
            self._register_handlers()
            
            # Start client in background
            asyncio.create_task(self._run_client())
            
            # Wait for ready
            await self._wait_for_ready()
            
            logger.info(f"Discord adapter initialized for guild {self.config.guild_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Discord adapter: {e}")
            return False
    
    def _register_handlers(self):
        """Register Discord event handlers."""
        @self._client.event
        async def on_ready():
            self._metrics.connections += 1
            logger.info(f"Discord bot logged in as {self._client.user}")
            
        @self._client.event
        async def on_message(message: DiscordMessage):
            if message.author.bot:
                return
            await self._handle_message(message)
            
        @self._client.event
        async def on_message_edit(before: DiscordMessage, after: DiscordMessage):
            await self._handle_edit(before, after)
            
        @self._client.event
        async def on_message_delete(message: DiscordMessage):
            await self._handle_delete(message)
            
    async def _wait_for_ready(self):
        """Wait for Discord client to be ready."""
        while not self._client or not self._client.is_ready():
            await asyncio.sleep(0.1)
    
    async def _run_client(self):
        """Run Discord client."""
        self._running = True
        try:
            await self._client.start(self.config.bot_token)
        except Exception as e:
            logger.error(f"Discord client error: {e}")
        finally:
            self._running = False
    
    async def _handle_message(self, message: DiscordMessage):
        """Handle incoming Discord message."""
        try:
            # Check if message is in allowed channel
            if str(message.channel.id) not in self.config.channel_ids:
                return
                
            # Create message object
            channel_msg = DiscordMessageData(
                id=message.id,
                platform=self.PLATFORM,
                type=MessageType.TEXT,
                content=message.content,
                user=DiscordUser(
                    id=message.author.id,
                    username=message.author.name,
                    display_name=message.author.display_name,
                    discord_id=str(message.author.id),
                    discriminator=message.author.discriminator,
                    is_bot=message.author.bot,
                    avatar_url=str(message.author.avatar.url) if message.author.avatar else ""
                ),
                timestamp=message.created_at,
                discord_message_id=str(message.id),
                guild_id=str(message.guild.id) if message.guild else "",
                channel_id=str(message.channel.id),
                embeds=[embed.to_dict() for embed in message.embeds],
                attachments=[{"filename": a.filename, "url": a.url} for a in message.attachments]
            )
            
            # Add to queue
            await self._message_queue.put(channel_msg)
            self._metrics.messages_received += 1
            
            # Emit event
            await self._emit_message(channel_msg)
            
        except Exception as e:
            logger.error(f"Error handling Discord message: {e}")
            self._metrics.errors += 1
    
    async def _handle_edit(self, before: DiscordMessage, after: DiscordMessage):
        """Handle message edit."""
        try:
            edited_msg = DiscordMessageData(
                id=after.id,
                platform=self.PLATFORM,
                type=MessageType.EDIT,
                content=after.content,
                user=DiscordUser(
                    id=after.author.id,
                    username=after.author.name,
                    display_name=after.author.display_name
                ),
                timestamp=after.edited_at,
                discord_message_id=str(after.id),
                channel_id=str(after.channel.id)
            )
            
            await self._emit_message(edited_msg, event_type="message_edited")
            
        except Exception as e:
            logger.error(f"Error handling message edit: {e}")
    
    async def _handle_delete(self, message: DiscordMessage):
        """Handle message delete."""
        try:
            deleted_msg = DiscordMessageData(
                id=message.id,
                platform=self.PLATFORM,
                type=MessageType.DELETE,
                content=message.content,
                timestamp=datetime.utcnow(),
                discord_message_id=str(message.id),
                channel_id=str(message.channel.id)
            )
            
            await self._emit_message(deleted_msg, event_type="message_deleted")
            
        except Exception as e:
            logger.error(f"Error handling message delete: {e}")
    
    async def send_message(
        self,
        channel_id: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Send message to Discord channel."""
        try:
            # Get channel
            channel = self._client.get_channel(int(channel_id))
            if not channel:
                raise ValueError(f"Channel {channel_id} not found")
            
            # Handle embed if provided
            embed_data = metadata.get("embed") if metadata else None
            embeds = []
            if embed_data:
                embed = Embed(
                    title=embed_data.get("title", ""),
                    description=embed_data.get("description", ""),
                    color=embed_data.get("color", 0x7289DA)
                )
                if "fields" in embed_data:
                    for field in embed_data["fields"]:
                        embed.add_field(
                            name=field.get("name", ""),
                            value=field.get("value", ""),
                            inline=field.get("inline", False)
                        )
                embeds.append(embed)
            
            # Send message
            if embeds:
                message = await channel.send(content=content, embeds=embeds)
            else:
                # Split long messages
                if len(content) > self.config.max_message_length:
                    parts = self._split_message(content)
                    messages = []
                    for part in parts:
                        msg = await channel.send(content=part)
                        messages.append(msg)
                    message_id = ",".join([str(m.id) for m in messages])
                else:
                    message = await channel.send(content=content)
                    message_id = str(message.id)
            
            self._metrics.messages_sent += 1
            return message_id
            
        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
            self._metrics.errors += 1
            raise
    
    def _split_message(self, content: str) -> List[str]:
        """Split message into chunks."""
        chunks = []
        while len(content) > self.config.max_message_length:
            # Find last newline before limit
            split_idx = content.rfind("\n", 0, self.config.max_message_length - 3)
            if split_idx == -1:
                split_idx = self.config.max_message_length - 3
            chunks.append(content[:split_idx] + "...")
            content = content[split_idx:]
        chunks.append(content)
        return chunks
    
    async def send_typing_indicator(self, channel_id: str) -> None:
        """Send typing indicator."""
        try:
            channel = self._client.get_channel(int(channel_id))
            if channel:
                async with channel.typing():
                    pass
        except Exception as e:
            logger.error(f"Error sending typing indicator: {e}")
    
    async def add_reaction(self, channel_id: str, message_id: str, emoji: str) -> bool:
        """Add reaction to message."""
        try:
            channel = self._client.get_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))
            await message.add_reaction(emoji)
            self._metrics.messages_sent += 1
            return True
        except Exception as e:
            logger.error(f"Error adding reaction: {e}")
            return False
    
    async def remove_reaction(
        self,
        channel_id: str,
        message_id: str,
        emoji: str,
        user_id: Optional[str] = None
    ) -> bool:
        """Remove reaction from message."""
        try:
            channel = self._client.get_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))
            await message.remove_reaction(emoji, self._client.user)
            return True
        except Exception as e:
            logger.error(f"Error removing reaction: {e}")
            return False
    
    async def get_message(self, channel_id: str, message_id: str) -> Optional[DiscordMessageData]:
        """Get specific message."""
        try:
            channel = self._client.get_channel(int(channel_id))
            message = await channel.fetch_message(int(message_id))
            
            return DiscordMessageData(
                id=message.id,
                platform=self.PLATFORM,
                content=message.content,
                timestamp=message.created_at,
                discord_message_id=str(message.id),
                channel_id=channel_id
            )
        except Exception as e:
            logger.error(f"Error getting message: {e}")
            return None
    
    async def get_channel_history(
        self,
        channel_id: str,
        limit: int = 100
    ) -> List[DiscordMessageData]:
        """Get message history from channel."""
        try:
            channel = self._client.get_channel(int(channel_id))
            messages = []
            async for message in channel.history(limit=limit):
                msg_data = DiscordMessageData(
                    id=message.id,
                    platform=self.PLATFORM,
                    content=message.content,
                    timestamp=message.created_at,
                    discord_message_id=str(message.id),
                    channel_id=channel_id
                )
                messages.append(msg_data)
            return messages
        except Exception as e:
            logger.error(f"Error getting channel history: {e}")
            return []
    
    async def create_channel(self, guild_id: str, name: str, category: Optional[str] = None) -> str:
        """Create new channel in guild."""
        try:
            guild = self._client.get_guild(int(guild_id))
            if not guild:
                raise ValueError(f"Guild {guild_id} not found")
            
            channel = await guild.create_text_channel(name)
            return str(channel.id)
        except Exception as e:
            logger.error(f"Error creating channel: {e}")
            raise
    
    async def delete_channel(self, channel_id: str) -> bool:
        """Delete channel."""
        try:
            channel = self._client.get_channel(int(channel_id))
            if channel:
                await channel.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting channel: {e}")
            return False
    
    async def get_user(self, user_id: str) -> Optional[DiscordUser]:
        """Get user information."""
        try:
            user = self._client.get_user(int(user_id))
            if user:
                return DiscordUser(
                    id=user.id,
                    username=user.name,
                    display_name=user.display_name,
                    discord_id=str(user.id),
                    discriminator=user.discriminator,
                    is_bot=user.bot,
                    avatar_url=str(user.avatar.url) if user.avatar else ""
                )
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def get_metrics(self) -> AdapterMetrics:
        """Get adapter metrics."""
        return self._metrics
    
    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        return {
            "platform": self.PLATFORM.value,
            "connected": self._client.is_ready() if self._client else False,
            "running": self._running,
            "queue_size": self._message_queue.qsize(),
            "metrics": self._metrics.__dict__
        }
    
    async def shutdown(self) -> None:
        """Shutdown adapter gracefully."""
        self._running = False
        if self._client:
            await self._client.close()
        if self._session:
            await self._session.close()
        logger.info("Discord adapter shutdown complete")
