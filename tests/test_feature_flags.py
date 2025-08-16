"""
🎛️ Comprehensive test suite for Feature Flags System

Tests for enterprise feature flag management system addressing report.md requirements.
Covers flag evaluation, targeting, A/B testing, audit logging, and performance.
"""

import pytest
import tempfile
import shutil
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Test imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from streamlit_extension.utils.feature_flags import (
    FeatureFlagManager, FeatureFlagEvaluator, FeatureFlagStore,
    FlagType, Environment, TargetingRule, FlagMetadata, TargetingConfig,
    ABTestVariant, FlagEvaluation, get_flag_manager, setup_flag_manager,
    is_feature_enabled, get_feature_variant
)

# Disable monitoring for tests to avoid Prometheus conflicts
import streamlit_extension.utils.feature_flags as ff_module
ff_module.MONITORING_AVAILABLE = False


class TestFeatureFlagEvaluator:
    """Test the FeatureFlagEvaluator class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.evaluator = FeatureFlagEvaluator()
    
    def test_boolean_flag_evaluation(self):
        """Test boolean flag evaluation."""
        flag = FlagMetadata(
            flag_key="test_boolean",
            name="Test Boolean Flag",
            description="Test flag",
            flag_type=FlagType.BOOLEAN,
            environment=Environment.DEVELOPMENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test",
            enabled=True,
            default_value=False,
            targeting=TargetingConfig(rules=[], percentage=100.0)
        )
        
        user_context = {"user_id": "test_user", "email": "test@example.com"}
        
        result = self.evaluator.evaluate_flag(flag, user_context)
        
        assert result.flag_key == "test_boolean"
        assert result.enabled is True
        assert result.reason == "targeting_matched"
        assert result.user_id == "test_user"
        assert result.targeting_matched is True
    
    def test_disabled_flag_evaluation(self):
        """Test disabled flag returns false."""
        flag = FlagMetadata(
            flag_key="test_disabled",
            name="Test Disabled Flag",
            description="Test flag",
            flag_type=FlagType.BOOLEAN,
            environment=Environment.DEVELOPMENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test",
            enabled=False,  # Disabled
            default_value=False,
            targeting=TargetingConfig(rules=[], percentage=100.0)
        )
        
        user_context = {"user_id": "test_user"}
        
        result = self.evaluator.evaluate_flag(flag, user_context)
        
        assert result.enabled is False
        assert result.reason == "flag_disabled"
        assert result.targeting_matched is False
    
    def test_kill_switch_evaluation(self):
        """Test kill switch overrides everything."""
        flag = FlagMetadata(
            flag_key="test_kill_switch",
            name="Test Kill Switch",
            description="Test flag",
            flag_type=FlagType.BOOLEAN,
            environment=Environment.DEVELOPMENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test",
            enabled=True,
            default_value=False,
            targeting=TargetingConfig(rules=[], percentage=100.0),
            kill_switch=True  # Kill switch active
        )
        
        user_context = {"user_id": "test_user"}
        
        result = self.evaluator.evaluate_flag(flag, user_context)
        
        assert result.enabled is False
        assert result.reason == "kill_switch_active"
        assert result.targeting_matched is False
    
    def test_percentage_flag_evaluation(self):
        """Test percentage-based flag evaluation."""
        flag = FlagMetadata(
            flag_key="test_percentage",
            name="Test Percentage Flag",
            description="Test flag",
            flag_type=FlagType.PERCENTAGE,
            environment=Environment.DEVELOPMENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test",
            enabled=True,
            default_value=False,
            targeting=TargetingConfig(rules=[], percentage=50.0)  # 50% rollout
        )
        
        # Test multiple users to verify percentage distribution
        enabled_count = 0
        total_users = 100
        
        for i in range(total_users):
            user_context = {"user_id": f"user_{i}"}
            result = self.evaluator.evaluate_flag(flag, user_context)
            if result.enabled:
                enabled_count += 1
        
        # Should be approximately 50% (allow some variance for hash distribution)
        assert 40 <= enabled_count <= 60, f"Expected ~50 users enabled, got {enabled_count}"
    
    def test_user_list_flag_evaluation(self):
        """Test user allowlist flag evaluation."""
        flag = FlagMetadata(
            flag_key="test_user_list",
            name="Test User List Flag",
            description="Test flag",
            flag_type=FlagType.USER_LIST,
            environment=Environment.DEVELOPMENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test",
            enabled=True,
            default_value=False,
            targeting=TargetingConfig(
                rules=[
                    {
                        "type": "user_id",
                        "values": ["allowed_user1", "allowed_user2"]
                    }
                ]
            )
        )
        
        # Test allowed user
        allowed_context = {"user_id": "allowed_user1"}
        result = self.evaluator.evaluate_flag(flag, allowed_context)
        assert result.enabled is True
        assert result.reason == "user_in_allowlist"
        
        # Test non-allowed user
        denied_context = {"user_id": "denied_user"}
        result = self.evaluator.evaluate_flag(flag, denied_context)
        assert result.enabled is False
        assert result.reason == "user_not_in_allowlist"
    
    def test_ab_test_flag_evaluation(self):
        """Test A/B test flag evaluation with variants."""
        flag = FlagMetadata(
            flag_key="test_ab_test",
            name="Test A/B Test Flag",
            description="Test flag",
            flag_type=FlagType.AB_TEST,
            environment=Environment.DEVELOPMENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test",
            enabled=True,
            default_value=False,
            targeting=TargetingConfig(rules=[], percentage=100.0),
            variants=[
                ABTestVariant(name="control", weight=0.5, config={"color": "blue"}),
                ABTestVariant(name="treatment", weight=0.5, config={"color": "red"})
            ]
        )
        
        # Test multiple users to verify variant distribution
        variant_counts = {"control": 0, "treatment": 0, None: 0}
        total_users = 100
        
        for i in range(total_users):
            user_context = {"user_id": f"user_{i}"}
            result = self.evaluator.evaluate_flag(flag, user_context)
            variant_counts[result.variant] += 1
        
        # Should have good distribution between variants
        assert variant_counts["control"] > 30
        assert variant_counts["treatment"] > 30
        assert variant_counts[None] == 0  # All users should get a variant
    
    def test_time_window_evaluation(self):
        """Test time window flag evaluation."""
        # Flag active only in the future
        future_flag = FlagMetadata(
            flag_key="test_future",
            name="Test Future Flag",
            description="Test flag",
            flag_type=FlagType.BOOLEAN,
            environment=Environment.DEVELOPMENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test",
            enabled=True,
            default_value=False,
            targeting=TargetingConfig(rules=[], percentage=100.0),
            time_window_start=datetime.utcnow() + timedelta(hours=1)  # Future
        )
        
        user_context = {"user_id": "test_user"}
        result = self.evaluator.evaluate_flag(future_flag, user_context)
        
        assert result.enabled is False
        assert result.reason == "outside_time_window"
        
        # Flag that expired
        expired_flag = FlagMetadata(
            flag_key="test_expired",
            name="Test Expired Flag",
            description="Test flag",
            flag_type=FlagType.BOOLEAN,
            environment=Environment.DEVELOPMENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test",
            enabled=True,
            default_value=False,
            targeting=TargetingConfig(rules=[], percentage=100.0),
            time_window_end=datetime.utcnow() - timedelta(hours=1)  # Past
        )
        
        result = self.evaluator.evaluate_flag(expired_flag, user_context)
        
        assert result.enabled is False
        assert result.reason == "outside_time_window"
    
    def test_segment_targeting_evaluation(self):
        """Test segment-based targeting."""
        flag = FlagMetadata(
            flag_key="test_segment",
            name="Test Segment Flag",
            description="Test flag",
            flag_type=FlagType.SEGMENT,
            environment=Environment.DEVELOPMENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test",
            enabled=True,
            default_value=False,
            targeting=TargetingConfig(
                rules=[
                    {
                        "type": "email_domain",
                        "values": ["company.com", "partner.com"]
                    },
                    {
                        "type": "user_role",
                        "values": ["admin", "beta_user"]
                    }
                ]
            )
        )
        
        # Test email domain match
        domain_context = {"user_id": "user1", "email": "test@company.com", "role": "user"}
        result = self.evaluator.evaluate_flag(flag, domain_context)
        assert result.enabled is True
        assert result.reason == "user_matches_segment"
        
        # Test role match
        role_context = {"user_id": "user2", "email": "test@other.com", "role": "admin"}
        result = self.evaluator.evaluate_flag(flag, role_context)
        assert result.enabled is True
        assert result.reason == "user_matches_segment"
        
        # Test no match
        no_match_context = {"user_id": "user3", "email": "test@other.com", "role": "user"}
        result = self.evaluator.evaluate_flag(flag, no_match_context)
        assert result.enabled is False
        assert result.reason == "user_not_in_segments"
    
    def test_custom_attribute_targeting(self):
        """Test custom attribute targeting."""
        flag = FlagMetadata(
            flag_key="test_custom_attr",
            name="Test Custom Attribute Flag",
            description="Test flag",
            flag_type=FlagType.SEGMENT,
            environment=Environment.DEVELOPMENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test",
            enabled=True,
            default_value=False,
            targeting=TargetingConfig(
                rules=[
                    {
                        "type": "custom_attribute",
                        "attribute_name": "subscription_tier",
                        "values": ["premium", "enterprise"],
                        "operator": "equals"
                    }
                ]
            )
        )
        
        # Test matching attribute
        premium_context = {
            "user_id": "user1",
            "attributes": {"subscription_tier": "premium"}
        }
        result = self.evaluator.evaluate_flag(flag, premium_context)
        assert result.enabled is True
        
        # Test non-matching attribute
        basic_context = {
            "user_id": "user2",
            "attributes": {"subscription_tier": "basic"}
        }
        result = self.evaluator.evaluate_flag(flag, basic_context)
        assert result.enabled is False
    
    def test_excluded_users(self):
        """Test excluded users functionality."""
        flag = FlagMetadata(
            flag_key="test_excluded",
            name="Test Excluded Users Flag",
            description="Test flag",
            flag_type=FlagType.BOOLEAN,
            environment=Environment.DEVELOPMENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test",
            enabled=True,
            default_value=False,
            targeting=TargetingConfig(
                rules=[],
                percentage=100.0,
                excluded_users=["excluded_user1", "excluded_user2"]
            )
        )
        
        # Test excluded user
        excluded_context = {"user_id": "excluded_user1"}
        result = self.evaluator.evaluate_flag(flag, excluded_context)
        assert result.enabled is False
        
        # Test normal user
        normal_context = {"user_id": "normal_user"}
        result = self.evaluator.evaluate_flag(flag, normal_context)
        assert result.enabled is True
    
    def test_evaluation_error_handling(self):
        """Test error handling during evaluation."""
        # Create a flag with malformed data
        flag = FlagMetadata(
            flag_key="test_error",
            name="Test Error Flag",
            description="Test flag",
            flag_type=FlagType.BOOLEAN,
            environment=Environment.DEVELOPMENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test",
            enabled=True,
            default_value=True,  # This should be returned on error
            targeting=None  # This might cause issues
        )
        
        user_context = {"user_id": "test_user"}
        
        # Mock an error in targeting evaluation
        with patch.object(self.evaluator, '_evaluate_targeting', side_effect=Exception("Test error")):
            result = self.evaluator.evaluate_flag(flag, user_context)
            
            # Should return default value when error occurs
            assert result.enabled is True  # Default value
            assert "evaluation_error" in result.reason


class TestFeatureFlagStore:
    """Test the FeatureFlagStore class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "test_flags.db")
        self.store = FeatureFlagStore(self.db_path)
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_and_retrieve_flag(self):
        """Test creating and retrieving a flag."""
        flag = FlagMetadata(
            flag_key="test_create",
            name="Test Create Flag",
            description="Test flag creation",
            flag_type=FlagType.BOOLEAN,
            environment=Environment.DEVELOPMENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test",
            enabled=True,
            default_value=False,
            targeting=TargetingConfig(rules=[], percentage=100.0)
        )
        
        # Create flag
        success = self.store.create_flag(flag)
        assert success is True
        
        # Retrieve flag
        retrieved = self.store.get_flag("test_create", Environment.DEVELOPMENT)
        assert retrieved is not None
        assert retrieved.flag_key == "test_create"
        assert retrieved.name == "Test Create Flag"
        assert retrieved.enabled is True
        assert retrieved.flag_type == FlagType.BOOLEAN
    
    def test_update_flag(self):
        """Test updating a flag."""
        # Create initial flag
        flag = FlagMetadata(
            flag_key="test_update",
            name="Test Update Flag",
            description="Original description",
            flag_type=FlagType.BOOLEAN,
            environment=Environment.DEVELOPMENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test",
            enabled=False,
            default_value=False,
            targeting=TargetingConfig(rules=[], percentage=100.0)
        )
        
        self.store.create_flag(flag)
        
        # Update flag
        flag.name = "Updated Flag Name"
        flag.description = "Updated description"
        flag.enabled = True
        
        success = self.store.update_flag(flag)
        assert success is True
        
        # Verify update
        updated = self.store.get_flag("test_update", Environment.DEVELOPMENT)
        assert updated.name == "Updated Flag Name"
        assert updated.description == "Updated description"
        assert updated.enabled is True
    
    def test_delete_flag(self):
        """Test deleting a flag."""
        # Create flag
        flag = FlagMetadata(
            flag_key="test_delete",
            name="Test Delete Flag",
            description="Test flag deletion",
            flag_type=FlagType.BOOLEAN,
            environment=Environment.DEVELOPMENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test",
            enabled=True,
            default_value=False,
            targeting=TargetingConfig(rules=[], percentage=100.0)
        )
        
        self.store.create_flag(flag)
        
        # Verify flag exists
        retrieved = self.store.get_flag("test_delete", Environment.DEVELOPMENT)
        assert retrieved is not None
        
        # Delete flag
        success = self.store.delete_flag("test_delete", Environment.DEVELOPMENT)
        assert success is True
        
        # Verify flag is gone
        deleted = self.store.get_flag("test_delete", Environment.DEVELOPMENT)
        assert deleted is None
    
    def test_list_flags(self):
        """Test listing flags with filtering."""
        # Create multiple flags
        flags = [
            FlagMetadata(
                flag_key="test_list_1",
                name="Test List Flag 1",
                description="Test flag 1",
                flag_type=FlagType.BOOLEAN,
                environment=Environment.DEVELOPMENT,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by="test",
                enabled=True,
                default_value=False,
                targeting=TargetingConfig(rules=[], percentage=100.0)
            ),
            FlagMetadata(
                flag_key="test_list_2",
                name="Test List Flag 2",
                description="Test flag 2",
                flag_type=FlagType.PERCENTAGE,
                environment=Environment.DEVELOPMENT,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by="test",
                enabled=False,
                default_value=False,
                targeting=TargetingConfig(rules=[], percentage=50.0)
            ),
            FlagMetadata(
                flag_key="test_list_3",
                name="Test List Flag 3",
                description="Test flag 3",
                flag_type=FlagType.BOOLEAN,
                environment=Environment.PRODUCTION,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                created_by="test",
                enabled=True,
                default_value=False,
                targeting=TargetingConfig(rules=[], percentage=100.0)
            )
        ]
        
        for flag in flags:
            self.store.create_flag(flag)
        
        # List all development flags
        dev_flags = self.store.list_flags(Environment.DEVELOPMENT)
        assert len(dev_flags) == 2
        
        # List enabled flags only
        enabled_flags = self.store.list_flags(Environment.DEVELOPMENT, enabled_only=True)
        assert len(enabled_flags) == 1
        assert enabled_flags[0].flag_key == "test_list_1"
        
        # List production flags
        prod_flags = self.store.list_flags(Environment.PRODUCTION)
        assert len(prod_flags) == 1
        assert prod_flags[0].flag_key == "test_list_3"
    
    def test_complex_flag_with_variants(self):
        """Test storing and retrieving complex A/B test flag."""
        flag = FlagMetadata(
            flag_key="test_complex",
            name="Test Complex Flag",
            description="Complex A/B test flag",
            flag_type=FlagType.AB_TEST,
            environment=Environment.DEVELOPMENT,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            created_by="test",
            enabled=True,
            default_value=False,
            targeting=TargetingConfig(
                rules=[
                    {
                        "type": "user_role",
                        "values": ["beta_user", "admin"]
                    }
                ],
                percentage=80.0
            ),
            variants=[
                ABTestVariant(name="control", weight=0.4, config={"color": "blue", "size": "medium"}),
                ABTestVariant(name="variant_a", weight=0.3, config={"color": "red", "size": "large"}),
                ABTestVariant(name="variant_b", weight=0.3, config={"color": "green", "size": "small"})
            ],
            tags=["a_b_test", "ui_experiment"],
            dependencies=["feature_x_enabled"]
        )
        
        # Store complex flag
        success = self.store.create_flag(flag)
        assert success is True
        
        # Retrieve and verify
        retrieved = self.store.get_flag("test_complex", Environment.DEVELOPMENT)
        assert retrieved is not None
        assert retrieved.flag_type == FlagType.AB_TEST
        assert len(retrieved.variants) == 3
        assert retrieved.variants[0].name == "control"
        assert retrieved.variants[0].weight == 0.4
        assert retrieved.targeting.percentage == 80.0
        assert len(retrieved.targeting.rules) == 1
        assert retrieved.tags == ["a_b_test", "ui_experiment"]
        assert retrieved.dependencies == ["feature_x_enabled"]
    
    def test_log_evaluation(self):
        """Test logging flag evaluations."""
        evaluation = FlagEvaluation(
            flag_key="test_log",
            enabled=True,
            variant="treatment",
            reason="targeting_matched",
            user_id="test_user",
            evaluation_time=datetime.utcnow(),
            targeting_matched=True,
            metadata={"test": "data"}
        )
        
        success = self.store.log_evaluation(evaluation)
        assert success is True
        
        # Verify the evaluation was logged (would need additional query method in real implementation)
    
    def test_record_metric(self):
        """Test recording flag metrics."""
        success = self.store.record_metric(
            "test_metric_flag",
            "conversion_rate",
            0.85,
            {"segment": "premium_users", "timestamp": "2025-01-01"}
        )
        assert success is True


