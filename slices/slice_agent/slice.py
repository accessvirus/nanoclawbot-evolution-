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
        self._lifecycle_service: Optional[Any] = None
        self._execution_service: Optional[Any] = None
        self._query_service: Optional[Any] = None
        self._current_request_id: str = ""
        self._initialized: bool = False
    
    @property
    def config(self) -> SliceConfig:
        return self._config
    
    async def initialize(self) -> None:
        """Initialize the slice and its services."""
        if self._initialized:
            return
        from .core.services import AgentLifecycleServices, AgentExecutionServices, AgentQueryServices
        self._lifecycle_service = AgentLifecycleServices(self)
        self._execution_service = AgentExecutionServices(self)
        self._query_service = AgentQueryServices(self)
        await self._lifecycle_service.initialize()
        await self._execution_service.initialize()
        self._initialized = True
        logger.info("Agent slice initialized")
    
    async def execute(self, request: SliceRequest) -> SliceResponse:
        """Public execute method for slice."""
        if not self._initialized:
            await self.initialize()
        return await self._execute_core(request)
    
    async def _execute_core(self, request: SliceRequest) -> SliceResponse:
        """Execute agent operation."""
        self._current_request_id = request.request_id
        operation = request.operation
        payload = request.payload
        
        if operation == "create_agent":
            return await self._create_agent(payload)
        elif operation == "run_agent":
            return await self._run_agent(payload)
        elif operation == "get_agent_status":
            return await self._get_agent_status(payload)
        elif operation == "list_agents":
            return await self._list_agents(payload)
        elif operation == "delete_agent":
            return await self._delete_agent(payload)
        else:
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": f"Unknown operation: {operation}"}
            )
    
    async def _create_agent(self, payload: Dict[str, Any]) -> SliceResponse:
        """Create a new agent."""
        try:
            agent_id = await self._lifecycle_service.create_agent(
                name=payload.get("name", ""),
                instructions=payload.get("instructions", ""),
                model=payload.get("model", ""),
                tools=payload.get("tools", [])
            )
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=True,
                payload={"agent_id": agent_id}
            )
        except Exception as e:
            logger.error(f"Failed to create agent: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _run_agent(self, payload: Dict[str, Any]) -> SliceResponse:
        """Run an agent."""
        try:
            result = await self._execution_service.run_agent(
                agent_id=payload.get("agent_id", ""),
                input_text=payload.get("input", "")
            )
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=True,
                payload=result
            )
        except Exception as e:
            logger.error(f"Failed to run agent: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _get_agent_status(self, payload: Dict[str, Any]) -> SliceResponse:
        """Get agent status."""
        try:
            status = await self._lifecycle_service.get_agent_status(
                agent_id=payload.get("agent_id", "")
            )
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=True,
                payload=status or {}
            )
        except Exception as e:
            logger.error(f"Failed to get agent status: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _list_agents(self, payload: Dict[str, Any]) -> SliceResponse:
        """List all agents."""
        try:
            agents = await self._query_service.list_agents(
                status=payload.get("status")
            )
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=True,
                payload={"agents": agents}
            )
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _delete_agent(self, payload: Dict[str, Any]) -> SliceResponse:
        """Delete an agent."""
        try:
            success = await self._lifecycle_service.delete_agent(
                agent_id=payload.get("agent_id", "")
            )
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=success,
                payload={"deleted": success}
            )
        except Exception as e:
            logger.error(f"Failed to delete agent: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
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
