#!/usr/bin/env python3
"""
🧪 Integration Tests Execution Script

Simple script to run the comprehensive integration test suite for the TDD Framework.

Usage:
    python run_integration_tests.py                 # Run essential tests
    python run_integration_tests.py --quick         # Run only high-priority tests
    python run_integration_tests.py --full          # Run all tests (including slow ones)
    python run_integration_tests.py --report        # Generate report only
    python run_integration_tests.py --check         # Quick system health check
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Main execution function."""
    # Determine script mode from arguments
    args = sys.argv[1:]
    
    # Add project root to Python path
    project_root = Path(__file__).parent
    test_runner_path = project_root / "tests" / "integration" / "test_runner.py"
    
    if not test_runner_path.exists():
        print("❌ Integration test runner not found!")
        print(f"Expected: {test_runner_path}")
        sys.exit(1)
    
    # Parse simple arguments
    if "--help" in args or "-h" in args:
        print(__doc__)
        return
    
    # Determine mode
    if "--quick" in args:
        mode = "quick"
        print("🚀 Running Quick Integration Tests (High Priority Only)")
    elif "--full" in args:
        mode = "full"
        print("🧪 Running Full Integration Test Suite (All Tests)")
    elif "--report" in args:
        print("📊 Generating Integration Test Report")
        cmd = [sys.executable, str(test_runner_path), "--report-only"]
    elif "--check" in args:
        mode = "quick"
        print("🏥 Running System Health Check")
    else:
        mode = "essential"
        print("⚡ Running Essential Integration Tests (High + Medium Priority)")
    
    # Build command
    if "--report" not in args:
        cmd = [
            sys.executable, 
            str(test_runner_path),
            "--mode", mode
        ]
        
        # Add verbose flag if requested
        if "--verbose" in args or "-v" in args:
            cmd.append("--verbose")
        
        # Add detailed flag if requested
        if "--detailed" in args:
            cmd.append("--detailed")
        
        # Add save report flag if requested
        if "--save" in args:
            cmd.append("--save-report")
    
    print(f"📋 Command: {' '.join(cmd)}")
    print("=" * 60)
    
    # Execute the test runner
    try:
        result = subprocess.run(cmd, cwd=project_root)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n⚠️ Integration tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()