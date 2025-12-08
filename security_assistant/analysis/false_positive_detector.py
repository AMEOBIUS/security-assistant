"""
False Positive Detector

Detects likely false positives in security scan results.

Combines multiple pattern detectors:
- Test code detection
- Sanitization detection
- Mock data detection
- Safe context detection

Version: 1.0.0
"""

import logging
from typing import Dict, Optional
from dataclasses import dataclass

from security_assistant.analysis.patterns.test_code import TestCodePattern
from security_assistant.analysis.patterns.sanitization import SanitizationPattern
from security_assistant.analysis.patterns.mock_data import MockDataPattern
from security_assistant.analysis.patterns.safe_contexts import SafeContextPattern


logger = logging.getLogger(__name__)


@dataclass
class FalsePositiveAnalysis:
    """Analysis result for false positive detection."""
    is_likely_false_positive: bool
    confidence: float  # 0.0-1.0
    reasons: list[str]
    pattern_scores: Dict[str, float]


class FalsePositiveDetector:
    """
    Detects likely false positives in security findings.
    
    Uses multiple pattern detectors to identify findings that are
    unlikely to be real vulnerabilities:
    - Test code (test files, test functions)
    - Sanitized code (input validation, escaping)
    - Mock data (fixtures, test data)
    - Safe contexts (logging, comments)
    
    Example:
        >>> detector = FalsePositiveDetector()
        >>> analysis = detector.analyze(
        ...     file_path="tests/test_auth.py",
        ...     code="def test_sql_injection(): assert True"
        ... )
        >>> if analysis.is_likely_false_positive:
        ...     print(f"Likely FP: {analysis.reasons}")
    """
    
    # Confidence threshold for FP detection
    FP_THRESHOLD = 0.4  # 40% confidence → likely FP
    
    def __init__(
        self,
        fp_threshold: float = FP_THRESHOLD,
    ):
        """
        Initialize false positive detector.
        
        Args:
            fp_threshold: Confidence threshold for FP detection (0.0-1.0)
        """
        self.fp_threshold = fp_threshold
        
        # Initialize pattern detectors
        self.test_code = TestCodePattern()
        self.sanitization = SanitizationPattern()
        self.mock_data = MockDataPattern()
        self.safe_context = SafeContextPattern()
        
        logger.info(f"Initialized FalsePositiveDetector (threshold={fp_threshold})")
    
    def analyze(
        self,
        file_path: str,
        code: Optional[str] = None,
        vulnerability_type: Optional[str] = None,
    ) -> FalsePositiveAnalysis:
        """
        Analyze a finding for false positive likelihood.
        
        Args:
            file_path: File path where finding was detected
            code: Optional code snippet
            vulnerability_type: Optional vulnerability type (e.g., "SQL Injection")
        
        Returns:
            FalsePositiveAnalysis with confidence and reasons
        
        Example:
            >>> detector = FalsePositiveDetector()
            >>> analysis = detector.analyze(
            ...     file_path="tests/test_db.py",
            ...     code="mock_query = 'SELECT * FROM users'"
            ... )
            >>> print(f"FP: {analysis.is_likely_false_positive}")
            >>> print(f"Confidence: {analysis.confidence:.2f}")
            >>> print(f"Reasons: {analysis.reasons}")
        """
        reasons = []
        pattern_scores = {}
        
        # 1. Test code detection
        test_score = self.test_code.get_confidence(file_path, code)
        pattern_scores["test_code"] = test_score
        
        if test_score > 0.5:
            reasons.append(f"Test code detected (confidence: {test_score:.2f})")
        
        # 2. Sanitization detection (only if code provided)
        if code:
            sanitization_score = self.sanitization.get_confidence(code)
            pattern_scores["sanitization"] = sanitization_score
            
            if sanitization_score > 0.5:
                reasons.append(f"Input sanitization detected (confidence: {sanitization_score:.2f})")
        
        # 3. Mock data detection (only if code provided)
        if code:
            mock_score = self.mock_data.get_confidence(code)
            pattern_scores["mock_data"] = mock_score
            
            if mock_score > 0.5:
                reasons.append(f"Mock/test data detected (confidence: {mock_score:.2f})")
        
        # 4. Safe context detection (only if code provided)
        if code:
            safe_context_score = self.safe_context.get_confidence(code)
            pattern_scores["safe_context"] = safe_context_score
            
            if safe_context_score > 0.5:
                reasons.append(f"Safe context detected (confidence: {safe_context_score:.2f})")
        
        # Calculate overall confidence
        # Weighted average: test_code (50%), mock_data (30%), others (10% each)
        # Test code and mock data are strongest indicators of FP
        weights = {
            "test_code": 0.5,
            "sanitization": 0.1,
            "mock_data": 0.3,
            "safe_context": 0.1,
        }
        
        overall_confidence = sum(
            pattern_scores.get(pattern, 0.0) * weight
            for pattern, weight in weights.items()
        )
        
        # Determine if likely FP
        is_likely_fp = overall_confidence >= self.fp_threshold
        
        return FalsePositiveAnalysis(
            is_likely_false_positive=is_likely_fp,
            confidence=overall_confidence,
            reasons=reasons,
            pattern_scores=pattern_scores,
        )
    
    def analyze_batch(
        self,
        findings: list[Dict[str, str]],
    ) -> Dict[int, FalsePositiveAnalysis]:
        """
        Analyze multiple findings for false positives.
        
        Args:
            findings: List of findings, each with:
                - file_path: str
                - code: Optional[str]
                - vulnerability_type: Optional[str]
        
        Returns:
            Dictionary mapping finding index to FalsePositiveAnalysis
        
        Example:
            >>> detector = FalsePositiveDetector()
            >>> findings = [
            ...     {"file_path": "tests/test_auth.py", "code": "def test_login(): ..."},
            ...     {"file_path": "src/auth.py", "code": "def login(): ..."},
            ... ]
            >>> results = detector.analyze_batch(findings)
            >>> for idx, analysis in results.items():
            ...     print(f"Finding {idx}: FP={analysis.is_likely_false_positive}")
        """
        results = {}
        
        for idx, finding in enumerate(findings):
            analysis = self.analyze(
                file_path=finding.get("file_path", ""),
                code=finding.get("code"),
                vulnerability_type=finding.get("vulnerability_type"),
            )
            results[idx] = analysis
        
        logger.info(f"Analyzed {len(findings)} findings for false positives")
        
        return results
    
    def filter_false_positives(
        self,
        findings: list[Dict[str, str]],
    ) -> tuple[list[Dict[str, str]], list[Dict[str, str]]]:
        """
        Filter findings into likely real and likely false positives.
        
        Args:
            findings: List of findings
        
        Returns:
            Tuple of (real_findings, false_positives)
        
        Example:
            >>> detector = FalsePositiveDetector()
            >>> findings = [...]
            >>> real, fps = detector.filter_false_positives(findings)
            >>> print(f"Real: {len(real)}, FP: {len(fps)}")
        """
        real_findings = []
        false_positives = []
        
        analyses = self.analyze_batch(findings)
        
        for idx, finding in enumerate(findings):
            analysis = analyses[idx]
            
            if analysis.is_likely_false_positive:
                # Add FP analysis to finding
                finding["fp_analysis"] = {
                    "confidence": analysis.confidence,
                    "reasons": analysis.reasons,
                }
                false_positives.append(finding)
            else:
                real_findings.append(finding)
        
        logger.info(
            f"Filtered {len(findings)} findings: "
            f"{len(real_findings)} real, {len(false_positives)} FP"
        )
        
        return real_findings, false_positives
    
    def get_statistics(
        self,
        findings: list[Dict[str, str]],
    ) -> Dict[str, any]:
        """
        Get false positive statistics for findings.
        
        Args:
            findings: List of findings
        
        Returns:
            Dictionary with FP statistics
        
        Example:
            >>> detector = FalsePositiveDetector()
            >>> findings = [...]
            >>> stats = detector.get_statistics(findings)
            >>> print(f"FP rate: {stats['fp_rate']:.1%}")
        """
        analyses = self.analyze_batch(findings)
        
        total = len(findings)
        fps = sum(1 for a in analyses.values() if a.is_likely_false_positive)
        
        # Pattern breakdown
        pattern_counts = {
            "test_code": 0,
            "sanitization": 0,
            "mock_data": 0,
            "safe_context": 0,
        }
        
        for analysis in analyses.values():
            for pattern, score in analysis.pattern_scores.items():
                if score > 0.5:
                    pattern_counts[pattern] += 1
        
        return {
            "total": total,
            "false_positives": fps,
            "real_findings": total - fps,
            "fp_rate": fps / total if total > 0 else 0.0,
            "pattern_breakdown": pattern_counts,
        }
