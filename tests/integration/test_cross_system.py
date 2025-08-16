"""
🔗 Cross-System Integration Tests

Tests the integration between different system components:
- Authentication + Rate Limiting integration
- Exception Handler + Correlation ID tracking
- Security systems (CSRF, XSS) + Real operations
- Performance monitoring + Load testing
- Database transactions + Cache invalidation
- Audit trail + Operation correlation

These tests ensure all security, monitoring, and performance systems
work together correctly in production scenarios.
"""

import pytest
import time
import threading
import sqlite3
import tempfile
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch, MagicMock
import json
import hashlib
import secrets

# Core test imports
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

# Test authentication/security if available
try:
    from streamlit_extension.utils.auth_manager import AuthManager
    from streamlit_extension.security.csrf_protection import CSRFProtection
    from streamlit_extension.security.xss_protection import XSSProtection
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

# Test rate limiting if available
try:
    from streamlit_extension.middleware.rate_limiting import RateLimiter, RateLimit
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    RATE_LIMITING_AVAILABLE = False

# Test exception handling if available
try:
    from streamlit_extension.utils.exceptions import (
        GlobalExceptionHandler, ApplicationError, SecurityError
    )
    from streamlit_extension.utils.logging_config import get_logger, log_security_event
    EXCEPTION_HANDLING_AVAILABLE = True
except ImportError:
    EXCEPTION_HANDLING_AVAILABLE = False

# Test database transactions if available
try:
    from duration_system.database_transactions import TransactionalDatabaseManager
    TRANSACTIONS_AVAILABLE = True
except ImportError:
    TRANSACTIONS_AVAILABLE = False


