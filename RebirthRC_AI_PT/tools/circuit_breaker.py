"""
Circuit Breaker Pattern Implementation
Prevents cascading failures and provides graceful degradation
"""

import time
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker for protecting against cascading failures
    
    Intelligence: Learns failure patterns and adapts thresholds
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2,
        half_open_max_calls: int = 3
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.half_open_max_calls = half_open_max_calls
        
        # State
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        
        # Intelligence: Track patterns
        self.failure_history = []
        self.recovery_attempts = 0
        self.total_calls = 0
        self.total_failures = 0
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        """
        self.total_calls += 1
        
        # Check if circuit is open
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Wait {self._time_until_retry():.1f}s before retry."
                )
        
        # Limit calls in half-open state
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls >= self.half_open_max_calls:
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is HALF_OPEN and at max test calls"
                )
            self.half_open_calls += 1
        
        # Execute the function
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure(e)
            raise
    
    def _on_success(self):
        """Handle successful call"""
        self.success_count += 1
        
        if self.state == CircuitState.HALF_OPEN:
            if self.success_count >= self.success_threshold:
                self._transition_to_closed()
        else:
            # Reset failure count on success in closed state
            self.failure_count = 0
    
    def _on_failure(self, exception: Exception):
        """Handle failed call"""
        self.failure_count += 1
        self.total_failures += 1
        self.last_failure_time = time.time()
        
        # Record failure for intelligence
        self.failure_history.append({
            'time': time.time(),
            'exception': str(exception),
            'state': self.state.value
        })
        
        # Keep only last 100 failures
        if len(self.failure_history) > 100:
            self.failure_history = self.failure_history[-100:]
        
        if self.state == CircuitState.HALF_OPEN:
            # Failed during recovery, go back to open
            self._transition_to_open()
        elif self.failure_count >= self.failure_threshold:
            self._transition_to_open()
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return False
        
        time_since_failure = time.time() - self.last_failure_time
        
        # Intelligence: Increase timeout after multiple failed recovery attempts
        adjusted_timeout = self.recovery_timeout * (1.5 ** min(self.recovery_attempts, 5))
        
        return time_since_failure >= adjusted_timeout
    
    def _time_until_retry(self) -> float:
        """Calculate time until next retry attempt"""
        if self.last_failure_time is None:
            return 0
        
        time_since_failure = time.time() - self.last_failure_time
        adjusted_timeout = self.recovery_timeout * (1.5 ** min(self.recovery_attempts, 5))
        
        return max(0, adjusted_timeout - time_since_failure)
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        self.state = CircuitState.OPEN
        self.recovery_attempts += 1
        print(f"[CircuitBreaker:{self.name}] Transitioned to OPEN (failures: {self.failure_count})")
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.half_open_calls = 0
        self.success_count = 0
        self.failure_count = 0
        print(f"[CircuitBreaker:{self.name}] Transitioned to HALF_OPEN (testing recovery)")
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.half_open_calls = 0
        self.recovery_attempts = 0
        print(f"[CircuitBreaker:{self.name}] Transitioned to CLOSED (recovered)")
    
    def reset(self):
        """Manually reset circuit breaker"""
        self._transition_to_closed()
        self.last_failure_time = None
    
    def get_stats(self) -> dict:
        """Get circuit breaker statistics"""
        return {
            'name': self.name,
            'state': self.state.value,
            'total_calls': self.total_calls,
            'total_failures': self.total_failures,
            'failure_rate': self.total_failures / max(self.total_calls, 1),
            'current_failure_count': self.failure_count,
            'recovery_attempts': self.recovery_attempts,
            'recent_failures': len(self.failure_history),
            'time_until_retry': self._time_until_retry() if self.state == CircuitState.OPEN else 0
        }


class CircuitBreakerOpenError(Exception):
    """Exception raised when circuit breaker is open"""
    pass


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 60
):
    """
    Decorator for applying circuit breaker to functions
    
    Usage:
        @circuit_breaker('api_call', failure_threshold=3, recovery_timeout=30)
        def call_external_api():
            # ... API call logic
            pass
    """
    breaker = CircuitBreaker(name, failure_threshold, recovery_timeout)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        # Attach breaker to function for access to stats
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator


# Example usage and testing
if __name__ == '__main__':
    print("=== Testing Circuit Breaker ===\n")
    
    # Create a circuit breaker
    breaker = CircuitBreaker('test_service', failure_threshold=3, recovery_timeout=5)
    
    def unreliable_service(should_fail=False):
        """Simulated unreliable service"""
        if should_fail:
            raise Exception("Service failed!")
        return "Success"
    
    # Test normal operation
    print("1. Normal operation (CLOSED state):")
    for i in range(3):
        try:
            result = breaker.call(unreliable_service, should_fail=False)
            print(f"   Call {i+1}: {result}")
        except Exception as e:
            print(f"   Call {i+1}: Failed - {e}")
    
    print(f"\nStats: {breaker.get_stats()}\n")
    
    # Test failures
    print("2. Triggering failures:")
    for i in range(5):
        try:
            result = breaker.call(unreliable_service, should_fail=True)
            print(f"   Call {i+1}: {result}")
        except CircuitBreakerOpenError as e:
            print(f"   Call {i+1}: Circuit OPEN - {e}")
        except Exception as e:
            print(f"   Call {i+1}: Failed - {e}")
    
    print(f"\nStats: {breaker.get_stats()}\n")
    
    # Test circuit is open
    print("3. Circuit is OPEN, requests rejected:")
    try:
        breaker.call(unreliable_service, should_fail=False)
    except CircuitBreakerOpenError as e:
        print(f"   {e}")
    
    print(f"\nStats: {breaker.get_stats()}\n")
    
    # Test recovery
    print("4. Waiting for recovery timeout...")
    time.sleep(6)
    
    print("5. Testing recovery (HALF_OPEN state):")
    for i in range(3):
        try:
            result = breaker.call(unreliable_service, should_fail=False)
            print(f"   Call {i+1}: {result}")
        except Exception as e:
            print(f"   Call {i+1}: Failed - {e}")
    
    print(f"\nFinal Stats: {breaker.get_stats()}\n")
    print("=== Circuit Breaker Test Complete ===")
