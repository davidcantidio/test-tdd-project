#!/usr/bin/env python3
"""
Security Testing Suite
Comprehensive tests for XSS, CSRF, SQL Injection prevention.
CONFLICT RESOLUTION: Consolidated patches 1 and 2 into unified test suite.
"""

import pytest
import sqlite3
import tempfile
import os
from unittest.mock import Mock, patch
from streamlit_extension.utils.security import SecurityManager, sanitize_input
from streamlit_extension.utils.database import DatabaseManager


class TestXSSPrevention:
    """Test XSS (Cross-Site Scripting) prevention."""

    def test_script_tag_sanitization(self):
        """Test that script tags are properly sanitized."""
        malicious_input = "<script>alert('XSS')</script>"
        sanitized = sanitize_input(malicious_input)
        assert "<script>" not in sanitized
        assert "alert" not in sanitized or "&lt;script&gt;" in sanitized

    def test_javascript_protocol_sanitization(self):
        """Test that javascript: protocol is sanitized."""
        malicious_input = "<a href='javascript:alert(1)'>Click me</a>"
        sanitized = sanitize_input(malicious_input)
        assert "javascript:" not in sanitized

    def test_event_handler_sanitization(self):
        """Test that event handlers are sanitized."""
        malicious_input = "<img src='x' onerror='alert(1)'>"
        sanitized = sanitize_input(malicious_input)
        assert "onerror" not in sanitized or "&quot;" in sanitized

    def test_data_protocol_sanitization(self):
        """Test that data: protocol with scripts is sanitized."""
        malicious_input = "<iframe src='data:text/html,<script>alert(1)</script>'>"
        sanitized = sanitize_input(malicious_input)
        assert "data:text/html" not in sanitized or "&quot;" in sanitized

    def test_svg_script_sanitization(self):
        """Test that SVG with scripts is sanitized."""
        malicious_input = "<svg onload='alert(1)'></svg>"
        sanitized = sanitize_input(malicious_input)
        assert "onload" not in sanitized or "&quot;" in sanitized

    def test_style_expression_sanitization(self):
        """Test that CSS expressions are sanitized."""
        malicious_input = "<div style='expression(alert(1))'></div>"
        sanitized = sanitize_input(malicious_input)
        assert "expression(" not in sanitized

    def test_unicode_bypass_attempt(self):
        """Test that unicode bypass attempts are blocked."""
        malicious_input = "<script>al\\u0065rt(1)</script>"
        sanitized = sanitize_input(malicious_input)
        assert "\\u0065" not in sanitized or "&lt;script&gt;" in sanitized

    def test_nested_tags_sanitization(self):
        """Test that nested malicious tags are sanitized."""
        malicious_input = "<<script>script>alert(1)<</script>/script>"
        sanitized = sanitize_input(malicious_input)
        assert "<script>" not in sanitized


class TestCSRFPrevention:
    """Test CSRF (Cross-Site Request Forgery) prevention."""

    def setup_method(self):
        """Setup for CSRF tests."""
        self.security_manager = SecurityManager()

    def test_csrf_token_generation(self):
        """Test that CSRF tokens are generated properly."""
        token1 = self.security_manager.generate_csrf_token("test_form")
        token2 = self.security_manager.generate_csrf_token("test_form")
        
        assert token1 != token2  # Tokens should be unique
        assert len(token1) >= 32  # Minimum length
        assert isinstance(token1, str)

    def test_csrf_token_validation_success(self):
        """Test successful CSRF token validation."""
        form_id = "test_form"
        token = self.security_manager.generate_csrf_token(form_id)
        
        # Should validate successfully
        assert self.security_manager.validate_csrf_token(token, form_id) is True

    def test_csrf_token_validation_failure(self):
        """Test failed CSRF token validation."""
        form_id = "test_form"
        valid_token = self.security_manager.generate_csrf_token(form_id)
        invalid_token = "invalid_token_12345"
        
        # Should fail validation
        assert self.security_manager.validate_csrf_token(invalid_token, form_id) is False

    def test_csrf_token_reuse_prevention(self):
        """Test that CSRF tokens cannot be reused."""
        form_id = "test_form"
        token = self.security_manager.generate_csrf_token(form_id)
        
        # First use should succeed
        assert self.security_manager.validate_csrf_token(token, form_id) is True
        
        # Second use should fail (one-time use)
        assert self.security_manager.validate_csrf_token(token, form_id) is False

    def test_csrf_token_timing_attack_resistance(self):
        """Test that CSRF validation is resistant to timing attacks."""
        form_id = "test_form"
        valid_token = self.security_manager.generate_csrf_token(form_id)
        invalid_token = "a" * len(valid_token)  # Same length
        
        import time
        
        # Time valid token validation
        start = time.time()
        self.security_manager.validate_csrf_token(valid_token, form_id)
        valid_time = time.time() - start
        
        # Time invalid token validation
        start = time.time()
        self.security_manager.validate_csrf_token(invalid_token, form_id)
        invalid_time = time.time() - start
        
        # Should take similar time (constant-time comparison)
        time_diff = abs(valid_time - invalid_time)
        assert time_diff < 0.001  # Less than 1ms difference


class TestSQLInjectionPrevention:
    """Test SQL Injection prevention."""

    def setup_method(self):
        """Setup test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        self.db_manager = DatabaseManager(
            framework_db_path=self.temp_db.name,
            timer_db_path=self.temp_db.name
        )
        
        # Create test table
        with sqlite3.connect(self.temp_db.name) as conn:
            conn.execute("""
                CREATE TABLE test_users (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    email TEXT
                )
            """)
            conn.execute("INSERT INTO test_users (name, email) VALUES ('Test User', 'test@example.com')")
            conn.commit()

    def teardown_method(self):
        """Cleanup test database."""
        os.unlink(self.temp_db.name)

    def test_parameterized_query_protection(self):
        """Test that parameterized queries prevent injection."""
        malicious_input = "'; DROP TABLE test_users; --"
        
        # This should not drop the table due to parameterization
        try:
            with sqlite3.connect(self.temp_db.name) as conn:
                cursor = conn.execute("SELECT * FROM test_users WHERE name = ?", (malicious_input,))
                results = cursor.fetchall()
                assert len(results) == 0  # No matching records
        except sqlite3.Error:
            pytest.fail("SQL injection attempt caused database error")
        
        # Verify table still exists
        with sqlite3.connect(self.temp_db.name) as conn:
