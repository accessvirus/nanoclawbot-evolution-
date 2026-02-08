"""
Data models for Agent Core Slice.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SessionState(str, Enum):
    """Session state"""
    ACTIVE = "active"
    IDLE = "idle"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class AgentSession(BaseModel):
    """Agent session model"""
    id: str = Field(default_factory=str)
    user_id: str
    context: Dict[str, Any] = Field(default_factory=dict)
    state: SessionState = SessionState.ACTIVE
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AgentExecution(BaseModel):
    """Agent execution model"""
    id: str = Field(default_factory=str)
    session_id: str
    request: str
    response: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    duration_ms: int = 0
    success: bool = True
    error_message: Optional[str] = None
    model_used: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    executed_at: datetime = Field(default_factory=datetime.utcnow)


class PromptTemplate(BaseModel):
    """Prompt template model"""
    id: str = Field(default_factory=str)
    name: str
    description: Optional[str] = None
    template: str
    variables: List[str] = Field(default_factory=list)
    version: int = 1
    is_default: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContextConfig(BaseModel):
    """Context configuration model"""
    max_total_tokens: int = 8000
    system_prompt: str = ""
    include_history: bool = True
    history_turns: int = 10
    include_memory: bool = True
    memory_retrieval_limit: int = 5


class AgentRequest(BaseModel):
    """Agent execution request"""
    user_id: str
    message: str
    session_id: Optional[str] = None
    context_override: Dict[str, Any] = Field(default_factory=dict)
    model: Optional[str] = None
    stream: bool = False


class AgentResponse(BaseModel):
    """Agent execution response"""
    session_id: str
    execution_id: str
    response: str
    success: bool
    error_message: Optional[str] = None
    tokens_used: int = 0
    duration_ms: int = 0
    model_used: str = ""
