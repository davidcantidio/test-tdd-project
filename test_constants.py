#!/usr/bin/env python3
"""
🧪 Constants and Enums Testing Suite

Tests the centralized constants addressing report.md requirement:
"Centralize hard-coded strings in enums/config"

This test validates:
- Enum value consistency
- Constants accessibility
- Configuration completeness
- No duplicate values
- Proper enum methods
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from streamlit_extension.config.constants import (
        TaskStatus, EpicStatus, ProjectStatus, GeneralStatus, TDDPhase,
        ClientTier, CompanySize, Priority, TableNames, FieldNames,
        UIConstants, FormFields, CacheConfig, FilterOptions, ValidationRules
    )
    CONSTANTS_AVAILABLE = True
except ImportError as e:
    CONSTANTS_AVAILABLE = False
    print(f"❌ Constants module not available: {e}")


def test_task_status_enum():
    """Test TaskStatus enum functionality."""
    if not CONSTANTS_AVAILABLE:
        return False
    
    print("📋 Testing TaskStatus Enum")
    print("=" * 40)
    
    try:
        # Test enum values
        assert TaskStatus.TODO.value == "todo", "TODO value should be 'todo'"
        assert TaskStatus.IN_PROGRESS.value == "in_progress", "IN_PROGRESS value should be 'in_progress'"
        assert TaskStatus.COMPLETED.value == "completed", "COMPLETED value should be 'completed'"
        assert TaskStatus.BLOCKED.value == "blocked", "BLOCKED value should be 'blocked'"
        assert TaskStatus.PENDING.value == "pending", "PENDING value should be 'pending'"
        
        print("✅ Enum values correct")
        
        # Test get_all_values method
        all_values = TaskStatus.get_all_values()
        expected_values = ["todo", "in_progress", "completed", "blocked", "pending"]
        assert set(all_values) == set(expected_values), "get_all_values should return all status values"
        
        print("✅ get_all_values method working")
        
        # Test get_active_statuses method
        active_statuses = TaskStatus.get_active_statuses()
        expected_active = ["todo", "in_progress", "blocked", "pending"]
        assert set(active_statuses) == set(expected_active), "get_active_statuses should exclude completed"
        
        print("✅ get_active_statuses method working")
        
        return True
        
    except Exception as e:
        print(f"❌ TaskStatus test failed: {e}")
        return False


def test_epic_status_enum():
    """Test EpicStatus enum functionality."""
    if not CONSTANTS_AVAILABLE:
        return False
    
    print("\n🎯 Testing EpicStatus Enum")
    print("-" * 35)
    
    try:
        # Test enum values
        assert EpicStatus.PLANNING.value == "planning", "PLANNING value should be 'planning'"
        assert EpicStatus.ACTIVE.value == "active", "ACTIVE value should be 'active'"
        assert EpicStatus.COMPLETED.value == "completed", "COMPLETED value should be 'completed'"
        
        print("✅ Enum values correct")
        
        # Test methods
        all_values = EpicStatus.get_all_values()
        assert len(all_values) == 6, "Should have 6 epic status values"
        
        active_statuses = EpicStatus.get_active_statuses()
        assert "completed" not in active_statuses, "Active statuses should not include completed"
        assert "archived" not in active_statuses, "Active statuses should not include archived"
        
        print("✅ Epic status methods working")
        
        return True
        
    except Exception as e:
        print(f"❌ EpicStatus test failed: {e}")
        return False


def test_client_tier_enum():
    """Test ClientTier enum functionality."""
    if not CONSTANTS_AVAILABLE:
        return False
    
    print("\n👥 Testing ClientTier Enum")
    print("-" * 30)
    
    try:
        # Test enum values
        assert ClientTier.BASIC.value == "basic", "BASIC value should be 'basic'"
        assert ClientTier.STANDARD.value == "standard", "STANDARD value should be 'standard'"
        assert ClientTier.PREMIUM.value == "premium", "PREMIUM value should be 'premium'"
        assert ClientTier.ENTERPRISE.value == "enterprise", "ENTERPRISE value should be 'enterprise'"
        
        print("✅ Client tier values correct")
        
        # Test get_default method
        default_tier = ClientTier.get_default()
        assert default_tier == "standard", "Default tier should be 'standard'"
        
        print("✅ Default tier method working")
        
        # Test all values
        all_tiers = ClientTier.get_all_values()
        assert len(all_tiers) == 4, "Should have 4 client tiers"
        
        print("✅ Client tier methods working")
        
        return True
        
    except Exception as e:
        print(f"❌ ClientTier test failed: {e}")
        return False


def test_company_size_enum():
    """Test CompanySize enum functionality."""
    if not CONSTANTS_AVAILABLE:
        return False
    
    print("\n🏢 Testing CompanySize Enum")
    print("-" * 32)
    
    try:
        # Test enum values
        sizes = CompanySize.get_all_values()
        expected_sizes = ["startup", "small", "medium", "large", "enterprise"]
        assert set(sizes) == set(expected_sizes), "Should have all expected company sizes"
        
        print("✅ Company size values correct")
        
        # Test default
        default_size = CompanySize.get_default()
        assert default_size == "startup", "Default size should be 'startup'"
        
        print("✅ Default size method working")
        
        return True
        
    except Exception as e:
        print(f"❌ CompanySize test failed: {e}")
        return False


def test_tdd_phase_enum():
    """Test TDDPhase enum functionality."""
    if not CONSTANTS_AVAILABLE:
        return False
    
    print("\n🔄 Testing TDDPhase Enum")
    print("-" * 28)
    
    try:
        # Test enum values
        assert TDDPhase.RED.value == "red", "RED value should be 'red'"
        assert TDDPhase.GREEN.value == "green", "GREEN value should be 'green'"
        assert TDDPhase.REFACTOR.value == "refactor", "REFACTOR value should be 'refactor'"
        
        print("✅ TDD phase values correct")
        
        # Test all values
        phases = TDDPhase.get_all_values()
        assert len(phases) == 3, "Should have 3 TDD phases"
        assert set(phases) == {"red", "green", "refactor"}, "Should have correct TDD phases"
        
        print("✅ TDD phase methods working")
        
        return True
        
    except Exception as e:
        print(f"❌ TDDPhase test failed: {e}")
        return False


def test_priority_enum():
    """Test Priority enum functionality."""
    if not CONSTANTS_AVAILABLE:
        return False
    
    print("\n⭐ Testing Priority Enum")
    print("-" * 26)
    
    try:
        # Test enum values
        assert Priority.HIGH.value == 1, "HIGH priority should be 1"
        assert Priority.MEDIUM.value == 2, "MEDIUM priority should be 2"
        assert Priority.LOW.value == 3, "LOW priority should be 3"
        
        print("✅ Priority values correct")
        
        # Test default
        default_priority = Priority.get_default()
        assert default_priority == 2, "Default priority should be 2 (MEDIUM)"
        
        print("✅ Default priority method working")
        
        # Test all values
        all_priorities = Priority.get_all_values()
        assert set(all_priorities) == {1, 2, 3}, "Should have priorities 1, 2, 3"
        
        print("✅ Priority methods working")
        
        return True
        
    except Exception as e:
        print(f"❌ Priority test failed: {e}")
        return False


def test_table_names():
    """Test TableNames constants."""
    if not CONSTANTS_AVAILABLE:
        return False
    
    print("\n🗄️ Testing TableNames Constants")
    print("-" * 35)
    
    try:
        # Test table name constants
        assert hasattr(TableNames, 'FRAMEWORK_EPICS'), "Should have FRAMEWORK_EPICS"
        assert hasattr(TableNames, 'FRAMEWORK_TASKS'), "Should have FRAMEWORK_TASKS"
        assert hasattr(TableNames, 'CLIENTS'), "Should have CLIENTS"
        assert hasattr(TableNames, 'PROJECTS'), "Should have PROJECTS"
        
        assert TableNames.FRAMEWORK_EPICS == "framework_epics", "Table name should match"
        assert TableNames.FRAMEWORK_TASKS == "framework_tasks", "Table name should match"
        
        print("✅ Table names correct")
        
        return True
        
    except Exception as e:
        print(f"❌ TableNames test failed: {e}")
        return False


def test_field_names():
    """Test FieldNames constants."""
    if not CONSTANTS_AVAILABLE:
        return False
    
    print("\n📊 Testing FieldNames Constants")
    print("-" * 34)
    
    try:
        # Test field name constants
        assert FieldNames.ID == "id", "ID field should be 'id'"
        assert FieldNames.NAME == "name", "NAME field should be 'name'"
        assert FieldNames.STATUS == "status", "STATUS field should be 'status'"
        assert FieldNames.CREATED_AT == "created_at", "CREATED_AT field should be 'created_at'"
        
        print("✅ Field names correct")
        
        return True
        
    except Exception as e:
        print(f"❌ FieldNames test failed: {e}")
        return False


def test_ui_constants():
    """Test UIConstants."""
    if not CONSTANTS_AVAILABLE:
        return False
    
    print("\n🖥️ Testing UIConstants")
    print("-" * 24)
    
    try:
        # Test page titles
        assert "Client" in UIConstants.CLIENTS_PAGE_TITLE, "Clients page title should mention client"
        assert "Project" in UIConstants.PROJECTS_PAGE_TITLE, "Projects page title should mention project"
        
        # Test button text
        assert "Edit" in UIConstants.EDIT_BUTTON, "Edit button should mention edit"
        assert "Delete" in UIConstants.DELETE_BUTTON, "Delete button should mention delete"
        
        # Test messages
        assert "success" in UIConstants.SUCCESS_CREATE.lower(), "Success message should mention success"
        assert "error" in UIConstants.ERROR_GENERIC.lower(), "Error message should mention error"
        
        print("✅ UI constants correct")
        
        return True
        
    except Exception as e:
        print(f"❌ UIConstants test failed: {e}")
        return False


def test_filter_options():
    """Test FilterOptions configuration."""
    if not CONSTANTS_AVAILABLE:
        return False
    
    print("\n🔍 Testing FilterOptions")
    print("-" * 26)
    
    try:
        # Test filter options
        assert FilterOptions.ALL_OPTION == "all", "All option should be 'all'"
        
        # Test status filters
        task_filters = FilterOptions.STATUS_FILTERS["tasks"]
        assert "all" in task_filters, "Task filters should include 'all'"
        assert "todo" in task_filters, "Task filters should include 'todo'"
        assert "completed" in task_filters, "Task filters should include 'completed'"
        
        # Test tier filters
        tier_filters = FilterOptions.TIER_FILTERS
        assert "all" in tier_filters, "Tier filters should include 'all'"
        assert "basic" in tier_filters, "Tier filters should include 'basic'"
        
        print("✅ Filter options correct")
        
        return True
        
    except Exception as e:
        print(f"❌ FilterOptions test failed: {e}")
        return False


def test_validation_rules():
    """Test ValidationRules constants."""
    if not CONSTANTS_AVAILABLE:
        return False
    
    print("\n✅ Testing ValidationRules")
    print("-" * 29)
    
    try:
        # Test length limits
        assert ValidationRules.MAX_NAME_LENGTH > 0, "Max name length should be positive"
        assert ValidationRules.MIN_KEY_LENGTH > 0, "Min key length should be positive"
        assert ValidationRules.MAX_KEY_LENGTH > ValidationRules.MIN_KEY_LENGTH, "Max key length should be greater than min"
        
        # Test numeric limits
        assert ValidationRules.MIN_PRIORITY == 1, "Min priority should be 1"
        assert ValidationRules.MAX_PRIORITY == 3, "Max priority should be 3"
        assert ValidationRules.MIN_HOURLY_RATE >= 0, "Min hourly rate should be non-negative"
        
        # Test regex patterns
        assert ValidationRules.EMAIL_PATTERN, "Email pattern should exist"
        assert ValidationRules.PHONE_PATTERN, "Phone pattern should exist"
        
        print("✅ Validation rules correct")
        
        return True
        
    except Exception as e:
        print(f"❌ ValidationRules test failed: {e}")
        return False


def test_constants_no_duplicates():
    """Test that constants don't have duplicate values where they shouldn't."""
    if not CONSTANTS_AVAILABLE:
        return False
    
    print("\n🔍 Testing No Duplicate Values")
    print("-" * 35)
    
    try:
        # Test task statuses are unique
        task_values = TaskStatus.get_all_values()
        assert len(task_values) == len(set(task_values)), "Task status values should be unique"
        
        # Test epic statuses are unique
        epic_values = EpicStatus.get_all_values()
        assert len(epic_values) == len(set(epic_values)), "Epic status values should be unique"
        
        # Test client tiers are unique
        tier_values = ClientTier.get_all_values()
        assert len(tier_values) == len(set(tier_values)), "Client tier values should be unique"
        
        print("✅ No duplicate values found")
        
        return True
        
    except Exception as e:
        print(f"❌ Duplicate values test failed: {e}")
        return False


def main():
    """Main test execution."""
    print("🏗️ CONSTANTS AND ENUMS TEST SUITE")
    print("=" * 60)
    print("Addresses report.md requirement:")
    print("- Centralize hard-coded strings in enums/config")
    print()
    
    if not CONSTANTS_AVAILABLE:
        print("❌ Constants system not available")
        return False
    
    tests = [
        ("TaskStatus Enum", test_task_status_enum),
        ("EpicStatus Enum", test_epic_status_enum),
        ("ClientTier Enum", test_client_tier_enum),
        ("CompanySize Enum", test_company_size_enum),
        ("TDDPhase Enum", test_tdd_phase_enum),
        ("Priority Enum", test_priority_enum),
        ("TableNames Constants", test_table_names),
        ("FieldNames Constants", test_field_names),
        ("UIConstants", test_ui_constants),
        ("FilterOptions", test_filter_options),
        ("ValidationRules", test_validation_rules),
        ("No Duplicates", test_constants_no_duplicates),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
    
    print("-" * 60)
    print(f"Tests passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Constants and enums are working correctly")
        print("✅ Report.md requirement fulfilled: Hard-coded strings centralized")
        print("✅ Enums provide type safety and consistency")
        print("✅ Configuration is maintainable and extensible")
        return True
    else:
        print(f"\n❌ {total-passed} tests failed")
        print("❗ Constants system needs fixes")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)