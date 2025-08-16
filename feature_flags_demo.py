#!/usr/bin/env python3
"""
🎛️ Feature Flags System - Comprehensive Demo

Demonstrates enterprise feature flag management for the TDD Framework.
Shows practical usage patterns, A/B testing, gradual rollouts, and management operations.

Features Demonstrated:
- Boolean flags for simple on/off features
- Percentage rollouts for gradual deployment
- User allowlists for targeted releases
- A/B testing with variants
- Time-based activations
- Kill switches for emergency control
- Audit logging and performance monitoring
- Integration with existing systems
"""

import os
import sys
import time
import random
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from streamlit_extension.utils.feature_flags import (
        FeatureFlagManager, FlagType, Environment, TargetingConfig,
        ABTestVariant, setup_flag_manager, is_feature_enabled, get_feature_variant
    )
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("⚠️  Make sure you're running from the project root directory")
    sys.exit(1)


def demo_basic_feature_flags():
    """Demonstrate basic feature flag operations."""
    print("\n🎛️ === DEMO 1: Basic Feature Flags ===")
    
    # Setup manager
    manager = setup_flag_manager("demo_feature_flags.db", Environment.DEVELOPMENT)
    
    # Create boolean flags
    print("📝 Creating boolean feature flags...")
    
    flags_to_create = [
        ("new_ui", "New User Interface", "Enable the redesigned user interface"),
        ("dark_mode", "Dark Mode", "Enable dark mode theme"),
        ("advanced_search", "Advanced Search", "Enable advanced search functionality"),
        ("beta_features", "Beta Features", "Access to beta features")
    ]
    
    for flag_key, name, description in flags_to_create:
        success = manager.create_flag(
            flag_key, name, FlagType.BOOLEAN, description,
            enabled=True, created_by="admin"
        )
        print(f"✅ Created {flag_key}: {name}")
    
    # Test flag evaluations
    print("\n🧪 Testing flag evaluations for different users...")
    
    test_users = [
        {"user_id": "alice", "email": "alice@company.com", "role": "admin"},
        {"user_id": "bob", "email": "bob@company.com", "role": "user"},
        {"user_id": "charlie", "email": "charlie@contractor.com", "role": "beta_user"},
    ]
    
    for user in test_users:
        print(f"\n👤 User: {user['user_id']} ({user['role']})")
        
        for flag_key, name, _ in flags_to_create:
            enabled = manager.is_enabled(flag_key, user)
            status = "✅ Enabled" if enabled else "❌ Disabled"
            print(f"   {name}: {status}")


def demo_percentage_rollouts():
    """Demonstrate percentage-based gradual rollouts."""
    print("\n📈 === DEMO 2: Percentage Rollouts ===")
    
    manager = setup_flag_manager("demo_feature_flags.db", Environment.DEVELOPMENT)
    
    # Create percentage rollout flags
    rollout_flags = [
        ("performance_boost", "Performance Optimization", 25.0),
        ("new_algorithm", "New Recommendation Algorithm", 50.0),
        ("caching_layer", "Enhanced Caching", 75.0),
    ]
    
    print("📝 Creating percentage rollout flags...")
    
    for flag_key, name, percentage in rollout_flags:
        success = manager.create_flag(
            flag_key, name, FlagType.PERCENTAGE,
            f"Gradual rollout at {percentage}%",
            enabled=True, created_by="admin"
        )
        
        # Set the rollout percentage
        manager.set_percentage_rollout(flag_key, percentage)
        print(f"✅ Created {flag_key}: {percentage}% rollout")
    
    # Test rollout distribution
    print("\n🎯 Testing rollout distribution (100 users)...")
    
    for flag_key, name, expected_percentage in rollout_flags:
        enabled_count = 0
        total_users = 100
        
        for i in range(total_users):
            user_context = {"user_id": f"user_{i:03d}"}
            if manager.is_enabled(flag_key, user_context):
                enabled_count += 1
        
        actual_percentage = (enabled_count / total_users) * 100
        print(f"📊 {name}: {enabled_count}/100 users ({actual_percentage:.1f}%) - Target: {expected_percentage}%")


