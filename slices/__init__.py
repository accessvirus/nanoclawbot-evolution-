"""
Slices package - Vertical slice modules for RefactorBot.

Each slice is a self-contained module with:
- Core business logic
- SQLite database
- LLM provider for self-awareness
- Streamlit UI
"""
from .slice_base import (
    AtomicSlice,
    BaseSlice,
    SliceConfig,
    SliceCapabilities,
    SliceDatabase,
    SliceRequest,
    SliceResponse,
    SliceStatus,
    HealthStatus,
    SliceMetrics,
    SliceEvent,
    SliceEventType,
    LLMConfig,
    LLMResponse,
    ImprovementFeedback,
    ImprovementPlan,
)

__all__ = [
    "AtomicSlice",
    "BaseSlice",
    "SliceConfig",
    "SliceCapabilities",
    "SliceDatabase",
    "SliceRequest",
    "SliceResponse",
    "SliceStatus",
    "HealthStatus",
    "SliceMetrics",
    "SliceEvent",
    "SliceEventType",
    "LLMConfig",
    "LLMResponse",
    "ImprovementFeedback",
    "ImprovementPlan",
]
