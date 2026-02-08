"""
Telegram Channel Adapter Plugin for RefactorBot V2

This plugin provides Telegram integration for multi-channel communication.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import aiohttp
from telegram import Bot, Chat, Message as TelegramMessage, User as TelegramUser
from telegram.error import TelegramError
from telegram.constants import ParseMode

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
class TelegramConfig(ChannelConfig):
    """Telegram-specific configuration."""
    bot_token: str = ""
    api_id: str = ""
    api_hash: str = ""
    chat_ids: List[str] = field(default_factory=list)
    parse_mode: str = "HTML"
    max_message_length: int = 4096
    rate_limit_per_second: int = 30
    webhook_url: Optional[str] = None
    webhook_path: str = "/webhook/telegram"
    delete_after_seconds: Optional[int] = None


@dataclass
class TelegramUserData(ChannelUser):
    """Telegram-specific user data."""
    telegram_id: int = 0
    is_premium: bool = False
    language_code: str = ""
    is_bot: bool = False


@dataclass
class TelegramMessageData(ChannelMessage):
    """Telegram-specific message data."""
    telegram_message_id: int = 0
    chat_id: int = 0
    message_thread_id: Optional[int] = None
    entities: List[Dict[str, Any]] = field(default_factory=list)
    reply_to_message_id: Optional[int] = None
    edit_date: Optional[datetime] = None


class TelegramAdapter(BaseChannelAdapter):
    """
    Telegram channel adapter for RefactorBot V2.
    
    Provides bidirectional communication with Telegram,
    supporting text, photos, documents, and stickers.
    """
    
    PLATFORM = PlatformType.TELEGRAM
    CONFIG_CLASS = TelegramConfig
    MESSAGE_CLASS = TelegramMessageData
    USER_CLASS = TelegramUserData
    
    def __init__(self, config: TelegramConfig):
        super().__init__(config)
        self.config: TelegramConfig = config
        self._bot: Optional[Bot] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._running = False
        self._metrics: AdapterMetrics = AdapterMetrics()
        self._rate_limiter = asyncio.Semaphore(self.config.rate_limit_per_second)
        
    async def initialize(self) -> bool:
        """Initialize Telegram bot."""
        try:
            self._bot = Bot(token=self.config.bot_token)
            self._session = aiohttp.ClientSession()
            
            # Set bot commands
            await self._set_commands()
            
            # Verify connection
            me = await self._bot.get_me()
            logger.info(f"Telegram bot initialized: @{me.username}")
            
            # Start polling or webhook
            if self.config.webhook_url:
                await self._setup_webhook()
            else:
                asyncio.create_task(self._polling_loop())
            
            self._running = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram adapter: {e}")
            return False
    
    async def _set_commands(self):
        """Set bot commands."""
        try:
            from telegram import BotCommand
            commands = [
                BotCommand("start", "Start the bot"),
                BotCommand("help", "Show help"),
                BotCommand("status", "Show status"),
            ]
            await self._bot.set_my_commands(commands)
        except Exception as e:
            logger.warning(f"Could not set commands: {e}")
    
    async def _setup_webhook(self):
        """Setup webhook for incoming updates."""
        try:
            webhook_url = f"{self.config.webhook_url}{self.config.webhook_path}"
            await self._bot.set_webhook(webhook_url)
            logger.info(f"Webhook set to {webhook_url}")
        except Exception as e:
            logger.error(f"Failed to setup webhook: {e}")
    
    async def _polling_loop(self):
        """Run polling loop for updates."""
        last_update_id = 0
        while self._running:
            try:
                updates = await self._bot.get_updates(
                    offset=last_update_id + 1,
                    timeout=30
                )
                for update in updates:
                    last_update_id = update.update_id
                    await self._handle_update(update)
            except TelegramError as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected polling error: {e}")
                await asyncio.sleep(1)
    
    async def _handle_update(self, update):
        """Handle incoming update."""
        try:
            if update.message:
                await self._handle_message(update.message)
            elif update.edited_message:
                await self._handle_edit(update.edited_message)
            elif update.callback_query:
                await self._handle_callback(update.callback_query)
        except Exception as e:
            logger.error(f"Error handling update: {e}")
            self._metrics.errors += 1
    
    async def _handle_message(self, message: TelegramMessage):
        """Handle incoming message."""
        try:
            # Check if chat is allowed
            if str(message.chat.id) not in self.config.chat_ids:
                return
                
            # Create message object
            channel_msg = TelegramMessageData(
                id=message.message_id,
                platform=self.PLATFORM,
                type=self._get_message_type(message),
                content=message.text or message.caption or "",
                user=TelegramUserData(
                    id=message.from_user.id,
                    username=message.from_user.username or "",
                    display_name=f"{message.from_user.first_name} {message.from_user.last_name or ''}".strip(),
                    telegram_id=message.from_user.id,
                    is_premium=message.from_user.is_premium or False,
                    language_code=message.from_user.language_code or "",
                    is_bot=message.from_user.is_bot
                ),
                timestamp=message.date,
                telegram_message_id=message.message_id,
                chat_id=message.chat.id,
                message_thread_id=message.message_thread_id,
                entities=[e.to_dict() for e in (message.entities or [])],
                reply_to_message_id=message.reply_to_message.message_id if message.reply_to_message else None
            )
            
            # Add to queue
            await self._message_queue.put(channel_msg)
            self._metrics.messages_received += 1
            
            # Emit event
            await self._emit_message(channel_msg)
            
        except Exception as e:
            logger.error(f"Error handling Telegram message: {e}")
            self._metrics.errors += 1
    
    def _get_message_type(self, message: TelegramMessage) -> MessageType:
        """Determine message type."""
        if message.text:
            return MessageType.TEXT
        elif message.photo:
            return MessageType.IMAGE
        elif message.document:
            return MessageType.FILE
        elif message.sticker:
            return MessageType.STICKER
        elif message.voice:
            return MessageType.AUDIO
        elif message.video:
            return MessageType.VIDEO
        elif message.location:
            return MessageType.LOCATION
        elif message.contact:
            return MessageType.CONTACT
        else:
            return MessageType.TEXT
    
    async def _handle_edit(self, message: TelegramMessage):
        """Handle edited message."""
        try:
            edited_msg = TelegramMessageData(
                id=message.message_id,
                platform=self.PLATFORM,
                type=MessageType.EDIT,
                content=message.text or message.caption or "",
                timestamp=message.date,
                telegram_message_id=message.message_id,
                chat_id=message.chat.id,
                edit_date=message.edit_date
            )
            
            await self._emit_message(edited_msg, event_type="message_edited")
            
        except Exception as e:
            logger.error(f"Error handling message edit: {e}")
    
    async def _handle_callback(self, callback):
        """Handle callback query."""
        try:
            await self._bot.answer_callback_query(callback.id)
            
            # Emit callback event
            await self._emit_message(
                TelegramMessageData(
                    id=callback.message.message_id if callback.message else 0,
                    platform=self.PLATFORM,
                    type=MessageType.CALLBACK,
                    content=callback.data,
                    chat_id=callback.message.chat.id if callback.message else 0
                ),
                event_type="callback_received"
            )
            
        except Exception as e:
            logger.error(f"Error handling callback: {e}")
    
    async def send_message(
        self,
        chat_id: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Send message to Telegram chat."""
        async with self._rate_limiter:
            try:
                chat_id_int = int(chat_id)
                parse_mode = ParseMode.HTML if self.config.parse_mode == "HTML" else None
                
                # Handle reply
                reply_to = metadata.get("reply_to_message_id") if metadata else None
                
                # Handle keyboard
                reply_markup = None
                if metadata and "keyboard" in metadata:
                    from telegram import ReplyKeyboardMarkup
                    reply_markup = ReplyKeyboardMarkup(
                        metadata["keyboard"],
                        resize_keyboard=True
                    )
                elif metadata and "inline_keyboard" in metadata:
                    from telegram import InlineKeyboardMarkup
                    reply_markup = InlineKeyboardMarkup(metadata["inline_keyboard"])
                
                # Send message
                if message_type == MessageType.IMAGE and metadata and "photo" in metadata:
                    message = await self._bot.send_photo(
                        chat_id=chat_id_int,
                        photo=metadata["photo"],
                        caption=content,
                        parse_mode=parse_mode,
                        reply_to_message_id=reply_to,
                        reply_markup=reply_markup
                    )
                elif message_type == MessageType.FILE and metadata and "document" in metadata:
                    message = await self._bot.send_document(
                        chat_id=chat_id_int,
                        document=metadata["document"],
                        caption=content,
                        parse_mode=parse_mode,
                        reply_to_message_id=reply_to,
                        reply_markup=reply_markup
                    )
                else:
                    # Split long messages
                    if len(content) > self.config.max_message_length:
                        parts = self._split_message(content)
                        message_ids = []
                        for part in parts:
                            msg = await self._bot.send_message(
                                chat_id=chat_id_int,
                                text=part,
                                parse_mode=parse_mode,
                                reply_to_message_id=reply_to,
                                reply_markup=reply_markup
                            )
                            message_ids.append(str(msg.message_id))
                            reply_to = None  # Only reply to first
                        message_id = ",".join(message_ids)
                    else:
                        message = await self._bot.send_message(
                            chat_id=chat_id_int,
                            text=content,
                            parse_mode=parse_mode,
                            reply_to_message_id=reply_to,
                            reply_markup=reply_markup
                        )
                        message_id = str(message.message_id)
                
                self._metrics.messages_sent += 1
                return message_id
                
            except TelegramError as e:
                logger.error(f"Telegram error sending message: {e}")
                self._metrics.errors += 1
                raise
    
    def _split_message(self, content: str) -> List[str]:
        """Split message into chunks."""
        chunks = []
        while len(content) > self.config.max_message_length:
            split_idx = content.rfind("\n", 0, self.config.max_message_length - 3)
            if split_idx == -1:
                split_idx = self.config.max_message_length - 3
            chunks.append(content[:split_idx] + "...")
            content = content[split_idx:]
        chunks.append(content)
        return chunks
    
    async def send_typing_indicator(self, chat_id: str) -> None:
        """Send typing indicator."""
        try:
            await self._bot.send_chat_action(chat_id=chat_id, action="typing")
        except TelegramError as e:
            logger.error(f"Error sending typing indicator: {e}")
    
    async def add_reaction(
        self,
        chat_id: str,
        message_id: str,
        emoji: str
    ) -> bool:
        """Add reaction to message."""
        try:
            await self._bot.set_message_reaction(
                chat_id=int(chat_id),
                message_id=int(message_id),
                reaction=[{"type": "emoji", "emoji": emoji}]
            )
            return True
        except TelegramError as e:
            logger.error(f"Error adding reaction: {e}")
            return False
    
    async def remove_reaction(
        self,
        chat_id: str,
        message_id: str,
        emoji: str
    ) -> bool:
        """Remove reaction from message."""
        try:
            await self._bot.set_message_reaction(
                chat_id=int(chat_id),
                message_id=int(message_id),
                reaction=[]
            )
            return True
        except TelegramError as e:
            logger.error(f"Error removing reaction: {e}")
            return False
    
    async def get_message(self, chat_id: str, message_id: str) -> Optional[TelegramMessageData]:
        """Get specific message."""
        try:
            message = await self._bot.forward_message(
                chat_id=chat_id,
                from_chat_id=chat_id,
                message_id=int(message_id)
            )
            
            return TelegramMessageData(
                id=message.message_id,
                platform=self.PLATFORM,
                content=message.text or "",
                timestamp=message.date,
                telegram_message_id=message.message_id,
                chat_id=int(chat_id)
            )
        except TelegramError as e:
            logger.error(f"Error getting message: {e}")
            return None
    
    async def get_chat_history(
        self,
        chat_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[TelegramMessageData]:
        """Get message history from chat."""
        try:
            messages = await self._bot.get_chat_history(
                chat_id=int(chat_id),
                limit=min(limit, 100)
            )
            
            result = []
            for message in list(messages)[offset:]:
                msg_data = TelegramMessageData(
                    id=message.message_id,
                    platform=self.PLATFORM,
                    content=message.text or message.caption or "",
                    timestamp=message.date,
                    telegram_message_id=message.message_id,
                    chat_id=int(chat_id)
                )
                result.append(msg_data)
            return result
        except TelegramError as e:
            logger.error(f"Error getting chat history: {e}")
            return []
    
    async def create_group(self, title: str, users: List[str]) -> str:
        """Create new group chat."""
        try:
            chat = await self._bot.create_group_chat(
                title=title,
                user_ids=[int(u) for u in users]
            )
            return str(chat.id)
        except TelegramError as e:
            logger.error(f"Error creating group: {e}")
            raise
    
    async def leave_chat(self, chat_id: str) -> bool:
        """Leave chat."""
        try:
            await self._bot.leave_chat(chat_id=int(chat_id))
            return True
        except TelegramError as e:
            logger.error(f"Error leaving chat: {e}")
            return False
    
    async def get_user(self, user_id: str) -> Optional[TelegramUserData]:
        """Get user information."""
        try:
            user = await self._bot.get_chat_member(chat_id=int(user_id), user_id=int(user_id))
            return TelegramUserData(
                id=user.user.id,
                username=user.user.username or "",
                display_name=f"{user.user.first_name} {user.user.last_name or ''}".strip(),
                telegram_id=user.user.id,
                is_premium=user.user.is_premium or False,
                language_code=user.user.language_code or "",
                is_bot=user.user.is_bot
            )
        except TelegramError as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    def get_metrics(self) -> AdapterMetrics:
        """Get adapter metrics."""
        return self._metrics
    
    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        try:
            me = await self._bot.get_me()
            return {
                "platform": self.PLATFORM.value,
                "connected": True,
                "bot_username": me.username,
                "running": self._running,
                "queue_size": self._message_queue.qsize(),
                "metrics": self._metrics.__dict__
            }
        except Exception as e:
            return {
                "platform": self.PLATFORM.value,
                "connected": False,
                "error": str(e)
            }
    
    async def shutdown(self) -> None:
        """Shutdown adapter gracefully."""
        self._running = False
        if self._bot:
            try:
                await self._bot.close()
            except Exception:
                pass
        if self._session:
            await self._session.close()
        logger.info("Telegram adapter shutdown complete")
