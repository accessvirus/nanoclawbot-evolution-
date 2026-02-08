"""
Analytics page for Agent Core Slice.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta


def render():
    """Render the analytics page"""
    st.set_page_config(
        page_title="Agent Core - Analytics",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Agent Core Analytics")
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
    
    # Time range selector
    days = st.selectbox(
        "Time Range",
        options=[7, 14, 30, 60, 90],
        index=0,
        format_func=lambda x: f"Last {x} days"
    )
    
    # Get analytics
    import asyncio
    analytics_response = asyncio.run(slice.execute(
        "get_analytics",
        {"days": days}
    ))
    
    analytics = analytics_response.payload if analytics_response.success else {}
    
    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "Total Executions",
            analytics.get("total_executions", 0),
            delta=f"+{analytics.get('total_executions', 0)} this period"
        )
    
    with col2:
        success_rate = analytics.get("success_rate", 0)
        st.metric(
            "Success Rate",
            f"{success_rate}%",
            delta="Target: 95%",
            delta_color="normal" if success_rate >= 95 else "inverse"
        )
    
    with col3:
        st.metric(
            "Failed Executions",
            analytics.get("failed", 0),
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            "Total Tokens",
            f"{analytics.get('total_tokens', 0):,}"
        )
    
    with col5:
        st.metric(
            "Avg Latency",
            f"{analytics.get('avg_latency_ms', 0):.0f}ms",
            delta="-100ms target",
            delta_color="normal"
        )
    
    st.markdown("---")
    
    # Charts
    col_left, col_right = st.columns(2)
    
    daily_data = analytics.get("daily_breakdown", [])
    
    if daily_data:
        df = pd.DataFrame(daily_data)
        df["date"] = pd.to_datetime(df["date"])
        
        with col_left:
            st.subheader("📈 Executions Over Time")
            fig = px.line(
                df,
                x="date",
                y=["successful_executions", "failed_executions"],
                title="Daily Executions",
                labels={"value": "Count", "date": "Date"},
                color_discrete_map={
                    "successful_executions": "green",
                    "failed_executions": "red"
                }
            )
            fig.update_layout(hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
        
        with col_right:
            st.subheader("📊 Token Usage")
            fig = px.bar(
                df,
                x="date",
                y="total_tokens",
                title="Daily Token Usage",
                labels={"total_tokens": "Tokens", "date": "Date"},
                color="total_tokens",
                color_continuous_scale="Viridis"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Latency chart
        st.subheader("⏱️ Latency Over Time")
        fig = px.line(
            df,
            x="date",
            y="avg_latency_ms",
            title="Average Execution Latency",
            labels={"avg_latency_ms": "Latency (ms)", "date": "Date"},
            markers=True
        )
        fig.update_traces(line_color="orange", marker_size=8)
        st.plotly_chart(fig, use_container_width=True)
        
        # Summary statistics
        st.subheader("📋 Summary Statistics")
        
        stats_col1, stats_col2, stats_col3 = st.columns(3)
        
        with stats_col1:
            st.markdown("#### Performance")
            st.write(f"**Average Latency:** {df['avg_latency_ms'].mean():.0f}ms")
            st.write(f"**Median Latency:** {df['avg_latency_ms'].median():.0f}ms")
            st.write(f"**Max Latency:** {df['avg_latency_ms'].max():.0f}ms")
        
        with stats_col2:
            st.markdown("#### Success Rate")
            success_rate = df["successful_executions"].sum() / df["total_executions"].sum() * 100 if df["total_executions"].sum() > 0 else 0
            st.write(f"**Overall Rate:** {success_rate:.1f}%")
            st.write(f"**Best Day:** {df['successful_executions'].max()} executions")
        
        with stats_col3:
            st.markdown("#### Volume")
            st.write(f"**Total Tokens:** {df['total_tokens'].sum():,}")
            st.write(f"**Avg Daily:** {df['total_executions'].mean():.1f}")
            st.write(f"**Peak Day:** {df['total_executions'].max()}")
    
    else:
        st.info("No analytics data available for the selected period.")
    
    # Daily breakdown table
    st.markdown("---")
    st.subheader("📅 Daily Breakdown")
    
    if daily_data:
        df = pd.DataFrame(daily_data)
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        
        # Format for display
        display_df = df.rename(columns={
            "date": "Date",
            "total_executions": "Total",
            "successful_executions": "Success",
            "failed_executions": "Failed",
            "avg_latency_ms": "Avg Latency",
            "total_tokens": "Tokens",
            "total_cost": "Cost ($)"
        })
        
        display_df["Success Rate"] = display_df.apply(
            lambda r: f"{r['Success'] / r['Total'] * 100:.1f}%" if r['Total'] > 0 else "N/A",
            axis=1
        )
        
        st.dataframe(
            display_df[["Date", "Total", "Success", "Failed", "Success Rate", "Avg Latency", "Tokens"]],
            use_container_width=True
        )
    
    # Export
    st.markdown("---")
    if daily_data:
        csv = pd.DataFrame(daily_data).to_csv(index=False)
        st.download_button(
            "📥 Export Analytics Data",
            csv,
            "agent_core_analytics.csv",
            "text/csv"
        )


if __name__ == "__main__":
    render()
