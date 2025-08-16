#!/usr/bin/env python3
"""
🔐 Secrets Vault Integration Demo

Demonstrates enterprise secrets management integration with TDD Framework.
Shows practical usage patterns for development, testing, and production scenarios.

Features Demonstrated:
- Database credential management
- API key storage and rotation
- Environment-specific secret handling
- Access control and audit logging
- Integration with existing DatabaseManager
- Streamlit configuration secrets
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from streamlit_extension.utils.secrets_vault import (
        SecretsVault, SecretType, AccessLevel, Environment, 
        EnvironmentSecrets, setup_vault, CRYPTOGRAPHY_AVAILABLE
    )
    from streamlit_extension.utils.database import DatabaseManager
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("⚠️  Make sure you're running from the project root directory")
    sys.exit(1)


def demo_basic_usage():
    """Demonstrate basic secrets vault usage."""
    print("\n🔐 === DEMO 1: Basic Secrets Management ===")
    
    if not CRYPTOGRAPHY_AVAILABLE:
        print("❌ Cryptography package not available - skipping demo")
        return
    
    # Setup vault in demo directory
    vault = setup_vault("demo_secrets_vault")
    
    # Set security context
    with vault.security_context("demo_admin", "192.168.1.100", "DemoScript/1.0"):
        print("✅ Security context established")
        
        # Store various types of secrets
        secrets = [
            ("github_api_key", "ghp_demo_token_abcdef123456", SecretType.API_KEY, Environment.DEVELOPMENT),
            ("database_password", "super_secure_db_pass_2024", SecretType.DATABASE_PASSWORD, Environment.PRODUCTION),
            ("stripe_webhook_secret", "whsec_demo_webhook_secret", SecretType.WEBHOOK_SECRET, Environment.PRODUCTION),
            ("jwt_signing_key", "jwt_demo_key_256_bits_long", SecretType.ENCRYPTION_KEY, Environment.PRODUCTION),
        ]
        
        stored_ids = []
        for name, value, secret_type, environment in secrets:
            secret_id = vault.store_secret(
                name=name,
                value=value,
                secret_type=secret_type,
                environment=environment,
                description=f"Demo {secret_type.value} for {environment.value}"
            )
            stored_ids.append((name, secret_id))
            print(f"✅ Stored {name}: {secret_id[:16]}...")
        
        # Retrieve secrets by ID and name
        print("\n🔍 Retrieving secrets:")
        for name, secret_id in stored_ids:
            # By ID
            value_by_id = vault.get_secret(secret_id=secret_id)
            print(f"✅ Retrieved {name} by ID: {value_by_id[:10]}...")
            
            # By name (need to determine environment)
            if name == "github_api_key":
                value_by_name = vault.get_secret(name=name, environment=Environment.DEVELOPMENT)
                print(f"✅ Retrieved {name} by name: {value_by_name[:10]}...")
        
        # List secrets
        dev_secrets = vault.list_secrets(environment=Environment.DEVELOPMENT)
        prod_secrets = vault.list_secrets(environment=Environment.PRODUCTION)
        
        print(f"\n📋 Development secrets: {len(dev_secrets)}")
        print(f"📋 Production secrets: {len(prod_secrets)}")
        
        # Show vault health
        health = vault.get_vault_health()
        print(f"\n🏥 Vault Health:")
        print(f"   Total active secrets: {health['total_active_secrets']}")
        print(f"   Vault size: {health['vault_size_bytes']} bytes")
        print(f"   Cryptography available: {health['cryptography_available']}")


def demo_access_control():
    """Demonstrate role-based access control."""
    print("\n🛡️ === DEMO 2: Access Control & Permissions ===")
    
    if not CRYPTOGRAPHY_AVAILABLE:
        print("❌ Cryptography package not available - skipping demo")
        return
    
    vault = setup_vault("demo_secrets_vault")
    
    # Admin creates restricted secret
    with vault.security_context("admin", "192.168.1.100"):
        secret_id = vault.store_secret(
            name="restricted_production_key",
            value="ultra_secret_production_key_2024",
            secret_type=SecretType.ENCRYPTION_KEY,
            environment=Environment.PRODUCTION,
            description="Highly restricted production encryption key",
            access_policy={
                "admin": [AccessLevel.ADMIN],
                "developer": [AccessLevel.READ],
                "ci_system": [AccessLevel.READ],
                "key_manager": [AccessLevel.READ, AccessLevel.WRITE, AccessLevel.ROTATE]
            }
        )
        print(f"✅ Admin created restricted secret: {secret_id[:16]}...")
    
    # Test different user access levels
    users_and_permissions = [
        ("admin", ["read", "write", "delete", "rotate"]),
        ("developer", ["read"]),
        ("ci_system", ["read"]),
        ("key_manager", ["read", "write", "rotate"]),
        ("unauthorized_user", [])
    ]
    
    for user, expected_permissions in users_and_permissions:
        print(f"\n👤 Testing user: {user}")
        
        with vault.security_context(user, "192.168.1.50"):
            # Test read access
            try:
                value = vault.get_secret(secret_id=secret_id)
                if value:
                    print(f"   ✅ READ: Success - {value[:10]}...")
                else:
                    print(f"   ❌ READ: Failed - secret not found")
            except PermissionError:
                print(f"   ❌ READ: Permission denied")
            except Exception as e:
                print(f"   ❌ READ: Error - {e}")
            
            # Test write access
            if "write" in expected_permissions:
                try:
                    success = vault.update_secret(secret_id, f"updated_by_{user}_{int(time.time())}")
                    print(f"   ✅ WRITE: Success" if success else "   ❌ WRITE: Failed")
                except PermissionError:
                    print(f"   ❌ WRITE: Permission denied")
                except Exception as e:
                    print(f"   ❌ WRITE: Error - {e}")
            
            # Test rotate access
            if "rotate" in expected_permissions:
                try:
                    success = vault.rotate_secret(secret_id)
                    print(f"   ✅ ROTATE: Success" if success else "   ❌ ROTATE: Failed")
                except PermissionError:
                    print(f"   ❌ ROTATE: Permission denied")
                except Exception as e:
                    print(f"   ❌ ROTATE: Error - {e}")


def demo_environment_secrets():
    """Demonstrate environment-specific secret management."""
    print("\n🌍 === DEMO 3: Environment-Specific Secrets ===")
    
    if not CRYPTOGRAPHY_AVAILABLE:
        print("❌ Cryptography package not available - skipping demo")
        return
    
    vault = setup_vault("demo_secrets_vault")
    
    # Setup environment helpers
    dev_secrets = EnvironmentSecrets(vault, Environment.DEVELOPMENT)
    staging_secrets = EnvironmentSecrets(vault, Environment.STAGING)
    prod_secrets = EnvironmentSecrets(vault, Environment.PRODUCTION)
    
    with vault.security_context("devops", "192.168.1.200"):
        print("🏗️ Setting up environment-specific configurations...")
        
        # Development environment
        dev_db_id = dev_secrets.store_database_credentials(
            host="localhost",
            port=5432,
            username="dev_user",
            password="dev_password_2024",
            database="tdd_framework_dev"
        )
        print(f"✅ Development DB configured: {dev_db_id[:16]}...")
        
        # Store dev API keys
        vault.store_secret(
            name="api_key_stripe",
            value="sk_test_dev_stripe_key_12345",
            secret_type=SecretType.API_KEY,
            environment=Environment.DEVELOPMENT,
            description="Stripe test API key for development"
        )
        
        # Staging environment
        staging_db_id = staging_secrets.store_database_credentials(
            host="staging-db.company.com",
            port=5432,
            username="staging_user",
            password="staging_secure_pass_2024",
            database="tdd_framework_staging"
        )
        print(f"✅ Staging DB configured: {staging_db_id[:16]}...")
        
        # Production environment
        prod_db_id = prod_secrets.store_database_credentials(
            host="prod-db.company.com",
            port=5432,
            username="prod_user",
            password="ultra_secure_prod_pass_2024!@#",
            database="tdd_framework_prod"
        )
        print(f"✅ Production DB configured: {prod_db_id[:16]}...")
        
        # Store production API keys
        vault.store_secret(
            name="api_key_stripe",
            value="sk_live_prod_stripe_key_67890",
            secret_type=SecretType.API_KEY,
            environment=Environment.PRODUCTION,
            description="Stripe live API key for production"
        )
        
        # Demonstrate retrieval
        print("\n🔍 Environment-specific retrieval:")
        
        dev_db_url = dev_secrets.get_database_url()
        staging_db_url = staging_secrets.get_database_url()
        prod_db_url = prod_secrets.get_database_url()
        
        print(f"🏗️ Dev DB URL: {dev_db_url[:30]}...")
        print(f"🏗️ Staging DB URL: {staging_db_url[:30]}...")
        print(f"🏗️ Prod DB URL: {prod_db_url[:30]}...")
        
        # API keys for same service, different environments
        dev_stripe = dev_secrets.get_api_key("stripe")
        prod_stripe = prod_secrets.get_api_key("stripe")
        
        print(f"🏗️ Dev Stripe Key: {dev_stripe[:20]}...")
        print(f"🏗️ Prod Stripe Key: {prod_stripe[:20]}...")


def demo_audit_and_monitoring():
    """Demonstrate audit logging and monitoring."""
    print("\n📊 === DEMO 4: Audit Logging & Monitoring ===")
    
    if not CRYPTOGRAPHY_AVAILABLE:
        print("❌ Cryptography package not available - skipping demo")
        return
    
    vault = setup_vault("demo_secrets_vault")
    
    # Perform various operations to generate audit entries
    users = ["alice", "bob", "charlie", "admin"]
    operations = [
        ("store_secret", "monitoring_test", "secret_value_123"),
        ("get_secret", None, None),
        ("update_secret", None, "updated_value_456"),
        ("get_secret", None, None),
    ]
    
    secret_id = None
    
    for user in users:
        print(f"\n👤 User {user} performing operations...")
        
        with vault.security_context(user, f"192.168.1.{hash(user) % 255}", f"Client-{user}/1.0"):
            for operation, name, value in operations:
                try:
                    if operation == "store_secret" and name:
                        secret_id = vault.store_secret(
                            name=f"{name}_{user}",
                            value=value,
                            secret_type=SecretType.API_KEY,
                            environment=Environment.DEVELOPMENT,
                            description=f"Monitoring test secret for {user}"
                        )
                        print(f"   ✅ {operation}: {secret_id[:16]}...")
                    
                    elif operation == "get_secret" and secret_id:
                        result = vault.get_secret(secret_id=secret_id)
                        print(f"   ✅ {operation}: {'Success' if result else 'Not found'}")
                    
                    elif operation == "update_secret" and secret_id and value:
                        success = vault.update_secret(secret_id, f"{value}_{user}")
                        print(f"   ✅ {operation}: {'Success' if success else 'Failed'}")
                    
                except PermissionError:
                    print(f"   ❌ {operation}: Permission denied")
                except Exception as e:
                    print(f"   ❌ {operation}: Error - {type(e).__name__}")
                
                # Small delay to make timestamps distinguishable
                time.sleep(0.1)
    
    # Display audit log
    print("\n📋 Recent Audit Log:")
    with vault.security_context("admin", "192.168.1.1"):
        audit_entries = vault.get_audit_log(limit=20)
        
        print(f"{'Timestamp':<20} {'User':<12} {'Operation':<15} {'Success':<8} {'IP Address':<15}")
        print("-" * 80)
        
        for entry in audit_entries[-10:]:  # Show last 10 entries
            timestamp = entry['timestamp'][:19]  # Remove microseconds
            user_id = entry['user_id'][:12]
            operation = entry['operation'][:15]
            success = "✅" if entry['success'] else "❌"
            ip_address = entry.get('ip_address', 'N/A') or 'N/A'
            
            print(f"{timestamp:<20} {user_id:<12} {operation:<15} {success:<8} {ip_address:<15}")


def demo_secret_rotation():
    """Demonstrate automated secret rotation."""
    print("\n🔄 === DEMO 5: Secret Rotation ===")
    
    if not CRYPTOGRAPHY_AVAILABLE:
        print("❌ Cryptography package not available - skipping demo")
        return
    
    vault = setup_vault("demo_secrets_vault")
    
    with vault.security_context("rotation_manager", "192.168.1.250"):
        # Store secret with rotation schedule
        secret_id = vault.store_secret(
            name="rotatable_api_key",
            value="original_api_key_12345",
            secret_type=SecretType.API_KEY,
            environment=Environment.PRODUCTION,
            description="API key that supports automatic rotation",
            rotation_interval_days=30,
            access_policy={
                "rotation_manager": [AccessLevel.ADMIN, AccessLevel.ROTATE]
            }
        )
        print(f"✅ Created rotatable secret: {secret_id[:16]}...")
        
        # Check original value
        original_value = vault.get_secret(secret_id=secret_id)
        print(f"🔍 Original value: {original_value}")
        
        # Perform automatic rotation
        print("\n🔄 Performing automatic rotation...")
        success = vault.rotate_secret(secret_id)
        print(f"✅ Automatic rotation: {'Success' if success else 'Failed'}")
        
        # Check new value
        rotated_value = vault.get_secret(secret_id=secret_id)
        print(f"🔍 Rotated value: {rotated_value}")
        print(f"🔍 Values different: {original_value != rotated_value}")
        
        # Custom rotation function
        def generate_custom_api_key():
            """Generate a custom API key format."""
            import secrets
            import string
            
            prefix = "ck_live_"
            key_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
            return f"{prefix}{key_part}"
        
        print("\n🔄 Performing custom rotation...")
        success = vault.rotate_secret(secret_id, generate_custom_api_key)
        print(f"✅ Custom rotation: {'Success' if success else 'Failed'}")
        
        # Check custom rotated value
        custom_value = vault.get_secret(secret_id=secret_id)
        print(f"🔍 Custom value: {custom_value}")
        print(f"🔍 Has custom prefix: {custom_value.startswith('ck_live_')}")


def demo_database_integration():
    """Demonstrate integration with existing DatabaseManager."""
    print("\n🗄️ === DEMO 6: DatabaseManager Integration ===")
    
    if not CRYPTOGRAPHY_AVAILABLE:
        print("❌ Cryptography package not available - skipping demo")
        return
    
    vault = setup_vault("demo_secrets_vault")
    
    with vault.security_context("database_admin", "192.168.1.100"):
        # Store database connection secrets
        vault.store_secret(
            name="framework_db_path",
            value="/secure/path/to/framework.db",
            secret_type=SecretType.DATABASE_PASSWORD,
            environment=Environment.PRODUCTION,
            description="Secure path to framework database"
        )
        
        vault.store_secret(
            name="timer_db_path",
            value="/secure/path/to/task_timer.db",
            secret_type=SecretType.DATABASE_PASSWORD,
            environment=Environment.PRODUCTION,
            description="Secure path to timer database"
        )
        
        # Demonstrate how DatabaseManager could use secrets
        try:
            # Note: This is conceptual - actual integration would require 
            # modifying DatabaseManager to accept secrets
            framework_db_path = vault.get_secret(name="framework_db_path", environment=Environment.PRODUCTION)
            timer_db_path = vault.get_secret(name="timer_db_path", environment=Environment.PRODUCTION)
            
            print(f"✅ Framework DB path from vault: {framework_db_path}")
            print(f"✅ Timer DB path from vault: {timer_db_path}")
            
            # Show how this would integrate with DatabaseManager
            print("\n💡 Integration example:")
            print("    # In DatabaseManager.__init__():")
            print("    vault = get_vault()")
            print("    with vault.security_context(user_id, request_ip):")
            print("        self.framework_db_path = vault.get_secret('framework_db_path', env)")
            print("        self.timer_db_path = vault.get_secret('timer_db_path', env)")
            
        except Exception as e:
            print(f"❌ Error demonstrating integration: {e}")


def demo_performance_and_caching():
    """Demonstrate performance characteristics."""
    print("\n⚡ === DEMO 7: Performance & Caching ===")
    
    if not CRYPTOGRAPHY_AVAILABLE:
        print("❌ Cryptography package not available - skipping demo")
        return
    
    vault = setup_vault("demo_secrets_vault")
    
    with vault.security_context("performance_tester", "192.168.1.100"):
        # Store test secrets
        secret_ids = []
        
        print("🏗️ Creating test secrets...")
        start_time = time.time()
        
        for i in range(10):
            secret_id = vault.store_secret(
                name=f"perf_test_secret_{i}",
                value=f"performance_test_value_{i}_{'x' * 100}",  # Longer value
                secret_type=SecretType.API_KEY,
                environment=Environment.DEVELOPMENT,
                description=f"Performance test secret #{i}"
            )
            secret_ids.append(secret_id)
        
        store_time = time.time() - start_time
        print(f"✅ Stored 10 secrets in {store_time:.3f}s ({store_time/10:.3f}s per secret)")
        
        # Test retrieval performance
        print("\n🔍 Testing retrieval performance...")
        start_time = time.time()
        
        for secret_id in secret_ids:
            value = vault.get_secret(secret_id=secret_id)
            assert value is not None
        
        retrieve_time = time.time() - start_time
        print(f"✅ Retrieved 10 secrets in {retrieve_time:.3f}s ({retrieve_time/10:.3f}s per secret)")
        
        # Test list performance
        print("\n📋 Testing list performance...")
        start_time = time.time()
        
        secrets_list = vault.list_secrets(environment=Environment.DEVELOPMENT)
        
        list_time = time.time() - start_time
        print(f"✅ Listed {len(secrets_list)} secrets in {list_time:.3f}s")
        
        # Performance summary
        print(f"\n📊 Performance Summary:")
        print(f"   Storage: {1000 * store_time/10:.1f}ms per secret")
        print(f"   Retrieval: {1000 * retrieve_time/10:.1f}ms per secret")
        print(f"   List operation: {1000 * list_time:.1f}ms for {len(secrets_list)} secrets")


def main():
    """Run all demos."""
    print("🔐 TDD Framework - Enterprise Secrets Vault Demo")
    print("=" * 60)
    
    if not CRYPTOGRAPHY_AVAILABLE:
        print("❌ CRITICAL: cryptography package not available")
        print("📦 Install with: pip install cryptography")
        print("⚠️  Secrets vault requires cryptography for encryption")
        return
    
    try:
        demo_basic_usage()
        demo_access_control()
        demo_environment_secrets()
        demo_audit_and_monitoring()
        demo_secret_rotation()
        demo_database_integration()
        demo_performance_and_caching()
        
        print("\n✅ === ALL DEMOS COMPLETED SUCCESSFULLY ===")
        print("\n📋 Summary:")
        print("   ✅ Basic secrets management")
        print("   ✅ Role-based access control")
        print("   ✅ Environment-specific configurations")
        print("   ✅ Comprehensive audit logging")
        print("   ✅ Automatic and custom secret rotation")
        print("   ✅ DatabaseManager integration patterns")
        print("   ✅ Performance benchmarking")
        
        print("\n🔐 Secrets Vault is ready for production use!")
        print("📁 Demo vault created at: demo_secrets_vault/")
        print("🧪 Run tests with: python -m pytest tests/test_secrets_vault.py -v")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()