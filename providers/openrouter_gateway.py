"""
OpenRouter Gateway - Unified LLM access layer.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from pydantic import BaseModel


class OpenRouterConfig(BaseModel):
    """Configuration for OpenRouter"""
    api_key: str
    base_url: str = "https://openrouter.ai/api/v1"
    timeout: float = 60.0
    max_retries: int = 3


class ModelInfo(BaseModel):
    """Information about a model"""
    id: str
    name: str
    provider: str
    context_length: int = 4096
    capabilities: List[str] = []


class CostInfo(BaseModel):
    """Cost information for a model"""
    prompt_cost_per_1m: float = 0.0
    completion_cost_per_1m: float = 0.0


class OpenRouterGateway:
    """
    Unified LLM access layer via OpenRouter.
    Supports model routing, cost tracking, fallback strategies.
    """
    
    def __init__(self, config: OpenRouterConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://refactorbot.dev",
            }
        )
        self._model_cache: Dict[str, ModelInfo] = {}
        self._cost_cache: Dict[str, CostInfo] = {}
    
    async def close(self) -> None:
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def complete(
        self,
        prompt: str,
        model: str = "openai/gpt-4-turbo",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        stream: bool = False,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Complete a prompt.
        
        Args:
            prompt: User prompt
            model: Model identifier
            system_prompt: System prompt
            temperature: Temperature setting
            max_tokens: Maximum tokens to generate
            stream: Whether to stream
            metadata: Optional metadata
            
        Returns:
            Response dictionary
        """
        body = {
            "model": model,
            "messages": [
                *([{"role": "system", "content": system_prompt}] if system_prompt else []),
                [{"role": "user", "content": prompt}]
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        
        if metadata:
            body["metadata"] = metadata
        
        # Execute request with retries
        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.post(
                    f"{self.config.base_url}/chat/completions",
                    json=body
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract response
                choice = data["choices"][0]
                message = choice["message"]
                usage = data.get("usage", {})
                
                return {
                    "content": message.get("content", ""),
                    "role": message.get("role", "assistant"),
                    "finish_reason": choice.get("finish_reason", "stop"),
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                    "model": model,
                    "created": data.get("created"),
                }
            
            except httpx.HTTPStatusError as e:
                if e.response.status_code >= 500:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise
    
    async def stream(
        self,
        prompt: str,
        model: str = "openai/gpt-4-turbo",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream a completion.
        
        Yields:
            Response chunks
        """
        body = {
            "model": model,
            "messages": [
                *([{"role": "system", "content": system_prompt}] if system_prompt else []),
                [{"role": "user", "content": prompt}]
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        
        async with self.client.stream(
            "POST",
            f"{self.config.base_url}/chat/completions",
            json=body
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        choice = chunk.get("choices", [{}])[0]
                        delta = choice.get("delta", {})
                        
                        yield {
                            "content": delta.get("content", ""),
                            "finish_reason": choice.get("finish_reason"),
                        }
                    except json.JSONDecodeError:
                        pass
    
    async def list_models(self) -> List[ModelInfo]:
        """
        List available models.
        
        Returns:
            List of model information
        """
        if self._model_cache:
            return list(self._model_cache.values())
        
        try:
            response = await self.client.get(
                f"{self.config.base_url}/models"
            )
            response.raise_for_status()
            data = response.json()
            
            models = []
            for model in data.get("data", []):
                info = ModelInfo(
                    id=model["id"],
                    name=model.get("name", model["id"]),
                    provider=model["id"].split("/")[0] if "/" in model["id"] else "unknown",
                    context_length=model.get("context_length", 4096),
                    capabilities=model.get("capabilities", []),
                )
                self._model_cache[info.id] = info
                models.append(info)
            
            return models
        
        except Exception:
            # Return defaults if API fails
            return [
                ModelInfo(id="openai/gpt-4-turbo", name="GPT-4 Turbo", provider="openai", context_length=128000),
                ModelInfo(id="openai/gpt-4o", name="GPT-4o", provider="openai", context_length=128000),
                ModelInfo(id="anthropic/claude-3-opus", name="Claude 3 Opus", provider="anthropic", context_length=200000),
                ModelInfo(id="anthropic/claude-3-sonnet", name="Claude 3 Sonnet", provider="anthropic", context_length=200000),
            ]
    
    async def get_cost(self, model: str) -> CostInfo:
        """Get cost information for a model"""
        if model in self._cost_cache:
            return self._cost_cache[model]
        
        # Default costs (should be updated from API)
        default_costs = {
            "openai/gpt-4-turbo": CostInfo(prompt_cost_per_1m=10.0, completion_cost_per_1m=30.0),
            "openai/gpt-4o": CostInfo(prompt_cost_per_1m=5.0, completion_cost_per_1m=15.0),
            "anthropic/claude-3-opus": CostInfo(prompt_cost_per_1m=15.0, completion_cost_per_1m=75.0),
            "anthropic/claude-3-sonnet": CostInfo(prompt_cost_per_1m=3.0, completion_cost_per_1m=15.0),
        }
        
        cost = default_costs.get(model, CostInfo())
        self._cost_cache[model] = cost
        return cost
    
    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate cost for a request"""
        cost_info = asyncio.run(self.get_cost(model))
        
        prompt_cost = (prompt_tokens / 1_000_000) * cost_info.prompt_cost_per_1m
        completion_cost = (completion_tokens / 1_000_000) * cost_info.completion_cost_per_1m
        
        return prompt_cost + completion_cost


async def create_gateway(api_key: str) -> OpenRouterGateway:
    """Create and initialize a gateway"""
    config = OpenRouterConfig(api_key=api_key)
    gateway = OpenRouterGateway(config)
    await gateway.list_models()  # Preload models
    return gateway
