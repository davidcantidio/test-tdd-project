#!/usr/bin/env python3
"""
🧪 Step 2.3.2 - Enhanced Test Integration for Migration Validation

Integration test module that connects migration validation with existing test infrastructure.
Adds pytest markers and comprehensive test integration for migration checkpoints.

Features:
- Migration-specific pytest markers (migration_batch1, migration_batch2, migration_batch3)
- Integration with comprehensive_integrity_test.py
- Automated validation checkpoints with rollback capability
- Performance regression detection during migration
- Detailed migration test reporting
"""

import pytest
import sys
import subprocess
import importlib.util
from pathlib import Path
from typing import Dict, List, Any, Optional

# Migration validation imports
try:
    from migration_validation import MigrationValidationOrchestrator
    from batch1_checkpoints import Batch1ValidationCheckpoints
    from batch2_checkpoints import Batch2ValidationCheckpoints  
    from batch3_checkpoints import Batch3ValidationCheckpoints
    from rollback_manager import RollbackManager
    MIGRATION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Migration validation not available: {e}")
    MIGRATION_AVAILABLE = False

# Comprehensive test integration
try:
    spec = importlib.util.spec_from_file_location(
        "comprehensive_integrity_test", 
        "scripts/testing/comprehensive_integrity_test.py"
    )
    comprehensive_test = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(comprehensive_test)
    COMPREHENSIVE_TEST_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Comprehensive test not available: {e}")
    COMPREHENSIVE_TEST_AVAILABLE = False

# Migration-specific pytest markers
pytest_plugins = []

def pytest_configure(config):
    """Configure pytest with migration markers."""
    config.addinivalue_line(
        "markers", "migration_batch1: mark test as batch 1 migration validation"
    )
    config.addinivalue_line(
        "markers", "migration_batch2: mark test as batch 2 migration validation"
    )
    config.addinivalue_line(
        "markers", "migration_batch3: mark test as batch 3 migration validation"
    )
    config.addinivalue_line(
        "markers", "migration_validation: mark test as migration validation"
    )
    config.addinivalue_line(
        "markers", "rollback_test: mark test as rollback validation"
    )
    config.addinivalue_line(
        "markers", "migration_performance: mark test as migration performance validation"
    )

@pytest.fixture(scope="session")
def migration_orchestrator():
    """Migration validation orchestrator fixture."""
    if not MIGRATION_AVAILABLE:
        pytest.skip("Migration validation not available")
    return MigrationValidationOrchestrator()

@pytest.fixture(scope="session")
def comprehensive_validator():
    """Comprehensive integrity validator fixture."""
    if not COMPREHENSIVE_TEST_AVAILABLE:
        pytest.skip("Comprehensive test not available")
    return comprehensive_test.IntegrityValidator()

@pytest.fixture(scope="session")
def rollback_manager():
    """Rollback manager fixture."""
    if not MIGRATION_AVAILABLE:
        pytest.skip("Migration validation not available")
    return RollbackManager()

# Migration Batch 1 Tests
@pytest.mark.migration_batch1
@pytest.mark.migration_validation
class TestBatch1Migration:
    """Test suite for Batch 1 migration validation (Simple Replacements)."""
    
    def test_batch1_api_readiness(self, migration_orchestrator):
        """Test API replacement readiness for Batch 1 files."""
        validator = Batch1ValidationCheckpoints()
        result = validator.validate_api_replacement_readiness()
        assert result['overall_status'] is True, f"API not ready: {result.get('issues', [])}"
    
    def test_batch1_modular_api_availability(self, migration_orchestrator):
        """Test modular API availability for Batch 1."""
        validator = Batch1ValidationCheckpoints()
        result = validator.validate_modular_api_availability()
        assert result['apis_available'] >= 10, "Insufficient modular APIs available"
    
    @pytest.mark.migration_performance
    def test_batch1_performance_baseline(self, migration_orchestrator):
        """Test performance baseline for Batch 1 migration."""
        validator = Batch1ValidationCheckpoints()
        result = validator.validate_performance_baseline()
        assert result['baseline_established'] is True, "Performance baseline not established"
        assert result['average_query_time_ms'] < 50, "Query performance below threshold"

