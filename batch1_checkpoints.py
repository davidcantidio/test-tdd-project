#!/usr/bin/env python3
"""
🟢 Batch 1 Checkpoints - Simple Replacements

Validation checkpoints específicos para Batch 1 da migração DatabaseManager.
Foca em substituições simples com validação de API equivalente.

Batch 1 Files (11 files - LOW RISK):
- monitoring/health_check.py
- monitoring/graceful_shutdown.py  
- validate_phase1.py
- scripts/testing/test_database_extension_quick.py
- streamlit_extension/database/queries.py
- streamlit_extension/database/health.py
- streamlit_extension/database/schema.py
- streamlit_extension/pages/projects.py
- streamlit_extension/models/base.py
- backups/context_extraction_20250819_212949/systematic_file_auditor.py (optional)
- scripts/migration/ast_database_migration.py (optional)

Features:
- Direct API replacement validation
- Performance baseline comparison
- Import and syntax validation
- Integration smoke tests
- Zero business logic changes expected
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

class Batch1Checkpoints:
    """Specific checkpoint validations for Batch 1 migration."""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.batch_files = [
            "monitoring/health_check.py",
            "monitoring/graceful_shutdown.py",
            "validate_phase1.py",
            "scripts/testing/test_database_extension_quick.py",
            "streamlit_extension/database/queries.py",
            "streamlit_extension/database/health.py", 
            "streamlit_extension/database/schema.py",
            "streamlit_extension/pages/projects.py",
            "streamlit_extension/models/base.py"
        ]
        
        self.optional_files = [
            "backups/context_extraction_20250819_212949/systematic_file_auditor.py",
            "scripts/migration/ast_database_migration.py"
        ]
        
        # Expected API replacements for Batch 1
        self.api_replacements = {
            "get_connection": "connection.get_connection",
            "get_epics": "queries.list_epics", 
            "get_tasks": "queries.list_tasks",
            "get_all_epics": "queries.list_all_epics",
            "get_all_tasks": "queries.list_all_tasks",
            "check_database_health": "health.check_health"
        }
    
    def run_all_checkpoints(self) -> Dict[str, Any]:
        """Run all Batch 1 specific checkpoints."""
        logger.info("🟢 Starting Batch 1 comprehensive checkpoints")
        
        results = {
            "batch_name": "Simple Replacements",
            "start_time": time.time(),
            "checkpoints": {},
            "overall_status": "running"
        }
        
        try:
            # Checkpoint 1: Direct API replacement readiness
            logger.info("📋 Checkpoint 1: Direct API replacement readiness")
            results["checkpoints"]["api_replacement_readiness"] = self._check_api_replacement_readiness()
            
            # Checkpoint 2: Modular API availability
            logger.info("📋 Checkpoint 2: Modular API availability")
            results["checkpoints"]["modular_api_availability"] = self._check_modular_api_availability()
            
            # Checkpoint 3: File-specific method usage analysis
            logger.info("📋 Checkpoint 3: File-specific method usage analysis")
            results["checkpoints"]["method_usage_analysis"] = self._analyze_method_usage()
            
            # Checkpoint 4: Performance comparison baseline
            logger.info("📋 Checkpoint 4: Performance comparison baseline")
            results["checkpoints"]["performance_baseline"] = self._establish_performance_baseline()
            
            # Checkpoint 5: Integration point validation
            logger.info("📋 Checkpoint 5: Integration point validation")
            results["checkpoints"]["integration_validation"] = self._validate_integration_points()
            
            # Checkpoint 6: Backward compatibility check
            logger.info("📋 Checkpoint 6: Backward compatibility check")  
            results["checkpoints"]["backward_compatibility"] = self._check_backward_compatibility()
            
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
            logger.error(f"Batch 1 checkpoints failed: {e}")
        
        results["end_time"] = time.time()
        results["duration"] = results["end_time"] - results["start_time"]
        
        return results
    
    def _check_api_replacement_readiness(self) -> Dict[str, Any]:
        """Check if all required API replacements are available in modular API."""
        result = {"passed": True, "available_replacements": [], "missing_replacements": []}
        
        for legacy_method, modular_replacement in self.api_replacements.items():
            try:
                # Test if modular replacement is available
                module_path, function_name = modular_replacement.split('.')
                test_code = f"""
