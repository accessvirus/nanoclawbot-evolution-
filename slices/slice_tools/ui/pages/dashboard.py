"""Tools Slice Dashboard."""
import streamlit as st


def render():
    st.set_page_config(page_title="Tools - Dashboard", page_icon="🛠️", layout="wide")
    st.title("🛠️ Tools Slice Dashboard")
    st.markdown("---")
    
    # Initialize slice
    if "slice" not in st.session_state:
        try:
            from slices.slice_tools import ToolsSlice
            st.session_state.slice = ToolsSlice()
            import asyncio
            asyncio.run(st.session_state.slice.initialize())
        except Exception as e:
            st.error(f"Failed to initialize: {e}")
            return
    
    slice = st.session_state.slice
    
    # Metrics
    import asyncio
    response = asyncio.run(slice.execute("list_tools", {}))
    tools = response.payload.get("tools", [])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tools", len(tools))
    with col2:
        st.metric("Active", len([t for t in tools if t.get("enabled", True)]))
    with col3:
        st.metric("Categories", len(set(t.get("category", "uncategorized") for t in tools)))
    
    st.markdown("---")
    
    # Tool Registry
    st.subheader("🛠️ Tool Registry")
    
    # Add new tool form
    with st.expander("➕ Add New Tool"):
        with st.form("add_tool"):
            name = st.text_input("Tool Name")
            description = st.text_area("Description")
            schema = st.text_area("Schema (JSON)", value='{"type": "object", "properties": {}}')
            category = st.text_input("Category")
            
            if st.form_submit_button("Add Tool"):
                import asyncio, json
                try:
                    asyncio.run(slice.execute("register_tool", {
                        "name": name,
                        "description": description,
                        "schema": json.loads(schema) if schema else {},
                        "category": category
                    }))
                    st.success(f"Tool '{name}' added!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    # Tool list
    if tools:
        for tool in tools:
            with st.expander(f"🛠️ {tool.get('name', 'Unknown')}"):
                st.write(f"**Description:** {tool.get('description', 'N/A')}")
                st.write(f"**Category:** {tool.get('category', 'Uncategorized')}")
                st.json(tool.get("schema", {}))
    else:
        st.info("No tools registered yet.")


if __name__ == "__main__":
    render()
