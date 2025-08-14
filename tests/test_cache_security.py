"""
🔐 Cache Security Regression Tests

Tests for the SEC-001 security fix: replacement of MD5 with SHA-256 in cache key generation.
Ensures the cache system is cryptographically secure and meets enterprise security standards.

Security fixes validated:
1. SHA-256 replaces MD5 for cache key generation
2. Cryptographic salt per cache instance
3. Deterministic key generation for cache consistency
4. Unique keys across different cache instances
5. Proper encoding and error handling
"""

import pytest
import hashlib
import re
import sys
import secrets
from pathlib import Path

# Add duration_system to path
sys.path.append(str(Path(__file__).parent.parent))

from duration_system.cache_fix import InterruptSafeCache


class TestCacheSecurityFixes:
    """Test suite for cache security enhancements (SEC-001)."""
    
    def setup_method(self):
        """Setup for each test method."""
        self.cache = InterruptSafeCache(enable_disk_cache=False)  # Memory only for tests
    
    def test_sha256_used_not_md5(self):
        """Verify SHA-256 is used instead of MD5 for key generation."""
        test_key = "test_security_key"
        generated_key = self.cache._generate_key(test_key)
        
        # SHA-256 produces 64-character hex strings
        assert len(generated_key) == 64, f"Expected SHA-256 64-char key, got {len(generated_key)}-char"
        
        # Verify it's hexadecimal
        assert re.match(r'^[a-f0-9]{64}$', generated_key), "Key should be 64-character lowercase hex"
        
        # Key should be different from MD5 output
        md5_key = hashlib.md5(test_key.encode()).hexdigest()
        assert generated_key != md5_key, "Generated key should not match MD5 output"
        
        # Key should be different from raw SHA-256 (due to salt)
        raw_sha256 = hashlib.sha256(test_key.encode()).hexdigest()
        assert generated_key != raw_sha256, "Generated key should include salt, not be raw SHA-256"
    
    def test_salt_uniqueness_across_instances(self):
        """Verify each cache instance has a unique salt."""
        cache1 = InterruptSafeCache(enable_disk_cache=False)
        cache2 = InterruptSafeCache(enable_disk_cache=False)
        
        test_key = "identical_input"
        
        key1 = cache1._generate_key(test_key)
        key2 = cache2._generate_key(test_key)
        
        # Same input should produce different keys due to different salts
        assert key1 != key2, "Different cache instances should produce different keys for same input"
        
        # Both should be valid SHA-256 hashes
        assert len(key1) == 64 and len(key2) == 64
        assert re.match(r'^[a-f0-9]{64}$', key1) and re.match(r'^[a-f0-9]{64}$', key2)
    
    def test_deterministic_key_generation(self):
        """Verify key generation is deterministic within the same cache instance."""
        test_key = "deterministic_test"
        
        key1 = self.cache._generate_key(test_key)
        key2 = self.cache._generate_key(test_key)
        key3 = self.cache._generate_key(test_key)
        
        # Same cache instance should always produce the same key for same input
        assert key1 == key2 == key3, "Key generation should be deterministic within same instance"
    
    def test_different_input_types(self):
        """Test secure key generation for different input types."""
        # String input
        str_key = self.cache._generate_key("test_string")
        assert len(str_key) == 64
        
        # Tuple input
        tuple_key = self.cache._generate_key(("tuple", "test", 123))
        assert len(tuple_key) == 64
        
        # Dict input
        dict_key = self.cache._generate_key({"key": "value", "number": 42})
        assert len(dict_key) == 64
        
        # List input
        list_key = self.cache._generate_key(["list", "test", 456])
        assert len(list_key) == 64
        
        # All keys should be different
        keys = [str_key, tuple_key, dict_key, list_key]
        assert len(set(keys)) == 4, "Different input types should produce different keys"
    
    def test_unicode_handling(self):
        """Test secure handling of Unicode characters."""
        unicode_inputs = [
            "Hello 世界",
            "Café français",
            "مرحبا بالعالم",
            "Здравствуй мир",
            "🚀🔐💻"
        ]
        
        keys = []
        for input_str in unicode_inputs:
            key = self.cache._generate_key(input_str)
            keys.append(key)
            
            # Verify valid SHA-256 format
            assert len(key) == 64
            assert re.match(r'^[a-f0-9]{64}$', key)
        
        # All Unicode inputs should produce different keys
        assert len(set(keys)) == len(unicode_inputs), "Unicode inputs should produce unique keys"
    
    def test_edge_cases(self):
        """Test edge cases that might cause security issues."""
        edge_cases = [
            "",  # Empty string
            " ",  # Single space
            "\n\t\r",  # Whitespace characters
            "a" * 1000,  # Very long string
            "\x00\x01\x02",  # Control characters
            "null\x00byte",  # Null bytes
            "special!@#$%^&*()chars",  # Special characters
        ]
        
        keys = []
        for case in edge_cases:
            try:
                key = self.cache._generate_key(case)
                keys.append(key)
                
                # Verify valid SHA-256 format
                assert len(key) == 64
                assert re.match(r'^[a-f0-9]{64}$', key)
                
            except Exception as e:
                pytest.fail(f"Key generation failed for edge case '{repr(case)}': {e}")
        
        # All edge cases should produce different keys
        assert len(set(keys)) == len(edge_cases), "Edge cases should produce unique keys"
    
    def test_salt_properties(self):
        """Test properties of the cryptographic salt."""
        # Salt should be 32 bytes (256 bits)
        assert len(self.cache._cache_salt) == 32, "Salt should be 32 bytes (256 bits)"
        
        # Salt should be random bytes, not all zeros
        assert self.cache._cache_salt != b'\x00' * 32, "Salt should not be all zeros"
        
        # Different cache instances should have different salts
        cache2 = InterruptSafeCache(enable_disk_cache=False)
        assert self.cache._cache_salt != cache2._cache_salt, "Each cache should have unique salt"
    
    def test_no_md5_in_output(self):
        """Verify that MD5 patterns are not present in generated keys."""
        test_inputs = [
            "test1",
            "test2",
            ("tuple", "test"),
            {"dict": "test"},
            ["list", "test"]
        ]
        
        for test_input in test_inputs:
            generated_key = self.cache._generate_key(test_input)
            
            # Generate what MD5 would produce
            if isinstance(test_input, str):
                md5_output = hashlib.md5(test_input.encode()).hexdigest()
            else:
                md5_output = hashlib.md5(str(test_input).encode()).hexdigest()
            
            # Generated key should NOT match MD5 output
            assert generated_key != md5_output, f"Generated key matches MD5 for input: {test_input}"
            
            # Generated key should be longer than MD5 (64 vs 32 chars)
            assert len(generated_key) > len(md5_output), "SHA-256 key should be longer than MD5"
    
    def test_collision_resistance(self):
        """Test collision resistance of the new key generation."""
        # Generate keys for many similar inputs
        similar_inputs = [
            f"test_input_{i}" for i in range(1000)
        ]
        
        generated_keys = set()
        for input_str in similar_inputs:
            key = self.cache._generate_key(input_str)
            
            # Check for collisions
            assert key not in generated_keys, f"Collision detected for input: {input_str}"
            generated_keys.add(key)
        
        # Should have generated 1000 unique keys
        assert len(generated_keys) == 1000, "All inputs should produce unique keys"
    
    def test_cache_functionality_with_security_fix(self):
        """Verify cache still functions correctly with security enhancements."""
        # Test basic cache operations
        self.cache.set("key1", "value1")
        assert self.cache.get("key1") == "value1"
        
        # Test with complex keys
        complex_key = {"user": "test", "action": "login", "timestamp": 1234567890}
        self.cache.set(complex_key, "complex_value")
        assert self.cache.get(complex_key) == "complex_value"
        
        # Test cache hit/miss statistics
        initial_hits = self.cache.stats["hits"]
        initial_misses = self.cache.stats["misses"]
        
        # Cache hit
        self.cache.get("key1")
        assert self.cache.stats["hits"] == initial_hits + 1
        
        # Cache miss
        self.cache.get("nonexistent_key")
        assert self.cache.stats["misses"] == initial_misses + 1
    
    def test_performance_regression(self):
        """Ensure security fix doesn't cause significant performance regression."""
        import time
        
        # Measure key generation performance
        test_keys = [f"performance_test_{i}" for i in range(100)]
        
        start_time = time.time()
        for key in test_keys:
            self.cache._generate_key(key)
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time_per_key = total_time / len(test_keys)
        
        # Key generation should be fast (< 1ms per key on average)
        assert avg_time_per_key < 0.001, f"Key generation too slow: {avg_time_per_key:.4f}s per key"
        
        print(f"Key generation performance: {avg_time_per_key*1000:.2f}ms per key")


