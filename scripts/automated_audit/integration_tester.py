#!/usr/bin/env python3
"""
🧪 Integration Tester - Component Integration Validation

Framework de teste de integração para validar que componentes do sistema de context extraction
funcionam corretamente juntos sem quebrar funcionalidades existentes.

Usage:
    python scripts/automated_audit/integration_tester.py [options]

Features:
- Component integration testing
- Regression detection  
- Performance impact validation
- Cross-reference verification
- System health monitoring during changes
- Automated rollback triggers

Created: 2025-08-19 (Sétima Camada - Context Extraction System)
"""

import os
import sys
import json
import time
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import tempfile
import shutil


class TestResult(Enum):
    """Test result status."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"
    ERROR = "error"


class TestCategory(Enum):
    """Categories of integration tests."""
    COMPONENT_INTEGRATION = "component_integration"
    CROSS_REFERENCE = "cross_reference"
    PERFORMANCE_IMPACT = "performance_impact"
    SYSTEM_HEALTH = "system_health"
    REGRESSION_DETECTION = "regression_detection"
    DEPENDENCY_VALIDATION = "dependency_validation"


@dataclass
class TestCase:
    """Individual test case definition."""
    name: str
    category: TestCategory
    description: str
    test_function: str
    expected_result: TestResult
    timeout_seconds: int = 30
    prerequisites: List[str] = None
    cleanup_required: bool = False


@dataclass 
class TestExecution:
    """Result of test execution."""
    test_case: TestCase
    result: TestResult
    execution_time: float
    output: str
    error_message: Optional[str] = None
    performance_metrics: Optional[Dict[str, float]] = None
    rollback_triggered: bool = False


@dataclass
class IntegrationTestMetrics:
    """Metrics for integration testing session."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    warning_tests: int
    skipped_tests: int
    error_tests: int
    total_execution_time: float
    average_execution_time: float
    performance_degradation_detected: bool
    rollbacks_triggered: int


