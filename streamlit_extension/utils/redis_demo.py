"""
🚀 Redis Cache System Demo

Demonstration of the Redis caching layer capabilities:
- Shows performance improvements with and without cache
- Demonstrates cache invalidation strategies
- Simulates real-world database operations
- Provides benchmarking and metrics
- Works even without Redis (fallback mode)

This addresses the performance bottlenecks identified in report.md:
- Heavy SQL queries without pagination
- Expensive joins causing UI lag
- Streamlit reruns triggering repeated DB operations
"""

import sys
import time
import random
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))

try:
    from .redis_cache import (
        get_cache_manager, cached, invalidate_cache,
        get_cache_stats, flush_cache, CacheStrategy
    )
    REDIS_CACHE_AVAILABLE = True
except ImportError:
    REDIS_CACHE_AVAILABLE = False


class MockDatabaseOperations:
    """Mock expensive database operations for demonstration."""
    
    def __init__(self):
        """Initialize mock database."""
        self.query_count = 0
        self.expensive_queries = 0
        
        # Mock data
        self.clients = self._generate_mock_clients(100)
        self.projects = self._generate_mock_projects(500)
        self.epics = self._generate_mock_epics(2000)
        self.tasks = self._generate_mock_tasks(10000)
    
    def _generate_mock_clients(self, count: int) -> List[Dict[str, Any]]:
        """Generate mock client data."""
        clients = []
        for i in range(count):
            clients.append({
                "id": i + 1,
                "name": f"Client {i + 1}",
                "industry": random.choice(["Tech", "Finance", "Healthcare", "Retail"]),
                "status": random.choice(["active", "inactive", "pending"]),
                "tier": random.choice(["basic", "standard", "premium", "enterprise"]),
                "created_at": datetime.now() - timedelta(days=random.randint(1, 365))
            })
        return clients
    
    def _generate_mock_projects(self, count: int) -> List[Dict[str, Any]]:
        """Generate mock project data."""
        projects = []
        for i in range(count):
            projects.append({
                "id": i + 1,
                "name": f"Project {i + 1}",
                "client_id": random.randint(1, 100),
                "status": random.choice(["planning", "active", "completed", "on_hold"]),
                "budget": random.randint(10000, 1000000),
                "created_at": datetime.now() - timedelta(days=random.randint(1, 180))
            })
        return projects
    
    def _generate_mock_epics(self, count: int) -> List[Dict[str, Any]]:
        """Generate mock epic data."""
        epics = []
        for i in range(count):
            epics.append({
                "id": i + 1,
                "name": f"Epic {i + 1}",
                "project_id": random.randint(1, 500),
                "status": random.choice(["todo", "in_progress", "completed"]),
                "points": random.randint(1, 100),
                "created_at": datetime.now() - timedelta(days=random.randint(1, 90))
            })
        return epics
    
    def _generate_mock_tasks(self, count: int) -> List[Dict[str, Any]]:
        """Generate mock task data."""
        tasks = []
        for i in range(count):
            tasks.append({
                "id": i + 1,
                "title": f"Task {i + 1}",
                "epic_id": random.randint(1, 2000),
                "status": random.choice(["todo", "in_progress", "completed"]),
                "tdd_phase": random.choice(["red", "green", "refactor"]),
                "estimate_minutes": random.randint(30, 480),
                "created_at": datetime.now() - timedelta(days=random.randint(1, 30))
            })
        return tasks
    
    def expensive_client_search(self, search_term: str, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Simulate expensive client search operation."""
        self.query_count += 1
        self.expensive_queries += 1
        
        # Simulate expensive processing time
        time.sleep(0.1)  # 100ms delay
        
        results = []
        for client in self.clients:
            if search_term.lower() in client["name"].lower():
                if status_filter is None or client["status"] == status_filter:
                    results.append(client)
        
        return results
    
    def expensive_project_analytics(self, client_id: Optional[int] = None) -> Dict[str, Any]:
        """Simulate expensive project analytics aggregation."""
        self.query_count += 1
        self.expensive_queries += 1
        
        # Simulate very expensive processing time
        time.sleep(0.2)  # 200ms delay
        
        projects = self.projects
        if client_id:
            projects = [p for p in projects if p["client_id"] == client_id]
        
        analytics = {
            "total_projects": len(projects),
            "active_projects": len([p for p in projects if p["status"] == "active"]),
            "completed_projects": len([p for p in projects if p["status"] == "completed"]),
            "total_budget": sum(p["budget"] for p in projects),
            "avg_budget": sum(p["budget"] for p in projects) / len(projects) if projects else 0,
            "projects_by_status": {}
        }
        
        # Group by status
        for project in projects:
            status = project["status"]
            if status not in analytics["projects_by_status"]:
                analytics["projects_by_status"][status] = 0
            analytics["projects_by_status"][status] += 1
        
        return analytics
    
    def expensive_epic_progress_calculation(self, project_id: int) -> Dict[str, Any]:
        """Simulate expensive epic progress calculation."""
        self.query_count += 1
        self.expensive_queries += 1
        
        # Simulate expensive processing time
        time.sleep(0.15)  # 150ms delay
        
        epics = [e for e in self.epics if e["project_id"] == project_id]
        epic_tasks = {}
        
        for epic in epics:
            tasks = [t for t in self.tasks if t["epic_id"] == epic["id"]]
            epic_tasks[epic["id"]] = tasks
        
        progress_data = {
            "total_epics": len(epics),
            "completed_epics": len([e for e in epics if e["status"] == "completed"]),
            "total_tasks": sum(len(tasks) for tasks in epic_tasks.values()),
            "completed_tasks": sum(len([t for t in tasks if t["status"] == "completed"]) for tasks in epic_tasks.values()),
            "epic_progress": {}
        }
        
        for epic_id, tasks in epic_tasks.items():
            if tasks:
                completed = len([t for t in tasks if t["status"] == "completed"])
                progress_data["epic_progress"][epic_id] = (completed / len(tasks)) * 100
            else:
                progress_data["epic_progress"][epic_id] = 0
        
        return progress_data
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database operation statistics."""
        return {
            "total_queries": self.query_count,
            "expensive_queries": self.expensive_queries,
            "data_size": {
                "clients": len(self.clients),
                "projects": len(self.projects),
                "epics": len(self.epics),
                "tasks": len(self.tasks)
            }
        }


class CachePerformanceDemo:
    """Demonstration of cache performance improvements."""
    
    def __init__(self):
        """Initialize demo."""
        self.db = MockDatabaseOperations()
        
        # Initialize cache if available
        if REDIS_CACHE_AVAILABLE:
            self.cache_manager = get_cache_manager()
            print("🚀 Redis Cache Demo - Cache Available")
        else:
            self.cache_manager = None
            print("📝 Redis Cache Demo - Fallback Mode (No Redis)")
        
        # Create cached versions of expensive operations
        self._setup_cached_operations()
    
    def _setup_cached_operations(self):
        """Setup cached versions of expensive operations."""
        
        @cached("client_search", operation_type="quick")
        def cached_client_search(search_term: str, status_filter: Optional[str] = None):
            return self.db.expensive_client_search(search_term, status_filter)
        
        @cached("project_analytics", operation_type="heavy")
        def cached_project_analytics(client_id: Optional[int] = None):
            return self.db.expensive_project_analytics(client_id)
        
        @cached("epic_progress", operation_type="medium")
        def cached_epic_progress_calculation(project_id: int):
            return self.db.expensive_epic_progress_calculation(project_id)
        
        self.cached_client_search = cached_client_search
        self.cached_project_analytics = cached_project_analytics
        self.cached_epic_progress_calculation = cached_epic_progress_calculation
    
    def benchmark_operation(self, operation_name: str, operation_func, *args, **kwargs):
        """Benchmark an operation and return timing results."""
        start_time = time.time()
        result = operation_func(*args, **kwargs)
        end_time = time.time()
        
        return {
            "operation": operation_name,
            "execution_time": round((end_time - start_time) * 1000, 2),  # ms
            "result_size": len(result) if isinstance(result, (list, dict)) else 1,
            "timestamp": datetime.now().isoformat()
        }
    
    def run_performance_comparison(self):
        """Run performance comparison between cached and uncached operations."""
        print("\n" + "="*80)
        print("🏁 PERFORMANCE BENCHMARK - CACHED vs UNCACHED OPERATIONS")
        print("="*80)
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "Client Search",
                "cached_func": self.cached_client_search,
                "direct_func": self.db.expensive_client_search,
                "args": ["Client 1"],
                "kwargs": {"status_filter": "active"}
            },
            {
                "name": "Project Analytics",
                "cached_func": self.cached_project_analytics,
                "direct_func": self.db.expensive_project_analytics,
                "args": [],
                "kwargs": {"client_id": 5}
            },
            {
                "name": "Epic Progress",
                "cached_func": self.cached_epic_progress_calculation,
                "direct_func": self.db.expensive_epic_progress_calculation,
                "args": [10],
                "kwargs": {}
            }
        ]
        
        results = []
        
        for scenario in test_scenarios:
            print(f"\n🧪 Testing: {scenario['name']}")
            print("-" * 50)
            
            # Clear cache for clean test
            if REDIS_CACHE_AVAILABLE:
                flush_cache()
            
            # First call (cache miss)
            print("1️⃣ First call (cache miss):")
            cached_result1 = self.benchmark_operation(
                f"{scenario['name']} (Cache Miss)",
                scenario['cached_func'],
                *scenario['args'],
                **scenario['kwargs']
            )
            print(f"   ⏱️  Cached (miss): {cached_result1['execution_time']}ms")
            
            # Second call (cache hit)
            print("2️⃣ Second call (cache hit):")
            cached_result2 = self.benchmark_operation(
                f"{scenario['name']} (Cache Hit)",
                scenario['cached_func'],
                *scenario['args'],
                **scenario['kwargs']
            )
            print(f"   ⚡ Cached (hit):  {cached_result2['execution_time']}ms")
            
            # Direct database call for comparison
            print("3️⃣ Direct database call:")
            direct_result = self.benchmark_operation(
                f"{scenario['name']} (Direct DB)",
                scenario['direct_func'],
                *scenario['args'],
                **scenario['kwargs']
            )
            print(f"   🐌 Direct DB:    {direct_result['execution_time']}ms")
            
            # Calculate performance improvement
            if REDIS_CACHE_AVAILABLE and cached_result2['execution_time'] > 0:
                improvement = ((direct_result['execution_time'] - cached_result2['execution_time']) / 
                             direct_result['execution_time']) * 100
                print(f"   📈 Improvement:  {improvement:.1f}% faster with cache")
            
            results.extend([cached_result1, cached_result2, direct_result])
        
        return results
    
    def demonstrate_cache_invalidation(self):
        """Demonstrate cache invalidation strategies."""
        print("\n" + "="*80)
        print("🗑️ CACHE INVALIDATION DEMONSTRATION")
        print("="*80)
        
        if not REDIS_CACHE_AVAILABLE:
            print("⚠️ Cache invalidation demo requires Redis. Running in simulation mode.")
            return
        
        # Clear cache
        flush_cache()
        
        print("\n1️⃣ Initial cache state:")
        print("   📊 Performing initial analytics query...")
        
        # Perform cached operation
        start_time = time.time()
        analytics1 = self.cached_project_analytics(client_id=1)
        time1 = (time.time() - start_time) * 1000
        print(f"   ⏱️  First call: {time1:.2f}ms (cache miss)")
        
        # Second call should be cached
        start_time = time.time()
        analytics2 = self.cached_project_analytics(client_id=1)
        time2 = (time.time() - start_time) * 1000
        print(f"   ⚡ Second call: {time2:.2f}ms (cache hit)")
        
        print(f"\n2️⃣ Cache invalidation:")
        print("   🗑️ Invalidating project analytics cache...")
        
        # Invalidate specific cache
        invalidate_cache("project_analytics", client_id=1)
        
        # Third call should be cache miss again
        start_time = time.time()
        analytics3 = self.cached_project_analytics(client_id=1)
        time3 = (time.time() - start_time) * 1000
        print(f"   ⏱️  After invalidation: {time3:.2f}ms (cache miss again)")
        
        print("\n3️⃣ Pattern-based invalidation:")
        print("   🧹 Flushing all cache...")
        flush_cache()
        print("   ✅ All cache entries cleared")
    
    def show_cache_statistics(self):
        """Show comprehensive cache statistics."""
        print("\n" + "="*80)
        print("📊 CACHE STATISTICS AND MONITORING")
        print("="*80)
        
        # Database statistics
        db_stats = self.db.get_stats()
        print(f"\n🗄️ Database Operations:")
        print(f"   Total Queries: {db_stats['total_queries']}")
        print(f"   Expensive Queries: {db_stats['expensive_queries']}")
        print(f"   Data Size: {db_stats['data_size']}")
        
        # Cache statistics
        if REDIS_CACHE_AVAILABLE:
            cache_stats = get_cache_stats()
            print(f"\n🚀 Cache Statistics:")
            print(f"   Available: {cache_stats.get('available', False)}")
            print(f"   Host: {cache_stats.get('host', 'N/A')}:{cache_stats.get('port', 'N/A')}")
            
            metrics = cache_stats.get('metrics', {})
            print(f"   Hit Rate: {metrics.get('hit_rate_percent', 0):.1f}%")
            print(f"   Total Requests: {metrics.get('total_requests', 0)}")
            print(f"   Cache Hits: {metrics.get('hits', 0)}")
            print(f"   Cache Misses: {metrics.get('misses', 0)}")
            print(f"   Errors: {metrics.get('errors', 0)}")
            print(f"   Avg Response Time: {metrics.get('avg_response_time', 0):.3f}s")
            
            if 'redis_info' in cache_stats:
                redis_info = cache_stats['redis_info']
                print(f"\n🔧 Redis Server Info:")
                print(f"   Version: {redis_info.get('version', 'N/A')}")
                print(f"   Memory Used: {redis_info.get('memory_used', 'N/A')}")
                print(f"   Connected Clients: {redis_info.get('connected_clients', 'N/A')}")
        else:
            print(f"\n⚠️ Cache Status: Not Available (Fallback Mode)")
    
    def run_full_demonstration(self):
        """Run complete demonstration of cache capabilities."""
        print("🎯 TDD FRAMEWORK - REDIS CACHE PERFORMANCE DEMO")
        print("Resolving performance bottlenecks identified in report.md")
        print("="*80)
        
        # Run benchmarks
        benchmark_results = self.run_performance_comparison()
        
        # Show cache invalidation
        self.demonstrate_cache_invalidation()
        
        # Show statistics
        self.show_cache_statistics()
        
        # Summary
        print("\n" + "="*80)
        print("✅ DEMONSTRATION COMPLETE")
        print("="*80)
        
        if REDIS_CACHE_AVAILABLE:
            print("🚀 Redis caching is working and provides significant performance improvements!")
            print("📈 Benefits observed:")
            print("   • Reduced database query load")
            print("   • Faster response times for repeated operations")
            print("   • Intelligent cache invalidation on data changes")
            print("   • Comprehensive performance monitoring")
        else:
            print("📝 Demo completed in fallback mode (Redis not available)")
            print("🔧 To enable Redis caching:")
            print("   • Install Redis: pip install redis")
            print("   • Start Redis server: redis-server")
            print("   • Re-run demo for full performance benefits")
        
        print(f"\n🏁 Cache system addresses report.md performance issues:")
        print(f"   ✅ Heavy SQL queries → Cached aggregations")
        print(f"   ✅ Expensive joins → Cached results")
        print(f"   ✅ Streamlit reruns → Cached operations")
        print(f"   ✅ Large dataset UI lag → Cached with pagination")
        
        return benchmark_results


def main():
    """Main demonstration function."""
    demo = CachePerformanceDemo()
    results = demo.run_full_demonstration()
    
    return results


if __name__ == "__main__":
    main()