# Migration Batch 2 Tests  
@pytest.mark.migration_batch2
@pytest.mark.migration_validation
class TestBatch2Migration:
    """Test suite for Batch 2 migration validation (Service Layer Required)."""
    
    def test_batch2_service_container_config(self, migration_orchestrator):
        """Test ServiceContainer configuration for Batch 2."""
        validator = Batch2ValidationCheckpoints()
        result = validator.validate_service_container_configuration()
        assert result['configuration_valid'] is True, f"ServiceContainer not configured: {result.get('issues', [])}"
    
    def test_batch2_business_services_availability(self, migration_orchestrator):
        """Test 5 business services availability."""
        validator = Batch2ValidationCheckpoints()
        result = validator.validate_business_services_availability()
        assert result['services_available'] == 5, f"Expected 5 services, got {result['services_available']}"
        
        required_services = ['ProjectService', 'EpicService', 'TaskService', 'AnalyticsService', 'TimerService']
        for service in required_services:
            assert service in result['available_services'], f"Service {service} not available"
    
    @pytest.mark.migration_performance
    def test_batch2_service_layer_performance(self, migration_orchestrator):
        """Test service layer performance requirements."""
        validator = Batch2ValidationCheckpoints()
        result = validator.validate_service_layer_performance()
        assert result['performance_acceptable'] is True, "Service layer performance below threshold"

# Migration Batch 3 Tests
@pytest.mark.migration_batch3 
@pytest.mark.migration_validation
class TestBatch3Migration:
    """Test suite for Batch 3 migration validation (Complex/Hybrid)."""
    
    def test_batch3_critical_ui_components(self, migration_orchestrator):
        """Test critical UI components for Batch 3."""
        validator = Batch3ValidationCheckpoints()
        result = validator.validate_critical_ui_components()
        assert result['components_functional'] is True, f"UI components not functional: {result.get('issues', [])}"
        
        # Validate specific critical components
        critical_components = ['kanban', 'analytics', 'timer']
        for component in critical_components:
            assert component in result['tested_components'], f"Component {component} not tested"
    
    def test_batch3_hybrid_compatibility(self, migration_orchestrator):
        """Test hybrid architecture compatibility."""
        validator = Batch3ValidationCheckpoints()
        result = validator.validate_hybrid_architecture_compatibility()
        assert result['hybrid_compatible'] is True, "Hybrid architecture not compatible"
    
    @pytest.mark.migration_performance
    def test_batch3_complex_query_performance(self, migration_orchestrator):
        """Test complex query performance for Batch 3."""
        validator = Batch3ValidationCheckpoints()
        result = validator.validate_complex_query_performance()
        assert result['performance_acceptable'] is True, "Complex query performance below threshold"
        assert result['max_query_time_ms'] < 200, f"Query time too high: {result['max_query_time_ms']}ms"

# Rollback Testing
@pytest.mark.rollback_test
@pytest.mark.migration_validation 
class TestMigrationRollback:
    """Test suite for migration rollback functionality."""
    
    def test_rollback_manager_initialization(self, rollback_manager):
        """Test rollback manager initialization."""
        assert rollback_manager is not None
        result = rollback_manager.validate_rollback_readiness()
        assert result['rollback_ready'] is True, "Rollback manager not ready"
    
    def test_backup_creation(self, rollback_manager):
        """Test backup creation functionality."""
        result = rollback_manager.create_backup(backup_type='migration_test')
        assert result['backup_created'] is True, "Backup creation failed"
        assert 'backup_id' in result, "Backup ID not generated"
    
    def test_emergency_rollback_capability(self, rollback_manager):
        """Test emergency rollback capability."""
        result = rollback_manager.validate_emergency_rollback_capability()
        assert result['emergency_rollback_ready'] is True, "Emergency rollback not ready"

