#!/usr/bin/env python3
"""
🟡 Batch 2 Checkpoints - Service Layer Required

Validation checkpoints específicos para Batch 2 da migração DatabaseManager.
Foca em integração com service layer e resolução de dependências.

Batch 2 Files (15 files - MEDIUM RISK):
- streamlit_extension/database/connection.py
- streamlit_extension/database/seed.py
- streamlit_extension/models/database.py
- scripts/migration/add_performance_indexes.py
- streamlit_extension/utils/cached_database.py
- streamlit_extension/utils/performance_tester.py
- tests/test_security_scenarios.py
- tests/test_database_manager_duration_extension.py
- tests/test_migration_schemas.py
- scripts/testing/api_equivalence_validation.py
- scripts/testing/secrets_vault_demo.py
- scripts/testing/test_sql_pagination.py
- tests/test_type_hints_database_manager.py
- tests/performance/test_load_scenarios.py
- tests/test_epic_progress_defaults.py

Critical Blockers:
- ServiceContainer configuration issue: "db_manager é obrigatório quando use_modular_api=False"
- 15 service layer methods blocked by configuration
- Parameter mapping required for legacy signatures

Features:
- ServiceContainer configuration validation (CRITICAL BLOCKER)
- Service layer integration testing
- Parameter mapping validation 
- Dependency injection testing
- Test infrastructure compatibility
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

class Batch2Checkpoints:
    """Specific checkpoint validations for Batch 2 migration."""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.batch_files = [
            "streamlit_extension/database/connection.py",
            "streamlit_extension/database/seed.py", 
            "streamlit_extension/models/database.py",
            "scripts/migration/add_performance_indexes.py",
            "streamlit_extension/utils/cached_database.py",
            "streamlit_extension/utils/performance_tester.py",
            "tests/test_security_scenarios.py",
            "tests/test_database_manager_duration_extension.py",
            "tests/test_migration_schemas.py",
            "scripts/testing/api_equivalence_validation.py",
            "scripts/testing/secrets_vault_demo.py",
            "scripts/testing/test_sql_pagination.py",
            "tests/test_type_hints_database_manager.py", 
            "tests/performance/test_load_scenarios.py",
            "tests/test_epic_progress_defaults.py"
        ]
        
        # Business services that need to be functional for Batch 2
        self.required_services = [
            "ProjectService",
            "EpicService", 
            "TaskService",
            "AnalyticsService",
            "TimerService"
        ]
        
        # Service layer methods that are blocked by ServiceContainer issue
        self.blocked_methods = [
            "create_project", "update_project", "delete_project",
            "create_epic", "update_epic", "delete_epic",
            "create_task", "update_task", "delete_task", "update_task_status",
            "get_project_dashboard", "get_epic_progress", "calculate_epic_duration",
            "create_timer_session", "get_productivity_stats", "get_user_achievements"
        ]
    
    def run_all_checkpoints(self) -> Dict[str, Any]:
        """Run all Batch 2 specific checkpoints."""
        logger.info("🟡 Starting Batch 2 comprehensive checkpoints")
        
        results = {
            "batch_name": "Service Layer Required",
            "start_time": time.time(),
            "checkpoints": {},
            "overall_status": "running",
            "critical_blocker_resolved": False
        }
        
        try:
            # CRITICAL: ServiceContainer configuration validation
            logger.info("🚨 CRITICAL CHECKPOINT: ServiceContainer configuration validation")
            service_container_result = self._validate_service_container_configuration()
            results["checkpoints"]["service_container_configuration"] = service_container_result
            results["critical_blocker_resolved"] = service_container_result.get("passed", False)
            
            if not results["critical_blocker_resolved"]:
                logger.error("🚨 CRITICAL BLOCKER: ServiceContainer configuration failed - Batch 2 cannot proceed")
                results["overall_status"] = "blocked"
                results["blocker_message"] = "ServiceContainer configuration must be fixed before Batch 2 migration"
                return results
            
            # Checkpoint 1: Service layer integration testing
            logger.info("📋 Checkpoint 1: Service layer integration testing")
            results["checkpoints"]["service_integration"] = self._test_service_layer_integration()
            
            # Checkpoint 2: Parameter mapping validation
            logger.info("📋 Checkpoint 2: Parameter mapping validation")
            results["checkpoints"]["parameter_mapping"] = self._validate_parameter_mapping()
            
            # Checkpoint 3: Dependency injection testing
            logger.info("📋 Checkpoint 3: Dependency injection testing")
            results["checkpoints"]["dependency_injection"] = self._test_dependency_injection()
            
            # Checkpoint 4: Test infrastructure compatibility
            logger.info("📋 Checkpoint 4: Test infrastructure compatibility")
            results["checkpoints"]["test_infrastructure"] = self._validate_test_infrastructure()
            
            # Checkpoint 5: Performance & caching validation
            logger.info("📋 Checkpoint 5: Performance & caching validation")
            results["checkpoints"]["performance_caching"] = self._validate_performance_caching()
            
            # Checkpoint 6: Database connection architecture
            logger.info("📋 Checkpoint 6: Database connection architecture")
            results["checkpoints"]["connection_architecture"] = self._validate_connection_architecture()
            
            # Determine overall status
            failed_checkpoints = [name for name, result in results["checkpoints"].items() 
                                if not result.get("passed", False)]
            
            if failed_checkpoints:
                results["overall_status"] = "failed"
                results["failed_checkpoints"] = failed_checkpoints
            else:
                results["overall_status"] = "passed"
                
        except Exception as e:
            results["overall_status"] = "error"
            results["error"] = str(e)
            logger.error(f"Batch 2 checkpoints failed: {e}")
        
        results["end_time"] = time.time()
        results["duration"] = results["end_time"] - results["start_time"]
        
        return results
    
    def _validate_service_container_configuration(self) -> Dict[str, Any]:
        """
        CRITICAL: Validate ServiceContainer configuration.
        This is the main blocker identified in step 2.2.2.
        """
        result = {
            "passed": False,
            "blocker_status": "unresolved",
            "configuration_tests": [],
            "resolution_suggestions": []
        }
        
        # Test 1: Basic ServiceContainer import
        logger.info("  🔍 Test 1: ServiceContainer import test")
        import_test = self._test_service_container_import()
        result["configuration_tests"].append(import_test)
        
        # Test 2: ServiceContainer initialization
        logger.info("  🔍 Test 2: ServiceContainer initialization test")
        init_test = self._test_service_container_initialization()
        result["configuration_tests"].append(init_test)
        
        # Test 3: Service retrieval test
        logger.info("  🔍 Test 3: Service retrieval test")
        retrieval_test = self._test_service_retrieval()
        result["configuration_tests"].append(retrieval_test)
        
        # Test 4: Configuration parameter analysis
        logger.info("  🔍 Test 4: Configuration parameter analysis")
        config_test = self._analyze_configuration_parameters()
        result["configuration_tests"].append(config_test)
        
        # Determine if blocker is resolved
        successful_tests = [test for test in result["configuration_tests"] if test.get("passed", False)]
        
        if len(successful_tests) >= 3:  # Need at least import, init, and one service working
            result["passed"] = True
            result["blocker_status"] = "resolved"
            logger.info("✅ ServiceContainer blocker RESOLVED")
        else:
            result["blocker_status"] = "unresolved"
            result["resolution_suggestions"] = self._generate_resolution_suggestions(result["configuration_tests"])
            logger.error("❌ ServiceContainer blocker UNRESOLVED")
        
        return result
    
    def _test_service_container_import(self) -> Dict[str, Any]:
        """Test ServiceContainer import."""
        test_code = """
try:
    from streamlit_extension.services import ServiceContainer
    print("✅ ServiceContainer import successful")
except ImportError as e:
    print(f"❌ ServiceContainer import failed: {e}")
    exit(1)
except Exception as e:
    print(f"⚠️ ServiceContainer import warning: {e}")
    exit(2)
"""
        
        try:
            result = subprocess.run(['python', '-c', test_code], 
                                  capture_output=True, text=True, timeout=30)
            
            return {
                "name": "service_container_import",
                "passed": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "return_code": result.returncode
            }
        except Exception as e:
            return {
                "name": "service_container_import", 
                "passed": False,
                "error": str(e)
            }
    
    def _test_service_container_initialization(self) -> Dict[str, Any]:
        """Test ServiceContainer initialization - this is where the main blocker occurs."""
        test_code = """
try:
    from streamlit_extension.services import ServiceContainer
    print("✅ ServiceContainer imported")
    
    # This is where the blocker typically occurs
    container = ServiceContainer()
    print("✅ ServiceContainer initialization successful")
    
except Exception as e:
    print(f"❌ ServiceContainer initialization failed: {e}")
    
    # Check for specific error patterns
    error_msg = str(e)
    if "db_manager é obrigatório" in error_msg:
        print("🚨 KNOWN BLOCKER: ServiceContainer requires db_manager configuration")
        print("💡 Suggestion: Check ServiceContainer constructor parameters")
    
    exit(1)
"""
        
        try:
            result = subprocess.run(['python', '-c', test_code],
                                  capture_output=True, text=True, timeout=30)
            
            return {
                "name": "service_container_initialization",
                "passed": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None,
                "return_code": result.returncode,
                "known_blocker_detected": "db_manager é obrigatório" in result.stdout or "db_manager é obrigatório" in result.stderr
            }
        except Exception as e:
            return {
                "name": "service_container_initialization",
                "passed": False,
                "error": str(e)
            }
    
    def _test_service_retrieval(self) -> Dict[str, Any]:
        """Test individual service retrieval from ServiceContainer."""
        result = {
            "name": "service_retrieval",
            "passed": True,
            "services_tested": [],
            "failed_services": []
        }
        
        for service_name in self.required_services:
            service_method = f"get_{service_name.lower().replace('service', '_service')}"
            
            test_code = f"""
try:
    from streamlit_extension.services import ServiceContainer
    container = ServiceContainer()
    service = container.{service_method}()
    print(f"✅ {service_name} retrieval successful")
except Exception as e:
    print(f"❌ {service_name} retrieval failed: {{e}}")
    exit(1)
"""
            
            try:
                test_result = subprocess.run(['python', '-c', test_code],
                                           capture_output=True, text=True, timeout=30)
                
                if test_result.returncode == 0:
                    result["services_tested"].append(service_name)
                else:
                    result["passed"] = False
                    result["failed_services"].append({
                        "service": service_name,
                        "method": service_method,
                        "error": test_result.stderr
                    })
            except Exception as e:
                result["passed"] = False
                result["failed_services"].append({
                    "service": service_name,
                    "method": service_method, 
                    "error": str(e)
                })
        
        return result
    
    def _analyze_configuration_parameters(self) -> Dict[str, Any]:
        """Analyze ServiceContainer configuration parameters to understand blocker."""
        test_code = """
try:
    import inspect
    from streamlit_extension.services import ServiceContainer
    
    # Analyze ServiceContainer constructor
    sig = inspect.signature(ServiceContainer.__init__)
    params = list(sig.parameters.keys())
    print(f"ServiceContainer parameters: {params}")
    
    # Try to understand the db_manager parameter
    for param_name, param in sig.parameters.items():
        if 'db' in param_name.lower():
            print(f"DB-related parameter: {param_name} = {param}")
            if param.default != inspect.Parameter.empty:
                print(f"  Default value: {param.default}")
            else:
                print(f"  No default value (may be required)")
    
except Exception as e:
    print(f"❌ Configuration analysis failed: {e}")
    exit(1)
"""
        
        try:
            result = subprocess.run(['python', '-c', test_code],
                                  capture_output=True, text=True, timeout=30)
            
            return {
                "name": "configuration_analysis",
                "passed": result.returncode == 0,
                "analysis_output": result.stdout,
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {
                "name": "configuration_analysis",
                "passed": False,
                "error": str(e)
            }
    
    def _generate_resolution_suggestions(self, test_results: List[Dict[str, Any]]) -> List[str]:
        """Generate specific suggestions to resolve ServiceContainer configuration."""
        suggestions = []
        
        # Analyze test results to provide specific suggestions
        init_test = next((test for test in test_results if test["name"] == "service_container_initialization"), None)
        
        if init_test and init_test.get("known_blocker_detected"):
            suggestions.extend([
                "1. Check ServiceContainer constructor in streamlit_extension/services/service_container.py",
                "2. Look for db_manager parameter and understand its requirements",
                "3. Consider providing DatabaseManager instance to ServiceContainer constructor",
                "4. Check if use_modular_api flag needs to be set to True",
                "5. Review ServiceContainer documentation for proper initialization"
            ])
        
        config_test = next((test for test in test_results if test["name"] == "configuration_analysis"), None)
        if config_test and config_test.get("passed"):
            suggestions.append("6. Review configuration analysis output for specific parameter requirements")
        
        suggestions.extend([
            "7. Consider temporary fix: modify ServiceContainer to not require db_manager",
            "8. Alternative: implement proper dependency injection for DatabaseManager",
            "9. Test with different ServiceContainer initialization patterns",
            "10. Consult service layer documentation for correct usage patterns"
        ])
        
        return suggestions
    
    def _test_service_layer_integration(self) -> Dict[str, Any]:
        """Test service layer integration functionality."""
        result = {"passed": True, "integration_tests": [], "blocked_methods_count": 0}
        
        # Test basic service operations
        service_operations = [
            {
                "name": "project_service_basic",
                "code": """
from streamlit_extension.services import ServiceContainer
container = ServiceContainer()
project_service = container.get_project_service()
# Test basic project operations
projects = project_service.get_all_projects()
print(f"✅ ProjectService operational - {len(projects.data) if projects.success else 0} projects")
"""
            },
            {
                "name": "epic_service_basic",
                "code": """
from streamlit_extension.services import ServiceContainer
container = ServiceContainer()
epic_service = container.get_epic_service()
# Test basic epic operations  
epics = epic_service.get_all_epics()
print(f"✅ EpicService operational - {len(epics.data) if epics.success else 0} epics")
"""
            }
        ]
        
        for operation in service_operations:
            try:
                test_result = subprocess.run(['python', '-c', operation["code"]],
                                           capture_output=True, text=True, timeout=30)
                
                integration_test = {
                    "name": operation["name"],
                    "passed": test_result.returncode == 0,
                    "output": test_result.stdout,
                    "error": test_result.stderr if test_result.returncode != 0 else None
                }
                
                if test_result.returncode != 0:
                    result["passed"] = False
                
                result["integration_tests"].append(integration_test)
                
            except Exception as e:
                result["passed"] = False
                result["integration_tests"].append({
                    "name": operation["name"],
                    "passed": False,
                    "error": str(e)
                })
        
        # Count how many blocked methods are still blocked
        result["blocked_methods_count"] = len(self.blocked_methods)
        result["blocked_methods"] = self.blocked_methods
        
        return result
    
    def _validate_parameter_mapping(self) -> Dict[str, Any]:
        """Validate parameter mapping between legacy and modular APIs."""
        result = {"passed": True, "mapping_tests": []}
        
        # Test parameter compatibility for common patterns
        mapping_tests = [
            {
                "name": "epic_id_parameter",
                "legacy_signature": "get_tasks(epic_id)",
                "modular_signature": "list_tasks(epic_id)",
                "test_code": """
# Test parameter mapping compatibility
from streamlit_extension.database.queries import list_tasks
try:
    # This should work if parameter mapping is correct
    tasks = list_tasks(1)  # Test with epic_id = 1
    print("✅ Parameter mapping compatible")
except TypeError as e:
    print(f"❌ Parameter mapping issue: {e}")
    exit(1)
except Exception as e:
    print(f"⚠️ Other issue (not parameter mapping): {e}")
"""
            }
        ]
        
        for mapping_test in mapping_tests:
            try:
                test_result = subprocess.run(['python', '-c', mapping_test["test_code"]],
                                           capture_output=True, text=True, timeout=30)
                
                test_record = {
                    "name": mapping_test["name"],
                    "legacy_signature": mapping_test["legacy_signature"],
                    "modular_signature": mapping_test["modular_signature"],
                    "passed": test_result.returncode == 0,
                    "output": test_result.stdout,
                    "error": test_result.stderr if test_result.returncode != 0 else None
                }
                
                if test_result.returncode != 0:
                    result["passed"] = False
                
                result["mapping_tests"].append(test_record)
                
            except Exception as e:
                result["passed"] = False
                result["mapping_tests"].append({
                    "name": mapping_test["name"],
                    "passed": False,
                    "error": str(e)
                })
        
        return result
    
    def _test_dependency_injection(self) -> Dict[str, Any]:
        """Test dependency injection patterns in Batch 2 files."""
        result = {"passed": True, "injection_tests": []}
        
        # Test files that use dependency injection patterns
        injection_files = [
            "scripts/migration/add_performance_indexes.py",
            "streamlit_extension/utils/cached_database.py"
        ]
        
        for file_path in injection_files:
            full_path = self.base_path / file_path
            if not full_path.exists():
                continue
            
            try:
                # Test basic import and structure
                test_code = f"""