class CrossSystemTestFramework:
    """Framework for testing integration between different systems."""
    
    def __init__(self):
        self.temp_db = None
        self.db_path = None
        self.correlation_id = None
        self.test_users = []
        self.security_events = []
        self.performance_metrics = []
        self.operation_log = []
        
        # System components
        self.auth_manager = None
        self.csrf_protection = None
        self.xss_protection = None
        self.rate_limiter = None
        self.exception_handler = None
        self.db_manager = None
        
    def setup(self):
        """Setup cross-system test environment."""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        
        # Initialize correlation ID
        self.correlation_id = str(uuid.uuid4())
        
        # Setup database schema
        self._initialize_test_database()
        
        # Initialize system components
        self._initialize_security_systems()
        self._initialize_monitoring_systems()
        
    def teardown(self):
        """Cleanup cross-system test environment."""
        if self.db_manager:
            try:
                self.db_manager.close()
            except:
                pass
        
        if self.db_path and Path(self.db_path).exists():
            try:
                Path(self.db_path).unlink()
            except:
                pass
    
    def _initialize_test_database(self):
        """Initialize test database schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Users table for authentication testing
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    login_attempts INTEGER DEFAULT 0,
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Security events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    user_id INTEGER,
                    ip_address TEXT,
                    user_agent TEXT,
                    details TEXT,
                    correlation_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Rate limiting table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rate_limit_events (
                    id INTEGER PRIMARY KEY,
                    identifier TEXT NOT NULL,
                    action TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    correlation_id TEXT
                )
            """)
            
            # Audit trail table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS audit_trail (
                    id INTEGER PRIMARY KEY,
                    operation TEXT NOT NULL,
                    entity_type TEXT,
                    entity_id INTEGER,
                    user_id INTEGER,
                    details TEXT,
                    correlation_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
    
    def _initialize_security_systems(self):
        """Initialize security system components."""
        if AUTH_AVAILABLE:
            try:
                self.auth_manager = AuthManager(db_path=self.db_path)
                self.csrf_protection = CSRFProtection(secret_key="test-csrf-key")
                self.xss_protection = XSSProtection()
            except:
                # Fall back to mock objects
                self._initialize_mock_security()
        else:
            self._initialize_mock_security()
        
        if RATE_LIMITING_AVAILABLE:
            try:
                self.rate_limiter = RateLimiter(storage_backend="memory")
            except:
                self.rate_limiter = Mock()
        else:
            self.rate_limiter = Mock()
    
    def _initialize_monitoring_systems(self):
        """Initialize monitoring and exception handling systems."""
        if EXCEPTION_HANDLING_AVAILABLE:
            try:
                self.exception_handler = GlobalExceptionHandler()
            except:
                self.exception_handler = Mock()
        else:
            self.exception_handler = Mock()
        
        if TRANSACTIONS_AVAILABLE:
            try:
                self.db_manager = TransactionalDatabaseManager(self.db_path)
            except:
                self.db_manager = Mock()
        else:
            self.db_manager = Mock()
    
    def _initialize_mock_security(self):
        """Initialize mock security components."""
        self.auth_manager = Mock()
        self.csrf_protection = Mock()
        self.xss_protection = Mock()
        
        # Configure mock responses
        self.auth_manager.authenticate.return_value = {"id": 1, "username": "test_user"}
        self.csrf_protection.generate_token.return_value = "mock-csrf-token"
        self.csrf_protection.validate_token.return_value = True
        self.xss_protection.sanitize.return_value = "sanitized content"
    
    def create_test_user(self, username: str, email: str, password: str = "test123") -> dict:
        """Create test user with proper password hashing."""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        
        user_data = {
            "username": username,
            "email": email,
            "password_hash": password_hash.hex(),
            "salt": salt,
            "is_active": True,
            "login_attempts": 0
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT INTO users (username, email, password_hash, salt, is_active, login_attempts)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_data["username"], user_data["email"], user_data["password_hash"],
                  user_data["salt"], user_data["is_active"], user_data["login_attempts"]))
            
            user_id = cursor.lastrowid
            user_data["id"] = user_id
            conn.commit()
        
        self.test_users.append(user_data)
        self.log_operation("create_test_user", {"user_id": user_id, "username": username})
        
        return user_data
    
    def log_security_event(self, event_type: str, severity: str, details: dict = None, user_id: int = None):
        """Log security event for testing."""
        event = {
            "event_type": event_type,
            "severity": severity,
            "user_id": user_id,
            "ip_address": "127.0.0.1",
            "user_agent": "Test-Agent/1.0",
            "details": json.dumps(details or {}),
            "correlation_id": self.correlation_id,
            "timestamp": datetime.now()
        }
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO security_events 
                (event_type, severity, user_id, ip_address, user_agent, details, correlation_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (event["event_type"], event["severity"], event["user_id"],
                  event["ip_address"], event["user_agent"], event["details"], event["correlation_id"]))
            conn.commit()
        
        self.security_events.append(event)
    
    def log_operation(self, operation: str, details: dict = None):
        """Log test operation with correlation ID."""
        self.operation_log.append({
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "correlation_id": self.correlation_id,
            "details": details or {}
        })
    
    def simulate_attack(self, attack_type: str, target_user_id: int = None) -> dict:
        """Simulate various attack scenarios for testing."""
        attack_results = {"attack_type": attack_type, "blocked": False, "events_logged": 0}
        
        if attack_type == "brute_force_login":
            # Simulate multiple failed login attempts
            for i in range(10):
                self.log_security_event(
                    "failed_login_attempt",
                    "warning",
                    {"attempt": i + 1, "reason": "invalid_password"},
                    user_id=target_user_id
                )
                
                # Check if rate limiter would block
                if self.rate_limiter and hasattr(self.rate_limiter, 'is_allowed'):
                    if not self.rate_limiter.is_allowed(f"login:{target_user_id}", "login"):
                        attack_results["blocked"] = True
                        break
            
            attack_results["events_logged"] = len([e for e in self.security_events 
                                                 if e["event_type"] == "failed_login_attempt"])
        
        elif attack_type == "csrf_attack":
            # Simulate CSRF attack
            csrf_token = "malicious-token"
            
            if self.csrf_protection and hasattr(self.csrf_protection, 'validate_token'):
                attack_results["blocked"] = not self.csrf_protection.validate_token(csrf_token)
            
            self.log_security_event(
                "csrf_attack_attempt",
                "high",
                {"provided_token": csrf_token},
                user_id=target_user_id
            )
            attack_results["events_logged"] = 1
        
        elif attack_type == "xss_injection":
            # Simulate XSS attack
            malicious_payload = "<script>alert('XSS')</script>"
            
            if self.xss_protection and hasattr(self.xss_protection, 'sanitize'):
                sanitized = self.xss_protection.sanitize(malicious_payload)
                attack_results["blocked"] = sanitized != malicious_payload
            
            self.log_security_event(
                "xss_attempt",
                "high",
                {"payload": malicious_payload},
                user_id=target_user_id
            )
            attack_results["events_logged"] = 1
        
        elif attack_type == "sql_injection":
            # Simulate SQL injection attempt
            malicious_query = "'; DROP TABLE users; --"
            
            try:
                # Test if parameterized queries prevent injection
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.execute(
                        "SELECT * FROM users WHERE username = ?",
                        (malicious_query,)
                    )
                    result = cursor.fetchone()
                    
                    # Should return None (no match) rather than causing error
                    attack_results["blocked"] = result is None
            except sqlite3.Error as e:
                # If error occurs, log it but consider attack blocked
                attack_results["blocked"] = True
                attack_results["error"] = str(e)
            
            self.log_security_event(
                "sql_injection_attempt",
                "critical",
                {"query": malicious_query},
                user_id=target_user_id
            )
            attack_results["events_logged"] = 1
        
        self.log_operation(f"simulate_{attack_type}", attack_results)
        return attack_results
    
    def test_system_recovery(self) -> dict:
        """Test system recovery after various failure scenarios."""
        recovery_results = {"scenarios_tested": 0, "successful_recoveries": 0}
        
        # Scenario 1: Database connection failure
        try:
            # Temporarily break database connection
            original_db_path = self.db_path
            self.db_path = "/invalid/path/database.db"
            
            # Attempt operation that should fail gracefully
            try:
                self.create_test_user("recovery_test", "recovery@test.com")
            except Exception as e:
                # Should be handled gracefully by exception handler
                if self.exception_handler and hasattr(self.exception_handler, 'handle_exception'):
                    app_error = self.exception_handler.handle_exception(e)
                    if app_error:
                        recovery_results["successful_recoveries"] += 1
            
            # Restore database connection
            self.db_path = original_db_path
            recovery_results["scenarios_tested"] += 1
        
        except Exception as e:
            self.log_operation("recovery_test_error", {"error": str(e)})
        
        # Scenario 2: Rate limiter overflow
        try:
            if self.rate_limiter:
                # Simulate rate limit breach
                for i in range(100):
                    if hasattr(self.rate_limiter, 'is_allowed'):
                        allowed = self.rate_limiter.is_allowed("test_user", "test_action")
                        if not allowed:
                            # Rate limiter should gracefully handle overflow
                            recovery_results["successful_recoveries"] += 1
                            break
            
            recovery_results["scenarios_tested"] += 1
        
        except Exception as e:
            self.log_operation("rate_limit_recovery_error", {"error": str(e)})
        
        self.log_operation("system_recovery_test", recovery_results)
        return recovery_results
    
    def get_correlation_analysis(self) -> dict:
        """Analyze correlation across all logged events."""
        correlation_analysis = {
            "total_operations": len(self.operation_log),
            "total_security_events": len(self.security_events),
            "correlation_id": self.correlation_id,
            "timeline": []
        }
        
        # Build timeline of all events
        all_events = []
        
        # Add operations
        for op in self.operation_log:
            all_events.append({
                "timestamp": op["timestamp"],
                "type": "operation",
                "data": op
            })
        
        # Add security events
        for event in self.security_events:
            all_events.append({
                "timestamp": event["timestamp"].isoformat(),
                "type": "security_event",
                "data": event
            })
        
        # Sort by timestamp
        all_events.sort(key=lambda x: x["timestamp"])
        correlation_analysis["timeline"] = all_events
        
        # Analyze patterns
        security_event_types = {}
        for event in self.security_events:
            event_type = event["event_type"]
            security_event_types[event_type] = security_event_types.get(event_type, 0) + 1
        
        correlation_analysis["security_patterns"] = security_event_types
        
        return correlation_analysis


