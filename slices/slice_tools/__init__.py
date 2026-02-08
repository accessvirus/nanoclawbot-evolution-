"""
Tools Slice - Tool registry and management.

Full-stack slice with:
- SQLite database for tool registry and executions
- LLM provider for self-awareness
- Streamlit UI for management
"""
from .slice import ToolsSlice

__all__ = ["ToolsSlice"]
