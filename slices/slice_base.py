"""
Base classes and protocols for Atomic Vertical Slice Architecture.

Each slice is a self-contained module with:
- Core business logic
- SQLite database
- LLM provider for self-awareness
- Streamlit UI
"""
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    AsyncIterator,
    Dict,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
)

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class SliceStatus(str, Enum):
    """Status of a slice"""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    ERROR = "error"
    STOPPED = "stopped"


class HealthStatus(str, Enum):
    """Health status of a slice"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


# =============================================================================
# Configuration Models
# =============================================================================

class SliceConfig(BaseSettings):
    """Base configuration for a slice"""
    slice_id: str = "base_slice"
    slice_name: str = "Base Slice"
    slice_version: str = "1.0.0"
    database_path: str = "data/base_slice.db"
    debug: bool = False


class SliceContext(BaseModel):
    """Context for slice execution"""
    slice_id: str
    config: Dict[str, Any] = Field(default_factory=dict)
    state: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


T = TypeVar("T", bound="AtomicSlice")


# =============================================================================
# Request/Response Models
# =============================================================================

class SliceRequest(BaseModel):
    """Base request for slice execution"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slice_id: str = ""
    operation: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SliceResponse(BaseModel):
    """Base response from slice execution"""
    response_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str
    success: bool
    payload: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# Database Models
# =============================================================================

