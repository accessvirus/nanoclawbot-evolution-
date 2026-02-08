"""
Configuration page for Agent Core Slice.
"""
import streamlit as st


def render():
    """Render the configuration page"""
    st.set_page_config(
        page_title="Agent Core - Configuration",
        page_icon="⚙️",
        layout="wide"
    )
    
    st.title("⚙️ Agent Core Configuration")
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
    
    # Tabs for different config sections
    tab1, tab2, tab3, tab4 = st.tabs([
        "🔧 General",
        "📝 Templates",
        "🧠 Context",
        "📊 Diagnostics"
    ])
    
    with tab1:
        st.subheader("General Configuration")
        
        # LLM Settings
        st.markdown("#### LLM Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            model = st.text_input(
                "Default Model",
                value=slice._config.llm_model,
                help="OpenRouter model identifier"
            )
            temperature = st.slider(
                "Temperature",
                min_value=0.0,
                max_value=2.0,
                value=slice._config.llm_temperature,
                step=0.1,
                help="Higher values = more creative, lower = more deterministic"
            )
        
        with col2:
            max_tokens = st.number_input(
                "Max Tokens",
                min_value=100,
                max_value=32000,
                value=slice._config.llm_max_tokens,
                step=100
            )
            debug_mode = st.toggle(
                "Debug Mode",
                value=slice._config.debug
            )
        
        if st.button("💾 Save General Settings"):
            st.success("Settings saved! (Demo - changes not persisted)")
        
        st.markdown("---")
        
        # System Prompt
        st.markdown("#### System Prompt")
        system_prompt = st.text_area(
            "Default System Prompt",
            value="You are a helpful AI assistant.",
            height=150,
            help="This is the default system prompt for all agent interactions"
        )
        
        if st.button("💾 Save System Prompt"):
            st.success("System prompt saved! (Demo)")
    
    with tab2:
        st.subheader("Prompt Templates")
        
        # List existing templates
        import asyncio
        templates_response = asyncio.run(slice.execute(
            "list_templates",
            {}
        ))
        
        templates = templates_response.payload.get("templates", []) if templates_response.success else []
        
        if templates:
            st.write(f"**{len(templates)}** templates found:")
            for t in templates:
                with st.expander(f"📄 {t['name']}"):
                    st.write(f"**Description:** {t.get('description', 'N/A')}")
                    st.write(f"**Template:**\n{t['template'][:200]}...")
                    st.caption(f"Version: {t['version']} | Default: {'Yes' if t['is_default'] else 'No'}")
        else:
            st.info("No templates found.")
        
        st.markdown("---")
        
        # Create new template
        st.markdown("#### Create New Template")
        
        with st.form("create_template"):
            template_name = st.text_input("Template Name")
            template_desc = st.text_input("Description")
            template_content = st.text_area("Template Content", height=150)
            template_vars = st.text_input("Variables (comma-separated)")
            is_default = st.checkbox("Set as Default")
            
            submitted = st.form_submit_button("Create Template")
            
            if submitted:
                if template_name and template_content:
                    import asyncio
                    variables = [v.strip() for v in template_vars.split(",")] if template_vars else []
                    response = asyncio.run(slice.execute(
                        "create_template",
                        {
                            "name": template_name,
                            "description": template_desc,
                            "template": template_content,
                            "variables": variables,
                            "is_default": is_default
                        }
                    ))
                    
                    if response.success:
                        st.success(f"Template '{template_name}' created!")
                        st.rerun()
                    else:
                        st.error(f"Error: {response.error_message}")
                else:
                    st.error("Name and content are required.")
    
    with tab3:
        st.subheader("Context Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            max_total_tokens = st.number_input(
                "Max Total Tokens",
                min_value=1000,
                max_value=128000,
                value=8000,
                step=1000
            )
            include_history = st.toggle(
                "Include Message History",
                value=True
            )
        
        with col2:
            history_turns = st.number_input(
                "History Turns",
                min_value=1,
                max_value=100,
                value=10,
                help="Number of conversation turns to include"
            )
            include_memory = st.toggle(
                "Include Memory",
                value=True
            )
        
        if st.button("💾 Save Context Settings"):
            st.success("Context settings saved! (Demo)")
    
    with tab4:
        st.subheader("Diagnostics")
        
        import asyncio
        diag_response = asyncio.run(slice.run_self_diagnostics())
        
        st.json(diag_response)
        
        st.markdown("---")
        
        if st.button("🔄 Run Full Diagnostics"):
            st.success("Diagnostics complete!")
        
        if st.button("🗑️ Clear All Sessions"):
            st.warning("This will delete all sessions. Are you sure?")
            if st.button("Yes, delete all"):
                st.error("Not implemented in demo.")
        
        if st.button("🗑️ Clear All Data"):
            st.warning("This will delete all data including analytics.")
            if st.button("Yes, delete all"):
                st.error("Not implemented in demo.")


if __name__ == "__main__":
    render()
