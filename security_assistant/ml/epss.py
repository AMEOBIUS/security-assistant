"""
EPSS (Exploit Prediction Scoring System) Client

Fetches exploit probability scores from FIRST.org EPSS API.

EPSS provides daily-updated probability (0-100%) that a CVE will be
exploited in the wild within the next 30 days.

API: https://api.first.org/data/v1/epss
Documentation: https://www.first.org/epss/api

Version: 1.0.0
"""

import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union

import requests

logger = logging.getLogger(__name__)


@dataclass
class EPSSScore:
    """EPSS score for a CVE."""

    cve_id: str
    epss: float  # Probability (0.0-1.0)
    percentile: float  # Percentile rank (0.0-1.0)
    date: str  # Score date (YYYY-MM-DD)


class EPSSClient:
    """
    Client for FIRST.org EPSS API.

    Features:
    - Fetch EPSS scores for CVEs
    - Batch requests (up to 100 CVEs per request)
    - Caching (24-hour TTL)
    - Rate limiting (respectful API usage)

    Example:
        >>> client = EPSSClient()
        >>> scores = client.get_scores(["CVE-2024-1234", "CVE-2024-5678"])
        >>> print(scores["CVE-2024-1234"])  # 0.85 (85% exploit probability)
    """

    BASE_URL = "https://api.first.org/data/v1/epss"
    MAX_BATCH_SIZE = 100  # API limit
    CACHE_TTL_HOURS = 24  # Cache scores for 24 hours
    RATE_LIMIT_DELAY = 0.5  # Seconds between requests

    def __init__(
        self,
        cache_enabled: bool = True,
        timeout: int = 10,
        cache_file: Optional[Union[str, Path]] = None,
    ):
        """
        Initialize EPSS client.

        Args:
            cache_enabled: Enable in-memory caching (default: True)
            timeout: Request timeout in seconds (default: 10)
            cache_file: Path to persistent cache file (optional)
        """
        self.cache_enabled = cache_enabled
        self.timeout = timeout
        self.cache_file = Path(cache_file) if cache_file else None

        # In-memory cache: {cve_id: (EPSSScore, timestamp)}
        self._cache: Dict[str, tuple[EPSSScore, datetime]] = {}

        # Load persistent cache if enabled
        if self.cache_enabled and self.cache_file:
            self._load_cache_from_file()

        # Rate limiting
        self._last_request_time: Optional[datetime] = None

        logger.info(
            f"Initialized EPSSClient (cache={cache_enabled}, file={self.cache_file})"
        )

    def get_score(self, cve_id: str) -> Optional[float]:
        """
        Get EPSS score for a single CVE.

        Args:
            cve_id: CVE ID (e.g., "CVE-2024-1234")

        Returns:
            EPSS score (0.0-1.0), or None if not found

        Example:
            >>> client = EPSSClient()
            >>> score = client.get_score("CVE-2024-1234")
            >>> print(f"Exploit probability: {score * 100:.1f}%")
        """
        scores = self.get_scores([cve_id])
        return scores.get(cve_id)

    def get_scores(self, cve_ids: List[str]) -> Dict[str, float]:
        """
        Get EPSS scores for multiple CVEs.

        Args:
            cve_ids: List of CVE IDs

        Returns:
            Dictionary mapping CVE ID to EPSS score (0.0-1.0)

        Example:
            >>> client = EPSSClient()
            >>> scores = client.get_scores(["CVE-2024-1234", "CVE-2024-5678"])
            >>> for cve, score in scores.items():
            ...     print(f"{cve}: {score * 100:.1f}%")
        """
        if not cve_ids:
            return {}

        # Normalize CVE IDs (uppercase)
        cve_ids = [cve.upper() for cve in cve_ids]

        # Check cache first
        cached_scores = {}
        uncached_cve_ids = []

        if self.cache_enabled:
            for cve_id in cve_ids:
                cached = self._get_from_cache(cve_id)
                if cached:
                    cached_scores[cve_id] = cached.epss
                else:
                    uncached_cve_ids.append(cve_id)
        else:
            uncached_cve_ids = cve_ids

        # Fetch uncached CVEs from API
        if uncached_cve_ids:
            fetched_scores = self._fetch_scores_batch(uncached_cve_ids)

            # Update cache
            if self.cache_enabled:
                for cve_id, epss_score in fetched_scores.items():
                    self._add_to_cache(cve_id, epss_score)

                # Save to file if configured
                if self.cache_file:
                    self._save_cache_to_file()

            # Merge with cached scores
            cached_scores.update(
                {cve: score.epss for cve, score in fetched_scores.items()}
            )

        return cached_scores

    def _fetch_scores_batch(self, cve_ids: List[str]) -> Dict[str, EPSSScore]:
        """
        Fetch EPSS scores from API in batches.

        Args:
            cve_ids: List of CVE IDs (max 100 per batch)

        Returns:
            Dictionary mapping CVE ID to EPSSScore
        """
        all_scores = {}

        # Split into batches of MAX_BATCH_SIZE
        for i in range(0, len(cve_ids), self.MAX_BATCH_SIZE):
            batch = cve_ids[i : i + self.MAX_BATCH_SIZE]

            # Rate limiting
            self._rate_limit()

            # Fetch batch
            try:
                batch_scores = self._fetch_batch(batch)
                all_scores.update(batch_scores)
            except Exception as e:
                logger.error(f"Failed to fetch EPSS scores for batch: {e}")
                # Continue with next batch

        return all_scores

    def _fetch_batch(self, cve_ids: List[str]) -> Dict[str, EPSSScore]:
        """
        Fetch a single batch of EPSS scores from API.

        Args:
            cve_ids: List of CVE IDs (max 100)

        Returns:
            Dictionary mapping CVE ID to EPSSScore
        """
        # Build query parameter
        cve_param = ",".join(cve_ids)

        # Make request
        url = f"{self.BASE_URL}?cve={cve_param}"

        logger.debug(f"Fetching EPSS scores for {len(cve_ids)} CVEs")

        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            data = response.json()

            # Parse response
            scores = {}
            for item in data.get("data", []):
                cve_id = item.get("cve", "").upper()
                epss = float(item.get("epss", 0.0))
                percentile = float(item.get("percentile", 0.0))
                date = item.get("date", "")

                scores[cve_id] = EPSSScore(
                    cve_id=cve_id,
                    epss=epss,
                    percentile=percentile,
                    date=date,
                )

            logger.info(f"Fetched EPSS scores for {len(scores)}/{len(cve_ids)} CVEs")

            return scores

        except requests.exceptions.RequestException as e:
            logger.error(f"EPSS API request failed: {e}")
            return {}
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to parse EPSS API response: {e}")
            return {}

    def _load_cache_from_file(self) -> None:
        """Load cache from file."""
        if not self.cache_file or not self.cache_file.exists():
            return

        try:
            with open(self.cache_file) as f:
                data = json.load(f)

            loaded_count = 0
            for cve_id, entry in data.items():
                try:
                    score_data = entry["score"]
                    timestamp_str = entry["timestamp"]
                    timestamp = datetime.fromisoformat(timestamp_str)

                    # Convert dict to EPSSScore
                    score = EPSSScore(**score_data)
                    self._cache[cve_id] = (score, timestamp)
                    loaded_count += 1
                except (ValueError, KeyError, TypeError):
                    continue

            logger.info(f"Loaded {loaded_count} EPSS scores from cache file")

        except Exception as e:
            logger.warning(f"Failed to load EPSS cache file: {e}")

    def _save_cache_to_file(self) -> None:
        """Save cache to file."""
        if not self.cache_file:
            return

        try:
            data = {}
            for cve_id, (score, timestamp) in self._cache.items():
                data[cve_id] = {
                    "score": asdict(score),
                    "timestamp": timestamp.isoformat(),
                }

            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w") as f:
                json.dump(data, f)

            logger.info(f"Saved {len(self._cache)} EPSS scores to cache file")

        except Exception as e:
            logger.warning(f"Failed to save EPSS cache file: {e}")

    def _get_from_cache(self, cve_id: str) -> Optional[EPSSScore]:
        """
        Get EPSS score from cache.

        Args:
            cve_id: CVE ID

        Returns:
            EPSSScore if cached and not expired, else None
        """
        if cve_id not in self._cache:
            return None

        score, timestamp = self._cache[cve_id]

        # Check if expired
        age = datetime.now() - timestamp
        if age > timedelta(hours=self.CACHE_TTL_HOURS):
            # Expired, remove from cache
            del self._cache[cve_id]
            return None

        return score

    def _add_to_cache(self, cve_id: str, score: EPSSScore) -> None:
        """
        Add EPSS score to cache.

        Args:
            cve_id: CVE ID
            score: EPSSScore
        """
        self._cache[cve_id] = (score, datetime.now())

    def _rate_limit(self) -> None:
        """
        Enforce rate limiting between API requests.

        Waits RATE_LIMIT_DELAY seconds since last request.
        """
        if self._last_request_time:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            if elapsed < self.RATE_LIMIT_DELAY:
                sleep_time = self.RATE_LIMIT_DELAY - elapsed
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
                time.sleep(sleep_time)

        self._last_request_time = datetime.now()

    def clear_cache(self) -> None:
        """Clear the in-memory cache."""
        self._cache.clear()
        logger.info("Cleared EPSS cache")

    def get_cache_stats(self) -> Dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total = len(self._cache)
        expired = 0

        now = datetime.now()
        for _, (_, timestamp) in self._cache.items():
            age = now - timestamp
            if age > timedelta(hours=self.CACHE_TTL_HOURS):
                expired += 1

        return {
            "total": total,
            "valid": total - expired,
            "expired": expired,
        }