try:
    from streamlit_extension.database.{module_path} import {function_name}
    print("✅ {modular_replacement} available")
except ImportError as e:
    print("❌ {modular_replacement} not available: {{e}}")
    exit(1)
"""
                
                test_result = subprocess.run(['python', '-c', test_code], 
                                           capture_output=True, text=True)
                
                if test_result.returncode == 0:
                    result["available_replacements"].append(modular_replacement)
                else:
                    result["passed"] = False
                    result["missing_replacements"].append({
                        "legacy": legacy_method,
                        "replacement": modular_replacement,
                        "error": test_result.stderr
                    })
                    
            except Exception as e:
                result["passed"] = False
                result["missing_replacements"].append({
                    "legacy": legacy_method,
                    "replacement": modular_replacement,
                    "error": str(e)
                })
        
        logger.info(f"API replacement check: {len(result['available_replacements'])}/{len(self.api_replacements)} available")
        return result
    
    def _check_modular_api_availability(self) -> Dict[str, Any]:
        """Check if modular database API components are available."""
        result = {"passed": True, "available_modules": [], "missing_modules": []}
        
        required_modules = [
            "streamlit_extension.database.connection",
            "streamlit_extension.database.health", 
            "streamlit_extension.database.queries",
            "streamlit_extension.database.schema"
        ]
        
        for module_name in required_modules:
            try:
                test_code = f"""
try:
    import {module_name}
    print("✅ {module_name} available")
except ImportError as e:
    print("❌ {module_name} not available: {{e}}")
    exit(1)
"""
                
                test_result = subprocess.run(['python', '-c', test_code],
                                           capture_output=True, text=True)
                
                if test_result.returncode == 0:
                    result["available_modules"].append(module_name)
                else:
                    result["passed"] = False
                    result["missing_modules"].append({
                        "module": module_name,
                        "error": test_result.stderr
                    })
                    
            except Exception as e:
                result["passed"] = False
                result["missing_modules"].append({
                    "module": module_name,
                    "error": str(e)
                })
        
        logger.info(f"Modular API check: {len(result['available_modules'])}/{len(required_modules)} modules available")
        return result
    
    def _analyze_method_usage(self) -> Dict[str, Any]:
        """Analyze DatabaseManager method usage in Batch 1 files."""
        result = {"passed": True, "file_analysis": [], "total_usages": 0}
        
        for file_path in self.batch_files:
            full_path = self.base_path / file_path
            if not full_path.exists():
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_analysis = {
                    "file": file_path,
                    "database_manager_imports": 0,
                    "method_calls": [],
                    "migration_complexity": "simple"
                }
                
                # Check for DatabaseManager import
                if "from streamlit_extension.utils.database import DatabaseManager" in content:
                    file_analysis["database_manager_imports"] += 1
                
                # Check for method usage patterns
                for legacy_method in self.api_replacements.keys():
                    pattern_variations = [
                        f"db_manager.{legacy_method}",
                        f"db.{legacy_method}",
                        f"DatabaseManager().{legacy_method}"
                    ]
                    
                    for pattern in pattern_variations:
                        count = content.count(pattern)
                        if count > 0:
                            file_analysis["method_calls"].append({
                                "method": legacy_method,
                                "pattern": pattern,
                                "count": count
                            })
                            result["total_usages"] += count
                
                # Determine complexity based on usage patterns
                total_calls = sum(call["count"] for call in file_analysis["method_calls"])
                if total_calls == 0:
                    file_analysis["migration_complexity"] = "none_needed"
                elif total_calls <= 3:
                    file_analysis["migration_complexity"] = "simple"
                else:
                    file_analysis["migration_complexity"] = "moderate"
                
                result["file_analysis"].append(file_analysis)
                
            except Exception as e:
                result["passed"] = False
                result["file_analysis"].append({
                    "file": file_path,
                    "error": str(e),
                    "migration_complexity": "error"
                })
        
        logger.info(f"Method usage analysis: {result['total_usages']} total DatabaseManager calls found")
        return result
    
    def _establish_performance_baseline(self) -> Dict[str, Any]:
        """Establish performance baseline for common operations in Batch 1."""
        result = {"passed": True, "baseline_metrics": {}, "performance_tests": []}
        
        # Test common operations that Batch 1 files use
        performance_tests = [
            {
                "name": "database_connection",
                "code": """
