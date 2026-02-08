"""
Master Core - Main orchestrator for all slices.

Responsibilities:
- Slice lifecycle management
- Request routing
- Cross-slice communication
- Resource allocation
- Dashboard integration
"""
from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel

from .global_state import GlobalStateManager
from .resource_allocator import ResourceAllocator, ResourceQuota
from .dashboard_connector import DashboardConnector


class OrchestrationRequest(BaseModel):
    """Request for orchestration"""
    request_id: str = ""
    operation: str
    payload: Dict[str, Any] = {}
    context: Dict[str, Any] = {}
    required_slices: List[str] = []
    priority: int = 0
    timeout_seconds: int = 300


class OrchestrationResponse(BaseModel):
    """Response from orchestration"""
    response_id: str = ""
    request_id: str
    success: bool
    payload: Dict[str, Any] = {}
    errors: List[str] = []
    metadata: Dict[str, Any] = {}
    duration_ms: float = 0.0


class MasterCore:
    """
    Master Core AI Orchestrator.
    
    Coordinates all slices and provides:
    - Unified request handling
    - Slice lifecycle management
    - Cross-slice communication
    - Resource management
    - Dashboard integration
    """
    
    @property
    def orchestrator_id(self) -> str:
        return "master_core"
    
    @property
    def orchestrator_name(self) -> str:
        return "Master AI Orchestrator"
    
    @property
    def orchestrator_version(self) -> str:
        return "1.0.0"
    
    def __init__(
        self,
        data_dir: str = "data",
        global_state_db: str = "data/master.db",
        openrouter_api_key: Optional[str] = None
    ):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.global_state = GlobalStateManager(db_path=global_state_db)
        self.resource_allocator = ResourceAllocator()
        self.dashboard = DashboardConnector(data_dir=data_dir)
        
        self.openrouter_api_key = openrouter_api_key
        
        self._slices: Dict[str, Any] = {}  # slice_id -> slice instance
        self._slice_classes: Dict[str, Type] = {}  # slice_id -> slice class
        
        # Metrics
        self._total_requests: int = 0
        self._total_errors: int = 0
        self._total_latency_ms: float = 0.0
        self._running: bool = False
        self._start_time: Optional[datetime] = None
    
    async def initialize(self) -> bool:
        """Initialize all registered slices."""
        try:
            # Initialize all registered slices
            for slice_id in self._slice_classes:
                if slice_id not in self._slices:
                    await self.initialize_slice(slice_id)
            
            self._running = True
            self._start_time = datetime.utcnow()
            
            self.dashboard.publish_event(
                slice_id="master",
                event_type="initialized",
                description="MasterCore initialized"
            )
            
            return True
        except Exception as e:
            self.dashboard.publish_alert(
                slice_id="master",
                alert_type="error",
                title="MasterCore initialization failed",
                message=str(e)
            )
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for master core."""
        return {
            "status": "healthy",
            "orchestrator": self.orchestrator_id,
            "slices": list(self._slices.keys()),
            "running": self._running,
            "total_requests": self._total_requests,
            "total_errors": self._total_errors
        }
    
    # -------------------------------------------------------------------------
    # Slice Registration
    # -------------------------------------------------------------------------
    
    def register_slice(
        self,
        slice_id: str,
        slice_class: Type,
        quota: Optional[ResourceQuota] = None
    ) -> None:
        """
        Register a slice class with the orchestrator.
        
        Args:
            slice_id: Unique identifier for the slice
            slice_class: Class implementing AtomicSlice
            quota: Optional resource quota
        """
        self._slice_classes[slice_id] = slice_class
        
        if quota:
            self.resource_allocator.set_quota(slice_id, quota)
        
        # Update dashboard
        self.dashboard.publish_event(
            slice_id=slice_id,
            event_type="registered",
            description=f"Slice {slice_id} registered"
        )
    
    def unregister_slice(self, slice_id: str) -> bool:
        """Unregister a slice"""
        if slice_id in self._slices:
            del self._slices[slice_id]
            self.resource_allocator.release(slice_id)
            return True
        return False
    
    # -------------------------------------------------------------------------
    # Slice Lifecycle
    # -------------------------------------------------------------------------
    
    async def initialize_slice(self, slice_id: str) -> bool:
        """Initialize a slice"""
        if slice_id not in self._slice_classes:
            return False
        
        if slice_id in self._slices:
            return True  # Already initialized
        
        try:
            slice_class = self._slice_classes[slice_id]
            slice_instance = slice_class()
            
            await slice_instance.initialize()
            
            self._slices[slice_id] = slice_instance
            
            # Allocate resources
            self.resource_allocator.allocate(slice_id)
            
            # Update dashboard
            self.dashboard.update_slice_state(
                slice_id=slice_id,
                status="ready",
                health="healthy"
            )
            
            return True
        
        except Exception as e:
            self.dashboard.publish_alert(
                slice_id=slice_id,
                alert_type="error",
                title="Slice initialization failed",
                message=str(e)
            )
            return False
    
    async def start_slice(self, slice_id: str) -> bool:
        """Start a slice"""
        if slice_id not in self._slices:
            if not await self.initialize_slice(slice_id):
                return False
        
        try:
            slice_instance = self._slices[slice_id]
            await slice_instance.start()
            
            # Update dashboard
            self.dashboard.update_slice_state(
                slice_id=slice_id,
                status="running",
                health="healthy"
            )
            
            self.dashboard.publish_event(
                slice_id=slice_id,
                event_type="started",
                description=f"Slice {slice_id} started"
            )
            
            return True
        
        except Exception as e:
            self.dashboard.publish_alert(
                slice_id=slice_id,
                alert_type="error",
                title="Slice start failed",
                message=str(e)
            )
            return False
    
    async def stop_slice(self, slice_id: str) -> bool:
        """Stop a slice"""
        if slice_id not in self._slices:
            return False
        
        try:
            slice_instance = self._slices[slice_id]
            await slice_instance.stop()
            
            # Update dashboard
            self.dashboard.update_slice_state(
                slice_id=slice_id,
                status="stopped",
                health="unknown"
            )
            
            return True
        
        except Exception as e:
            self.dashboard.publish_alert(
                slice_id=slice_id,
                alert_type="error",
                title="Slice stop failed",
                message=str(e)
            )
            return False
    
    async def shutdown(self) -> None:
        """Shutdown all slices and the orchestrator"""
        self._running = False
        
        for slice_id in list(self._slices.keys()):
            await self.stop_slice(slice_id)
        
        self.dashboard.publish_event(
            slice_id="master_core",
            event_type="shutdown",
            description="Master Core shutdown complete"
        )
    
    # -------------------------------------------------------------------------
    # Request Orchestration
    # -------------------------------------------------------------------------
    
    async def orchestrate(self, request: OrchestrationRequest) -> OrchestrationResponse:
        """
        Orchestrate a request across slices.
        
        Args:
            request: Orchestration request
            
        Returns:
            Orchestration response
        """
        start_time = time.time()
        request_id = request.request_id or str(uuid.uuid4())
        
        response = OrchestrationResponse(
            response_id=str(uuid.uuid4()),
            request_id=request_id,
            success=False,
            metadata={"operation": request.operation}
        )
        
        try:
            # Determine required slices if not specified
            required_slices = request.required_slices or self._determine_slices(request.operation)
            
            if not required_slices:
                response.errors.append("No suitable slices found for operation")
                return self._finalize_response(response, start_time)
            
            # Initialize required slices
            for slice_id in required_slices:
                if slice_id not in self._slices:
                    if not await self.initialize_slice(slice_id):
                        response.errors.append(f"Failed to initialize slice: {slice_id}")
                        return self._finalize_response(response, start_time)
                
                await self.start_slice(slice_id)
            
            # Execute across slices
            slice_results = {}
            
            for slice_id in required_slices:
                slice_instance = self._slices[slice_id]
                
                try:
                    result = await asyncio.wait_for(
                        slice_instance.execute(
                            operation=request.operation,
                            payload=request.payload,
                            context=request.context
                        ),
                        timeout=request.timeout_seconds
                    )
                    
                    slice_results[slice_id] = {
                        "success": result.success,
                        "payload": result.payload,
                        "error": result.error_message
                    }
                    
                    # Track metrics
                    self.dashboard.track_execution(
                        slice_id=slice_id,
                        latency_ms=result.metadata.get("latency_ms", 0),
                        success=result.success
                    )
                    
                except asyncio.TimeoutError:
                    slice_results[slice_id] = {
                        "success": False,
                        "error": "Execution timeout"
                    }
                    self._total_errors += 1
                
                except Exception as e:
                    slice_results[slice_id] = {
                        "success": False,
                        "error": str(e)
                    }
                    self._total_errors += 1
            
            response.payload["slice_results"] = slice_results
            response.success = all(r.get("success") for r in slice_results.values())
            
            if not response.success:
                response.errors = [
                    f"{s}: {r.get('error')}"
                    for s, r in slice_results.items()
                    if not r.get("success")
                ]
        
        except Exception as e:
            response.errors.append(f"Orchestration error: {str(e)}")
            self._total_errors += 1
        
        return self._finalize_response(response, start_time)
    
    def _finalize_response(
        self,
        response: OrchestrationResponse,
        start_time: float
    ) -> OrchestrationResponse:
        """Finalize and update metrics"""
        response.duration_ms = (time.time() - start_time) * 1000
        self._total_requests += 1
        self._total_latency_ms += response.duration_ms
        
        return response
    
    def _determine_slices(self, operation: str) -> List[str]:
        """Determine which slices are needed for an operation"""
        # Simple routing based on operation prefix
        operation_map = {
            "agent": ["slice_agent"],
            "tool": ["slice_tools"],
            "memory": ["slice_memory"],
            "comm": ["slice_communication", "slice_session"],
            "session": ["slice_session"],
            "provider": ["slice_providers"],
            "skill": ["slice_skills"],
            "event": ["slice_eventbus"],
        }
        
        for prefix, slices in operation_map.items():
            if operation.lower().startswith(prefix):
                return slices
        
        # Default to agent core
        return ["slice_agent"]
    
    # -------------------------------------------------------------------------
    # Status and Metrics
    # -------------------------------------------------------------------------
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        avg_latency = (
            self._total_latency_ms / self._total_requests
            if self._total_requests > 0 else 0
        )
        
        return {
            "running": self._running,
            "start_time": self._start_time.isoformat() if self._start_time else None,
            "total_slices_registered": len(self._slice_classes),
            "total_slices_running": len(self._slices),
            "total_requests": self._total_requests,
            "total_errors": self._total_errors,
            "avg_latency_ms": round(avg_latency, 2),
            "error_rate": round(
                self._total_errors / self._total_requests
                if self._total_requests > 0 else 0,
                4
            ),
            "resource_health": self.resource_allocator.get_health_status()
        }
    
    def get_slice_status(self) -> Dict[str, Any]:
        """Get status of all slices"""
        return {
            slice_id: {
                "registered": slice_id in self._slice_classes,
                "running": slice_id in self._slices,
                "state": self.global_state.get_slice_state(slice_id),
                "resources": self.resource_allocator.get_usage(slice_id)
            }
            for slice_id in self._slice_classes
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        return {
            "orchestrator": {
                "total_requests": self._total_requests,
                "total_errors": self._total_errors,
                "total_latency_ms": round(self._total_latency_ms, 2),
                "avg_latency_ms": round(
                    self._total_latency_ms / self._total_requests
                    if self._total_requests > 0 else 0,
                    2
                )
            },
            "resources": self.resource_allocator.get_available_resources(),
            "slices": self.dashboard.get_overview()
        }
    
    # -------------------------------------------------------------------------
    # Convenience Methods
    # -------------------------------------------------------------------------
    
    async def execute(
        self,
        operation: str,
        payload: Dict[str, Any] = {},
        context: Dict[str, Any] = {}
    ) -> OrchestrationResponse:
        """
        Convenience method to execute an operation.
        
        Args:
            operation: Operation to execute
            payload: Request payload
            context: Request context
            
        Returns:
            Orchestration response
        """
        request = OrchestrationRequest(
            operation=operation,
            payload=payload,
            context=context
        )
        
        return await self.orchestrate(request)
    
    async def start(self) -> None:
        """Start the orchestrator"""
        self._running = True
        self._start_time = datetime.utcnow()
        
        self.dashboard.publish_event(
            slice_id="master_core",
            event_type="started",
            description="Master Core started"
        )
    
    def is_running(self) -> bool:
        """Check if orchestrator is running"""
        return self._running


# =============================================================================
# Factory Function
# =============================================================================

def create_master_core(
    data_dir: str = "data",
    openrouter_api_key: Optional[str] = None
) -> MasterCore:
    """
    Create and configure a Master Core instance.
    
    Args:
        data_dir: Directory for data files
        openrouter_api_key: OpenRouter API key
        
    Returns:
        Configured Master Core instance
    """
    return MasterCore(
        data_dir=data_dir,
        openrouter_api_key=openrouter_api_key
    )
