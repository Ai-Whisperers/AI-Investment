"""
Base classes and interfaces for data providers.
Implements common functionality and error handling.
"""

import logging
import time
from abc import ABC, abstractmethod
from enum import Enum
from functools import wraps
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ProviderStatus(Enum):
    """Provider health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ProviderError(Exception):
    """Base exception for provider errors."""

    pass


class RateLimitError(ProviderError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class APIError(ProviderError):
    """Raised when API returns an error."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class CircuitBreakerError(ProviderError):
    """Raised when circuit breaker is open."""

    pass


class CircuitBreaker:
    """
    Simple circuit breaker implementation.
    Opens after consecutive failures, prevents unnecessary API calls.
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
            else:
                raise CircuitBreakerError("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try again."""
        return (
            self.last_failure_time
            and time.time() - self.last_failure_time >= self.recovery_timeout
        )

    def _on_success(self):
        """Reset circuit breaker on successful call."""
        self.failure_count = 0
        self.state = "closed"

    def _on_failure(self):
        """Handle failure, potentially opening circuit."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """
    Decorator for exponential backoff retry logic.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = base_delay
            last_exception = None

            for _attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except RateLimitError as e:
                    # Use retry_after if provided
                    delay = e.retry_after or delay
                    logger.warning(f"Rate limit hit, retrying in {delay}s...")
                    time.sleep(delay)
                    last_exception = e
                except APIError as e:
                    if e.status_code and e.status_code >= 500:
                        # Retry on server errors
                        logger.warning(f"Server error, retrying in {delay}s...")
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                        last_exception = e
                    else:
                        # Don't retry on client errors
                        raise
                except Exception as e:
                    last_exception = e
                    raise

            # All retries exhausted
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


class BaseProvider(ABC, Generic[T]):
    """
    Abstract base class for all data providers.
    Provides common functionality like caching, rate limiting, and error handling.
    """

    def __init__(self, api_key: str | None = None, cache_enabled: bool = True):
        self.api_key = api_key
        self.cache_enabled = cache_enabled
        self.circuit_breaker = CircuitBreaker()
        self._last_request_time = 0
        self._request_count = 0
        self._error_count = 0
        self._success_count = 0

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name."""
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate provider configuration."""
        pass

    @abstractmethod
    def health_check(self) -> ProviderStatus:
        """Check provider health status."""
        pass

    def get_stats(self) -> dict[str, Any]:
        """Get provider statistics."""
        return {
            "provider": self.get_provider_name(),
            "requests": self._request_count,
            "successes": self._success_count,
            "errors": self._error_count,
            "error_rate": self._error_count / max(self._request_count, 1),
            "circuit_breaker_state": self.circuit_breaker.state,
            "last_request": self._last_request_time,
        }

    def _record_request(self):
        """Record request for statistics."""
        self._request_count += 1
        self._last_request_time = time.time()

    def _record_success(self):
        """Record successful request."""
        self._success_count += 1

    def _record_error(self):
        """Record failed request."""
        self._error_count += 1

    @retry_with_backoff(max_retries=3)
    def make_request(self, endpoint: str, params: dict | None = None) -> Any:
        """
        Make API request with retry logic and circuit breaker.
        Subclasses should implement _execute_request.
        """
        self._record_request()

        try:
            result = self.circuit_breaker.call(self._execute_request, endpoint, params)
            self._record_success()
            return result
        except Exception:
            self._record_error()
            raise

    @abstractmethod
    def _execute_request(self, endpoint: str, params: dict | None = None) -> Any:
        """
        Execute the actual API request.
        Must be implemented by subclasses.
        """
        pass
