"""
Master Dashboard - Main entry point for RefactorBot.

Streamlit-based unified dashboard for all slices.
"""
import streamlit as st
import pandas as pd
import json
import asyncio
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="RefactorBot - Master Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Data directory
DATA_DIR = Path("data")


def get_slice_states() -> dict:
    """Get all slice states from dashboard connector"""
    state_file = DATA_DIR / "dashboard_state.json"
    
    if state_file.exists():
        with open(state_file, "r") as f:
            data = json.load(f)
            return data.get("slices", {})
    return {}


def get_overview() -> dict:
    """Get dashboard overview"""
    states = get_slice_states()
    
    healthy = sum(1 for s in states.values() if s.get("health") == "healthy")
    degraded = sum(1 for s in states.values() if s.get("health") == "degraded")
    unhealthy = sum(1 for s in states.values() if s.get("health") == "unhealthy")
    unknown = len(states) - healthy - degraded - unhealthy
    
    return {
        "total": len(states),
        "healthy": healthy,
        "degraded": degraded,
        "unhealthy": unhealthy,
        "unknown": unknown
    }


def render_sidebar():
    """Render sidebar navigation"""
    with st.sidebar:
        st.title("🤖 RefactorBot")
        st.caption("Self-Aware AI Agent Framework")
        
        st.markdown("---")
        
        # Overview
        overview = get_overview()
        
        st.markdown("### 📊 Overview")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Slices", overview["total"])
        with col2:
            st.metric("Healthy", overview["healthy"])
        
        st.markdown("---")
        
        # Navigation
        st.markdown("### 🧭 Navigation")
        page = st.radio(
            "Go to",
            ["Overview", "Control Panel", "Analytics", "Logs", "Settings", "🧠 Master Swarm Chat"]
        )
        
        st.markdown("---")
        
        # Slice quick links
        st.markdown("### ⚡ Quick Access")
        slices = [
            ("Agent Core", "slice_agent_core"),
            ("Tools", "slice_tools"),
            ("Memory", "slice_memory"),
            ("Communication", "slice_communication"),
            ("Session", "slice_session"),
            ("Providers", "slice_providers"),
            ("Skills", "slice_skills"),
            ("Event Bus", "slice_event_bus"),
        ]
        
        for name, slice_id in slices:
            state = get_slice_states().get(slice_id, {})
            status_emoji = {
                "healthy": "🟢",
                "degraded": "🟡",
                "unhealthy": "🔴",
            }.get(state.get("health", "unknown"), "⚪")
            
            if st.button(f"{status_emoji} {name}", use_container_width=True):
                st.session_state.selected_slice = slice_id
                st.session_state.page = "Slice Detail"
        
        st.markdown("---")
        
        # Refresh
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
        
        st.markdown("---")
        st.caption("RefactorBot v2.0.0")
    
    return page


