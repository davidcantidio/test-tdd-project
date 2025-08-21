"""
Advanced Health Monitoring System
Comprehensive health checks for production deployment
"""

import time
import psutil
import sqlite3
from datetime import datetime
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum

# Safe imports
try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheck:
    """Individual health check result"""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    duration_ms: float

@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    available_memory_mb: float
    available_disk_gb: float
    uptime_seconds: float

class DatabaseHealthChecker:
    """Database connectivity and performance health checks"""
    
    def __init__(self, db_path: str = "framework.db"):
        self.db_path = db_path
    
    def check_connection(self) -> HealthCheck:
        """Test database connection"""
        start_time = time.time()
        
        try:
            with sqlite3.connect(self.db_path, timeout=5.0) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
            
            duration_ms = (time.time() - start_time) * 1000
            
            if result and result[0] == 1:
                return HealthCheck(
                    name="database_connection",
                    status=HealthStatus.HEALTHY,
                    message="Database connection successful",
                    details={"response_time_ms": round(duration_ms, 2)},
                    timestamp=datetime.utcnow(),
                    duration_ms=duration_ms
                )
            else:
                return HealthCheck(
                    name="database_connection",
                    status=HealthStatus.CRITICAL,
                    message="Database query returned unexpected result",
                    details={"result": result},
                    timestamp=datetime.utcnow(),
                    duration_ms=duration_ms
                )
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                name="database_connection",
                status=HealthStatus.CRITICAL,
                message=f"Database connection failed: {str(e)}",
                details={"error": str(e), "db_path": self.db_path},
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms
            )
    
    def check_performance(self) -> HealthCheck:
        """Test database performance"""
        start_time = time.time()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test query performance
            test_queries = [
                "SELECT COUNT(*) FROM framework_clients",
                "SELECT COUNT(*) FROM framework_projects", 
                "SELECT COUNT(*) FROM framework_epics"
            ]
            
            query_times = []
            for query in test_queries:
                query_start = time.time()
                cursor.execute(query)
                cursor.fetchone()
                query_times.append((time.time() - query_start) * 1000)
            
            conn.close()
            
            avg_query_time = sum(query_times) / len(query_times)
            max_query_time = max(query_times)
            duration_ms = (time.time() - start_time) * 1000
            
            # Performance thresholds
            if max_query_time > 1000:  # 1 second
                status = HealthStatus.CRITICAL
                message = "Database queries are too slow"
            elif avg_query_time > 100:  # 100ms average
                status = HealthStatus.WARNING
                message = "Database performance is degraded"
            else:
                status = HealthStatus.HEALTHY
                message = "Database performance is good"
            
            return HealthCheck(
                name="database_performance",
                status=status,
                message=message,
                details={
                    "avg_query_time_ms": round(avg_query_time, 2),
                    "max_query_time_ms": round(max_query_time, 2),
                    "query_times_ms": [round(t, 2) for t in query_times]
                },
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return HealthCheck(
                name="database_performance",
                status=HealthStatus.CRITICAL,
                message=f"Database performance check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                duration_ms=duration_ms
            )

class SystemResourceChecker:
    """System resource monitoring"""
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = psutil.boot_time()
        
        return SystemMetrics(
            cpu_percent=psutil.cpu_percent(interval=1),
            memory_percent=memory.percent,
            disk_percent=disk.percent,
            available_memory_mb=memory.available / (1024 * 1024),
            available_disk_gb=disk.free / (1024 * 1024 * 1024),
            uptime_seconds=time.time() - boot_time
        )
    
    def check_resources(self) -> List[HealthCheck]:
        """Check system resource health"""
        metrics = self.get_system_metrics()
        checks = []

        # CPU check
        start_cpu = time.time()
        if metrics.cpu_percent > 90:
            cpu_status = HealthStatus.CRITICAL
            cpu_message = "CPU usage is critically high"
        elif metrics.cpu_percent > 70:
            cpu_status = HealthStatus.WARNING
            cpu_message = "CPU usage is elevated"
        else:
            cpu_status = HealthStatus.HEALTHY
            cpu_message = "CPU usage is normal"
        
        checks.append(HealthCheck(
            name="system_cpu",
            status=cpu_status,
            message=cpu_message,
            details={"cpu_percent": metrics.cpu_percent},
            timestamp=datetime.utcnow(),
            duration_ms=(time.time() - start_cpu) * 1000
        ))

        # Memory check
        start_mem = time.time()
        if metrics.memory_percent > 90:
            memory_status = HealthStatus.CRITICAL
            memory_message = "Memory usage is critically high"
        elif metrics.memory_percent > 80:
            memory_status = HealthStatus.WARNING
            memory_message = "Memory usage is elevated"
        else:
            memory_status = HealthStatus.HEALTHY
            memory_message = "Memory usage is normal"
        
        checks.append(HealthCheck(
            name="system_memory",
            status=memory_status,
            message=memory_message,
            details={
                "memory_percent": metrics.memory_percent,
                "available_mb": round(metrics.available_memory_mb, 2)
            },
            timestamp=datetime.utcnow(),
            duration_ms=(time.time() - start_mem) * 1000
        ))

        # Disk check
        start_disk = time.time()
        if metrics.disk_percent > 95:
            disk_status = HealthStatus.CRITICAL
            disk_message = "Disk space is critically low"
        elif metrics.disk_percent > 85:
            disk_status = HealthStatus.WARNING
            disk_message = "Disk space is running low"
        else:
            disk_status = HealthStatus.HEALTHY
            disk_message = "Disk space is adequate"
        
        checks.append(HealthCheck(
            name="system_disk",
            status=disk_status,
            message=disk_message,
            details={
                "disk_percent": metrics.disk_percent,
                "available_gb": round(metrics.available_disk_gb, 2)
            },
            timestamp=datetime.utcnow(),
            duration_ms=(time.time() - start_disk) * 1000
        ))
        
        return checks

class ApplicationHealthChecker:
    """Application-specific health checks"""
    
    def check_streamlit_session(self) -> HealthCheck:
        """Check Streamlit session health"""
        start_time = time.time()
        
        if not STREAMLIT_AVAILABLE:
            return HealthCheck(
                name="streamlit_availability",
                status=HealthStatus.WARNING,
                message="Streamlit not available in current environment",
                details={"streamlit_available": False},
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000
            )
        
        try:
            # Test session state access
            if hasattr(st, 'session_state'):
                session_keys = len(st.session_state.keys()) if hasattr(st.session_state, 'keys') else 0
                return HealthCheck(
                    name="streamlit_session",
                    status=HealthStatus.HEALTHY,
                    message="Streamlit session is healthy",
                    details={"session_keys_count": session_keys},
                    timestamp=datetime.utcnow(),
                    duration_ms=(time.time() - start_time) * 1000
                )
            else:
                return HealthCheck(
                    name="streamlit_session",
                    status=HealthStatus.WARNING,
                    message="Streamlit session state not available",
                    details={"session_state_available": False},
                    timestamp=datetime.utcnow(),
                    duration_ms=(time.time() - start_time) * 1000
                )
                
        except Exception as e:
            return HealthCheck(
                name="streamlit_session",
                status=HealthStatus.CRITICAL,
                message=f"Streamlit session check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000
            )
    
    def check_cache_system(self) -> HealthCheck:
        """Check caching system health"""
        start_time = time.time()
        
        try:
            # Test cache functionality
            if STREAMLIT_AVAILABLE and hasattr(st, 'cache_data'):
                # Streamlit's new caching
                cache_status = HealthStatus.HEALTHY
                cache_message = "Streamlit cache system is available"
                cache_details = {"cache_type": "streamlit_cache_data"}
            else:
                cache_status = HealthStatus.WARNING
                cache_message = "Advanced caching not available"
                cache_details = {"cache_type": "none"}
            
            return HealthCheck(
                name="cache_system",
                status=cache_status,
                message=cache_message,
                details=cache_details,
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000
            )
            
        except Exception as e:
            return HealthCheck(
                name="cache_system",
                status=HealthStatus.CRITICAL,
                message=f"Cache system check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.utcnow(),
                duration_ms=(time.time() - start_time) * 1000
            )

class HealthMonitor:
    """Main health monitoring coordinator"""
    
    def __init__(self, db_path: str = "framework.db"):
        self.db_checker = DatabaseHealthChecker(db_path)
        self.system_checker = SystemResourceChecker()
        self.app_checker = ApplicationHealthChecker()
        self._last_check_time = None
        self._last_results = None
        self._check_interval = 30  # seconds
    
    def run_all_checks(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Run all health checks"""
        current_time = time.time()
        
        # Use cached results if recent and not forced
        if (not force_refresh and 
            self._last_check_time and 
            self._last_results and
            current_time - self._last_check_time < self._check_interval):
            return self._last_results
        
        start_time = time.time()
        all_checks = []
        
        # Database checks
        all_checks.append(self.db_checker.check_connection())
        all_checks.append(self.db_checker.check_performance())
        
        # System resource checks
        all_checks.extend(self.system_checker.check_resources())
        
        # Application checks
        all_checks.append(self.app_checker.check_streamlit_session())
        all_checks.append(self.app_checker.check_cache_system())
        
        # Determine overall status
        overall_status = self._determine_overall_status(all_checks)
        
        # Get system metrics
        system_metrics = self.system_checker.get_system_metrics()
        
        total_duration = (time.time() - start_time) * 1000
        
        results = {
            "overall_status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_duration_ms": round(total_duration, 2),
            "checks": [asdict(check) for check in all_checks],
            "system_metrics": asdict(system_metrics),
            "summary": {
                "total_checks": len(all_checks),
                "healthy": len([c for c in all_checks if c.status == HealthStatus.HEALTHY]),
                "warning": len([c for c in all_checks if c.status == HealthStatus.WARNING]),
                "critical": len([c for c in all_checks if c.status == HealthStatus.CRITICAL]),
                "unknown": len([c for c in all_checks if c.status == HealthStatus.UNKNOWN])
            }
        }
        
        # Cache results
        self._last_check_time = current_time
        self._last_results = results
        
        return results
    
    def _determine_overall_status(self, checks: List[HealthCheck]) -> HealthStatus:
        """Determine overall health status from individual checks"""
        if any(check.status == HealthStatus.CRITICAL for check in checks):
            return HealthStatus.CRITICAL
        elif any(check.status == HealthStatus.WARNING for check in checks):
            return HealthStatus.WARNING
        elif all(check.status == HealthStatus.HEALTHY for check in checks):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def get_readiness_status(self) -> Dict[str, Any]:
        """Kubernetes readiness probe endpoint"""
        critical_checks = [
            "database_connection",
            "system_memory",
            "system_disk"
        ]
        
        results = self.run_all_checks()
        
        # Check only critical components for readiness
        critical_results = [
            check for check in results["checks"] 
            if check["name"] in critical_checks
        ]
        
        is_ready = all(
            check["status"] in ["healthy", "warning"] 
            for check in critical_results
        )
        
        return {
            "ready": is_ready,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "critical_checks": critical_results
        }
    
    def get_liveness_status(self) -> Dict[str, Any]:
        """Kubernetes liveness probe endpoint"""
        # Simple liveness check - just verify we can respond
        return {
            "alive": True,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": time.time() - psutil.boot_time()
        }

# Global health monitor instance
health_monitor = HealthMonitor()

# Convenience functions for different probe types (JSON safe handled below)

def health_check_endpoint() -> Dict[str, Any]:
    """Main health check endpoint with JSON serialization"""
    raw_data = health_monitor.run_all_checks()
    
    # Ensure all data is JSON serializable
    def make_serializable(obj):
        if isinstance(obj, HealthStatus):
            return obj.value
        elif isinstance(obj, datetime):
            return obj.isoformat() + "Z"
        elif isinstance(obj, dict):
            return {k: make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [make_serializable(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return make_serializable(obj.__dict__)
        else:
            return obj
    
    return make_serializable(raw_data)

def readiness_probe() -> Dict[str, Any]:
    """Kubernetes readiness probe"""
    return health_monitor.get_readiness_status()

def liveness_probe() -> Dict[str, Any]:
    """Kubernetes liveness probe"""
    return health_monitor.get_liveness_status()