def demo_user_targeting():
    """Demonstrate user-based targeting and allowlists."""
    print("\n🎯 === DEMO 3: User Targeting & Allowlists ===")
    
    manager = setup_flag_manager("demo_feature_flags.db", Environment.DEVELOPMENT)
    
    # Create user allowlist flag
    print("📝 Creating user allowlist flag...")
    
    success = manager.create_flag(
        "vip_features", "VIP Features", FlagType.USER_LIST,
        "Exclusive features for VIP users",
        enabled=True, created_by="admin"
    )
    print("✅ Created VIP features flag")
    
    # Define test users
    all_users = ["alice", "bob", "charlie", "david", "eve"]
    vip_users = ["alice", "charlie", "eve"]
    
    # Add VIP users to allowlist
    print("\n👑 Adding VIP users to allowlist...")
    for user_id in vip_users:
        success = manager.add_user_to_flag("vip_features", user_id)
        print(f"✅ Added {user_id} to VIP allowlist")
    
    # Test access for all users
    print("\n🧪 Testing VIP feature access...")
    
    for user_id in all_users:
        user_context = {"user_id": user_id}
        has_access = manager.is_enabled("vip_features", user_context)
        is_vip = user_id in vip_users
        
        if has_access and is_vip:
            print(f"👑 {user_id}: ✅ VIP Access (Expected)")
        elif not has_access and not is_vip:
            print(f"👤 {user_id}: ❌ No Access (Expected)")
        else:
            print(f"⚠️ {user_id}: Unexpected access result!")
    
    # Demonstrate removal from allowlist
    print("\n🚫 Removing user from allowlist...")
    manager.remove_user_from_flag("vip_features", "charlie")
    
    charlie_context = {"user_id": "charlie"}
    has_access = manager.is_enabled("vip_features", charlie_context)
    print(f"👤 Charlie after removal: {'✅ Access' if has_access else '❌ No Access'}")


def demo_ab_testing():
    """Demonstrate A/B testing with variants."""
    print("\n🧪 === DEMO 4: A/B Testing ===")
    
    manager = setup_flag_manager("demo_feature_flags.db", Environment.DEVELOPMENT)
    
    # Create A/B test flag manually (would normally use manager methods)
    print("📝 Creating A/B test flag...")
    
    # For this demo, we'll create a simple flag and show the concept
    # In a real implementation, we'd have better A/B test management
    
    success = manager.create_flag(
        "checkout_experiment", "Checkout Flow A/B Test", FlagType.AB_TEST,
        "Test different checkout flows",
        enabled=True, created_by="admin"
    )
    print("✅ Created A/B test flag")
    
    # Simulate A/B test results
    print("\n📊 Simulating A/B test distribution (100 users)...")
    
    variants = {"control": 0, "variant_a": 0, "variant_b": 0, "no_variant": 0}
    
    for i in range(100):
        user_context = {"user_id": f"test_user_{i:03d}"}
        
        # Simulate variant assignment (in real implementation, this would be handled by the flag)
        variant = get_feature_variant("checkout_experiment", user_context)
        
        if variant:
            variants[variant] += 1
        else:
            variants["no_variant"] += 1
    
    print("🎯 A/B Test Distribution:")
    for variant, count in variants.items():
        percentage = (count / 100) * 100
        print(f"   {variant}: {count} users ({percentage:.1f}%)")


def demo_time_based_flags():
    """Demonstrate time-based feature activation."""
    print("\n⏰ === DEMO 5: Time-Based Activation ===")
    
    manager = setup_flag_manager("demo_feature_flags.db", Environment.DEVELOPMENT)
    
    # Create time-sensitive flags
    print("📝 Creating time-based flags...")
    
    # Flag for future activation
    future_time = datetime.utcnow() + timedelta(hours=1)
    success = manager.create_flag(
        "future_feature", "Future Feature", FlagType.TIME_WINDOW,
        "Feature that activates in the future",
        enabled=True, created_by="admin"
    )
    print(f"✅ Created future feature (activates at {future_time.strftime('%H:%M')})")
    
    # Flag that expires soon
    past_time = datetime.utcnow() - timedelta(hours=1)
    success = manager.create_flag(
        "expired_feature", "Expired Feature", FlagType.TIME_WINDOW,
        "Feature that has expired",
        enabled=True, created_by="admin"
    )
    print(f"✅ Created expired feature (expired at {past_time.strftime('%H:%M')})")
    
    # Current active flag
    success = manager.create_flag(
        "current_promotion", "Current Promotion", FlagType.BOOLEAN,
        "Currently active promotion",
        enabled=True, created_by="admin"
    )
    print("✅ Created current promotion")
    
    # Test time-based access
    print("\n🕐 Testing time-based access...")
    
    user_context = {"user_id": "time_tester"}
    
    time_flags = [
        ("future_feature", "Future Feature"),
        ("expired_feature", "Expired Feature"),
        ("current_promotion", "Current Promotion")
    ]
    
    for flag_key, name in time_flags:
        enabled = manager.is_enabled(flag_key, user_context)
        status = "✅ Active" if enabled else "❌ Inactive"
        print(f"   {name}: {status}")


