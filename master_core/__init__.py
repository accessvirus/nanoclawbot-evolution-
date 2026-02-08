"""
Master Core package - Orchestrates all slices.
"""
from .master_core import MasterCore
from .global_state import GlobalStateManager
from .resource_allocator import ResourceAllocator
from .dashboard_connector import DashboardConnector

__all__ = [
    "MasterCore",
    "GlobalStateManager",
    "ResourceAllocator",
    "DashboardConnector",
]
