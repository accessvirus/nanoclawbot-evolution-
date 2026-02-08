"""
Memory System Configuration Page for slice_memory

Configuration management for memory system.
"""

import streamlit as st
import json
from datetime import datetime


def render_config():
    """Render configuration page."""
    st.title("🧠 Memory Configuration")
    
    tab1, tab2, tab3 = st.tabs(["Storage", "Retrieval", "Cleanup"])
    
    with tab1:
        st.subheader("Storage Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            max_memories = st.number_input(
                "Max Memories per User",
                min_value=100,
                max_value=100000,
                value=10000
            )
            retention_days = st.number_input(
                "Retention Period (days)",
                min_value=1,
                max_value=3650,
                value=365
            )
        with col2:
            enable_compression = st.checkbox("Enable Compression", value=True)
            storage_backend = st.selectbox(
                "Storage Backend",
                ["sqlite", "postgresql", "redis"]
            )
        
        if st.button("Save Storage Settings"):
            st.session_state["memory_storage_config"] = {
                "max_memories": max_memories,
                "retention_days": retention_days,
                "enable_compression": enable_compression,
                "storage_backend": storage_backend
            }
            st.success("Storage settings saved!")
    
    with tab2:
        st.subheader("Retrieval Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            default_limit = st.number_input(
                "Default Retrieval Limit",
                min_value=1,
                max_value=100,
                value=10
            )
            min_similarity = st.slider(
                "Minimum Similarity Score",
                0.0,
                1.0,
                0.7
            )
        with col2:
            enable_semantic = st.checkbox("Enable Semantic Search", value=True)
            cache_results = st.checkbox("Cache Retrieval Results", value=True)
            cache_ttl = st.number_input("Cache TTL (seconds)", 60, 3600, 300)
        
        if st.button("Save Retrieval Settings"):
            st.session_state["memory_retrieval_config"] = {
                "default_limit": default_limit,
                "min_similarity": min_similarity,
                "enable_semantic": enable_semantic,
                "cache_results": cache_results,
                "cache_ttl": cache_ttl
            }
            st.success("Retrieval settings saved!")
    
    with tab3:
        st.subheader("Cleanup Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            auto_cleanup = st.checkbox("Enable Auto Cleanup", value=True)
            cleanup_interval = st.number_input(
                "Cleanup Interval (hours)",
                min_value=1,
                max_value=168,
                value=24
            )
        with col2:
            consolidate_on_read = st.checkbox(
                "Consolidate on Read", 
                value=True
            )
            consolidate_threshold = st.slider(
                "Consolidation Threshold",
                0.5,
                0.99,
                0.85
            )
        
        if st.button("Save Cleanup Settings"):
            st.session_state["memory_cleanup_config"] = {
                "auto_cleanup": auto_cleanup,
                "cleanup_interval": cleanup_interval,
                "consolidate_on_read": consolidate_on_read,
                "consolidate_threshold": consolidate_threshold
            }
            st.success("Cleanup settings saved!")
    
    # Import/Export
    st.divider()
    st.subheader("Import/Export")
    
    config = {
        "storage": st.session_state.get("memory_storage_config", {}),
        "retrieval": st.session_state.get("memory_retrieval_config", {}),
        "cleanup": st.session_state.get("memory_cleanup_config", {})
    }
    
    st.download_button(
        "Export Configuration",
        json.dumps(config, indent=2),
        "memory_config.json",
        "application/json"
    )


if __name__ == "__main__":
    render_config()
