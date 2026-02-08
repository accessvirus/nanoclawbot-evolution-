"""Event Bus Slice Dashboard."""
import streamlit as st


def render():
    st.set_page_config(page_title="Event Bus - Dashboard", page_icon="🚌", layout="wide")
    st.title("🚌 Event Bus Slice Dashboard")
    st.markdown("---")
    
    if "slice" not in st.session_state:
        try:
            from slices.slice_providers import EventBusSlice
            st.session_state.slice = EventBusSlice()
            import asyncio
            asyncio.run(st.session_state.slice.initialize())
        except Exception as e:
            st.error(f"Failed to initialize: {e}")
            return
    
    slice = st.session_state.slice
    
    # Stats
    import asyncio
    response = asyncio.run(slice.execute("stats", {}))
    stats = response.payload.get("stats", {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Events", stats.get("total_events", 0))
    with col2:
        st.metric("Processed", stats.get("processed", 0))
    with col3:
        st.metric("Pending", stats.get("pending", 0))
    with col4:
        st.metric("Failed", stats.get("failed", 0))
    
    st.markdown("---")
    
    # Publish event
    st.subheader("📤 Publish Event")
    
    with st.form("publish_event"):
        col1, col2 = st.columns(2)
        with col1:
            event_type = st.text_input("Event Type")
            source_slice = st.text_input("Source Slice")
        with col2:
            payload = st.text_area("Payload (JSON)", value='{}')
        
        if st.form_submit_button("Publish"):
            import asyncio, json
            try:
                response = asyncio.run(slice.execute("publish", {
                    "event_type": event_type,
                    "source_slice": source_slice,
                    "payload": json.loads(payload) if payload else {}
                }))
                if response.success:
                    st.success("Event published!")
                    st.rerun()
                else:
                    st.error(response.error_message)
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.markdown("---")
    
    # Subscriptions
    st.subheader("📥 Subscriptions")
    
    with st.expander("Add Subscription"):
        with st.form("add_sub"):
            event_type = st.text_input("Event Type to Subscribe")
            subscriber = st.text_input("Subscriber Slice")
            if st.form_submit_button("Add"):
                import asyncio
                response = asyncio.run(slice.execute("subscribe", {
                    "event_type": event_type,
                    "subscriber": subscriber
                }))
                if response.success:
                    st.success("Subscription added!")
    
    # Recent events
    st.subheader("📋 Recent Events")
    
    response = asyncio.run(slice.execute("list", {"limit": 20}))
    events = response.payload.get("events", [])
    
    if events:
        for event in events:
            with st.expander(f"📋 {event.get('event_type', 'Unknown')}"):
                st.write(f"**Source:** {event.get('source_slice', 'N/A')}")
                st.write(f"**Status:** {event.get('status', 'N/A')}")
                st.json(event.get("payload", {}))
    else:
        st.info("No events yet.")


if __name__ == "__main__":
    render()