# Comprehensive Integration Tests
@pytest.mark.migration_validation
class TestMigrationComprehensiveIntegration:
    """Integration tests with comprehensive validation system."""
    
    def test_integration_with_comprehensive_validator(self, migration_orchestrator, comprehensive_validator):
        """Test integration with comprehensive integrity validator."""
        if not COMPREHENSIVE_TEST_AVAILABLE:
            pytest.skip("Comprehensive test not available")
            
        # Run comprehensive validation
        comp_result = comprehensive_validator.run_all_validations()
        
        # Run migration validation
        migration_result = migration_orchestrator.run_all_checkpoints()
        
        # Validate both systems pass
        assert comp_result['overall_status'] is True, "Comprehensive validation failed"
        assert migration_result['overall_status'] is True, "Migration validation failed"
        
        # Cross-validate data integrity
        assert comp_result['referential_integrity'] is True, "Referential integrity issues detected"
        assert migration_result['data_integrity_maintained'] is True, "Migration data integrity issues"
    
    @pytest.mark.migration_performance
    def test_performance_regression_detection(self, migration_orchestrator, comprehensive_validator):
        """Test performance regression detection during migration."""
        if not COMPREHENSIVE_TEST_AVAILABLE:
            pytest.skip("Comprehensive test not available")
        
        # Establish baseline performance
        baseline = comprehensive_validator.run_performance_benchmarks()
        
        # Simulate migration operations
        migration_result = migration_orchestrator.validate_batch(batch_number=1, performance_check=True)
        
        # Validate no performance regression
        current_performance = migration_result['performance_metrics']
        
        # Allow up to 10% performance degradation during migration
        performance_threshold = baseline['average_query_time'] * 1.1
        assert current_performance['average_query_time'] <= performance_threshold, \
            f"Performance regression detected: {current_performance['average_query_time']}ms > {performance_threshold}ms"

# Migration CLI Integration Tests
@pytest.mark.migration_validation
class TestMigrationCLIIntegration:
    """Test CLI integration for migration validation."""
    
    def test_migration_validation_cli_batch1(self):
        """Test migration validation CLI for batch 1."""
        result = subprocess.run(
            [sys.executable, "migration_validation.py", "--batch", "1", "--dry-run"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"CLI batch 1 validation failed: {result.stderr}"
    
    def test_migration_validation_cli_comprehensive(self):
        """Test comprehensive migration validation via CLI."""
        result = subprocess.run(
            [sys.executable, "migration_validation.py", "--comprehensive", "--dry-run"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"CLI comprehensive validation failed: {result.stderr}"
    
    def test_rollback_cli_functionality(self):
        """Test rollback CLI functionality."""
        result = subprocess.run(
            [sys.executable, "migration_validation.py", "--test-rollback"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"CLI rollback test failed: {result.stderr}"

# Utility Functions for Test Integration
def run_migration_test_suite(batch_number: Optional[int] = None) -> Dict[str, Any]:
    """Run migration test suite with optional batch filtering."""
    pytest_args = ["-v", "-m", "migration_validation"]
    
    if batch_number:
        pytest_args.extend(["-m", f"migration_batch{batch_number}"])
    
    # Add current file as test target
    pytest_args.append(__file__)
    
    exit_code = pytest.main(pytest_args)
    
    return {
        "exit_code": exit_code,
        "success": exit_code == 0,
        "batch_tested": batch_number,
        "timestamp": "2025-08-24T12:00:00Z"
    }

def generate_migration_test_report() -> Dict[str, Any]:
    """Generate comprehensive migration test report."""
    report = {
        "test_suite": "Migration Validation Enhanced Integration",
        "timestamp": "2025-08-24T12:00:00Z",
        "pytest_markers": [
            "migration_batch1",
            "migration_batch2", 
            "migration_batch3",
            "migration_validation",
            "rollback_test",
            "migration_performance"
        ],
        "integration_points": [
            "comprehensive_integrity_test.py",
            "migration_validation.py",
            "batch1_checkpoints.py",
            "batch2_checkpoints.py",
            "batch3_checkpoints.py",
            "rollback_manager.py"
        ],
        "test_categories": {
            "batch1_tests": 3,
            "batch2_tests": 3, 
            "batch3_tests": 3,
            "rollback_tests": 3,
            "integration_tests": 2,
            "cli_tests": 3
        },
        "total_tests": 17
    }
    
    return report

if __name__ == "__main__":
    # Run comprehensive migration test suite
    print("🧪 Running Migration Validation Test Suite...")
    result = run_migration_test_suite()
    
    if result["success"]:
        print("✅ Migration validation test suite passed!")
    else:
        print("❌ Migration validation test suite failed!")
        sys.exit(1)
    
    # Generate report
    report = generate_migration_test_report()
    print(f"📊 Test report generated: {report['total_tests']} tests across {len(report['pytest_markers'])} markers")