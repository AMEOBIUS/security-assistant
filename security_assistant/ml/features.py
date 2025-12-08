"""
Feature Extraction for ML-Based Vulnerability Scoring

Extracts features from UnifiedFinding objects for ML model training and inference.

Features extracted:
1. Severity (CRITICAL, HIGH, MEDIUM, LOW, INFO)
2. CVSS Score (0.0-10.0, extracted from CWE/references)
3. EPSS Score (0.0-1.0, from EPSS API)
4. Scanner type (Bandit, Semgrep, Trivy)
5. File type (.py, .js, .java, etc.)
6. Category (security, secret, misconfig, vulnerability)
7. Confidence (HIGH, MEDIUM, LOW)
8. Fix availability (boolean)
9. CWE presence (boolean)
10. OWASP presence (boolean)

Version: 1.0.0
"""

import logging
import re
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from pathlib import Path
from dataclasses import dataclass
import numpy as np

if TYPE_CHECKING:
    from ..orchestrator import UnifiedFinding, FindingSeverity, ScannerType
else:
    # Avoid circular import at runtime
    UnifiedFinding = Any
    FindingSeverity = Any
    ScannerType = Any


logger = logging.getLogger(__name__)


@dataclass
class FeatureVector:
    """
    Feature vector for ML model.
    
    Contains both numerical and categorical features extracted from a finding.
    """
    # Numerical features
    severity_numeric: float  # 0-4 (INFO=0, LOW=1, MEDIUM=2, HIGH=3, CRITICAL=4)
    cvss_score: float  # 0.0-10.0
    epss_score: float  # 0.0-1.0
    confidence_numeric: float  # 0-2 (LOW=0, MEDIUM=1, HIGH=2)
    has_fix: float  # 0 or 1
    has_cwe: float  # 0 or 1
    has_owasp: float  # 0 or 1
    reference_count: float  # Number of references
    
    # Categorical features (one-hot encoded)
    scanner_bandit: float  # 0 or 1
    scanner_semgrep: float  # 0 or 1
    scanner_trivy: float  # 0 or 1
    
    category_security: float  # 0 or 1
    category_secret: float  # 0 or 1
    category_misconfig: float  # 0 or 1
    category_vulnerability: float  # 0 or 1
    
    file_type_python: float  # 0 or 1
    file_type_javascript: float  # 0 or 1
    file_type_java: float  # 0 or 1
    file_type_go: float  # 0 or 1
    file_type_other: float  # 0 or 1
    
    # Metadata (not used in model, but useful for tracking)
    finding_id: str = ""
    
    def to_array(self) -> np.ndarray:
        """Convert to numpy array for model input."""
        return np.array([
            self.severity_numeric,
            self.cvss_score,
            self.epss_score,
            self.confidence_numeric,
            self.has_fix,
            self.has_cwe,
            self.has_owasp,
            self.reference_count,
            self.scanner_bandit,
            self.scanner_semgrep,
            self.scanner_trivy,
            self.category_security,
            self.category_secret,
            self.category_misconfig,
            self.category_vulnerability,
            self.file_type_python,
            self.file_type_javascript,
            self.file_type_java,
            self.file_type_go,
            self.file_type_other,
        ])
    
    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary for debugging/logging."""
        return {
            "severity_numeric": self.severity_numeric,
            "cvss_score": self.cvss_score,
            "epss_score": self.epss_score,
            "confidence_numeric": self.confidence_numeric,
            "has_fix": self.has_fix,
            "has_cwe": self.has_cwe,
            "has_owasp": self.has_owasp,
            "reference_count": self.reference_count,
            "scanner_bandit": self.scanner_bandit,
            "scanner_semgrep": self.scanner_semgrep,
            "scanner_trivy": self.scanner_trivy,
            "category_security": self.category_security,
            "category_secret": self.category_secret,
            "category_misconfig": self.category_misconfig,
            "category_vulnerability": self.category_vulnerability,
            "file_type_python": self.file_type_python,
            "file_type_javascript": self.file_type_javascript,
            "file_type_java": self.file_type_java,
            "file_type_go": self.file_type_go,
            "file_type_other": self.file_type_other,
        }
    
    @staticmethod
    def feature_names() -> List[str]:
        """Get feature names in order."""
        return [
            "severity_numeric",
            "cvss_score",
            "epss_score",
            "confidence_numeric",
            "has_fix",
            "has_cwe",
            "has_owasp",
            "reference_count",
            "scanner_bandit",
            "scanner_semgrep",
            "scanner_trivy",
            "category_security",
            "category_secret",
            "category_misconfig",
            "category_vulnerability",
            "file_type_python",
            "file_type_javascript",
            "file_type_java",
            "file_type_go",
            "file_type_other",
        ]


class FeatureExtractor:
    """
    Extract features from UnifiedFinding for ML model.
    
    Features:
    - Numerical: severity, CVSS, EPSS, confidence, etc.
    - Categorical: scanner, category, file type (one-hot encoded)
    
    Example:
        >>> extractor = FeatureExtractor()
        >>> features = extractor.extract(finding)
        >>> X = features.to_array()  # For model input
    """
    
    def __init__(self, epss_client: Optional[Any] = None):
        """
        Initialize feature extractor.
        
        Args:
            epss_client: Optional EPSS client for fetching exploit probabilities
        """
        self.epss_client = epss_client
        logger.info("Initialized FeatureExtractor")
    
    def extract(self, finding: "UnifiedFinding") -> FeatureVector:
        """
        Extract features from a UnifiedFinding.
        
        Args:
            finding: UnifiedFinding to extract features from
        
        Returns:
            FeatureVector with extracted features
        """
        # Numerical features
        from ..orchestrator import FindingSeverity, ScannerType
        
        severity_map = {
            FindingSeverity.INFO: 0.0,
            FindingSeverity.LOW: 1.0,
            FindingSeverity.MEDIUM: 2.0,
            FindingSeverity.HIGH: 3.0,
            FindingSeverity.CRITICAL: 4.0,
        }
        severity_numeric = severity_map.get(finding.severity, 2.0)
        cvss_score = self._extract_cvss_score(finding)
        epss_score = self._extract_epss_score(finding)
        confidence_numeric = self._extract_confidence(finding)
        has_fix = 1.0 if finding.fix_available else 0.0
        has_cwe = 1.0 if finding.cwe_ids else 0.0
        has_owasp = 1.0 if finding.owasp_categories else 0.0
        reference_count = float(len(finding.references))
        
        # Scanner one-hot encoding
        scanner_bandit = 1.0 if finding.scanner == ScannerType.BANDIT else 0.0
        scanner_semgrep = 1.0 if finding.scanner == ScannerType.SEMGREP else 0.0
        scanner_trivy = 1.0 if finding.scanner == ScannerType.TRIVY else 0.0
        
        # Category one-hot encoding
        category_security = 1.0 if finding.category == "security" else 0.0
        category_secret = 1.0 if finding.category == "secret" else 0.0
        category_misconfig = 1.0 if finding.category == "misconfig" else 0.0
        category_vulnerability = 1.0 if finding.category == "vulnerability" else 0.0
        
        # File type one-hot encoding
        file_type = self._extract_file_type(finding.file_path)
        file_type_python = 1.0 if file_type == "python" else 0.0
        file_type_javascript = 1.0 if file_type == "javascript" else 0.0
        file_type_java = 1.0 if file_type == "java" else 0.0
        file_type_go = 1.0 if file_type == "go" else 0.0
        file_type_other = 1.0 if file_type == "other" else 0.0
        
        return FeatureVector(
            severity_numeric=severity_numeric,
            cvss_score=cvss_score,
            epss_score=epss_score,
            confidence_numeric=confidence_numeric,
            has_fix=has_fix,
            has_cwe=has_cwe,
            has_owasp=has_owasp,
            reference_count=reference_count,
            scanner_bandit=scanner_bandit,
            scanner_semgrep=scanner_semgrep,
            scanner_trivy=scanner_trivy,
            category_security=category_security,
            category_secret=category_secret,
            category_misconfig=category_misconfig,
            category_vulnerability=category_vulnerability,
            file_type_python=file_type_python,
            file_type_javascript=file_type_javascript,
            file_type_java=file_type_java,
            file_type_go=file_type_go,
            file_type_other=file_type_other,
            finding_id=finding.finding_id,
        )
    
    def extract_batch(self, findings: List["UnifiedFinding"]) -> List[FeatureVector]:
        """
        Extract features from multiple findings.
        
        Args:
            findings: List of UnifiedFinding objects
        
        Returns:
            List of FeatureVector objects
        """
        return [self.extract(finding) for finding in findings]
    
    def _extract_severity(self, finding: "UnifiedFinding") -> float:
        """Extract severity as numeric value."""
        # Import here to avoid circular import
        from ..orchestrator import FindingSeverity
        
        severity_map = {
            FindingSeverity.INFO: 0.0,
            FindingSeverity.LOW: 1.0,
            FindingSeverity.MEDIUM: 2.0,
            FindingSeverity.HIGH: 3.0,
            FindingSeverity.CRITICAL: 4.0,
        }
        return severity_map.get(finding.severity, 2.0)
    
    def _extract_scanner(self, finding: "UnifiedFinding") -> tuple:
        """Extract scanner one-hot encoding."""
        # Import here to avoid circular import
        from ..orchestrator import ScannerType
        
        return (
            1.0 if finding.scanner == ScannerType.BANDIT else 0.0,
            1.0 if finding.scanner == ScannerType.SEMGREP else 0.0,
            1.0 if finding.scanner == ScannerType.TRIVY else 0.0,
        )
    
    def _extract_cvss_score(self, finding: "UnifiedFinding") -> float:
        """
        Extract CVSS score from finding.
        
        Tries to extract from:
        1. CWE IDs (lookup in database, future)
        2. References (parse CVSS from URLs)
        3. Fallback to severity-based estimate
        
        Returns:
            CVSS score (0.0-10.0)
        """
        from ..orchestrator import FindingSeverity
        
        # TODO: Implement CVSS lookup from CWE database
        # For now, use severity-based estimate
        severity_to_cvss = {
            FindingSeverity.CRITICAL: 9.0,
            FindingSeverity.HIGH: 7.5,
            FindingSeverity.MEDIUM: 5.0,
            FindingSeverity.LOW: 3.0,
            FindingSeverity.INFO: 1.0,
        }
        
        return severity_to_cvss.get(finding.severity, 5.0)
    
    def _extract_epss_score(self, finding: "UnifiedFinding") -> float:
        """
        Extract EPSS score from finding.
        
        Uses EPSS client to fetch exploit probability for CVEs.
        
        Returns:
            EPSS score (0.0-1.0), or 0.0 if not available
        """
        if not self.epss_client:
            return 0.0
        
        # Extract CVE IDs from finding
        cve_ids = self._extract_cve_ids(finding)
        
        if not cve_ids:
            return 0.0
        
        # Fetch EPSS scores for all CVEs
        try:
            epss_scores = self.epss_client.get_scores(cve_ids)
            # Return max EPSS score if multiple CVEs
            return max(epss_scores.values()) if epss_scores else 0.0
        except Exception as e:
            logger.warning(f"Failed to fetch EPSS scores: {e}")
            return 0.0
    
    def _extract_cve_ids(self, finding: "UnifiedFinding") -> List[str]:
        """
        Extract CVE IDs from finding.
        
        Searches in:
        - Title
        - Description
        - References
        
        Returns:
            List of CVE IDs (e.g., ["CVE-2024-1234"])
        """
        cve_pattern = r"CVE-\d{4}-\d{4,7}"
        cve_ids = set()
        
        # Search in title
        cve_ids.update(re.findall(cve_pattern, finding.title, re.IGNORECASE))
        
        # Search in description
        cve_ids.update(re.findall(cve_pattern, finding.description, re.IGNORECASE))
        
        # Search in references
        for ref in finding.references:
            cve_ids.update(re.findall(cve_pattern, ref, re.IGNORECASE))
        
        return list(cve_ids)
    
    def _extract_confidence(self, finding: "UnifiedFinding") -> float:
        """
        Extract confidence score.
        
        Returns:
            Confidence (0.0=LOW, 1.0=MEDIUM, 2.0=HIGH)
        """
        confidence_map = {
            "LOW": 0.0,
            "MEDIUM": 1.0,
            "HIGH": 2.0,
        }
        
        if not finding.confidence:
            return 1.0  # Default to MEDIUM
        
        return confidence_map.get(finding.confidence.upper(), 1.0)
    
    def _extract_file_type(self, file_path: str) -> str:
        """
        Extract file type from file path.
        
        Returns:
            File type: "python", "javascript", "java", "go", or "other"
        """
        file_type_map = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "javascript",
            ".tsx": "javascript",
            ".java": "java",
            ".go": "go",
        }
        
        ext = Path(file_path).suffix.lower()
        return file_type_map.get(ext, "other")