class TestCryptographicCompliance:
    """Test cryptographic compliance with security policy."""
    
    def test_approved_algorithms_only(self):
        """Verify only approved algorithms are used."""
        cache = InterruptSafeCache(enable_disk_cache=False)
        
        # Generate a key to trigger algorithm usage
        test_key = cache._generate_key("compliance_test")
        
        # Verify SHA-256 characteristics
        assert len(test_key) == 64, "Should use SHA-256 (64-char output)"
        assert re.match(r'^[a-f0-9]{64}$', test_key), "Should produce hex output"
    
    def test_salt_entropy(self):
        """Test that salt has sufficient entropy."""
        cache = InterruptSafeCache(enable_disk_cache=False)
        salt = cache._cache_salt
        
        # Calculate byte entropy (simple check)
        unique_bytes = len(set(salt))
        entropy_ratio = unique_bytes / len(salt)
        
        # Should have good entropy (at least 50% unique bytes)
        assert entropy_ratio > 0.5, f"Salt entropy too low: {entropy_ratio:.2f}"
        
        # Should not have obvious patterns
        assert salt != salt[:16] + salt[:16], "Salt should not have repeating patterns"
    
    def test_secure_random_usage(self):
        """Verify secure random number generation."""
        # Create multiple cache instances to test salt randomness
        salts = []
        for _ in range(10):
            cache = InterruptSafeCache(enable_disk_cache=False)
            salts.append(cache._cache_salt)
        
        # All salts should be unique
        assert len(set(salts)) == 10, "All salts should be unique (cryptographically random)"
        
        # Salts should have proper length
        for salt in salts:
            assert len(salt) == 32, "All salts should be 32 bytes"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])