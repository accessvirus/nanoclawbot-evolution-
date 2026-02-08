"""
Agent Core Slice - Main implementation.

Full-stack slice with:
- SQLite database for sessions and executions
- LLM provider for self-awareness
- Streamlit UI for management
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic_settings import BaseSettings

from slices.slice_base import (
    AtomicSlice,
    BaseSlice,
    HealthStatus,
    ImprovementFeedback,
    ImprovementPlan,
    LLMConfig,
    SliceCapabilities,
    SliceConfig,
    SliceDatabase,
    SliceResponse,
    SliceStatus,
    SliceMetrics,
)

from .core import AgentCoreService, AgentRequest
from .database import AgentCoreDatabase


class AgentCoreConfig(SliceConfig):
    """Configuration for Agent Core Slice"""
    slice_id: str = "slice_agent_core"
    slice_name: str = "Agent Core"
    slice_version: str = "2.0.0"
    database_path: str = "data/slice_agent_core.db"
    debug: bool = False
    
    # LLM Configuration
    llm_model: str = "openai/gpt-4-turbo"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 4000


class AgentCoreSlice(BaseSlice, AtomicSlice):
    """
    Agent Core Slice - Main agent loop and context management.
    
    Owns:
    - Agent session management
    - Context building and prompt engineering
    - Execution tracking
    - Analytics
    """
    
    slice_id: str = "slice_agent_core"
    slice_name: str = "Agent Core"
    slice_version: str = "2.0.0"
    config_class = AgentCoreConfig
    
    def __init__(self, config: Optional[AgentCoreConfig] = None):
        super().__init__(config)
        self._database: Optional[AgentCoreDatabase] = None
        self._service: Optional[AgentCoreService] = None
        self._metrics = SliceMetrics(self.slice_id)
        self._status = SliceStatus.INITIALIZING
        self._llm_config = LLMConfig(
            provider="openrouter",
            model=self._config.llm_model,
            temperature=self._config.llm_temperature,
            max_tokens=self._config.llm_max_tokens,
            system_prompt="You are a helpful AI assistant."
        )
    
    @property
    def database(self) -> AgentCoreDatabase:
        if self._database is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._database
    
    @property
    def llm_config(self) -> LLMConfig:
        return self._llm_config
    
    # -------------------------------------------------------------------------
    # Lifecycle
    # -------------------------------------------------------------------------
    
    async def initialize(self) -> None:
        """Initialize the slice"""
        self._status = SliceStatus.INITIALIZING
        
        # Initialize database
        self._database = AgentCoreDatabase(
            db_path=self._config.database_path
        )
        await self._database.initialize()
        
        # Initialize service
        self._service = AgentCoreService(self._database)
        
        self._status = SliceStatus.READY
        self._health = HealthStatus.HEALTHY
    
    async def start(self) -> None:
        """Start the slice"""
        if self._status != SliceStatus.READY:
            await self.initialize()
        self._status = SliceStatus.RUNNING
    
    async def stop(self) -> None:
        """Stop the slice"""
        self._status = SliceStatus.STOPPED
    
    async def shutdown(self) -> None:
        """Shutdown the slice"""
        await self.stop()
        if self._database:
            await self._database.close()
    
    # -------------------------------------------------------------------------
    # Core Operations
    # -------------------------------------------------------------------------
    
    async def execute(
        self,
        operation: str,
        payload: Dict[str, Any],
        context: Dict[str, Any] = {}
    ) -> SliceResponse:
        """Execute an operation"""
        import time
        start_time = time.time()
        
        try:
            result: Dict[str, Any] = {}
            
            if operation == "create_session":
                session = await self._service.create_session(
                    user_id=payload["user_id"],
                    context=payload.get("context"),
                    metadata=payload.get("metadata")
                )
                result = {"session_id": session.id}
            
            elif operation == "execute":
                request = AgentRequest(
                    user_id=payload["user_id"],
                    message=payload["message"],
                    session_id=payload.get("session_id"),
                    context_override=payload.get("context_override", {}),
                    model=payload.get("model")
                )
                response = await self._service.execute(request)
                result = response.model_dump()
            
            elif operation == "get_session":
                session = await self._service.get_session(payload["session_id"])
                result = session.model_dump() if session else {}
            
            elif operation == "list_sessions":
                sessions = await self._service.list_sessions(
                    user_id=payload.get("user_id"),
                    limit=payload.get("limit", 50)
                )
                result = {"sessions": [s.model_dump() for s in sessions]}
            
            elif operation == "get_execution":
                execution = await self._service.get_execution(payload["execution_id"])
                result = execution.model_dump() if execution else {}
            
            elif operation == "list_executions":
                executions = await self._service.list_executions(
                    session_id=payload.get("session_id"),
                    limit=payload.get("limit", 100)
                )
                result = {"executions": [e.model_dump() for e in executions]}
            
            elif operation == "get_analytics":
                analytics = await self._service.get_analytics(
                    days=payload.get("days", 7)
                )
                result = analytics
            
            elif operation == "create_template":
                template = await self._service.create_template(
                    name=payload["name"],
                    template=payload["template"],
                    description=payload.get("description"),
                    variables=payload.get("variables"),
                    is_default=payload.get("is_default", False)
                )
                result = {"template_id": template.id}
            
            elif operation == "list_templates":
                templates = await self._service.list_templates()
                result = {"templates": [t.model_dump() for t in templates]}
            
            else:
                return SliceResponse(
                    request_id="",
                    success=False,
                    error_message=f"Unknown operation: {operation}"
                )
            
            latency_ms = (time.time() - start_time) * 1000
            self._metrics.record_execution(latency_ms, True)
            
            return SliceResponse(
                request_id="",
                success=True,
                payload=result,
                metadata={"latency_ms": latency_ms}
            )
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self._metrics.record_execution(latency_ms, False)
            
            return SliceResponse(
                request_id="",
                success=False,
                error_message=str(e),
                metadata={"latency_ms": latency_ms}
            )
    
    async def get_capabilities(self) -> SliceCapabilities:
        """Get slice capabilities"""
        return SliceCapabilities(
            capabilities=[
                "agent.sessions",
                "agent.execution",
                "agent.context",
                "agent.analytics",
                "agent.templates"
            ],
            supported_operations=[
                "create_session",
                "execute",
                "get_session",
                "list_sessions",
                "get_execution",
                "list_executions",
                "get_analytics",
                "create_template",
                "list_templates"
            ],
            dependencies=["slice_memory", "slice_providers"]
        )
    
    async def health_check(self) -> HealthStatus:
        """Check slice health"""
        try:
            # Check database connection
            if self._database:
                await self._database.execute("SELECT 1")
            
            # Check service
            if self._service:
                return HealthStatus.HEALTHY
            
            return HealthStatus.DEGRADED
        
        except Exception:
            return HealthStatus.UNHEALTHY
    
    # -------------------------------------------------------------------------
    # Self-Improvement
    # -------------------------------------------------------------------------
    
    async def self_improve(self, feedback: ImprovementFeedback) -> ImprovementPlan:
        """Analyze and create improvement plan"""
        improvements = []
        
        if "performance" in feedback.issue_type:
            improvements.append({
                "type": "optimization",
                "description": "Optimize context building",
                "estimated_effort": 2,
                "priority": "high"
            })
        
        if "accuracy" in feedback.issue_type:
            improvements.append({
                "type": "prompt_engineering",
                "description": "Improve prompt templates",
                "estimated_effort": 4,
                "priority": "high"
            })
        
        return ImprovementPlan(
            slice_id=self.slice_id,
            improvements=improvements,
            estimated_effort_hours=sum(i["estimated_effort"] for i in improvements),
            risk_level="low"
        )
    
    async def run_self_diagnostics(self) -> Dict[str, Any]:
        """Run self-diagnostics"""
        stats = self._metrics.get_stats()
        
        return {
            "slice_id": self.slice_id,
            "status": self._status.value,
            "health": (await self.health_check()).value,
            "database_connected": self._database is not None,
            "service_initialized": self._service is not None,
            "metrics": stats
        }
    
    # -------------------------------------------------------------------------
    # UI Methods
    # -------------------------------------------------------------------------
    
    def render_dashboard(self) -> None:
        """Render slice dashboard page"""
        from .ui.pages.dashboard import render
        render()
    
    def render_analytics(self) -> None:
        """Render analytics page"""
        from .ui.pages.analytics import render
        render()
    
    def render_config(self) -> None:
        """Render configuration page"""
        from .ui.pages.config import render
        render()
