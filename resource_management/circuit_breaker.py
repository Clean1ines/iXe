import asyncio
import logging
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit broken, requests blocked
    HALF_OPEN = "half_open" # Testing if circuit can be closed

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 3
    timeout_seconds: int = 60
    reset_timeout_seconds: int = 30

class CircuitBreaker:
    """Circuit breaker pattern for browser resource resilience."""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_attempt_time: Optional[datetime] = None
        self._lock = asyncio.Lock()
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker transitioning to HALF_OPEN for reset attempt")
                else:
                    raise Exception("Circuit breaker is OPEN - requests blocked")
                    
        try:
            result = await func(*args, **kwargs)
            
            async with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    logger.info("Circuit breaker reset successful, transitioning to CLOSED")
                    self._reset()
                return result
                
        except Exception as e:
            async with self._lock:
                self._record_failure()
                if self.failure_count >= self.config.failure_threshold:
                    logger.warning(f"Circuit breaker OPENING after {self.failure_count} failures")
                    self.state = CircuitState.OPEN
                    self.last_failure_time = datetime.now()
                    
            raise e
            
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt circuit reset."""
        if not self.last_failure_time:
            return True
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.config.reset_timeout_seconds)
        
    def _record_failure(self):
        """Record a failure and update state."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
    def _reset(self):
        """Reset circuit breaker state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.last_attempt_time = None
        
    def get_state_info(self) -> dict:
        """Get current circuit breaker state information."""
        return {
            'state': self.state.value,
            'failure_count': self.failure_count,
            'last_failure_time': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'should_reset': self._should_attempt_reset()
        }
