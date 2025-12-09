"""
Performance optimization examples.

This module demonstrates how to use the performance monitoring
and optimization features.
"""

import time
from pathlib import Path

from security_assistant.performance import (
    PerformanceCache,
    PerformanceMonitor,
    PerformanceOptimizer,
    ResourceMonitor,
    cached,
    export_metrics,
    get_monitor,
    get_performance_summary,
    profile,
)


def example_1_basic_profiling():
    """Example 1: Basic performance profiling."""
    print("\n" + "="*70)
    print("Example 1: Basic Performance Profiling")
    print("="*70)
    
    monitor = PerformanceMonitor()
    
    # Profile an operation
    metrics = monitor.start_operation("scan_files")
    
    # Simulate work
    time.sleep(0.1)
    
    # Finish profiling
    metrics.finish(success=True)
    
    # Get summary
    summary = monitor.get_summary()
    
    print(f"\nOperation: {metrics.operation}")
    print(f"Duration: {metrics.duration:.3f}s")
    print(f"Memory delta: {metrics.memory_delta:,} bytes")
    print("\nSummary:")
    for op, stats in summary.items():
        print(f"  {op}:")
        print(f"    Count: {stats['count']}")
        print(f"    Avg duration: {stats['avg_duration']:.3f}s")
        print(f"    Success rate: {stats['success_count']}/{stats['count']}")


def example_2_decorator_profiling():
    """Example 2: Using @profile decorator."""
    print("\n" + "="*70)
    print("Example 2: Decorator-based Profiling")
    print("="*70)
    
    @profile()
    def expensive_operation(n):
        """Simulate expensive operation."""
        total = 0
        for i in range(n):
            total += i ** 2
        return total
    
    # Run the function multiple times
    for i in range(3):
        result = expensive_operation(1000000)
    
    # Get performance summary
    summary = get_performance_summary()
    
    print("\nPerformance Summary:")
    for op, stats in summary.items():
        print(f"\n{op}:")
        print(f"  Executions: {stats['count']}")
        print(f"  Avg duration: {stats['avg_duration']:.4f}s")
        print(f"  Min duration: {stats['min_duration']:.4f}s")
        print(f"  Max duration: {stats['max_duration']:.4f}s")


def example_3_caching():
    """Example 3: Result caching."""
    print("\n" + "="*70)
    print("Example 3: Result Caching")
    print("="*70)
    
    cache = PerformanceCache(max_size=100, default_ttl=3600)
    
    @cached(cache=cache)
    def expensive_computation(x, y):
        """Simulate expensive computation."""
        time.sleep(0.1)  # Simulate work
        return x ** y
    
    # First call (cache miss)
    print("\nFirst call (cache miss):")
    start = time.time()
    result1 = expensive_computation(2, 10)
    duration1 = time.time() - start
    print(f"  Result: {result1}")
    print(f"  Duration: {duration1:.3f}s")
    
    # Second call (cache hit)
    print("\nSecond call (cache hit):")
    start = time.time()
    result2 = expensive_computation(2, 10)
    duration2 = time.time() - start
    print(f"  Result: {result2}")
    print(f"  Duration: {duration2:.6f}s")
    if duration2 > 0:
        print(f"  Speedup: {duration1/duration2:.1f}x")
    else:
        print("  Speedup: >1000x (instant)")
    
    # Cache statistics
    stats = cache.get_stats()
    print("\nCache Statistics:")
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Hit rate: {stats['hit_rate']:.1%}")
    print(f"  Size: {stats['size']}/{stats['max_size']}")


