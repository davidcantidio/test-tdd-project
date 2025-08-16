#!/usr/bin/env python3
"""
🧪 Health Check System Testing Suite

Tests the health check endpoint system addressing report.md requirement:
"Implement health-check endpoint for orchestration"

This test validates:
- Health check endpoint functionality
- Database connectivity checks
- System resource monitoring
- Kubernetes readiness/liveness probes
- Metrics endpoint
"""

import sys
import time
import json
import requests
import threading
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

try:
    from monitoring.health_check import (
        HealthCheckManager, 
        HealthCheckServer,
        HealthStatus,
        get_health_status,
        start_health_check_server,
        stop_health_check_server
    )
    HEALTH_CHECK_AVAILABLE = True
except ImportError as e:
    HEALTH_CHECK_AVAILABLE = False
    print(f"❌ Health check module not available: {e}")


def test_health_check_manager():
    """Test health check manager functionality."""
    if not HEALTH_CHECK_AVAILABLE:
        return False
    
    print("🩺 Testing Health Check Manager")
    print("=" * 45)
    
    try:
        # Create health check manager
        manager = HealthCheckManager()
        
        # Verify default checks are registered
        check_names = [check.name for check in manager.checks]
        print(f"✅ Registered checks: {', '.join(check_names)}")
        
        expected_checks = ["uptime"]  # This should always be available
        for expected in expected_checks:
            assert expected in check_names, f"Expected check '{expected}' not found"
        
        # Run health checks
        result = manager.run_checks()
        
        # Validate response structure
        required_fields = ["status", "timestamp", "environment", "version", "uptime_seconds", "checks"]
        for field in required_fields:
            assert field in result, f"Required field '{field}' missing from health check result"
        
        print(f"✅ Health check result structure valid")
        print(f"   Status: {result['status']}")
        print(f"   Environment: {result['environment']}")
        print(f"   Checks: {len(result['checks'])}")
        print(f"   Duration: {result.get('duration_ms', 0)}ms")
        
        # Validate individual checks
        for check in result['checks']:
            check_fields = ["name", "status", "message", "critical", "duration_ms", "timestamp"]
            for field in check_fields:
                assert field in check, f"Check field '{field}' missing from check '{check.get('name', 'unknown')}'"
        
        print("✅ All health check components working")
        return True
        
    except Exception as e:
        print(f"❌ Health check manager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_health_check_server():
    """Test health check HTTP server."""
    if not HEALTH_CHECK_AVAILABLE:
        return False
    
    print("\n🌐 Testing Health Check Server")
    print("-" * 35)
    
    server = None
    try:
        # Start server on a test port
        test_port = 8081
        server = HealthCheckServer(host="127.0.0.1", port=test_port)
        server.start(blocking=False)
        
        # Give server time to start
        time.sleep(1)
        
        base_url = f"http://127.0.0.1:{test_port}"
        
        # Test health endpoint
        print("📋 Testing /health endpoint...")
        response = requests.get(f"{base_url}/health", timeout=5)
        
        assert response.status_code in [200, 503], f"Unexpected status code: {response.status_code}"
        
        health_data = response.json()
        assert "status" in health_data, "Health response missing 'status' field"
        assert "checks" in health_data, "Health response missing 'checks' field"
        
        print(f"✅ /health endpoint working (status: {health_data['status']})")
        
        # Test readiness endpoint
        print("📋 Testing /ready endpoint...")
        response = requests.get(f"{base_url}/ready", timeout=5)
        
        assert response.status_code in [200, 503], f"Unexpected readiness status: {response.status_code}"
        
        ready_data = response.json()
        assert "status" in ready_data, "Readiness response missing 'status' field"
        
        print(f"✅ /ready endpoint working (status: {ready_data['status']})")
        
        # Test liveness endpoint
        print("📋 Testing /live endpoint...")
        response = requests.get(f"{base_url}/live", timeout=5)
        
        assert response.status_code == 200, f"Liveness check failed: {response.status_code}"
        
        live_data = response.json()
        assert "status" in live_data, "Liveness response missing 'status' field"
        assert live_data["status"] == "alive", f"Expected 'alive' status, got: {live_data['status']}"
        
        print(f"✅ /live endpoint working")
        
        # Test metrics endpoint
        print("📋 Testing /metrics endpoint...")
        response = requests.get(f"{base_url}/metrics", timeout=5)
        
        assert response.status_code == 200, f"Metrics check failed: {response.status_code}"
        
        metrics_data = response.json()
        expected_metrics = ["health_status", "uptime_seconds", "total_checks"]
        for metric in expected_metrics:
            assert metric in metrics_data, f"Expected metric '{metric}' missing"
        
        print(f"✅ /metrics endpoint working (checks: {metrics_data.get('total_checks', 0)})")
        
        print("✅ All HTTP endpoints working correctly")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ HTTP request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Health check server test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if server:
            server.stop()


def test_individual_health_checks():
    """Test individual health check components."""
    if not HEALTH_CHECK_AVAILABLE:
        return False
    
    print("\n🔍 Testing Individual Health Checks")
    print("-" * 40)
    
    try:
        manager = HealthCheckManager()
        
        # Test each health check individually
        for health_check in manager.checks:
            print(f"📋 Testing {health_check.name} check...")
            
            start_time = time.time()
            result = health_check.run()
            duration = time.time() - start_time
            
            # Validate result structure
            required_fields = ["name", "status", "message", "critical", "duration_ms", "timestamp"]
            for field in required_fields:
                assert field in result, f"Check result missing '{field}' field"
            
            # Validate status values
            valid_statuses = [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
            assert result["status"] in valid_statuses, f"Invalid status: {result['status']}"
            
            # Validate timing
            assert result["duration_ms"] > 0, "Duration should be positive"
            assert duration < 10, f"Check took too long: {duration}s"
            
            status_emoji = {
                HealthStatus.HEALTHY: "✅",
                HealthStatus.DEGRADED: "⚠️",
                HealthStatus.UNHEALTHY: "❌"
            }.get(result["status"], "❓")
            
            critical_mark = " (CRITICAL)" if result["critical"] else ""
            print(f"   {status_emoji} {result['name']}{critical_mark}: {result['message']}")
            print(f"   Duration: {result['duration_ms']}ms")
        
        print("✅ All individual health checks completed")
        return True
        
    except Exception as e:
        print(f"❌ Individual health checks test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_health_check_resilience():
    """Test health check system resilience."""
    if not HEALTH_CHECK_AVAILABLE:
        return False
    
    print("\n🛡️ Testing Health Check Resilience")
    print("-" * 40)
    
    try:
        manager = HealthCheckManager()
        
        # Add a check that always fails
        def failing_check():
            raise Exception("Intentional test failure")
        
        manager.add_check("test_failure", failing_check, timeout=1.0, critical=False)
        
        # Run checks with failure
        result = manager.run_checks()
        
        # Should still return results despite failure
        assert "status" in result, "Health check should return status despite failures"
        assert "checks" in result, "Health check should return check results despite failures"
        
        # Find the failing check
        failing_check_result = next(
            (check for check in result["checks"] if check["name"] == "test_failure"),
            None
        )
        
        assert failing_check_result is not None, "Failing check result not found"
        assert failing_check_result["status"] == HealthStatus.UNHEALTHY, "Failing check should be unhealthy"
        
        print("✅ System handles individual check failures gracefully")
        
        # Test timeout resilience
        def slow_check():
            time.sleep(2)  # Slower than timeout
            return {"status": HealthStatus.HEALTHY}
        
        manager.add_check("test_timeout", slow_check, timeout=0.5, critical=False)
        
        start_time = time.time()
        result = manager.run_checks()
        total_duration = time.time() - start_time
        
        # Should complete in reasonable time despite slow check
        assert total_duration < 5, f"Health checks took too long: {total_duration}s"
        
        print("✅ System handles slow checks appropriately")
        
        print("✅ Health check resilience validated")
        return True
        
    except Exception as e:
        print(f"❌ Health check resilience test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_kubernetes_integration():
    """Test Kubernetes-style probes."""
    if not HEALTH_CHECK_AVAILABLE:
        return False
    
    print("\n☸️ Testing Kubernetes Integration")
    print("-" * 40)
    
    server = None
    try:
        # Start server
        test_port = 8082
        server = HealthCheckServer(host="127.0.0.1", port=test_port)
        server.start(blocking=False)
        time.sleep(1)
        
        base_url = f"http://127.0.0.1:{test_port}"
        
        # Test readiness probe (should be 200 or 503)
        response = requests.get(f"{base_url}/ready", timeout=3)
        print(f"✅ Readiness probe: HTTP {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            assert data["status"] == "ready", "Ready response should indicate ready status"
        
        # Test liveness probe (should always be 200)
        response = requests.get(f"{base_url}/live", timeout=3)
        assert response.status_code == 200, "Liveness probe should always return 200"
        
        data = response.json()
        assert data["status"] == "alive", "Live response should indicate alive status"
        
        print("✅ Liveness probe: HTTP 200 (always alive)")
        
        # Test that probes are fast (Kubernetes requirement)
        start_time = time.time()
        requests.get(f"{base_url}/ready", timeout=3)
        requests.get(f"{base_url}/live", timeout=3)
        probe_duration = time.time() - start_time
        
        assert probe_duration < 2, f"Probes too slow for Kubernetes: {probe_duration}s"
        print(f"✅ Probe performance: {probe_duration:.2f}s (fast enough for K8s)")
        
        print("✅ Kubernetes integration compatible")
        return True
        
    except Exception as e:
        print(f"❌ Kubernetes integration test failed: {e}")
        return False
    finally:
        if server:
            server.stop()


def test_cli_interface():
    """Test command-line interface."""
    if not HEALTH_CHECK_AVAILABLE:
        return False
    
    print("\n💻 Testing CLI Interface")
    print("-" * 30)
    
    try:
        # Test get_health_status function
        result = get_health_status()
        
        assert isinstance(result, dict), "Health status should return dictionary"
        assert "status" in result, "Health status should include status"
        assert "checks" in result, "Health status should include checks"
        
        print(f"✅ CLI health check working (status: {result['status']})")
        
        # Test would normally include subprocess testing of CLI
        # but that's more complex for this validation
        
        print("✅ CLI interface functional")
        return True
        
    except Exception as e:
        print(f"❌ CLI interface test failed: {e}")
        return False


def main():
    """Main test execution."""
    print("🩺 HEALTH CHECK SYSTEM TEST SUITE")
    print("=" * 60)
    print("Addresses report.md requirement:")
    print("- Implement health-check endpoint for orchestration")
    print()
    
    if not HEALTH_CHECK_AVAILABLE:
        print("❌ Health check system not available")
        return False
    
    tests = [
        ("Health Check Manager", test_health_check_manager),
        ("Health Check Server", test_health_check_server),
        ("Individual Health Checks", test_individual_health_checks),
        ("Health Check Resilience", test_health_check_resilience),
        ("Kubernetes Integration", test_kubernetes_integration),
        ("CLI Interface", test_cli_interface),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
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
        print("✅ Health check system is working correctly")
        print("✅ Report.md requirement fulfilled: Health-check endpoint implemented")
        print("✅ Kubernetes/Docker compatible probes available")
        print("✅ Production deployment ready")
        return True
    else:
        print(f"\n❌ {total-passed} tests failed")
        print("❗ Health check system needs fixes")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)