import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
from streamlit_extension.endpoints import HealthCheckEndpoint, HealthStatus, ComponentChecker


def test_basic_health_check():
    endpoint = HealthCheckEndpoint()
    data = endpoint.basic_health()
    assert data["status"] == HealthStatus.HEALTHY.value
    assert "timestamp" in data and "uptime" in data


def test_detailed_health_check():
    endpoint = HealthCheckEndpoint()
    data = endpoint.detailed_health()
    assert data["status"] == HealthStatus.HEALTHY.value
    components = data["components"]
    assert set(["database", "cache", "system"]).issubset(components.keys())


def test_readiness_check():
    endpoint = HealthCheckEndpoint()
    code, payload = endpoint.readiness_check()
    assert code == 200
    assert payload["ready"] is True


def test_liveness_check():
    endpoint = HealthCheckEndpoint()
    code, payload = endpoint.liveness_check()
    assert code == 200
    assert payload["alive"] is True


def test_health_check_with_database_down(monkeypatch):
    def failed_db(self):
        return {"status": HealthStatus.UNHEALTHY.value}

    monkeypatch.setattr(ComponentChecker, "check_database", failed_db, raising=False)
    endpoint = HealthCheckEndpoint()
    data = endpoint.detailed_health()
    assert data["status"] == HealthStatus.UNHEALTHY.value


def test_health_check_with_degraded_performance(monkeypatch):
    def degraded_memory(self):
        return {
            "status": HealthStatus.DEGRADED.value,
            "cpu_usage": "95%",
            "memory_usage": "95%",
        }

    monkeypatch.setattr(ComponentChecker, "check_memory_usage", degraded_memory, raising=False)
    endpoint = HealthCheckEndpoint()
    data = endpoint.detailed_health()
    assert data["status"] == HealthStatus.DEGRADED.value