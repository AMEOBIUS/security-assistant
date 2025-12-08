"""
KEV (Known Exploited Vulnerabilities) Client

Fetches actively exploited CVEs from CISA KEV Catalog.

CISA maintains a catalog of vulnerabilities that are known to be
actively exploited in the wild. These vulnerabilities should be
prioritized for remediation.

API: https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
Documentation: https://www.cisa.gov/known-exploited-vulnerabilities-catalog

Version: 1.0.0
"""

import logging
import requests
from typing import Dict, List, Optional, Set, Union
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
import json


logger = logging.getLogger(__name__)


@dataclass
class KEVEntry:
    """Known Exploited Vulnerability entry."""
    cve_id: str
    vendor_project: str
    product: str
    vulnerability_name: str
    date_added: str  # Date added to KEV catalog (YYYY-MM-DD)
    short_description: str
    required_action: str
    due_date: str  # Due date for remediation (YYYY-MM-DD)
    known_ransomware_campaign_use: bool
    notes: str


class KEVClient:
    """
    Client for CISA Known Exploited Vulnerabilities Catalog.
    
    Features:
    - Fetch KEV catalog (daily updates)
    - Check if CVE is actively exploited
    - Caching (24-hour TTL)
    - Offline fallback
    
    Example:
        >>> client = KEVClient()
        >>> is_exploited = client.is_exploited("CVE-2021-44228")
        >>> if is_exploited:
        ...     print("CRITICAL: Actively exploited in the wild!")
    """
    
    KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
    CACHE_TTL_HOURS = 24  # Cache catalog for 24 hours
    REQUEST_TIMEOUT = 15  # Seconds
    
    def __init__(
        self,
        cache_enabled: bool = True,
        offline_fallback: bool = True,
        cache_file: Optional[Union[str, Path]] = None,
    ):
        """
        Initialize KEV client.
        
        Args:
            cache_enabled: Enable in-memory caching (default: True)
            offline_fallback: Use cached data if API fails (default: True)
            cache_file: Path to persistent cache file (optional)
        """
        self.cache_enabled = cache_enabled
        self.offline_fallback = offline_fallback
        self.cache_file = Path(cache_file) if cache_file else None
        
        # In-memory cache: {cve_id: KEVEntry}
        self._cache: Dict[str, KEVEntry] = {}
        self._cache_timestamp: Optional[datetime] = None
        
        # KEV catalog metadata
        self._catalog_version: Optional[str] = None
        self._catalog_date: Optional[str] = None
        self._catalog_count: int = 0
        
        logger.info(f"Initialized KEVClient (cache={cache_enabled}, offline={offline_fallback}, file={self.cache_file})")
    
    def is_exploited(self, cve_id: str) -> bool:
        """
        Check if CVE is in CISA KEV catalog (actively exploited).
        
        Args:
            cve_id: CVE ID (e.g., "CVE-2021-44228")
        
        Returns:
            True if CVE is actively exploited, False otherwise
        
        Example:
            >>> client = KEVClient()
            >>> if client.is_exploited("CVE-2021-44228"):
            ...     print("CRITICAL: Log4Shell is actively exploited!")
        """
        cve_id = cve_id.upper()
        
        # Ensure catalog is loaded
        self._ensure_catalog_loaded()
        
        return cve_id in self._cache
    
    def get_entry(self, cve_id: str) -> Optional[KEVEntry]:
        """
        Get KEV entry for a CVE.
        
        Args:
            cve_id: CVE ID (e.g., "CVE-2021-44228")
        
        Returns:
            KEVEntry if CVE is in catalog, None otherwise
        
        Example:
            >>> client = KEVClient()
            >>> entry = client.get_entry("CVE-2021-44228")
            >>> if entry:
            ...     print(f"Added: {entry.date_added}")
            ...     print(f"Action: {entry.required_action}")
        """
        cve_id = cve_id.upper()
        
        # Ensure catalog is loaded
        self._ensure_catalog_loaded()
        
        return self._cache.get(cve_id)
    
    def get_entries(self, cve_ids: List[str]) -> Dict[str, KEVEntry]:
        """
        Get KEV entries for multiple CVEs.
        
        Args:
            cve_ids: List of CVE IDs
        
        Returns:
            Dictionary mapping CVE ID to KEVEntry (only exploited CVEs)
        
        Example:
            >>> client = KEVClient()
            >>> entries = client.get_entries(["CVE-2021-44228", "CVE-2022-1234"])
            >>> for cve, entry in entries.items():
            ...     print(f"{cve}: {entry.vulnerability_name}")
        """
        # Normalize CVE IDs
        cve_ids = [cve.upper() for cve in cve_ids]
        
        # Ensure catalog is loaded
        self._ensure_catalog_loaded()
        
        # Filter exploited CVEs
        entries = {}
        for cve_id in cve_ids:
            if cve_id in self._cache:
                entries[cve_id] = self._cache[cve_id]
        
        return entries
    
    def get_all_exploited_cves(self) -> Set[str]:
        """
        Get all CVE IDs in KEV catalog.
        
        Returns:
            Set of CVE IDs that are actively exploited
        
        Example:
            >>> client = KEVClient()
            >>> exploited = client.get_all_exploited_cves()
            >>> print(f"Total exploited CVEs: {len(exploited)}")
        """
        # Ensure catalog is loaded
        self._ensure_catalog_loaded()
        
        return set(self._cache.keys())
    
    def get_catalog_metadata(self) -> Dict[str, any]:
        """
        Get KEV catalog metadata.
        
        Returns:
            Dictionary with catalog version, date, and count
        
        Example:
            >>> client = KEVClient()
            >>> metadata = client.get_catalog_metadata()
            >>> print(f"Catalog version: {metadata['version']}")
            >>> print(f"Last updated: {metadata['date']}")
            >>> print(f"Total CVEs: {metadata['count']}")
        """
        # Ensure catalog is loaded
        self._ensure_catalog_loaded()
        
        return {
            "version": self._catalog_version,
            "date": self._catalog_date,
            "count": self._catalog_count,
            "cache_age_hours": self._get_cache_age_hours(),
        }
    
    def refresh_catalog(self) -> bool:
        """
        Force refresh KEV catalog from API.
        
        Returns:
            True if refresh successful, False otherwise
        
        Example:
            >>> client = KEVClient()
            >>> if client.refresh_catalog():
            ...     print("Catalog refreshed successfully")
        """
        return self._fetch_catalog()
    
    def _ensure_catalog_loaded(self) -> None:
        """
        Ensure KEV catalog is loaded (fetch if needed).
        
        Checks cache expiration and fetches fresh data if needed.
        """
        # Check if memory cache is valid
        if self.cache_enabled and self._is_cache_valid():
            return
            
        # Check if file cache is valid
        if self.cache_file and self._load_from_cache_file():
            if self._is_cache_valid():
                return
        
        # Fetch fresh catalog
        success = self._fetch_catalog()
        
        # If fetch failed and offline fallback is enabled, use stale cache
        if not success and self.offline_fallback and self._cache:
            logger.warning("Using stale KEV cache (offline fallback)")
            return
        
        # If fetch failed and no cache, raise error
        if not success and not self._cache:
            logger.error("Failed to load KEV catalog and no cache available")

    def _load_from_cache_file(self) -> bool:
        """Load catalog from cache file."""
        if not self.cache_file or not self.cache_file.exists():
            return False
            
        try:
            # Check file age
            mtime = datetime.fromtimestamp(self.cache_file.stat().st_mtime)
            age = datetime.now() - mtime
            
            # If expired and we are NOT in offline fallback mode (meaning we want fresh data), return False
            # But if network fails later, we might still want this data?
            # Actually _ensure_catalog_loaded calls this first. If it returns False (expired), 
            # then it tries _fetch_catalog. If that fails, it checks self._cache.
            # So if we return False here, self._cache is empty.
            # We should load it ANYWAY if it exists, but mark it as expired?
            # Or better: Load it, set timestamp. _ensure_catalog_loaded checks _is_cache_valid.
            # So we should ALWAYS load it if it exists.
            
            with open(self.cache_file, "r") as f:
                data = json.load(f)
                
            self._parse_catalog(data)
            # Use file mtime as cache timestamp
            self._cache_timestamp = mtime
            
            logger.info(f"Loaded KEV catalog from file: {self.cache_file}")
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load KEV cache file: {e}")
            return False

    def _save_to_cache_file(self, data: dict) -> None:
        """Save catalog to cache file."""
        if not self.cache_file:
            return
            
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w") as f:
                json.dump(data, f)
            logger.info(f"Saved KEV catalog to cache file: {self.cache_file}")
        except Exception as e:
            logger.warning(f"Failed to save KEV cache file: {e}")
    
    def _is_cache_valid(self) -> bool:
        """
        Check if cache is valid (not expired).
        
        Returns:
            True if cache is valid, False otherwise
        """
        if not self._cache_timestamp:
            return False
        
        age = datetime.now() - self._cache_timestamp
        return age < timedelta(hours=self.CACHE_TTL_HOURS)
    
    def _get_cache_age_hours(self) -> Optional[float]:
        """
        Get cache age in hours.
        
        Returns:
            Cache age in hours, or None if no cache
        """
        if not self._cache_timestamp:
            return None
        
        age = datetime.now() - self._cache_timestamp
        return age.total_seconds() / 3600
    
    def _fetch_catalog(self) -> bool:
        """
        Fetch KEV catalog from CISA API.
        
        Returns:
            True if fetch successful, False otherwise
        """
        logger.info("Fetching KEV catalog from CISA...")
        
        try:
            response = requests.get(self.KEV_URL, timeout=self.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            # Save to file cache if configured
            if self.cache_file:
                self._save_to_cache_file(data)
            
            # Parse catalog
            self._parse_catalog(data)
            
            # Update cache timestamp
            self._cache_timestamp = datetime.now()
            
            logger.info(
                f"Loaded KEV catalog: {self._catalog_count} CVEs "
                f"(version: {self._catalog_version}, date: {self._catalog_date})"
            )
            
            return True
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch KEV catalog: {e}")
            return False
        except (ValueError, KeyError) as e:
            logger.error(f"Failed to parse KEV catalog: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error fetching KEV catalog: {e}")
            return False
    
    def _parse_catalog(self, data: dict) -> None:
        """
        Parse KEV catalog JSON.
        
        Args:
            data: KEV catalog JSON data
        """
        # Extract metadata
        self._catalog_version = data.get("catalogVersion", "unknown")
        self._catalog_date = data.get("dateReleased", "unknown")
        
        # Parse vulnerabilities
        vulnerabilities = data.get("vulnerabilities", [])
        self._catalog_count = len(vulnerabilities)
        
        # Clear cache
        self._cache.clear()
        
        # Parse each entry
        for vuln in vulnerabilities:
            try:
                cve_id = vuln.get("cveID", "").upper()
                
                entry = KEVEntry(
                    cve_id=cve_id,
                    vendor_project=vuln.get("vendorProject", ""),
                    product=vuln.get("product", ""),
                    vulnerability_name=vuln.get("vulnerabilityName", ""),
                    date_added=vuln.get("dateAdded", ""),
                    short_description=vuln.get("shortDescription", ""),
                    required_action=vuln.get("requiredAction", ""),
                    due_date=vuln.get("dueDate", ""),
                    known_ransomware_campaign_use=vuln.get("knownRansomwareCampaignUse", "Unknown") == "Known",
                    notes=vuln.get("notes", ""),
                )
                
                self._cache[cve_id] = entry
            
            except Exception as e:
                logger.warning(f"Failed to parse KEV entry: {e}")
                continue
    
    def clear_cache(self) -> None:
        """Clear the in-memory cache."""
        self._cache.clear()
        self._cache_timestamp = None
        self._catalog_version = None
        self._catalog_date = None
        self._catalog_count = 0
        logger.info("Cleared KEV cache")
