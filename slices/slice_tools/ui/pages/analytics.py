"""
Tool System Analytics Page for slice_tools

Analytics and metrics for tool management.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta


def render_analytics():
    """Render analytics page."""
    st.title("🔧 Tool Analytics")
    
    # Get services
    services = _get_services()
    
    # Stats overview
    stats = st.session_state.get("tool_stats", {})
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Tools", stats.get("total_tools", 0))
    col2.metric("Total Executions", stats.get("total_executions", 0))
    col3.metric("Success Rate", f"{stats.get('success_rate', 0):.1f}%")
    col4.metric("Active Categories", stats.get("categories", 0))
    
    st.divider()
    
    # Execution trends
    st.subheader("Execution Trends")
    
    # Get execution history
    history = st.session_state.get("execution_history", [])
    
    if history:
        df = pd.DataFrame(history)
        df["created_at"] = pd.to_datetime(df["created_at"])
        
        # Daily executions
        daily = df.groupby(df["created_at"].dt.date).size().reset_index(name="count")
        fig = px.line(daily, x="created_at", y="count", title="Daily Tool Executions")
        st.plotly_chart(fig, use_container_width=True)
        
        # Success vs Failed
        status_counts = df.groupby(["created_at", "success"]).size().reset_index(name="count")
        fig2 = px.bar(
            status_counts,
            x="created_at",
            y="count",
            color="success",
            title="Success vs Failed Executions"
        )
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No execution data available yet.")
    
    # Tool usage breakdown
    st.subheader("Tool Usage Breakdown")
    
    tool_usage = st.session_state.get("tool_usage", [])
    if tool_usage:
        df = pd.DataFrame(tool_usage)
        fig3 = px.bar(df, x="tool_name", y="execution_count", title="Tool Usage")
        st.plotly_chart(fig3, use_container_width=True)
    
    # Performance metrics
    st.subheader("Performance Metrics")
    
    perf_data = st.session_state.get("performance_data", [])
    if perf_data:
        df = pd.DataFrame(perf_data)
        fig4 = px.box(df, x="tool_name", y="execution_time", title="Execution Time by Tool")
        st.plotly_chart(fig4, use_container_width=True)
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.write("**Average Execution Time**")
            st.dataframe(df.groupby("tool_name")["execution_time"].mean())
        with col_b:
            st.write("**Max Execution Time**")
            st.dataframe(df.groupby("tool_name")["execution_time"].max())
    
    # Recent errors
    st.subheader("Recent Errors")
    
    errors = st.session_state.get("recent_errors", [])
    if errors:
        st.error(f"{len(errors)} errors in recent executions")
        with st.expander("View Errors"):
            for error in errors[-10:]:
                st.code(f"[{error['timestamp']}] {error['error']}")
    else:
        st.success("No recent errors!")
    
    # Export options
    st.divider()
    st.subheader("Export Data")
    
    col_export, _ = st.columns([1, 2])
    with col_export:
        export_format = st.selectbox("Export Format", ["CSV", "JSON"])
        if st.button("Export Analytics"):
            if export_format == "CSV":
                if history:
                    df.to_csv("tool_analytics.csv", index=False)
                    st.download_button("Download CSV", open("tool_analytics.csv", "rb"), "tool_analytics.csv")
            else:
                if history:
                    import json
                    st.download_button("Download JSON", json.dumps(history), "tool_analytics.json")


def _get_services():
    """Get services from context."""
    from slices.slice_tools.slice import SliceTools
    return SliceTools


if __name__ == "__main__":
    render_analytics()
