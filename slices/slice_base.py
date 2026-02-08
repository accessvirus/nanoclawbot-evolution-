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


T = TypeVar("T", bound="AtomicSlice")


class SliceCapabilities(BaseModel):
    """Capabilities of a slice"""
    capabilities: List[str] = []
    supported_operations: List[str] = []
    dependencies: List[str] = []


# =============================================================================
# Request/Response Models
# =============================================================================

class SliceRequest(BaseModel):
    """Base request for slice execution"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slice_id: str
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
        raise NotImplementedError()
    
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
    
    @property
    def database(self) -> SliceDatabase:
        """Slice's SQLite database"""
        ...
    
    @property
    def llm_config(self) -> LLMConfig:
        """Slice's LLM configuration"""
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
    
    async def get_capabilities(self) -> SliceCapabilities:
        """Get slice capabilities"""
        ...
    
    async def health_check(self) -> HealthStatus:
        """Check slice health"""
        ...
    
    # -------------------------------------------------------------------------
    # Self-Improvement Methods
    # -------------------------------------------------------------------------
    
    async def self_improve(self, feedback: ImprovementFeedback) -> ImprovementPlan:
        """Analyze and create improvement plan"""
        ...
    
    async def run_self_diagnostics(self) -> Dict[str, Any]:
        """Run self-diagnostics"""
        ...
    
    # -------------------------------------------------------------------------
    # UI Methods
    # -------------------------------------------------------------------------
    
    def render_dashboard(self) -> None:
        """Render slice dashboard page"""
        ...
    
    def render_analytics(self) -> None:
        """Render analytics page"""
        ...
    
    def render_config(self) -> None:
        """Render configuration page"""
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
        return self._version
    
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
    
    async def get_capabilities(self) -> SliceCapabilities:
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
        """Run self-diagnostics"""
        return {
            "slice_id": self.slice_id,
            "status": self._status.value,
            "health": self._health.value,
            "database_connected": self._database is not None
        }


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
