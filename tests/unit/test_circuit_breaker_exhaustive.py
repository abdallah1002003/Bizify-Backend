import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from app.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerOpenError,
)

@pytest.mark.asyncio
async def test_circuit_breaker_init_validation():
    with pytest.raises(ValueError, match="failure_threshold must be > 0"):
        CircuitBreaker("test", config=CircuitBreakerConfig(failure_threshold=0))
    
    with pytest.raises(ValueError, match="recovery_timeout_seconds must be > 0"):
        CircuitBreaker("test", config=CircuitBreakerConfig(recovery_timeout_seconds=0))
        
    with pytest.raises(ValueError, match="half_open_success_threshold must be > 0"):
        CircuitBreaker("test", config=CircuitBreakerConfig(half_open_success_threshold=0))

@pytest.mark.asyncio
async def test_circuit_breaker_closed_to_open():
    cb = CircuitBreaker("test", config=CircuitBreakerConfig(failure_threshold=2))
    assert cb.state == CircuitState.CLOSED
    
    async def failing_call():
        raise ValueError("fail")
    
    # First failure
    with pytest.raises(ValueError):
        await cb.call(failing_call)
    assert cb.state == CircuitState.CLOSED
    assert cb._failure_count == 1
    
    # Second failure -> OPEN
    with pytest.raises(ValueError):
        await cb.call(failing_call)
    assert cb.state == CircuitState.OPEN
    assert cb._opened_at is not None

@pytest.mark.asyncio
async def test_circuit_breaker_open_fail_fast():
    cb = CircuitBreaker("test", config=CircuitBreakerConfig(failure_threshold=1))
    
    # Open the circuit
    async def failing(): raise ValueError()
    with pytest.raises(ValueError): await cb.call(failing)
    assert cb.state == CircuitState.OPEN
    
    # Subsequent calls fail fast
    async def success(): return "ok"
    with pytest.raises(CircuitBreakerOpenError, match="failing fast"):
        await cb.call(success)
        
    # Test custom message
    with pytest.raises(CircuitBreakerOpenError, match="Custom error"):
        await cb.call(success, open_error_message="Custom error")

@pytest.mark.asyncio
async def test_circuit_breaker_recovery_to_half_open():
    config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout_seconds=0.1)
    cb = CircuitBreaker("test", config=config)
    
    async def fail(): raise ValueError()
    # Open
    with pytest.raises(ValueError): await cb.call(fail)
    
    # Still open
    assert cb.state == CircuitState.OPEN
    assert await cb.allow_call() is False
    
    # Wait for recovery
    await asyncio.sleep(0.15)
    
    # Transitions to HALF_OPEN on allow_call
    assert await cb.allow_call() is True
    assert cb.state == CircuitState.HALF_OPEN
    assert cb._half_open_in_flight is True

@pytest.mark.asyncio
async def test_circuit_breaker_half_open_logic():
    cb = CircuitBreaker("test", config=CircuitBreakerConfig(half_open_success_threshold=2))
    cb._state = CircuitState.HALF_OPEN
    
    # First probe success
    await cb.record_success()
    assert cb.state == CircuitState.HALF_OPEN
    assert cb._half_open_successes == 1
    
    # Second probe success -> CLOSED
    await cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb._failure_count == 0

@pytest.mark.asyncio
async def test_circuit_breaker_half_open_to_open_on_failure():
    cb = CircuitBreaker("test")
    cb._state = CircuitState.HALF_OPEN
    cb._half_open_in_flight = True
    
    await cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb._half_open_in_flight is False

@pytest.mark.asyncio
async def test_circuit_breaker_half_open_concurrency():
    cb = CircuitBreaker("test")
    cb._state = CircuitState.HALF_OPEN
    
    # First probe allowed
    assert await cb.allow_call() is True
    assert cb._half_open_in_flight is True
    
    # Second concurrent probe rejected
    assert await cb.allow_call() is False

@pytest.mark.asyncio
async def test_circuit_breaker_success_resets_failure_count():
    cb = CircuitBreaker("test")
    cb._failure_count = 3
    
    await cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb._failure_count == 0

@pytest.mark.asyncio
async def test_circuit_breaker_enter_half_open_if_ready_branches():
    cb = CircuitBreaker("test")
    
    # Case: not OPEN
    await cb._enter_half_open_if_ready()
    assert cb.state == CircuitState.CLOSED
    
    # Case: OPEN but _opened_at is None (line 69)
    cb._state = CircuitState.OPEN
    cb._opened_at = None
    assert cb._should_attempt_reset(time.monotonic()) is False
    
    # Case: OPEN but not timed out
    cb._opened_at = time.monotonic()
    await cb._enter_half_open_if_ready()
    assert cb.state == CircuitState.OPEN
    
@pytest.mark.asyncio
async def test_circuit_breaker_full_cycle():
    cb = CircuitBreaker("test", config=CircuitBreakerConfig(failure_threshold=1, recovery_timeout_seconds=0.01))
    
    async def success(val="ok"): return val
    async def fail(): raise ValueError()

    # Success
    assert await cb.call(success) == "ok"
    
    # Failure -> Open
    with pytest.raises(ValueError):
        await cb.call(fail)
    assert cb.state == CircuitState.OPEN
    
    # Wait
    await asyncio.sleep(0.02)
    
    # Half-Open Success -> Closed
    assert await cb.call(lambda: success("recovered")) == "recovered"
    assert cb.state == CircuitState.CLOSED
