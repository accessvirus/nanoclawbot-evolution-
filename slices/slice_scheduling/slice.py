"""
Scheduling Slice - Vertical Slice for Task Scheduling

This slice handles scheduled task execution, cron jobs, and heartbeat monitoring.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..slice_base import AtomicSlice, SliceConfig, SliceDatabase, SliceRequest, SliceResponse, SliceStatus, HealthStatus, SelfImprovementServices

logger = logging.getLogger(__name__)


@dataclass
class ScheduledTask:
    """Represents a scheduled task."""
    id: str = ""
    name: str = ""
    description: str = ""
    task_type: str = ""  # "cron", "interval", "once"
    cron_expression: str = ""  # Cron format: "*/5 * * * *" (every 5 minutes)
    interval_seconds: int = 0  # For interval-based tasks
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    payload: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    execution_timeout: int = 300  # seconds
    status: str = "pending"  # pending, running, completed, failed
    created_at: str = ""
    updated_at: str = ""


class SchedulingConfig(SliceConfig):
    """Scheduling slice configuration."""
    default_timeout: int = 300
    max_concurrent_tasks: int = 10
    timezone: str = "UTC"
    enable_heartbeat: bool = True
    heartbeat_interval: int = 60


class SchedulingDatabase(SliceDatabase):
    """Database manager for scheduling slice."""
    
    def __init__(self, db_path: str):
        super().__init__(db_path)
    
    async def initialize(self) -> None:
        """Initialize scheduling database schema."""
        await self.connect()
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                task_type TEXT NOT NULL,
                cron_expression TEXT,
                interval_seconds INTEGER DEFAULT 0,
                next_run TEXT,
                last_run TEXT,
                payload TEXT DEFAULT '{}',
                enabled BOOLEAN DEFAULT 1,
                max_retries INTEGER DEFAULT 3,
                retry_delay INTEGER DEFAULT 60,
                execution_timeout INTEGER DEFAULT 300,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                updated_at TEXT
            )
        """)
        await self._connection.execute("""CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_next_run ON scheduled_tasks(next_run)""")
        await self._connection.execute("""CREATE INDEX IF NOT EXISTS idx_scheduled_tasks_status ON scheduled_tasks(status)""")
        await self._connection.commit()


