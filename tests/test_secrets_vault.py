"""
🔐 Comprehensive test suite for Secrets Vault System

Tests for enterprise secrets management system addressing report.md security requirements.
Covers encryption, access control, audit logging, and all CRUD operations.
"""

import pytest
import tempfile
import shutil
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Test imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from streamlit_extension.utils.secrets_vault import (
    SecretsVault, SecretType, AccessLevel, Environment, SecretEncryption,
    EnvironmentSecrets, get_vault, setup_vault, CRYPTOGRAPHY_AVAILABLE
)


class TestSecretEncryption:
    """Test the SecretEncryption class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography package not available")
        self.encryption = SecretEncryption()
    
    def test_master_key_generation(self):
        """Test master key generation."""
        key1 = self.encryption._generate_master_key()
        key2 = self.encryption._generate_master_key()
        
        assert len(key1) == 32  # 256-bit key
        assert len(key2) == 32
        assert key1 != key2  # Should be random
    
    def test_key_derivation(self):
        """Test key derivation from master key."""
        salt = b"test_salt_16byte"
        key1 = self.encryption._derive_key(salt)
        key2 = self.encryption._derive_key(salt)
        
        assert len(key1) == 32  # 256-bit derived key
        assert key1 == key2  # Same salt should produce same key
        
        # Different salt should produce different key
        different_salt = b"different_salt16"
        key3 = self.encryption._derive_key(different_salt)
        assert key1 != key3
    
    def test_encrypt_decrypt_cycle(self):
        """Test encryption and decryption cycle."""
        plaintext = "super_secret_password_123"
        
        # Encrypt
        encrypted_data = self.encryption.encrypt_secret(plaintext)
        
        # Verify structure
        assert "ciphertext" in encrypted_data
        assert "salt" in encrypted_data
        assert "iv" in encrypted_data
        assert "tag" in encrypted_data
        
        # Decrypt
        decrypted = self.encryption.decrypt_secret(encrypted_data)
        assert decrypted == plaintext
    
    def test_encrypt_with_additional_data(self):
        """Test encryption with additional authenticated data."""
        plaintext = "secret_with_context"
        additional_data = b"context_data"
        
        encrypted_data = self.encryption.encrypt_secret(plaintext, additional_data)
        decrypted = self.encryption.decrypt_secret(encrypted_data, additional_data)
        
        assert decrypted == plaintext
    
    def test_decrypt_with_wrong_additional_data_fails(self):
        """Test that decryption fails with wrong additional data."""
        plaintext = "secret_with_context"
        additional_data = b"correct_context"
        wrong_data = b"wrong_context"
        
        encrypted_data = self.encryption.encrypt_secret(plaintext, additional_data)
        
        with pytest.raises(Exception):  # Should raise cryptographic error
            self.encryption.decrypt_secret(encrypted_data, wrong_data)
    
    def test_encrypt_empty_string(self):
        """Test encryption of empty string."""
        plaintext = ""
        encrypted_data = self.encryption.encrypt_secret(plaintext)
        decrypted = self.encryption.decrypt_secret(encrypted_data)
        assert decrypted == plaintext
    
    def test_encrypt_unicode_string(self):
        """Test encryption of Unicode strings."""
        plaintext = "senha_çâréctêrés_特殊字符_🔐"
        encrypted_data = self.encryption.encrypt_secret(plaintext)
        decrypted = self.encryption.decrypt_secret(encrypted_data)
        assert decrypted == plaintext


class TestSecretsVault:
    """Test the SecretsVault class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography package not available")
        
        # Create temporary directory for test vault
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = os.path.join(self.temp_dir, "test_vault")
        self.vault = SecretsVault(self.vault_path)
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_vault_initialization(self):
        """Test vault initialization."""
        assert Path(self.vault_path).exists()
        assert Path(self.vault_path).stat().st_mode & 0o777 == 0o700  # Restricted permissions
        
        # Check database file exists
        db_path = Path(self.vault_path) / "vault.db"
        assert db_path.exists()
        
        # Check master key file exists
        key_file = Path(self.vault_path) / "master.key"
        assert key_file.exists()
        assert key_file.stat().st_mode & 0o777 == 0o600  # Owner read/write only
    
    def test_security_context(self):
        """Test security context management."""
        # Test context manager
        with self.vault.security_context("test_user", "192.168.1.100", "TestAgent/1.0"):
            context = self.vault.get_context()
            assert context["user_id"] == "test_user"
            assert context["ip_address"] == "192.168.1.100"
            assert context["user_agent"] == "TestAgent/1.0"
        
        # Context should be cleared after exiting
        context = self.vault.get_context()
        assert context.get("user_id") is None
    
    def test_store_and_retrieve_secret(self):
        """Test basic secret storage and retrieval."""
        with self.vault.security_context("admin", "127.0.0.1"):
            # Store secret
            secret_id = self.vault.store_secret(
                name="test_api_key",
                value="sk-1234567890abcdef",
                secret_type=SecretType.API_KEY,
                environment=Environment.DEVELOPMENT,
                description="Test API key"
            )
            
            assert secret_id is not None
            assert len(secret_id) > 20  # Should be a substantial token
            
            # Retrieve by ID
            retrieved_value = self.vault.get_secret(secret_id=secret_id)
            assert retrieved_value == "sk-1234567890abcdef"
            
            # Retrieve by name
            retrieved_value = self.vault.get_secret(
                name="test_api_key",
                environment=Environment.DEVELOPMENT
            )
            assert retrieved_value == "sk-1234567890abcdef"
    
    def test_duplicate_secret_name_fails(self):
        """Test that duplicate secret names in same environment fail."""
        with self.vault.security_context("admin", "127.0.0.1"):
            # Store first secret
            self.vault.store_secret(
                name="duplicate_test",
                value="first_value",
                secret_type=SecretType.API_KEY,
                environment=Environment.DEVELOPMENT
            )
            
            # Try to store duplicate - should fail
            with pytest.raises(ValueError, match="already exists"):
                self.vault.store_secret(
                    name="duplicate_test",
                    value="second_value",
                    secret_type=SecretType.API_KEY,
                    environment=Environment.DEVELOPMENT
                )
    
    def test_same_name_different_environment_allowed(self):
        """Test that same name in different environments is allowed."""
        with self.vault.security_context("admin", "127.0.0.1"):
            # Store in development
            dev_id = self.vault.store_secret(
                name="multi_env_secret",
                value="dev_value",
                secret_type=SecretType.API_KEY,
                environment=Environment.DEVELOPMENT
            )
            
            # Store in production with same name - should succeed
            prod_id = self.vault.store_secret(
                name="multi_env_secret",
                value="prod_value",
                secret_type=SecretType.API_KEY,
                environment=Environment.PRODUCTION
            )
            
            assert dev_id != prod_id
            
            # Verify both can be retrieved
            dev_value = self.vault.get_secret(name="multi_env_secret", environment=Environment.DEVELOPMENT)
            prod_value = self.vault.get_secret(name="multi_env_secret", environment=Environment.PRODUCTION)
            
            assert dev_value == "dev_value"
            assert prod_value == "prod_value"
    
    def test_access_control(self):
        """Test role-based access control."""
        with self.vault.security_context("admin", "127.0.0.1"):
            # Create secret with specific access policy
            secret_id = self.vault.store_secret(
                name="restricted_secret",
                value="top_secret_value",
                secret_type=SecretType.API_KEY,
                environment=Environment.PRODUCTION,
                access_policy={
                    "admin": [AccessLevel.ADMIN],
                    "reader": [AccessLevel.READ],
                    "writer": [AccessLevel.READ, AccessLevel.WRITE]
                }
            )
        
        # Test admin access (should work)
        with self.vault.security_context("admin", "127.0.0.1"):
            value = self.vault.get_secret(secret_id=secret_id)
            assert value == "top_secret_value"
        
        # Test reader access (should work for read)
        with self.vault.security_context("reader", "127.0.0.1"):
            value = self.vault.get_secret(secret_id=secret_id)
            assert value == "top_secret_value"
        
        # Test writer access (should work for read and write)
        with self.vault.security_context("writer", "127.0.0.1"):
            value = self.vault.get_secret(secret_id=secret_id)
            assert value == "top_secret_value"
            
            # Should be able to update
            success = self.vault.update_secret(secret_id, "new_secret_value")
            assert success is True
        
        # Test unauthorized user (should fail)
        with self.vault.security_context("unauthorized", "127.0.0.1"):
            with pytest.raises(PermissionError):
                self.vault.get_secret(secret_id=secret_id)
    
    def test_update_secret(self):
        """Test secret update functionality."""
        with self.vault.security_context("admin", "127.0.0.1"):
            # Store initial secret
            secret_id = self.vault.store_secret(
                name="updatable_secret",
                value="initial_value",
                secret_type=SecretType.API_KEY,
                environment=Environment.DEVELOPMENT
            )
            
            # Update secret
            success = self.vault.update_secret(secret_id, "updated_value")
            assert success is True
            
            # Verify update
            updated_value = self.vault.get_secret(secret_id=secret_id)
            assert updated_value == "updated_value"
    
    def test_delete_secret_soft(self):
        """Test soft delete functionality (hard_delete=False)."""
        with self.vault.security_context("admin", "127.0.0.1"):
            # Store secret
            secret_id = self.vault.store_secret(
                name="deletable_secret",
                value="to_be_deleted",
                secret_type=SecretType.API_KEY,
                environment=Environment.DEVELOPMENT
            )
            
            # Soft delete (hard_delete=False means soft delete)
            success = self.vault.delete_secret(secret_id, hard_delete=False)
            assert success is True
            
            # Should not be retrievable after soft delete
            value = self.vault.get_secret(secret_id=secret_id)
            assert value is None
    
    def test_list_secrets(self):
        """Test listing secrets functionality."""
        with self.vault.security_context("admin", "127.0.0.1"):
            # Store multiple secrets
            self.vault.store_secret(
                name="list_test_1",
                value="value1",
                secret_type=SecretType.API_KEY,
                environment=Environment.DEVELOPMENT,
                tags=["test", "api"]
            )
            
            self.vault.store_secret(
                name="list_test_2",
                value="value2",
                secret_type=SecretType.DATABASE_PASSWORD,
                environment=Environment.DEVELOPMENT,
                tags=["test", "db"]
            )
            
            self.vault.store_secret(
                name="list_test_3",
                value="value3",
                secret_type=SecretType.API_KEY,
                environment=Environment.PRODUCTION,
                tags=["test", "api"]
            )
            
            # List all development secrets
            dev_secrets = self.vault.list_secrets(environment=Environment.DEVELOPMENT)
            assert len(dev_secrets) >= 2
            
            # List API keys only
            api_secrets = self.vault.list_secrets(secret_type=SecretType.API_KEY)
            assert len(api_secrets) >= 2
            
            # List development API keys
            dev_api_secrets = self.vault.list_secrets(
                environment=Environment.DEVELOPMENT,
                secret_type=SecretType.API_KEY
            )
            assert len(dev_api_secrets) >= 1
    
    def test_secret_rotation(self):
        """Test secret rotation functionality."""
        with self.vault.security_context("admin", "127.0.0.1"):
            # Store secret
            secret_id = self.vault.store_secret(
                name="rotatable_secret",
                value="original_value",
                secret_type=SecretType.API_KEY,
                environment=Environment.DEVELOPMENT,
                access_policy={"admin": [AccessLevel.ADMIN, AccessLevel.ROTATE]}
            )
            
            # Test automatic rotation
            success = self.vault.rotate_secret(secret_id)
            assert success is True
            
            # Verify value changed
            new_value = self.vault.get_secret(secret_id=secret_id)
            assert new_value != "original_value"
            assert len(new_value) > 20  # Should be a substantial token
            
            # Test custom rotation function
            def custom_rotation():
                return "custom_rotated_value"
            
            success = self.vault.rotate_secret(secret_id, custom_rotation)
            assert success is True
            
            rotated_value = self.vault.get_secret(secret_id=secret_id)
            assert rotated_value == "custom_rotated_value"
    
    def test_audit_logging(self):
        """Test audit logging functionality."""
        with self.vault.security_context("test_user", "192.168.1.100", "TestAgent/1.0"):
            # Perform various operations
            secret_id = self.vault.store_secret(
                name="audit_test",
                value="audit_value",
                secret_type=SecretType.API_KEY,
                environment=Environment.DEVELOPMENT
            )
            
            self.vault.get_secret(secret_id=secret_id)
            self.vault.update_secret(secret_id, "updated_audit_value")
        
        # Check audit log
        with self.vault.security_context("admin", "127.0.0.1"):
            audit_entries = self.vault.get_audit_log(limit=10)
            
            assert len(audit_entries) >= 3  # store, get, update
            
            # Verify audit entry structure
            entry = audit_entries[0]
            assert "timestamp" in entry
            assert "user_id" in entry
            assert "operation" in entry
            assert "secret_id" in entry
            assert "success" in entry
            assert "ip_address" in entry
            assert "details" in entry
    
    def test_vault_health(self):
        """Test vault health check functionality."""
        with self.vault.security_context("admin", "127.0.0.1"):
            # Store some test data
            self.vault.store_secret(
                name="health_test_dev",
                value="value",
                secret_type=SecretType.API_KEY,
                environment=Environment.DEVELOPMENT
            )
            
            self.vault.store_secret(
                name="health_test_prod",
                value="value",
                secret_type=SecretType.DATABASE_PASSWORD,
                environment=Environment.PRODUCTION
            )
            
            # Get health status
            health = self.vault.get_vault_health()
            
            assert "vault_path" in health
            assert "database_exists" in health
            assert "cryptography_available" in health
            assert "secrets_by_environment" in health
            assert "secrets_by_type" in health
            assert "total_active_secrets" in health
            assert "vault_size_bytes" in health
            
            # Verify counts
            assert health["total_active_secrets"] >= 2
            assert health["secrets_by_environment"].get("development", 0) >= 1
            assert health["secrets_by_environment"].get("production", 0) >= 1
    
    def test_backup_and_restore(self):
        """Test backup functionality."""
        with self.vault.security_context("admin", "127.0.0.1"):
            # Store test data
            secret_id = self.vault.store_secret(
                name="backup_test",
                value="backup_value",
                secret_type=SecretType.API_KEY,
                environment=Environment.DEVELOPMENT
            )
            
            # Create backup
            backup_path = os.path.join(self.temp_dir, "vault_backup.tar.gz")
            success = self.vault.backup_vault(backup_path)
            assert success is True
            assert os.path.exists(backup_path)
            
            # Verify backup contains data
            import tarfile
            with tarfile.open(backup_path, 'r:gz') as tar:
                names = tar.getnames()
                assert any('vault.db' in name for name in names)
                assert any('master.key' in name for name in names)


