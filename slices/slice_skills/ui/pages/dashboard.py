"""Skills Slice Dashboard."""
import streamlit as st


def render():
    st.set_page_config(page_title="Skills - Dashboard", page_icon="📚", layout="wide")
    st.title("📚 Skills Slice Dashboard")
    st.markdown("---")
    
    if "slice" not in st.session_state:
        try:
            from slices.slice_providers import SkillsSlice
            st.session_state.slice = SkillsSlice()
            import asyncio
            asyncio.run(st.session_state.slice.initialize())
        except Exception as e:
            st.error(f"Failed to initialize: {e}")
            return
    
    slice = st.session_state.slice
    
    # Stats
    import asyncio
    response = asyncio.run(slice.execute("list", {}))
    skills = response.payload.get("skills", [])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Skills", len(skills))
    with col2:
        st.metric("Active", len([s for s in skills if s.get("enabled", True)]))
    with col3:
        st.metric("Executions Today", 0)
    
    st.markdown("---")
    
    # Add skill
    st.subheader("📚 Add Skill")
    
    with st.form("add_skill"):
        name = st.text_input("Skill Name")
        description = st.text_area("Description")
        skill_file = st.text_area("Skill File (YAML)")
        
        if st.form_submit_button("Add Skill"):
            import asyncio
            response = asyncio.run(slice.execute("add", {
                "name": name,
                "description": description,
                "skill_file": skill_file
            }))
            if response.success:
                st.success(f"Skill '{name}' added!")
                st.rerun()
            else:
                st.error(response.error_message)
    
    st.markdown("---")
    
    # Skills list
    st.subheader("📚 Skills")
    
    if skills:
        for skill in skills:
            with st.expander(f"📚 {skill.get('name', 'Unknown')}"):
                st.write(f"**Description:** {skill.get('description', 'N/A')}")
                st.write(f"**Version:** {skill.get('version', 'N/A')}")
                st.write(f"**Status:** {'✅ Active' if skill.get('enabled', True) else '❌ Disabled'}")
    else:
        st.info("No skills loaded yet.")


if __name__ == "__main__":
    render()
