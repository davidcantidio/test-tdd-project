"""
🧪 Test Suite for JSON Security Module

Comprehensive tests for JSON security validation and sanitization.
Tests all security features including:
- Input validation
- Injection attack prevention
- Size and depth limits
- Dangerous key detection
- Sanitization capabilities
"""

import pytest
import json
import sys
from pathlib import Path

# Add duration_system to path
sys.path.append(str(Path(__file__).parent.parent))

from duration_system.json_security import (
    SecureJsonValidator,
    SecureJsonFieldHandler,
    JsonSecurityError,
    SecurityViolationType,
    SecurityViolation,
    create_strict_validator,
    create_relaxed_validator,
    create_api_validator,
    enhance_json_handler_security
)

# Test Constants - Extracted from magic numbers/strings
TEST_MAX_DEPTH = 3
TEST_MAX_SIZE = 1000
TEST_MAX_TOTAL_SIZE = 5000
TEST_MAX_KEYS = 10
TEST_MAX_STRING_LENGTH = 100
TEST_MAX_ARRAY_LENGTH = 10
LARGE_STRING_SIZE = 200
LARGE_ARRAY_SIZE = 20
MANY_KEYS_COUNT = 15

# Dangerous patterns for testing
DANGEROUS_PROTO_KEY = "__proto__"
DANGEROUS_CONSTRUCTOR_KEY = "constructor"
XSS_SCRIPT_PAYLOAD = "<script>alert('XSS')</script>"
SQL_INJECTION_PAYLOAD = "admin' OR '1'='1"