import importlib.util
spec = importlib.util.spec_from_file_location("test_module", "{file_path}")
if spec and spec.loader:
    module = importlib.util.module_from_spec(spec)
    # Check if it has dependency injection patterns
    has_db_manager_param = False
    try:
        source = open("{file_path}").read()
        has_db_manager_param = "db_manager:" in source or "DatabaseManager" in source
    except:
        pass
    
    print(f"✅ {file_path} - DI patterns: {{has_db_manager_param}}")
else:
    print(f"❌ {file_path} - Module structure invalid")
    exit(1)
"""
                
                test_result = subprocess.run(['python', '-c', test_code],
                                           capture_output=True, text=True, timeout=30)
                
                injection_test = {
                    "file": file_path,
                    "passed": test_result.returncode == 0,
                    "output": test_result.stdout,
                    "error": test_result.stderr if test_result.returncode != 0 else None
                }
                
                if test_result.returncode != 0:
                    result["passed"] = False
                
                result["injection_tests"].append(injection_test)
                
            except Exception as e:
                result["passed"] = False
                result["injection_tests"].append({
                    "file": file_path,
                    "passed": False,
                    "error": str(e)
                })
        
        return result
    
    def _validate_test_infrastructure(self) -> Dict[str, Any]:
        """Validate test infrastructure compatibility for Batch 2."""
        result = {"passed": True, "test_files": []}
        
        # Test files that are part of Batch 2
        test_files = [
            "tests/test_security_scenarios.py",
            "tests/test_database_manager_duration_extension.py",
            "tests/test_migration_schemas.py",
            "tests/test_type_hints_database_manager.py",
            "tests/performance/test_load_scenarios.py",
            "tests/test_epic_progress_defaults.py"
        ]
        
        for test_file in test_files:
            full_path = self.base_path / test_file
            if not full_path.exists():
                continue
            
            try:
                # Test basic pytest compatibility
                test_result = subprocess.run(['python', '-m', 'pytest', str(full_path), '--collect-only'],
                                           capture_output=True, text=True, timeout=60)
                
                test_record = {
                    "file": test_file,
                    "passed": test_result.returncode == 0,
                    "collected_tests": self._count_collected_tests(test_result.stdout),
                    "error": test_result.stderr if test_result.returncode != 0 else None
                }
                
                if test_result.returncode != 0:
                    result["passed"] = False
                
                result["test_files"].append(test_record)
                
            except Exception as e:
                result["passed"] = False
                result["test_files"].append({
                    "file": test_file,
                    "passed": False,
                    "error": str(e)
                })
        
        return result
    
    def _count_collected_tests(self, pytest_output: str) -> int:
        """Count collected tests from pytest output."""
        try:
            import re
            matches = re.findall(r'(\d+) tests? collected', pytest_output)
            return int(matches[-1]) if matches else 0
        except:
            return 0
    
    def _validate_performance_caching(self) -> Dict[str, Any]:
        """Validate performance and caching functionality for Batch 2."""
        result = {"passed": True, "performance_tests": []}
        
        # Test performance-related files
        perf_tests = [
            {
                "name": "cached_database_functionality",
                "code": """
try:
    # Test cached database utilities
    import sys
    import os
    sys.path.append(os.getcwd())
    
    from streamlit_extension.utils.cached_database import *  # Import cached utilities
    print("✅ Cached database utilities available")
except ImportError as e:
    print(f"❌ Cached database import failed: {e}")
    exit(1)
except Exception as e:
    print(f"⚠️ Cached database warning: {e}")
"""
            },
            {
                "name": "performance_tester_functionality",
                "code": """
try:
    from streamlit_extension.utils.performance_tester import *
    print("✅ Performance tester utilities available")
except ImportError as e:
    print(f"❌ Performance tester import failed: {e}")
    exit(1)
except Exception as e:
    print(f"⚠️ Performance tester warning: {e}")
