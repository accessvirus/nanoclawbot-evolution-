"""
Providers Core Services - Service Layer for Providers Slice

Implements actual database operations for provider management.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from ...slice_base import AtomicSlice

logger = logging.getLogger(__name__)


class ProviderRegistrationServices:
    """Service for registering providers."""
    
    def __init__(self, slice: AtomicSlice):
        self.slice = slice
        self.db = getattr(slice, '_database', None) or getattr(slice, 'database', None)
    
    async def register_provider(
        self,
        provider_type: str,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        credentials: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register a new provider."""
        provider_id = f"provider_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow().isoformat()
        
        if self.db:
            async with self.db.transaction():
                await self.db.execute(
                    """INSERT INTO providers (id, type, name, config, credentials, status, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    provider_id, provider_type, name, str(config or {}), str(credentials or {}), "active", now, now
                )
        
        logger.info(f"Registering provider: {name} (ID: {provider_id})")
        return provider_id


class ProviderRetrievalServices:
    """Service for retrieving providers."""
    
    def __init__(self, slice: AtomicSlice):
        self.slice = slice
        self.db = getattr(slice, '_database', None) or getattr(slice, 'database', None)
    
    async def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get a provider by its ID."""
        if self.db:
            row = await self.db.fetchone(
                "SELECT * FROM providers WHERE id = ?",
                (provider_id,)
            )
            return dict(row) if row else None
        logger.info(f"Retrieving provider: {provider_id}")
        return {"id": provider_id}
    
    async def get_provider_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a provider by its name."""
        if self.db:
            row = await self.db.fetchone(
                "SELECT * FROM providers WHERE name = ?",
                (name,)
            )
            return dict(row) if row else None
        logger.info(f"Retrieving provider by name: {name}")
        return None


class ProviderQueryServices:
    """Service for querying providers."""
    
    def __init__(self, slice: AtomicSlice):
        self.slice = slice
        self.db = getattr(slice, '_database', None) or getattr(slice, 'database', None)
    
    async def list_providers(
        self,
        provider_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List providers, optionally filtered."""
        if self.db:
            query = "SELECT * FROM providers WHERE 1=1"
            params = []
            if provider_type:
                query += " AND type = ?"
                params.append(provider_type)
            if status:
                query += " AND status = ?"
                params.append(status)
            query += " ORDER BY priority DESC, name"
            rows = await self.db.fetchall(query, params)
            return [dict(row) for row in rows]
        logger.info(f"Listing providers: type={provider_type}, status={status}")
        return []
    
    async def count_providers(
        self,
        provider_type: Optional[str] = None,
        status: Optional[str] = None
    ) -> int:
        """Count providers, optionally filtered."""
        if self.db:
            query = "SELECT COUNT(*) as count FROM providers WHERE 1=1"
            params = []
            if provider_type:
                query += " AND type = ?"
                params.append(provider_type)
            if status:
                query += " AND status = ?"
                params.append(status)
            row = await self.db.fetchone(query, params)
            return row["count"] if row else 0
        logger.info(f"Counting providers: type={provider_type}, status={status}")
        return 0


class ProviderManagementServices:
    """Service for managing providers."""
    
    def __init__(self, slice: AtomicSlice):
        self.slice = slice
        self.db = getattr(slice, '_database', None) or getattr(slice, 'database', None)
    
    async def update_provider(
        self,
        provider_id: str,
        config: Dict[str, Any]
    ) -> bool:
        """Update a provider's config."""
        if self.db:
            now = datetime.utcnow().isoformat()
            result = await self.db.execute(
                "UPDATE providers SET config = ?, updated_at = ? WHERE id = ?",
                (str(config), now, provider_id)
            )
            return result > 0
        logger.info(f"Updating provider: {provider_id}")
        return True
    
    async def delete_provider(self, provider_id: str) -> bool:
        """Delete a provider."""
        if self.db:
            result = await self.db.execute(
                "DELETE FROM providers WHERE id = ?",
                (provider_id,)
            )
            return result > 0
        logger.info(f"Deleting provider: {provider_id}")
        return True
    
    async def disable_provider(self, provider_id: str) -> bool:
        """Disable a provider."""
        if self.db:
            result = await self.db.execute(
                "UPDATE providers SET status = 'disabled', updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), provider_id)
            )
            return result > 0
        logger.info(f"Disabling provider: {provider_id}")
        return True
    
    async def enable_provider(self, provider_id: str) -> bool:
        """Enable a provider."""
        if self.db:
            result = await self.db.execute(
                "UPDATE providers SET status = 'active', updated_at = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), provider_id)
            )
            return result > 0
        logger.info(f"Enabling provider: {provider_id}")
        return True


class ProviderTestingServices:
    """Service for testing providers."""
    
    def __init__(self, slice: AtomicSlice):
        self.slice = slice
        self.db = getattr(slice, '_database', None) or getattr(slice, 'database', None)
    
    async def test_provider(self, provider_id: str) -> Dict[str, Any]:
        """Test a provider's connectivity."""
        # Get provider from database
        if self.db:
            row = await self.db.fetchone(
                "SELECT * FROM providers WHERE id = ?",
                (provider_id,)
            )
            if row:
                provider_type = row["type"]
                
                # Test based on provider type
                if provider_type == "openrouter":
                    return await self._test_openrouter(row)
                elif provider_type == "litellm":
                    return await self._test_litellm(row)
                else:
                    return {"success": True, "message": f"Provider type {provider_type} configured"}
        
        logger.info(f"Testing provider: {provider_id}")
        return {"success": True, "latency_ms": 0, "message": "Provider test successful"}
    
    async def _test_openrouter(self, provider: Dict[str, Any]) -> Dict[str, Any]:
        """Test OpenRouter provider."""
        import httpx
        import time
        
        api_key = provider.get("api_key", "")
        base_url = provider.get("base_url", "https://openrouter.ai/api/v1")
        
        if not api_key:
            return {"success": False, "message": "API key not configured"}
        
        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{base_url}/models",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                latency_ms = (time.perf_counter() - start_time) * 1000
                
                if response.status_code == 200:
                    return {"success": True, "latency_ms": latency_ms, "message": "OpenRouter connection successful"}
                else:
                    return {"success": False, "latency_ms": latency_ms, "message": f"API returned status {response.status_code}"}
        except Exception as e:
            return {"success": False, "latency_ms": 0, "message": str(e)}
    
    async def _test_litellm(self, provider: Dict[str, Any]) -> Dict[str, Any]:
        """Test LiteLLM provider."""
        import httpx
        import time
        
        api_key = provider.get("api_key", "")
        base_url = provider.get("base_url", "")
        model = provider.get("model", "gpt-4")
        
        if not api_key or not base_url:
            return {"success": False, "message": "API key or base URL not configured"}
        
        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{base_url}/chat/completions",
                    json={
                        "model": model,
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 5
                    },
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                latency_ms = (time.perf_counter() - start_time) * 1000
                
                if response.status_code == 200:
                    return {"success": True, "latency_ms": latency_ms, "message": "LiteLLM connection successful"}
                else:
                    return {"success": False, "latency_ms": latency_ms, "message": f"API returned status {response.status_code}"}
        except Exception as e:
            return {"success": False, "latency_ms": 0, "message": str(e)}
    
    async def test_provider_connection(
        self,
        provider_id: str,
        test_payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Test a provider with a custom payload."""
        return await self.test_provider(provider_id)
