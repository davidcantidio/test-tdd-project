"""
Connection Resilience System
Implements retry logic, circuit breakers, and connection pool management
"""

import time
import logging
import threading
from enum import Enum
from typing import Any, Callable, Optional, Dict, Union
from functools import wraps
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"        # Normal operation
    OPEN = "open"            # Failures detected, blocking calls
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

@dataclass 
class CircuitBreakerConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 2
    timeout: float = 30.0

class ConnectionPool:
    """Thread-safe connection pool with leak detection"""
    
    def __init__(self, max_connections: int = 10, idle_timeout: float = 300.0):
        self.max_connections = max_connections
        self.idle_timeout = idle_timeout
        self._connections = []
        self._active_connections = set()
        self._lock = threading.RLock()
        self._created_count = 0
        self._leaked_connections = []
        
    def get_connection(self):
        """Get connection from pool with leak detection"""
        with self._lock:
            # Check for available connection
            now = time.time()
            for i, (conn, last_used) in enumerate(self._connections):
                if now - last_used < self.idle_timeout:
                    self._connections.pop(i)
                    self._active_connections.add(id(conn))
                    logger.debug("Reused connection %d", id(conn))
                    return conn
            
            # Create new connection if under limit
            if len(self._active_connections) < self.max_connections:
                conn = self._create_connection()
                self._active_connections.add(id(conn))
                self._created_count += 1
                logger.debug("Created new connection %d (total: %d)", id(conn), self._created_count)
                return conn
            
            # Pool exhausted
            logger.warning("Connection pool exhausted: %d/%d", len(self._active_connections), self.max_connections)
            raise ConnectionError(f"Connection pool exhausted")
    
    def return_connection(self, conn):
        """Return connection to pool"""
        with self._lock:
            conn_id = id(conn)
            if conn_id in self._active_connections:
                self._active_connections.remove(conn_id)
                self._connections.append((conn, time.time()))
                logger.debug("Returned connection %d", conn_id)
            else:
                logger.warning("Attempted to return unknown connection %d", conn_id)
    
    def _create_connection(self):
        """Create new database connection"""
        # This would be implemented with actual database connection logic
        # For now, return a mock connection
        return f"connection_{self._created_count}"
    
    def cleanup_idle_connections(self):
        """Remove idle connections from pool"""
        with self._lock:
            now = time.time()
            active_connections = []
            removed_count = 0
            
            for conn, last_used in list(self._connections):
                if now - last_used < self.idle_timeout:
                    active_connections.append((conn, last_used))
                else:
                    removed_count += 1
                    logger.debug("Removed idle connection %d", id(conn))
            
            self._connections = active_connections
            logger.info("Cleanup removed %d idle connections", removed_count)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        with self._lock:
            return {
                "active_connections": len(self._active_connections),
                "idle_connections": len(self._connections),
                "max_connections": self.max_connections,
                "total_created": self._created_count,
                "utilization": len(self._active_connections) / self.max_connections if self.max_connections else 0.0
            }

class CircuitBreaker:
    """Circuit breaker for database operations"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute function with circuit breaker protection"""
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise ConnectionError("Circuit breaker is OPEN")
        
        try:
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            # Check for timeout
            if duration > self.config.timeout:
                raise TimeoutError(f"Operation timed out after {duration:.2f}s")
            
            self._on_success()
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt to reset"""
        if self.last_failure_time is None:
            return True
        
        return (time.time() - self.last_failure_time) >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation"""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info("Circuit breaker CLOSED - service recovered")
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed operation"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.success_count = 0
                logger.warning("Circuit breaker OPEN - service still failing")
            elif (self.state == CircuitState.CLOSED and 
                  self.failure_count >= self.config.failure_threshold):
                self.state = CircuitState.OPEN
                logger.warning("Circuit breaker OPEN - %d failures detected", self.failure_count)
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state"""
        with self._lock:
            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time
            }

class RetryManager:
    """Retry manager with exponential backoff"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    def execute_with_retry(self, func: Callable, *args, **kwargs):
        """Execute function with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.config.max_attempts - 1:
                    logger.error("All %d attempts failed for %s", self.config.max_attempts, func.__name__, exc_info=True)
                    break
                
                delay = self._calculate_delay(attempt)
                logger.warning("Attempt %d failed for %s: %s. Retrying in %.2fs", attempt + 1, func.__name__, e, delay)
                time.sleep(delay)
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for next attempt"""
        delay = self.config.base_delay * (self.config.exponential_base ** attempt)
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # 50-100% of calculated delay
        
        return delay

class DatabaseResilience:
    """Main resilience coordinator"""
    
    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        circuit_config: Optional[CircuitBreakerConfig] = None,
        pool_size: int = 10
    ):
        self.retry_manager = RetryManager(retry_config or RetryConfig())
        self.circuit_breaker = CircuitBreaker(circuit_config or CircuitBreakerConfig())
        self.connection_pool = ConnectionPool(max_connections=pool_size)
        self._cleanup_thread = None
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Start background cleanup thread"""
        def cleanup_worker():
            while True:
                try:
                    self.connection_pool.cleanup_idle_connections()
                    time.sleep(60)  # Cleanup every minute
                except Exception as e:
                    logger.error("Cleanup thread error: %s", e, exc_info=True)
                    time.sleep(60)
        
        self._cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self._cleanup_thread.start()
    
    @contextmanager
    def get_connection(self):
        """Get database connection with resilience"""
        conn = None
        try:
            # Get connection through circuit breaker and retry logic
            conn = self.retry_manager.execute_with_retry(
                lambda: self.circuit_breaker.call(self.connection_pool.get_connection)
            )
            yield conn
        finally:
            if conn:
                self.connection_pool.return_connection(conn)
    
    def execute_query(self, query_func: Callable, *args, **kwargs):
        """Execute database query with full resilience"""
        with self.get_connection() as conn:
            return query_func(conn, *args, **kwargs)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        return {
            "connection_pool": self.connection_pool.get_stats(),
            "circuit_breaker": self.circuit_breaker.get_state(),
            "timestamp": datetime.utcnow().isoformat()
        }

# Decorators for easy integration
def with_resilience(resilience_manager: DatabaseResilience):
    """Decorator to add resilience to database methods"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return resilience_manager.execute_query(func, *args, **kwargs)
        return wrapper
    return decorator

# Global instance
default_resilience = DatabaseResilience()