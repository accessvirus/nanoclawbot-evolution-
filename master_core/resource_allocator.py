"""
Resource Allocator - Manages resource allocation across slices.
"""
from __future__ import annotations

import asyncio
import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ResourceType(str, Enum):
    """Types of resources"""
    MEMORY = "memory"
    CPU = "cpu"
    TOKENS = "tokens"
    DATABASE_CONNECTIONS = "db_connections"


class ResourceStatus(str, Enum):
    """Status of resource allocation"""
    AVAILABLE = "available"
    ALLOCATED = "allocated"
    EXHAUSTED = "exhausted"


class ResourceQuota(BaseModel):
    """Resource quota configuration"""
    max_memory_mb: int = 512
    max_cpu_percent: int = 80
    max_tokens_per_minute: int = 10000
    max_db_connections: int = 10


class ResourceAllocation(BaseModel):
    """Resource allocation for a slice"""
    slice_id: str
    allocated_memory_mb: int
    allocated_cpu_percent: int
    allocated_tokens_per_minute: int
    allocated_db_connections: int
    allocated_at: datetime = datetime.utcnow()


class ResourceAllocator:
    """
    Manages resource allocation across all slices.
    Thread-safe with real-time tracking.
    """
    
    def __init__(
        self,
        total_memory_mb: int = 2048,
        total_cpu_percent: int = 100,
        total_tokens_per_minute: int = 100000,
        total_db_connections: int = 50
    ):
        self.total_memory_mb = total_memory_mb
        self.total_cpu_percent = total_cpu_percent
        self.total_tokens_per_minute = total_tokens_per_minute
        self.total_db_connections = total_db_connections
        
        self._lock = threading.Lock()
        self._quotas: Dict[str, ResourceQuota] = {}
        self._allocations: Dict[str, ResourceAllocation] = {}
        self._usage: Dict[str, Dict[str, Any]] = {}
    
    def set_quota(self, slice_id: str, quota: ResourceQuota) -> None:
        """Set resource quota for a slice"""
        with self._lock:
            self._quotas[slice_id] = quota
    
    def get_quota(self, slice_id: str) -> Optional[ResourceQuota]:
        """Get resource quota for a slice"""
        return self._quotas.get(slice_id)
    
    def allocate(
        self,
        slice_id: str,
        requested_memory_mb: int = 128,
        requested_cpu_percent: int = 20,
        requested_tokens: int = 1000,
        requested_db_connections: int = 2
    ) -> ResourceAllocation:
        """Allocate resources for a slice"""
        with self._lock:
            # Get quota or use defaults
            quota = self._quotas.get(slice_id, ResourceQuota())
            
            # Calculate actual allocation (min of requested and quota)
            allocation = ResourceAllocation(
                slice_id=slice_id,
                allocated_memory_mb=min(requested_memory_mb, quota.max_memory_mb),
                allocated_cpu_percent=min(requested_cpu_percent, quota.max_cpu_percent),
                allocated_tokens_per_minute=min(
                    requested_tokens, 
                    quota.max_tokens_per_minute
                ),
                allocated_db_connections=min(
                    requested_db_connections,
                    quota.max_db_connections
                )
            )
            
            self._allocations[slice_id] = allocation
            self._usage[slice_id] = {
                "memory_used_mb": 0,
                "cpu_used_percent": 0,
                "tokens_used": 0,
                "db_connections_used": 0
            }
            
            return allocation
    
    def update_usage(
        self,
        slice_id: str,
        memory_mb: Optional[int] = None,
        cpu_percent: Optional[int] = None,
        tokens: Optional[int] = None,
        db_connections: Optional[int] = None
    ) -> None:
        """Update resource usage for a slice"""
        with self._lock:
            if slice_id not in self._usage:
                return
            
            if memory_mb is not None:
                self._usage[slice_id]["memory_used_mb"] = memory_mb
            if cpu_percent is not None:
                self._usage[slice_id]["cpu_used_percent"] = cpu_percent
            if tokens is not None:
                self._usage[slice_id]["tokens_used"] = tokens
            if db_connections is not None:
                self._usage[slice_id]["db_connections_used"] = db_connections
    
    def get_usage(self, slice_id: str) -> Optional[Dict[str, Any]]:
        """Get resource usage for a slice"""
        return self._usage.get(slice_id)
    
    def get_all_usage(self) -> Dict[str, Dict[str, Any]]:
        """Get resource usage for all slices"""
        return dict(self._usage)
    
    def release(self, slice_id: str) -> bool:
        """Release resources for a slice"""
        with self._lock:
            if slice_id in self._allocations:
                del self._allocations[slice_id]
                del self._usage[slice_id]
                return True
            return False
    
    def get_available_resources(self) -> Dict[str, Any]:
        """Get available resources"""
        with self._lock:
            used_memory = sum(u["memory_used_mb"] for u in self._usage.values())
            used_cpu = max(u["cpu_used_percent"] for u in self._usage.values())
            used_tokens = sum(u["tokens_used"] for u in self._usage.values())
            used_db = sum(u["db_connections_used"] for u in self._usage.values())
            
            return {
                "memory": {
                    "total_mb": self.total_memory_mb,
                    "used_mb": used_memory,
                    "available_mb": self.total_memory_mb - used_memory
                },
                "cpu": {
                    "total_percent": self.total_cpu_percent,
                    "used_percent": used_cpu,
                    "available_percent": self.total_cpu_percent - used_cpu
                },
                "tokens": {
                    "total_per_minute": self.total_tokens_per_minute,
                    "used_per_minute": used_tokens,
                    "available_per_minute": self.total_tokens_per_minute - used_tokens
                },
                "db_connections": {
                    "total": self.total_db_connections,
                    "used": used_db,
                    "available": self.total_db_connections - used_db
                }
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall resource health status"""
        available = self.get_available_resources()
        
        warnings = []
        critical = []
        
        # Check memory
        mem_available = available["memory"]["available_mb"]
        mem_total = available["memory"]["total_mb"]
        if mem_available / mem_total < 0.1:
            critical.append("Memory critically low")
        elif mem_available / mem_total < 0.2:
            warnings.append("Memory running low")
        
        # Check CPU
        cpu_used = available["cpu"]["used_percent"]
        if cpu_used > 90:
            critical.append("CPU usage critically high")
        elif cpu_used > 80:
            warnings.append("CPU usage high")
        
        return {
            "status": "healthy" if not critical else "degraded" if not critical else "critical",
            "available": available,
            "warnings": warnings,
            "critical": critical,
            "slice_count": len(self._allocations)
        }
