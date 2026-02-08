"""
Core services for Agent Core Slice.
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import (
    AgentExecution,
    AgentRequest,
    AgentResponse,
    AgentSession,
    ContextConfig,
    PromptTemplate,
    SessionState,
)
from .database import AgentCoreDatabase


class AgentCoreService:
    """
    Core service for agent operations.
    Handles sessions, executions, and context management.
    """
    
    def __init__(self, database: AgentCoreDatabase):
        self.db = database
        self._default_context: ContextConfig = ContextConfig()
        self._templates: Dict[str, PromptTemplate] = {}
    
    # -------------------------------------------------------------------------
    # Session Management
    # -------------------------------------------------------------------------
    
    async def create_session(
        self,
        user_id: str,
        context: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentSession:
        """Create a new agent session"""
        session_id = await self.db.create_session(
            user_id=user_id,
            context=context,
            metadata=metadata
        )
        
        session = AgentSession(
            id=session_id,
            user_id=user_id,
            context=context or {},
            metadata=metadata or {}
        )
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Get a session by ID"""
        data = await self.db.get_session(session_id)
        
        if data:
            return AgentSession(
                id=data["id"],
                user_id=data["user_id"],
                context=data["context"],
                state=SessionState(data["state"]),
                metadata=data["metadata"],
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"])
            )
        
        return None
    
    async def update_session(
        self,
        session_id: str,
        context: Optional[Dict[str, Any]] = None,
        state: Optional[SessionState] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update a session"""
        return await self.db.update_session(
            session_id=session_id,
            context=context,
            state=state.value if state else None,
            metadata=metadata
        )
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        state: Optional[SessionState] = None,
        limit: int = 50
    ) -> List[AgentSession]:
        """List sessions"""
        data = await self.db.list_sessions(
            user_id=user_id,
            state=state.value if state else None,
            limit=limit
        )
        
        return [
            AgentSession(
                id=s["id"],
                user_id=s["user_id"],
                context=s["context"],
                state=SessionState(s["state"]),
                metadata=s["metadata"],
                created_at=datetime.fromisoformat(s["created_at"]),
                updated_at=datetime.fromisoformat(s["updated_at"])
            )
            for s in data
        ]
    
    # -------------------------------------------------------------------------
    # Execution
    # -------------------------------------------------------------------------
    
    async def execute(
        self,
        request: AgentRequest,
        llm_provider: Any = None
    ) -> AgentResponse:
        """
        Execute an agent request.
        
        Args:
            request: Agent request
            llm_provider: LLM provider (optional, defaults to mock)
            
        Returns:
            Agent response
        """
        start_time = time.time()
        
        # Get or create session
        if request.session_id:
            session = await self.get_session(request.session_id)
            if not session:
                session = await self.create_session(request.user_id)
        else:
            session = await self.create_session(request.user_id)
        
        # Build context
        context = self._build_context(session, request)
        
        # Call LLM (mock for now)
        response_text = await self._call_llm(
            prompt=self._build_prompt(request.message, context),
            model=request.model,
            provider=llm_provider
        )
        
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Record execution
        execution_id = await self.db.create_execution(
            session_id=session.id,
            request=request.message,
            response=response_text,
            prompt_tokens=len(request.message) // 4,
            completion_tokens=len(response_text) // 4,
            duration_ms=duration_ms,
            success=True
        )
        
        # Update analytics
        await self.db.update_analytics(
            success=True,
            latency_ms=duration_ms,
            tokens=(len(request.message) + len(response_text)) // 4
        )
        
        # Update session
        await self.update_session(
            session_id=session.id,
            context=context
        )
        
        return AgentResponse(
            session_id=session.id,
            execution_id=execution_id,
            response=response_text,
            success=True,
            tokens_used=(len(request.message) + len(response_text)) // 4,
            duration_ms=duration_ms
        )
    
    async def get_execution(self, execution_id: str) -> Optional[AgentExecution]:
        """Get an execution by ID"""
        data = await self.db.get_execution(execution_id)
        
        if data:
            return AgentExecution(
                id=data["id"],
                session_id=data["session_id"],
                request=data["request"],
                response=data["response"],
                prompt_tokens=data["prompt_tokens"],
                completion_tokens=data["completion_tokens"],
                total_tokens=data["total_tokens"],
                duration_ms=data["duration_ms"],
                success=data["success"],
                error_message=data["error_message"],
                model_used=data["model_used"],
                metadata=data["metadata"],
                executed_at=datetime.fromisoformat(data["executed_at"])
            )
        
        return None
    
    async def list_executions(
        self,
        session_id: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentExecution]:
        """List executions"""
        data = await self.db.list_executions(session_id=session_id, limit=limit)
        
        return [
            AgentExecution(
                id=e["id"],
                session_id=e["session_id"],
                request=e["request"],
                response=e["response"],
                prompt_tokens=e["prompt_tokens"],
                completion_tokens=e["completion_tokens"],
                total_tokens=e["total_tokens"],
                duration_ms=e["duration_ms"],
                success=e["success"],
                error_message=e["error_message"],
                model_used=e["model_used"],
                metadata=e["metadata"],
                executed_at=datetime.fromisoformat(e["executed_at"])
            )
            for e in data
        ]
    
    # -------------------------------------------------------------------------
    # Context Management
    # -------------------------------------------------------------------------
    
    def _build_context(
        self,
        session: AgentSession,
        request: AgentRequest
    ) -> Dict[str, Any]:
        """Build context for the agent"""
        context = session.context.copy()
        
        # Apply context overrides
        for key, value in request.context_override.items():
            context[key] = value
        
        # Add request timestamp
        context["request_time"] = datetime.utcnow().isoformat()
        
        # Track message history
        if "message_history" not in context:
            context["message_history"] = []
        
        context["message_history"].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Limit history size
        max_history = self._default_context.history_turns
        context["message_history"] = context["message_history"][-max_history:]
        
        return context
    
    def _build_prompt(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> str:
        """Build the full prompt"""
        system_prompt = self._default_context.system_prompt
        
        # Include conversation history
        history = context.get("message_history", [])
        history_text = ""
        for msg in history:
            history_text += f"{msg['role']}: {msg['content']}\n"
        
        # Build final prompt
        prompt = f"{system_prompt}\n\n"
        if history_text:
            prompt += f"Conversation History:\n{history_text}\n"
        prompt += f"User: {message}\n"
        prompt += "Assistant:"
        
        return prompt
    
    async def _call_llm(
        self,
        prompt: str,
        model: Optional[str] = None,
        provider: Any = None
    ) -> str:
        """Call the LLM provider"""
        # Mock implementation - replace with actual LLM call
        if provider:
            try:
                response = await provider.complete(
                    prompt=prompt,
                    model=model,
                    max_tokens=2000
                )
                return response.content
            except Exception as e:
                return f"Error: {str(e)}"
        
        # Default mock response
        return f"I processed your message: '{prompt[-100:]}...'"
    
    # -------------------------------------------------------------------------
    # Templates
    # -------------------------------------------------------------------------
    
    async def create_template(
        self,
        name: str,
        template: str,
        description: Optional[str] = None,
        variables: Optional[List[str]] = None,
        is_default: bool = False
    ) -> PromptTemplate:
        """Create a prompt template"""
        template_id = await self.db.create_template(
            name=name,
            template=template,
            description=description,
            variables=variables,
            is_default=is_default
        )
        
        return PromptTemplate(
            id=template_id,
            name=name,
            description=description,
            template=template,
            variables=variables or [],
            is_default=is_default
        )
    
    async def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a template by name"""
        data = await self.db.get_template(name)
        
        if data:
            return PromptTemplate(
                id=data["id"],
                name=data["name"],
                description=data["description"],
                template=data["template"],
                variables=data["variables"],
                version=data["version"],
                is_default=data["is_default"],
                created_at=datetime.fromisoformat(data["created_at"]),
                updated_at=datetime.fromisoformat(data["updated_at"])
            )
        
        return None
    
    async def list_templates(self) -> List[PromptTemplate]:
        """List all templates"""
        data = await self.db.list_templates()
        
        return [
            PromptTemplate(
                id=t["id"],
                name=t["name"],
                description=t["description"],
                template=t["template"],
                variables=t["variables"],
                version=t["version"],
                is_default=t["is_default"],
                created_at=datetime.fromisoformat(t["created_at"]),
                updated_at=datetime.fromisoformat(t["updated_at"])
            )
            for t in data
        ]
    
    # -------------------------------------------------------------------------
    # Analytics
    # -------------------------------------------------------------------------
    
    async def get_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Get execution analytics"""
        data = await self.db.get_analytics(days=days)
        
        total_executions = sum(a["total_executions"] for a in data)
        successful = sum(a["successful_executions"] for a in data)
        failed = sum(a["failed_executions"] for a in data)
        total_tokens = sum(a["total_tokens"] for a in data)
        avg_latency = (
            sum(a["avg_latency_ms"] * a["total_executions"] for a in data)
            / total_executions if total_executions > 0 else 0
        )
        
        return {
            "period_days": days,
            "total_executions": total_executions,
            "successful": successful,
            "failed": failed,
            "success_rate": round(successful / total_executions * 100, 2) if total_executions > 0 else 0,
            "total_tokens": total_tokens,
            "avg_latency_ms": round(avg_latency, 2),
            "daily_breakdown": data
        }
    
    # -------------------------------------------------------------------------
    # Memory Cache
    # -------------------------------------------------------------------------
    
    async def cache_set(
        self,
        session_id: str,
        key: str,
        value: Any,
        expires_in_seconds: Optional[int] = None
    ) -> None:
        """Set a cache value"""
        await self.db.cache_set(
            session_id=session_id,
            key=key,
            value=value,
            expires_in_seconds=expires_in_seconds
        )
    
    async def cache_get(self, session_id: str, key: str) -> Any:
        """Get a cache value"""
        return await self.db.cache_get(session_id=session_id, key=key)
    
    async def cache_delete(self, session_id: str, key: str) -> None:
        """Delete a cache value"""
        await self.db.cache_delete(session_id=session_id, key=key)
    
    async def cache_clear(self, session_id: str) -> None:
        """Clear all cache for a session"""
        await self.db.cache_clear(session_id=session_id)
