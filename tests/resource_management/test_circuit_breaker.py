import pytest
import asyncio
from resource_management.circuit_breaker import CircuitBreaker, CircuitBreakerConfig


@pytest.mark.asyncio
async def test_circuit_breaker_normal_operation():
    """Test circuit breaker in normal operation."""
    config = CircuitBreakerConfig(failure_threshold=3, reset_timeout_seconds=1)
    circuit_breaker = CircuitBreaker(config)
    
    async def success_func():
        return "success"
    
    # Should work normally
    result = await circuit_breaker.call(success_func)
    assert result == "success"
    
    state_info = circuit_breaker.get_state_info()
    assert state_info['state'] == 'closed'


@pytest.mark.asyncio
async def test_circuit_breaker_failure_threshold():
    """Test circuit breaker opens after failure threshold."""
    config = CircuitBreakerConfig(failure_threshold=2, reset_timeout_seconds=0.1)
    circuit_breaker = CircuitBreaker(config)
    
    async def failure_func():
        raise Exception("Simulated failure")
    
    # First failure
    with pytest.raises(Exception):
        await circuit_breaker.call(failure_func)
    
    state_info = circuit_breaker.get_state_info()
    assert state_info['state'] == 'closed'
    assert state_info['failure_count'] == 1
    
    # Second failure - should open circuit
    with pytest.raises(Exception):
        await circuit_breaker.call(failure_func)
    
    state_info = circuit_breaker.get_state_info()
    assert state_info['state'] == 'open'
    
    # Should raise exception when circuit is open
    with pytest.raises(Exception) as exc_info:
        await circuit_breaker.call(failure_func)
    
    assert "Circuit breaker is OPEN" in str(exc_info.value)


@pytest.mark.asyncio
async def test_circuit_breaker_reset():
    """Test circuit breaker reset after timeout."""
    config = CircuitBreakerConfig(failure_threshold=1, reset_timeout_seconds=0.1)
    circuit_breaker = CircuitBreaker(config)
    
    async def failure_func():
        raise Exception("Simulated failure")
    
    async def success_func():
        return "success"
    
    # Cause failure and open circuit
    with pytest.raises(Exception):
        await circuit_breaker.call(failure_func)
    
    state_info = circuit_breaker.get_state_info()
    assert state_info['state'] == 'open'
    
    # Wait for reset timeout
    await asyncio.sleep(0.2)
    
    # Next call should transition to half-open and succeed
    result = await circuit_breaker.call(success_func)
    assert result == "success"
    
    state_info = circuit_breaker.get_state_info()
    assert state_info['state'] == 'closed'
    assert state_info['failure_count'] == 0