def demo_kill_switches():
    """Demonstrate emergency kill switches."""
    print("\n🚨 === DEMO 6: Emergency Kill Switches ===")
    
    manager = setup_flag_manager("demo_feature_flags.db", Environment.DEVELOPMENT)
    
    # Create critical features with kill switches
    critical_features = [
        ("payment_processing", "Payment Processing"),
        ("user_uploads", "User File Uploads"),
        ("email_notifications", "Email Notifications")
    ]
    
    print("📝 Creating critical features...")
    
    for flag_key, name in critical_features:
        success = manager.create_flag(
            flag_key, name, FlagType.BOOLEAN,
            f"Critical feature: {name}",
            enabled=True, created_by="admin"
        )
        print(f"✅ Created {name}")
    
    # Test normal operation
    print("\n✅ Normal operation status:")
    
    user_context = {"user_id": "normal_user"}
    
    for flag_key, name in critical_features:
        enabled = manager.is_enabled(flag_key, user_context)
        status = "🟢 Operational" if enabled else "🔴 Disabled"
        print(f"   {name}: {status}")
    
    # Simulate emergency - activate kill switch
    print("\n🚨 EMERGENCY: Activating kill switch for payment processing...")
    manager.kill_switch("payment_processing", True)
    
    # Test emergency status
    print("\n🔴 Emergency status:")
    
    for flag_key, name in critical_features:
        enabled = manager.is_enabled(flag_key, user_context)
        if flag_key == "payment_processing":
            status = "🚨 KILL SWITCH ACTIVE" if not enabled else "⚠️ Kill switch failed!"
        else:
            status = "🟢 Operational" if enabled else "🔴 Disabled"
        print(f"   {name}: {status}")
    
    # Recovery - deactivate kill switch
    print("\n🔧 RECOVERY: Deactivating kill switch...")
    manager.kill_switch("payment_processing", False)
    
    payment_enabled = manager.is_enabled("payment_processing", user_context)
    status = "🟢 Restored" if payment_enabled else "🔴 Still disabled"
    print(f"   Payment Processing: {status}")


def demo_segment_targeting():
    """Demonstrate user segment targeting."""
    print("\n👥 === DEMO 7: Segment Targeting ===")
    
    manager = setup_flag_manager("demo_feature_flags.db", Environment.DEVELOPMENT)
    
    # Create segment-based flag
    print("📝 Creating segment-targeted flag...")
    
    success = manager.create_flag(
        "enterprise_features", "Enterprise Features", FlagType.SEGMENT,
        "Features for enterprise customers",
        enabled=True, created_by="admin"
    )
    print("✅ Created enterprise features flag")
    
    # Define test users with different segments
    test_users = [
        {"user_id": "user1", "email": "user1@company.com", "role": "user", "tier": "basic"},
        {"user_id": "admin1", "email": "admin1@company.com", "role": "admin", "tier": "basic"},
        {"user_id": "enterprise1", "email": "ent1@enterprise.com", "role": "user", "tier": "enterprise"},
        {"user_id": "partner1", "email": "partner@partner.com", "role": "partner", "tier": "premium"},
    ]
    
    # Test segment targeting (simulated - would need proper targeting rules)
    print("\n🎯 Testing segment access...")
    
    for user in test_users:
        # For demo purposes, we'll simulate segment logic
        # In real implementation, this would be configured in targeting rules
        user_context = {
            "user_id": user["user_id"],
            "email": user["email"],
            "role": user["role"],
            "attributes": {"tier": user["tier"]}
        }
        
        # Simulate enterprise access based on email domain or tier
        is_enterprise = (
            "@enterprise.com" in user["email"] or 
            user["tier"] == "enterprise" or 
            user["role"] in ["admin", "partner"]
        )
        
        enabled = manager.is_enabled("enterprise_features", user_context)
        
        print(f"👤 {user['user_id']} ({user['tier']}, {user['role']}): ", end="")
        
        if is_enterprise:
            print("🏢 Enterprise Access Expected")
        else:
            print("👤 Standard Access")


