#!/usr/bin/env python3
"""
🧪 Testes para as correções do Cache LRU

Valida especificamente as correções implementadas:
1. Cache LRU bug fix - sincronização memória/disco 
2. Cleanup de arquivos órfãos
3. Performance e consistência
"""

import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

try:
    from streamlit_extension.utils.cache import AdvancedCache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False


class TestCacheLRUFix:
    """Testa as correções críticas do cache LRU."""
    
    def setup_method(self):
        """Setup para cada teste."""
        if not CACHE_AVAILABLE:
            self.skip_test("Cache utilities not available")
            return
        
        # Create temporary directory for cache
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Initialize cache with small size for testing
        self.cache = AdvancedCache(
            max_size=3,  # Small size to trigger LRU eviction
            enable_disk_cache=True,
            max_disk_cache_mb=1
        )
        
        # Override cache_dir to use our temp directory
        self.cache.cache_dir = self.temp_dir
    
    def teardown_method(self):
        """Cleanup após cada teste."""
        if hasattr(self, 'temp_dir') and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def skip_test(self, reason):
        """Helper para pular testes quando dependências não disponíveis."""
        print(f"⚠️ SKIP: {reason}")
    
    def test_lru_eviction_removes_disk_files(self):
        """CRITICAL TEST: Verifica se evicção LRU remove arquivos do disco."""
        if not CACHE_AVAILABLE:
            self.skip_test("Cache not available")
            return
        
        print("\n🧪 Testing LRU eviction removes disk files...")
        
        # Fill cache to capacity
        self.cache.set("key1", "value1", ttl=3600)
        self.cache.set("key2", "value2", ttl=3600)
        self.cache.set("key3", "value3", ttl=3600)
        
        # Verify files exist on disk
        disk_files_before = list(self.temp_dir.glob("*.cache"))
        assert len(disk_files_before) == 3, f"Expected 3 files, got {len(disk_files_before)}"
        
        # Add one more item to trigger LRU eviction
        self.cache.set("key4", "value4", ttl=3600)
        
        # Verify that LRU item was evicted from memory
        assert "key1" not in self.cache._memory_cache, "key1 should be evicted from memory"
        
        # CRITICAL: Verify that disk file was also removed
        disk_files_after = list(self.temp_dir.glob("*.cache"))
        disk_file_names = [f.stem for f in disk_files_after]
        
        assert "key1" not in disk_file_names, "key1.cache should be removed from disk"
        assert len(disk_files_after) == 3, f"Expected 3 files after eviction, got {len(disk_files_after)}"
        
        print("   ✅ LRU eviction correctly removes disk files")
    
    def test_lru_evicted_data_not_recovered(self):
        """CRITICAL TEST: Dados evicted por LRU não devem ser recuperados do disco."""
        if not CACHE_AVAILABLE:
            self.skip_test("Cache not available")
            return
        
        print("\n🧪 Testing evicted data is not recovered...")
        
        # Fill cache and trigger eviction
        self.cache.set("old_key", "old_value", ttl=3600)
        self.cache.set("key2", "value2", ttl=3600)
        self.cache.set("key3", "value3", ttl=3600)
        self.cache.set("key4", "value4", ttl=3600)  # This should evict old_key
        
        # Try to get evicted key - should return None
        result = self.cache.get("old_key")
        assert result is None, f"Expected None for evicted key, got {result}"
        
        print("   ✅ Evicted data correctly returns None")
    
    def test_cleanup_orphaned_files(self):
        """Testa limpeza de arquivos órfãos."""
        if not CACHE_AVAILABLE:
            self.skip_test("Cache not available")
            return
        
        print("\n🧪 Testing cleanup of orphaned cache files...")
        
        # Create some cache entries
        self.cache.set("key1", "value1", ttl=3600)
        self.cache.set("key2", "value2", ttl=3600)
        
        # Manually create orphaned file
        orphan_file = self.temp_dir / "orphan_key.cache"
        orphan_file.write_text("orphaned data")
        
        # Verify orphan file exists
        assert orphan_file.exists(), "Orphan file should exist"
        
        # Run cleanup
        removed_count = self.cache.cleanup_orphaned_cache_files()
        
        # Verify orphan was removed
        assert not orphan_file.exists(), "Orphan file should be removed"
        assert removed_count == 1, f"Expected 1 removed file, got {removed_count}"
        
        # Verify legitimate files still exist
        # Note: Keys are hashed for security, so we need to calculate the expected hashes
        import hashlib
        key1_hash = hashlib.sha256("key1".encode('utf-8')).hexdigest()
        key2_hash = hashlib.sha256("key2".encode('utf-8')).hexdigest()
        key1_file = self.temp_dir / f"{key1_hash}.cache"
        key2_file = self.temp_dir / f"{key2_hash}.cache"
        assert key1_file.exists(), f"Hashed key1 file ({key1_hash}.cache) should still exist"
        assert key2_file.exists(), f"Hashed key2 file ({key2_hash}.cache) should still exist"
        
        print("   ✅ Orphaned files cleanup works correctly")
    
    def test_cache_consistency_after_eviction(self):
        """Testa consistência do cache após evicções múltiplas."""
        if not CACHE_AVAILABLE:
            self.skip_test("Cache not available")
            return
        
        print("\n🧪 Testing cache consistency after multiple evictions...")
        
        # Perform multiple evictions
        for i in range(10):
            self.cache.set(f"key_{i}", f"value_{i}", ttl=3600)
        
        # Verify only max_size entries remain
        assert len(self.cache._memory_cache) <= self.cache.max_size
        
        # Verify disk files match memory cache
        disk_files = list(self.temp_dir.glob("*.cache"))
        disk_keys = [f.stem for f in disk_files]
        memory_keys = list(self.cache._memory_cache.keys())
        
        # All memory keys should have corresponding disk files
        for key in memory_keys:
            assert key in disk_keys, f"Memory key {key} missing from disk"
        
        print(f"   ✅ Cache consistent: {len(memory_keys)} memory entries, {len(disk_keys)} disk files")
    
    def test_performance_benchmark(self):
        """Benchmark de performance das operações de cache."""
        if not CACHE_AVAILABLE:
            self.skip_test("Cache not available")
            return
        
        print("\n🧪 Testing cache performance...")
        
        # Test set performance
        start_time = time.time()
        for i in range(100):
            self.cache.set(f"perf_key_{i}", f"value_{i}", ttl=3600)
        set_time = time.time() - start_time
        
        # Test get performance
        start_time = time.time()
        for i in range(90, 100):  # Get recent entries
            self.cache.get(f"perf_key_{i}")
        get_time = time.time() - start_time
        
        print(f"   📊 SET performance: {set_time:.3f}s for 100 ops ({set_time*10:.1f}ms/op)")
        print(f"   📊 GET performance: {get_time:.3f}s for 10 ops ({get_time*100:.1f}ms/op)")
        
        # Performance should be reasonable
        assert set_time < 1.0, f"SET operations too slow: {set_time:.3f}s"
        assert get_time < 0.1, f"GET operations too slow: {get_time:.3f}s"
        
        print("   ✅ Performance benchmarks passed")


def validate_cache_lru_fixes():
    """Run all cache LRU fix tests."""
    print("🔧 CACHE LRU FIXES TEST SUITE")
    print("=" * 50)
    
    if not CACHE_AVAILABLE:
        print("⚠️ Cache utilities not available - skipping tests")
        return False
    
    test_instance = TestCacheLRUFix()
    
    tests = [
        test_instance.test_lru_eviction_removes_disk_files,
        test_instance.test_lru_evicted_data_not_recovered,
        test_instance.test_cleanup_orphaned_files,
        test_instance.test_cache_consistency_after_eviction,
        test_instance.test_performance_benchmark
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            test_instance.setup_method()
            test_func()  # Test methods now use assertions instead of return values
            passed += 1
            test_instance.teardown_method()
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            test_instance.teardown_method()
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("✅ ALL CACHE LRU FIXES VALIDATED")
        return True
    else:
        print("⚠️ Some tests failed - fixes need review")
        return False


if __name__ == "__main__":
    success = validate_cache_lru_fixes()
    exit(0 if success else 1)