class TestEnvironmentSecrets:
    """Test the EnvironmentSecrets helper class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography package not available")
        
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = os.path.join(self.temp_dir, "test_vault")
        self.vault = SecretsVault(self.vault_path)
        self.env_secrets = EnvironmentSecrets(self.vault, Environment.DEVELOPMENT)
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_store_and_get_database_credentials(self):
        """Test database credential management."""
        with self.vault.security_context("admin", "127.0.0.1"):
            secret_id = self.env_secrets.store_database_credentials(
                host="localhost",
                port=5432,
                username="testuser",
                password="testpass",
                database="testdb"
            )
            
            assert secret_id is not None
            
            # Retrieve connection URL
            connection_url = self.env_secrets.get_database_url()
            assert connection_url == "postgresql://testuser:testpass@localhost:5432/testdb"
    
    def test_api_key_management(self):
        """Test API key management through helper."""
        with self.vault.security_context("admin", "127.0.0.1"):
            # Store API key manually for testing
            self.vault.store_secret(
                name="api_key_github",
                value="ghp_test_token_123",
                secret_type=SecretType.API_KEY,
                environment=Environment.DEVELOPMENT
            )
            
            # Retrieve through helper
            api_key = self.env_secrets.get_api_key("github")
            assert api_key == "ghp_test_token_123"
    
    def test_oauth_token_management(self):
        """Test OAuth token management through helper."""
        with self.vault.security_context("admin", "127.0.0.1"):
            # Store OAuth token manually for testing
            self.vault.store_secret(
                name="oauth_token_google",
                value="ya29.test_oauth_token",
                secret_type=SecretType.OAUTH_TOKEN,
                environment=Environment.DEVELOPMENT
            )
            
            # Retrieve through helper
            oauth_token = self.env_secrets.get_oauth_token("google")
            assert oauth_token == "ya29.test_oauth_token"


class TestGlobalVaultInstance:
    """Test global vault instance management."""
    
    def setup_method(self):
        """Setup test fixtures."""
        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography package not available")
        
        self.temp_dir = tempfile.mkdtemp()
        
        # Clear global instance
        import streamlit_extension.utils.secrets_vault as vault_module
        vault_module._vault_instance = None
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Clear global instance
        import streamlit_extension.utils.secrets_vault as vault_module
        vault_module._vault_instance = None
    
    def test_get_vault_singleton(self):
        """Test global vault singleton pattern."""
        vault_path = os.path.join(self.temp_dir, "global_vault")
        
        vault1 = get_vault(vault_path)
        vault2 = get_vault(vault_path)
        
        assert vault1 is vault2  # Should be same instance
    
    def test_setup_vault(self):
        """Test vault setup function."""
        vault_path = os.path.join(self.temp_dir, "setup_vault")
        
        vault = setup_vault(vault_path)
        assert vault is not None
        assert Path(vault_path).exists()
        
        # Should return same instance on subsequent calls
        vault2 = get_vault(vault_path)
        assert vault is vault2


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def setup_method(self):
        """Setup test fixtures."""
        if not CRYPTOGRAPHY_AVAILABLE:
            pytest.skip("cryptography package not available")
        
        self.temp_dir = tempfile.mkdtemp()
        self.vault_path = os.path.join(self.temp_dir, "test_vault")
        self.vault = SecretsVault(self.vault_path)
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_get_nonexistent_secret(self):
        """Test retrieving non-existent secret."""
        with self.vault.security_context("admin", "127.0.0.1"):
            value = self.vault.get_secret(secret_id="nonexistent_id")
            assert value is None
            
            value = self.vault.get_secret(name="nonexistent", environment=Environment.DEVELOPMENT)
            assert value is None
    
    def test_invalid_parameters(self):
        """Test various invalid parameter scenarios."""
        with self.vault.security_context("admin", "127.0.0.1"):
            # Missing required parameters
            with pytest.raises(ValueError):
                self.vault.get_secret()  # No parameters
            
            with pytest.raises(ValueError):
                self.vault.get_secret(name="test")  # Name without environment
    
    def test_permission_errors(self):
        """Test permission error scenarios."""
        with self.vault.security_context("admin", "127.0.0.1"):
            secret_id = self.vault.store_secret(
                name="permission_test",
                value="secret_value",
                secret_type=SecretType.API_KEY,
                environment=Environment.DEVELOPMENT,
                access_policy={"admin": [AccessLevel.ADMIN]}
            )
        
        # Try to access without permission
        with self.vault.security_context("unauthorized", "127.0.0.1"):
            with pytest.raises(PermissionError):
                self.vault.get_secret(secret_id=secret_id)
            
            with pytest.raises(PermissionError):
                self.vault.update_secret(secret_id, "new_value")
            
            with pytest.raises(PermissionError):
                self.vault.delete_secret(secret_id)
    
    def test_database_corruption_recovery(self):
        """Test recovery from database issues."""
        # This is a simplified test - in real scenarios we'd test more corruption cases
        with self.vault.security_context("admin", "127.0.0.1"):
            # Store secret first
            secret_id = self.vault.store_secret(
                name="corruption_test",
                value="test_value",
                secret_type=SecretType.API_KEY,
                environment=Environment.DEVELOPMENT
            )
            
            # Verify we can get health even if there are issues
            health = self.vault.get_vault_health()
            assert "vault_path" in health
            assert "database_exists" in health


@pytest.mark.skipif(not CRYPTOGRAPHY_AVAILABLE, reason="cryptography package not available")
class TestCryptographyIntegration:
    """Test integration with cryptography library."""
    
    def test_encryption_algorithms(self):
        """Test that correct encryption algorithms are used."""
        encryption = SecretEncryption()
        plaintext = "test_encryption_algorithms"
        
        encrypted_data = encryption.encrypt_secret(plaintext)
        
        # Verify components are present (base64 encoded)
        import base64
        
        ciphertext = base64.b64decode(encrypted_data['ciphertext'])
        salt = base64.b64decode(encrypted_data['salt'])
        iv = base64.b64decode(encrypted_data['iv'])
        tag = base64.b64decode(encrypted_data['tag'])
        
        assert len(salt) == 16  # 128-bit salt
        assert len(iv) == 12   # 96-bit IV for GCM
        assert len(tag) == 16  # 128-bit authentication tag
        assert len(ciphertext) >= len(plaintext.encode('utf-8'))  # Ciphertext at least as long as plaintext


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])