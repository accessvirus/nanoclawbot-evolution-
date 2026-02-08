"""
Provider System Services for slice_providers

Core business logic for LLM provider management.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..slice_base import AtomicSlice

logger = logging.getLogger(__name__)


class ProviderServices:
    """Services for provider management."""
    
    def __init__(self, slice: "AtomicSlice"):
        self.slice = slice
        self.db = slice.database
    
    async def register_provider(
        self,
        name: str,
        provider_type: str,
        api_endpoint: str,
        api_key: str = None,
        models: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Register a new provider."""
        provider_id = f"prov_{int(datetime.utcnow().timestamp() * 1000)}"
        
        async with self.db.transaction():
            await self.db.execute(
                """INSERT INTO providers 
                   (id, name, type, api_endpoint, api_key, models, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                provider_id, name, provider_type, api_endpoint, 
                api_key, str(models or []), str(metadata or {}), datetime.utcnow().isoformat()
            )
        
        logger.info(f"Provider registered: {name}")
        return provider_id
    
    async def get_provider(self, provider_id: str) -> Optional[Dict[str, Any]]:
        """Get provider by ID."""
        row = await self.db.fetchone(
            "SELECT * FROM providers WHERE id = ?",
            (provider_id,)
        )
        return dict(row) if row else None
    
    async def list_providers(self, provider_type: str = None) -> List[Dict[str, Any]]:
        """List all providers."""
        if provider_type:
            rows = await self.db.fetchall(
                "SELECT * FROM providers WHERE type = ? ORDER BY name",
                (provider_type,)
            )
        else:
            rows = await self.db.fetchall("SELECT * FROM providers ORDER BY name")
        
        return [dict(row) for row in rows]
    
    async def update_provider(
        self,
        provider_id: str,
        **updates
    ) -> bool:
        """Update provider."""
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [provider_id]
        
        await self.db.execute(
            f"UPDATE providers SET {set_clause} WHERE id = ?",
            values
        )
        return True
    
    async def delete_provider(self, provider_id: str) -> bool:
        """Delete provider."""
        await self.db.execute(
            "UPDATE providers SET is_active = 0 WHERE id = ?",
            (provider_id,)
        )
        return True
    
    async def get_provider_models(self, provider_id: str) -> List[str]:
        """Get models for a provider."""
        provider = await self.get_provider(provider_id)
        if provider:
            return eval(provider.get("models", "[]"))
        return []


class CostTrackingServices:
    """Services for cost tracking."""
    
    def __init__(self, slice: "AtomicSlice"):
        self.slice = slice
        self.db = slice.database
    
    async def record_usage(
        self,
        provider_id: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        user_id: str = None,
        cost: float = 0.0
    ) -> str:
        """Record API usage."""
        usage_id = f"usage_{int(datetime.utcnow().timestamp() * 1000)}"
        
        async with self.db.transaction():
            await self.db.execute(
                """INSERT INTO usage_records 
                   (id, provider_id, model, prompt_tokens, completion_tokens, 
                    total_tokens, cost, user_id, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                usage_id, provider_id, model, prompt_tokens, 
                completion_tokens, prompt_tokens + completion_tokens, 
                cost, user_id, datetime.utcnow().isoformat()
            )
        
        return usage_id
    
    async def get_usage_stats(
        self,
        provider_id: str = None,
        user_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Dict[str, Any]:
        """Get usage statistics."""
        query = "SELECT * FROM usage_records WHERE 1=1"
        params = []
        
        if provider_id:
            query += " AND provider_id = ?"
            params.append(provider_id)
        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)
        if start_date:
            query += " AND created_at >= ?"
            params.append(start_date.isoformat())
        if end_date:
            query += " AND created_at <= ?"
            params.append(end_date.isoformat())
        
        rows = await self.db.fetchall(query, params)
        
        total_cost = sum(row["cost"] for row in rows) if rows else 0
        total_tokens = sum(row["total_tokens"] for row in rows) if rows else 0
        
        return {
            "total_requests": len(rows),
            "total_cost": total_cost,
            "total_tokens": total_tokens
        }
    
    async def get_user_costs(self, user_id: str) -> Dict[str, Any]:
        """Get costs for a user."""
        rows = await self.db.fetchall(
            """SELECT provider_id, SUM(cost) as total_cost, SUM(total_tokens) as total_tokens
               FROM usage_records WHERE user_id = ?
               GROUP BY provider_id""",
            (user_id,)
        )
        
        return {
            "providers": [dict(row) for row in rows],
            "total_cost": sum(row["total_cost"] for row in rows) if rows else 0
        }