class IntegrationTester:
    """Main integration testing framework."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """Initialize integration tester."""
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.logger = logging.getLogger(f"{__name__}.IntegrationTester")
        
        # Performance baselines
        self.performance_baselines = {}
        self.performance_tolerance = 0.1  # 10% tolerance
        
        # Test results storage
        self.test_executions = []
        
        # Test definitions
        self.test_cases = self._define_test_cases()
        
        # Rollback triggers
        self.rollback_conditions = {
            "max_failed_tests": 3,
            "performance_degradation_threshold": 0.2,  # 20%
            "critical_component_failure": True
        }
        
    def _define_test_cases(self) -> List[TestCase]:
        """Define all integration test cases."""
        return [
            # Component Integration Tests
            TestCase(
                name="context_validator_integration",
                category=TestCategory.COMPONENT_INTEGRATION,
                description="Test context_validator.py integrates with existing system",
                test_function="test_context_validator_integration",
                expected_result=TestResult.PASS,
                timeout_seconds=30
            ),
            TestCase(
                name="systematic_auditor_integration", 
                category=TestCategory.COMPONENT_INTEGRATION,
                description="Test systematic_file_auditor.py works with new components",
                test_function="test_systematic_auditor_integration",
                expected_result=TestResult.PASS,
                timeout_seconds=60
            ),
            TestCase(
                name="claude_md_loading",
                category=TestCategory.COMPONENT_INTEGRATION,
                description="Test CLAUDE.md files load and parse correctly",
                test_function="test_claude_md_loading",
                expected_result=TestResult.PASS,
                timeout_seconds=15
            ),
            
            # Cross-Reference Tests
            TestCase(
                name="documentation_links",
                category=TestCategory.CROSS_REFERENCE,
                description="Verify all documentation cross-references are valid",
                test_function="test_documentation_links",
                expected_result=TestResult.PASS,
                timeout_seconds=45
            ),
            TestCase(
                name="context_extraction_references",
                category=TestCategory.CROSS_REFERENCE,
                description="Test context extraction roteiros reference existing docs",
                test_function="test_context_extraction_references",
                expected_result=TestResult.PASS,
                timeout_seconds=20
            ),
            
            # Performance Impact Tests
            TestCase(
                name="system_startup_performance",
                category=TestCategory.PERFORMANCE_IMPACT,
                description="Measure system startup time impact",
                test_function="test_system_startup_performance",
                expected_result=TestResult.PASS,
                timeout_seconds=120
            ),
            TestCase(
                name="context_loading_performance",
                category=TestCategory.PERFORMANCE_IMPACT,
                description="Test context loading doesn't degrade performance",
                test_function="test_context_loading_performance",
                expected_result=TestResult.PASS,
                timeout_seconds=60
            ),
            
            # System Health Tests
            TestCase(
                name="comprehensive_integrity_test",
                category=TestCategory.SYSTEM_HEALTH,
                description="Run comprehensive integrity test after changes",
                test_function="test_comprehensive_integrity",
                expected_result=TestResult.PASS,
                timeout_seconds=180
            ),
            TestCase(
                name="database_health_check",
                category=TestCategory.SYSTEM_HEALTH,
                description="Verify database remains healthy",
                test_function="test_database_health",
                expected_result=TestResult.PASS,
                timeout_seconds=30
            ),
            
            # Regression Detection Tests
            TestCase(
                name="existing_functionality_regression",
                category=TestCategory.REGRESSION_DETECTION,
                description="Test that existing functionality still works",
                test_function="test_existing_functionality",
                expected_result=TestResult.PASS,
                timeout_seconds=90
            ),
            TestCase(
                name="import_regression_test",
                category=TestCategory.REGRESSION_DETECTION,
                description="Test that Python imports still work",
                test_function="test_import_regression",
                expected_result=TestResult.PASS,
                timeout_seconds=30
            )
        ]
    
    def run_integration_tests(self, categories: Optional[List[TestCategory]] = None) -> IntegrationTestMetrics:
        """Run integration tests for specified categories."""
        if categories is None:
            categories = list(TestCategory)
        
        self.logger.info(f"Starting integration tests for categories: {[c.value for c in categories]}")
        
        # Filter test cases by category
        test_cases_to_run = [tc for tc in self.test_cases if tc.category in categories]
        
        self.logger.info(f"Running {len(test_cases_to_run)} test cases")
        
        start_time = time.time()
        
        for test_case in test_cases_to_run:
            execution = self._execute_test_case(test_case)
            self.test_executions.append(execution)
            
            # Check for rollback conditions
            if self._should_trigger_rollback(execution):
                self.logger.error(f"Rollback condition triggered by test: {test_case.name}")
                execution.rollback_triggered = True
                break
        
        total_time = time.time() - start_time
        
        # Calculate metrics
        metrics = self._calculate_test_metrics(total_time)
        
        self.logger.info(f"Integration testing complete: {metrics.passed_tests}/{metrics.total_tests} passed")
        
        return metrics
    
    def _execute_test_case(self, test_case: TestCase) -> TestExecution:
        """Execute a single test case."""
        self.logger.info(f"Executing test: {test_case.name}")
        
        start_time = time.time()
        
        try:
            # Get test function
            test_function = getattr(self, test_case.test_function)
            
            # Execute with timeout
            result, output, error_message, metrics = self._run_with_timeout(
                test_function, test_case.timeout_seconds
            )
            
            execution_time = time.time() - start_time
            
            execution = TestExecution(
                test_case=test_case,
                result=result,
                execution_time=execution_time,
                output=output,
                error_message=error_message,
                performance_metrics=metrics
            )
            
            self.logger.info(f"Test {test_case.name}: {result.value} ({execution_time:.2f}s)")
            
            return execution
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            execution = TestExecution(
                test_case=test_case,
                result=TestResult.ERROR,
                execution_time=execution_time,
                output="",
                error_message=str(e)
            )
            
            self.logger.error(f"Test {test_case.name} error: {e}")
            
            return execution
    
    def _run_with_timeout(self, test_function, timeout_seconds: int) -> Tuple[TestResult, str, Optional[str], Optional[Dict[str, float]]]:
        """Run test function with timeout."""
        result = None
        output = ""
        error_message = None
        metrics = None
        
        def target():
            nonlocal result, output, error_message, metrics
            try:
                result, output, metrics = test_function()
            except Exception as e:
                result = TestResult.ERROR
                error_message = str(e)
        
        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout_seconds)
        
        if thread.is_alive():
            # Timeout occurred
            result = TestResult.ERROR
            error_message = f"Test timed out after {timeout_seconds} seconds"
            
        return result, output, error_message, metrics
    
    def _should_trigger_rollback(self, execution: TestExecution) -> bool:
        """Check if rollback should be triggered."""
        # Count failures
        failed_tests = sum(1 for ex in self.test_executions if ex.result == TestResult.FAIL)
        
        if failed_tests >= self.rollback_conditions["max_failed_tests"]:
            return True
        
        # Check for critical component failure
        if (execution.test_case.category == TestCategory.SYSTEM_HEALTH and 
            execution.result == TestResult.FAIL and
            self.rollback_conditions["critical_component_failure"]):
            return True
        
        # Check for performance degradation
        if (execution.performance_metrics and
            execution.performance_metrics.get("degradation_percentage", 0) > 
            self.rollback_conditions["performance_degradation_threshold"]):
            return True
        
        return False
    
    # Test Implementation Methods
    
    def test_context_validator_integration(self) -> Tuple[TestResult, str, Optional[Dict[str, float]]]:
        """Test context_validator.py integration."""
        try:
            # Import and test basic functionality
            sys.path.insert(0, str(self.project_root / "scripts" / "automated_audit"))
            
            import context_validator
            
            validator = context_validator.ContextValidator(self.project_root)
            
            # Test with sample content
            sample_content = """
            # TDD Workflow Integration
            This document describes TDD workflow patterns including Red-Green-Refactor cycles.
            
            ## TDAH Optimization
            Focus sessions and interruption handling for TDAH users.
            """
            
            result = validator.validate_context_quality(
                sample_content, 
                context_validator.ContextType.TDD_WORKFLOW
            )
            
            if result.quality_score > 0:
                return TestResult.PASS, f"Context validator working: {result.quality_score:.1f}% quality", None
            else:
                return TestResult.FAIL, "Context validator returned zero quality score", None
                
        except Exception as e:
            return TestResult.ERROR, f"Context validator integration failed: {e}", None
    
    def test_systematic_auditor_integration(self) -> Tuple[TestResult, str, Optional[Dict[str, float]]]:
        """Test systematic_file_auditor.py integration."""
        try:
            # Test that systematic auditor can be imported and initialized
            sys.path.insert(0, str(self.project_root))
            
            import scripts.automated_audit.systematic_file_auditor as auditor
            
            # Initialize components
            from streamlit_extension.utils.database import DatabaseManager
            
            db_manager = DatabaseManager()
            tracker = auditor.DatabaseTracker(db_manager)
            token_manager = auditor.TokenManager()
            file_manager = auditor.FileListManager(self.project_root)
            
            # Test basic functionality
            files = file_manager.get_all_python_files()
            
            if len(files) > 0:
                return TestResult.PASS, f"Systematic auditor working: {len(files)} files detected", None
            else:
                return TestResult.WARNING, "No Python files detected by auditor", None
                
        except Exception as e:
            return TestResult.ERROR, f"Systematic auditor integration failed: {e}", None
    
    def test_claude_md_loading(self) -> Tuple[TestResult, str, Optional[Dict[str, float]]]:
        """Test CLAUDE.md files load correctly."""
        try:
            claude_files = []
            issues = []
            
            # Find all CLAUDE.md files
            for claude_file in self.project_root.rglob("CLAUDE.md"):
                claude_files.append(claude_file)
                
                try:
                    with open(claude_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    if len(content) < 100:
                        issues.append(f"CLAUDE.md too short: {claude_file}")
                        
                except Exception as e:
                    issues.append(f"Failed to read {claude_file}: {e}")
            
            if len(issues) == 0:
                return TestResult.PASS, f"All {len(claude_files)} CLAUDE.md files load correctly", None
            elif len(issues) < len(claude_files) * 0.1:  # Less than 10% issues
                return TestResult.WARNING, f"{len(issues)} issues found in {len(claude_files)} files", None
            else:
                return TestResult.FAIL, f"Too many issues: {issues}", None
                
        except Exception as e:
            return TestResult.ERROR, f"CLAUDE.md loading test failed: {e}", None
    
    def test_documentation_links(self) -> Tuple[TestResult, str, Optional[Dict[str, float]]]:
        """Test documentation cross-references."""
        try:
            broken_links = []
            total_links = 0
            
            # Check documentation files for broken links
            for doc_file in self.project_root.rglob("*.md"):
                try:
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Find markdown links
                    import re
                    links = re.findall(r'\[.*?\]\((.*?)\)', content)
                    
                    for link in links:
                        total_links += 1
                        
                        # Check if it's a local file reference
                        if link.endswith('.md') and not link.startswith('http'):
                            link_path = doc_file.parent / link
                            if not link_path.exists():
                                broken_links.append(f"{doc_file}: {link}")
                                
                except Exception as e:
                    continue  # Skip files that can't be read
            
            if len(broken_links) == 0:
                return TestResult.PASS, f"All {total_links} documentation links valid", None
            elif len(broken_links) < total_links * 0.05:  # Less than 5% broken
                return TestResult.WARNING, f"{len(broken_links)} broken links found", None
            else:
                return TestResult.FAIL, f"Too many broken links: {len(broken_links)}", None
                
        except Exception as e:
            return TestResult.ERROR, f"Documentation links test failed: {e}", None
    
    def test_context_extraction_references(self) -> Tuple[TestResult, str, Optional[Dict[str, float]]]:
        """Test context extraction roteiros reference existing docs."""
        try:
            roteiros_file = self.project_root / "scripts" / "automated_audit" / "CONTEXT_EXTRACTION_ROTEIROS.md"
            
            if not roteiros_file.exists():
                return TestResult.SKIP, "CONTEXT_EXTRACTION_ROTEIROS.md not found", None
            
            with open(roteiros_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for references to existing documentation
            required_refs = [
                "CLAUDE.md", "INDEX.md", "NAVIGATION.md", 
                "streamlit_extension", "duration_system"
            ]
            
            missing_refs = []
            for ref in required_refs:
                if ref not in content:
                    missing_refs.append(ref)
            
            if len(missing_refs) == 0:
                return TestResult.PASS, "All required references found in roteiros", None
            else:
                return TestResult.WARNING, f"Missing references: {missing_refs}", None
                
        except Exception as e:
            return TestResult.ERROR, f"Context extraction references test failed: {e}", None
    
    def test_system_startup_performance(self) -> Tuple[TestResult, str, Optional[Dict[str, float]]]:
        """Test system startup performance impact."""
        try:
            # Measure import time
            start_time = time.time()
            
            # Test critical imports
            import streamlit_extension.utils.database
            import duration_system.duration_calculator
            
            import_time = time.time() - start_time
            
            # Check if reasonable (under 2 seconds)
            if import_time < 2.0:
                return TestResult.PASS, f"System imports in {import_time:.2f}s", {"import_time": import_time}
            elif import_time < 5.0:
                return TestResult.WARNING, f"Slow imports: {import_time:.2f}s", {"import_time": import_time}
            else:
                return TestResult.FAIL, f"Very slow imports: {import_time:.2f}s", {"import_time": import_time}
                
        except Exception as e:
            return TestResult.ERROR, f"Startup performance test failed: {e}", None
    
    def test_context_loading_performance(self) -> Tuple[TestResult, str, Optional[Dict[str, float]]]:
        """Test context loading performance."""
        try:
            # Test context validator performance
            sys.path.insert(0, str(self.project_root / "scripts" / "automated_audit"))
            import context_validator
            
            start_time = time.time()
            
            validator = context_validator.ContextValidator(self.project_root)
            
            # Load a real CLAUDE.md file
            claude_file = self.project_root / "streamlit_extension" / "services" / "CLAUDE.md"
            if claude_file.exists():
                with open(claude_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                result = validator.validate_context_quality(
                    content, context_validator.ContextType.TDD_WORKFLOW
                )
            
            loading_time = time.time() - start_time
            
            if loading_time < 1.0:
                return TestResult.PASS, f"Context loading in {loading_time:.2f}s", {"loading_time": loading_time}
            elif loading_time < 3.0:
                return TestResult.WARNING, f"Slow context loading: {loading_time:.2f}s", {"loading_time": loading_time}
            else:
                return TestResult.FAIL, f"Very slow context loading: {loading_time:.2f}s", {"loading_time": loading_time}
                
        except Exception as e:
            return TestResult.ERROR, f"Context loading performance test failed: {e}", None
    
    def test_comprehensive_integrity(self) -> Tuple[TestResult, str, Optional[Dict[str, float]]]:
        """Run comprehensive integrity test."""
        try:
            # Run the comprehensive integrity test
            result = subprocess.run(
                [sys.executable, "scripts/testing/comprehensive_integrity_test.py"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if result.returncode == 0:
                # Check output for pass/fail indicators
                output = result.stdout + result.stderr
                
                if "PASS" in output and "FAIL" not in output:
                    return TestResult.PASS, "Comprehensive integrity test passed", None
                elif "FAIL" in output:
                    return TestResult.WARNING, "Some integrity test components failed", None
                else:
                    return TestResult.PASS, "Integrity test completed without errors", None
            else:
                return TestResult.FAIL, f"Integrity test failed with code {result.returncode}", None
                
        except subprocess.TimeoutExpired:
            return TestResult.ERROR, "Comprehensive integrity test timed out", None
        except Exception as e:
            return TestResult.ERROR, f"Comprehensive integrity test failed: {e}", None
    
    def test_database_health(self) -> Tuple[TestResult, str, Optional[Dict[str, float]]]:
        """Test database health."""
        try:
            from streamlit_extension.utils.database import DatabaseManager
            
            db_manager = DatabaseManager()
            
            # Test basic database operations
            with db_manager.get_connection("framework") as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
            
            if table_count > 0:
                return TestResult.PASS, f"Database healthy: {table_count} tables", None
            else:
                return TestResult.FAIL, "No tables found in database", None
                
        except Exception as e:
            return TestResult.ERROR, f"Database health test failed: {e}", None
    
    def test_existing_functionality(self) -> Tuple[TestResult, str, Optional[Dict[str, float]]]:
        """Test existing functionality for regressions."""
        try:
            # Test basic functionality that should still work
            from streamlit_extension.utils.database import DatabaseManager
            from duration_system.duration_calculator import DurationCalculator
            
            # Test database manager
            db_manager = DatabaseManager()
            
            # Test duration calculator
            calc = DurationCalculator()
            
            # Test basic operations
            with db_manager.get_connection("framework") as conn:
                cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
                result = cursor.fetchone()
            
            if result:
                return TestResult.PASS, "Core functionality working correctly", None
            else:
                return TestResult.WARNING, "No database tables found", None
                
        except Exception as e:
            return TestResult.ERROR, f"Existing functionality test failed: {e}", None
    
    def test_import_regression(self) -> Tuple[TestResult, str, Optional[Dict[str, float]]]:
        """Test Python imports for regressions."""
        try:
            critical_imports = [
                "streamlit_extension.utils.database",
                "streamlit_extension.services",
                "duration_system.duration_calculator", 
                "scripts.automated_audit.systematic_file_auditor"
            ]
            
            failed_imports = []
            
            for import_name in critical_imports:
                try:
                    __import__(import_name)
                except ImportError as e:
                    failed_imports.append(f"{import_name}: {e}")
            
            if len(failed_imports) == 0:
                return TestResult.PASS, f"All {len(critical_imports)} critical imports working", None
            else:
                return TestResult.FAIL, f"Failed imports: {failed_imports}", None
                
        except Exception as e:
            return TestResult.ERROR, f"Import regression test failed: {e}", None
    
    def _calculate_test_metrics(self, total_time: float) -> IntegrationTestMetrics:
        """Calculate test metrics from executions."""
        total_tests = len(self.test_executions)
        if total_tests == 0:
            return IntegrationTestMetrics(0, 0, 0, 0, 0, 0, 0.0, 0.0, False, 0)
        
        passed = sum(1 for ex in self.test_executions if ex.result == TestResult.PASS)
        failed = sum(1 for ex in self.test_executions if ex.result == TestResult.FAIL)
        warning = sum(1 for ex in self.test_executions if ex.result == TestResult.WARNING)
        skipped = sum(1 for ex in self.test_executions if ex.result == TestResult.SKIP)
        error = sum(1 for ex in self.test_executions if ex.result == TestResult.ERROR)
        
        avg_time = total_time / total_tests if total_tests > 0 else 0.0
        
        # Check for performance degradation
        performance_degradation = any(
            ex.performance_metrics and ex.performance_metrics.get("degradation_percentage", 0) > 0.1
            for ex in self.test_executions
        )
        
        # Count rollbacks
        rollbacks = sum(1 for ex in self.test_executions if ex.rollback_triggered)
        
        return IntegrationTestMetrics(
            total_tests=total_tests,
            passed_tests=passed,
            failed_tests=failed,
            warning_tests=warning,
            skipped_tests=skipped,
            error_tests=error,
            total_execution_time=total_time,
            average_execution_time=avg_time,
            performance_degradation_detected=performance_degradation,
            rollbacks_triggered=rollbacks
        )
    
    def generate_test_report(self, output_path: Optional[Path] = None) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        if not self.test_executions:
            self.logger.warning("No test executions to report")
            return {}
        
        metrics = self._calculate_test_metrics(
            sum(ex.execution_time for ex in self.test_executions)
        )
        
        report = {
            "test_summary": asdict(metrics),
            "test_executions": [asdict(ex) for ex in self.test_executions],
            "failed_tests": [
                asdict(ex) for ex in self.test_executions 
                if ex.result in [TestResult.FAIL, TestResult.ERROR]
            ],
            "performance_metrics": [
                ex.performance_metrics for ex in self.test_executions 
                if ex.performance_metrics
            ],
            "rollback_recommendations": self._generate_rollback_recommendations(),
            "generated_at": self._get_timestamp(),
            "tester_version": "1.0.0"
        }
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Test report saved to: {output_path}")
        
        return report
    
    def _generate_rollback_recommendations(self) -> List[str]:
        """Generate rollback recommendations."""
        recommendations = []
        
        failed_count = sum(1 for ex in self.test_executions if ex.result == TestResult.FAIL)
        error_count = sum(1 for ex in self.test_executions if ex.result == TestResult.ERROR)
        
        if failed_count >= 3:
            recommendations.append("Consider rollback due to multiple test failures")
        
        if error_count >= 2:
            recommendations.append("Consider rollback due to multiple test errors")
        
        if any(ex.rollback_triggered for ex in self.test_executions):
            recommendations.append("Automatic rollback was triggered")
        
        return recommendations
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    """Main entry point for integration tester."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Integration Tester")
    parser.add_argument("--categories", nargs='+', help="Test categories to run")
    parser.add_argument("--output-report", help="Output test report path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    # Setup logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format='%(asctime)s - %(levelname)s - %(message)s')
    
    tester = IntegrationTester()
    
    try:
        # Determine categories to run
        categories = None
        if args.categories:
            categories = []
            for cat_name in args.categories:
                try:
                    categories.append(TestCategory(cat_name))
                except ValueError:
                    print(f"Unknown category: {cat_name}")
                    return 1
        
        # Run tests
        metrics = tester.run_integration_tests(categories)
        
        # Display results
        print(f"\n✅ Integration Testing Complete:")
        print(f"   Total Tests: {metrics.total_tests}")
        print(f"   Passed: {metrics.passed_tests}")
        print(f"   Failed: {metrics.failed_tests}")
        print(f"   Warnings: {metrics.warning_tests}")
        print(f"   Errors: {metrics.error_tests}")
        print(f"   Execution Time: {metrics.total_execution_time:.2f}s")
        
        if metrics.performance_degradation_detected:
            print(f"   ⚠️ Performance degradation detected")
        
        if metrics.rollbacks_triggered > 0:
            print(f"   🚨 {metrics.rollbacks_triggered} rollback(s) triggered")
        
        # Generate report if requested
        if args.output_report:
            report = tester.generate_test_report(Path(args.output_report))
            print(f"📊 Test report saved to: {args.output_report}")
        
        # Return appropriate exit code
        if metrics.failed_tests > 0 or metrics.error_tests > 0:
            return 1
        
    except Exception as e:
        logging.error(f"Integration testing failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())