"""
Dashboard Connector - Connects Master Core to Streamlit Dashboard.

Provides real-time data streaming for the dashboard.
"""
from __future__ import annotations

import asyncio
import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from pydantic import BaseModel


class DashboardMetric(BaseModel):
    """Metric to display on dashboard"""
    metric_id: str
    slice_id: str
    metric_type: str  # "counter", "gauge", "histogram"
    name: str
    value: float
    unit: str = ""
    timestamp: datetime = datetime.utcnow()
    metadata: Dict[str, Any] = {}


class DashboardAlert(BaseModel):
    """Alert to display on dashboard"""
    alert_id: str
    slice_id: str
    alert_type: str  # "error", "warning", "info"
    title: str
    message: str
    timestamp: datetime = datetime.utcnow()
    acknowledged: bool = False


class DashboardEvent(BaseModel):
    """Event to display on dashboard"""
    event_id: str
    slice_id: str
    event_type: str
    description: str
    timestamp: datetime = datetime.utcnow()
    metadata: Dict[str, Any] = {}


class DashboardConnector:
    """
    Connects Master Core to Streamlit Dashboard.
    Provides real-time data streaming via file-based message queue.
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self._metrics_file = self.data_dir / "dashboard_metrics.jsonl"
        self._alerts_file = self.data_dir / "dashboard_alerts.jsonl"
        self._events_file = self.data_dir / "dashboard_events.jsonl"
        self._state_file = self.data_dir / "dashboard_state.json"
        
        self._lock = threading.Lock()
        self._subscribers: List[Callable] = []
        self._metrics_buffer: List[DashboardMetric] = []
        self._alerts_buffer: List[DashboardAlert] = []
        
        # Initialize files
        self._init_files()
    
    def _init_files(self) -> None:
        """Initialize dashboard files"""
        for f in [self._metrics_file, self._alerts_file, self._events_file]:
            if not f.exists():
                f.touch()
        
        if not self._state_file.exists():
            self._save_state({"slices": {}, "last_update": None})
    
    def _save_state(self, state: Dict[str, Any]) -> None:
        """Save dashboard state"""
        with self._lock:
            state["last_update"] = datetime.utcnow().isoformat()
            with open(self._state_file, "w") as f:
                json.dump(state, f)
    
    def _load_state(self) -> Dict[str, Any]:
        """Load dashboard state"""
        with self._lock:
            if self._state_file.exists():
                with open(self._state_file, "r") as f:
                    return json.load(f)
            return {"slices": {}, "last_update": None}
    
    # -------------------------------------------------------------------------
    # Metrics
    # -------------------------------------------------------------------------
    
    def publish_metric(
        self,
        slice_id: str,
        metric_type: str,
        name: str,
        value: float,
        unit: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Publish a metric to the dashboard"""
        metric = DashboardMetric(
            metric_id=f"{slice_id}_{name}_{datetime.utcnow().timestamp()}",
            slice_id=slice_id,
            metric_type=metric_type,
            name=name,
            value=value,
            unit=unit,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._metrics_buffer.append(metric)
            
            # Write to file
            with open(self._metrics_file, "a") as f:
                f.write(metric.model_dump_json() + "\n")
            
            # Notify subscribers
            for callback in self._subscribers:
                try:
                    callback("metric", metric)
                except Exception:
                    pass
    
    def track_cost(
        self,
        slice_id: str,
        cost: float,
        model: str = ""
    ) -> None:
        """Track LLM cost for a slice"""
        self.publish_metric(
            slice_id=slice_id,
            metric_type="counter",
            name="llm_cost",
            value=cost,
            unit="USD",
            metadata={"model": model}
        )
    
    def track_execution(
        self,
        slice_id: str,
        latency_ms: float,
        success: bool
    ) -> None:
        """Track slice execution"""
        self.publish_metric(
            slice_id=slice_id,
            metric_type="histogram",
            name="execution_latency",
            value=latency_ms,
            unit="ms",
            metadata={"success": success}
        )
    
    def track_tokens(
        self,
        slice_id: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> None:
        """Track token usage"""
        total = prompt_tokens + completion_tokens
        self.publish_metric(
            slice_id=slice_id,
            metric_type="counter",
            name="tokens_used",
            value=total,
            unit="tokens",
            metadata={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens
            }
        )
    
    # -------------------------------------------------------------------------
    # Alerts
    # -------------------------------------------------------------------------
    
    def publish_alert(
        self,
        slice_id: str,
        alert_type: str,
        title: str,
        message: str
    ) -> str:
        """Publish an alert to the dashboard"""
        alert = DashboardAlert(
            alert_id=f"{slice_id}_{alert_type}_{datetime.utcnow().timestamp()}",
            slice_id=slice_id,
            alert_type=alert_type,
            title=title,
            message=message
        )
        
        with self._lock:
            self._alerts_buffer.append(alert)
            
            # Write to file
            with open(self._alerts_file, "a") as f:
                f.write(alert.model_dump_json() + "\n")
            
            # Notify subscribers
            for callback in self._subscribers:
                try:
                    callback("alert", alert)
                except Exception:
                    pass
        
        return alert.alert_id
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        alerts = []
        acknowledged = False
        
        with self._lock:
            if self._alerts_file.exists():
                with open(self._alerts_file, "r") as f:
                    for line in f:
                        if line.strip():
                            alert = DashboardAlert.model_validate_json(line)
                            if alert.alert_id == alert_id:
                                alert.acknowledged = True
                                acknowledged = True
                            alerts.append(alert)
                
                if acknowledged:
                    with open(self._alerts_file, "w") as f:
                        for alert in alerts:
                            f.write(alert.model_dump_json() + "\n")
        
        return acknowledged
    
    # -------------------------------------------------------------------------
    # Events
    # -------------------------------------------------------------------------
    
    def publish_event(
        self,
        slice_id: str,
        event_type: str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish an event to the dashboard"""
        event = DashboardEvent(
            event_id=f"{slice_id}_{event_type}_{datetime.utcnow().timestamp()}",
            slice_id=slice_id,
            event_type=event_type,
            description=description,
            metadata=metadata or {}
        )
        
        with self._lock:
            # Write to file
            with open(self._events_file, "a") as f:
                f.write(event.model_dump_json() + "\n")
            
            # Notify subscribers
            for callback in self._subscribers:
                try:
                    callback("event", event)
                except Exception:
                    pass
        
        return event.event_id
    
    # -------------------------------------------------------------------------
    # Slice State Updates
    # -------------------------------------------------------------------------
    
    def update_slice_state(
        self,
        slice_id: str,
        status: str,
        health: str,
        metrics: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update slice state for dashboard"""
        state = self._load_state()
        
        state["slices"][slice_id] = {
            "slice_id": slice_id,
            "status": status,
            "health": health,
            "metrics": metrics or {},
            "last_update": datetime.utcnow().isoformat()
        }
        
        self._save_state(state)
        
        self.publish_event(
            slice_id=slice_id,
            event_type="state_change",
            description=f"Slice status changed to {status}",
            metadata={"status": status, "health": health}
        )
    
    # -------------------------------------------------------------------------
    # Data Retrieval
    # -------------------------------------------------------------------------
    
    def get_metrics(
        self,
        slice_id: Optional[str] = None,
        metric_name: Optional[str] = None,
        limit: int = 100
    ) -> List[DashboardMetric]:
        """Get metrics from dashboard"""
        metrics = []
        
        with self._lock:
            if self._metrics_file.exists():
                with open(self._metrics_file, "r") as f:
                    for line in f:
                        if line.strip():
                            metric = DashboardMetric.model_validate_json(line)
                            
                            if slice_id and metric.slice_id != slice_id:
                                continue
                            if metric_name and metric.name != metric_name:
                                continue
                            
                            metrics.append(metric)
        
        return metrics[-limit:]
    
    def get_alerts(
        self,
        slice_id: Optional[str] = None,
        acknowledged: Optional[bool] = None,
        limit: int = 50
    ) -> List[DashboardAlert]:
        """Get alerts from dashboard"""
        alerts = []
        
        with self._lock:
            if self._alerts_file.exists():
                with open(self._alerts_file, "r") as f:
                    for line in f:
                        if line.strip():
                            alert = DashboardAlert.model_validate_json(line)
                            
                            if slice_id and alert.slice_id != slice_id:
                                continue
                            if acknowledged is not None and alert.acknowledged != acknowledged:
                                continue
                            
                            alerts.append(alert)
        
        return alerts[-limit:]
    
    def get_events(
        self,
        slice_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[DashboardEvent]:
        """Get events from dashboard"""
        events = []
        
        with self._lock:
            if self._events_file.exists():
                with open(self._events_file, "r") as f:
                    for line in f:
                        if line.strip():
                            event = DashboardEvent.model_validate_json(line)
                            
                            if slice_id and event.slice_id != slice_id:
                                continue
                            if event_type and event.event_type != event_type:
                                continue
                            
                            events.append(event)
        
        return events[-limit:]
    
    def get_slice_states(self) -> Dict[str, Any]:
        """Get all slice states"""
        return self._load_state()["slices"]
    
    def get_overview(self) -> Dict[str, Any]:
        """Get dashboard overview"""
        states = self.get_slice_states()
        alerts = self.get_alerts(acknowledged=False)
        
        healthy = sum(1 for s in states.values() if s.get("health") == "healthy")
        degraded = sum(1 for s in states.values() if s.get("health") == "degraded")
        unhealthy = sum(1 for s in states.values() if s.get("health") == "unhealthy")
        
        return {
            "total_slices": len(states),
            "healthy_slices": healthy,
            "degraded_slices": degraded,
            "unhealthy_slices": unhealthy,
            "unacknowledged_alerts": len(alerts),
            "last_update": datetime.utcnow().isoformat()
        }
    
    # -------------------------------------------------------------------------
    # Subscription
    # -------------------------------------------------------------------------
    
    def subscribe(self, callback: Callable) -> None:
        """Subscribe to dashboard updates"""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable) -> None:
        """Unsubscribe from dashboard updates"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    # -------------------------------------------------------------------------
    # Cleanup
    # -------------------------------------------------------------------------
    
    def clear_old_data(self, days: int = 7) -> int:
        """Clear data older than specified days"""
        import time
        
        cutoff = datetime.utcnow().timestamp() - (days * 24 * 60 * 60)
        cleared = 0
        
        with self._lock:
            for file_path, model_class in [
                (self._metrics_file, DashboardMetric),
                (self._alerts_file, DashboardAlert),
                (self._events_file, DashboardEvent)
            ]:
                if file_path.exists():
                    lines = []
                    with open(file_path, "r") as f:
                        for line in f:
                            if line.strip():
                                obj = model_class.model_validate_json(line)
                                if obj.timestamp.timestamp() > cutoff:
                                    lines.append(line)
                    
                    with open(file_path, "w") as f:
                        f.writelines(lines)
                    
                    cleared += len(lines)
        
        return cleared
