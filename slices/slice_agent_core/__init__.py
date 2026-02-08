"""
Agent Core Slice - Main agent loop and context management.

This is a full-stack slice with:
- SQLite database for sessions and executions
- LLM provider for self-awareness
- Streamlit UI for management
"""
from .slice import AgentCoreSlice

__all__ = ["AgentCoreSlice"]
