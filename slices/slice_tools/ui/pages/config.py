"""
Tool System Configuration Page for slice_tools

Configuration management for tool system.
"""

import streamlit as st
import json
from datetime import datetime


def render_config():
    """Render configuration page."""
    st.title("🔧 Tool Configuration")
    
    # Settings sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "General",
        "Execution",
        "Security",
        "Categories"
    ])
    
    with tab1:
        st.subheader("General Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            max_concurrent = st.number_input(
                "Max Concurrent Executions",
                min_value=1,
                max_value=100,
                value=10
            )
            default_timeout = st.number_input(
                "Default Timeout (seconds)",
                min_value=1,
                max_value=300,
                value=30
            )
        with col2:
            enable_logging = st.checkbox("Enable Execution Logging", value=True)
            enable_metrics = st.checkbox("Enable Metrics Collection", value=True)
            auto_register = st.checkbox("Auto-register Built-in Tools", value=True)
        
        if st.button("Save General Settings"):
            st.session_state["tool_config"] = {
                "max_concurrent": max_concurrent,
                "default_timeout": default_timeout,
                "enable_logging": enable_logging,
                "enable_metrics": enable_metrics,
                "auto_register": auto_register
            }
            st.success("Settings saved!")
    
    with tab2:
        st.subheader("Execution Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            retry_failed = st.checkbox("Retry Failed Executions", value=True)
            max_retries = st.number_input("Max Retries", 0, 10, 3)
        with col2:
            sandbox_enabled = st.checkbox("Enable Sandboxing", value=True)
            memory_limit = st.number_input("Memory Limit (MB)", 64, 4096, 256)
        
        if st.button("Save Execution Settings"):
            st.session_state["execution_config"] = {
                "retry_failed": retry_failed,
                "max_retries": max_retries,
                "sandbox_enabled": sandbox_enabled,
                "memory_limit": memory_limit
            }
            st.success("Execution settings saved!")
    
    with tab3:
        st.subheader("Security Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            validate_params = st.checkbox("Validate Parameters", value=True)
            restrict_imports = st.checkbox("Restrict Imports", value=True)
        with col2:
            allowed_imports = st.text_area(
                "Allowed Imports (one per line)",
                value="os\njson\nre\nmath\ndatetime"
            )
        
        if st.button("Save Security Settings"):
            st.session_state["security_config"] = {
                "validate_params": validate_params,
                "restrict_imports": restrict_imports,
                "allowed_imports": allowed_imports.split("\n")
            }
            st.success("Security settings saved!")
    
    with tab4:
        st.subheader("Tool Categories")
        
        # Category management
        categories = st.session_state.get("tool_categories", [
            {"id": "data", "name": "Data Processing", "color": "#4CAF50"},
            {"id": "file", "name": "File Operations", "color": "#2196F3"},
            {"id": "api", "name": "API Calls", "color": "#FF9800"},
            {"id": "math", "name": "Mathematical", "color": "#9C27B0"},
        ])
        
        # Add new category
        with st.expander("Add Category"):
            new_name = st.text_input("Category Name")
            new_color = st.color_picker("Color", "#4CAF50")
            if st.button("Add Category"):
                categories.append({
                    "id": new_name.lower().replace(" ", "_"),
                    "name": new_name,
                    "color": new_color
                })
                st.session_state["tool_categories"] = categories
                st.rerun()
        
        # Display categories
        for cat in categories:
            col_cat, col_act = st.columns([4, 1])
            with col_cat:
                st.markdown(
                    f'<span style="color:{cat["color"]}">●</span> **{cat["name"]}**',
                    unsafe_allow_html=True
                )
            with col_act:
                if st.button("🗑️", key=f"del_{cat['id']}"):
                    categories = [c for c in categories if c["id"] != cat["id"]]
                    st.session_state["tool_categories"] = categories
                    st.rerun()
    
    # Import/Export config
    st.divider()
    st.subheader("Configuration Management")
    
    col_imp, col_exp = st.columns(2)
    
    with col_exp:
        config_json = json.dumps({
            "general": st.session_state.get("tool_config", {}),
            "execution": st.session_state.get("execution_config", {}),
            "security": st.session_state.get("security_config", {}),
            "categories": st.session_state.get("tool_categories", [])
        }, indent=2)
        st.download_button(
            "Export Configuration",
            config_json,
            "tool_config.json",
            "application/json"
        )
    
    with col_imp:
        uploaded = st.file_uploader("Import Configuration", type="json")
        if uploaded:
            try:
                config = json.load(uploaded)
                if "general" in config:
                    st.session_state["tool_config"] = config["general"]
                if "execution" in config:
                    st.session_state["execution_config"] = config["execution"]
                if "security" in config:
                    st.session_state["security_config"] = config["security"]
                if "categories" in config:
                    st.session_state["tool_categories"] = config["categories"]
                st.success("Configuration imported!")
            except Exception as e:
                st.error(f"Invalid configuration: {e}")
    
    # Reset to defaults
    st.divider()
    if st.button("Reset to Defaults", type="primary"):
        st.session_state["tool_config"] = {}
        st.session_state["execution_config"] = {}
        st.session_state["security_config"] = {}
        st.success("Reset to defaults!")


if __name__ == "__main__":
    render_config()