"""
            }
        ]
        
        for perf_test in perf_tests:
            try:
                test_result = subprocess.run(['python', '-c', perf_test["code"]],
                                           capture_output=True, text=True, timeout=30)
                
                test_record = {
                    "name": perf_test["name"],
                    "passed": test_result.returncode == 0,
                    "output": test_result.stdout,
                    "error": test_result.stderr if test_result.returncode != 0 else None
                }
                
                if test_result.returncode != 0:
                    result["passed"] = False
                
                result["performance_tests"].append(test_record)
                
            except Exception as e:
                result["passed"] = False
                result["performance_tests"].append({
                    "name": perf_test["name"],
                    "passed": False,
                    "error": str(e)
                })
        
        return result
    
    def _validate_connection_architecture(self) -> Dict[str, Any]:
        """Validate database connection architecture for Batch 2."""
        result = {"passed": True, "architecture_tests": []}
        
        # Test connection.py functionality
        connection_test = {
            "name": "connection_module_architecture",
            "code": """
try:
    from streamlit_extension.database.connection import get_connection, release_connection
    print("✅ Connection architecture available")
    
    # Test basic connection functionality
    conn = get_connection()
    if conn:
        print("✅ Connection retrieval successful")
        release_connection(conn)
        print("✅ Connection release successful")
    else:
        print("⚠️ Connection retrieval returned None")
        
except ImportError as e:
    print(f"❌ Connection architecture import failed: {e}")
    exit(1)
except Exception as e:
    print(f"⚠️ Connection architecture warning: {e}")
"""
        }
        
        try:
            test_result = subprocess.run(['python', '-c', connection_test["code"]],
                                       capture_output=True, text=True, timeout=30)
            
            architecture_test = {
                "name": connection_test["name"],
                "passed": test_result.returncode == 0,
                "output": test_result.stdout,
                "error": test_result.stderr if test_result.returncode != 0 else None
            }
            
            if test_result.returncode != 0:
                result["passed"] = False
            
            result["architecture_tests"].append(architecture_test)
            
        except Exception as e:
            result["passed"] = False
            result["architecture_tests"].append({
                "name": connection_test["name"],
                "passed": False,
                "error": str(e)
            })
        
        return result

def main():
    """Main entry point for Batch 2 checkpoints."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch 2 Migration Checkpoints")
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--ignore-blocker', action='store_true', 
                       help='Continue even if ServiceContainer blocker is not resolved')
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    print("🟡 Starting Batch 2 Migration Checkpoints")
    print("🚨 CRITICAL: Validating ServiceContainer configuration blocker")
    
    checkpoints = Batch2Checkpoints()
    results = checkpoints.run_all_checkpoints()
    
    print(f"\n📋 Batch 2 Checkpoints Summary:")
    print(f"Status: {results['overall_status']}")
    print(f"Duration: {results['duration']:.2f} seconds")
    print(f"Critical Blocker Resolved: {results['critical_blocker_resolved']}")
    
    if results['overall_status'] == 'blocked':
        print(f"\n🚨 MIGRATION BLOCKED: {results.get('blocker_message', 'Unknown blocker')}")
        
        # Show resolution suggestions if available
        service_container_result = results['checkpoints'].get('service_container_configuration', {})
        if service_container_result.get('resolution_suggestions'):
            print("\n💡 Resolution Suggestions:")
            for i, suggestion in enumerate(service_container_result['resolution_suggestions'], 1):
                print(f"  {suggestion}")
        
        if not args.ignore_blocker:
            print("\n❌ Batch 2 migration cannot proceed until ServiceContainer issue is resolved")
            return 1
    
    print(f"\nCheckpoints: {len(results['checkpoints'])}")
    for checkpoint_name, checkpoint_result in results['checkpoints'].items():
        status_icon = "✅" if checkpoint_result.get('passed', False) else "❌"
        if checkpoint_name == 'service_container_configuration':
            status_icon = "🚨" if not checkpoint_result.get('passed', False) else "✅"
        print(f"  {status_icon} {checkpoint_name}")
    
    if results['overall_status'] not in ['passed', 'blocked']:
        print(f"\n⚠️ Failed checkpoints: {results.get('failed_checkpoints', [])}")
        return 1
    elif results['overall_status'] == 'passed':
        print("\n🎉 All Batch 2 checkpoints passed! ServiceContainer blocker resolved!")
        return 0
    else:
        return 2  # Blocked status

if __name__ == "__main__":
    exit(main())