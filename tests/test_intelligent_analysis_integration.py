import unittest
from unittest.mock import MagicMock, patch

from security_assistant.analysis.false_positive_detector import (
    FalsePositiveAnalysis,
    FalsePositiveDetector,
)
from security_assistant.enrichment.kev import KEVClient
from security_assistant.orchestrator import (
    FindingSeverity,
    ScannerType,
    ScanOrchestrator,
    UnifiedFinding,
)


class TestIntelligentAnalysisIntegration(unittest.TestCase):
    
    def setUp(self):
        # Mock KEV Client
        self.kev_client_mock = MagicMock(spec=KEVClient)
        # Default behavior: not exploited
        self.kev_client_mock.is_exploited.return_value = False
        
        # Mock FP Detector
        self.fp_detector_mock = MagicMock(spec=FalsePositiveDetector)
        # Default behavior: not FP
        default_analysis = FalsePositiveAnalysis(
            is_likely_false_positive=False,
            confidence=0.1,
            reasons=[],
            pattern_scores={}
        )
        self.fp_detector_mock.analyze_batch.return_value = {0: default_analysis}
        
        # Initialize Orchestrator with mocks enabled
        with patch('security_assistant.enrichment.kev.KEVClient', return_value=self.kev_client_mock), \
             patch('security_assistant.analysis.false_positive_detector.FalsePositiveDetector', return_value=self.fp_detector_mock):
            self.orchestrator = ScanOrchestrator(
                enable_kev=True,
                enable_fp_detection=True,
                enable_meta_security=False,
                enable_ml_scoring=False
            )
            
    def test_kev_boosting(self):
        """Test that active exploitation boosts priority to 100."""
        # Setup KEV match
        self.kev_client_mock.is_exploited.side_effect = lambda cve: cve == "CVE-2021-44228"
        
        finding = UnifiedFinding(
            finding_id="trivy-CVE-2021-44228-log4j",
            scanner=ScannerType.TRIVY,
            severity=FindingSeverity.HIGH,
            category="vulnerability",
            file_path="pom.xml",
            line_start=1,
            line_end=10,
            title="Log4Shell",
            description="Log4j vulnerability",
            code_snippet="",
            # UnifiedFinding parses finding_id for Trivy
        )
        
        score = self.orchestrator._calculate_priority_score(finding)
        
        self.assertEqual(score, 100.0)
        self.assertTrue(finding.is_active_exploit)
        self.assertEqual(finding.severity, FindingSeverity.CRITICAL)
        self.kev_client_mock.is_exploited.assert_called_with("CVE-2021-44228")

    def test_fp_detection(self):
        """Test that FP detection marks findings correctly."""
        # Setup FP match
        fp_analysis = FalsePositiveAnalysis(
            is_likely_false_positive=True,
            confidence=0.8,
            reasons=["Test code detected"],
            pattern_scores={"test_code": 0.9}
        )
        self.fp_detector_mock.analyze_batch.return_value = {0: fp_analysis}
        
        finding = UnifiedFinding(
            finding_id="bandit-101-test_auth.py-5",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.MEDIUM,
            category="security",
            file_path="tests/test_auth.py",
            line_start=5,
            line_end=5,
            title="Assert Used",
            description="Use of assert detected",
            code_snippet="assert True"
        )
        
        # Manually trigger detection since we are testing internal logic or mocking scan
        self.orchestrator._enrichment_service.detect_false_positives([finding])
        
        self.assertTrue(finding.is_false_positive)
        self.assertEqual(finding.fp_confidence, 0.8)
        self.assertEqual(finding.fp_reasons, ["Test code detected"])

    def test_calculate_priority_score_with_fp(self):
        """Test that FP detection is separate from priority score, but both work."""
        # This test ensures that enabling both doesn't crash
        finding = UnifiedFinding(
            finding_id="test-1",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.LOW,
            category="security",
            file_path="app.py",
            line_start=1,
            line_end=1,
            title="Test",
            description="Test",
            code_snippet=""
        )
        
        score = self.orchestrator._calculate_priority_score(finding)
        self.assertTrue(0 <= score <= 100)

if __name__ == '__main__':
    unittest.main()
