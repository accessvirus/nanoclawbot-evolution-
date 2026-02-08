"""
Feishu (Lark) Channel Adapter Plugin for RefactorBot V2

This plugin provides Feishu/Lark integration for multi-channel communication.
Supports chat, cards, and collaboration features.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import aiohttp
from urllib.parse import urlencode

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
class FeishuConfig(ChannelConfig):
    """Feishu-specific configuration."""
    app_id: str = ""
    app_secret: str = ""
    app_access_token: str = ""
    tenant_access_token: str = ""
    webhook_signature_key: str = ""
    base_url: str = "https://open.feishu.cn/open-apis"
    rate_limit_per_second: int = 60
    max_message_length: int = 5000
    default_receive_id_type: str = "open_id"


@dataclass
class FeishuUser(ChannelUser):
    """Feishu-specific user data."""
    feishu_id: str = ""
    open_id: str = ""
    union_id: str = ""
    tenant_id: str = ""
    is_admin: bool = False
    avatar_url: str = ""


@dataclass
class FeishuMessage(ChannelMessage):
    """Feishu-specific message data."""
    feishu_message_id: str = ""
    msg_type: str = ""
    open_id: str = ""
    tenant_key: str = ""
    root_id: Optional[str] = None
    parent_id: Optional[str] = None


class FeishuAdapter(BaseChannelAdapter):
    """
    Feishu (Lark) channel adapter for RefactorBot V2.
    
    Provides bidirectional communication with Feishu,
    supporting text, rich text, cards, and images.
    """
    
    PLATFORM = PlatformType.FEISHU
    CONFIG_CLASS = FeishuConfig
    MESSAGE_CLASS = FeishuMessage
    USER_CLASS = FeishuUser
    
    def __init__(self, config: FeishuConfig):
        super().__init__(config)
        self.config: FeishuConfig = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._running = False
        self._metrics: AdapterMetrics = AdapterMetrics()
        self._rate_limiter = asyncio.Semaphore(self.config.rate_limit_per_second)
        self._token_expires_at: Optional[datetime] = None
        
    async def initialize(self) -> bool:
        """Initialize Feishu adapter."""
        try:
            self._session = aiohttp.ClientSession(
                headers={"Content-Type": "application/json"}
            )
            
            # Get tenant access token
            success = await self._get_tenant_token()
            if not success:
                return False
            
            # Start message processor
            self._running = True
            asyncio.create_task(self._process_queue())
            
            logger.info("Feishu adapter initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Feishu adapter: {e}")
            return False
    
    async def _get_tenant_token(self) -> bool:
        """Get or refresh tenant access token."""
        try:
            # Check if existing token is still valid
            if self.config.tenant_access_token and self._token_expires_at:
                if datetime.utcnow() < self._token_expires_at:
                    return True
            
            async with self._session.post(
                f"{self.config.base_url}/auth/v3/tenant_access_token/internal",
                json={
                    "app_id": self.config.app_id,
                    "app_secret": self.config.app_secret
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("code") == 0:
                        self.config.tenant_access_token = data.get("tenant_access_token", "")
                        # Token typically expires in 2 hours
                        self._token_expires_at = datetime.utcnow() + \
                            datetime.timedelta(seconds=data.get("expire", 7200) - 60)
                        
                        # Update session headers
                        self._session.headers["Authorization"] = \
                            f"Bearer {self.config.tenant_access_token}"
                        return True
                    else:
                        logger.error(f"Tenant token error: {data}")
                        return False
                else:
                    logger.error(f"Token request failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error getting tenant token: {e}")
            return False
    
    async def _ensure_token(self):
        """Ensure token is valid before API call."""
        if not self.config.tenant_access_token or \
           (self._token_expires_at and datetime.utcnow() >= self._token_expires_at):
            await self._get_tenant_token()
    
    async def _process_queue(self):
        """Process outgoing message queue."""
        while self._running:
            try:
                item = await self._message_queue.get()
                if item is None:
                    break
                
                await self._send_queued(item)
                await asyncio.sleep(1 / self.config.rate_limit_per_second)
                
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await asyncio.sleep(1)
    
    async def _send_queued(self, item: Dict[str, Any]):
        """Send queued message."""
        try:
            async with self._rate_limiter:
                await self._ensure_token()
                await self._send_raw(item["receive_id"], item["msg_type"], item["content"])
        except Exception as e:
            logger.error(f"Error sending queued message: {e}")
            item["retry_count"] = item.get("retry_count", 0) + 1
            if item["retry_count"] < 3:
                await self._message_queue.put(item)
    
    async def _send_raw(
        self,
        receive_id: str,
        msg_type: str,
        content: Dict[str, Any]
    ) -> str:
        """Send raw message via API."""
        try:
            await self._ensure_token()
            
            payload = {
                "receive_id": receive_id,
                "receive_id_type": self.config.default_receive_id_type,
                "msg_type": msg_type,
                "content": json.dumps(content)
            }
            
            async with self._session.post(
                f"{self.config.base_url}/im/v1/messages",
                params={"receive_id_type": self.config.default_receive_id_type},
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("code") == 0:
                        message_id = data.get("data", {}).get("message_id", "")
                        self._messages_sent += 1
                        return message_id
                    else:
                        logger.error(f"Feishu API error: {data}")
                        self._metrics.errors += 1
                        raise Exception(f"API error: {data.get('msg')}")
                else:
                    logger.error(f"HTTP error: {response.status}")
                    raise Exception(f"HTTP error: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    async def handle_webhook(self, headers: Dict[str, str], body: bytes) -> Dict[str, Any]:
        """Handle incoming webhook from Feishu."""
        try:
            data = json.loads(body.decode("utf-8"))
            
            # Handle different event types
            event_type = data.get("type", "")
            
            if event_type == "url_verification":
                # Handle URL verification
                return {"challenge": data.get("challenge", "")}
            
            elif event_type == "event_callback":
                event = data.get("event", {})
                event_handler = event.get("type", "")
                
                if event_handler == "im":
                    await self._handle_im_event(event)
                    
            return {"code": 0, "msg": "success"}
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return {"code": -1, "msg": str(e)}
    
    async def _handle_im_event(self, event: Dict[str, Any]):
        """Handle IM (instant messaging) events."""
        try:
            event_type = event.get("event_type", "")
            
            if event_type == "message":
                await self._handle_message(event)
            elif event_type == "message.read":
                await self._handle_read(event)
                
        except Exception as e:
            logger.error(f"Error handling IM event: {e}")
    
    async def _handle_message(self, event: Dict[str, Any]):
        """Handle incoming message."""
        try:
            message = event.get("message", {})
            sender = event.get("sender", {})
            
            msg_type = message.get("msg_type", "text")
            content = json.loads(message.get("content", "{}"))
            
            # Create user object
            user = FeishuUser(
                id=sender.get("sender_id", {}).get("open_id", ""),
                username=sender.get("sender_id", {}).get("open_id", ""),
                display_name=sender.get("sender_id", {}).get("open_id", ""),
                feishu_id=sender.get("sender_id", {}).get("open_id", ""),
                open_id=sender.get("sender_id", {}).get("open_id", ""),
                union_id=sender.get("sender_id", {}).get("union_id", ""),
                tenant_key=sender.get("tenant_key", ""),
                is_admin=sender.get("sender_type", "") == "app"
            )
            
            # Parse content based on type
            text_content = self._parse_content(msg_type, content)
            
            # Create message object
            channel_msg = FeishuMessage(
                id=message.get("message_id", ""),
                platform=self.PLATFORM,
                type=self._map_message_type(msg_type),
                content=text_content,
                user=user,
                timestamp=datetime.fromisoformat(message.get("create_time", "").replace("+0000", "")),
                feishu_message_id=message.get("message_id", ""),
                msg_type=msg_type,
                open_id=user.open_id,
                tenant_key=user.tenant_key,
                root_id=message.get("root_id"),
                parent_id=message.get("parent_id")
            )
            
            await self._message_queue.put(channel_msg)
            self._metrics.messages_received += 1
            await self._emit_message(channel_msg)
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            self._metrics.errors += 1
    
    def _parse_content(self, msg_type: str, content: Dict[str, Any]) -> str:
        """Parse message content based on type."""
        if msg_type == "text":
            return content.get("text", "")
        elif msg_type == "image":
            return f"[Image: {content.get('image_key', '')}]"
        elif msg_type == "file":
            return f"[File: {content.get('file_key', '')}]"
        elif msg_type == "audio":
            return f"[Audio: {content.get('audio_key', '')}]"
        elif msg_type == "video":
            return f"[Video: {content.get('video_key', '')}]"
        elif msg_type == "rich_text":
            # Parse rich text
            elements = content.get("elements", [])
            text_parts = []
            for element in elements:
                if element.get("type") == "text":
                    text_parts.append(element.get("text", ""))
                elif element.get("type") == "url":
                    text_parts.append(element.get("text", element.get("url", "")))
            return "".join(text_parts)
        elif msg_type == "card":
            return content.get("text", "")
        else:
            return str(content)
    
    def _map_message_type(self, feishu_type: str) -> MessageType:
        """Map Feishu message type to our type."""
        mapping = {
            "text": MessageType.TEXT,
            "image": MessageType.IMAGE,
            "file": MessageType.FILE,
            "audio": MessageType.AUDIO,
            "video": MessageType.VIDEO,
            "rich_text": MessageType.TEXT,
            "card": MessageType.INTERACTIVE,
        }
        return mapping.get(feishu_type, MessageType.TEXT)
    
    async def _handle_read(self, event: Dict[str, Any]):
        """Handle message read event."""
        try:
            await self._emit_message(
                FeishuMessage(
                    id=event.get("message", {}).get("message_id", ""),
                    platform=self.PLATFORM,
                    type=MessageType.STATUS,
                    content="Message read"
                ),
                event_type="message_read"
            )
        except Exception as e:
            logger.error(f"Error handling read event: {e}")
    
    async def send_message(
        self,
        to: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Send message to Feishu user."""
        try:
            msg_type, msg_content = self._build_content(content, message_type, metadata)
            
            # Add to queue
            self._message_queue.put({
                "receive_id": to,
                "msg_type": msg_type,
                "content": msg_content
            })
            
            return f"queued_{secrets.token_hex(8)}"
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self._metrics.errors += 1
            raise
    
    def _build_content(
        self,
        content: str,
        message_type: MessageType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> tuple:
        """Build message content for Feishu."""
        if message_type == MessageType.TEXT:
            return "text", {"text": content}
        
        elif message_type == MessageType.IMAGE:
            return "image", {"image_key": metadata.get("image_key", "")}
        
        elif message_type == MessageType.FILE:
            return "file", {"file_key": metadata.get("file_key", "")}
        
        elif message_type == MessageType.CARD:
            # Build card message
            card = {
                "config": {
                    "wide_screen_mode": True,
                    "enable_forward": True
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "plain_text",
                            "content": content
                        }
                    }
                ]
            }
            
            # Add buttons if provided
            if metadata and "buttons" in metadata:
                buttons = []
                for btn in metadata["buttons"]:
                    buttons.append({
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": btn.get("text", "")},
                        "type": btn.get("type", "default"),
                        "action_id": btn.get("action_id", "")
                    })
                card["elements"].append({
                    "tag": "action",
                    "actions": buttons
                })
            
            return "card", card
        
        elif message_type == MessageType.RICH_TEXT:
            return "rich_text", {"elements": metadata.get("elements", [])}
        
        else:
            return "text", {"text": content}
    
    async def send_card(
        self,
        to: str,
        card_content: Dict[str, Any],
        receive_id_type: str = "open_id"
    ) -> str:
        """Send card message."""
        try:
            await self._ensure_token()
            
            payload = {
                "receive_id": to,
                "receive_id_type": receive_id_type,
                "msg_type": "card",
                "content": json.dumps(card_content)
            }
            
            async with self._session.post(
                f"{self.config.base_url}/im/v1/messages",
                params={"receive_id_type": receive_id_type},
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {}).get("message_id", "")
                raise Exception(f"Card send failed: {response.status}")
                
        except Exception as e:
            logger.error(f"Error sending card: {e}")
            raise
    
    async def upload_image(self, image_path: str) -> str:
        """Upload image and return image key."""
        try:
            await self._ensure_token()
            
            form = aiohttp.FormData()
            form.add_field(
                "image_type", "message",
                filename="image.jpg",
                content_type="image/jpeg"
            )
            with open(image_path, "rb") as f:
                form.add_field(
                    "image",
                    f.read(),
                    filename="image.jpg",
                    content_type="image/jpeg"
                )
            
            async with self._session.post(
                f"{self.config.base_url}/im/v1/images",
                params={"receive_id_type": self.config.default_receive_id_type},
                data=form
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {}).get("image_key", "")
                raise Exception(f"Upload failed: {response.status}")
                
        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            raise
    
    async def get_user(self, open_id: str) -> Optional[FeishuUser]:
        """Get user information."""
        try:
            await self._ensure_token()
            
            async with self._session.get(
                f"{self.config.base_url}/contact/v3/users/{open_id}"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    user_data = data.get("data", {})
                    return FeishuUser(
                        id=open_id,
                        username=user_data.get("name", ""),
                        display_name=user_data.get("name", ""),
                        feishu_id=open_id,
                        open_id=open_id,
                        union_id=user_data.get("union_id", ""),
                        is_admin=user_data.get("is_admin", False),
                        avatar_url=user_data.get("avatar", {}).get("avatar_72", "")
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None
    
    async def get_chat_members(self, chat_id: str) -> List[FeishuUser]:
        """Get members of a chat."""
        try:
            await self._ensure_token()
            
            members = []
            page_token = ""
            
            while True:
                async with self._session.get(
                    f"{self.config.base_url}/im/v1/chats/{chat_id}/members",
                    params={
                        "page_token": page_token,
                        "page_size": 100
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        items = data.get("data", {}).get("items", [])
                        for item in items:
                            members.append(FeishuUser(
                                id=item.get("open_id", ""),
                                open_id=item.get("open_id", ""),
                                union_id=item.get("union_id", "")
                            ))
                        
                        page_token = data.get("data", {}).get("page_token", "")
                        if not page_token or len(items) < 100:
                            break
                    else:
                        break
                        
            return members
            
        except Exception as e:
            logger.error(f"Error getting chat members: {e}")
            return []
    
    def get_metrics(self) -> AdapterMetrics:
        """Get adapter metrics."""
        return self._metrics
    
    async def health_check(self) -> Dict[str, Any]:
        """Check adapter health."""
        try:
            await self._ensure_token()
            return {
                "platform": self.PLATFORM.value,
                "connected": True,
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
        """Shutdown adapter."""
        self._running = False
        await self._message_queue.put(None)
        if self._session:
            await self._session.close()
        logger.info("Feishu adapter shutdown complete")