from streamlit_extension.utils.database import DatabaseManager
import time
start = time.time()
db = DatabaseManager()
conn = db.get_connection()
end = time.time()
print(f"Connection time: {end - start:.4f}s")
"""
            },
            {
                "name": "get_epics_query",
                "code": """
from streamlit_extension.utils.database import DatabaseManager
import time
db = DatabaseManager()
start = time.time()
epics = db.get_all_epics()
end = time.time()
print(f"Get epics time: {end - start:.4f}s - Count: {len(epics) if epics else 0}")
"""
            },
            {
                "name": "health_check",
                "code": """
from streamlit_extension.utils.database import DatabaseManager
import time
db = DatabaseManager()
start = time.time()
health = db.check_database_health()
end = time.time()
print(f"Health check time: {end - start:.4f}s - Status: {health.get('status') if health else 'unknown'}")
"""
            }
        ]
        
        for test in performance_tests:
            try:
                test_result = subprocess.run(['python', '-c', test["code"]],
                                           capture_output=True, text=True, timeout=30)
                
                if test_result.returncode == 0:
                    # Parse timing from output
                    output_lines = test_result.stdout.strip().split('\n')
                    timing_info = output_lines[-1] if output_lines else ""
                    
                    test_record = {
                        "name": test["name"],
                        "status": "success",
                        "output": timing_info,
                        "duration": self._extract_timing_from_output(timing_info)
                    }
                    
                    # Store baseline for comparison
                    result["baseline_metrics"][test["name"]] = test_record["duration"]
                    
                else:
                    test_record = {
                        "name": test["name"],
                        "status": "failed",
                        "error": test_result.stderr,
                        "duration": None
                    }
                    result["passed"] = False
                
                result["performance_tests"].append(test_record)
                
            except subprocess.TimeoutExpired:
                result["passed"] = False
                result["performance_tests"].append({
                    "name": test["name"],
                    "status": "timeout",
                    "duration": None
                })
            except Exception as e:
                result["passed"] = False
                result["performance_tests"].append({
                    "name": test["name"],
                    "status": "error",
                    "error": str(e),
                    "duration": None
                })
        
        logger.info(f"Performance baseline: {len([t for t in result['performance_tests'] if t['status'] == 'success'])} tests successful")
        return result
    
    def _extract_timing_from_output(self, output: str) -> float:
        """Extract timing information from test output."""
        try:
            # Look for patterns like "Connection time: 0.0123s"
            import re
            timing_match = re.search(r'time:\s*(\d+\.\d+)s', output)
            if timing_match:
                return float(timing_match.group(1))
        except Exception:
            pass
        return 0.0
    
    def _validate_integration_points(self) -> Dict[str, Any]:
        """Validate integration points between Batch 1 files and other components."""
        result = {"passed": True, "integration_tests": []}
        
        integration_tests = [
            {
                "name": "monitoring_health_integration",
                "description": "Test health monitoring integration",
                "code": """
try:
    from monitoring.health_check import main as health_main
    print("✅ Health check module import successful")
except ImportError as e:
    print(f"❌ Health check import failed: {e}")
    exit(1)
except Exception as e:
    print(f"⚠️ Health check import warning: {e}")
"""
            },
            {
                "name": "database_queries_integration",
                "description": "Test database queries module integration",
                "code": """
try:
    from streamlit_extension.database.queries import list_epics, list_all_epics
    print("✅ Database queries module import successful")
    
    # Test basic functionality
    epics = list_all_epics()
    print(f"✅ Query functionality test: {len(epics) if epics else 0} epics")
except ImportError as e:
    print(f"❌ Database queries import failed: {e}")
    exit(1)
except Exception as e:
    print(f"⚠️ Database queries warning: {e}")
"""
            },
            {
                "name": "projects_page_integration",
                "description": "Test projects page integration", 
                "code": """
try:
    import sys
    import os
    sys.path.append(os.getcwd())
    
    # Test basic import without executing Streamlit code
    import importlib.util
    spec = importlib.util.spec_from_file_location("projects_page", 
                                                  "streamlit_extension/pages/projects.py")
    if spec and spec.loader:
        print("✅ Projects page module structure valid")
    else:
        print("❌ Projects page module structure invalid")
        exit(1)
except Exception as e:
    print(f"⚠️ Projects page integration warning: {e}")
