"""
Memory System Analytics Page for slice_memory

Analytics and metrics for memory storage.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta


def render_analytics():
    """Render analytics page."""
    st.title("🧠 Memory Analytics")
    
    # Stats overview
    stats = st.session_state.get("memory_stats", {})
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Memories", stats.get("total_memories", 0))
    col2.metric("User Memories", stats.get("user_memories", 0))
    col3.metric("Consolidated", stats.get("consolidated", 0))
    col4.metric("Storage Used", stats.get("storage_mb", 0))
    
    st.divider()
    
    # Memory by type
    st.subheader("Memory by Type")
    
    type_data = stats.get("by_type", {})
    if type_data:
        df = pd.DataFrame(list(type_data.items()), columns=["Type", "Count"])
        fig = px.pie(df, values="Count", names="Type", title="Memory Distribution")
        st.plotly_chart(fig, use_container_width=True)
    
    # Memory growth
    st.subheader("Memory Growth")
    
    history = st.session_state.get("memory_history", [])
    if history:
        df = pd.DataFrame(history)
        df["date"] = pd.to_datetime(df["date"])
        fig2 = px.line(df, x="date", y="count", title="Memory Growth Over Time")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No historical data available.")
    
    # Retrieval patterns
    st.subheader("Retrieval Patterns")
    
    retrieval_data = st.session_state.get("retrieval_stats", [])
    if retrieval_data:
        df = pd.DataFrame(retrieval_data)
        fig3 = px.bar(df, x="query_type", y="count", title="Retrieval by Type")
        st.plotly_chart(fig3, use_container_width=True)
    
    # Memory usage by user
    st.subheader("Top Users by Memory")
    
    user_data = st.session_state.get("user_memory_stats", [])
    if user_data:
        df = pd.DataFrame(user_data)
        fig4 = px.bar(df.head(10), x="user_id", y="memory_count", title="Memory Count by User")
        st.plotly_chart(fig4, use_container_width=True)
    
    # Cleanup statistics
    st.subheader("Cleanup Statistics")
    
    cleanup_stats = st.session_state.get("cleanup_stats", {})
    col_c1, col_c2, col_c3 = st.columns(3)
    col_c1.metric("Deleted", cleanup_stats.get("deleted", 0))
    col_c2.metric("Consolidated", cleanup_stats.get("consolidated", 0))
    col_c3.metric("Space Reclaimed", cleanup_stats.get("space_reclaimed", "0 MB"))
    
    # Export options
    st.divider()
    st.subheader("Export")
    
    if st.button("Export Memory Analytics"):
        analytics_data = {
            "stats": stats,
            "history": history,
            "exported_at": datetime.utcnow().isoformat()
        }
        import json
        st.download_button(
            "Download JSON",
            json.dumps(analytics_data),
            "memory_analytics.json"
        )


if __name__ == "__main__":
    render_analytics()
