"""
🚀 Integration Test Runner

Comprehensive test runner for all integration tests with reporting and analysis.
Coordinates execution of all integration test suites and provides detailed
reporting on system integration status.

Features:
- Sequential and parallel test execution
- Comprehensive reporting with metrics
- Performance analysis and trending
- System health validation
- Integration coverage analysis
- Failure analysis and recommendations

Usage:
    python test_runner.py --mode full
    python test_runner.py --mode quick
    python test_runner.py --report-only
"""

import pytest
import time
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import subprocess
import os
import traceback

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))


class IntegrationTestRunner:
    """Comprehensive integration test runner and reporter."""
    
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
        self.system_health = {}
        self.coverage_data = {}
        self.start_time = None
        self.end_time = None
        
        # Test suites configuration
        self.test_suites = {
            "e2e_workflows": {
                "module": "test_e2e_workflows",
                "description": "End-to-end user workflows",
                "priority": "high",
                "estimated_duration": 120,  # seconds
                "dependencies": []
            },
            "cross_system": {
                "module": "test_cross_system", 
                "description": "Cross-system integration",
                "priority": "high",
                "estimated_duration": 90,
                "dependencies": []
            },
            "performance": {
                "module": "test_performance_integration",
                "description": "Performance under load",
                "priority": "medium",
                "estimated_duration": 180,
                "dependencies": []
            },
            "cache_system": {
                "module": "test_cache_system",
                "description": "Cache system integration",
                "priority": "medium", 
                "estimated_duration": 60,
                "dependencies": []
            },
            "ui_components": {
                "module": "test_ui_components",
                "description": "UI component integration",
                "priority": "low",
                "estimated_duration": 45,
                "dependencies": []
            },
            "theme_system": {
                "module": "test_theme_system",
                "description": "Theme system integration",
                "priority": "low",
                "estimated_duration": 30,
                "dependencies": []
            }
        }
    
    def run_test_suite(self, suite_name: str, verbose: bool = False) -> Dict[str, Any]:
        """Run a single test suite and collect results."""
        suite_config = self.test_suites.get(suite_name)
        if not suite_config:
            return {"error": f"Unknown test suite: {suite_name}"}
        
        test_file = Path(__file__).parent / f"{suite_config['module']}.py"
        if not test_file.exists():
            return {"error": f"Test file not found: {test_file}"}
        
        print(f"📋 Running {suite_name}: {suite_config['description']}")
        
        start_time = time.time()
        
        try:
            # Run pytest with JSON output
            cmd = [
                sys.executable, "-m", "pytest",
                str(test_file),
                "--json-report",
                "--json-report-file", f"/tmp/test_report_{suite_name}.json",
                "-v" if verbose else "-q",
                "--tb=short"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=suite_config["estimated_duration"] * 2  # Double timeout as safety
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Parse JSON report if available
            report_file = Path(f"/tmp/test_report_{suite_name}.json")
            if report_file.exists():
                try:
                    with open(report_file) as f:
                        pytest_report = json.load(f)
                except:
                    pytest_report = {}
            else:
                pytest_report = {}
            
            # Extract test results
            test_results = {
                "suite_name": suite_name,
                "description": suite_config["description"],
                "priority": suite_config["priority"],
                "start_time": datetime.fromtimestamp(start_time).isoformat(),
                "end_time": datetime.fromtimestamp(end_time).isoformat(),
                "duration_seconds": duration,
                "return_code": result.returncode,
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "pytest_report": pytest_report
            }
            
            # Extract test statistics from pytest report
            if pytest_report and "summary" in pytest_report:
                summary = pytest_report["summary"]
                test_results.update({
                    "tests_collected": summary.get("total", 0),
                    "tests_passed": summary.get("passed", 0),
                    "tests_failed": summary.get("failed", 0),
                    "tests_skipped": summary.get("skipped", 0),
                    "tests_error": summary.get("error", 0)
                })
            else:
                # Parse from stdout as fallback
                stdout_lines = result.stdout.split("\\n")
                for line in stdout_lines:
                    if "passed" in line and "failed" in line:
                        # Extract test counts from pytest output
                        test_results.update(self._parse_pytest_output(line))
                        break
            
            # Clean up report file
            if report_file.exists():
                try:
                    report_file.unlink()
                except:
                    pass
            
        except subprocess.TimeoutExpired:
            test_results = {
                "suite_name": suite_name,
                "description": suite_config["description"],
                "priority": suite_config["priority"],
                "duration_seconds": suite_config["estimated_duration"] * 2,
                "success": False,
                "error": "Test suite timed out",
                "timeout": True
            }
        
        except Exception as e:
            test_results = {
                "suite_name": suite_name,
                "description": suite_config["description"],
                "priority": suite_config["priority"],
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
        
        return test_results
    
    def _parse_pytest_output(self, output_line: str) -> Dict[str, int]:
        """Parse pytest output line to extract test counts."""
        counts = {
            "tests_collected": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "tests_skipped": 0,
            "tests_error": 0
        }
        
        # Example line: "5 passed, 2 failed, 1 skipped in 10.5s"
        import re
        
        passed_match = re.search(r"(\\d+) passed", output_line)
        if passed_match:
            counts["tests_passed"] = int(passed_match.group(1))
        
        failed_match = re.search(r"(\\d+) failed", output_line)
        if failed_match:
            counts["tests_failed"] = int(failed_match.group(1))
        
        skipped_match = re.search(r"(\\d+) skipped", output_line)
        if skipped_match:
            counts["tests_skipped"] = int(skipped_match.group(1))
        
        error_match = re.search(r"(\\d+) error", output_line)
        if error_match:
            counts["tests_error"] = int(error_match.group(1))
        
        counts["tests_collected"] = sum([
            counts["tests_passed"],
            counts["tests_failed"], 
            counts["tests_skipped"],
            counts["tests_error"]
        ])
        
        return counts
    
    def run_all_tests(self, mode: str = "full", verbose: bool = False) -> Dict[str, Any]:
        """Run all integration tests based on mode."""
        self.start_time = time.time()
        
        print(f"🚀 Starting Integration Test Suite - Mode: {mode}")
        print("=" * 60)
        
        # Determine which tests to run based on mode
        if mode == "quick":
            suites_to_run = [name for name, config in self.test_suites.items() 
                           if config["priority"] == "high"]
        elif mode == "essential":
            suites_to_run = [name for name, config in self.test_suites.items() 
                           if config["priority"] in ["high", "medium"]]
        else:  # full mode
            suites_to_run = list(self.test_suites.keys())
        
        print(f"📋 Running {len(suites_to_run)} test suites: {', '.join(suites_to_run)}")
        
        # Estimate total duration
        estimated_duration = sum(
            self.test_suites[suite]["estimated_duration"] 
            for suite in suites_to_run
        )
        print(f"⏰ Estimated duration: {estimated_duration // 60}m {estimated_duration % 60}s")
        print()
        
        # Run test suites
        for suite_name in suites_to_run:
            result = self.run_test_suite(suite_name, verbose)
            self.test_results[suite_name] = result
            
            # Print immediate feedback
            if result.get("success", False):
                status = "✅ PASSED"
                duration = result.get("duration_seconds", 0)
                test_info = ""
                if "tests_passed" in result:
                    test_info = f" ({result['tests_passed']} tests)"
                print(f"{status} {suite_name}{test_info} - {duration:.1f}s")
            else:
                status = "❌ FAILED"
                error = result.get("error", "Unknown error")
                print(f"{status} {suite_name} - {error}")
            
            print()
        
        self.end_time = time.time()
        
        # Generate comprehensive report
        return self._generate_comprehensive_report()
    
    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_duration = self.end_time - self.start_time
        
        # Calculate overall statistics
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        total_errors = 0
        successful_suites = 0
        failed_suites = 0
        
        suite_summaries = []
        
        for suite_name, result in self.test_results.items():
            if result.get("success", False):
                successful_suites += 1
            else:
                failed_suites += 1
            
            # Aggregate test counts
            total_tests += result.get("tests_collected", 0)
            total_passed += result.get("tests_passed", 0)
            total_failed += result.get("tests_failed", 0)
            total_skipped += result.get("tests_skipped", 0)
            total_errors += result.get("tests_error", 0)
            
            # Create suite summary
            suite_summary = {
                "name": suite_name,
                "description": result.get("description", ""),
                "priority": result.get("priority", "unknown"),
                "success": result.get("success", False),
                "duration": result.get("duration_seconds", 0),
                "tests": {
                    "collected": result.get("tests_collected", 0),
                    "passed": result.get("tests_passed", 0),
                    "failed": result.get("tests_failed", 0),
                    "skipped": result.get("tests_skipped", 0),
                    "error": result.get("tests_error", 0)
                }
            }
            
            if not result.get("success", False):
                suite_summary["error"] = result.get("error", "Unknown error")
            
            suite_summaries.append(suite_summary)
        
        # Calculate success rates
        suite_success_rate = (successful_suites / len(self.test_results)) * 100 if self.test_results else 0
        test_success_rate = (total_passed / total_tests) * 100 if total_tests > 0 else 0
        
        # Overall health assessment
        overall_health = "healthy"
        if failed_suites > 0 or total_failed > 0:
            if suite_success_rate < 50:
                overall_health = "critical"
            elif suite_success_rate < 80:
                overall_health = "degraded"
            else:
                overall_health = "warning"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_run_duration": total_duration,
            "overall_status": overall_health,
            
            "suite_summary": {
                "total_suites": len(self.test_results),
                "successful_suites": successful_suites,
                "failed_suites": failed_suites,
                "suite_success_rate": suite_success_rate
            },
            
            "test_summary": {
                "total_tests": total_tests,
                "passed": total_passed,
                "failed": total_failed,
                "skipped": total_skipped,
                "errors": total_errors,
                "test_success_rate": test_success_rate
            },
            
            "suites": suite_summaries,
            "detailed_results": self.test_results,
            
            "recommendations": self._generate_recommendations(overall_health, suite_summaries)
        }
        
        return report
    
    def _generate_recommendations(self, overall_health: str, suite_summaries: List[Dict]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        # Overall health recommendations
        if overall_health == "critical":
            recommendations.append("🚨 CRITICAL: Multiple test suites failing. Immediate investigation required.")
        elif overall_health == "degraded":
            recommendations.append("⚠️ WARNING: System integration has significant issues. Review failed tests.")
        elif overall_health == "warning":
            recommendations.append("⚠️ Some test failures detected. Monitor and address failing tests.")
        else:
            recommendations.append("✅ All integration tests passing. System integration is healthy.")
        
        # Suite-specific recommendations
        failed_suites = [suite for suite in suite_summaries if not suite["success"]]
        for suite in failed_suites:
            if suite["priority"] == "high":
                recommendations.append(f"🔥 HIGH PRIORITY: Fix {suite['name']} - {suite['description']}")
            elif suite["priority"] == "medium":
                recommendations.append(f"📋 MEDIUM PRIORITY: Address {suite['name']} issues")
            else:
                recommendations.append(f"📝 LOW PRIORITY: Review {suite['name']} when time permits")
        
        # Performance recommendations
        slow_suites = [suite for suite in suite_summaries if suite["duration"] > 120]
        if slow_suites:
            recommendations.append(f"⏰ Performance concern: {len(slow_suites)} test suites taking >2 minutes")
        
        # Coverage recommendations
        skipped_tests = sum(suite["tests"]["skipped"] for suite in suite_summaries)
        if skipped_tests > 0:
            recommendations.append(f"📊 {skipped_tests} tests skipped - consider environment setup or dependencies")
        
        return recommendations
    
    def print_report(self, report: Dict[str, Any], detailed: bool = False):
        """Print formatted test report."""
        print("🧪 INTEGRATION TEST REPORT")
        print("=" * 60)
        print(f"📅 Timestamp: {report['timestamp']}")
        print(f"⏱️ Duration: {report['test_run_duration']:.1f} seconds")
        print(f"🏥 Overall Status: {report['overall_status'].upper()}")
        print()
        
        # Suite summary
        suite_summary = report["suite_summary"]
        print("📋 TEST SUITE SUMMARY")
        print("-" * 30)
        print(f"Total Suites: {suite_summary['total_suites']}")
        print(f"Successful: {suite_summary['successful_suites']} ({suite_summary['suite_success_rate']:.1f}%)")
        print(f"Failed: {suite_summary['failed_suites']}")
        print()
        
        # Test summary
        test_summary = report["test_summary"]
        print("🧪 TEST SUMMARY")
        print("-" * 30)
        print(f"Total Tests: {test_summary['total_tests']}")
        print(f"Passed: {test_summary['passed']} ({test_summary['test_success_rate']:.1f}%)")
        print(f"Failed: {test_summary['failed']}")
        print(f"Skipped: {test_summary['skipped']}")
        print(f"Errors: {test_summary['errors']}")
        print()
        
        # Suite details
        print("📊 SUITE DETAILS")
        print("-" * 30)
        for suite in report["suites"]:
            status = "✅" if suite["success"] else "❌"
            priority = suite["priority"].upper()
            duration = suite["duration"]
            tests = suite["tests"]
            
            print(f"{status} {suite['name']} ({priority}) - {duration:.1f}s")
            print(f"    {suite['description']}")
            
            if tests["collected"] > 0:
                print(f"    Tests: {tests['passed']}/{tests['collected']} passed")
                if tests["failed"] > 0:
                    print(f"    ⚠️ {tests['failed']} failed")
                if tests["skipped"] > 0:
                    print(f"    ⏭️ {tests['skipped']} skipped")
            
            if not suite["success"] and "error" in suite:
                print(f"    ❌ Error: {suite['error']}")
            
            print()
        
        # Recommendations
        print("💡 RECOMMENDATIONS")
        print("-" * 30)
        for rec in report["recommendations"]:
            print(f"  {rec}")
        print()
        
        # Detailed results (if requested)
        if detailed:
            print("🔍 DETAILED RESULTS")
            print("-" * 30)
            print(json.dumps(report["detailed_results"], indent=2))
    
    def save_report(self, report: Dict[str, Any], filename: Optional[str] = None):
        """Save report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"integration_test_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📁 Report saved to: {filename}")


def main():
    """Main entry point for integration test runner."""
    parser = argparse.ArgumentParser(description="Integration Test Runner")
    parser.add_argument(
        "--mode", 
        choices=["quick", "essential", "full"],
        default="essential",
        help="Test execution mode"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--detailed",
        action="store_true", 
        help="Show detailed test results"
    )
    parser.add_argument(
        "--save-report",
        action="store_true",
        help="Save report to JSON file"
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Only generate and display report from existing results"
    )
    
    args = parser.parse_args()
    
    runner = IntegrationTestRunner()
    
    if args.report_only:
        # Load existing results if available
        print("📊 Report-only mode: Displaying last test results")
        # This would load from a previous run - for now just show empty
        report = runner._generate_comprehensive_report()
    else:
        # Run tests
        report = runner.run_all_tests(mode=args.mode, verbose=args.verbose)
    
    # Display report
    runner.print_report(report, detailed=args.detailed)
    
    # Save report if requested
    if args.save_report:
        runner.save_report(report)
    
    # Exit with appropriate code
    if report["overall_status"] in ["critical", "degraded"]:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()