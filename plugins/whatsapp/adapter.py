"""
WhatsApp Channel Adapter Plugin for RefactorBot V2

This plugin provides WhatsApp Business API integration for multi-channel communication.
Uses WhatsApp Cloud API for messaging.
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
from base64 import b64decode

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
class WhatsAppConfig(ChannelConfig):
    """WhatsApp-specific configuration."""
    phone_number_id: str = ""
    business_account_id: str = ""
    access_token: str = ""
    app_secret: str = ""
    webhook_verify_token: str = ""
    api_version: str = "v18.0"
    base_url: str = "https://graph.facebook.com"
    rate_limit_per_second: int = 30
    default_country_code: str = "1"
    max_message_length: int = 4096


@dataclass
class WhatsAppUser(ChannelUser):
    """WhatsApp-specific user data."""
    whatsapp_id: str = ""
    is_business: bool = False
    verified_name: str = ""
    platform: str = "whatsapp"


@dataclass
class WhatsAppMessage(ChannelMessage):
    """WhatsApp-specific message data."""
    whatsapp_message_id: str = ""
    waid: str = ""
    message_type: str = ""
    timestamp: str = ""
    reply_to: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


class WhatsAppAdapter(BaseChannelAdapter):
    """
    WhatsApp Business channel adapter for RefactorBot V2.
    
    Provides bidirectional communication via WhatsApp Cloud API,
    supporting text, images, documents, and interactive messages.
    """
    
    PLATFORM = PlatformType.WHATSAPP
    CONFIG_CLASS = WhatsAppConfig
    MESSAGE_CLASS = WhatsAppMessage
    USER_CLASS = WhatsAppUser
    
    def __init__(self, config: WhatsAppConfig):
        super().__init__(config)
        self.config: WhatsAppConfig = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._running = False
        self._metrics: AdapterMetrics = AdapterMetrics()
        self._rate_limiter = asyncio.Semaphore(self.config.rate_limit_per_second)
        self._token_cache: Dict[str, datetime] = {}
        
    def _get_api_url(self, endpoint: str) -> str:
        """Get full API URL."""
        return f"{self.config.base_url}/{self.config.api_version}/{endpoint}"
    
    async def initialize(self) -> bool:
        """Initialize WhatsApp adapter."""
        try:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.config.access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            # Verify credentials
            success = await self._verify_credentials()
            if not success:
                return False
            
            # Start webhook handler
            self._running = True
            asyncio.create_task(self._process_queue())
            
            logger.info(f"WhatsApp adapter initialized for phone {self.config.phone_number_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize WhatsApp adapter: {e}")
            return False
    
    async def _verify_credentials(self) -> bool:
        """Verify WhatsApp credentials."""
        try:
            async with self._session.get(
                self._get_api_url(f"{self.config.phone_number_id}/whatsapp_business_profile")
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"WhatsApp Business Profile: {data}")
                    return True
                else:
                    logger.error(f"Credential verification failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error verifying credentials: {e}")
            return False
    
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
                await self._send_raw(item["to"], item["payload"])
        except Exception as e:
            logger.error(f"Error sending queued message: {e}")
            item["retry_count"] = item.get("retry_count", 0) + 1
            if item["retry_count"] < 3:
                await self._message_queue.put(item)
    
    async def _send_raw(self, to: str, payload: Dict[str, Any]) -> str:
        """Send raw message via API."""
        try:
            async with self._session.post(
                self._get_api_url(f"{self.config.phone_number_id}/messages"),
                json=payload
            ) as response:
                if response.status in [200, 201]:
                    data = await response.json()
                    message_id = data.get("messages", [{}])[0].get("id", "")
                    self._metrics.messages_sent += 1
                    return message_id
                else:
                    error = await response.text()
                    logger.error(f"WhatsApp API error: {error}")
                    self._metrics.errors += 1
                    raise Exception(f"API error: {response.status}")
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    async def handle_webhook(self, headers: Dict[str, str], body: bytes) -> Dict[str, Any]:
        """Handle incoming webhook from WhatsApp."""
        # Verify signature
        if not self._verify_signature(headers, body):
            logger.warning("Invalid webhook signature")
            return {"status": "error", "message": "Invalid signature"}
        
        try:
            data = json.loads(body.decode("utf-8"))
            
            # Handle different webhook entries
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    
                    if "messages" in value:
                        await self._handle_messages(value)
                    elif "statuses" in value:
                        await self._handle_statuses(value)
                        
            return {"status": "success"}
            
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            return {"status": "error", "message": str(e)}
    
    def _verify_signature(self, headers: Dict[str, str], body: bytes) -> bool:
        """Verify X-Hub-Signature-256."""
        signature = headers.get("x-hub-signature-256", "")
        if not signature:
            return False
            
        expected = hmac.new(
            self.config.app_secret.encode("utf-8"),
            body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected}", signature)
    
    async def _handle_messages(self, value: Dict[str, Any]):
        """Handle incoming messages."""
        try:
            contacts = value.get("contacts", [])
            messages = value.get("messages", [])
            
            for message in messages:
                waid = message.get("from", "")
                message_type = message.get("type", "text")
                
                # Get user info
                contact = next((c for c in contacts if c.get("waid") == waid), {})
                profile = contact.get("profile", {})
                
                user = WhatsAppUser(
                    id=waid,
                    username=profile.get("name", ""),
                    display_name=profile.get("name", ""),
                    whatsapp_id=waid,
                    verified_name=profile.get("name", ""),
                    is_business=contact.get("waid", "").startswith("business_")
                )
                
                # Parse message content
                content = ""
                extra_data = {}
                
                if message_type == "text":
                    content = message.get("text", {}).get("body", "")
                elif message_type == "image":
                    image_data = message.get("image", {})
                    content = image_data.get("caption", "")
                    extra_data["image"] = {
                        "id": image_data.get("id", ""),
                        "mime_type": image_data.get("mime_type", ""),
                        "sha256": image_data.get("sha256", "")
                    }
                elif message_type == "document":
                    doc_data = message.get("document", {})
                    content = doc_data.get("caption", "") or doc_data.get("filename", "")
                    extra_data["document"] = {
                        "id": doc_data.get("id", ""),
                        "mime_type": doc_data.get("mime_type", ""),
                        "filename": doc_data.get("filename", "")
                    }
                elif message_type == "button":
                    content = message.get("button", {}).get("text", "")
                elif message_type == "interactive":
                    interactive = message.get("interactive", {})
                    content = interactive.get("button_reply", {}).get("title", "") or \
                              interactive.get("list_reply", {}).get("title", "")
                    extra_data["interactive"] = interactive
                elif message_type == "location":
                    loc = message.get("location", {})
                    content = f"Location: {loc.get('latitude')}, {loc.get('longitude')}"
                    extra_data["location"] = loc
                elif message_type == "contacts":
                    contacts_data = message.get("contacts", [])
                    content = f"Contact: {len(contacts_data)} contact(s)"
                    extra_data["contacts"] = contacts_data
                
                # Create message object
                channel_msg = WhatsAppMessage(
                    id=message.get("id", ""),
                    platform=self.PLATFORM,
                    type=self._map_message_type(message_type),
                    content=content,
                    user=user,
                    timestamp=datetime.fromisoformat(message.get("timestamp", "")),
                    whatsapp_message_id=message.get("id", ""),
                    waid=waid,
                    message_type=message_type,
                    timestamp=message.get("timestamp", ""),
                    reply_to=message.get("context", {}).get("id"),
                    context=extra_data
                )
                
                await self._message_queue.put(channel_msg)
                self._metrics.messages_received += 1
                await self._emit_message(channel_msg)
                
        except Exception as e:
            logger.error(f"Error handling messages: {e}")
            self._metrics.errors += 1
    
    def _map_message_type(self, wa_type: str) -> MessageType:
        """Map WhatsApp message type to our type."""
        mapping = {
            "text": MessageType.TEXT,
            "image": MessageType.IMAGE,
            "document": MessageType.FILE,
            "audio": MessageType.AUDIO,
            "video": MessageType.VIDEO,
            "sticker": MessageType.STICKER,
            "location": MessageType.LOCATION,
            "contact": MessageType.CONTACT,
            "button": MessageType.INTERACTIVE,
            "interactive": MessageType.INTERACTIVE,
        }
        return mapping.get(wa_type, MessageType.TEXT)
    
    async def _handle_statuses(self, value: Dict[str, Any]):
        """Handle message status updates."""
        try:
            for status in value.get("statuses", []):
                logger.info(f"Message {status.get('id')} status: {status.get('status')}")
                await self._emit_message(
                    WhatsAppMessage(
                        id=status.get("id", ""),
                        platform=self.PLATFORM,
                        type=MessageType.STATUS,
                        content=f"Status: {status.get('status')}",
                        timestamp=status.get("timestamp", "")
                    ),
                    event_type="message_status"
                )
        except Exception as e:
            logger.error(f"Error handling statuses: {e}")
    
    async def send_message(
        self,
        to: str,
        content: str,
        message_type: MessageType = MessageType.TEXT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Send message to WhatsApp user."""
        try:
            # Format phone number
            if not to.startswith("+"):
                to = f"+{to}"
            
            # Build payload
            payload = self._build_payload(content, message_type, metadata)
            
            # Add to queue for rate limiting
            self._message_queue.put({"to": to, "payload": payload})
            
            # Return placeholder ID (actual ID will be from webhook status)
            return f"queued_{secrets.token_hex(8)}"
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self._metrics.errors += 1
            raise
    
    def _build_payload(
        self,
        content: str,
        message_type: MessageType,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build message payload."""
        messaging_product = "whatsapp"
        
        if message_type == MessageType.TEXT:
            return {
                "messaging_product": messaging_product,
                "to": None,  # Set at send time
                "type": "text",
                "text": {"preview_url": False, "body": content}
            }
        
        elif message_type == MessageType.IMAGE:
            return {
                "messaging_product": messaging_product,
                "to": None,
                "type": "image",
                "image": {
                    "link": metadata.get("image_url", ""),
                    "caption": content
                } if metadata and metadata.get("image_url") else {
                    "id": metadata.get("image_id", ""),
                    "caption": content
                }
            }
        
        elif message_type == MessageType.DOCUMENT:
            return {
                "messaging_product": messaging_product,
                "to": None,
                "type": "document",
                "document": {
                    "link": metadata.get("document_url", ""),
                    "caption": content,
                    "filename": metadata.get("filename", "document.pdf")
                } if metadata and metadata.get("document_url") else {
                    "id": metadata.get("document_id", ""),
                    "caption": content
                }
            }
        
        elif message_type == MessageType.INTERACTIVE:
            interactive_type = metadata.get("interactive_type", "button")
            if interactive_type == "list":
                return {
                    "messaging_product": messaging_product,
                    "to": None,
                    "type": "interactive",
                    "interactive": {
                        "type": "list",
                        "body": {"text": content},
                        "action": {
                            "button": metadata.get("button_text", "Select"),
                            "sections": metadata.get("sections", [])
                        }
                    }
                }
            else:
                buttons = metadata.get("buttons", [])
                return {
                    "messaging_product": messaging_product,
                    "to": None,
                    "type": "interactive",
                    "interactive": {
                        "type": "button",
                        "body": {"text": content},
                        "action": {
                            "buttons": [
                                {
                                    "type": "reply",
                                    "reply": {"id": b.get("id", ""), "title": b.get("title", "")[:20]}
                                }
                                for b in buttons
                            ]
                        }
                    }
                }
        
        elif message_type == MessageType.LOCATION:
            return {
                "messaging_product": messaging_product,
                "to": None,
                "type": "location",
                "location": {
                    "latitude": metadata.get("latitude", 0),
                    "longitude": metadata.get("longitude", 0),
                    "name": metadata.get("name", ""),
                    "address": metadata.get("address", "")
                }
            }
        
        else:
            # Default to text
            return {
                "messaging_product": messaging_product,
                "to": None,
                "type": "text",
                "text": {"preview_url": False, "body": content}
            }
    
    async def send_template(
        self,
        to: str,
        template_name: str,
        language: str = "en",
        components: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Send template message."""
        try:
            if not to.startswith("+"):
                to = f"+{to}"
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": language},
                    "components": components or []
                }
            }
            
            return await self._send_raw(to, payload)
            
        except Exception as e:
            logger.error(f"Error sending template: {e}")
            raise
    
    async def mark_message_read(self, message_id: str) -> bool:
        """Mark message as read."""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            async with self._session.post(
                self._get_api_url(f"{self.config.phone_number_id}/messages"),
                json=payload
            ) as response:
                return response.status == 200
                
        except Exception as e:
            logger.error(f"Error marking message read: {e}")
            return False
    
    async def get_message(self, message_id: str) -> Optional[WhatsAppMessage]:
        """Get specific message."""
        try:
            async with self._session.get(
                self._get_api_url(message_id)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    # Parse and return message
                    return WhatsAppMessage(
                        id=data.get("id", ""),
                        platform=self.PLATFORM,
                        content=data.get("text", {}).get("body", ""),
                        whatsapp_message_id=data.get("id", ""),
                        message_type=data.get("type", "text")
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting message: {e}")
            return None
    
    async def get_user(self, waid: str) -> Optional[WhatsAppUser]:
        """Get user information."""
        try:
            async with self._session.get(
                self._get_api_url(f"{waid}?fields=name,profile_picture")
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return WhatsAppUser(
                        id=waid,
                        username=data.get("name", ""),
                        display_name=data.get("name", ""),
                        whatsapp_id=waid
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
        try:
            async with self._session.get(
                self._get_api_url(f"{self.config.phone_number_id}/whatsapp_business_profile")
            ) as response:
                return {
                    "platform": self.PLATFORM.value,
                    "connected": response.status == 200,
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
        await self._message_queue.put(None)  # Signal queue to stop
        if self._session:
            await self._session.close()
        logger.info("WhatsApp adapter shutdown complete")
