"""
Tests for performance monitoring and optimization.
"""

import pytest
import time
import tempfile
from pathlib import Path

from security_assistant.performance import (
    PerformanceMetrics,
    PerformanceMonitor,
    PerformanceCache,
    CacheEntry,
    ResourceMonitor,
    PerformanceOptimizer,
    cache_key,
)


class TestPerformanceMetrics:
    """Test PerformanceMetrics class."""
    
    def test_metrics_creation(self):
        """Test creating performance metrics."""
        metrics = PerformanceMetrics(
            operation="test_op",
            start_time=time.time()
        )
        
        assert metrics.operation == "test_op"
        assert metrics.start_time > 0
        assert metrics.end_time is None
        assert metrics.duration is None
        assert metrics.success is True
    
    def test_metrics_finish(self):
        """Test finishing metrics collection."""
        metrics = PerformanceMetrics(
            operation="test_op",
            start_time=time.time()
        )
        
        time.sleep(0.1)
        metrics.finish(success=True)
        
        assert metrics.end_time is not None
        assert metrics.duration >= 0.1
        assert metrics.success is True
        assert metrics.error is None
    
    def test_metrics_finish_with_error(self):
        """Test finishing metrics with error."""
        metrics = PerformanceMetrics(
            operation="test_op",
            start_time=time.time()
        )
        
        metrics.finish(success=False, error="Test error")
        
        assert metrics.success is False
        assert metrics.error == "Test error"
    
    def test_metrics_to_dict(self):
        """Test converting metrics to dictionary."""
        metrics = PerformanceMetrics(
            operation="test_op",
            start_time=time.time(),
            metadata={'key': 'value'}
        )
        metrics.finish()
        
        data = metrics.to_dict()
        
        assert isinstance(data, dict)
        assert data['operation'] == "test_op"
        assert 'duration' in data
        assert data['metadata'] == {'key': 'value'}


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""
    
    def test_monitor_creation(self):
        """Test creating performance monitor."""
        monitor = PerformanceMonitor(enabled=True)
        
        assert monitor.enabled is True
        assert len(monitor.metrics) == 0
    
    def test_start_operation(self):
        """Test starting operation monitoring."""
        monitor = PerformanceMonitor()
        
        metrics = monitor.start_operation("test_op", key="value")
        
        assert metrics.operation == "test_op"
        assert metrics.metadata == {'key': 'value'}
        assert len(monitor.metrics) == 1
    
    def test_disabled_monitor(self):
        """Test disabled monitor."""
        monitor = PerformanceMonitor(enabled=False)
        
        metrics = monitor.start_operation("test_op")
        
        assert metrics.operation == "test_op"
        assert len(monitor.metrics) == 0
    
    def test_get_metrics(self):
        """Test getting collected metrics."""
        monitor = PerformanceMonitor()
        
        monitor.start_operation("op1")
        monitor.start_operation("op2")
        monitor.start_operation("op1")
        
        all_metrics = monitor.get_metrics()
        assert len(all_metrics) == 3
        
        op1_metrics = monitor.get_metrics("op1")
        assert len(op1_metrics) == 2
    
    def test_get_summary(self):
        """Test getting performance summary."""
        monitor = PerformanceMonitor()
        
        # Add some metrics
        m1 = monitor.start_operation("op1")
        time.sleep(0.05)
        m1.finish()
        
        m2 = monitor.start_operation("op1")
        time.sleep(0.05)
        m2.finish()
        
        summary = monitor.get_summary()
        
        assert 'op1' in summary
        assert summary['op1']['count'] == 2
        assert summary['op1']['avg_duration'] > 0
        assert summary['op1']['success_count'] == 2
    
    def test_clear_metrics(self):
        """Test clearing metrics."""
        monitor = PerformanceMonitor()
        
        monitor.start_operation("op1")
        monitor.start_operation("op2")
        
        assert len(monitor.metrics) == 2
        
        monitor.clear()
        
        assert len(monitor.metrics) == 0
    
    def test_export_metrics(self, tmp_path):
        """Test exporting metrics to file."""
        monitor = PerformanceMonitor()
        
        m = monitor.start_operation("test_op")
        time.sleep(0.01)
        m.finish()
        
        output_file = tmp_path / "metrics.json"
        monitor.export_metrics(output_file)
        
        assert output_file.exists()
        
        import json
        data = json.loads(output_file.read_text())
        
        assert 'timestamp' in data
        assert 'metrics' in data
        assert 'summary' in data


