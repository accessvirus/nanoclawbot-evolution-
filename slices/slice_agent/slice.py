"""
Agent Core Slice - Vertical Slice for Agent Core

This slice handles agent lifecycle and orchestration.
"""

import logging
from typing import Any, Dict, Optional

from ..slice_base import (
    AtomicSlice, 
    SliceConfig, 
    SliceRequest, 
    SliceResponse,
    SelfImprovementServices
)

logger = logging.getLogger(__name__)


class SliceAgent(AtomicSlice):
    """
    Agent Core slice for managing AI agents.
    
    Responsibilities:
    - Agent lifecycle management
    - Agent configuration
    - Agent execution
    """
    
    # Protocol properties
    @property
    def slice_id(self) -> str:
        return "slice_agent"
    
    @property
    def slice_name(self) -> str:
        return "Agent Core Slice"
    
    @property
    def slice_version(self) -> str:
        return "1.0.0"
    
    def __init__(self, config: Optional[SliceConfig] = None):
        self._config = config or SliceConfig(slice_id="slice_agent")
        self._services: Optional[Any] = None
    
    @property
    def config(self) -> SliceConfig:
        return self._config
    
    async def _execute_core(self, request: SliceRequest) -> SliceResponse:
        """Execute agent operation."""
        operation = request.operation
        
        if operation == "create_agent":
            return await self._create_agent(request.payload)
        elif operation == "run_agent":
            return await self._run_agent(request.payload)
        elif operation == "get_agent_status":
            return await self._get_agent_status(request.payload)
        elif operation == "list_agents":
            return await self._list_agents(request.payload)
        elif operation == "delete_agent":
            return await self._delete_agent(request.payload)
        else:
            return SliceResponse(
                request_id=request.request_id,
                success=False,
                payload={"error": f"Unknown operation: {operation}"}
            )
    
    async def _create_agent(self, payload: Dict[str, Any]) -> SliceResponse:
        """Create a new agent."""
        try:
            from .core.services import AgentLifecycleServices
            if self._services is None:
                self._services = AgentLifecycleServices(self)
            
            agent_id = await self._services.create_agent(
                name=payload.get("name", ""),
                instructions=payload.get("instructions", ""),
                model=payload.get("model", ""),
                tools=payload.get("tools", [])
            )
            
            return SliceResponse(
                request_id=request.request_id,
                success=True,
                payload={"agent_id": agent_id}
            )
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            return SliceResponse(
                request_id=request.request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _run_agent(self, payload: Dict[str, Any]) -> SliceResponse:
        """Run an agent."""
        try:
            from .core.services import AgentExecutionServices
            if self._services is None:
                self._services = AgentExecutionServices(self)
            
            result = await self._services.run_agent(
                agent_id=payload.get("agent_id", ""),
                input_text=payload.get("input", "")
            )
            
            return SliceResponse(
                request_id=request.request_id,
                success=True,
                payload=result
            )
        except Exception as e:
            logger.error(f"Failed to run agent: {e}")
            return SliceResponse(
                request_id=request.request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _get_agent_status(self, payload: Dict[str, Any]) -> SliceResponse:
        """Get agent status."""
        try:
            from .core.services import AgentLifecycleServices
            if self._services is None:
                self._services = AgentLifecycleServices(self)
            
            status = await self._services.get_agent_status(
                agent_id=payload.get("agent_id", "")
            )
            
            return SliceResponse(
                request_id=request.request_id,
                success=True,
                payload=status
            )
        except Exception as e:
            logger.error(f"Failed to get agent status: {e}")
            return SliceResponse(
                request_id=request.request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _list_agents(self, payload: Dict[str, Any]) -> SliceResponse:
        """List all agents."""
        try:
            from .core.services import AgentQueryServices
            if self._services is None:
                self._services = AgentQueryServices(self)
            
            agents = await self._services.list_agents(
                status=payload.get("status")
            )
            
            return SliceResponse(
                request_id=request.request_id,
                success=True,
                payload={"agents": agents}
            )
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return SliceResponse(
                request_id=request.request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _delete_agent(self, payload: Dict[str, Any]) -> SliceResponse:
        """Delete an agent."""
        try:
            from .core.services import AgentLifecycleServices
            if self._services is None:
                self._services = AgentLifecycleServices(self)
            
            success = await self._services.delete_agent(
                agent_id=payload.get("agent_id", "")
            )
            
            return SliceResponse(
                request_id=request.request_id,
                success=success,
                payload={"deleted": success}
            )
        except Exception as e:
            logger.error(f"Failed to delete agent: {e}")
            return SliceResponse(
                request_id=request.request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def self_improve(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Self-improvement for agent core slice."""
        improver = SelfImprovementServices(self)
        improvements = await improver.analyze_and_improve(feedback)
        return {
            "improvements": improvements,
            "message": "Agent core slice self-improvement complete"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for agent core slice."""
        return {
            "status": "healthy",
            "slice": self.slice_id,
            "version": self.slice_version
        }
