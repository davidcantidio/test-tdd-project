import sys
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
module_path = ROOT / "streamlit_extension" / "utils" / "monitoring.py"
spec = importlib.util.spec_from_file_location("streamlit_extension.utils.monitoring", module_path)
monitoring = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = monitoring
spec.loader.exec_module(monitoring)
SystemMonitor = monitoring.SystemMonitor
MetricsCollector = monitoring.MetricsCollector
AlertManager = monitoring.AlertManager


def test_metrics_collection():
    monitor = SystemMonitor()
    metrics = monitor.collect_metrics()
    assert set(["cpu_usage", "memory_usage", "disk_usage"]).issubset(metrics.keys())


def test_performance_monitoring():
    monitor = SystemMonitor()
    monitor.alert_manager.define_thresholds({"cpu_usage": 1000, "memory_usage": 1e9, "disk_usage": 1000})
    status = monitor.check_performance()
    assert status["cpu_usage"] == "healthy"
    assert status["memory_usage"] == "healthy"


def test_alert_generation():
    collector = MetricsCollector()
    monitor = SystemMonitor(collector=collector, alert_manager=AlertManager())
    monitor.alert_manager.define_thresholds({"cpu_usage": 0})
    alerts = monitor.generate_alerts()
    assert alerts
    assert monitor.alert_manager.notifications == alerts


def test_metrics_export():
    monitor = SystemMonitor()
    export = monitor.export_metrics()
    assert "cpu_usage" in export
