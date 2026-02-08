"""
Dashboard page for Agent Core Slice.
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


def render():
    """Render the dashboard page"""
    st.set_page_config(
        page_title="Agent Core - Dashboard",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 Agent Core Slice Dashboard")
    st.markdown("---")
    
    # Initialize slice
    if "slice" not in st.session_state:
        try:
            from slices.slice_agent_core import AgentCoreSlice
            st.session_state.slice = AgentCoreSlice()
            import asyncio
            asyncio.run(st.session_state.slice.initialize())
        except Exception as e:
            st.error(f"Failed to initialize slice: {e}")
            return
    
    slice = st.session_state.slice
    
    # Sidebar - Quick Actions
    with st.sidebar:
        st.header("Quick Actions")
        
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
        
        st.markdown("### Session")
        user_id = st.text_input("User ID", value="default_user")
        
        if st.button("➕ New Session", use_container_width=True):
            import asyncio
            response = asyncio.run(slice.execute(
                "create_session",
                {"user_id": user_id}
            ))
            if response.success:
                st.session_state.current_session = response.payload["session_id"]
                st.success(f"Session created: {response.payload['session_id'][:8]}...")
            else:
                st.error(response.error_message)
    
    # Main Content
    col1, col2, col3, col4 = st.columns(4)
    
    # Get analytics
    import asyncio
    analytics_response = asyncio.run(slice.execute(
        "get_analytics",
        {"days": 7}
    ))
    
    analytics = analytics_response.payload if analytics_response.success else {}
    
    with col1:
        st.metric(
            "Total Executions",
            analytics.get("total_executions", 0),
            delta=f"{analytics.get('successful', 0)} successful"
        )
    
    with col2:
        st.metric(
            "Success Rate",
            f"{analytics.get('success_rate', 0)}%",
            delta="Target: 95%"
        )
    
    with col3:
        st.metric(
            "Avg Latency",
            f"{analytics.get('avg_latency_ms', 0):.0f}ms",
            delta="-50ms target"
        )
    
    with col4:
        st.metric(
            "Total Tokens",
            f"{analytics.get('total_tokens', 0):,}",
            delta="This week"
        )
    
    st.markdown("---")
    
    # Two columns layout
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader("💬 Test Agent")
        
        # Session selector
        sessions_response = asyncio.run(slice.execute(
            "list_sessions",
            {"user_id": user_id, "limit": 10}
        ))
        
        sessions = sessions_response.payload.get("sessions", []) if sessions_response.success else []
        
        if "current_session" not in st.session_state:
            st.session_state.current_session = sessions[0]["id"] if sessions else None
        
        if sessions:
            session_options = {s["id"][:8]: s["id"] for s in sessions}
            selected_label = st.selectbox(
                "Session",
                options=list(session_options.keys()),
                index=0
            )
            st.session_state.current_session = session_options[selected_label]
        else:
            st.info("No sessions found. Create a new session to get started.")
            st.session_state.current_session = None
        
        # Message input
        if st.session_state.current_session:
            message = st.text_area(
                "Message",
                placeholder="Type your message here...",
                height=100
            )
            
            if st.button("Send", type="primary", use_container_width=True):
                if message:
                    import asyncio
                    response = asyncio.run(slice.execute(
                        "execute",
                        {
                            "user_id": user_id,
                            "message": message,
                            "session_id": st.session_state.current_session
                        }
                    ))
                    
                    if response.success:
                        st.session_state.last_response = response.payload
                        st.success("Response received!")
                    else:
                        st.error(f"Error: {response.error_message}")
            
            # Show last response
            if "last_response" in st.session_state:
                resp = st.session_state.last_response
                st.markdown("### Last Response")
                st.info(resp.get("response", "No response"))
                st.caption(
                    f"Tokens: {resp.get('tokens_used', 0)} | "
                    f"Duration: {resp.get('duration_ms', 0)}ms"
                )
        else:
            st.warning("Please create a new session first.")
    
    with col_right:
        st.subheader("📊 Recent Executions")
        
        # List recent executions
        exec_response = asyncio.run(slice.execute(
            "list_executions",
            {"limit": 10}
        ))
        
        executions = exec_response.payload.get("executions", []) if exec_response.success else []
        
        if executions:
            for exec in executions[:5]:
                with st.expander(f"Execution {exec['id'][:8]}"):
                    st.write(f"**Request:** {exec['request'][:100]}...")
                    st.write(f"**Response:** {exec['response'][:100] if exec.get('response') else 'N/A'}...")
                    st.caption(
                        f"Status: {'✅' if exec['success'] else '❌'} | "
                        f"Tokens: {exec.get('total_tokens', 0)} | "
                        f"Duration: {exec.get('duration_ms', 0)}ms"
                    )
        else:
            st.info("No executions yet.")
    
    st.markdown("---")
    
    # Sessions List
    st.subheader("📁 Sessions")
    
    if sessions:
        df = pd.DataFrame([
            {
                "ID": s["id"][:8],
                "User": s["user_id"],
                "State": s["state"],
                "Created": datetime.fromisoformat(s["created_at"]).strftime("%Y-%m-%d %H:%M")
            }
            for s in sessions
        ])
        
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No sessions found.")
    
    # Diagnostics
    with st.expander("🔍 Diagnostics"):
        import asyncio
        diag_response = asyncio.run(slice.run_self_diagnostics())
        st.json(diag_response)


if __name__ == "__main__":
    render()
