"""
Vulnerability Enricher

Combines EPSS and KEV data to enrich vulnerability findings.

Provides:
- EPSS scores (exploit probability)
- KEV status (actively exploited)
- Smart prioritization (KEV=true → CRITICAL)

Version: 1.0.0
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass

from security_assistant.ml.epss import EPSSClient
from security_assistant.enrichment.kev import KEVClient, KEVEntry


logger = logging.getLogger(__name__)


@dataclass
class EnrichedVulnerability:
    """Enriched vulnerability with EPSS and KEV data."""
    cve_id: str
    
    # EPSS data
    epss_score: Optional[float] = None  # 0.0-1.0
    epss_percentile: Optional[float] = None  # 0.0-1.0
    
    # KEV data
    is_exploited: bool = False
    kev_entry: Optional[KEVEntry] = None
    
    # Smart prioritization
    priority: str = "UNKNOWN"  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    priority_reason: str = ""


class VulnerabilityEnricher:
    """
    Enriches vulnerabilities with EPSS and KEV data.
    
    Features:
    - EPSS scores (exploit probability)
    - KEV status (actively exploited)
    - Smart prioritization based on EPSS + KEV
    - Batch processing
    
    Example:
        >>> enricher = VulnerabilityEnricher()
        >>> enriched = enricher.enrich("CVE-2021-44228")
        >>> if enriched.is_exploited:
        ...     print(f"CRITICAL: {enriched.cve_id} is actively exploited!")
        >>> print(f"EPSS: {enriched.epss_score * 100:.1f}%")
    """
    
    # EPSS thresholds for prioritization
    EPSS_CRITICAL = 0.7  # 70%+ exploit probability
    EPSS_HIGH = 0.3      # 30-70% exploit probability
    EPSS_MEDIUM = 0.1    # 10-30% exploit probability
    # Below 10% = LOW
    
    def __init__(
        self,
        epss_client: Optional[EPSSClient] = None,
        kev_client: Optional[KEVClient] = None,
    ):
        """
        Initialize vulnerability enricher.
        
        Args:
            epss_client: EPSS client (creates default if None)
            kev_client: KEV client (creates default if None)
        """
        self.epss_client = epss_client or EPSSClient(cache_enabled=True)
        self.kev_client = kev_client or KEVClient(cache_enabled=True)
        
        logger.info("Initialized VulnerabilityEnricher")
    
    def enrich(self, cve_id: str) -> EnrichedVulnerability:
        """
        Enrich a single vulnerability.
        
        Args:
            cve_id: CVE ID (e.g., "CVE-2021-44228")
        
        Returns:
            EnrichedVulnerability with EPSS and KEV data
        
        Example:
            >>> enricher = VulnerabilityEnricher()
            >>> enriched = enricher.enrich("CVE-2021-44228")
            >>> print(f"Priority: {enriched.priority}")
            >>> print(f"Reason: {enriched.priority_reason}")
        """
        cve_id = cve_id.upper()
        
        # Fetch EPSS score
        epss_score = self.epss_client.get_score(cve_id)
        
        # Fetch KEV status
        is_exploited = self.kev_client.is_exploited(cve_id)
        kev_entry = self.kev_client.get_entry(cve_id) if is_exploited else None
        
        # Create enriched vulnerability
        enriched = EnrichedVulnerability(
            cve_id=cve_id,
            epss_score=epss_score,
            epss_percentile=None,  # TODO: Get from EPSS client
            is_exploited=is_exploited,
            kev_entry=kev_entry,
        )
        
        # Calculate priority
        self._calculate_priority(enriched)
        
        return enriched
    
    def enrich_batch(self, cve_ids: List[str]) -> Dict[str, EnrichedVulnerability]:
        """
        Enrich multiple vulnerabilities in batch.
        
        Args:
            cve_ids: List of CVE IDs
        
        Returns:
            Dictionary mapping CVE ID to EnrichedVulnerability
        
        Example:
            >>> enricher = VulnerabilityEnricher()
            >>> enriched = enricher.enrich_batch([
            ...     "CVE-2021-44228",
            ...     "CVE-2022-22965"
            ... ])
            >>> for cve, data in enriched.items():
            ...     print(f"{cve}: {data.priority}")
        """
        if not cve_ids:
            return {}
        
        # Normalize CVE IDs
        cve_ids = [cve.upper() for cve in cve_ids]
        
        # Fetch EPSS scores (batch)
        epss_scores = self.epss_client.get_scores(cve_ids)
        
        # Fetch KEV entries (batch)
        kev_entries = self.kev_client.get_entries(cve_ids)
        
        # Create enriched vulnerabilities
        enriched = {}
        for cve_id in cve_ids:
            enriched_vuln = EnrichedVulnerability(
                cve_id=cve_id,
                epss_score=epss_scores.get(cve_id),
                epss_percentile=None,  # TODO: Get from EPSS client
                is_exploited=cve_id in kev_entries,
                kev_entry=kev_entries.get(cve_id),
            )
            
            # Calculate priority
            self._calculate_priority(enriched_vuln)
            
            enriched[cve_id] = enriched_vuln
        
        logger.info(f"Enriched {len(enriched)} vulnerabilities")
        
        return enriched
    
    def _calculate_priority(self, enriched: EnrichedVulnerability) -> None:
        """
        Calculate priority based on EPSS and KEV data.
        
        Priority rules:
        1. KEV=true → CRITICAL (actively exploited)
        2. EPSS ≥ 70% → CRITICAL
        3. EPSS 30-70% → HIGH
        4. EPSS 10-30% → MEDIUM
        5. EPSS < 10% → LOW
        6. No EPSS data → INFO
        
        Args:
            enriched: EnrichedVulnerability to update
        """
        # Rule 1: KEV=true → CRITICAL
        if enriched.is_exploited:
            enriched.priority = "CRITICAL"
            enriched.priority_reason = "Actively exploited in the wild (CISA KEV)"
            
            if enriched.kev_entry and enriched.kev_entry.known_ransomware_campaign_use:
                enriched.priority_reason += " - Used in ransomware campaigns"
            
            return
        
        # Rules 2-6: EPSS-based prioritization
        if enriched.epss_score is None:
            enriched.priority = "INFO"
            enriched.priority_reason = "No EPSS data available"
            return
        
        epss_pct = enriched.epss_score * 100
        
        if enriched.epss_score >= self.EPSS_CRITICAL:
            enriched.priority = "CRITICAL"
            enriched.priority_reason = f"Very high exploit probability (EPSS: {epss_pct:.1f}%)"
        
        elif enriched.epss_score >= self.EPSS_HIGH:
            enriched.priority = "HIGH"
            enriched.priority_reason = f"High exploit probability (EPSS: {epss_pct:.1f}%)"
        
        elif enriched.epss_score >= self.EPSS_MEDIUM:
            enriched.priority = "MEDIUM"
            enriched.priority_reason = f"Medium exploit probability (EPSS: {epss_pct:.1f}%)"
        
        else:
            enriched.priority = "LOW"
            enriched.priority_reason = f"Low exploit probability (EPSS: {epss_pct:.1f}%)"
    
    def get_critical_cves(self, cve_ids: List[str]) -> List[str]:
        """
        Get list of CRITICAL CVEs from a list.
        
        Args:
            cve_ids: List of CVE IDs to check
        
        Returns:
            List of CVE IDs with CRITICAL priority
        
        Example:
            >>> enricher = VulnerabilityEnricher()
            >>> critical = enricher.get_critical_cves([
            ...     "CVE-2021-44228",  # Log4Shell (KEV)
            ...     "CVE-2024-1234",   # Random CVE
            ... ])
            >>> print(f"Critical CVEs: {critical}")
        """
        enriched = self.enrich_batch(cve_ids)
        
        critical = [
            cve_id
            for cve_id, data in enriched.items()
            if data.priority == "CRITICAL"
        ]
        
        return critical
    
    def get_exploited_cves(self, cve_ids: List[str]) -> List[str]:
        """
        Get list of actively exploited CVEs from a list.
        
        Args:
            cve_ids: List of CVE IDs to check
        
        Returns:
            List of CVE IDs that are actively exploited (KEV)
        
        Example:
            >>> enricher = VulnerabilityEnricher()
            >>> exploited = enricher.get_exploited_cves([
            ...     "CVE-2021-44228",  # Log4Shell (KEV)
            ...     "CVE-2024-1234",   # Random CVE
            ... ])
            >>> print(f"Exploited CVEs: {exploited}")
        """
        enriched = self.enrich_batch(cve_ids)
        
        exploited = [
            cve_id
            for cve_id, data in enriched.items()
            if data.is_exploited
        ]
        
        return exploited
