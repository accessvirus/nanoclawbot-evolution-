"""
Observability Module for RefactorBot V2

Provides comprehensive metrics, logging, and alerting capabilities.
"""

import asyncio
import json
import logging
import sys
import time
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TypeVar
import threading

# Try to import optional dependencies
try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False

try:
    from prometheus_client import (
        Counter,
        Gauge,
        Histogram,
        Summary,
        CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


logger = logging.getLogger(__name__)


# =============================================================================
# Metrics
# =============================================================================

@dataclass
class MetricsConfig:
    """Metrics configuration."""
    enabled: bool = True
    export_interval: int = 60  # seconds
    retention_days: int = 7
    prefix: str = "refactorbot"
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """
    Central metrics collector for RefactorBot V2.
    
    Collects and exports metrics in multiple formats:
    - Prometheus
    - In-memory storage for dashboard
    """
    
    def __init__(self, config: MetricsConfig = None):
        self.config = config or MetricsConfig()
        self._counters: Dict[str, Counter] = {}
        self._gauges: Dict[str, Gauge] = {}
        self._histograms: Dict[str, Histogram] = {}
        self._summaries: Dict[str, Summary] = {}
        self._registry = CollectorRegistry()
        self._lock = threading.Lock()
        self._history: List[Dict[str, Any]] = []
        
    def _make_name(self, name: str) -> str:
        """Create full metric name with prefix."""
        return f"{self.config.prefix}_{name}" if self.config.prefix else name
    
    def counter(self, name: str, description: str = "", labels: List[str] = None):
        """Create or get a counter metric."""
        with self._lock:
            full_name = self._make_name(name)
            if full_name not in self._counters:
                if PROMETHEUS_AVAILABLE:
                    self._counters[full_name] = Counter(
                        full_name,
                        description,
                        labels or [],
                        registry=self._registry
                    )
                else:
                    self._counters[full_name] = {"value": 0, "labels": labels}
            return self._counters[full_name]
    
    def gauge(self, name: str, description: str = "", labels: List[str] = None):
        """Create or get a gauge metric."""
        with self._lock:
            full_name = self._make_name(name)
            if full_name not in self._gauges:
                if PROMETHEUS_AVAILABLE:
                    self._gauges[full_name] = Gauge(
                        full_name,
                        description,
                        labels or [],
                        registry=self._registry
                    )
                else:
                    self._gauges[full_name] = {"value": 0, "labels": labels}
            return self._gauges[full_name]
    
    def histogram(
        self,
        name: str,
        description: str = "",
        labels: List[str] = None,
        buckets: List[float] = None
    ):
        """Create or get a histogram metric."""
        with self._lock:
            full_name = self._make_name(name)
            if full_name not in self._histograms:
                if PROMETHEUS_AVAILABLE:
                    self._histograms[full_name] = Histogram(
                        full_name,
                        description,
                        labels or [],
                        buckets or [0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
                        registry=self._registry
                    )
                else:
                    self._histograms[full_name] = {"values": [], "labels": labels}
            return self._histograms[full_name]
    
    def summary(self, name: str, description: str = "", labels: List[str] = None):
        """Create or get a summary metric."""
        with self._lock:
            full_name = self._make_name(name)
            if full_name not in self._summaries:
                if PROMETHEUS_AVAILABLE:
                    self._summaries[full_name] = Summary(
                        full_name,
                        description,
                        labels or [],
                        registry=self._registry
                    )
                else:
                    self._summaries[full_name] = {"values": [], "labels": labels}
            return self._summaries[full_name]
    
    def increment(self, name: str, value: float = 1, labels: Dict[str, str] = None):
        """Increment a counter."""
        counter = self.counter(name)
        if PROMETHEUS_AVAILABLE:
            if labels:
                counter.labels(**labels).inc(value)
            else:
                counter.inc(value)
        else:
            counter["value"] += value
        
        self._record_metric(name, "counter", value, labels)
    
    def gauge_set(self, name: str, value: float, labels: Dict[str, str] = None):
        """Set a gauge value."""
        gauge = self.gauge(name)
        if PROMETHEUS_AVAILABLE:
            if labels:
                gauge.labels(**labels).set(value)
            else:
                gauge.set(value)
        else:
            gauge["value"] = value
        
        self._record_metric(name, "gauge", value, labels)
    
    def histogram_observe(self, name: str, value: float, labels: Dict[str, str] = None):
        """Observe a histogram value."""
        histogram = self.histogram(name)
        if PROMETHEUS_AVAILABLE:
            if labels:
                histogram.labels(**labels).observe(value)
            else:
                histogram.observe(value)
        else:
            histogram["values"].append(value)
        
        self._record_metric(name, "histogram", value, labels)
    
    def _record_metric(
        self,
        name: str,
        mtype: str,
        value: Any,
        labels: Optional[Dict[str, str]]
    ):
        """Record metric to history."""
        now = datetime.utcnow()
        self._history.append({
            "timestamp": now.isoformat(),
            "name": name,
            "type": mtype,
            "value": value,
            "labels": labels or {}
        })
        
        # Trim history
        cutoff = now - timedelta(days=self.config.retention_days)
        self._history = [
            m for m in self._history
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]
    
    def get_value(self, name: str) -> Optional[float]:
        """Get current value of a metric."""
        with self._lock:
            if name in self._counters:
                counter = self._counters[name]
                if PROMETHEUS_AVAILABLE:
                    return counter._value.get() if hasattr(counter, "_value") else 0
                return counter.get("value", 0)
            elif name in self._gauges:
                gauge = self._gauges[name]
                if PROMETHEUS_AVAILABLE:
                    return gauge._value.get() if hasattr(gauge, "_value") else 0
                return gauge.get("value", 0)
            return None
    
    def get_history(
        self,
        name: str,
        since: datetime = None
    ) -> List[Dict[str, Any]]:
        """Get metric history."""
        since = since or datetime.utcnow() - timedelta(days=1)
        return [
            m for m in self._history
            if m["name"] == name and
            datetime.fromisoformat(m["timestamp"]) > since
        ]
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """Get all current metrics."""
        result = {
            "counters": {},
            "gauges": {},
            "histograms": {},
            "summaries": {}
        }
        
        with self._lock:
            for name, counter in self._counters.items():
                if PROMETHEUS_AVAILABLE:
                    result["counters"][name] = counter._value.get()
                else:
                    result["counters"][name] = counter.get("value", 0)
            
            for name, gauge in self._gauges.items():
                if PROMETHEUS_AVAILABLE:
                    result["gauges"][name] = gauge._value.get()
                else:
                    result["gauges"][name] = gauge.get("value", 0)
        
        return result
    
    def get_prometheus_metrics(self) -> bytes:
        """Get metrics in Prometheus format."""
        if PROMETHEUS_AVAILABLE:
            return generate_latest(self._registry)
        return b"# Prometheus metrics not available"


# Global metrics collector
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics(config: MetricsConfig = None) -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector(config)
    return _metrics_collector


# =============================================================================
# Structured Logging
# =============================================================================

class StructuredLogger:
    """
    Structured logger for RefactorBot V2.
    
    Provides JSON-formatted logs with consistent fields.
    """
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.name = name
        self._logger = logging.getLogger(name)
        self._logger.setLevel(level)
        
        # Add handler if not already configured
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)
    
    def _log(
        self,
        level: int,
        message: str,
        extra: Dict[str, Any] = None
    ):
        """Log with structured data."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "logger": self.name,
            "level": logging.getLevelName(level),
            "message": message
        }
        
        if extra:
            log_data.update(extra)
        
        self._logger.log(level, json.dumps(log_data), extra={"structured_data": log_data})
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, kwargs)
    
    def exception(self, message: str, **kwargs):
        kwargs["exception"] = True
        self._log(logging.ERROR, message, kwargs)
    
    def performance(self, operation: str, duration: float, **kwargs):
        """Log performance metrics."""
        self._log(logging.INFO, f"Performance: {operation}", {
            "performance": True,
            "operation": operation,
            "duration_seconds": duration,
            **kwargs
        })
    
    def audit(
        self,
        action: str,
        actor: str,
        resource: str,
        result: str,
        **kwargs
    ):
        """Log audit trail."""
        self._log(logging.INFO, f"Audit: {action}", {
            "audit": True,
            "action": action,
            "actor": actor,
            "resource": resource,
            "result": result,
            **kwargs
        })


def get_logger(name: str) -> StructuredLogger:
    """Get structured logger."""
    return StructuredLogger(name)


# =============================================================================
# Alerting
# =============================================================================

@dataclass
class AlertRule:
    """Alert rule configuration."""
    name: str
    metric: str
    condition: str  # "gt", "lt", "eq", "gte", "lte"
    threshold: float
    severity: str  # "critical", "warning", "info"
    message: str
    enabled: bool = True
    cooldown_seconds: int = 300


@dataclass
class Alert:
    """Active alert."""
    alert_id: str
    rule_name: str
    severity: str
    message: str
    triggered_at: datetime
    metric_value: float
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None


class AlertingManager:
    """
    Alerting manager for RefactorBot V2.
    
    Monitors metrics and triggers alerts based on rules.
    """
    
    def __init__(self, metrics_collector: MetricsCollector = None):
        self.metrics = metrics_collector or get_metrics()
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self._alert_callbacks: List[Callable[[Alert], None]] = []
        self._lock = threading.Lock()
        self._monitoring = False
        
    def add_rule(self, rule: AlertRule):
        """Add alert rule."""
        with self._lock:
            self.rules[rule.name] = rule
    
    def remove_rule(self, name: str):
        """Remove alert rule."""
        with self._lock:
            self.rules.pop(name, None)
    
    def register_callback(self, callback: Callable[[Alert], None]):
        """Register alert callback."""
        self._alert_callbacks.append(callback)
    
    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition."""
        if condition == "gt":
            return value > threshold
        elif condition == "lt":
            return value < threshold
        elif condition == "eq":
            return value == threshold
        elif condition == "gte":
            return value >= threshold
        elif condition == "lte":
            return value <= threshold
        return False
    
    async def check_rules(self):
        """Check all alert rules."""
        with self._lock:
            rules = list(self.rules.values())
        
        for rule in rules:
            if not rule.enabled:
                continue
            
            # Check if alert is in cooldown
            alert_key = f"{rule.name}:{rule.metric}"
            if alert_key in self.active_alerts:
                alert = self.active_alerts[alert_key]
                if (datetime.utcnow() - alert.triggered_at).total_seconds() < rule.cooldown_seconds:
                    continue
            
            # Get metric value
            value = self.metrics.get_value(rule.metric)
            if value is None:
                continue
            
            # Evaluate condition
            if self._evaluate_condition(value, rule.condition, rule.threshold):
                await self._trigger_alert(rule, value)
    
    async def _trigger_alert(self, rule: AlertRule, value: float):
        """Trigger an alert."""
        alert = Alert(
            alert_id=f"alert-{int(time.time())}",
            rule_name=rule.name,
            severity=rule.severity,
            message=rule.message,
            triggered_at=datetime.utcnow(),
            metric_value=value
        )
        
        with self._lock:
            self.active_alerts[rule.name] = alert
        
        # Call callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception:
                pass
        
        logger.warning(f"Alert triggered: {rule.name} - {rule.message}")
    
    async def acknowledge_alert(
        self,
        rule_name: str,
        acknowledged_by: str = "system"
    ) -> bool:
        """Acknowledge an active alert."""
        with self._lock:
            if rule_name not in self.active_alerts:
                return False
            
            alert = self.active_alerts[rule_name]
            alert.acknowledged = True
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by
            return True
    
    def get_active_alerts(self, severity: str = None) -> List[Alert]:
        """Get active alerts."""
        with self._lock:
            alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return sorted(alerts, key=lambda a: a.triggered_at, reverse=True)
    
    async def start_monitoring(self, interval: float = 60.0):
        """Start background monitoring."""
        self._monitoring = True
        
        async def _monitor():
            while self._monitoring:
                try:
                    await self.check_rules()
                except Exception as e:
                    logger.error(f"Alert monitoring error: {e}")
                await asyncio.sleep(interval)
        
        asyncio.create_task(_monitor())
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self._monitoring = False


# =============================================================================
# Performance Tracing
# =============================================================================

class PerformanceTracer:
    """
    Performance tracer for tracking operation timing.
    """
    
    def __init__(self, metrics_collector: MetricsCollector = None):
        self.metrics = metrics_collector or get_metrics()
        self._operations: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
    
    @contextmanager
    def trace(self, operation: str, labels: Dict[str, str] = None):
        """Context manager for tracing an operation."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.record(operation, duration, labels)
    
    def record(
        self,
        operation: str,
        duration: float,
        labels: Dict[str, str] = None
    ):
        """Record operation duration."""
        with self._lock:
            self._operations[operation].append(duration)
        
        # Update metrics
        self.metrics.histogram_observe(f"{operation}_duration", duration, labels)
        self.metrics.gauge_set(f"{operation}_last_duration", duration, labels)
    
    def get_stats(self, operation: str) -> Optional[Dict[str, float]]:
        """Get statistics for an operation."""
        with self._lock:
            values = self._operations.get(operation, [])
            if not values:
                return None
        
        values.sort()
        return {
            "count": len(values),
            "min": values[0],
            "max": values[-1],
            "avg": sum(values) / len(values),
            "p50": values[len(values) // 2],
            "p95": values[int(len(values) * 0.95)],
            "p99": values[int(len(values) * 0.99)]
        }
    
    def clear(self, operation: str = None):
        """Clear recorded operations."""
        with self._lock:
            if operation:
                self._operations[operation].clear()
            else:
                self._operations.clear()


# =============================================================================
# Health Checks
# =============================================================================

class HealthChecker:
    """
    Health check manager for RefactorBot V2.
    
    Registers and runs health checks for components.
    """
    
    def __init__(self):
        self._checks: Dict[str, Callable[[], Any]] = {}
        self._results: Dict[str, Dict[str, Any]] = {}
    
    def register(self, name: str, check_fn: Callable[[], Any]):
        """Register a health check."""
        self._checks[name] = check_fn
    
    async def run_check(self, name: str) -> Dict[str, Any]:
        """Run a specific health check."""
        if name not in self._checks:
            return {"status": "unknown", "error": "Check not found"}
        
        try:
            result = self._checks[name]()
            if asyncio.iscoroutine(result):
                result = await result
            
            self._results[name] = {
                "status": "healthy" if result else "unhealthy",
                "timestamp": datetime.utcnow().isoformat()
            }
            return self._results[name]
        except Exception as e:
            self._results[name] = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            return self._results[name]
    
    async def run_all(self) -> Dict[str, Dict[str, Any]]:
        """Run all health checks."""
        results = {}
        for name in self._checks:
            results[name] = await self.run_check(name)
        return results
    
    def get_status(self) -> str:
        """Get overall status."""
        if not self._results:
            return "unknown"
        
        statuses = [r["status"] for r in self._results.values()]
        
        if "error" in statuses:
            return "error"
        if "unhealthy" in statuses:
            return "degraded"
        if "healthy" in statuses:
            return "healthy"
        return "unknown"


# =============================================================================
# Decorators
# =============================================================================

def trace_operation(metrics_collector: MetricsCollector = None):
    """Decorator to trace function execution."""
    tracer = PerformanceTracer(metrics_collector)
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            with tracer.trace(func.__name__):
                return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            with tracer.trace(func.__name__):
                return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def track_metric(metric_name: str, metrics_collector: MetricsCollector = None):
    """Decorator to track function calls."""
    metrics = metrics_collector or get_metrics()
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            metrics.increment(metric_name)
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            metrics.increment(metric_name)
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