def render_overview_page():
    """Render the overview page"""
    st.title("📊 System Overview")
    st.markdown("---")
    
    overview = get_overview()
    
    # Status metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Slices",
            overview["total"],
            delta="Active"
        )
    
    with col2:
        st.metric(
            "Healthy",
            overview["healthy"],
            delta_color="normal"
        )
    
    with col3:
        st.metric(
            "Degraded",
            overview["degraded"],
            delta_color="inverse" if overview["degraded"] > 0 else "normal"
        )
    
    with col4:
        st.metric(
            "Unhealthy",
            overview["unhealthy"],
            delta_color="inverse"
        )
    
    st.markdown("---")
    
    # Slice status grid
    st.subheader("🔌 Slice Status")
    
    states = get_slice_states()
    slices = [
        ("Agent Core", "slice_agent_core", "🤖"),
        ("Tools", "slice_tools", "🛠️"),
        ("Memory", "slice_memory", "🧠"),
        ("Communication", "slice_communication", "💬"),
        ("Session", "slice_session", "📁"),
        ("Providers", "slice_providers", "🔌"),
        ("Skills", "slice_skills", "📚"),
        ("Event Bus", "slice_event_bus", "🚌"),
    ]
    
    cols = st.columns(4)
    
    for i, (name, slice_id, emoji) in enumerate(slices):
        state = states.get(slice_id, {})
        status = state.get("status", "unknown")
        health = state.get("health", "unknown")
        
        with cols[i % 4]:
            status_color = {
                "healthy": "🟢",
                "degraded": "🟡",
                "unhealthy": "🔴",
                "unknown": "⚪",
                "running": "🟢",
                "ready": "🟢",
                "stopped": "⚪",
            }.get(health, "⚪")
            
            st.markdown(f"""
            <div style="
                padding: 15px;
                border-radius: 10px;
                background-color: #1e1e1e;
                margin: 5px;
            ">
                <h3 style="margin: 0;">{status_color} {name}</h3>
                <p style="margin: 5px 0 0 0; color: #888;">
                    Status: {status}<br>
                    Health: {health}
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Resource overview
    st.subheader("💻 Resource Usage")
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.info("Resource monitoring will be added when slices report metrics.")
    
    with col_right:
        st.info("Cost tracking will be added when OpenRouter integration is complete.")


def render_control_panel_page():
    """Render the control panel page"""
    st.title("🎛️ Control Panel")
    st.markdown("---")
    
    slices = [
        ("Agent Core", "slice_agent_core", "🤖"),
        ("Tools", "slice_tools", "🛠️"),
        ("Memory", "slice_memory", "🧠"),
        ("Communication", "slice_communication", "💬"),
        ("Session", "slice_session", "📁"),
        ("Providers", "slice_providers", "🔌"),
        ("Skills", "slice_skills", "📚"),
        ("Event Bus", "slice_event_bus", "🚌"),
    ]
    
    states = get_slice_states()
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ Start All Slices"):
            st.success("Starting all slices... (Demo)")
    
    with col2:
        if st.button("⏹️ Stop All Slices"):
            st.warning("Stopping all slices... (Demo)")
    
    with col3:
        if st.button("🔄 Restart All Slices"):
            st.info("Restarting all slices... (Demo)")
    
    st.markdown("---")
    
    # Individual slice controls
    st.subheader("🔌 Individual Slice Controls")
    
    for name, slice_id, emoji in slices:
        state = states.get(slice_id, {})
        status = state.get("status", "unknown")
        
        with st.expander(f"{emoji} {name} ({status})"):
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                if st.button(f"Start {name}", key=f"start_{slice_id}"):
                    st.success(f"Starting {name}... (Demo)")
            
            with col_b:
                if st.button(f"Stop {name}", key=f"stop_{slice_id}"):
                    st.warning(f"Stopping {name}... (Demo)")
            
            with col_c:
                if st.button(f"Restart {name}", key=f"restart_{slice_id}"):
                    st.info(f"Restarting {name}... (Demo)")
            
            st.markdown("**Metrics:**")
            st.json(state.get("metrics", {}))


def render_analytics_page():
    """Render the analytics page"""
    st.title("📈 System Analytics")
    st.markdown("---")
    
    st.info("Cross-slice analytics will be available when slices report metrics.")
    
    # Placeholder for aggregated analytics
    st.markdown("### 📊 Available Analytics")
    
    analytics_tabs = st.tabs([
        "Agent Core",
        "Tools",
        "Memory",
        "Communication",
        "Session",
        "Providers",
        "Skills",
        "Event Bus"
    ])
    
    for i, (name, slice_id, emoji) in enumerate([
        ("Agent Core", "slice_agent_core", "🤖"),
        ("Tools", "slice_tools", "🛠️"),
        ("Memory", "slice_memory", "🧠"),
        ("Communication", "slice_communication", "💬"),
        ("Session", "slice_session", "📁"),
        ("Providers", "slice_providers", "🔌"),
        ("Skills", "slice_skills", "📚"),
        ("Event Bus", "slice_event_bus", "🚌"),
    ]):
        with analytics_tabs[i]:
            st.markdown(f"## {emoji} {name}")
            st.info(f"View detailed {name} analytics in the slice-specific dashboard.")
            
            if st.button(f"Open {name} Analytics", key=f"analytics_{slice_id}"):
                st.session_state.page = f"Slice {name} Analytics"


def render_logs_page():
    """Render the logs page"""
    st.title("📋 System Logs")
    st.markdown("---")
    
    log_file = DATA_DIR / "dashboard_events.jsonl"
    
    if log_file.exists():
        with open(log_file, "r") as f:
            lines = f.readlines()[-100:]  # Last 100 lines
            
        events = []
        for line in lines:
            if line.strip():
                try:
                    events.append(json.loads(line))
                except:
                    pass
        
        if events:
            df = pd.DataFrame(events)
            
            # Filters
            col1, col2 = st.columns(2)
            
            with col1:
                event_types = ["All"] + list(df["event_type"].unique())
                selected_type = st.selectbox("Event Type", event_types)
            
            with col2:
                slices = ["All"] + list(df["slice_id"].unique())
                selected_slice = st.selectbox("Slice", slices)
            
            # Filtered events
            filtered = df.copy()
            if selected_type != "All":
                filtered = filtered[filtered["event_type"] == selected_type]
            if selected_slice != "All":
                filtered = filtered[filtered["slice_id"] == selected_slice]
            
            # Display
            st.dataframe(
                filtered[["timestamp", "slice_id", "event_type", "description"]],
                use_container_width=True
            )
        else:
            st.info("No events logged yet.")
    else:
        st.info("No logs available yet.")


def render_settings_page():
    """Render the settings page"""
    st.title("⚙️ Settings")
    st.markdown("---")
    
    # General settings
    st.subheader("🔤 General Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        theme = st.selectbox(
            "Theme",
            ["Dark", "Light", "System"]
        )
    
    with col2:
        refresh_rate = st.slider(
            "Auto-refresh Rate (seconds)",
            min_value=0,
            max_value=60,
            value=0,
            help="Set to 0 to disable auto-refresh"
        )
    
    if st.button("💾 Save Settings"):
        st.success("Settings saved! (Demo)")
    
    st.markdown("---")
    
    # OpenRouter configuration
    st.subheader("🔌 OpenRouter Configuration")
    
    api_key = st.text_input(
        "API Key",
        type="password",
        help="Your OpenRouter API key"
    )
    
    if st.button("💾 Save API Key"):
        if api_key:
            st.success("API key saved! (Demo)")
        else:
            st.error("Please enter an API key.")
    
    st.markdown("---")
    
    # Slice configuration
    st.subheader("🔧 Slice Configuration")
    st.info("Slice-specific configuration is managed in each slice's dashboard.")
    
    st.markdown("---")
    
    # Danger zone
    st.subheader("⚠️ Danger Zone")
    
    if st.button("🗑️ Clear All Data"):
        st.warning("This will delete all slice data. This action cannot be undone.")
        if st.button("Yes, delete everything"):
            st.error("Not implemented in demo.")
    
    if st.button("🔄 Reset to Defaults"):
        st.warning("This will reset all settings to defaults.")
        if st.button("Yes, reset"):
            st.info("Not implemented in demo.")


def render_master_chat_page():
    """Render the Master Swarm Chat page"""
    import json
    from datetime import datetime
    
    # Initialize master chat
    if "master_chat" not in st.session_state:
        from refactorbot.master_core.master_chat import MasterSwarmChat
        import os
        api_key = os.environ.get("OPENROUTER_API_KEY")
        st.session_state.master_chat = MasterSwarmChat(api_key=api_key)
        st.session_state.messages = []
        st.session_state.actions = []
    
    st.title("🧠 Master Swarm Chat")
    st.markdown("Chat with the AI swarm orchestrator. I'm aware of all slices and can coordinate them.")
    
    # Quick commands
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📋 List All Agents"):
            st.session_state.messages.append({
                "role": "user",
                "content": "List all agents",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    with col2:
        if st.button("🧠 Show My Memories"):
            st.session_state.messages.append({
                "role": "user",
                "content": "What do I have stored?",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    with col3:
        if st.button("🤖 Create New Agent"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Create a new agent named TestAgent",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    with col4:
        if st.button("🔧 Register a Tool"):
            st.session_state.messages.append({
                "role": "user",
                "content": "Register a tool called calculator",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    st.markdown("---")
    
    # Chat status
    chat_status = st.session_state.master_chat.get_status()
    st.markdown("### 📊 Chat Status")
    st.metric("Initialized", "✓" if chat_status["initialized"] else "✗")
    st.metric("Model", chat_status.get("model", "N/A"))
    st.metric("History", chat_status["history_length"])
    
    st.markdown("---")
    
    # Chat interface
    st.subheader("💬 Chat")
    
    # Chat messages
    for i, message in enumerate(st.session_state.messages):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "timestamp" in message:
                st.caption(f"{message['timestamp']}")
            
            # Show associated actions
            if i < len(st.session_state.actions) and st.session_state.actions[i]:
                with st.expander("🔧 Dispatched Actions"):
                    for action in st.session_state.actions[i]:
                        st.json(action)
    
    # Chat input
    if prompt := st.chat_input("Ask me to coordinate the swarm..."):
        # Add user message
        st.session_state.messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            
            # Get AI response
            result = st.session_state.master_chat.chat(prompt)
            response = result["response"]
            actions = result["actions"]
            
            # Display response
            message_placeholder.markdown(response)
            
            # Show actions
            if actions:
                with st.expander("🔧 Dispatched Actions", expanded=True):
                    for action in actions:
                        st.json(action)
            
            # Store actions
            st.session_state.actions.append(actions)
            
            st.caption(f"Model: {st.session_state.master_chat.model} | {result['timestamp']}")
    
    st.markdown("---")
    
    # Direct slice control
    st.subheader("🎛️ Direct Slice Control")
    
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        slice_id = st.selectbox(
            "Select Slice",
            ["slice_agent", "slice_tools", "slice_memory", 
             "slice_communication", "slice_session", "slice_providers",
             "slice_skills", "slice_eventbus"]
        )
        
        # Get slice info
        slice_info = None
        for info in st.session_state.master_chat.slice_info.values():
            if info.slice_id == slice_id:
                slice_info = info
                break
        
        if slice_info:
            st.markdown(f"**{slice_info.name}**")
            st.markdown(slice_info.description)
            st.markdown("**Operations:**")
            for op in slice_info.operations:
                st.code(op)
    
    with col_b:
        if slice_info:
            operation = st.selectbox("Operation", slice_info.operations)
            
            st.markdown("**Payload:**")
            payload_json = st.text_area("JSON Payload", value="{}", height=100)
            
            try:
                payload = json.loads(payload_json)
            except:
                payload = {}
                st.error("Invalid JSON")
            
            if st.button("🚀 Execute", use_container_width=True):
                st.info("Configure OPENROUTER_API_KEY for full execution")
                st.json({"slice": slice_id, "operation": operation, "payload": payload, "status": "pending"})
    
    # Implementation info
    with st.expander("ℹ️ Implementation Info"):
        st.markdown(st.session_state.master_chat.get_implementation_summary())


def render():
    """Main render function"""
    page = render_sidebar()
    
    if page == "Overview":
        render_overview_page()
    elif page == "Control Panel":
        render_control_panel_page()
    elif page == "Analytics":
        render_analytics_page()
    elif page == "Logs":
        render_logs_page()
    elif page == "Settings":
        render_settings_page()
    elif page == "🧠 Master Swarm Chat":
        render_master_chat_page()


if __name__ == "__main__":
    render()
