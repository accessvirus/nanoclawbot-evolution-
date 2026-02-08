"""
Security Module for RefactorBot V2

Provides rate limiting, input validation, and security utilities.
"""

import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional, Tuple
import asyncio

logger = logging.getLogger(__name__)


# =============================================================================
# Rate Limiting
# =============================================================================

@dataclass
class RateLimitConfig:
    """Rate limit configuration."""
    requests_per_second: int = 10
    requests_per_minute: int = 100
    requests_per_hour: int = 1000
    burst_size: int = 20
    window_seconds: int = 60
    enabled: bool = True


@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    remaining: int
    reset_at: float
    limit_type: str  # "burst", "window", "hard"
    retry_after: Optional[float] = None


class TokenBucket:
    """
    Token bucket rate limiter for precise rate limiting.
    """
    
    def __init__(
        self,
        capacity: int,
        refill_rate: float,
        initial_tokens: int = None
    ):
        self.capacity = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.tokens = initial_tokens if initial_tokens is not None else capacity
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()
    
    async def consume(self, tokens: int = 1) -> Tuple[bool, float]:
        """Try to consume tokens."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            
            # Refill tokens
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.refill_rate
            )
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0.0
            
            wait_time = (tokens - self.tokens) / self.refill_rate
            return False, wait_time
    
    def try_consume(self, tokens: int = 1) -> bool:
        """Synchronous try to consume tokens."""
        now = time.monotonic()
        elapsed = now - self.last_refill
        
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimiter:
    """
    Multi-level rate limiter for API endpoints.
    
    Supports:
    - Token bucket for burst handling
    - Sliding window for sustained limits
    - Per-user rate limiting
    """
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self._buckets: Dict[str, TokenBucket] = {}
        self._windows: Dict[str, List[float]] = {}
        self._lock = asyncio.Lock()
    
    def _get_key(self, identifier: str, limit_type: str) -> str:
        """Get rate limit key."""
        return f"{limit_type}:{identifier}"
    
    async def check_rate_limit(
        self,
        identifier: str,
        cost: int = 1
    ) -> RateLimitResult:
        """Check rate limit for identifier."""
        if not self.config.enabled:
            return RateLimitResult(True, 9999, 0.0, "disabled")
        
        # Check burst limit (token bucket)
        bucket_key = self._get_key(identifier, "burst")
        if bucket_key not in self._buckets:
            self._buckets[bucket_key] = TokenBucket(
                capacity=self.config.burst_size,
                refill_rate=self.config.requests_per_second
            )
        
        bucket = self._buckets[bucket_key]
        allowed, wait_time = await bucket.consume(cost)
        
        if not allowed:
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=time.monotonic() + wait_time,
                limit_type="burst",
                retry_after=wait_time
            )
        
        # Check sliding window
        window_key = self._get_key(identifier, "window")
        now = time.monotonic()
        
        async with self._lock:
            if window_key not in self._windows:
                self._windows[window_key] = []
            
            # Remove old entries
            cutoff = now - self.config.window_seconds
            self._windows[window_key] = [
                t for t in self._windows[window_key] if t > cutoff
            ]
            
            # Check limit
            if len(self._windows[window_key]) >= self.config.requests_per_minute:
                oldest = self._windows[window_key][0]
                reset_at = oldest + self.config.window_seconds
                return RateLimitResult(
                    allowed=False,
                    remaining=0,
                    reset_at=reset_at,
                    limit_type="window",
                    retry_after=reset_at - now
                )
            
            # Add current request
            self._windows[window_key].append(now)
        
        remaining = self.config.requests_per_minute - len(self._windows[window_key])
        
        return RateLimitResult(
            allowed=True,
            remaining=remaining,
            reset_at=now + self.config.window_seconds,
            limit_type="window"
        )
    
    def get_stats(self, identifier: str) -> Dict[str, Any]:
        """Get rate limit statistics."""
        bucket_key = self._get_key(identifier, "burst")
        window_key = self._get_key(identifier, "window")
        
        bucket = self._buckets.get(bucket_key)
        window = self._windows.get(window_key, [])
        now = time.monotonic()
        
        return {
            "burst_remaining": bucket.tokens if bucket else 0,
            "window_count": len([t for t in window if t > now - self.config.window_seconds]),
            "window_limit": self.config.requests_per_minute
        }


class PerSliceRateLimiter:
    """
    Rate limiter that manages limits per slice.
    """
    
    def __init__(self):
        self._limiters: Dict[str, RateLimiter] = {}
        self._default_config = RateLimitConfig()
        self._lock = asyncio.Lock()
    
    async def get_limiter(self, slice_name: str) -> RateLimiter:
        """Get or create rate limiter for slice."""
        async with self._lock:
            if slice_name not in self._limiters:
                self._limiters[slice_name] = RateLimiter()
            return self._limiters[slice_name]
    
    async def check_slice_limit(
        self,
        slice_name: str,
        identifier: str,
        cost: int = 1
    ) -> RateLimitResult:
        """Check rate limit for a slice."""
        limiter = await self.get_limiter(slice_name)
        return await limiter.check_rate_limit(identifier, cost)


# =============================================================================
# Input Validation
# =============================================================================

class InputValidator:
    """
    Comprehensive input validation utilities.
    """
    
    # Patterns for validation
    USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,32}$")
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    UUID_PATTERN = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
        re.IGNORECASE
    )
    SAFE_PATH_PATTERN = re.compile(r"^[a-zA-Z0-9/_.-]+$")
    
    # Maximum sizes
    MAX_MESSAGE_LENGTH = 100000
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
    MAX_DEPTH = 10
    
    @classmethod
    def validate_username(cls, value: str) -> Tuple[bool, str]:
        """Validate username."""
        if not value:
            return False, "Username is required"
        if len(value) > 32:
            return False, "Username too long"
        if not cls.USERNAME_PATTERN.match(value):
            return False, "Username contains invalid characters"
        return True, ""
    
    @classmethod
    def validate_email(cls, value: str) -> Tuple[bool, str]:
        """Validate email."""
        if not value:
            return False, "Email is required"
        if not cls.EMAIL_PATTERN.match(value):
            return False, "Invalid email format"
        return True, ""
    
    @classmethod
    def validate_path(cls, value: str) -> Tuple[bool, str]:
        """Validate file path for path traversal."""
        if not value:
            return False, "Path is required"
        
        # Check for path traversal
        if ".." in value or value.startswith("/"):
            return False, "Invalid path"
        
        # Check for unsafe characters
        if not cls.SAFE_PATH_PATTERN.match(value):
            return False, "Path contains invalid characters"
        
        # Check depth
        depth = value.count("/")
        if depth > cls.MAX_DEPTH:
            return False, "Path too deep"
        
        return True, ""
    
    @classmethod
    def validate_message_length(cls, value: str) -> Tuple[bool, str]:
        """Validate message length."""
        if len(value) > cls.MAX_MESSAGE_LENGTH:
            return False, f"Message exceeds maximum length of {cls.MAX_MESSAGE_LENGTH}"
        return True, ""
    
    @classmethod
    def validate_file_size(cls, size: int) -> Tuple[bool, str]:
        """Validate file size."""
        if size > cls.MAX_FILE_SIZE:
            return False, f"File exceeds maximum size of {cls.MAX_FILE_SIZE}"
        return True, ""
    
    @classmethod
    def sanitize_html(cls, value: str) -> str:
        """Sanitize HTML to prevent XSS."""
        # Basic HTML entity escaping
        replacements = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"'.encode('unicode_escape').decode(): "&quot;",
            "'": "&#x27;",
            "/": "&#x2F;"
        }
        for char, entity in replacements.items():
            value = value.replace(char, entity)
        return value
    
    @classmethod
    def validate_json(cls, value: str) -> Tuple[bool, str, Any]:
        """Validate and parse JSON."""
        try:
            data = json.loads(value)
            return True, "", data
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}", None
    
    @classmethod
    def validate_query_params(cls, params: Dict[str, str]) -> Tuple[bool, List[str]]:
        """Validate query parameters."""
        errors = []
        
        for key, value in params.items():
            # Check for SQL injection patterns
            if any(pattern in value.lower() for pattern in [
                "select ", "insert ", "update ", "delete ",
                "drop ", "truncate ", "alter ", "exec "
            ]):
                errors.append(f"Invalid value for parameter '{key}'")
        
        return len(errors) == 0, errors


# =============================================================================
# Security Utilities
# =============================================================================

class SecurityUtils:
    """
    Security utility functions.
    """
    
    @staticmethod
    def hash_password(password: str, salt: bytes = None) -> Tuple[str, str]:
        """Hash password with salt."""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            100000
        )
        
        return salt.hex(), key.hex()
    
    @staticmethod
    def verify_password(password: str, salt_hex: str, key_hex: str) -> bool:
        """Verify password against hash."""
        salt = bytes.fromhex(salt_hex)
        computed = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            100000
        )
        
        return hmac.compare_digest(computed.hex(), key_hex)
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key."""
        return f"rf_{secrets.token_urlsafe(32)}"
    
    @staticmethod
    def generate_session_token() -> str:
        """Generate secure session token."""
        return secrets.token_urlsafe(64)
    
    @staticmethod
    def generate_webhook_secret() -> str:
        """Generate webhook signature secret."""
        return secrets.token_hex(32)
    
    @staticmethod
    def verify_webhook_signature(
        payload: bytes,
        signature: str,
        secret: str
    ) -> bool:
        """Verify webhook signature."""
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(f"sha256={expected}", signature)
    
    @staticmethod
    def sign_data(data: str, secret: str) -> str:
        """Sign data with HMAC."""
        signature = hmac.new(
            secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{data}.{signature}"
    
    @staticmethod
    def verify_signature(data: str, secret: str) -> bool:
        """Verify signed data."""
        try:
            data_part, sig_part = data.rsplit(".", 1)
            expected = hmac.new(
                secret.encode(),
                data_part.encode(),
                hashlib.sha256
            ).hexdigest()
            return hmac.compare_digest(expected, sig_part)
        except ValueError:
            return False


# =============================================================================
# Security Middleware
# =============================================================================

class SecurityMiddleware:
    """
    Security middleware for API endpoints.
    """
    
    def __init__(self):
        self.rate_limiter = PerSliceRateLimiter()
        self.validator = InputValidator()
    
    async def check_security(
        self,
        slice_name: str,
        identifier: str,
        request_data: Dict[str, Any] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Perform security checks.
        
        Returns: (allowed, error_message)
        """
        # Rate limiting
        result = await self.rate_limiter.check_slice_limit(slice_name, identifier)
        if not result.allowed:
            logger.warning(f"Rate limit exceeded for {identifier} on {slice_name}")
            return False, f"Rate limited. Retry after {result.retry_after:.0f}s"
        
        # Input validation
        if request_data:
            valid, errors = self.validator.validate_query_params(request_data)
            if not valid:
                logger.warning(f"Invalid input from {identifier}: {errors}")
                return False, f"Invalid input: {errors[0]}"
        
        return True, None
    
    def create_rate_limit_headers(self, result: RateLimitResult) -> Dict[str, str]:
        """Create rate limit response headers."""
        headers = {
            "X-RateLimit-Limit": str(result.remaining + 1),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(int(result.reset_at))
        }
        
        if result.retry_after:
            headers["Retry-After"] = str(int(result.retry_after))
        
        return headers


# =============================================================================
# Decorators
# =============================================================================

def rate_limit(
    slice_name: str,
    requests_per_second: int = 10,
    requests_per_minute: int = 100
):
    """Decorator to apply rate limiting to a function."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            limiter = PerSliceRateLimiter()
            
            # Get identifier from args/kwargs or use default
            identifier = kwargs.get("identifier", "default")
            
            result = await limiter.check_slice_limit(slice_name, identifier)
            if not result.allowed:
                return {"error": "Rate limited", "retry_after": result.retry_after}
            
            return await func(*args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Synchronous version would use sync rate limiter
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def validate_input(validator_func):
    """Decorator to validate input."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            valid, error = validator_func(*args, **kwargs)
            if not valid:
                return {"error": error}
            return await func(*args, **kwargs)
        
        return async_wrapper
    
    return decorator
