"""
Priority Calculator for Security Findings.

Calculates priority scores using rule-based approach with optional ML enhancement.
Integrates with KEV (Known Exploited Vulnerabilities) for active exploit detection.
"""

import re
import logging
from typing import Optional, Dict, Any
from enum import Enum

logger = logging.getLogger(__name__)


class FindingSeverity(str, Enum):
    """Unified severity levels."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class PriorityCalculator:
    """
    Calculates priority scores for security findings.
    
    Supports:
    - Rule-based scoring (default)
    - ML-based scoring (optional)
    - KEV integration for active exploit detection
    
    Scoring factors:
    - Severity (40%)
    - Confidence (20%)
    - Fix availability (20%)
    - CWE/OWASP presence (10%)
    - Category (10%)
    
    Example:
        >>> calculator = PriorityCalculator()
        >>> score = calculator.calculate(finding)
        >>> print(f"Priority: {score}/100")
    """
    
    SEVERITY_WEIGHTS = {
        FindingSeverity.CRITICAL: 100,
        FindingSeverity.HIGH: 75,
        FindingSeverity.MEDIUM: 50,
        FindingSeverity.LOW: 25,
        FindingSeverity.INFO: 10,
    }
    
    CONFIDENCE_WEIGHTS = {
        "HIGH": 1.0,
        "MEDIUM": 0.7,
        "LOW": 0.4,
    }
    
    CATEGORY_WEIGHTS = {
        "injection": 100,
        "authentication": 95,
        "crypto": 85,
        "secret": 90,
        "deserialization": 80,
        "xxe": 75,
        "xss": 70,
        "ssrf": 70,
        "path-traversal": 65,
        "default": 50,
    }
    
    CVE_PATTERN = re.compile(r"CVE-\d{4}-\d{4,7}")
    
    def __init__(
        self,
        kev_client=None,
        ml_scorer=None,
        enable_ml: bool = False,
    ):
        """
        Initialize priority calculator.
        
        Args:
            kev_client: KEV client for active exploit detection
            ml_scorer: ML scorer for ML-based priority calculation
            enable_ml: Enable ML-based scoring
        """
        self._kev_client = kev_client
        self._ml_scorer = ml_scorer
        self.enable_ml = enable_ml and ml_scorer is not None
        
        logger.debug(
            f"PriorityCalculator initialized: ml={self.enable_ml}, kev={kev_client is not None}"
        )
    
    def calculate(self, finding) -> float:
        """
        Calculate priority score for a finding.
        
        Args:
            finding: UnifiedFinding object
            
        Returns:
            Priority score (0-100)
        """
        # Try ML scoring first
        if self.enable_ml and self._ml_scorer:
            try:
                return self._calculate_ml_score(finding)
            except Exception as e:
                logger.warning(f"ML scoring failed: {e}. Using rule-based.")
        
        return self._calculate_rule_based(finding)
    
    def _calculate_ml_score(self, finding) -> float:
        """Calculate score using ML model."""
        ml_result = self._ml_scorer.score(finding)
        
        # Store ML metadata
        finding.ml_score = ml_result.ml_score
        finding.ml_confidence_interval = ml_result.confidence_interval
        finding.epss_score = ml_result.epss_score
        
        logger.debug(
            f"ML Score: {ml_result.ml_score:.1f}/100 "
            f"(EPSS: {ml_result.epss_score * 100:.1f}%) "
            f"for {finding.finding_id}"
        )
        return ml_result.ml_score
    
    def _calculate_rule_based(self, finding) -> float:
        """Calculate score using rule-based approach."""
        # Check KEV first (highest priority)
        if self._kev_client:
            kev_score = self._check_kev(finding)
            if kev_score is not None:
                return kev_score
        
        score = 0.0
        
        # Severity (40%)
        severity_score = self._get_severity_score(finding.severity)
        score += severity_score * 0.4
        
        # Confidence (20%)
        confidence_score = self._get_confidence_score(finding.confidence)
        score += confidence_score * 0.2
        
        # Fix availability (20%)
        if finding.fix_available:
            score += 100 * 0.2
        
        # CWE/OWASP presence (10%)
        if finding.cwe_ids or finding.owasp_categories:
            score += 100 * 0.1
        
        # Category (10%)
        category_score = self._get_category_score(finding.category)
        score += category_score * 0.1
        
        return min(100.0, max(0.0, score))
    
    def _check_kev(self, finding) -> Optional[float]:
        """Check if finding is in KEV database."""
        cve_ids = self._extract_cves(finding)
        
        for cve in cve_ids:
            if self._kev_client.is_exploited(cve):
                finding.is_active_exploit = True
                finding.severity = FindingSeverity.CRITICAL
                logger.info(f"KEV Match: {cve} is actively exploited!")
                return 100.0
        
        return None
    
    def _extract_cves(self, finding) -> list:
        """Extract CVE IDs from finding."""
        cve_ids = []
        
        # From finding ID
        cve_ids.extend(self.CVE_PATTERN.findall(finding.finding_id))
        
        # From references
        for ref in finding.references:
            cve_ids.extend(self.CVE_PATTERN.findall(ref))
        
        # From title
        cve_ids.extend(self.CVE_PATTERN.findall(finding.title))
        
        return list(set(cve_ids))
    
    def _get_severity_score(self, severity) -> float:
        """Get score for severity level."""
        if isinstance(severity, str):
            severity = FindingSeverity(severity) if severity in [s.value for s in FindingSeverity] else None
        return self.SEVERITY_WEIGHTS.get(severity, 25)
    
    def _get_confidence_score(self, confidence: Optional[str]) -> float:
        """Get score for confidence level."""
        if not confidence:
            return 50  # Default medium
        return self.CONFIDENCE_WEIGHTS.get(confidence, 0.5) * 100
    
    def _get_category_score(self, category: str) -> float:
        """Get score for finding category."""
        if not category:
            return self.CATEGORY_WEIGHTS["default"]
        
        category_lower = category.lower()
        for key, score in self.CATEGORY_WEIGHTS.items():
            if key in category_lower:
                return score
        
        return self.CATEGORY_WEIGHTS["default"]
    
    def calculate_batch(self, findings: list) -> None:
        """Calculate priority scores for multiple findings in-place."""
        for finding in findings:
            finding.priority_score = self.calculate(finding)
