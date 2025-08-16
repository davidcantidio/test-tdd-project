# 🎯 PROMPT K - Security Test Suite Implementation

## CONTEXT
Report.md line 50: "Security testing lacks XSS/CSRF scenarios"
Report.md line 16-22: Security vulnerabilities identified but not tested

## TASK
Create comprehensive security test suite covering XSS, CSRF, SQL Injection, and authentication vulnerabilities.

## TARGET FILE
`tests/test_security_scenarios.py` (CREATE NEW FILE)

## REQUIREMENTS

### 1. XSS Testing (10+ test cases)
```python
def test_xss_script_injection():
    """Test various XSS payloads are properly sanitized"""
    payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "<body onload=alert('XSS')>",
        "javascript:alert('XSS')",
        "<iframe src='javascript:alert(\"XSS\")'></iframe>",
        "<svg onload=alert('XSS')>",
        "';alert('XSS');//",
        "<input type='text' value='x' onmouseover='alert(1)'>",
        "<a href='javascript:alert(1)'>Click</a>",
        "<div style='background:url(javascript:alert(1))'>",
    ]
    # Test each payload is sanitized
```

### 2. CSRF Testing (5+ test cases)
```python
def test_csrf_token_validation():
    """Test CSRF token is required and validated"""
    # Test missing token
    # Test invalid token
    # Test expired token
    # Test token reuse
    # Test token from different session
```

### 3. SQL Injection Testing (10+ test cases)
```python
def test_sql_injection_prevention():
    """Test SQL injection attempts are blocked"""
    injections = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        "' UNION SELECT * FROM users--",
        "1; DELETE FROM epics WHERE 1=1",
        "' OR 1=1--",
        "'; EXEC xp_cmdshell('net user'); --",
        "' AND (SELECT COUNT(*) FROM users) > 0--",
        "1' AND SLEEP(5)--",
        "' OR 'a'='a",
    ]
    # Test each injection is prevented
```

### 4. Authentication Bypass Testing (5+ test cases)
```python
def test_authentication_bypass_attempts():
    """Test various authentication bypass techniques"""
    # Test direct page access without auth
    # Test session hijacking
    # Test cookie manipulation
    # Test JWT token tampering (if applicable)
    # Test privilege escalation
```

### 5. Rate Limiting Testing
```python
def test_rate_limiting_enforcement():
    """Test rate limits are enforced"""
    # Test login attempts limit (5 in 5 minutes)
    # Test API calls limit
    # Test form submission limits
    # Test database query limits
```

### 6. Input Validation Testing
```python
def test_malicious_input_validation():
    """Test various malicious inputs are rejected"""
    # Test command injection
    # Test path traversal
    # Test file upload attacks
    # Test XXE injection
    # Test LDAP injection
```

## IMPLEMENTATION STRUCTURE

```python
import pytest
import sys
from pathlib import Path
from typing import List, Dict, Any
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from streamlit_extension.utils.security import (
    sanitize_input, 
    validate_input,
    security_manager,
    check_rate_limit
)
from streamlit_extension.auth.auth_manager import AuthManager
from streamlit_extension.utils.database import DatabaseManager

class TestSecurityScenarios:
    """Comprehensive security testing suite."""
    
    @pytest.fixture
    def setup_security(self):
        """Setup security components for testing."""
        # Setup code
        yield
        # Teardown code
    
    @pytest.mark.parametrize("payload", [
        "<script>alert('XSS')</script>",
        # ... all XSS payloads
    ])
    def test_xss_prevention(self, payload, setup_security):
        """Test XSS prevention for various payloads."""
        sanitized = sanitize_input(payload)
        assert "<script>" not in sanitized
        assert "javascript:" not in sanitized
        assert "onerror=" not in sanitized
    
    @pytest.mark.parametrize("injection", [
        "'; DROP TABLE users; --",
        # ... all SQL injections
    ])
    def test_sql_injection_prevention(self, injection, setup_security):
        """Test SQL injection prevention."""
        # Test implementation
        pass
    
    def test_csrf_token_required(self, setup_security):
        """Test CSRF token is required for state-changing operations."""
        # Test implementation
        pass
    
    def test_authentication_required(self, setup_security):
        """Test authentication is enforced on protected pages."""
        # Test implementation
        pass
    
    def test_rate_limiting(self, setup_security):
        """Test rate limiting is enforced."""
        # Test implementation
        pass
    
    @pytest.mark.security
    def test_session_security(self, setup_security):
        """Test session security measures."""
        # Test session timeout
        # Test session invalidation
        # Test concurrent session handling
        pass
    
    @pytest.mark.security
    def test_password_security(self, setup_security):
        """Test password security requirements."""
        # Test password hashing (SHA-256)
        # Test salt generation
        # Test password complexity
        pass
    
    def test_file_upload_security(self, setup_security):
        """Test file upload security."""
        # Test file type validation
        # Test file size limits
        # Test malicious file detection
        pass
    
    def test_error_message_security(self, setup_security):
        """Test error messages don't leak sensitive info."""
        # Test database errors are sanitized
        # Test path information is hidden
        # Test stack traces are suppressed in production
        pass

# Performance impact tests
class TestSecurityPerformance:
    """Test security measures don't significantly impact performance."""
    
    @pytest.mark.performance
    def test_sanitization_performance(self):
        """Test input sanitization performance."""
        import time
        start = time.time()
        for _ in range(1000):
            sanitize_input("<script>test</script>")
        duration = time.time() - start
        assert duration < 1.0  # Should process 1000 inputs in < 1 second
    
    @pytest.mark.performance
    def test_validation_performance(self):
        """Test input validation performance."""
        # Similar performance test for validation
        pass

# Integration tests
class TestSecurityIntegration:
    """Test security components work together."""
    
    def test_full_auth_flow_security(self):
        """Test complete authentication flow with security checks."""
        # Test login with CSRF
        # Test session management
        # Test logout
        pass
    
    def test_crud_operations_security(self):
        """Test CRUD operations have proper security."""
        # Test create with validation
        # Test update with authorization
        # Test delete with confirmation
        pass

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "security"])
```

## VALIDATION CHECKLIST
- [ ] All XSS vectors tested and blocked
- [ ] SQL injection attempts prevented
- [ ] CSRF tokens properly validated
- [ ] Authentication bypass attempts blocked
- [ ] Rate limiting enforced correctly
- [ ] No sensitive data in error messages
- [ ] Performance impact acceptable
- [ ] Integration with existing security components

## EXPECTED OUTPUT
```
tests/test_security_scenarios.py::TestSecurityScenarios::test_xss_prevention[<script>alert('XSS')</script>] PASSED
tests/test_security_scenarios.py::TestSecurityScenarios::test_sql_injection_prevention['; DROP TABLE users; --] PASSED
tests/test_security_scenarios.py::TestSecurityScenarios::test_csrf_token_required PASSED
tests/test_security_scenarios.py::TestSecurityScenarios::test_authentication_required PASSED
tests/test_security_scenarios.py::TestSecurityScenarios::test_rate_limiting PASSED
...
===================== 50+ passed in 2.34s =====================
```

## NOTES
- Use existing security components from `streamlit_extension/utils/security.py`
- Ensure tests are isolated and don't affect other tests
- Mark security-critical tests with `@pytest.mark.security`
- Include performance benchmarks for security operations
- Test both positive and negative scenarios