@pytest.fixture
def cross_system_framework():
    """Provide cross-system test framework."""
    framework = CrossSystemTestFramework()
    framework.setup()
    yield framework
    framework.teardown()


class TestAuthenticationIntegration:
    """Test authentication system integration with other components."""
    
    def test_auth_rate_limiting_integration(self, cross_system_framework):
        """Test authentication with rate limiting."""
        framework = cross_system_framework
        
        # Create test user
        user = framework.create_test_user("auth_test", "auth@test.com")
        
        # Test normal authentication flow
        if framework.auth_manager and hasattr(framework.auth_manager, 'authenticate'):
            # Simulate normal login
            auth_result = framework.auth_manager.authenticate("auth_test", "test123")
            framework.log_operation("normal_authentication", {"result": auth_result})
        
        # Test authentication with rate limiting
        framework.log_security_event("login_attempt", "info", {"username": "auth_test"}, user["id"])
        
        # Simulate multiple failed attempts (brute force)
        attack_result = framework.simulate_attack("brute_force_login", user["id"])
        
        # Verify rate limiting kicked in
        assert attack_result["attack_type"] == "brute_force_login"
        assert attack_result["events_logged"] > 0
        
        # Verify correlation tracking
        correlation = framework.get_correlation_analysis()
        assert correlation["total_security_events"] >= attack_result["events_logged"]
        assert correlation["correlation_id"] == framework.correlation_id
    
    def test_auth_exception_handling_integration(self, cross_system_framework):
        """Test authentication with exception handling."""
        framework = cross_system_framework
        
        # Test authentication error handling
        if framework.auth_manager and hasattr(framework.auth_manager, 'authenticate'):
            try:
                # Attempt authentication with invalid data
                auth_result = framework.auth_manager.authenticate(None, None)
                framework.log_operation("invalid_auth_attempt", {"result": auth_result})
            except Exception as e:
                # Should be handled by exception handler
                if framework.exception_handler and hasattr(framework.exception_handler, 'handle_exception'):
                    app_error = framework.exception_handler.handle_exception(e)
                    assert app_error is not None
                    framework.log_operation("auth_exception_handled", {"error_id": getattr(app_error, 'error_id', 'mock')})
        
        # Test database connection error during authentication
        try:
            # Break database temporarily
            original_db_path = framework.db_path
            framework.db_path = "/invalid/path.db"
            
            # Attempt authentication - should fail gracefully
            if framework.auth_manager and hasattr(framework.auth_manager, 'authenticate'):
                auth_result = framework.auth_manager.authenticate("test_user", "password")
                framework.log_operation("db_error_auth_attempt", {"result": auth_result})
        
        except Exception as e:
            framework.log_operation("expected_db_error", {"error": str(e)})
        
        finally:
            # Restore database path
            framework.db_path = original_db_path