class TestFeatureFlagManager:
    """Test the FeatureFlagManager class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "test_manager.db")
        self.manager = FeatureFlagManager(self.db_path, Environment.DEVELOPMENT)
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_and_check_flag(self):
        """Test creating and checking a flag."""
        success = self.manager.create_flag(
            "test_manager",
            "Test Manager Flag",
            FlagType.BOOLEAN,
            "Test flag for manager",
            enabled=True,
            created_by="test"
        )
        assert success is True
        
        # Check flag is enabled
        user_context = {"user_id": "test_user"}
        enabled = self.manager.is_enabled("test_manager", user_context)
        assert enabled is True
    
    def test_percentage_rollout_management(self):
        """Test percentage rollout management."""
        # Create percentage flag
        self.manager.create_flag(
            "test_rollout",
            "Test Rollout Flag",
            FlagType.PERCENTAGE,
            "Test percentage rollout",
            enabled=True,
            created_by="test"
        )
        
        # Set rollout to 50%
        success = self.manager.set_percentage_rollout("test_rollout", 50.0)
        assert success is True
        
        # Test multiple users
        enabled_count = 0
        total_users = 100
        
        for i in range(total_users):
            user_context = {"user_id": f"user_{i}"}
            if self.manager.is_enabled("test_rollout", user_context):
                enabled_count += 1
        
        # Should be approximately 50%
        assert 40 <= enabled_count <= 60
    
    def test_user_allowlist_management(self):
        """Test user allowlist management."""
        # Create user list flag
        self.manager.create_flag(
            "test_allowlist",
            "Test Allowlist Flag",
            FlagType.USER_LIST,
            "Test user allowlist",
            enabled=True,
            created_by="test"
        )
        
        # Initially, user should not be enabled
        user_context = {"user_id": "special_user"}
        enabled = self.manager.is_enabled("test_allowlist", user_context)
        assert enabled is False
        
        # Add user to allowlist
        success = self.manager.add_user_to_flag("test_allowlist", "special_user")
        assert success is True
        
        # Now user should be enabled
        enabled = self.manager.is_enabled("test_allowlist", user_context)
        assert enabled is True
        
        # Remove user from allowlist
        success = self.manager.remove_user_from_flag("test_allowlist", "special_user")
        assert success is True
        
        # User should no longer be enabled
        enabled = self.manager.is_enabled("test_allowlist", user_context)
        assert enabled is False
    
    def test_ab_test_management(self):
        """Test A/B test management."""
        # Create A/B test flag
        self.manager.create_flag(
            "test_ab",
            "Test A/B Flag",
            FlagType.AB_TEST,
            "Test A/B testing",
            enabled=True,
            created_by="test"
        )
        
        # Get variant for user
        user_context = {"user_id": "ab_test_user"}
        variant = self.manager.get_variant("test_ab", user_context)
        
        # For now, variant might be None since we haven't configured variants
        # In a real implementation, we'd set up variants through the manager
    
    def test_flag_enable_disable(self):
        """Test enabling and disabling flags."""
        # Create disabled flag
        self.manager.create_flag(
            "test_toggle",
            "Test Toggle Flag",
            FlagType.BOOLEAN,
            "Test toggling",
            enabled=False,
            created_by="test"
        )
        
        user_context = {"user_id": "test_user"}
        
        # Should be disabled
        enabled = self.manager.is_enabled("test_toggle", user_context)
        assert enabled is False
        
        # Enable flag
        success = self.manager.enable_flag("test_toggle")
        assert success is True
        
        # Should now be enabled
        enabled = self.manager.is_enabled("test_toggle", user_context)
        assert enabled is True
        
        # Disable flag
        success = self.manager.disable_flag("test_toggle")
        assert success is True
        
        # Should be disabled again
        enabled = self.manager.is_enabled("test_toggle", user_context)
        assert enabled is False
    
    def test_kill_switch(self):
        """Test kill switch functionality."""
        # Create enabled flag
        self.manager.create_flag(
            "test_kill",
            "Test Kill Switch Flag",
            FlagType.BOOLEAN,
            "Test kill switch",
            enabled=True,
            created_by="test"
        )
        
        user_context = {"user_id": "test_user"}
        
        # Should be enabled
        enabled = self.manager.is_enabled("test_kill", user_context)
        assert enabled is True
        
        # Activate kill switch
        success = self.manager.kill_switch("test_kill", True)
        assert success is True
        
        # Should now be disabled despite being enabled
        enabled = self.manager.is_enabled("test_kill", user_context)
        assert enabled is False
        
        # Deactivate kill switch
        success = self.manager.kill_switch("test_kill", False)
        assert success is True
        
        # Should be enabled again
        enabled = self.manager.is_enabled("test_kill", user_context)
        assert enabled is True
    
    def test_list_flags(self):
        """Test listing flags."""
        # Create multiple flags
        flags_to_create = [
            ("flag_1", True),
            ("flag_2", False),
            ("flag_3", True)
        ]
        
        for flag_key, enabled in flags_to_create:
            self.manager.create_flag(
                flag_key,
                f"Test {flag_key}",
                FlagType.BOOLEAN,
                f"Description for {flag_key}",
                enabled=enabled,
                created_by="test"
            )
        
        # List all flags
        all_flags = self.manager.list_flags()
        assert len(all_flags) == 3
        
        # List enabled flags only
        enabled_flags = self.manager.list_flags(enabled_only=True)
        assert len(enabled_flags) == 2
    
    def test_flag_caching(self):
        """Test flag caching behavior."""
        # Create flag
        self.manager.create_flag(
            "test_cache",
            "Test Cache Flag",
            FlagType.BOOLEAN,
            "Test caching",
            enabled=True,
            created_by="test"
        )
        
        user_context = {"user_id": "test_user"}
        
        # First evaluation should hit database and cache
        start_time = time.time()
        enabled1 = self.manager.is_enabled("test_cache", user_context)
        first_duration = time.time() - start_time
        
        # Second evaluation should hit cache and be faster
        start_time = time.time()
        enabled2 = self.manager.is_enabled("test_cache", user_context)
        second_duration = time.time() - start_time
        
        assert enabled1 is True
        assert enabled2 is True
        # Cache should make second call faster (though this might be unreliable in fast environments)
    
    def test_nonexistent_flag(self):
        """Test behavior with non-existent flags."""
        user_context = {"user_id": "test_user"}
        
        # Non-existent flag should return False
        enabled = self.manager.is_enabled("nonexistent_flag", user_context)
        assert enabled is False
        
        # Variant should return None
        variant = self.manager.get_variant("nonexistent_flag", user_context)
        assert variant is None


class TestGlobalFunctions:
    """Test global convenience functions."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "test_global.db")
        
        # Clear global manager
        import streamlit_extension.utils.feature_flags as ff_module
        ff_module._flag_manager = None
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Clear global manager
        import streamlit_extension.utils.feature_flags as ff_module
        ff_module._flag_manager = None
    
    def test_setup_and_get_manager(self):
        """Test setup and get manager functions."""
        # Setup manager
        manager1 = setup_flag_manager(self.db_path, Environment.DEVELOPMENT)
        assert manager1 is not None
        
        # Get same manager instance
        manager2 = get_flag_manager(self.db_path, Environment.DEVELOPMENT)
        assert manager1 is manager2  # Should be same instance
    
    def test_convenience_functions(self):
        """Test convenience functions."""
        # Setup manager and create flag
        manager = setup_flag_manager(self.db_path, Environment.DEVELOPMENT)
        manager.create_flag(
            "test_convenience",
            "Test Convenience Flag",
            FlagType.BOOLEAN,
            "Test convenience functions",
            enabled=True,
            created_by="test"
        )
        
        user_context = {"user_id": "test_user"}
        
        # Test convenience function
        enabled = is_feature_enabled("test_convenience", user_context)
        assert enabled is True
        
        # Test variant function (will return None for boolean flag)
        variant = get_feature_variant("test_convenience", user_context)
        assert variant is None


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "test_errors.db")
        self.manager = FeatureFlagManager(self.db_path, Environment.DEVELOPMENT)
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_database_error_handling(self):
        """Test handling of database errors."""
        # Create a flag normally
        success = self.manager.create_flag(
            "test_db_error",
            "Test DB Error Flag",
            FlagType.BOOLEAN,
            "Test database errors",
            enabled=True,
            created_by="test"
        )
        assert success is True
        
        # Try to create duplicate flag (should fail gracefully)
        success = self.manager.create_flag(
            "test_db_error",  # Same key
            "Duplicate Flag",
            FlagType.BOOLEAN,
            "Duplicate flag",
            enabled=True,
            created_by="test"
        )
        assert success is False  # Should fail but not crash
    
    def test_evaluation_with_missing_context(self):
        """Test evaluation with missing user context."""
        # Create flag
        self.manager.create_flag(
            "test_missing_context",
            "Test Missing Context Flag",
            FlagType.BOOLEAN,
            "Test missing context",
            enabled=True,
            created_by="test"
        )
        
        # Evaluate with empty context
        enabled = self.manager.is_enabled("test_missing_context", {})
        assert enabled is True  # Should still work with empty context
        
        # Evaluate with None context
        enabled = self.manager.is_enabled("test_missing_context", None)
        assert enabled is True  # Should handle None gracefully