class TestSecureJsonValidator:
    """Test suite for SecureJsonValidator."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.validator = SecureJsonValidator(
            max_depth=TEST_MAX_DEPTH,
            max_size=TEST_MAX_SIZE,
            max_total_size=TEST_MAX_TOTAL_SIZE,
            max_keys=TEST_MAX_KEYS,
            max_string_length=TEST_MAX_STRING_LENGTH,
            max_array_length=TEST_MAX_ARRAY_LENGTH,
            strict_mode=True
        )
    
    def _assert_validation_fails(self, data, expected_violation_type=None):
        """Helper method for common validation failure pattern."""
        is_valid, violations = self.validator.validate_data(data)
        assert is_valid is False
        assert len(violations) > 0
        
        if expected_violation_type:
            assert any(v.violation_type == expected_violation_type for v in violations)
        
        return violations
    
    def test_valid_json_passes(self):
        """Test that valid JSON passes validation."""
        valid_data = {
            "name": "Test User",
            "age": 30,
            "active": True,
            "tasks": ["task1", "task2", "task3"]
        }
        
        is_valid, violations = self.validator.validate_data(valid_data)
        
        assert is_valid is True
        assert len(violations) == 0
    
    # TODO: Consider extracting this block into a separate method
    # TODO: Consider extracting this block into a separate method
    def test_depth_limit_exceeded(self):
        """Test detection of excessive nesting depth."""
        deep_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "level5": "too deep"
                        }
                    }
                }
            }
        }
        
        is_valid, violations = self.validator.validate_data(deep_data)
        
        assert is_valid is False
        assert len(violations) > 0
        assert any(v.violation_type == SecurityViolationType.DEPTH_LIMIT_EXCEEDED
                  for v in violations)
    
# TODO: Consider extracting this block into a separate method
    
# TODO: Consider extracting this block into a separate method
    
    def test_size_limit_exceeded(self):
        """Test detection of oversized content."""
        # Create string that exceeds limit
        large_string = "x" * LARGE_STRING_SIZE
        data = {"large_field": large_string}
        
        self._assert_validation_fails(data, SecurityViolationType.SIZE_LIMIT_EXCEEDED)
    
    def test_dangerous_key_detection(self):
        """Test detection of dangerous keys."""
        dangerous_data = {
            DANGEROUS_PROTO_KEY: {"isAdmin": True},
            DANGEROUS_CONSTRUCTOR_KEY: "malicious",
            "normal_key": "safe value"
        }
        
        violations = self._assert_validation_fails(dangerous_data, SecurityViolationType.DANGEROUS_KEY)
        dangerous_violations = [v for v in violations
                               if v.violation_type == SecurityViolationType.DANGEROUS_KEY]
        assert len(dangerous_violations) >= 2  # __proto__ and constructor
    
    def test_script_injection_detection(self):
        """Test detection of script injection attempts."""
        script_data = {
            "comment": XSS_SCRIPT_PAYLOAD,
            "description": "Normal text",
            "onclick": "onclick='doEvil()'"
        }
        
        violations = self._assert_validation_fails(script_data, SecurityViolationType.SCRIPT_INJECTION)
        script_violations = [v for v in violations
                           if v.violation_type == SecurityViolationType.SCRIPT_INJECTION]
        assert len(script_violations) >= 1
    
    def test_sql_injection_detection(self):
        """Test detection of SQL injection patterns."""
        sql_data = {
            "username": SQL_INJECTION_PAYLOAD,
            "query": "'; DROP TABLE users; --",
            "search": "UNION SELECT * FROM passwords"
        }
        
        violations = self._assert_validation_fails(sql_data, SecurityViolationType.SQL_INJECTION)
        sql_violations = [v for v in violations
                         if v.violation_type == SecurityViolationType.SQL_INJECTION]
        assert len(sql_violations) >= 2
    
    def test_path_traversal_detection(self):
        """Test detection of path traversal attempts."""
        path_data = {
            "file": "../../../etc/passwd",
            "path": "..\\..\\windows\\system32",
            "url": "file:///etc/shadow"
        }
        
        is_valid, violations = self.validator.validate_data(path_data)
        
        assert is_valid is False
        path_violations = [v for v in violations
                          if v.violation_type == SecurityViolationType.PATH_TRAVERSAL]
        assert len(path_violations) >= 2
    
    def test_circular_reference_detection(self):
        """Test detection of circular references."""
        # Note: In Python, we can't create true circular refs in dict literals
        # But the validator should handle object identity checking
        obj = {"key": "value"}
        circular_data = {
            "obj1": obj,
            "obj2": obj  # Same object reference
        }
        
        # This should pass as it's not a true circular reference
        is_valid, violations = self.validator.validate_data(circular_data)
        assert is_valid is True
    
    def test_array_length_limit(self):
        """Test detection of oversized arrays."""
        large_array = list(range(20))  # Exceeds max_array_length of 10
        
        data = {"items": large_array}
        
        is_valid, violations = self.validator.validate_data(data)
        
        assert is_valid is False
        assert any(v.violation_type == SecurityViolationType.SIZE_LIMIT_EXCEEDED
                  for v in violations)
    
    def test_key_count_limit(self):
        """Test detection of too many keys."""
        # Create object with too many keys
        many_keys = {f"key{i}": i for i in range(15)}  # Exceeds max_keys of 10
        
        is_valid, violations = self.validator.validate_data(many_keys)
        
        assert is_valid is False
        assert any(v.violation_type == SecurityViolationType.SIZE_LIMIT_EXCEEDED
                  for v in violations)
    
    def test_null_byte_detection(self):
        """Test detection of null bytes in strings."""
        null_data = {
            "field": "text\x00with\x00nulls"
        }
        
        is_valid, violations = self.validator.validate_data(null_data)
        
        assert is_valid is False
        assert any(v.violation_type == SecurityViolationType.BINARY_DATA
                  for v in violations)
    
    def test_relaxed_mode(self):
        """Test that relaxed mode allows some dangerous patterns."""
        relaxed_validator = SecureJsonValidator(strict_mode=False)
        
        # This would fail in strict mode
        data = {
            "comment": "<script>test</script>",
            "query": "SELECT * FROM users"
        }
        
        is_valid, violations = relaxed_validator.validate_data(data)
        
        # In relaxed mode, these patterns might be allowed
        assert is_valid is True or len(violations) < 2


class TestJsonSanitization:
    """Test suite for JSON sanitization."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.validator = SecureJsonValidator()
    
    def test_dangerous_key_removal(self):
        """Test removal of dangerous keys."""
        dangerous_data = {
            "__proto__": "bad",
            "constructor": "also bad",
            "safe_key": "safe value"
        }
        
        sanitized = self.validator.sanitize_json_data(dangerous_data, remove_dangerous=True)
        
        assert "__proto__" not in sanitized
        assert "constructor" not in sanitized
        assert "safe_key" in sanitized
        assert sanitized["safe_key"] == "safe value"
    
    def test_string_sanitization(self):
        """Test HTML escaping in strings."""
        data = {
            "html": "<div>Test</div>",
            "script": "<script>alert('XSS')</script>",
            "quotes": "It's \"quoted\""
        }
        
        sanitized = self.validator.sanitize_json_data(data)
        
        assert "&lt;div&gt;" in sanitized["html"]
        assert "&lt;script&gt;" in sanitized["script"]
        assert "&#x27;" in sanitized["quotes"]
    
    def test_null_byte_removal(self):
        """Test removal of null bytes."""
        data = {
            # TODO: Consider extracting this block into a separate method
            # TODO: Consider extracting this block into a separate method
            "field": "text\x00with\x00nulls"
        }
        
        sanitized = self.validator.sanitize_json_data(data)
        
        assert "\x00" not in sanitized["field"]
        assert sanitized["field"] == "textwithnulls"
    
    def test_nested_sanitization(self):
        """Test sanitization of nested structures."""
        nested_data = {
            "user": {
                "__proto__": "bad",
                "name": "<b>John</b>",
                "tasks": [
                    "<script>evil</script>",
                    "normal task"
                ]
            }
        }
        
        sanitized = self.validator.sanitize_json_data(nested_data)
        
        assert "__proto__" not in sanitized["user"]
        assert "&lt;b&gt;" in sanitized["user"]["name"]
        assert "&lt;script&gt;" in sanitized["user"]["tasks"][0]
        assert sanitized["user"]["tasks"][1] == "normal task"
    
    def test_string_truncation(self):
        """Test that oversized strings are truncated."""
        # Create a validator with small limit
        validator = SecureJsonValidator(max_string_length=10)
        
        data = {"field": "This is a very long string that should be truncated"}
        
        sanitized = validator.sanitize_json_data(data)
        
        assert len(sanitized["field"]) == 13  # 10 chars + "..."
        assert sanitized["field"].endswith("...")


