"""
Session Slice - Vertical Slice for Session Management
"""

import logging
from typing import Any, Dict, Optional

from ..slice_base import AtomicSlice, SliceConfig, SliceRequest, SliceResponse, SelfImprovementServices

logger = logging.getLogger(__name__)


class SliceSession(AtomicSlice):
    @property
    def slice_id(self) -> str:
        return "slice_session"
    
    @property
    def slice_name(self) -> str:
        return "Session Slice"
    
    @property
    def slice_version(self) -> str:
        return "1.0.0"
    
    def __init__(self, config: Optional[SliceConfig] = None):
        self._config = config or SliceConfig(slice_id="slice_session")
        self._services: Optional[Any] = None
        self._current_request_id: str = ""
    
    @property
    def config(self) -> SliceConfig:
        return self._config
    
    async def execute(self, request: SliceRequest) -> SliceResponse:
        """Public execute method for slice."""
        return await self._execute_core(request)
    
    async def _execute_core(self, request: SliceRequest) -> SliceResponse:
        self._current_request_id = request.request_id
        operation = request.operation
        
        if operation == "create":
            return await self._create_session(request.payload)
        elif operation == "get":
            return await self._get_session(request.payload)
        elif operation == "update":
            return await self._update_session(request.payload)
        elif operation == "end":
            return await self._end_session(request.payload)
        elif operation == "list":
            return await self._list_sessions(request.payload)
        else:
            return SliceResponse(request_id=request.request_id, success=False, payload={"error": f"Unknown operation: {operation}"})
    
    async def _create_session(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import SessionCreationServices
            if self._services is None:
                self._services = SessionCreationServices(self)
            session_id = await self._services.create_session(
                user_id=payload.get("user_id", ""),
                metadata=payload.get("metadata")
            )
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"session_id": session_id})
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _get_session(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import SessionQueryServices
            if self._services is None:
                self._services = SessionQueryServices(self)
            session = await self._services.get_session(session_id=payload.get("session_id", ""))
            return SliceResponse(request_id=self._current_request_id, success=True, payload=session or {})
        except Exception as e:
            logger.error(f"Failed to get session: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _update_session(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import SessionManagementServices
            if self._services is None:
                self._services = SessionManagementServices(self)
            success = await self._services.update_session(
                session_id=payload.get("session_id", ""),
                data=payload.get("data", {})
            )
            return SliceResponse(request_id=self._current_request_id, success=success, payload={"updated": success})
        except Exception as e:
            logger.error(f"Failed to update session: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _end_session(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import SessionManagementServices
            if self._services is None:
                self._services = SessionManagementServices(self)
            success = await self._services.end_session(session_id=payload.get("session_id", ""))
            return SliceResponse(request_id=self._current_request_id, success=success, payload={"ended": success})
        except Exception as e:
            logger.error(f"Failed to end session: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _list_sessions(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import SessionQueryServices
            if self._services is None:
                self._services = SessionQueryServices(self)
            sessions = await self._services.list_sessions(user_id=payload.get("user_id"))
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"sessions": sessions})
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def self_improve(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        improver = SelfImprovementServices(self)
        improvements = await improver.analyze_and_improve(feedback)
        return {"improvements": improvements, "message": "Session slice self-improvement complete"}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for session slice."""
        # Check database connection
        db_connected = False
        try:
            if self._database and self._database._connection:
                await self._database._connection.execute("SELECT 1")
                db_connected = True
        except Exception:
            db_connected = False
        
        # Check session count
        session_count = 0
        try:
            if db_connected:
                result = await self._database.fetchone("SELECT COUNT(*) as count FROM sessions")
                session_count = result["count"] if result else 0
        except Exception:
            pass
        
        # Determine overall health
        if db_connected:
            status = "healthy"
        else:
            status = "degraded"
        
        return {
            "status": status,
            "slice": self.slice_id,
            "version": self.slice_version,
            "initialized": self._status != SliceStatus.INITIALIZING,
            "database_connected": db_connected,
            "session_count": session_count,
            "timestamp": datetime.utcnow().isoformat()
        }