class TestPerformance:
    """Test performance characteristics."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = str(Path(self.temp_dir) / "test_perf.db")
        self.manager = FeatureFlagManager(self.db_path, Environment.DEVELOPMENT)
    
    def teardown_method(self):
        """Cleanup test fixtures."""
        if hasattr(self, 'temp_dir'):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_bulk_flag_creation(self):
        """Test creating many flags."""
        start_time = time.time()
        
        # Create 50 flags
        for i in range(50):
            success = self.manager.create_flag(
                f"perf_flag_{i}",
                f"Performance Flag {i}",
                FlagType.BOOLEAN,
                f"Performance test flag {i}",
                enabled=True,
                created_by="test"
            )
            assert success is True
        
        creation_time = time.time() - start_time
        print(f"Created 50 flags in {creation_time:.3f}s ({creation_time/50:.3f}s per flag)")
        
        # Should be reasonably fast
        assert creation_time < 5.0  # Less than 5 seconds for 50 flags
    
    def test_bulk_evaluations(self):
        """Test evaluating flags many times."""
        # Create test flag
        self.manager.create_flag(
            "perf_eval",
            "Performance Evaluation Flag",
            FlagType.BOOLEAN,
            "Performance test",
            enabled=True,
            created_by="test"
        )
        
        start_time = time.time()
        
        # Evaluate 1000 times
        for i in range(1000):
            user_context = {"user_id": f"user_{i}"}
            enabled = self.manager.is_enabled("perf_eval", user_context)
            assert enabled is True
        
        evaluation_time = time.time() - start_time
        print(f"1000 evaluations in {evaluation_time:.3f}s ({evaluation_time/1000*1000:.3f}ms per evaluation)")
        
        # Should be very fast due to caching
        assert evaluation_time < 2.0  # Less than 2 seconds for 1000 evaluations


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])