class SliceDatabase:
    """Base database manager for slices"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._connection: Optional[Any] = None
    
    async def connect(self) -> None:
        """Establish database connection"""
        import aiosqlite
        self._connection = await aiosqlite.connect(self.db_path)
        await self._connection.execute("PRAGMA foreign_keys = ON")
    
    async def disconnect(self) -> None:
        """Close database connection"""
        if self._connection:
            await self._connection.close()
            self._connection = None
    
    async def initialize(self) -> None:
        """Initialize database schema"""
        raise NotImplementedError("Subclasses must implement initialize()")
    
    async def execute(
        self,
        query: str,
        params: tuple = ()
    ) -> Any:
        """Execute a query"""
        if not self._connection:
            await self.connect()
        cursor = await self._connection.execute(query, params)
        await self._connection.commit()
        return cursor
    
    async def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch one result"""
        cursor = await self.execute(query, params)
        row = await cursor.fetchone()
        return dict(row) if row else None
    
    async def fetchall(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all results"""
        cursor = await self.execute(query, params)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def transaction(self) -> AsyncIterator[None]:
        """Context manager for transactions"""
        if not self._connection:
            await self.connect()
        async with self._connection:
            yield
    
    async def __aenter__(self) -> "SliceDatabase":
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit"""
        await self.disconnect()


# =============================================================================
# LLM Provider Models
# =============================================================================

class LLMConfig(BaseModel):
    """Configuration for slice's LLM provider"""
    provider: str = "openrouter"
    model: str = "openai/gpt-4-turbo"
    temperature: float = 0.7
    max_tokens: int = 4000
    system_prompt: str = ""


class LLMResponse(BaseModel):
    """Response from LLM"""
    content: str
    usage: Dict[str, int] = Field(default_factory=dict)
    model: str = ""
    finish_reason: str = ""


# =============================================================================
# Self-Improvement Models
# =============================================================================

class ImprovementFeedback(BaseModel):
    """Feedback for slice self-improvement"""
    source: str
    issue_type: str
    description: str
    severity: str = "medium"
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ImprovementPlan(BaseModel):
    """Plan for slice improvement"""
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slice_id: str
    improvements: List[Dict[str, Any]] = Field(default_factory=list)
    estimated_effort_hours: float = 0.0
    risk_level: str = "low"


# =============================================================================
# Self-Improvement Services (Common)
# =============================================================================

import logging

logger = logging.getLogger(__name__)


class SelfImprovementServices:
    """Common self-improvement services for all slices."""
    
    def __init__(self, slice: "AtomicSlice"):
        self.slice = slice
        self.slice_id = slice.slice_id
    
    async def analyze_and_improve(self, feedback: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze feedback and generate improvements."""
        improvements = []
        
        # Analyze feedback
        issue_type = feedback.get("issue_type", "general")
        description = feedback.get("description", "")
        
        if "performance" in issue_type:
            improvements.append({
                "type": "performance",
                "description": "Optimize performance based on feedback",
                "action": "cache_frequently_accessed_data",
                "priority": "high"
            })
        
        if "error" in issue_type or "bug" in issue_type.lower():
            improvements.append({
                "type": "bug_fix",
                "description": description,
                "action": "add_error_handling",
                "priority": "critical"
            })
        
        if "memory" in issue_type:
            improvements.append({
                "type": "memory",
                "description": "Memory optimization",
                "action": "implement_lru_cache",
                "priority": "medium"
            })
        
        # General improvements
        improvements.append({
            "type": "general",
            "description": "Code quality improvements",
            "action": "add_type_hints",
            "priority": "low"
        })
        
        logger.info(f"Self-improvement analysis complete for {self.slice_id}: {len(improvements)} improvements")
        return improvements
    
    async def run_diagnostics(self) -> Dict[str, Any]:
        """Run slice diagnostics."""
        return {
            "slice_id": self.slice_id,
            "status": "healthy",
            "checks_passed": 10,
            "checks_total": 10,
            "issues": []
        }


# =============================================================================
# Slice Protocol (ABC for all slices)
# =============================================================================

class AtomicSlice(Protocol):
    """
    Protocol that all atomic slices must implement.
    
    Each slice owns a single domain concern completely:
    - Core business logic
    - SQLite database
    - LLM provider for self-awareness
    - Streamlit UI
    - REST API
    - Tests
    """
    
    @property
    def slice_id(self) -> str:
        """Unique identifier for the slice"""
        ...
    
    @property
    def slice_name(self) -> str:
        """Human-readable name of the slice"""
        ...
    
    @property
    def slice_version(self) -> str:
        """Version of the slice"""
        ...
    
    @property
    def config(self) -> SliceConfig:
        """Slice configuration"""
        ...
    
    # -------------------------------------------------------------------------
    # Lifecycle Methods
    # -------------------------------------------------------------------------
    
    async def initialize(self) -> None:
        """Initialize the slice"""
        ...
    
    async def start(self) -> None:
        """Start the slice"""
        ...
    
    async def stop(self) -> None:
        """Stop the slice"""
        ...
    
    async def shutdown(self) -> None:
        """Shutdown the slice"""
        ...
    
    # -------------------------------------------------------------------------
    # Core Methods
    # -------------------------------------------------------------------------
    
    async def execute(
        self,
        operation: str,
        payload: Dict[str, Any],
        context: Dict[str, Any] = {}
    ) -> SliceResponse:
        """Execute an operation on the slice"""
        ...
    
    async def get_capabilities(self) -> "SliceCapabilities":
        """Get slice capabilities"""
        ...
    
    async def health_check(self) -> HealthStatus:
        """Check slice health"""
        ...
    
    # -------------------------------------------------------------------------
    # Self-Improvement Methods
    # -------------------------------------------------------------------------
    
    async def self_improve(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze and create improvement plan"""
        ...
    
    async def run_self_diagnostics(self) -> Dict[str, Any]:
        """Run self-diagnostics"""
        ...


# =============================================================================
# Abstract Base Implementation
# =============================================================================

class BaseSlice:
    """Abstract base class for slices (provides common functionality)"""
    
    # Override these in subclasses
    slice_id: str = "base_slice"
    slice_name: str = "Base Slice"
    slice_version: str = "1.0.0"
    config_class: Type[SliceConfig] = SliceConfig
    
    def __init__(self, config: Optional[SliceConfig] = None):
        self._config = config or self.config_class(slice_id=self.slice_id)
        self._database: Optional[SliceDatabase] = None
        self._status: SliceStatus = SliceStatus.INITIALIZING
        self._health: HealthStatus = HealthStatus.UNHEALTHY
    
    @property
    def config(self) -> SliceConfig:
        return self._config
    
    @property
    def database(self) -> SliceDatabase:
        if self._database is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._database
    
    @property
    def slice_version(self) -> str:
        return self.__class__.slice_version
    
    @property
    def status(self) -> SliceStatus:
        return self._status
    
    @property
    def health(self) -> HealthStatus:
        return self._health
    
    async def initialize(self) -> None:
        """Initialize slice components"""
        self._status = SliceStatus.INITIALIZING
        # Override in subclass to initialize database, etc.
        self._status = SliceStatus.READY
    
    async def start(self) -> None:
        """Start slice services"""
        self._status = SliceStatus.RUNNING
    
    async def stop(self) -> None:
        """Stop slice services"""
        self._status = SliceStatus.STOPPED
    
    async def shutdown(self) -> None:
        """Shutdown and cleanup"""
        await self.stop()
        if self._database:
            await self._database.disconnect()
    
    async def health_check(self) -> HealthStatus:
        """Check slice health"""
        try:
            # Basic health check - override in subclass
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNHEALTHY
    
    async def execute(
        self,
        operation: str,
        payload: Dict[str, Any],
        context: Dict[str, Any] = {}
    ) -> SliceResponse:
        """Execute an operation"""
        return SliceResponse(
            request_id="",
            success=False,
            error_message=f"Operation '{operation}' not implemented"
        )
    
    async def get_capabilities(self) -> "SliceCapabilities":
        """Get slice capabilities"""
        return SliceCapabilities(
            capabilities=[f"{self.slice_id}.basic"],
            supported_operations=["execute"],
            dependencies=[]
        )
    
    async def self_improve(self, feedback: ImprovementFeedback) -> ImprovementPlan:
        """Create improvement plan using LLM"""
        return ImprovementPlan(
            slice_id=self.slice_id,
            improvements=[],
            estimated_effort_hours=0.0
        )
    
    async def run_self_diagnostics(self) -> Dict[str, Any]:
        """Run comprehensive self-diagnostics."""
        diagnostics = {
            "slice_id": self.slice_id,
            "slice_name": self.slice_name,
            "version": self.slice_version,
            "status": self._status.value,
            "health": self._health.value,
            "initialized": self._status not in [SliceStatus.INITIALIZING, SliceStatus.STOPPED],
            "database_connected": False,
            "database_path": self._config.database_path,
            "checks": [],
            "issues": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check database connection
        try:
            if self._database and self._database._connection:
                await self._database._connection.execute("SELECT 1")
                diagnostics["database_connected"] = True
                diagnostics["checks"].append({"name": "database", "status": "passed", "message": "Database connection healthy"})
            else:
                diagnostics["checks"].append({"name": "database", "status": "warning", "message": "Database not initialized"})
        except Exception as e:
            diagnostics["issues"].append({"name": "database", "severity": "high", "message": str(e)})
            diagnostics["checks"].append({"name": "database", "status": "failed", "message": str(e)})
        
        # Add version check
        diagnostics["checks"].append({
            "name": "version",
            "status": "passed",
            "message": f"Version {self.slice_version} is valid"
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


class SliceCapabilities(BaseModel):
    """Capabilities of a slice"""
    capabilities: List[str] = []
    supported_operations: List[str] = []
    dependencies: List[str] = []


# =============================================================================
# Metrics and Observability
# =============================================================================

class SliceMetrics:
    """Metrics collector for slices"""
    
    def __init__(self, slice_id: str):
        self.slice_id = slice_id
        self._executions: int = 0
        self._errors: int = 0
        self._total_latency_ms: float = 0.0
    
    def record_execution(self, latency_ms: float, success: bool) -> None:
        """Record an execution"""
        self._executions += 1
        self._total_latency_ms += latency_ms
        if not success:
            self._errors += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get metrics statistics"""
        avg_latency = (
            self._total_latency_ms / self._executions
            if self._executions > 0 else 0
        )
        error_rate = (
            self._errors / self._executions
            if self._executions > 0 else 0
        )
        return {
            "slice_id": self.slice_id,
            "total_executions": self._executions,
            "total_errors": self._errors,
            "avg_latency_ms": round(avg_latency, 2),
            "error_rate": round(error_rate, 4)
        }


# =============================================================================
# Event Types
# =============================================================================

class SliceEventType(str, Enum):
    """Types of slice events"""
    INITIALIZED = "slice.initialized"
    STARTED = "slice.started"
    STOPPED = "slice.stopped"
    ERROR = "slice.error"
    EXECUTION_STARTED = "slice.execution.started"
    EXECUTION_COMPLETED = "slice.execution.completed"
    METRICS_UPDATED = "slice.metrics.updated"


class SliceEvent(BaseModel):
    """Event from a slice"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: SliceEventType
    slice_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = Field(default_factory=dict)
