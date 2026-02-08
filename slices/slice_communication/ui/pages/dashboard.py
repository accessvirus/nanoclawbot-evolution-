"""Communication Slice Dashboard."""
import streamlit as st


def render():
    st.set_page_config(page_title="Communication - Dashboard", page_icon="💬", layout="wide")
    st.title("💬 Communication Slice Dashboard")
    st.markdown("---")
    
    if "slice" not in st.session_state:
        try:
            from slices.slice_communication import CommunicationSlice
            st.session_state.slice = CommunicationSlice()
            import asyncio
            asyncio.run(st.session_state.slice.initialize())
        except Exception as e:
            st.error(f"Failed to initialize: {e}")
            return
    
    slice = st.session_state.slice
    
    # Channels overview
    import asyncio
    response = asyncio.run(slice.execute("list_channels", {}))
    channels = response.payload.get("channels", [])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Channels", len(channels))
    with col2:
        st.metric("Active", len([c for c in channels if c.get("enabled", True)]))
    
    st.markdown("---")
    
    # Add channel
    st.subheader("📡 Add Channel")
    
    with st.form("add_channel"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Channel Name")
            channel_type = st.selectbox("Type", ["discord", "telegram", "whatsapp", "feishu", "webhook"])
        with col2:
            config = st.text_area("Config (JSON)", value='{}')
        
        if st.form_submit_button("Add Channel"):
            import asyncio, json
            try:
                asyncio.run(slice.execute("add_channel", {
                    "name": name,
                    "type": channel_type,
                    "config": json.loads(config) if config else {}
                }))
                st.success(f"Channel '{name}' added!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Channel list
    st.subheader("📡 Channels")
    
    if channels:
        for channel in channels:
            with st.expander(f"💬 {channel.get('name', 'Unknown')} ({channel.get('type', 'Unknown')})"):
                st.write(f"**Status:** {'✅ Active' if channel.get('enabled', True) else '❌ Disabled'}")
                st.json(channel.get("config", {}))
    else:
        st.info("No channels configured yet.")


if __name__ == "__main__":
    render()