def example_4_resource_monitoring():
    """Example 4: Resource monitoring."""
    print("\n" + "="*70)
    print("Example 4: Resource Monitoring")
    print("="*70)
    
    monitor = ResourceMonitor()
    
    # Get initial state
    print("\nInitial state:")
    memory = monitor.get_memory_usage()
    print(f"  Memory RSS: {memory['rss'] / 1024 / 1024:.1f} MB")
    print(f"  Memory %: {memory['percent']:.1f}%")
    
    cpu = monitor.get_cpu_usage()
    print(f"  CPU %: {cpu['percent']:.1f}%")
    print(f"  Threads: {cpu['num_threads']}")
    
    # Allocate memory
    print("\nAllocating 10MB...")
    data = bytearray(10 * 1024 * 1024)
    
    # Get updated state
    memory = monitor.get_memory_usage()
    print(f"  Memory delta: {memory['delta'] / 1024 / 1024:.1f} MB")
    
    # Get full summary
    summary = monitor.get_summary()
    print("\nFull Summary:")
    print(f"  Timestamp: {summary['timestamp']}")
    print(f"  Memory RSS: {summary['memory']['rss'] / 1024 / 1024:.1f} MB")
    print(f"  CPU %: {summary['cpu']['percent']:.1f}%")


def example_5_performance_optimizer():
    """Example 5: Using PerformanceOptimizer."""
    print("\n" + "="*70)
    print("Example 5: Performance Optimizer")
    print("="*70)
    
    # Create optimizer with temp cache dir
    import tempfile
    cache_dir = Path(tempfile.mkdtemp())
    optimizer = PerformanceOptimizer(cache_dir=cache_dir)
    
    # Simulate scan results with duplicates
    results = [
        {'file': 'test.py', 'line': 10, 'rule_id': 'B101', 'severity': 'HIGH'},
        {'file': 'test.py', 'line': 10, 'rule_id': 'B101', 'severity': 'HIGH'},  # Duplicate
        {'file': 'test.py', 'line': 20, 'rule_id': 'B102', 'severity': 'MEDIUM'},
        {'file': 'app.py', 'line': 5, 'rule_id': 'B103', 'severity': 'LOW'},
        {'file': 'app.py', 'line': 5, 'rule_id': 'B103', 'severity': 'LOW'},  # Duplicate
    ]
    
    print(f"\nOriginal results: {len(results)} findings")
    
    # Optimize (deduplicate)
    optimized = optimizer.optimize_scan_results(results)
    
    print(f"Optimized results: {len(optimized)} findings")
    print(f"Removed: {len(results) - len(optimized)} duplicates")
    
    # Cache scan results
    print("\nCaching scan results...")
    optimizer.cache_scan_results("src/", "bandit", {'findings': optimized})
    
    # Retrieve from cache
    cached = optimizer.get_cached_scan("src/", "bandit")
    print(f"Retrieved from cache: {len(cached['findings'])} findings")
    
    # Get performance report
    report = optimizer.get_performance_report()
    
    print("\nPerformance Report:")
    print("  Scan cache stats:")
    print(f"    Hits: {report['scan_cache_stats']['hits']}")
    print(f"    Misses: {report['scan_cache_stats']['misses']}")
    print(f"    Size: {report['scan_cache_stats']['size']}")
    
    print("  Resource usage:")
    print(f"    Memory: {report['resource_usage']['memory']['rss'] / 1024 / 1024:.1f} MB")
    print(f"    CPU: {report['resource_usage']['cpu']['percent']:.1f}%")
    
    # Save caches
    optimizer.save_caches()
    print(f"\nCaches saved to: {cache_dir}")


def example_6_export_metrics():
    """Example 6: Exporting metrics."""
    print("\n" + "="*70)
    print("Example 6: Exporting Metrics")
    print("="*70)
    
    monitor = get_monitor()
    monitor.clear()
    
    # Run some operations
    @profile()
    def operation_a():
        time.sleep(0.05)
    
    @profile()
    def operation_b():
        time.sleep(0.03)
    
    # Execute operations
    for _ in range(3):
        operation_a()
        operation_b()
    
    # Export metrics
    import tempfile
    output_file = Path(tempfile.mktemp(suffix='.json'))
    export_metrics(output_file)
    
    print(f"\nMetrics exported to: {output_file}")
    print(f"File size: {output_file.stat().st_size} bytes")
    
    # Read and display
    import json
    data = json.loads(output_file.read_text())
    
    print("\nExported data:")
    print(f"  Timestamp: {data['timestamp']}")
    print(f"  Total metrics: {len(data['metrics'])}")
    print("  Operations:")
    for op, stats in data['summary'].items():
        print(f"    {op}: {stats['count']} executions, avg {stats['avg_duration']:.4f}s")