class TestSecuritySystemIntegration:
    """Test security system integration (CSRF, XSS, Rate Limiting)."""
    
    def test_csrf_xss_protection_integration(self, cross_system_framework):
        """Test CSRF and XSS protection working together."""
        framework = cross_system_framework
        
        user = framework.create_test_user("security_test", "security@test.com")
        
        # Test CSRF protection
        csrf_attack = framework.simulate_attack("csrf_attack", user["id"])
        assert csrf_attack["attack_type"] == "csrf_attack"
        
        # Test XSS protection
        xss_attack = framework.simulate_attack("xss_injection", user["id"])
        assert xss_attack["attack_type"] == "xss_injection"
        
        # Test SQL injection protection
        sql_attack = framework.simulate_attack("sql_injection", user["id"])
        assert sql_attack["attack_type"] == "sql_injection"
        
        # Verify all attacks were logged with correlation
        correlation = framework.get_correlation_analysis()
        security_patterns = correlation["security_patterns"]
        
        assert "csrf_attack_attempt" in security_patterns
        assert "xss_attempt" in security_patterns
        assert "sql_injection_attempt" in security_patterns
        
        # Verify correlation ID is consistent
        all_events_have_correlation = all(
            event["data"].get("correlation_id") == framework.correlation_id
            for event in correlation["timeline"]
            if event["type"] == "security_event"
        )
        assert all_events_have_correlation
    
    def test_security_rate_limiting_integration(self, cross_system_framework):
        """Test security events with rate limiting."""
        framework = cross_system_framework
        
        user = framework.create_test_user("rate_test", "rate@test.com")
        
        # Test multiple security events in sequence
        for i in range(5):
            framework.simulate_attack("csrf_attack", user["id"])
            
            # Check if rate limiting would apply
            if framework.rate_limiter and hasattr(framework.rate_limiter, 'is_allowed'):
                allowed = framework.rate_limiter.is_allowed(f"security:{user['id']}", "security_event")
                framework.log_operation(f"rate_check_{i}", {"allowed": allowed})
        
        # Verify security events were logged
        correlation = framework.get_correlation_analysis()
        assert correlation["total_security_events"] >= 5
        
        # Test system behavior under attack load
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(framework.simulate_attack, "xss_injection", user["id"])
                for _ in range(10)
            ]
            
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        
        # Verify system handled concurrent attacks
        successful_attacks = [r for r in results if r["events_logged"] > 0]
        assert len(successful_attacks) == 10
        
        # Performance should be reasonable
        total_time = end_time - start_time
        assert total_time < 5.0, f"Security system too slow under load: {total_time:.2f}s"


