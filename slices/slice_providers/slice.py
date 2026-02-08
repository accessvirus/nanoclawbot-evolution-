"""
Providers Slice - Vertical Slice for Provider Management
"""

import logging
from typing import Any, Dict, Optional

from ..slice_base import AtomicSlice, SliceConfig, SliceRequest, SliceResponse, SelfImprovementServices

logger = logging.getLogger(__name__)


class SliceProviders(AtomicSlice):
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
        return {"status": "healthy", "slice": self.slice_id}
