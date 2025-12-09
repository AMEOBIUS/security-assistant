"""
Performance monitoring and optimization module.

This module provides:
- Performance profiling
- Metrics collection
- Caching layer
- Resource management
- Performance monitoring
"""

import functools
import hashlib
import json
import logging
import pickle
import threading
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single operation."""

    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_before: Optional[int] = None
    memory_after: Optional[int] = None
    memory_delta: Optional[int] = None
    cpu_percent: Optional[float] = None
    success: bool = True
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def finish(self, success: bool = True, error: Optional[str] = None):
        """Mark operation as finished."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error = error

        # Capture final memory
        process = psutil.Process()
        self.memory_after = process.memory_info().rss
        if self.memory_before:
            self.memory_delta = self.memory_after - self.memory_before

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class PerformanceMonitor:
    """Monitor and collect performance metrics."""

    def __init__(self, enabled: bool = True):
        """
        Initialize performance monitor.

        Args:
            enabled: Whether monitoring is enabled
        """
        self.enabled = enabled
        self.metrics: List[PerformanceMetrics] = []
        self._lock = threading.Lock()
        self._process = psutil.Process()

    def start_operation(self, operation: str, **metadata) -> PerformanceMetrics:
        """
        Start monitoring an operation.

        Args:
            operation: Operation name
            **metadata: Additional metadata

        Returns:
            PerformanceMetrics instance
        """
        if not self.enabled:
            return PerformanceMetrics(operation=operation, start_time=time.time())

        try:
            memory_before = self._process.memory_info().rss
            cpu_percent = self._process.cpu_percent(interval=None)  # Non-blocking
        except Exception:
            memory_before = None
            cpu_percent = None

        metrics = PerformanceMetrics(
            operation=operation,
            start_time=time.time(),
            memory_before=memory_before,
            cpu_percent=cpu_percent,
            metadata=metadata,
        )

        with self._lock:
            self.metrics.append(metrics)

        return metrics

    def get_metrics(self, operation: Optional[str] = None) -> List[PerformanceMetrics]:
        """
        Get collected metrics.

        Args:
            operation: Filter by operation name

        Returns:
            List of metrics
        """
        with self._lock:
            if operation:
                return [m for m in self.metrics if m.operation == operation]
            return self.metrics.copy()

    def get_summary(self) -> Dict[str, Any]:
        """
        Get performance summary.

        Returns:
            Summary statistics
        """
        with self._lock:
            if not self.metrics:
                return {}

            summary = defaultdict(
                lambda: {
                    "count": 0,
                    "total_duration": 0.0,
                    "avg_duration": 0.0,
                    "min_duration": float("inf"),
                    "max_duration": 0.0,
                    "total_memory_delta": 0,
                    "avg_memory_delta": 0,
                    "success_count": 0,
                    "error_count": 0,
                }
            )

            for metric in self.metrics:
                if metric.duration is None:
                    continue

                op = metric.operation
                stats = summary[op]

                stats["count"] += 1
                stats["total_duration"] += metric.duration
                stats["min_duration"] = min(stats["min_duration"], metric.duration)
                stats["max_duration"] = max(stats["max_duration"], metric.duration)

                if metric.memory_delta:
                    stats["total_memory_delta"] += metric.memory_delta

                if metric.success:
                    stats["success_count"] += 1
                else:
                    stats["error_count"] += 1

            # Calculate averages
            for stats in summary.values():
                if stats["count"] > 0:
                    stats["avg_duration"] = stats["total_duration"] / stats["count"]
                    stats["avg_memory_delta"] = (
                        stats["total_memory_delta"] / stats["count"]
                    )

            return dict(summary)

    def clear(self):
        """Clear collected metrics."""
        with self._lock:
            self.metrics.clear()

    def export_metrics(self, filepath: Path):
        """
        Export metrics to JSON file.

        Args:
            filepath: Output file path
        """
        # Get data without holding lock
        metrics_data = []
        with self._lock:
            metrics_data = [m.to_dict() for m in self.metrics]

        # Get summary (which also uses lock)
        summary = self.get_summary()

        data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics_data,
            "summary": summary,
        }

        filepath.write_text(json.dumps(data, indent=2))


# Global performance monitor
_monitor = PerformanceMonitor()


def get_monitor() -> PerformanceMonitor:
    """Get global performance monitor."""
    return _monitor