def example_7_cache_persistence():
    """Example 7: Cache persistence."""
    print("\n" + "="*70)
    print("Example 7: Cache Persistence")
    print("="*70)
    
    import tempfile
    cache_file = Path(tempfile.mktemp(suffix='.pkl'))
    
    # Create cache and add data
    print("\nCreating cache...")
    cache1 = PerformanceCache(persist_path=cache_file)
    cache1.set("key1", "value1")
    cache1.set("key2", {"data": [1, 2, 3]})
    cache1.set("key3", 42)
    
    print(f"Added {cache1.get_stats()['size']} entries")
    
    # Save to disk
    cache1.save()
    print(f"Saved to: {cache_file}")
    print(f"File size: {cache_file.stat().st_size} bytes")
    
    # Load from disk
    print("\nLoading cache from disk...")
    cache2 = PerformanceCache(persist_path=cache_file)
    
    print(f"Loaded {cache2.get_stats()['size']} entries")
    print(f"  key1: {cache2.get('key1')}")
    print(f"  key2: {cache2.get('key2')}")
    print(f"  key3: {cache2.get('key3')}")


def example_8_ttl_expiration():
    """Example 8: TTL and expiration."""
    print("\n" + "="*70)
    print("Example 8: TTL and Expiration")
    print("="*70)
    
    cache = PerformanceCache(default_ttl=1)  # 1 second TTL
    
    # Add entries with different TTLs
    cache.set("short_lived", "expires in 0.5s", ttl=0.5)
    cache.set("medium_lived", "expires in 1s")  # Uses default
    cache.set("long_lived", "expires in 5s", ttl=5)
    cache.set("immortal", "never expires", ttl=None)
    
    print("\nInitial state:")
    print(f"  short_lived: {cache.get('short_lived')}")
    print(f"  medium_lived: {cache.get('medium_lived')}")
    print(f"  long_lived: {cache.get('long_lived')}")
    print(f"  immortal: {cache.get('immortal')}")
    
    # Wait 0.6 seconds
    print("\nAfter 0.6 seconds:")
    time.sleep(0.6)
    print(f"  short_lived: {cache.get('short_lived')}")  # Expired
    print(f"  medium_lived: {cache.get('medium_lived')}")  # Still valid
    print(f"  long_lived: {cache.get('long_lived')}")  # Still valid
    print(f"  immortal: {cache.get('immortal')}")  # Still valid
    
    # Wait another 0.5 seconds
    print("\nAfter 1.1 seconds total:")
    time.sleep(0.5)
    print(f"  medium_lived: {cache.get('medium_lived')}")  # Expired
    print(f"  long_lived: {cache.get('long_lived')}")  # Still valid
    print(f"  immortal: {cache.get('immortal')}")  # Still valid
    
    stats = cache.get_stats()
    print("\nCache stats:")
    print(f"  Expirations: {stats['expirations']}")
    print(f"  Current size: {stats['size']}")


def main():
    """Run all examples."""
    print("\n" + "="*70)
    print("PERFORMANCE OPTIMIZATION EXAMPLES")
    print("="*70)
    
    examples = [
        example_1_basic_profiling,
        example_2_decorator_profiling,
        example_3_caching,
        example_4_resource_monitoring,
        example_5_performance_optimizer,
        example_6_export_metrics,
        example_7_cache_persistence,
        example_8_ttl_expiration,
    ]
    
    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"\n❌ Error in {example.__name__}: {e}")
    
    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETED")
    print("="*70)


if __name__ == "__main__":
    main()
