"""
Slices Package - Vertical Slice Architecture for RefactorBot
"""

from .slice_base import AtomicSlice, SliceConfig, SliceRequest, SliceResponse, SliceContext, SelfImprovementServices

__all__ = [
    "AtomicSlice",
    "SliceConfig", 
    "SliceRequest",
    "SliceResponse",
    "SliceContext",
    "SelfImprovementServices"
]