def profile(operation: Optional[str] = None):
    """
    Decorator to profile function performance.

    Args:
        operation: Operation name (defaults to function name)
    """

    def decorator(func: Callable) -> Callable:
        op_name = operation or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            metrics = _monitor.start_operation(op_name)

            try:
                result = func(*args, **kwargs)
                metrics.finish(success=True)
                return result
            except Exception as e:
                metrics.finish(success=False, error=str(e))
                raise

        return wrapper

    return decorator


class CacheEntry:
    """Cache entry with TTL support."""

    def __init__(self, value: Any, ttl: Optional[int] = None):
        """
        Initialize cache entry.

        Args:
            value: Cached value
            ttl: Time to live in seconds
        """
        self.value = value
        self.created_at = time.time()
        self.last_accessed_at = self.created_at
        self.ttl = ttl
        self.hits = 0

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl

    def get(self) -> Any:
        """Get cached value and increment hit counter."""
        self.hits += 1
        self.last_accessed_at = time.time()
        return self.value


class PerformanceCache:
    """High-performance cache with TTL and persistence."""

    def __init__(
        self,
        max_size: int = 1000,
        default_ttl: Optional[int] = 3600,
        persist_path: Optional[Path] = None,
    ):
        """
        Initialize cache.

        Args:
            max_size: Maximum cache size
            default_ttl: Default TTL in seconds
            persist_path: Path for cache persistence
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.persist_path = persist_path
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "expirations": 0}

        # Load persisted cache
        if persist_path and persist_path.exists():
            self._load()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats["misses"] += 1
                return None

            if entry.is_expired():
                del self._cache[key]
                self._stats["expirations"] += 1
                self._stats["misses"] += 1
                return None

            self._stats["hits"] += 1
            return entry.get()

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live (overrides default)
        """
        with self._lock:
            # Evict if at max size
            if len(self._cache) >= self.max_size and key not in self._cache:
                self._evict_lru()

            ttl = ttl if ttl is not None else self.default_ttl
            self._cache[key] = CacheEntry(value, ttl)

    def delete(self, key: str):
        """Delete key from cache."""
        with self._lock:
            self._cache.pop(key, None)

    def clear(self):
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
            self._stats = {"hits": 0, "misses": 0, "evictions": 0, "expirations": 0}

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                self._stats["hits"] / total_requests if total_requests > 0 else 0.0
            )

            return {
                **self._stats,
                "size": len(self._cache),
                "max_size": self.max_size,
                "hit_rate": hit_rate,
                "total_requests": total_requests,
            }

    def _evict_lru(self):
        """Evict least recently used entry."""
        if not self._cache:
            return

        # Find entry with the oldest last_accessed_at timestamp
        lru_key = min(self._cache.items(), key=lambda x: x[1].last_accessed_at)[0]
        del self._cache[lru_key]
        self._stats["evictions"] += 1

    def _load(self):
        """Load cache from disk."""
        try:
            with open(self.persist_path, "rb") as f:
                data = pickle.load(f)  # nosec B301 - trusted local cache file
                self._cache = data.get("cache", {})
                self._stats = data.get("stats", self._stats)
            logger.info(
                f"Loaded {len(self._cache)} cache entries from {self.persist_path}"
            )
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")

    def save(self):
        """Save cache to disk."""
        if not self.persist_path:
            return

        try:
            with self._lock:
                data = {
                    "cache": self._cache,
                    "stats": self._stats,
                    "timestamp": datetime.now().isoformat(),
                }

                with open(self.persist_path, "wb") as f:
                    pickle.dump(data, f)

                logger.info(
                    f"Saved {len(self._cache)} cache entries to {self.persist_path}"
                )
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")


def cache_key(*args, **kwargs) -> str:
    """
    Generate cache key from arguments.

    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments

    Returns:
        Cache key string
    """
    key_data = {"args": args, "kwargs": sorted(kwargs.items())}
    key_str = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(key_str.encode()).hexdigest()


def cached(
    cache: Optional[PerformanceCache] = None,
    ttl: Optional[int] = None,
    key_func: Optional[Callable] = None,
):
    """
    Decorator to cache function results.

    Args:
        cache: Cache instance (creates new if None)
        ttl: Time to live for cached results
        key_func: Custom key generation function
    """
    if cache is None:
        cache = PerformanceCache()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                key = f"{func.__name__}:{cache_key(*args, **kwargs)}"

            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result

        wrapper.cache = cache
        return wrapper

    return decorator


