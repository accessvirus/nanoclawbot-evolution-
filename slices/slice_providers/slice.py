"""
Providers Slice - Vertical Slice for Provider Management
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from ..slice_base import AtomicSlice, SliceConfig, SliceDatabase, SliceRequest, SliceResponse, SliceStatus, HealthStatus, SelfImprovementServices

logger = logging.getLogger(__name__)


class ProvidersDatabase(SliceDatabase):
    """Database manager for providers slice."""
    
    def __init__(self, db_path: str):
        super().__init__(db_path)
    
    async def initialize(self) -> None:
        """Initialize providers database schema."""
        await self.connect()
        await self._connection.execute("""
            CREATE TABLE IF NOT EXISTS providers (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                name TEXT UNIQUE NOT NULL,
                config TEXT DEFAULT '{}',
                credentials TEXT DEFAULT '{}',
                api_key TEXT,
                base_url TEXT,
                model TEXT,
                status TEXT DEFAULT 'active',
                priority INTEGER DEFAULT 0,
                created_at TEXT,
                updated_at TEXT
            )
        """)
        await self._connection.execute("""CREATE INDEX IF NOT EXISTS idx_providers_type ON providers(type)""")
        await self._connection.execute("""CREATE INDEX IF NOT EXISTS idx_providers_status ON providers(status)""")
        await self._connection.commit()


class SliceProviders(AtomicSlice):
    """Providers slice for managing LLM providers."""
    
    @property
    def slice_id(self) -> str:
        return "slice_providers"
    
    @property
    def slice_name(self) -> str:
        return "Providers Slice"
    
    @property
    def slice_version(self) -> str:
        return "1.0.0"
    
    def __init__(self, config: Optional[SliceConfig] = None):
        self._config = config or SliceConfig(slice_id="slice_providers")
        self._services: Optional[Any] = None
        self._current_request_id: str = ""
        self._status: SliceStatus = SliceStatus.INITIALIZING
        self._health: HealthStatus = HealthStatus.UNHEALTHY
        # Initialize database
        data_dir = Path("data")
        data_dir.mkdir(parents=True, exist_ok=True)
        self._database = ProvidersDatabase(str(data_dir / "providers.db"))
    
    @property
    def config(self) -> SliceConfig:
        return self._config
    
    async def execute(self, request: SliceRequest) -> SliceResponse:
        """Public execute method for slice."""
        return await self._execute_core(request)
    
    async def _execute_core(self, request: SliceRequest) -> SliceResponse:
        self._current_request_id = request.request_id
        operation = request.operation
        
        if operation == "register":
            return await self._register_provider(request.payload)
        elif operation == "get":
            return await self._get_provider(request.payload)
        elif operation == "list":
            return await self._list_providers(request.payload)
        elif operation == "update":
            return await self._update_provider(request.payload)
        elif operation == "delete":
            return await self._delete_provider(request.payload)
        elif operation == "test":
            return await self._test_provider(request.payload)
        else:
            return SliceResponse(request_id=request.request_id, success=False, payload={"error": f"Unknown operation: {operation}"})
    
    async def _register_provider(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import ProviderRegistrationServices
            if self._services is None:
                self._services = ProviderRegistrationServices(self)
            provider_id = await self._services.register_provider(
                provider_type=payload.get("provider_type", ""),
                name=payload.get("name", ""),
                config=payload.get("config", {})
            )
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"provider_id": provider_id})
        except Exception as e:
            logger.error(f"Failed to register provider: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _get_provider(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import ProviderQueryServices
            if self._services is None:
                self._services = ProviderQueryServices(self)
            provider = await self._services.get_provider(provider_id=payload.get("provider_id", ""))
            return SliceResponse(request_id=self._current_request_id, success=True, payload=provider or {})
        except Exception as e:
            logger.error(f"Failed to get provider: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _list_providers(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import ProviderQueryServices
            if self._services is None:
                self._services = ProviderQueryServices(self)
            providers = await self._services.list_providers(provider_type=payload.get("type"))
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"providers": providers})
        except Exception as e:
            logger.error(f"Failed to list providers: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _update_provider(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import ProviderManagementServices
            if self._services is None:
                self._services = ProviderManagementServices(self)
            success = await self._services.update_provider(
                provider_id=payload.get("provider_id", ""),
                config=payload.get("config", {})
            )
            return SliceResponse(request_id=self._current_request_id, success=success, payload={"updated": success})
        except Exception as e:
            logger.error(f"Failed to update provider: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _delete_provider(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import ProviderManagementServices
            if self._services is None:
                self._services = ProviderManagementServices(self)
            success = await self._services.delete_provider(provider_id=payload.get("provider_id", ""))
            return SliceResponse(request_id=self._current_request_id, success=success, payload={"deleted": success})
        except Exception as e:
            logger.error(f"Failed to delete provider: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _test_provider(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            from .core.services import ProviderTestingServices
            if self._services is None:
                self._services = ProviderTestingServices(self)
            result = await self._services.test_provider(provider_id=payload.get("provider_id", ""))
            return SliceResponse(request_id=self._current_request_id, success=result.get("success", False), payload=result)
        except Exception as e:
            logger.error(f"Failed to test provider: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def self_improve(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        improver = SelfImprovementServices(self)
        improvements = await improver.analyze_and_improve(feedback)
        return {"improvements": improvements, "message": "Providers slice self-improvement complete"}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for providers slice."""
        # Check database connection
        db_connected = False
        try:
            if self._database and self._database._connection:
                await self._database._connection.execute("SELECT 1")
                db_connected = True
        except Exception:
            db_connected = False
        
        # Check provider count
        provider_count = 0
        try:
            if db_connected:
                result = await self._database.fetchone("SELECT COUNT(*) as count FROM providers")
                provider_count = result["count"] if result else 0
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
            "provider_count": provider_count,
            "timestamp": datetime.utcnow().isoformat()
        }