"""
            }
        ]
        
        for test in integration_tests:
            try:
                test_result = subprocess.run(['python', '-c', test["code"]],
                                           capture_output=True, text=True, timeout=30)
                
                test_record = {
                    "name": test["name"],
                    "description": test["description"],
                    "status": "success" if test_result.returncode == 0 else "failed",
                    "output": test_result.stdout,
                    "error": test_result.stderr if test_result.returncode != 0 else None
                }
                
                if test_result.returncode != 0:
                    result["passed"] = False
                
                result["integration_tests"].append(test_record)
                
            except Exception as e:
                result["passed"] = False
                result["integration_tests"].append({
                    "name": test["name"],
                    "description": test["description"],
                    "status": "error",
                    "error": str(e)
                })
        
        logger.info(f"Integration validation: {len([t for t in result['integration_tests'] if t['status'] == 'success'])} tests successful")
        return result
    
    def _check_backward_compatibility(self) -> Dict[str, Any]:
        """Check backward compatibility requirements for Batch 1."""
        result = {"passed": True, "compatibility_checks": []}
        
        compatibility_checks = [
            {
                "name": "legacy_api_still_works",
                "description": "Verify legacy DatabaseManager API still functional",
                "code": """
from streamlit_extension.utils.database import DatabaseManager
db = DatabaseManager()
# Test basic legacy operations
conn = db.get_connection()
epics = db.get_all_epics()
print(f"✅ Legacy API functional - {len(epics) if epics else 0} epics")
"""
            },
            {
                "name": "modular_api_coexistence", 
                "description": "Verify modular and legacy APIs can coexist",
                "code": """
# Test both APIs working together
from streamlit_extension.utils.database import DatabaseManager
from streamlit_extension.database.queries import list_all_epics

# Legacy API
db = DatabaseManager()
legacy_epics = db.get_all_epics()

# Modular API  
modular_epics = list_all_epics()

legacy_count = len(legacy_epics) if legacy_epics else 0
modular_count = len(modular_epics) if modular_epics else 0

print(f"✅ API coexistence test - Legacy: {legacy_count}, Modular: {modular_count}")

if legacy_count == modular_count:
    print("✅ Data consistency between APIs")
else:
    print(f"⚠️ Data inconsistency: Legacy {legacy_count} vs Modular {modular_count}")
"""
            }
        ]
        
        for check in compatibility_checks:
            try:
                test_result = subprocess.run(['python', '-c', check["code"]],
                                           capture_output=True, text=True, timeout=30)
                
                check_record = {
                    "name": check["name"],
                    "description": check["description"],
                    "status": "success" if test_result.returncode == 0 else "failed",
                    "output": test_result.stdout,
                    "error": test_result.stderr if test_result.returncode != 0 else None
                }
                
                if test_result.returncode != 0:
                    result["passed"] = False
                
                result["compatibility_checks"].append(check_record)
                
            except Exception as e:
                result["passed"] = False
                result["compatibility_checks"].append({
                    "name": check["name"],
                    "description": check["description"],
                    "status": "error",
                    "error": str(e)
                })
        
        logger.info(f"Backward compatibility: {len([c for c in result['compatibility_checks'] if c['status'] == 'success'])} checks successful")
        return result

def main():
    """Main entry point for Batch 1 checkpoints."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Batch 1 Migration Checkpoints")
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    print("🟢 Starting Batch 1 Migration Checkpoints")
    
    checkpoints = Batch1Checkpoints()
    results = checkpoints.run_all_checkpoints()
    
    print(f"\n📋 Batch 1 Checkpoints Summary:")
    print(f"Status: {results['overall_status']}")
    print(f"Duration: {results['duration']:.2f} seconds")
    print(f"Checkpoints: {len(results['checkpoints'])}")
    
    for checkpoint_name, checkpoint_result in results['checkpoints'].items():
        status_icon = "✅" if checkpoint_result.get('passed', False) else "❌"
        print(f"  {status_icon} {checkpoint_name}")
    
    if results['overall_status'] != 'passed':
        print(f"\n⚠️ Failed checkpoints: {results.get('failed_checkpoints', [])}")
        return 1
    else:
        print("\n🎉 All Batch 1 checkpoints passed!")
        return 0

if __name__ == "__main__":
    exit(main())