class ResourceMonitor:
    """Monitor system resource usage."""

    def __init__(self):
        """Initialize resource monitor."""
        self._process = psutil.Process()
        self._baseline_memory = self._process.memory_info().rss
        self._baseline_cpu = self._process.cpu_percent()

    def get_memory_usage(self) -> Dict[str, int]:
        """
        Get current memory usage.

        Returns:
            Memory usage statistics
        """
        mem_info = self._process.memory_info()
        return {
            "rss": mem_info.rss,
            "vms": mem_info.vms,
            "percent": self._process.memory_percent(),
            "delta": mem_info.rss - self._baseline_memory,
        }

    def get_cpu_usage(self) -> Dict[str, float]:
        """
        Get current CPU usage.

        Returns:
            CPU usage statistics
        """
        try:
            cpu_percent = self._process.cpu_percent(interval=None)  # Non-blocking
            num_threads = self._process.num_threads()
            delta = cpu_percent - self._baseline_cpu if cpu_percent else 0
        except Exception:
            cpu_percent = 0.0
            num_threads = 0
            delta = 0.0

        return {"percent": cpu_percent, "num_threads": num_threads, "delta": delta}

    def get_io_stats(self) -> Dict[str, int]:
        """
        Get I/O statistics.

        Returns:
            I/O statistics
        """
        try:
            io_counters = self._process.io_counters()
            return {
                "read_count": io_counters.read_count,
                "write_count": io_counters.write_count,
                "read_bytes": io_counters.read_bytes,
                "write_bytes": io_counters.write_bytes,
            }
        except (AttributeError, OSError):
            return {}

    def get_summary(self) -> Dict[str, Any]:
        """
        Get complete resource summary.

        Returns:
            Resource usage summary
        """
        return {
            "memory": self.get_memory_usage(),
            "cpu": self.get_cpu_usage(),
            "io": self.get_io_stats(),
            "timestamp": datetime.now().isoformat(),
        }


class PerformanceOptimizer:
    """Optimize scanner performance."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize optimizer.

        Args:
            cache_dir: Directory for cache storage
        """
        self.cache_dir = cache_dir or Path.home() / ".security-assistant" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize caches
        self.scan_cache = PerformanceCache(
            max_size=100,
            default_ttl=3600,
            persist_path=self.cache_dir / "scan_cache.pkl",
        )

        self.dependency_cache = PerformanceCache(
            max_size=500,
            default_ttl=86400,  # 24 hours
            persist_path=self.cache_dir / "dependency_cache.pkl",
        )

        self.monitor = PerformanceMonitor()
        self.resource_monitor = ResourceMonitor()

    def optimize_scan_results(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Optimize scan results by deduplication and filtering.

        Args:
            results: Raw scan results

        Returns:
            Optimized results
        """
        metrics = self.monitor.start_operation("optimize_scan_results")

        try:
            # Remove duplicates based on file + line + rule
            seen = set()
            optimized = []

            for result in results:
                key = (result.get("file"), result.get("line"), result.get("rule_id"))

                if key not in seen:
                    seen.add(key)
                    optimized.append(result)

            metrics.finish(success=True)
            return optimized

        except Exception as e:
            metrics.finish(success=False, error=str(e))
            raise

    def get_cached_scan(self, target: str, scanner: str) -> Optional[Dict[str, Any]]:
        """
        Get cached scan results.

        Args:
            target: Scan target
            scanner: Scanner name

        Returns:
            Cached results or None
        """
        key = f"{scanner}:{target}"
        return self.scan_cache.get(key)

    def cache_scan_results(
        self,
        target: str,
        scanner: str,
        results: Dict[str, Any],
        ttl: Optional[int] = None,
    ):
        """
        Cache scan results.

        Args:
            target: Scan target
            scanner: Scanner name
            results: Scan results
            ttl: Time to live
        """
        key = f"{scanner}:{target}"
        self.scan_cache.set(key, results, ttl)

    def save_caches(self):
        """Save all caches to disk."""
        self.scan_cache.save()
        self.dependency_cache.save()

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get comprehensive performance report.

        Returns:
            Performance report
        """
        return {
            "metrics_summary": self.monitor.get_summary(),
            "scan_cache_stats": self.scan_cache.get_stats(),
            "dependency_cache_stats": self.dependency_cache.get_stats(),
            "resource_usage": self.resource_monitor.get_summary(),
            "timestamp": datetime.now().isoformat(),
        }


# Convenience functions
def start_profiling(operation: str, **metadata) -> PerformanceMetrics:
    """Start profiling an operation."""
    return _monitor.start_operation(operation, **metadata)


def get_performance_summary() -> Dict[str, Any]:
    """Get performance summary."""
    return _monitor.get_summary()


def export_metrics(filepath: Path):
    """Export metrics to file."""
    _monitor.export_metrics(filepath)