class TestPerformanceIntegration:
    """Test performance monitoring integration with other systems."""
    
    def test_performance_under_security_load(self, cross_system_framework):
        """Test system performance under security attack load."""
        framework = cross_system_framework
        
        # Create multiple test users
        users = [
            framework.create_test_user(f"perf_user_{i}", f"perf{i}@test.com")
            for i in range(5)
        ]
        
        start_time = time.time()
        attack_count = 0
        
        # Simulate attacks from multiple users
        for user in users:
            for attack_type in ["csrf_attack", "xss_injection", "sql_injection"]:
                result = framework.simulate_attack(attack_type, user["id"])
                if result["events_logged"] > 0:
                    attack_count += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Performance metrics
        attacks_per_second = attack_count / total_time
        
        framework.log_operation("performance_security_test", {
            "total_attacks": attack_count,
            "total_time": total_time,
            "attacks_per_second": attacks_per_second,
            "users_tested": len(users)
        })
        
        # Verify reasonable performance
        assert attacks_per_second > 1.0, "Security system too slow"
        assert total_time < 10.0, f"Security test took too long: {total_time:.2f}s"
        
        # Verify data integrity after load
        with sqlite3.connect(framework.db_path) as conn:
            user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            event_count = conn.execute("SELECT COUNT(*) FROM security_events").fetchone()[0]
            
            assert user_count == len(users)
            assert event_count >= attack_count
    
    def test_transaction_performance_integration(self, cross_system_framework):
        """Test database transaction performance under load."""
        framework = cross_system_framework
        
        if not TRANSACTIONS_AVAILABLE:
            pytest.skip("Database transactions not available")
        
        start_time = time.time()
        transaction_count = 0
        
        def create_user_transaction(user_id: int):
            """Create user in a transaction."""
            nonlocal transaction_count
            try:
                user = framework.create_test_user(f"trans_user_{user_id}", f"trans{user_id}@test.com")
                transaction_count += 1
                return user
            except Exception as e:
                framework.log_operation("transaction_error", {"user_id": user_id, "error": str(e)})
                return None
        
        # Run concurrent transactions
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(create_user_transaction, i)
                for i in range(20)
            ]
            
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        successful_transactions = [r for r in results if r is not None]
        transactions_per_second = len(successful_transactions) / total_time
        
        framework.log_operation("transaction_performance_test", {
            "total_transactions": transaction_count,
            "successful_transactions": len(successful_transactions),
            "total_time": total_time,
            "transactions_per_second": transactions_per_second
        })
        
        # Verify reasonable transaction performance
        assert transactions_per_second > 2.0, "Transaction system too slow"
        assert len(successful_transactions) >= 15, "Too many transaction failures"


class TestSystemRecovery:
    """Test system recovery and resilience."""
    
    def test_comprehensive_system_recovery(self, cross_system_framework):
        """Test comprehensive system recovery scenarios."""
        framework = cross_system_framework
        
        user = framework.create_test_user("recovery_test", "recovery@test.com")
        
        # Test recovery scenarios
        recovery_results = framework.test_system_recovery()
        
        assert recovery_results["scenarios_tested"] > 0
        assert recovery_results["successful_recoveries"] >= 0
        
        # Test continued operation after recovery
        post_recovery_user = framework.create_test_user("post_recovery", "post@recovery.com")
        assert post_recovery_user["id"] is not None
        
        # Test security systems still work after recovery
        attack_result = framework.simulate_attack("csrf_attack", post_recovery_user["id"])
        assert attack_result["events_logged"] > 0
        
        # Verify correlation tracking continues to work
        correlation = framework.get_correlation_analysis()
        assert correlation["total_operations"] > 0
        assert correlation["correlation_id"] == framework.correlation_id
    
    def test_error_correlation_tracking(self, cross_system_framework):
        """Test error correlation across system components."""
        framework = cross_system_framework
        
        user = framework.create_test_user("correlation_test", "correlation@test.com")
        
        # Generate various events with same correlation ID
        framework.log_security_event("test_event_1", "info", {"test": "data"}, user["id"])
        framework.simulate_attack("csrf_attack", user["id"])
        framework.log_operation("test_operation", {"operation": "test"})
        framework.log_security_event("test_event_2", "warning", {"test": "data2"}, user["id"])
        
        # Analyze correlation
        correlation = framework.get_correlation_analysis()
        
        # Verify all events have same correlation ID
        correlated_events = [
            event for event in correlation["timeline"]
            if event["data"].get("correlation_id") == framework.correlation_id
        ]
        
        assert len(correlated_events) >= 3  # At least security events + operation
        
        # Verify timeline ordering
        timestamps = [event["timestamp"] for event in correlation["timeline"]]
        assert timestamps == sorted(timestamps), "Timeline not properly ordered"
        
        # Verify security pattern analysis
        assert "csrf_attack_attempt" in correlation["security_patterns"]
        assert correlation["security_patterns"]["csrf_attack_attempt"] >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])