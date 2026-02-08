"""
Plugin Management Dashboard Page for RefactorBot V2

Provides UI for managing channel adapter plugins.
"""

import streamlit as st
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from plugins.plugin_base import PlatformType
from plugins.discord.adapter import DiscordAdapter, DiscordConfig
from plugins.telegram.adapter import TelegramAdapter, TelegramConfig
from plugins.whatsapp.adapter import WhatsAppAdapter, WhatsAppConfig
from plugins.feishu.adapter import FeishuAdapter, FeishuConfig


def render_plugins_page():
    """Render the plugin management page."""
    st.title("🔌 Plugin Management")
    st.markdown("Manage channel adapter plugins for multi-channel communication.")
    
    # Initialize plugin manager in session state
    if "plugin_manager" not in st.session_state:
        st.session_state.plugin_manager = PluginManager()
    
    manager = st.session_state.plugin_manager
    
    # Tabs for different plugin types
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📱 Discord",
        "✈️ Telegram",
        "💬 WhatsApp",
        "🏢 Feishu",
        "📊 Overview"
    ])
    
    with tab1:
        render_discord_plugin(manager)
    
    with tab2:
        render_telegram_plugin(manager)
    
    with tab3:
        render_whatsapp_plugin(manager)
    
    with tab4:
        render_feishu_plugin(manager)
    
    with tab5:
        render_plugin_overview(manager)


def render_discord_plugin(manager):
    """Render Discord plugin configuration."""
    st.subheader("Discord Adapter")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Configuration form
        with st.form("discord_config"):
            bot_token = st.text_input("Bot Token", type="password")
            guild_id = st.text_input("Guild ID")
            channel_ids = st.text_area("Channel IDs (one per line)")
            command_prefix = st.text_input("Command Prefix", value="!")
            
            submitted = st.form_submit_button("Save Configuration")
            
            if submitted:
                config = DiscordConfig(
                    bot_token=bot_token,
                    guild_id=guild_id,
                    channel_ids=channel_ids.split("\n"),
                    command_prefix=command_prefix
                )
                manager.configure_plugin(PlatformType.DISCORD, config)
                st.success("Configuration saved!")
    
    with col2:
        # Status and controls
        status = manager.get_plugin_status(PlatformType.DISCORD)
        
        if status["configured"]:
            st.info("✅ Plugin Configured")
            
            if status["running"]:
                st.success("🟢 Connected")
                st.metric("Messages Received", status.get("metrics", {}).get("messages_received", 0))
                st.metric("Messages Sent", status.get("metrics", {}).get("messages_sent", 0))
                
                if st.button("Disconnect", key="discord_disconnect"):
                    manager.stop_plugin(PlatformType.DISCORD)
                    st.rerun()
            else:
                st.warning("🔴 Disconnected")
                
                if st.button("Connect", key="discord_connect"):
                    success = manager.start_plugin(PlatformType.DISCORD)
                    if success:
                        st.success("Connected successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to connect")
        else:
            st.error("⚙️ Not Configured")
    
    # Guild selector
    if status.get("running"):
        st.divider()
        st.subheader("Quick Actions")
        
        col_a, col_b = st.columns(2)
        with col_a:
            target_channel = st.selectbox("Target Channel", status.get("channels", []))
            test_message = st.text_input("Test Message", value="Hello from RefactorBot!")
            
            if st.button("Send Test Message", key="discord_test"):
                manager.send_test_message(PlatformType.DISCORD, target_channel, test_message)
        
        with col_b:
            st.write("**Activity Log**")
            activity = status.get("activity", [])
            if activity:
                for item in activity[-5:]:
                    st.text(f"• {item}")
            else:
                st.text("No recent activity")


def render_telegram_plugin(manager):
    """Render Telegram plugin configuration."""
    st.subheader("Telegram Adapter")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("telegram_config"):
            bot_token = st.text_input("Bot Token", type="password")
            chat_ids = st.text_area("Chat IDs (one per line)")
            parse_mode = st.selectbox("Parse Mode", ["HTML", "Markdown"])
            webhook_url = st.text_input("Webhook URL (optional)")
            
            submitted = st.form_submit_button("Save Configuration")
            
            if submitted:
                config = TelegramConfig(
                    bot_token=bot_token,
                    chat_ids=chat_ids.split("\n"),
                    parse_mode=parse_mode,
                    webhook_url=webhook_url if webhook_url else None
                )
                manager.configure_plugin(PlatformType.TELEGRAM, config)
                st.success("Configuration saved!")
    
    with col2:
        status = manager.get_plugin_status(PlatformType.TELEGRAM)
        
        if status["configured"]:
            st.info("✅ Plugin Configured")
            
            if status["running"]:
                st.success("🟢 Connected")
                st.metric("Messages Received", status.get("metrics", {}).get("messages_received", 0))
                
                if st.button("Disconnect", key="telegram_disconnect"):
                    manager.stop_plugin(PlatformType.TELEGRAM)
                    st.rerun()
            else:
                st.warning("🔴 Disconnected")
                
                if st.button("Connect", key="telegram_connect"):
                    success = manager.start_plugin(PlatformType.TELEGRAM)
                    if success:
                        st.success("Connected successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to connect")
        else:
            st.error("⚙️ Not Configured")
    
    # Quick actions
    if status.get("running"):
        st.divider()
        st.subheader("Quick Actions")
        
        target_chat = st.selectbox("Target Chat", status.get("chats", []))
        test_msg = st.text_input("Test Message", "Hello from RefactorBot!")
        
        if st.button("Send Test Message", key="telegram_test"):
            manager.send_test_message(PlatformType.TELEGRAM, target_chat, test_msg)


