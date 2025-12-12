"""
Enrichment Service for Security Findings.

Provides comprehensive finding enrichment:
- KEV (Known Exploited Vulnerabilities) integration
- False Positive detection
- Reachability analysis for SCA findings
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Any, List, Optional

logger = logging.getLogger(__name__)


class EnrichmentType(str, Enum):
    """Available enrichment types."""

    KEV = "kev"
    FALSE_POSITIVE = "false_positive"
    REACHABILITY = "reachability"


class EnrichmentService:
    """
    Comprehensive enrichment service for security findings.

    Features:
    - KEV integration for active exploit detection
    - False positive detection using heuristics
    - Reachability analysis for dependency findings

    Example:
        >>> service = EnrichmentService()
        >>> service.enrich_findings(findings)
    """

    def __init__(
        self,
        enable_kev: bool = True,
        enable_fp_detection: bool = True,
        enable_reachability: bool = True,
        project_root: Optional[str] = None,
        llm_service=None,
    ):
        """
        Initialize enrichment service.

        Args:
            enable_kev: Enable KEV integration
            enable_fp_detection: Enable false positive detection
            enable_reachability: Enable reachability analysis
            project_root: Project root for reachability analysis
            llm_service: LLM service for AI-based enrichment
        """
        self._kev_client = None
        self._fp_detector = None
        self._reachability_analyzer = None
        self._llm_service = llm_service
        self.project_root = project_root or str(Path.cwd())

        if enable_kev:
            self._init_kev()

        if enable_fp_detection:
            self._init_fp_detector()

        if enable_reachability:
            self._init_reachability()

    def _init_kev(self) -> None:
        """Initialize KEV client."""
        try:
            from ..enrichment.kev import KEVClient

            cache_path = Path(self.project_root) / ".cache" / "kev_catalog.json"
            self._kev_client = KEVClient(cache_file=cache_path)
            logger.info(f"KEV enrichment enabled (cache: {cache_path})")
        except Exception as e:
            logger.warning(f"Failed to initialize KEV client: {e}")

    def _init_fp_detector(self) -> None:
        """Initialize false positive detector."""
        try:
            from ..analysis.false_positive_detector import FalsePositiveDetector

            self._fp_detector = FalsePositiveDetector()
            logger.info("False positive detection enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize FP detector: {e}")

    def _init_reachability(self) -> None:
        """Initialize reachability analyzer."""
        try:
            from ..analysis.reachability.reachability_analyzer import (
                ReachabilityAnalyzer,
            )

            self._reachability_analyzer = ReachabilityAnalyzer(
                project_root=self.project_root
            )
            logger.info("Reachability analysis enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize Reachability Analyzer: {e}")

    @property
    def kev_client(self) -> Optional[Any]:
        """Get KEV client instance (for backward compatibility)."""
        return self._kev_client

    @property
    def fp_detector(self) -> Optional[Any]:
        """Get false positive detector instance."""
        return self._fp_detector

    @property
    def reachability_analyzer(self) -> Optional[Any]:
        """Get reachability analyzer instance."""
        return self._reachability_analyzer

    def enrich_findings(
        self,
        findings: List[Any],
        scanner_type: Optional[str] = None,
    ) -> None:
        """
        Enrich findings with all available enrichments.

        Args:
            findings: List of UnifiedFinding objects
            scanner_type: Optional scanner type for filtering
        """
        self.detect_false_positives(findings)
        self.analyze_reachability(findings, scanner_type)

    def detect_false_positives(self, findings: List[Any]) -> None:
        """
        Run false positive detection on findings.

        Args:
            findings: List of UnifiedFinding objects (modified in-place)
        """
        # 1. Use Heuristic FP Detector
        if self._fp_detector:
            findings_dict_list = []
            for f in findings:
                findings_dict_list.append(
                    {
                        "file_path": f.file_path,
                        "code": f.code_snippet,
                        "vulnerability_type": f.title,
                    }
                )

            analyses = self._fp_detector.analyze_batch(findings_dict_list)

            for idx, analysis in analyses.items():
                if idx < len(findings):
                    finding = findings[idx]
                    finding.is_false_positive = analysis.is_likely_false_positive
                    finding.fp_confidence = analysis.confidence
                    finding.fp_reasons = analysis.reasons

                    if finding.is_false_positive:
                        logger.info(
                            f"Probable False Positive (Heuristic): {finding.finding_id} "
                            f"(Confidence: {finding.fp_confidence:.2f})"
                        )

        # 2. Use LLM FP Detector (if enabled and finding is not already marked as FP)
        if self._llm_service:
            import asyncio
            
            for finding in findings:
                # Skip if already marked as FP with high confidence
                if finding.is_false_positive and finding.fp_confidence > 0.8:
                    continue
                    
                try:
                    is_fp, reason = asyncio.run(self._llm_service.detect_false_positive(finding))
                    if is_fp:
                        finding.is_false_positive = True
                        finding.fp_confidence = 0.9  # High confidence for LLM
                        finding.fp_reasons.append(f"LLM: {reason}")
                        logger.info(f"Probable False Positive (LLM): {finding.finding_id} - {reason}")
                except Exception as e:
                    logger.warning(f"LLM FP detection failed for {finding.finding_id}: {e}")

    def analyze_reachability(
        self,
        findings: List[Any],
        scanner_type: Optional[str] = None,
    ) -> None:
        """
        Analyze reachability for SCA findings.

        Args:
            findings: List of UnifiedFinding objects (modified in-place)
            scanner_type: Optional scanner type for filtering
        """
        if not self._reachability_analyzer:
            return

        # Filter for Trivy vulnerability findings (SCA)
        sca_findings = [
            f
            for f in findings
            if str(f.scanner.value).lower() == "trivy" and f.category == "vulnerability"
        ]

        if not sca_findings:
            return

        logger.info(f"Analyzing reachability for {len(sca_findings)} SCA findings...")

        for finding in sca_findings:
            pkg_name = self._extract_package_name(finding)

            if pkg_name:
                result = self._reachability_analyzer.analyze_dependency(pkg_name)
                finding.is_reachable = result.is_reachable
                finding.reachability_confidence = result.confidence

                if not finding.is_reachable:
                    logger.info(
                        f"Unreachable dependency: {pkg_name} "
                        f"(finding: {finding.finding_id})"
                    )

    def _extract_package_name(self, finding: Any) -> Optional[str]:
        """Extract package name from finding."""
        if finding.raw_data and "trivy_finding" in finding.raw_data:
            trivy_finding = finding.raw_data["trivy_finding"]
            if isinstance(trivy_finding, dict):
                return trivy_finding.get("pkg_name") or trivy_finding.get("PkgName")
            else:
                return getattr(trivy_finding, "pkg_name", None)
        return None

    def check_kev(self, cve_id: str) -> bool:
        """
        Check if CVE is in KEV database.

        Args:
            cve_id: CVE identifier

        Returns:
            True if CVE is actively exploited
        """
        if not self._kev_client:
            return False
        return self._kev_client.is_exploited(cve_id)
