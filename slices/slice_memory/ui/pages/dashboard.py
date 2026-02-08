"""Memory Slice Dashboard."""
import streamlit as st


def render():
    st.set_page_config(page_title="Memory - Dashboard", page_icon="🧠", layout="wide")
    st.title("🧠 Memory Slice Dashboard")
    st.markdown("---")
    
    if "slice" not in st.session_state:
        try:
            from slices.slice_memory import MemorySlice
            st.session_state.slice = MemorySlice()
            import asyncio
            asyncio.run(st.session_state.slice.initialize())
        except Exception as e:
            st.error(f"Failed to initialize: {e}")
            return
    
    slice = st.session_state.slice
    
    # Stats
    import asyncio
    stats = asyncio.run(slice.execute("get_stats", {}))
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Memories", stats.payload.get("total_memories", 0))
    with col2:
        st.metric("Long-term Memories", stats.payload.get("long_term_memories", 0))
    
    st.markdown("---")
    
    # Store memory
    st.subheader("💾 Store Memory")
    
    with st.form("store_memory"):
        col1, col2 = st.columns(2)
        with col1:
            content = st.text_area("Memory Content")
            memory_type = st.selectbox("Type", ["short_term", "long_term", "contextual"])
        with col2:
            user_id = st.text_input("User ID")
            session_id = st.text_input("Session ID")
        
        if st.form_submit_button("Store"):
            import asyncio
            response = asyncio.run(slice.execute("store", {
                "content": content,
                "memory_type": memory_type,
                "user_id": user_id,
                "session_id": session_id
            }))
            if response.success:
                st.success("Memory stored!")
                st.rerun()
            else:
                st.error(response.error_message)
    
    st.markdown("---")
    
    # Retrieve memories
    st.subheader("🔍 Retrieve Memories")
    
    with st.form("retrieve"):
        query = st.text_input("Query")
        memory_type = st.selectbox("Filter by Type", ["all", "short_term", "long_term", "contextual"])
        
        if st.form_submit_button("Retrieve"):
            import asyncio
            response = asyncio.run(slice.execute("retrieve", {
                "query": query,
                "memory_type": None if memory_type == "all" else memory_type
            }))
            if response.success:
                memories = response.payload.get("memories", [])
                for mem in memories:
                    with st.expander(f"📝 {mem.get('memory_type', 'Unknown')}"):
                        st.write(mem.get("content", ""))
                        st.caption(f"Created: {mem.get('created_at', 'N/A')}")
            else:
                st.error(response.error_message)


if __name__ == "__main__":
    render()