class SliceScheduling(AtomicSlice):
    """
    Scheduling slice for task management.
    
    Responsibilities:
    - Task scheduling (cron, interval, one-time)
    - Task execution
    - Heartbeat monitoring
    - Retry handling
    """
    
    @property
    def slice_id(self) -> str:
        return "slice_scheduling"
    
    @property
    def slice_name(self) -> str:
        return "Scheduling Slice"
    
    @property
    def slice_version(self) -> str:
        return "1.0.0"
    
    def __init__(self, config: Optional[SchedulingConfig] = None):
        if config is None:
            config = SchedulingConfig()
            config.slice_id = "slice_scheduling"
        self._config = config
        self._services: Optional[Any] = None
        self._current_request_id: str = ""
        self._scheduler_task: Optional[asyncio.Task] = None
        self._running = False
        self._status: SliceStatus = SliceStatus.INITIALIZING
        self._health: HealthStatus = HealthStatus.UNHEALTHY
        
        # Initialize database
        data_dir = Path("data")
        data_dir.mkdir(parents=True, exist_ok=True)
        self._database = SchedulingDatabase(str(data_dir / "scheduling.db"))
    
    @property
    def config(self) -> SchedulingConfig:
        return self._config
    
    async def initialize(self) -> None:
        """Initialize the scheduler."""
        if self._running:
            return
        
        from .core.services import TaskSchedulingServices, HeartbeatServices
        self._services = TaskSchedulingServices(self)
        await self._services.initialize()
        
        # Start the scheduler
        self._running = True
        self._scheduler_task = asyncio.create_task(self._run_scheduler())
        
        logger.info("Scheduling slice initialized")
    
    async def _run_scheduler(self):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._services.run_scheduled_tasks()
                await asyncio.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(5)
    
    async def execute(
        self,
        request: Optional[SliceRequest] = None,
        *,
        operation: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None
    ) -> SliceResponse:
        """Public execute method for slice."""
        # Handle keyword arguments for convenience
        if request is None:
            request = SliceRequest(
                operation=operation or "",
                payload=payload or {}
            )
        if not self._running:
            await self.initialize()
        return await self._execute_core(request)
    
    async def _execute_core(self, request: SliceRequest) -> SliceResponse:
        """Execute scheduling operation."""
        self._current_request_id = request.request_id
        operation = request.operation
        
        if operation == "create_task" or operation == "schedule_task":
            return await self._create_task(request.payload)
        elif operation == "get_task":
            return await self._get_task(request.payload)
        elif operation == "list_tasks":
            return await self._list_tasks(request.payload)
        elif operation == "update_task":
            return await self._update_task(request.payload)
        elif operation == "delete_task":
            return await self._delete_task(request.payload)
        elif operation == "run_task":
            return await self._run_task(request.payload)
        elif operation == "pause_task":
            return await self._pause_task(request.payload)
        elif operation == "resume_task":
            return await self._resume_task(request.payload)
        elif operation == "get_heartbeat_status":
            return await self._get_heartbeat_status(request.payload)
        else:
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": f"Unknown operation: {operation}"}
            )
    
    async def _create_task(self, payload: Dict[str, Any]) -> SliceResponse:
        """Create a scheduled task."""
        try:
            from .core.services import TaskSchedulingServices
            if self._services is None:
                self._services = TaskSchedulingServices(self)
            
            task_id = await self._services.create_task(
                name=payload.get("name", ""),
                description=payload.get("description", ""),
                task_type=payload.get("task_type", "interval"),
                cron_expression=payload.get("cron_expression"),
                interval_seconds=payload.get("interval_seconds", 0),
                payload=payload.get("payload", {}),
                enabled=payload.get("enabled", True)
            )
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=True,
                payload={"task_id": task_id}
            )
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _get_task(self, payload: Dict[str, Any]) -> SliceResponse:
        """Get a scheduled task."""
        try:
            from .core.services import TaskSchedulingServices
            if self._services is None:
                self._services = TaskSchedulingServices(self)
            
            task = await self._services.get_task(payload.get("task_id", ""))
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=True,
                payload=task or {}
            )
        except Exception as e:
            logger.error(f"Failed to get task: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _list_tasks(self, payload: Dict[str, Any]) -> SliceResponse:
        """List all scheduled tasks."""
        try:
            from .core.services import TaskSchedulingServices
            if self._services is None:
                self._services = TaskSchedulingServices(self)
            
            tasks = await self._services.list_tasks(
                status=payload.get("status"),
                task_type=payload.get("task_type")
            )
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=True,
                payload={"tasks": tasks}
            )
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _update_task(self, payload: Dict[str, Any]) -> SliceResponse:
        """Update a scheduled task."""
        try:
            from .core.services import TaskSchedulingServices
            if self._services is None:
                self._services = TaskSchedulingServices(self)
            
            success = await self._services.update_task(
                task_id=payload.get("task_id", ""),
                updates=payload.get("updates", {})
            )
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=success,
                payload={"updated": success}
            )
        except Exception as e:
            logger.error(f"Failed to update task: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _delete_task(self, payload: Dict[str, Any]) -> SliceResponse:
        """Delete a scheduled task."""
        try:
            from .core.services import TaskSchedulingServices
            if self._services is None:
                self._services = TaskSchedulingServices(self)
            
            success = await self._services.delete_task(payload.get("task_id", ""))
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=success,
                payload={"deleted": success}
            )
        except Exception as e:
            logger.error(f"Failed to delete task: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _run_task(self, payload: Dict[str, Any]) -> SliceResponse:
        """Manually run a task."""
        try:
            from .core.services import TaskSchedulingServices
            if self._services is None:
                self._services = TaskSchedulingServices(self)
            
            result = await self._services.run_task_now(payload.get("task_id", ""))
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=result.get("success", False),
                payload=result
            )
        except Exception as e:
            logger.error(f"Failed to run task: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _pause_task(self, payload: Dict[str, Any]) -> SliceResponse:
        """Pause a scheduled task."""
        try:
            from .core.services import TaskSchedulingServices
            if self._services is None:
                self._services = TaskSchedulingServices(self)
            
            success = await self._services.pause_task(payload.get("task_id", ""))
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=success,
                payload={"paused": success}
            )
        except Exception as e:
            logger.error(f"Failed to pause task: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _resume_task(self, payload: Dict[str, Any]) -> SliceResponse:
        """Resume a paused task."""
        try:
            from .core.services import TaskSchedulingServices
            if self._services is None:
                self._services = TaskSchedulingServices(self)
            
            success = await self._services.resume_task(payload.get("task_id", ""))
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=success,
                payload={"resumed": success}
            )
        except Exception as e:
            logger.error(f"Failed to resume task: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def _get_heartbeat_status(self, payload: Dict[str, Any]) -> SliceResponse:
        """Get heartbeat status."""
        try:
            from .core.services import HeartbeatServices
            if self._services is None:
                self._services = HeartbeatServices(self)
            
            status = await self._services.get_status()
            
            return SliceResponse(
                request_id=self._current_request_id,
                success=True,
                payload=status
            )
        except Exception as e:
            logger.error(f"Failed to get heartbeat status: {e}")
            return SliceResponse(
                request_id=self._current_request_id,
                success=False,
                payload={"error": str(e)}
            )
    
    async def self_improve(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        """Self-improvement for scheduling slice."""
        improver = SelfImprovementServices(self)
        improvements = await improver.analyze_and_improve(feedback)
        return {
            "improvements": improvements,
            "message": "Scheduling slice self-improvement complete"
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for scheduling slice."""
        # Check database connection
        db_connected = False
        try:
            if self._database and self._database._connection:
                await self._database._connection.execute("SELECT 1")
                db_connected = True
        except Exception:
            db_connected = False
        
        # Check scheduled tasks count
        task_count = 0
        try:
            if db_connected:
                result = await self._database.fetchone("SELECT COUNT(*) as count FROM scheduled_tasks")
                task_count = result["count"] if result else 0
        except Exception:
            pass
        
        # Determine overall health
        if db_connected and self._running:
            status = "healthy"
        elif self._running:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return {
            "status": status,
            "slice": self.slice_id,
            "version": self.slice_version,
            "initialized": self._status != SliceStatus.INITIALIZING,
            "database_connected": db_connected,
            "running": self._running,
            "task_count": task_count,
            "timestamp": datetime.utcnow().isoformat()
        }