def render_whatsapp_plugin(manager):
    """Render WhatsApp plugin configuration."""
    st.subheader("WhatsApp Business Adapter")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("whatsapp_config"):
            phone_number_id = st.text_input("Phone Number ID")
            business_account_id = st.text_input("Business Account ID")
            access_token = st.text_input("Access Token", type="password")
            app_secret = st.text_input("App Secret", type="password")
            
            submitted = st.form_submit_button("Save Configuration")
            
            if submitted:
                config = WhatsAppConfig(
                    phone_number_id=phone_number_id,
                    business_account_id=business_account_id,
                    access_token=access_token,
                    app_secret=app_secret
                )
                manager.configure_plugin(PlatformType.WHATSAPP, config)
                st.success("Configuration saved!")
    
    with col2:
        status = manager.get_plugin_status(PlatformType.WHATSAPP)
        
        if status["configured"]:
            st.info("✅ Plugin Configured")
            
            if status["running"]:
                st.success("🟢 Connected")
                st.metric("Messages Received", status.get("metrics", {}).get("messages_received", 0))
                st.metric("Messages Sent", status.get("metrics", {}).get("messages_sent", 0))
                
                if st.button("Disconnect", key="whatsapp_disconnect"):
                    manager.stop_plugin(PlatformType.WHATSAPP)
                    st.rerun()
            else:
                st.warning("🔴 Disconnected")
                
                if st.button("Connect", key="whatsapp_connect"):
                    success = manager.start_plugin(PlatformType.WHATSAPP)
                    if success:
                        st.success("Connected successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to connect")
        else:
            st.error("⚙️ Not Configured")
    
    # Webhook configuration
    if status["configured"]:
        st.divider()
        st.subheader("Webhook Configuration")
        st.code(f"/webhook/whatsapp", language="text")
        st.text("Use this endpoint for webhook events from WhatsApp Cloud API")


def render_feishu_plugin(manager):
    """Render Feishu plugin configuration."""
    st.subheader("Feishu (Lark) Adapter")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("feishu_config"):
            app_id = st.text_input("App ID")
            app_secret = st.text_input("App Secret", type="password")
            webhook_key = st.text_input("Webhook Signature Key", type="password")
            
            submitted = st.form_submit_button("Save Configuration")
            
            if submitted:
                config = FeishuConfig(
                    app_id=app_id,
                    app_secret=app_secret,
                    webhook_signature_key=webhook_key
                )
                manager.configure_plugin(PlatformType.FEISHU, config)
                st.success("Configuration saved!")
    
    with col2:
        status = manager.get_plugin_status(PlatformType.FEISHU)
        
        if status["configured"]:
            st.info("✅ Plugin Configured")
            
            if status["running"]:
                st.success("🟢 Connected")
                st.metric("Messages Received", status.get("metrics", {}).get("messages_received", 0))
                
                if st.button("Disconnect", key="feishu_disconnect"):
                    manager.stop_plugin(PlatformType.FEISHU)
                    st.rerun()
            else:
                st.warning("🔴 Disconnected")
                
                if st.button("Connect", key="feishu_connect"):
                    success = manager.start_plugin(PlatformType.FEISHU)
                    if success:
                        st.success("Connected successfully!")
                        st.rerun()
                    else:
                        st.error("Failed to connect")
        else:
            st.error("⚙️ Not Configured")
    
    # Webhook endpoint
    if status["configured"]:
        st.divider()
        st.subheader("Webhook Configuration")
        st.code(f"/webhook/feishu", language="text")
        st.text("Use this endpoint for webhook events from Feishu")


