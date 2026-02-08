"""
Agent Core Slice - Vertical Slice for Agent Core

This slice handles agent lifecycle and orchestration.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..slice_base import (
    AtomicSlice, 
    SliceConfig, 
    SliceRequest, 
    SliceResponse,
    SliceStatus,
    HealthStatus,
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
        self._status: SliceStatus = SliceStatus.INITIALIZING
        self._health: HealthStatus = HealthStatus.UNHEALTHY
    
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
        # Check database connection
        db_connected = False
        try:
            if self._database and self._database._connection:
                await self._database._connection.execute("SELECT 1")
                db_connected = True
        except Exception:
            db_connected = False
        
        # Determine overall health
        if db_connected:
            status = "healthy"
        else:
            status = "degraded"
        
        return {
            "status": status,
            "slice": self.slice_id,
            "version": self.slice_version,
            "initialized": self._status != SliceStatus.INITIALIZING,
            "database_connected": db_connected,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def run_self_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive self-diagnostics for agent slice."""
        diagnostics = {
            "slice_id": self.slice_id,
            "slice_name": self.slice_name,
            "version": self.slice_version,
            "status": self._status.value,
            "health": self._health.value,
            "initialized": self._initialized,
            "checks": [],
            "issues": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check lifecycle service
        if self._lifecycle_service:
            diagnostics["checks"].append({
                "name": "lifecycle_service",
                "status": "passed",
                "message": "Lifecycle service initialized"
            })
        else:
            diagnostics["checks"].append({
                "name": "lifecycle_service",
                "status": "warning",
                "message": "Lifecycle service not initialized"
            })
        
        # Check execution service
        if self._execution_service:
            diagnostics["checks"].append({
                "name": "execution_service",
                "status": "passed",
                "message": "Execution service initialized"
            })
        else:
            diagnostics["checks"].append({
                "name": "execution_service",
                "status": "warning",
                "message": "Execution service not initialized"
            })
        
        # Check query service
        if self._query_service:
            diagnostics["checks"].append({
                "name": "query_service",
                "status": "passed",
                "message": "Query service initialized"
            })
        else:
            diagnostics["checks"].append({
                "name": "query_service",
                "status": "warning",
                "message": "Query service not initialized"
            })
        
        # Calculate overall health
        failed_checks = [c for c in diagnostics["checks"] if c["status"] == "failed"]
        if failed_checks:
            diagnostics["overall_health"] = "unhealthy"
        elif any(c["status"] == "warning" for c in diagnostics["checks"]):
            diagnostics["overall_health"] = "degraded"
        else:
            diagnostics["overall_health"] = "healthy"
        
        # Summary
        diagnostics["summary"] = {
            "total_checks": len(diagnostics["checks"]),
            "passed": len([c for c in diagnostics["checks"] if c["status"] == "passed"]),
            "failed": len(failed_checks),
            "warnings": len([c for c in diagnostics["checks"] if c["status"] == "warning"])
        }
        
        return diagnostics
