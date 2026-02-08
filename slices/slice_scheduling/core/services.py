"""
Scheduling Core Services - Service Layer for Scheduling Slice

Implements task scheduling, cron parsing, and heartbeat monitoring.
"""

import asyncio
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskSchedulingServices:
    """Service for task scheduling management."""
    
    def __init__(self, slice: Any):
        self.slice = slice
        self.db = getattr(slice, '_database', None)
        self._tasks: Dict[str, Dict] = {}
    
    async def initialize(self) -> None:
        """Initialize and load tasks from database."""
        if self.db:
            await self.db.initialize()
            await self._load_tasks()
    
    async def _load_tasks(self) -> None:
        """Load tasks from database."""
        if self.db:
            rows = await self.db.fetchall("SELECT * FROM scheduled_tasks")
            for row in rows:
                self._tasks[row["id"]] = dict(row)
    
    async def create_task(
        self,
        name: str,
        description: str,
        task_type: str,
        cron_expression: Optional[str],
        interval_seconds: int,
        payload: Dict[str, Any],
        enabled: bool
    ) -> str:
        """Create a new scheduled task."""
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        
        # Calculate next run
        next_run = self._calculate_next_run(task_type, cron_expression, interval_seconds)
        
        task_data = {
            "id": task_id,
            "name": name,
            "description": description,
            "task_type": task_type,
            "cron_expression": cron_expression or "",
            "interval_seconds": interval_seconds,
            "next_run": next_run.isoformat() if next_run else None,
            "last_run": None,
            "payload": str(payload),
            "enabled": enabled,
            "max_retries": 3,
            "retry_delay": 60,
            "execution_timeout": 300,
            "status": "pending",
            "created_at": now,
            "updated_at": now
        }
        
        if self.db:
            await self.db.execute(
                """INSERT INTO scheduled_tasks 
                   (id, name, description, task_type, cron_expression, interval_seconds, 
                    next_run, payload, enabled, max_retries, retry_delay, execution_timeout, 
                    status, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (task_id, name, description, task_type, cron_expression or "", interval_seconds,
                 next_run.isoformat() if next_run else None, str(payload), enabled, 3, 60, 300,
                 "pending", now, now)
            )
            await self.db.commit()
        
        self._tasks[task_id] = task_data
        logger.info(f"Created task: {task_id} ({name})")
        return task_id
    
    def _calculate_next_run(
        self,
        task_type: str,
        cron_expression: Optional[str],
        interval_seconds: int
    ) -> Optional[datetime]:
        """Calculate next run time."""
        now = datetime.utcnow()
        
        if task_type == "once":
            return None  # One-time task
        
        elif task_type == "interval":
            return now + timedelta(seconds=interval_seconds)
        
        elif task_type == "cron":
            return self._parse_cron_next(cron_expression, now)
        
        return None
    
    def _parse_cron_next(self, cron_expression: str, now: datetime) -> datetime:
        """Parse cron expression and calculate next run time."""
        # Simple cron parser (supports: minute hour day month day-of-week)
        parts = cron_expression.split()
        
        if len(parts) < 5:
            return now + timedelta(hours=1)  # Default: 1 hour
        
        minute, hour, day, month, dow = parts[:5]
        
        # Find next matching time
        current = now.replace(second=0, microsecond=0)
        
        for _ in range(366):  # Check up to 1 year ahead
            if self._cron_matches(parts, current):
                return current
            current += timedelta(minutes=1)
        
        return now + timedelta(hours=1)
    
    def _cron_matches(self, parts: List[str], dt: datetime) -> bool:
        """Check if datetime matches cron expression."""
        minute, hour, day, month, dow = parts[:5]
        
        return (
            self._matches_field(minute, dt.minute, 0, 59) and
            self._matches_field(hour, dt.hour, 0, 23) and
            self._matches_field(day, dt.day, 1, 31) and
            self._matches_field(month, dt.month, 1, 12) and
            self._matches_field(dow, dt.weekday(), 0, 6)
        )
    
    def _matches_field(self, field: str, value: int, min_val: int, max_val: int) -> bool:
        """Check if field matches value."""
        if field == "*":
            return True
        
        if "/" in field:
            base, step = field.split("/")
            base = int(base) if base != "*" else min_val
            step = int(step)
            return (value - base) % step == 0
        
        if "," in field:
            return any(self._matches_field(f, value, min_val, max_val) for f in field.split(","))
        
        if "-" in field:
            start, end = map(int, field.split("-"))
            return start <= value <= end
        
        try:
            return int(field) == value
        except ValueError:
            return True
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get a task by ID."""
        return self._tasks.get(task_id)
    
    async def list_tasks(
        self,
        status: Optional[str] = None,
        task_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all tasks."""
        tasks = list(self._tasks.values())
        
        if status:
            tasks = [t for t in tasks if t.get("status") == status]
        if task_type:
            tasks = [t for t in tasks if t.get("task_type") == task_type]
        
        return tasks
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """Update a task."""
        if task_id not in self._tasks:
            return False
        
        task = self._tasks[task_id]
        now = datetime.utcnow().isoformat()
        
        for key, value in updates.items():
            if key in task:
                task[key] = value
        
        task["updated_at"] = now
        
        # Recalculate next run if schedule changed
        if "cron_expression" in updates or "interval_seconds" in updates:
            next_run = self._calculate_next_run(
                task["task_type"],
                task.get("cron_expression"),
                task.get("interval_seconds", 0)
            )
            task["next_run"] = next_run.isoformat() if next_run else None
        
        if self.db:
            await self.db.execute(
                "UPDATE scheduled_tasks SET next_run = ?, updated_at = ? WHERE id = ?",
                (task.get("next_run"), now, task_id)
            )
            await self.db.commit()
        
        return True
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id not in self._tasks:
            return False
        
        del self._tasks[task_id]
        
        if self.db:
            await self.db.execute("DELETE FROM scheduled_tasks WHERE id = ?", (task_id,))
            await self.db.commit()
        
        logger.info(f"Deleted task: {task_id}")
        return True
    
    async def pause_task(self, task_id: str) -> bool:
        """Pause a task."""
        return await self.update_task(task_id, {"enabled": False, "status": "paused"})
    
    async def resume_task(self, task_id: str) -> bool:
        """Resume a paused task."""
        return await self.update_task(task_id, {"enabled": True, "status": "pending"})
    
    async def run_task_now(self, task_id: str) -> Dict[str, Any]:
        """Run a task immediately."""
        task = self._tasks.get(task_id)
        if not task:
            return {"success": False, "error": "Task not found"}
        
        # Execute the task
        try:
            await self._execute_task(task)
            return {"success": True, "task_id": task_id, "message": "Task executed"}
        except Exception as e:
            return {"success": False, "task_id": task_id, "error": str(e)}
    
    async def run_scheduled_tasks(self) -> None:
        """Run all due tasks."""
        now = datetime.utcnow()
        
        for task_id, task in list(self._tasks.items()):
            if not task.get("enabled", True):
                continue
            
            if task.get("status") == "running":
                continue
            
            next_run_str = task.get("next_run")
            if not next_run_str:
                continue
            
            try:
                next_run = datetime.fromisoformat(next_run_str)
                if now >= next_run:
                    asyncio.create_task(self._execute_with_retry(task))
            except Exception as e:
                logger.error(f"Error checking task {task_id}: {e}")
    
    async def _execute_with_retry(self, task: Dict[str, Any]) -> None:
        """Execute task with retry logic."""
        task_id = task["id"]
        max_retries = task.get("max_retries", 3)
        retry_delay = task.get("retry_delay", 60)
        
        # Update status to running
        await self.update_task(task_id, {"status": "running"})
        
        for attempt in range(max_retries):
            try:
                await self._execute_task(task)
                await self.update_task(task_id, {"status": "completed", "last_run": datetime.utcnow().isoformat()})
                return
            except Exception as e:
                logger.error(f"Task {task_id} attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(retry_delay)
        
        await self.update_task(task_id, {"status": "failed"})
    
    async def _execute_task(self, task: Dict[str, Any]) -> None:
        """Execute a task based on its type."""
        task_type = task.get("task_type")
        payload = task.get("payload", {})
        
        if task_type == "http_request":
            await self._execute_http_task(payload)
        elif task_type == "agent_run":
            await self._execute_agent_task(payload)
        elif task_type == "slice_execute":
            await self._execute_slice_task(payload)
        else:
            logger.info(f"Executing generic task: {task['name']}")
        
        # Calculate next run
        next_run = self._calculate_next_run(
            task_type,
            task.get("cron_expression"),
            task.get("interval_seconds", 0)
        )
        
        await self.update_task(
            task["id"],
            {"next_run": next_run.isoformat() if next_run else None}
        )
    
    async def _execute_http_task(self, payload: Dict[str, Any]) -> None:
        """Execute HTTP request task."""
        import httpx
        url = payload.get("url")
        method = payload.get("method", "GET")
        
        async with httpx.AsyncClient() as client:
            if method == "GET":
                await client.get(url)
            elif method == "POST":
                await client.post(url, json=payload.get("json"))
    
    async def _execute_agent_task(self, payload: Dict[str, Any]) -> None:
        """Execute agent run task."""
        agent_id = payload.get("agent_id")
        input_text = payload.get("input")
        
        # This would call the agent slice
        logger.info(f"Running agent {agent_id} with input: {input_text}")
    
    async def _execute_slice_task(self, payload: Dict[str, Any]) -> None:
        """Execute slice operation task."""
        slice_id = payload.get("slice_id")
        operation = payload.get("operation")
        
        logger.info(f"Executing slice {slice_id} operation: {operation}")


class HeartbeatServices:
    """Service for heartbeat monitoring."""
    
    def __init__(self, slice: Any):
        self.slice = slice
        self.db = getattr(slice, '_database', None)
        self._beats: Dict[str, Dict] = {}
        self._last_check = datetime.utcnow()
    
    async def register_heartbeat(
        self,
        component_id: str,
        component_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register a component for heartbeat monitoring."""
        beat_id = f"beat_{uuid.uuid4().hex[:8]}"
        now = datetime.utcnow().isoformat()
        
        beat_data = {
            "id": beat_id,
            "component_id": component_id,
            "component_type": component_type,
            "last_beat": now,
            "status": "alive",
            "metadata": str(metadata or {}),
            "created_at": now
        }
        
        self._beats[component_id] = beat_data
        logger.info(f"Registered heartbeat: {component_id}")
        return beat_id
    
    async def record_beat(self, component_id: str) -> bool:
        """Record a heartbeat for a component."""
        if component_id not in self._beats:
            return False
        
        self._beats[component_id]["last_beat"] = datetime.utcnow().isoformat()
        self._beats[component_id]["status"] = "alive"
        return True
    
    async def check_heartbeats(self, timeout_seconds: int = 300) -> Dict[str, Any]:
        """Check all heartbeats and report stale ones."""
        now = datetime.utcnow()
        stale = []
        alive = []
        
        for component_id, beat in self._beats.items():
            last_beat = datetime.fromisoformat(beat["last_beat"])
            if (now - last_beat).total_seconds() > timeout_seconds:
                beat["status"] = "stale"
                stale.append(component_id)
            else:
                alive.append(component_id)
        
        return {
            "alive": alive,
            "stale": stale,
            "total": len(self._beats),
            "checked_at": now.isoformat()
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get heartbeat system status."""
        result = await self.check_heartbeats()
        return {
            "components": len(self._beats),
            "alive": len(result["alive"]),
            "stale": len(result["stale"]),
            "last_check": result["checked_at"]
        }
    
    async def unregister_heartbeat(self, component_id: str) -> bool:
        """Unregister a component from heartbeat monitoring."""
        if component_id in self._beats:
            del self._beats[component_id]
            return True
        return False
