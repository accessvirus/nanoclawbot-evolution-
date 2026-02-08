"""
LiteLLM Gateway - Unified LLM access layer supporting multiple providers.

Supported providers:
- OpenAI
- Anthropic
- Google (VertexAI)
- Azure
- Bedrock
- Cohere
- HuggingFace
- TogetherAI
- OpenRouter
- And 50+ more via LiteLLM
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx
from pydantic import BaseModel


class LiteLLMConfig(BaseModel):
    """Configuration for LiteLLM"""
    api_key: str
    base_url: str = "http://0.0.0.0:4000"
    timeout: float = 60.0
    max_retries: int = 3


class LiteLLMModel(BaseModel):
    """Model information"""
    id: str
    name: str
    provider: str
    context_length: int = 4096
    supports_streaming: bool = True


class LiteLLMGateway:
    """
    Unified LLM gateway via LiteLLM proxy.
    
    Features:
    - Model routing across 50+ providers
    - Cost tracking per provider
    - Fallback strategies
    - Streaming support
    """
    
    # Supported providers
    SUPPORTED_PROVIDERS = [
        "openai", "anthropic", "google", "azure", "bedrock",
        "cohere", "togetherai", "openrouter", "huggingface",
        "replicate", "mistral", "groq", "cerebras", "fireworksai",
        "perplexity", "anyscale", "base", "vertexai", "sagemaker"
    ]
    
    # Provider to model mapping
    PROVIDER_MODELS = {
        "openai": ["gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-3.5-turbo"],
        "anthropic": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
        "google": ["gemini-pro", "gemini-1.5-pro"],
        "azure": ["gpt-4", "gpt-35-turbo"],
        "bedrock": ["anthropic.claude-3-sonnet-20240229-v1:0", "anthropic.claude-v2"],
        "cohere": ["command-r-plus", "command-r"],
        "togetherai": ["togethercomputer/llama-3-70b", "togethercomputer/llama-3-8b"],
    }
    
    def __init__(self, config: Optional[LiteLLMConfig] = None):
        if config is None:
            config = LiteLLMConfig(api_key="")
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=config.timeout,
            headers={"Authorization": f"Bearer {config.api_key}"}
        )
        self._model_cache: Dict[str, LiteLLMModel] = {}
    
    async def close(self) -> None:
        """Close the HTTP client"""
        await self.client.aclose()
    
    async def complete(
        self,
        prompt: str,
        model: str = "gpt-4",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
        stream: bool = False,
        provider: Optional[str] = None,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Complete a prompt via LiteLLM.
        
        Args:
            prompt: User prompt
            model: Model identifier
            system_prompt: System prompt
            temperature: Temperature setting
            max_tokens: Maximum tokens to generate
            stream: Whether to stream
            provider: Override provider
            api_base: Override API base URL
            api_key: Override API key
            
        Returns:
            Response dictionary
        """
        # Validate API key is configured
        effective_api_key = api_key or self.config.api_key
        if not effective_api_key:
            raise ValueError("API key is required for LLM completion")
        
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Build request body (LiteLLM format)
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        
        # Add provider-specific settings
        if provider:
            body["model_info"] = {"provider": provider}
        
        # Determine API base
        base_url = api_base or self.config.base_url
        
        # Execute request with retries
        for attempt in range(self.config.max_retries):
            try:
                response = await self.client.post(
                    f"{base_url}/chat/completions",
                    json=body
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract response
                choice = data["choices"][0]
                message = choice.get("message", {})
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
            except Exception as e:
                logger.error(f"LiteLLM request failed: {e}")
                raise
    
    async def stream(
        self,
        prompt: str,
        model: str = "gpt-4",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream a completion.
        
        Yields:
            Response chunks
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        body = {
            "model": model,
            "messages": messages,
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
    
    async def list_models(self) -> List[LiteLLMModel]:
        """
        List available models from LiteLLM.
        
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
                info = LiteLLMModel(
                    id=model["id"],
                    name=model.get("id", model["id"]),
                    provider=model.get("id", "unknown").split("/")[0] if "/" in model.get("id", "") else "litellm",
                    context_length=model.get("context_length", 4096),
                    supports_streaming=model.get("supports_streaming", True),
                )
                self._model_cache[info.id] = info
                models.append(info)
            
            return models
        
        except Exception:
            # Return defaults if API fails
            return self._get_default_models()
    
    def _get_default_models(self) -> List[LiteLLMModel]:
        """Get default model list."""
        return [
            LiteLLMModel(id="gpt-4", name="GPT-4", provider="openai", context_length=128000),
            LiteLLMModel(id="gpt-4-turbo", name="GPT-4 Turbo", provider="openai", context_length=128000),
            LiteLLMModel(id="gpt-3.5-turbo", name="GPT-3.5 Turbo", provider="openai", context_length=16385),
            LiteLLMModel(id="claude-3-opus-20240229", name="Claude 3 Opus", provider="anthropic", context_length=200000),
            LiteLLMModel(id="claude-3-sonnet-20240229", name="Claude 3 Sonnet", provider="anthropic", context_length=200000),
            LiteLLMModel(id="gemini-pro", name="Gemini Pro", provider="google", context_length=131072),
        ]
    
    async def get_cost(self, model: str) -> Dict[str, float]:
        """Get cost information for a model"""
        # Default costs (should be updated from LiteLLM /cost API)
        default_costs = {
            "gpt-4": {"prompt_per_1m": 30.0, "completion_per_1m": 60.0},
            "gpt-4-turbo": {"prompt_per_1m": 10.0, "completion_per_1m": 30.0},
            "gpt-3.5-turbo": {"prompt_per_1m": 0.5, "completion_per_1m": 1.5},
            "claude-3-opus-20240229": {"prompt_per_1m": 15.0, "completion_per_1m": 75.0},
            "claude-3-sonnet-20240229": {"prompt_per_1m": 3.0, "completion_per_1m": 15.0},
        }
        return default_costs.get(model, {"prompt_per_1m": 0, "completion_per_1m": 0})
    
    def calculate_cost(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate cost for a request"""
        costs = asyncio.run(self.get_cost(model))
        prompt_cost = (prompt_tokens / 1_000_000) * costs["prompt_per_1m"]
        completion_cost = (completion_tokens / 1_000_000) * costs["completion_per_1m"]
        return prompt_cost + completion_cost


class MultiProviderGateway:
    """
    Gateway that manages multiple LLM providers with fallback.
    """
    
    def __init__(self):
        self.gateways: Dict[str, LiteLLMGateway] = {}
        self.fallback_order: List[str] = []
    
    def add_provider(
        self,
        name: str,
        gateway: LiteLLMGateway,
        priority: int = 0
    ):
        """Add a provider gateway."""
        self.gateways[name] = gateway
        self.fallback_order.append((priority, name))
        self.fallback_order.sort(key=lambda x: x[0])
    
    async def complete_with_fallback(
        self,
        prompt: str,
        model: str,
        providers: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Complete with fallback through providers.
        
        Args:
            prompt: User prompt
            model: Model to use
            providers: Provider order to try (uses fallback_order if not specified)
            **kwargs: Other completion args
            
        Returns:
            First successful response
        """
        provider_list = providers or [name for _, name in self.fallback_order]
        
        errors = []
        for provider_name in provider_list:
            gateway = self.gateways.get(provider_name)
            if gateway:
                try:
                    return await gateway.complete(model=model, prompt=prompt, **kwargs)
                except Exception as e:
                    errors.append(f"{provider_name}: {e}")
                    continue
        
        raise RuntimeError(f"All providers failed: {errors}")


import logging
logger = logging.getLogger(__name__)

from pydantic import BaseModel


async def create_litellm_gateway(
    api_key: str,
    base_url: str = "http://0.0.0.0:4000"
) -> LiteLLMGateway:
    """Create and initialize a LiteLLM gateway"""
    config = LiteLLMConfig(api_key=api_key, base_url=base_url)
    gateway = LiteLLMGateway(config)
    return gateway