class TestSecureJsonFieldHandler:
    """Test suite for SecureJsonFieldHandler."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.handler = SecureJsonFieldHandler(strict_mode=True, max_field_size=1000)
    
    def test_secure_serialize_valid(self):
        """Test secure serialization of valid data."""
        data = {
            "name": "Test",
            "value": 123,
            "items": [1, 2, 3]
        }
        
        json_str = self.handler.secure_serialize(data)
        
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert parsed == data
    
    def test_secure_serialize_with_sanitization(self):
        """Test serialization with automatic sanitization."""
        data = {
            "__proto__": "bad",
            "safe": "value"
        }
        
        json_str = self.handler.secure_serialize(data, sanitize=True)
        
        parsed = json.loads(json_str)
        assert "__proto__" not in parsed
        assert "safe" in parsed
    
    def test_secure_serialize_rejection(self):
        """Test that dangerous data is rejected in strict mode."""
        data = {
            "__proto__": "bad"
        }
        
        with pytest.raises(JsonSecurityError) as exc_info:
            self.handler.secure_serialize(data, sanitize=False)
        
        assert len(exc_info.value.violations) > 0
    
    def test_secure_deserialize_valid(self):
        """Test secure deserialization of valid JSON."""
        json_str = '{"name": "Test", "value": 123}'
        
        data = self.handler.secure_deserialize(json_str)
        
        assert data["name"] == "Test"
        assert data["value"] == 123
    
    def test_secure_deserialize_with_validation(self):
        """Test deserialization with validation."""
        json_str = '{"__proto__": "bad", "safe": "value"}'
        
        # Should raise error in strict mode
        with pytest.raises(JsonSecurityError):
            self.handler.secure_deserialize(json_str, validate=True)
    
    def test_secure_deserialize_with_sanitization(self):
        """Test deserialization with sanitization."""
        # Create handler in non-strict mode
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        handler = SecureJsonFieldHandler(strict_mode=False)
        
        json_str = '{"__proto__": "bad", "safe": "value"}'
        
        data = handler.secure_deserialize(json_str, sanitize=True)
        
        assert "__proto__" not in data
        assert data["safe"] == "value"
    
    def test_integrity_check(self):
        """Test data integrity checking."""
        data = {"key": "value", "number": 42}
        
        # Generate hash
        hash_value = self.handler.generate_integrity_hash(data)
        
        # Check integrity - should pass
        assert self.handler.check_integrity(data, hash_value) is True
        
        # Modify data
        data["key"] = "modified"
        
        # Check integrity - should fail
        assert self.handler.check_integrity(data, hash_value) is False


class TestFactoryFunctions:
    """Test factory functions for creating validators."""
    
    def test_strict_validator(self):
        """Test strict validator creation."""
        validator = create_strict_validator()
        
        assert validator.strict_mode is True
        assert validator.allow_dangerous_keys is False
        assert validator.max_depth == 5
        assert validator.max_size == 10_000
    
    def test_relaxed_validator(self):
        """Test relaxed validator creation."""
        validator = create_relaxed_validator()
        
        assert validator.strict_mode is False
        assert validator.allow_dangerous_keys is True
        assert validator.max_depth == 20
        assert validator.max_size == 1_000_000
    
    def test_api_validator(self):
        """Test API validator creation."""
        validator = create_api_validator()
        
# TODO: Consider extracting this block into a separate method
        
# TODO: Consider extracting this block into a separate method
        
        assert validator.strict_mode is True
        assert validator.allow_dangerous_keys is False
        assert validator.max_keys == 100
        assert validator.max_array_length == 100


class TestIntegrationWithJsonHandler:
    """Test integration with existing JsonFieldHandler."""
    
    def test_enhance_json_handler(self):
        """Test enhancing existing handler with security."""
        # Create a mock JSON handler
        class MockJsonHandler:
            def __init__(self):
                self.max_field_size = 1000
                self.strict_validation = True
            
            def serialize_json(self, data, field_type=None):
                return json.dumps(data)
            
            def deserialize_json(self, json_string, field_type=None, default=None):
                if not json_string:
                    return default
                return json.loads(json_string)
        
        # Create and enhance handler
        handler = MockJsonHandler()
        enhanced = enhance_json_handler_security(handler)
        
        # Test that security methods are added
        assert hasattr(enhanced, 'validate_security')
        assert hasattr(enhanced, 'sanitize_data')
        
        # Test validation works
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        dangerous_data = {"__proto__": "bad"}
        is_valid, violations = enhanced.validate_security(dangerous_data)
        assert is_valid is False
        
        # Test sanitization works
        sanitized = enhanced.sanitize_data(dangerous_data)
        assert "__proto__" not in sanitized


class TestSecurityViolationReporting:
    """Test security violation reporting."""
    
    def test_violation_details(self):
        """Test that violations contain proper details."""
        validator = create_strict_validator()
        
        data = {
            "__proto__": "bad",
            "script": "<script>alert('XSS')</script>"
        }
        
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        is_valid, violations = validator.validate_data(data)
        
        assert is_valid is False
        assert len(violations) >= 2
        
        # Check violation structure
        for violation in violations:
            assert isinstance(violation, SecurityViolation)
            assert violation.violation_type in SecurityViolationType
            assert violation.message is not None
            assert violation.path is not None
            assert violation.severity in ["low", "medium", "high", "critical"]
    
    def test_json_security_error(self):
        """Test JsonSecurityError exception."""
        violations = [
            SecurityViolation(
                violation_type=SecurityViolationType.DANGEROUS_KEY,
                message="Test violation",
                # TODO: Consider extracting this block into a separate method
                # TODO: Consider extracting this block into a separate method
                path="$.test"
            )
        ]
        
        error = JsonSecurityError("Test error", violations)
        
        assert str(error) == "Test error"
        assert len(error.violations) == 1
        assert error.violations[0].message == "Test violation"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_json(self):
        """Test validation of empty JSON."""
        validator = create_strict_validator()
        
        # Empty object
        is_valid, violations = validator.validate_data({})
        assert is_valid is True
        
        # Empty array
        is_valid, violations = validator.validate_data([])
        assert is_valid is True
        
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        # Null
        is_valid, violations = validator.validate_data(None)
        assert is_valid is True
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters."""
        validator = create_strict_validator()
        
        # Valid Unicode
        data = {"text": "Hello 世界 🌍"}
        is_valid, violations = validator.validate_data(data)
        assert is_valid is True
        
        # Invalid Unicode handling is tested in null byte test
    
    def test_mixed_content(self):
        """Test validation of mixed safe and unsafe content."""
        validator = create_strict_validator()
        
        # TODO: Consider extracting this block into a separate method
        # TODO: Consider extracting this block into a separate method
        data = {
            "safe": "normal text",
            "number": 42,
            "dangerous": "<script>alert('XSS')</script>",
            "nested": {
                "safe": True,
                "__proto__": "bad"
            }
        }
        
        is_valid, violations = validator.validate_data(data)
        
        assert is_valid is False
        # Should have violations for both dangerous content and __proto__
        assert len(violations) >= 2
    
    def test_very_deep_nesting(self):
        """Test handling of very deep nesting."""
        validator = SecureJsonValidator(max_depth=2)
        
        # Create deeply nested structure
        data = {"a": {"b": {"c": {"d": "too deep"}}}}
        
        is_valid, violations = validator.validate_data(data)
        
        assert is_valid is False
        depth_violations = [v for v in violations
                          if v.violation_type == SecurityViolationType.DEPTH_LIMIT_EXCEEDED]
        assert len(depth_violations) > 0


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])