class TestCacheEntry:
    """Test CacheEntry class."""
    
    def test_cache_entry_creation(self):
        """Test creating cache entry."""
        entry = CacheEntry("value", ttl=60)
        
        assert entry.value == "value"
        assert entry.ttl == 60
        assert entry.hits == 0
        assert not entry.is_expired()
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration."""
        entry = CacheEntry("value", ttl=0.1)
        
        assert not entry.is_expired()
        
        time.sleep(0.15)
        
        assert entry.is_expired()
    
    def test_cache_entry_no_ttl(self):
        """Test cache entry without TTL."""
        entry = CacheEntry("value", ttl=None)
        
        time.sleep(0.1)
        
        assert not entry.is_expired()
    
    def test_cache_entry_get(self):
        """Test getting value from cache entry."""
        entry = CacheEntry("value")
        
        assert entry.hits == 0
        
        value = entry.get()
        
        assert value == "value"
        assert entry.hits == 1


class TestPerformanceCache:
    """Test PerformanceCache class."""
    
    def test_cache_creation(self):
        """Test creating cache."""
        cache = PerformanceCache(max_size=100, default_ttl=3600)
        
        assert cache.max_size == 100
        assert cache.default_ttl == 3600
    
    def test_cache_set_get(self):
        """Test setting and getting cache values."""
        cache = PerformanceCache()
        
        cache.set("key1", "value1")
        
        value = cache.get("key1")
        
        assert value == "value1"
    
    def test_cache_miss(self):
        """Test cache miss."""
        cache = PerformanceCache()
        
        value = cache.get("nonexistent")
        
        assert value is None
    
    def test_cache_expiration(self):
        """Test cache entry expiration."""
        cache = PerformanceCache()
        
        cache.set("key1", "value1", ttl=0.1)
        
        assert cache.get("key1") == "value1"
        
        time.sleep(0.15)
        
        assert cache.get("key1") is None
    
    def test_cache_delete(self):
        """Test deleting cache entry."""
        cache = PerformanceCache()
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        cache.delete("key1")
        assert cache.get("key1") is None
    
    def test_cache_clear(self):
        """Test clearing cache."""
        cache = PerformanceCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = PerformanceCache()
        
        cache.set("key1", "value1")
        cache.get("key1")  # hit
        cache.get("key1")  # hit
        cache.get("key2")  # miss
        
        stats = cache.get_stats()
        
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['size'] == 1
        assert stats['hit_rate'] == 2/3
    
    def test_cache_eviction(self):
        """Test LRU eviction."""
        cache = PerformanceCache(max_size=2)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Access key1 to increase its hits
        cache.get("key1")
        cache.get("key1")
        
        # Add key3, should evict key2 (lower hits)
        cache.set("key3", "value3")
        
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"


    def test_lru_eviction_logic_diverges_from_lfu(self):
        """Test LRU eviction where it differs from LFU."""
        cache = PerformanceCache(max_size=3)

        cache.set("a", 1)  # Will become LRU but have most hits
        time.sleep(0.02)
        cache.set("b", 2)
        time.sleep(0.02)
        cache.set("c", 3)

        # Access 'a' twice to give it the most hits
        cache.get("a")
        cache.get("a")

        # Now access 'b' and 'c' to make 'a' the least recently used
        time.sleep(0.02)
        cache.get("b")
        time.sleep(0.02)
        cache.get("c")

        # At this point:
        # - 'a' has 2 hits. 'b' and 'c' have 1 hit.
        # - The last access for 'a' is the oldest.
        # LFU policy would evict 'b' or 'c'.
        # LRU policy must evict 'a'.

        # Add a new item to trigger eviction
        cache.set("d", 4)

        # The current LFU logic will evict 'b' or 'c', so 'a' will exist.
        # This assertion will fail with the current code.
        assert cache.get("a") is None

        # These assertions confirm the other items are present.
        assert cache.get("b") == 2
        assert cache.get("c") == 3
        assert cache.get("d") == 4
    
    def test_cache_persistence(self, tmp_path):
        """Test cache persistence."""
        cache_file = tmp_path / "cache.pkl"
        
        # Create cache and add data
        cache1 = PerformanceCache(persist_path=cache_file)
        cache1.set("key1", "value1")
        cache1.save()
        
        # Load cache from file
        cache2 = PerformanceCache(persist_path=cache_file)
        
        assert cache2.get("key1") == "value1"


class TestCacheKey:
    """Test cache_key function."""
    
    def test_cache_key_args(self):
        """Test cache key with positional args."""
        key1 = cache_key(1, 2, 3)
        key2 = cache_key(1, 2, 3)
        key3 = cache_key(1, 2, 4)
        
        assert key1 == key2
        assert key1 != key3
    
    def test_cache_key_kwargs(self):
        """Test cache key with keyword args."""
        key1 = cache_key(a=1, b=2)
        key2 = cache_key(b=2, a=1)  # Different order
        key3 = cache_key(a=1, b=3)
        
        assert key1 == key2  # Order doesn't matter
        assert key1 != key3
    
    def test_cache_key_mixed(self):
        """Test cache key with mixed args."""
        key1 = cache_key(1, 2, c=3, d=4)
        key2 = cache_key(1, 2, d=4, c=3)
        
        assert key1 == key2


class TestResourceMonitor:
    """Test ResourceMonitor class."""
    
    def test_resource_monitor_creation(self):
        """Test creating resource monitor."""
        monitor = ResourceMonitor()
        
        assert monitor is not None
    
    def test_get_memory_usage(self):
        """Test getting memory usage."""
        monitor = ResourceMonitor()
        
        memory = monitor.get_memory_usage()
        
        assert 'rss' in memory
        assert 'vms' in memory
        assert 'percent' in memory
        assert 'delta' in memory
        assert memory['rss'] > 0
    
    def test_get_cpu_usage(self):
        """Test getting CPU usage."""
        monitor = ResourceMonitor()
        
        cpu = monitor.get_cpu_usage()
        
        assert 'percent' in cpu
        assert 'num_threads' in cpu
        assert cpu['num_threads'] > 0
    
    def test_get_io_stats(self):
        """Test getting I/O statistics."""
        monitor = ResourceMonitor()
        
        io_stats = monitor.get_io_stats()
        
        # I/O stats may not be available on all platforms
        assert isinstance(io_stats, dict)
    
    def test_get_summary(self):
        """Test getting resource summary."""
        monitor = ResourceMonitor()
        
        summary = monitor.get_summary()
        
        assert 'memory' in summary
        assert 'cpu' in summary
        assert 'io' in summary
        assert 'timestamp' in summary


class TestPerformanceOptimizer:
    """Test PerformanceOptimizer class."""
    
    def test_optimizer_creation(self, tmp_path):
        """Test creating optimizer."""
        optimizer = PerformanceOptimizer(cache_dir=tmp_path)
        
        assert optimizer.cache_dir == tmp_path
        assert optimizer.scan_cache is not None
        assert optimizer.dependency_cache is not None
    
    def test_optimize_scan_results(self, tmp_path):
        """Test optimizing scan results."""
        optimizer = PerformanceOptimizer(cache_dir=tmp_path)
        
        results = [
            {'file': 'test.py', 'line': 10, 'rule_id': 'R1'},
            {'file': 'test.py', 'line': 10, 'rule_id': 'R1'},  # Duplicate
            {'file': 'test.py', 'line': 20, 'rule_id': 'R2'},
        ]
        
        optimized = optimizer.optimize_scan_results(results)
        
        assert len(optimized) == 2
    
    def test_cache_scan_results(self, tmp_path):
        """Test caching scan results."""
        optimizer = PerformanceOptimizer(cache_dir=tmp_path)
        
        results = {'findings': []}
        
        optimizer.cache_scan_results("target", "bandit", results)
        
        cached = optimizer.get_cached_scan("target", "bandit")
        
        assert cached == results
    
    def test_get_cached_scan_miss(self, tmp_path):
        """Test cache miss for scan results."""
        optimizer = PerformanceOptimizer(cache_dir=tmp_path)
        
        cached = optimizer.get_cached_scan("target", "bandit")
        
        assert cached is None
    
    def test_save_caches(self, tmp_path):
        """Test saving caches."""
        optimizer = PerformanceOptimizer(cache_dir=tmp_path)
        
        optimizer.cache_scan_results("target", "bandit", {'findings': []})
        optimizer.save_caches()
        
        # Check files exist
        assert (tmp_path / 'scan_cache.pkl').exists()
        assert (tmp_path / 'dependency_cache.pkl').exists()
    
    def test_get_performance_report(self, tmp_path):
        """Test getting performance report."""
        optimizer = PerformanceOptimizer(cache_dir=tmp_path)
        
        # Add some activity
        optimizer.cache_scan_results("target", "bandit", {'findings': []})
        optimizer.get_cached_scan("target", "bandit")
        
        report = optimizer.get_performance_report()
        
        assert 'metrics_summary' in report
        assert 'scan_cache_stats' in report
        assert 'dependency_cache_stats' in report
        assert 'resource_usage' in report
        assert 'timestamp' in report