def render_plugin_overview(manager):
    """Render overall plugin overview."""
    st.subheader("Plugin Overview")
    
    # Get all plugin statuses
    platforms = [
        PlatformType.DISCORD,
        PlatformType.TELEGRAM,
        PlatformType.WHATSAPP,
        PlatformType.FEISHU
    ]
    
    # Summary metrics
    total_configured = 0
    total_running = 0
    total_messages = 0
    
    status_data = []
    for platform in platforms:
        status = manager.get_plugin_status(platform)
        status_data.append({
            "platform": platform.value,
            "configured": status["configured"],
            "running": status.get("running", False),
            "messages": status.get("metrics", {}).get("messages_received", 0) + \
                      status.get("metrics", {}).get("messages_sent", 0)
        })
        if status["configured"]:
            total_configured += 1
        if status.get("running"):
            total_running += 1
        total_messages += status.get("metrics", {}).get("messages_received", 0)
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Plugins", len(platforms))
    col2.metric("Configured", total_configured)
    col3.metric("Running", total_running)
    col4.metric("Total Messages", total_messages)
    
    # Platform status table
    st.subheader("Platform Status")
    
    for data in status_data:
        with st.container():
            col_icon, col_name, col_status, col_messages = st.columns([1, 2, 2, 2])
            
            with col_icon:
                icons = {
                    "discord": "💬",
                    "telegram": "✈️",
                    "whatsapp": "💬",
                    "feishu": "🏢"
                }
                st.write(icons.get(data["platform"], "📱"))
            
            with col_name:
                st.write(f"**{data['platform'].title()}**")
            
            with col_status:
                if data["running"]:
                    st.write("🟢 Running")
                elif data["configured"]:
                    st.write("🟡 Configured")
                else:
                    st.write("⚪ Not Configured")
            
            with col_messages:
                st.write(f"📨 {data['messages']} messages")
            
            st.divider()
    
    # Bulk actions
    st.subheader("Bulk Actions")
    
    col_start, col_stop, col_reload = st.columns(3)
    
    with col_start:
        if st.button("Start All Configured"):
            for platform in platforms:
                if manager.get_plugin_status(platform)["configured"]:
                    manager.start_plugin(platform)
            st.rerun()
    
    with col_stop:
        if st.button("Stop All"):
            for platform in platforms:
                manager.stop_plugin(platform)
            st.rerun()
    
    with col_reload:
        if st.button("Reload All"):
            st.rerun()
    
    # Plugin health
    st.subheader("System Health")
    
    health_data = []
    for platform in platforms:
        health = manager.get_plugin_health(PlatformType.DISCORD)
        if health:
            health_data.append(health)
    
    if health_data:
        # Create a simple health visualization
        for health in health_data:
            health_status = "Healthy" if health.get("connected", False) else "Disconnected"
            st.write(f"**{health.get('platform', 'Unknown')}**: {health_status}")
    else:
        st.info("No health data available")


class PluginManager:
    """Manages all channel adapter plugins."""
    
    def __init__(self):
        self._plugins: Dict[PlatformType, Any] = {}
        self._configs: Dict[PlatformType, Any] = {}
        self._initialized = False
    
    def configure_plugin(self, platform: PlatformType, config):
        """Configure a plugin."""
        self._configs[platform] = config
        self._plugins[platform] = self._create_adapter(platform, config)
    
    def _create_adapter(self, platform: PlatformType, config):
        """Create adapter instance for platform."""
        adapters = {
            PlatformType.DISCORD: DiscordAdapter,
            PlatformType.TELEGRAM: TelegramAdapter,
            PlatformType.WHATSAPP: WhatsAppAdapter,
            PlatformType.FEISHU: FeishuAdapter,
        }
        return adapters.get(platform)(config)
    
    def start_plugin(self, platform: PlatformType) -> bool:
        """Start a plugin."""
        adapter = self._plugins.get(platform)
        if adapter:
            return asyncio.run(adapter.initialize())
        return False
    
    def stop_plugin(self, platform: PlatformType):
        """Stop a plugin."""
        adapter = self._plugins.get(platform)
        if adapter:
            asyncio.run(adapter.shutdown())
    
    def get_plugin_status(self, platform: PlatformType) -> Dict[str, Any]:
        """Get plugin status."""
        adapter = self._plugins.get(platform)
        config = self._configs.get(platform)
        
        if not config:
            return {"configured": False}
        
        if adapter:
            metrics = adapter.get_metrics()
            return {
                "configured": True,
                "running": True,
                "metrics": metrics.__dict__
            }
        
        return {"configured": True, "running": False}
    
    def get_plugin_health(self, platform: PlatformType) -> Optional[Dict[str, Any]]:
        """Get plugin health."""
        adapter = self._plugins.get(platform)
        if adapter:
            return asyncio.run(adapter.health_check())
        return None
    
    def send_test_message(self, platform: PlatformType, target: str, message: str):
        """Send test message via platform."""
        adapter = self._plugins.get(platform)
        if adapter and hasattr(adapter, "send_message"):
            from plugins.plugin_base import MessageType
            asyncio.run(adapter.send_message(target, message, MessageType.TEXT))
            st.success("Test message sent!")
        else:
            st.error("Cannot send test message - plugin not running")


if __name__ == "__main__":
    render_plugins_page()
