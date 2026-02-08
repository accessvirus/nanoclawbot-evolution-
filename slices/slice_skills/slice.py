"""
Skills Slice - Vertical Slice for Skills Management
"""

import logging
from typing import Any, Dict, Optional

from ..slice_base import AtomicSlice, SliceConfig, SliceRequest, SliceResponse, SelfImprovementServices

logger = logging.getLogger(__name__)


class SliceSkills(AtomicSlice):
    @property
    def slice_id(self) -> str:
        return "slice_skills"
    
    @property
    def slice_name(self) -> str:
        return "Skills Slice"
    
    @property
    def slice_version(self) -> str:
        return "1.0.0"
    
    def __init__(self, config: Optional[SliceConfig] = None):
        self._config = config or SliceConfig(slice_id="slice_skills")
        self._registration_service: Optional[Any] = None
        self._query_service: Optional[Any] = None
        self._management_service: Optional[Any] = None
        self._execution_service: Optional[Any] = None
        self._current_request_id: str = ""
        self._initialized: bool = False
    
    @property
    def config(self) -> SliceConfig:
        return self._config
    
    async def initialize(self) -> None:
        """Initialize the slice and its services."""
        if self._initialized:
            return
        from .core.services import (
            SkillRegistrationServices,
            SkillQueryServices,
            SkillManagementServices,
            SkillExecutionServices
        )
        self._registration_service = SkillRegistrationServices(self)
        self._query_service = SkillQueryServices(self)
        self._management_service = SkillManagementServices(self)
        self._execution_service = SkillExecutionServices(self)
        await self._registration_service.initialize()
        await self._execution_service.initialize()
        self._initialized = True
        logger.info("Skills slice initialized")
    
    async def execute(self, request: SliceRequest) -> SliceResponse:
        """Public execute method for slice."""
        if not self._initialized:
            await self.initialize()
        return await self._execute_core(request)
    
    async def _execute_core(self, request: SliceRequest) -> SliceResponse:
        self._current_request_id = request.request_id
        operation = request.operation
        
        if operation == "register":
            return await self._register_skill(request.payload)
        elif operation == "get":
            return await self._get_skill(request.payload)
        elif operation == "list":
            return await self._list_skills(request.payload)
        elif operation == "update":
            return await self._update_skill(request.payload)
        elif operation == "delete":
            return await self._delete_skill(request.payload)
        elif operation == "execute":
            return await self._execute_skill(request.payload)
        else:
            return SliceResponse(request_id=request.request_id, success=False, payload={"error": f"Unknown operation: {operation}"})
    
    async def _register_skill(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            skill_id = await self._registration_service.register_skill(
                name=payload.get("name", ""),
                description=payload.get("description", ""),
                parameters=payload.get("parameters", {})
            )
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"skill_id": skill_id})
        except Exception as e:
            logger.error(f"Failed to register skill: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _get_skill(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            skill = await self._registration_service.get_skill(skill_id=payload.get("skill_id", ""))
            return SliceResponse(request_id=self._current_request_id, success=True, payload=skill or {})
        except Exception as e:
            logger.error(f"Failed to get skill: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _list_skills(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            skills = await self._query_service.list_skills(category=payload.get("category"))
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"skills": skills})
        except Exception as e:
            logger.error(f"Failed to list skills: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _update_skill(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            success = await self._management_service.update_skill(
                skill_id=payload.get("skill_id", ""),
                data=payload.get("data", {})
            )
            return SliceResponse(request_id=self._current_request_id, success=success, payload={"updated": success})
        except Exception as e:
            logger.error(f"Failed to update skill: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _delete_skill(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            success = await self._management_service.delete_skill(skill_id=payload.get("skill_id", ""))
            return SliceResponse(request_id=self._current_request_id, success=success, payload={"deleted": success})
        except Exception as e:
            logger.error(f"Failed to delete skill: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def _execute_skill(self, payload: Dict[str, Any]) -> SliceResponse:
        try:
            result = await self._execution_service.execute_skill(
                skill_id=payload.get("skill_id", ""),
                parameters=payload.get("parameters", {})
            )
            return SliceResponse(request_id=self._current_request_id, success=True, payload={"result": result})
        except Exception as e:
            logger.error(f"Failed to execute skill: {e}")
            return SliceResponse(request_id=self._current_request_id, success=False, payload={"error": str(e)})
    
    async def self_improve(self, feedback: Dict[str, Any]) -> Dict[str, Any]:
        improver = SelfImprovementServices(self)
        improvements = await improver.analyze_and_improve(feedback)
        return {"improvements": improvements, "message": "Skills slice self-improvement complete"}
    
    async def health_check(self) -> Dict[str, Any]:
        return {"status": "healthy", "slice": self.slice_id}
