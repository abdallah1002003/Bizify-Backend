from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Awaitable, Callable, Generic, Optional, TypeVar


T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpenError(RuntimeError):
    pass


@dataclass(frozen=True)
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout_seconds: float = 30.0
    half_open_success_threshold: int = 1


class CircuitBreaker(Generic[T]):
    """
    Minimal async-friendly circuit breaker.

    Behavior:
    - CLOSED: allow all calls; count failures; open once threshold is reached.
    - OPEN: fail-fast until recovery timeout elapses.
    - HALF_OPEN: allow one in-flight probe call at a time; close on enough successes;
      open immediately on any failure.
    """

    def __init__(self, name: str, *, config: CircuitBreakerConfig | None = None) -> None:
        self.name = name
        self.config = config or CircuitBreakerConfig()

        if self.config.failure_threshold <= 0:
            raise ValueError("failure_threshold must be > 0")
        if self.config.recovery_timeout_seconds <= 0:
            raise ValueError("recovery_timeout_seconds must be > 0")
        if self.config.half_open_success_threshold <= 0:
            raise ValueError("half_open_success_threshold must be > 0")

        self._state: CircuitState = CircuitState.CLOSED
        self._failure_count: int = 0
        self._half_open_successes: int = 0
        self._opened_at: Optional[float] = None

        self._lock = asyncio.Lock()
        self._half_open_in_flight: bool = False

    @property
    def state(self) -> CircuitState:
        return self._state

    def _now(self) -> float:
        return time.monotonic()

    def _should_attempt_reset(self, now: float) -> bool:
        if self._opened_at is None:
            return False
        return (now - self._opened_at) >= float(self.config.recovery_timeout_seconds)

    async def _enter_half_open_if_ready(self) -> None:
        now = self._now()
        if self._state != CircuitState.OPEN:
            return
        if not self._should_attempt_reset(now):
            return
        # Transition to half-open and allow a probe.
        self._state = CircuitState.HALF_OPEN
        self._half_open_successes = 0
        self._half_open_in_flight = False
        self._opened_at = None

    async def allow_call(self) -> bool:
        async with self._lock:
            if self._state == CircuitState.OPEN:
                await self._enter_half_open_if_ready()

            if self._state == CircuitState.OPEN:
                return False

            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_in_flight:
                    return False
                self._half_open_in_flight = True
                return True

            # CLOSED
            return True

    async def record_success(self) -> None:
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_in_flight = False
                self._half_open_successes += 1
                if self._half_open_successes >= self.config.half_open_success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._half_open_successes = 0
                return

            # CLOSED
            self._failure_count = 0

    async def record_failure(self) -> None:
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._half_open_in_flight = False
                self._state = CircuitState.OPEN
                self._opened_at = self._now()
                self._failure_count = self.config.failure_threshold
                self._half_open_successes = 0
                return

            self._failure_count += 1
            if self._failure_count >= self.config.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = self._now()

    async def call(
        self,
        fn: Callable[[], Awaitable[T]],
        *,
        open_error_message: str | None = None,
    ) -> T:
        allowed = await self.allow_call()
        if not allowed:
            raise CircuitBreakerOpenError(
                open_error_message
                or f"Circuit breaker '{self.name}' is open; failing fast."
            )

        try:
            result = await fn()
        except Exception:
            await self.record_failure()
            raise
        else:
            await self.record_success()
            return result