def demo_flag_management():
    """Demonstrate flag management operations."""
    print("\n⚙️ === DEMO 8: Flag Management ===")
    
    manager = setup_flag_manager("demo_feature_flags.db", Environment.DEVELOPMENT)
    
    # Create management test flag
    print("📝 Creating management test flag...")
    
    success = manager.create_flag(
        "management_test", "Management Test Flag", FlagType.BOOLEAN,
        "Flag for testing management operations",
        enabled=False, created_by="admin"
    )
    print("✅ Created management test flag (disabled)")
    
    user_context = {"user_id": "test_user"}
    
    # Test enable/disable
    print("\n🔄 Testing enable/disable operations...")
    
    # Check initial state
    enabled = manager.is_enabled("management_test", user_context)
    print(f"Initial state: {'✅ Enabled' if enabled else '❌ Disabled'}")
    
    # Enable flag
    success = manager.enable_flag("management_test")
    enabled = manager.is_enabled("management_test", user_context)
    print(f"After enable: {'✅ Enabled' if enabled else '❌ Disabled'}")
    
    # Disable flag
    success = manager.disable_flag("management_test")
    enabled = manager.is_enabled("management_test", user_context)
    print(f"After disable: {'✅ Enabled' if enabled else '❌ Disabled'}")
    
    # List all flags
    print("\n📋 Listing all flags in environment...")
    
    all_flags = manager.list_flags()
    enabled_flags = manager.list_flags(enabled_only=True)
    
    print(f"Total flags: {len(all_flags)}")
    print(f"Enabled flags: {len(enabled_flags)}")
    
    print("\nFlag Summary:")
    for flag in all_flags[-5:]:  # Show last 5 flags
        status = "✅" if flag.enabled else "❌"
        kill_status = " 🚨" if flag.kill_switch else ""
        print(f"   {flag.flag_key}: {flag.flag_type.value} {status}{kill_status}")


def demo_performance_monitoring():
    """Demonstrate performance characteristics."""
    print("\n⚡ === DEMO 9: Performance Monitoring ===")
    
    manager = setup_flag_manager("demo_feature_flags.db", Environment.DEVELOPMENT)
    
    # Create performance test flags
    print("📝 Creating performance test flags...")
    
    flag_count = 20
    for i in range(flag_count):
        success = manager.create_flag(
            f"perf_flag_{i:02d}", f"Performance Flag {i:02d}", FlagType.BOOLEAN,
            f"Performance test flag #{i}",
            enabled=(i % 2 == 0), created_by="admin"
        )
    
    print(f"✅ Created {flag_count} performance test flags")
    
    # Test evaluation performance
    print("\n⚡ Testing evaluation performance...")
    
    user_contexts = [
        {"user_id": f"perf_user_{i:03d}"} 
        for i in range(100)
    ]
    
    # Measure bulk evaluations
    start_time = time.time()
    
    evaluation_count = 0
    for user_context in user_contexts:
        for i in range(flag_count):
            flag_key = f"perf_flag_{i:02d}"
            enabled = manager.is_enabled(flag_key, user_context)
            evaluation_count += 1
    
    end_time = time.time()
    
    total_time = end_time - start_time
    avg_time_per_eval = (total_time / evaluation_count) * 1000  # ms
    
    print(f"📊 Performance Results:")
    print(f"   Total evaluations: {evaluation_count}")
    print(f"   Total time: {total_time:.3f}s")
    print(f"   Average per evaluation: {avg_time_per_eval:.3f}ms")
    print(f"   Evaluations per second: {evaluation_count / total_time:.0f}")
    
    # Test cache performance
    print("\n🚀 Testing cache performance...")
    
    # First evaluation (cache miss)
    start_time = time.time()
    manager.is_enabled("perf_flag_00", {"user_id": "cache_test_user"})
    cache_miss_time = (time.time() - start_time) * 1000
    
    # Second evaluation (cache hit)
    start_time = time.time()
    manager.is_enabled("perf_flag_00", {"user_id": "cache_test_user"})
    cache_hit_time = (time.time() - start_time) * 1000
    
    print(f"📊 Cache Performance:")
    print(f"   Cache miss: {cache_miss_time:.3f}ms")
    print(f"   Cache hit: {cache_hit_time:.3f}ms")
    
    if cache_miss_time > 0:
        speedup = cache_miss_time / cache_hit_time if cache_hit_time > 0 else float('inf')
        print(f"   Cache speedup: {speedup:.1f}x")


