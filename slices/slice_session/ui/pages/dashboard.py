"""Session Slice Dashboard."""
import streamlit as st


def render():
    st.set_page_config(page_title="Session - Dashboard", page_icon="📁", layout="wide")
    st.title("📁 Session Slice Dashboard")
    st.markdown("---")
    
    if "slice" not in st.session_state:
        try:
            from slices.slice_session import SessionSlice
            st.session_state.slice = SessionSlice()
            import asyncio
            asyncio.run(st.session_state.slice.initialize())
        except Exception as e:
            st.error(f"Failed to initialize: {e}")
            return
    
    slice = st.session_state.slice
    
    # Stats
    import asyncio
    response = asyncio.run(slice.execute("list", {"state": "active"}))
    sessions = response.payload.get("sessions", [])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Active Sessions", len(sessions))
    with col2:
        st.metric("Total Messages", 0)
    with col3:
        st.metric("Avg Session Duration", "0m")
    
    st.markdown("---")
    
    # Create session
    st.subheader("📁 Create Session")
    
    with st.form("create_session"):
        user_id = st.text_input("User ID")
        session_type = st.selectbox("Type", ["conversation", "task", "research"])
        
        if st.form_submit_button("Create"):
            import asyncio
            response = asyncio.run(slice.execute("create", {
                "user_id": user_id,
                "session_type": session_type
            }))
            if response.success:
                st.success(f"Session created!")
                st.rerun()
            else:
                st.error(response.error_message)
    
    st.markdown("---")
    
    # Active sessions
    st.subheader("📁 Active Sessions")
    
    if sessions:
        for session in sessions[:10]:
            with st.expander(f"📁 {session.get('id', 'Unknown')[:8]}"):
                st.write(f"**User:** {session.get('user_id', 'N/A')}")
                st.write(f"**Type:** {session.get('session_type', 'N/A')}")
                st.write(f"**Started:** {session.get('started_at', 'N/A')}")
    else:
        st.info("No active sessions.")


if __name__ == "__main__":
    render()
