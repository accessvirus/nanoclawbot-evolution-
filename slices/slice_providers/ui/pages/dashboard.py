"""Providers Slice Dashboard."""
import streamlit as st


def render():
    st.set_page_config(page_title="Providers - Dashboard", page_icon="🔌", layout="wide")
    st.title("🔌 Providers Slice Dashboard")
    st.markdown("---")
    
    if "slice" not in st.session_state:
        try:
            from slices.slice_providers import ProvidersSlice
            st.session_state.slice = ProvidersSlice()
            import asyncio
            asyncio.run(st.session_state.slice.initialize())
        except Exception as e:
            st.error(f"Failed to initialize: {e}")
            return
    
    slice = st.session_state.slice
    
    # Stats
    import asyncio
    response = asyncio.run(slice.execute("list", {}))
    providers = response.payload.get("providers", [])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Providers", len(providers))
    with col2:
        st.metric("Active", len([p for p in providers if p.get("enabled", True)]))
    with col3:
        st.metric("Total Cost", "$0.00")
    
    st.markdown("---")
    
    # Add provider
    st.subheader("🔌 Add Provider")
    
    with st.form("add_provider"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Provider Name")
            provider_type = st.selectbox("Type", ["openrouter", "openai", "anthropic", "custom"])
        with col2:
            api_key = st.text_input("API Key", type="password")
            models = st.text_input("Models (comma-separated)")
        
        if st.form_submit_button("Add Provider"):
            import asyncio
            response = asyncio.run(slice.execute("add", {
                "name": name,
                "provider_type": provider_type,
                "api_key": api_key,
                "models": [m.strip() for m in models.split(",")] if models else []
            }))
            if response.success:
                st.success(f"Provider '{name}' added!")
                st.rerun()
            else:
                st.error(response.error_message)
    
    st.markdown("---")
    
    # Provider list
    st.subheader("🔌 Providers")
    
    if providers:
        for provider in providers:
            with st.expander(f"🔌 {provider.get('name', 'Unknown')}"):
                st.write(f"**Type:** {provider.get('provider_type', 'N/A')}")
                st.write(f"**Status:** {'✅ Active' if provider.get('enabled', True) else '❌ Disabled'}")
                st.write(f"**Models:** {', '.join(provider.get('models', []))}")
    else:
        st.info("No providers configured yet.")


if __name__ == "__main__":
    render()