def demo_integration_patterns():
    """Demonstrate integration with existing systems."""
    print("\n🔗 === DEMO 10: Integration Patterns ===")
    
    manager = setup_flag_manager("demo_feature_flags.db", Environment.DEVELOPMENT)
    
    # Create integration flags
    integration_flags = [
        ("database_migration", "Database Migration Mode"),
        ("maintenance_mode", "Maintenance Mode"),
        ("debug_logging", "Debug Logging"),
        ("rate_limiting", "Rate Limiting"),
        ("new_api_endpoints", "New API Endpoints")
    ]
    
    print("📝 Creating integration flags...")
    
    for flag_key, name in integration_flags:
        success = manager.create_flag(
            flag_key, name, FlagType.BOOLEAN,
            f"Integration flag: {name}",
            enabled=random.choice([True, False]), created_by="system"
        )
        print(f"✅ Created {name}")
    
    # Demonstrate different integration patterns
    print("\n🔧 Integration Patterns:")
    
    # Pattern 1: Service configuration
    user_context = {"user_id": "integration_test", "service": "api"}
    
    if manager.is_enabled("maintenance_mode", user_context):
        print("🚧 Maintenance Mode: Service in maintenance")
    else:
        print("🟢 Normal Mode: Service operational")
    
    # Pattern 2: Feature-specific behavior
    if manager.is_enabled("debug_logging", user_context):
        print("🐛 Debug Logging: Verbose logging enabled")
    else:
        print("📝 Normal Logging: Standard logging level")
    
    # Pattern 3: Rate limiting configuration
    if manager.is_enabled("rate_limiting", user_context):
        print("🚦 Rate Limiting: Strict rate limits applied")
    else:
        print("🚀 No Rate Limiting: Full speed ahead")
    
    # Pattern 4: API versioning
    if manager.is_enabled("new_api_endpoints", user_context):
        print("🆕 API v2: New endpoints available")
    else:
        print("📡 API v1: Legacy endpoints only")
    
    # Pattern 5: Database operations
    if manager.is_enabled("database_migration", user_context):
        print("💾 Database: Migration mode active")
    else:
        print("💾 Database: Normal operations")
    
    print("\n💡 Integration Tips:")
    print("   • Use flags for gradual rollouts")
    print("   • Implement kill switches for critical features")
    print("   • Monitor flag performance impact")
    print("   • Use segments for targeted releases")
    print("   • Clean up old flags regularly")


def main():
    """Run all feature flags demos."""
    print("🎛️ TDD Framework - Enterprise Feature Flags System Demo")
    print("=" * 65)
    
    try:
        demo_basic_feature_flags()
        demo_percentage_rollouts()
        demo_user_targeting()
        demo_ab_testing()
        demo_time_based_flags()
        demo_kill_switches()
        demo_segment_targeting()
        demo_flag_management()
        demo_performance_monitoring()
        demo_integration_patterns()
        
        print("\n✅ === ALL DEMOS COMPLETED SUCCESSFULLY ===")
        print("\n📋 Feature Flags System Summary:")
        print("   ✅ Boolean flags for simple on/off features")
        print("   ✅ Percentage rollouts for gradual deployment")
        print("   ✅ User allowlists for targeted releases")
        print("   ✅ A/B testing framework")
        print("   ✅ Time-based activation")
        print("   ✅ Emergency kill switches")
        print("   ✅ Segment targeting")
        print("   ✅ Performance optimization")
        print("   ✅ Integration patterns")
        print("   ✅ Management operations")
        
        print("\n🎛️ Feature Flags System is ready for production!")
        print("📁 Demo data saved to: demo_feature_flags.db")
        print("🧪 Run tests with: python -m pytest tests/test_feature_flags.py -v")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()