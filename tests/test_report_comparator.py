"""
Tests for Report Comparator

Tests comparison functionality, trend analysis, and diff generation.
"""

import unittest
from datetime import datetime, timedelta
from pathlib import Path

from security_assistant.report_comparator import (
    ReportComparator,
    ComparisonResult,
    FindingDiff,
    FindingStatus,
    TrendDirection,
)
from security_assistant.orchestrator import (
    OrchestrationResult,
    UnifiedFinding,
    FindingSeverity,
    ScannerType,
)


class TestReportComparator(unittest.TestCase):
    """Test ReportComparator functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.comparator = ReportComparator()
        
        # Create sample findings
        self.finding1 = UnifiedFinding(
            finding_id="test-1",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.HIGH,
            category="security",
            file_path="app.py",
            line_start=10,
            line_end=10,
            title="SQL Injection",
            description="Possible SQL injection",
            code_snippet="query = 'SELECT * FROM users WHERE id=' + user_id",
            priority_score=85.0,
        )
        
        self.finding2 = UnifiedFinding(
            finding_id="test-2",
            scanner=ScannerType.SEMGREP,
            severity=FindingSeverity.MEDIUM,
            category="security",
            file_path="utils.py",
            line_start=25,
            line_end=25,
            title="Hardcoded Secret",
            description="Hardcoded API key",
            code_snippet="API_KEY = 'secret123'",
            priority_score=60.0,
        )
        
        self.finding3 = UnifiedFinding(
            finding_id="test-3",
            scanner=ScannerType.TRIVY,
            severity=FindingSeverity.CRITICAL,
            category="vulnerability",
            file_path="requirements.txt",
            line_start=5,
            line_end=5,
            title="CVE-2023-1234",
            description="Critical vulnerability in requests",
            code_snippet="requests==2.25.0",
            priority_score=95.0,
        )
        
        self.finding4 = UnifiedFinding(
            finding_id="test-4",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.LOW,
            category="security",
            file_path="config.py",
            line_start=15,
            line_end=15,
            title="Weak Crypto",
            description="Use of weak cryptographic algorithm",
            code_snippet="hashlib.md5(data)",
            priority_score=30.0,
        )
    
    def _create_scan_result(
        self,
        findings: list,
        scan_time: datetime = None
    ) -> OrchestrationResult:
        """Helper to create OrchestrationResult"""
        if scan_time is None:
            scan_time = datetime.now()
        
        result = OrchestrationResult(
            deduplicated_findings=findings,
            scan_time=scan_time,
            target="test_project",
        )
        
        # Calculate statistics
        result.total_findings = len(findings)
        for finding in findings:
            result.findings_by_severity[finding.severity] = \
                result.findings_by_severity.get(finding.severity, 0) + 1
        
        return result
    
    def test_comparator_initialization(self):
        """Test comparator initialization"""
        comparator = ReportComparator(
            matching_strategy="content",
            track_severity_changes=True
        )
        
        self.assertEqual(comparator.matching_strategy, "content")
        self.assertTrue(comparator.track_severity_changes)
    
    def test_compare_identical_scans(self):
        """Test comparing identical scans"""
        findings = [self.finding1, self.finding2]
        
        baseline = self._create_scan_result(findings)
        latest = self._create_scan_result(findings)
        
        result = self.comparator.compare(baseline, latest)
        
        self.assertEqual(result.total_new, 0)
        self.assertEqual(result.total_fixed, 0)
        self.assertEqual(result.total_changed, 0)
        self.assertEqual(result.total_unchanged, 2)
        self.assertEqual(result.trend_direction, TrendDirection.STABLE)
    
    def test_compare_new_findings(self):
        """Test detection of new findings"""
        baseline_findings = [self.finding1]
        latest_findings = [self.finding1, self.finding2, self.finding3]
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        
        self.assertEqual(result.total_new, 2)
        self.assertEqual(result.total_fixed, 0)
        self.assertEqual(result.total_unchanged, 1)
        
        # Check new findings
        new_titles = {f.finding.title for f in result.new_findings}
        self.assertIn("Hardcoded Secret", new_titles)
        self.assertIn("CVE-2023-1234", new_titles)
        
        # Should show degradation
        self.assertEqual(result.trend_direction, TrendDirection.DEGRADED)
    
    def test_compare_fixed_findings(self):
        """Test detection of fixed findings"""
        baseline_findings = [self.finding1, self.finding2, self.finding3]
        latest_findings = [self.finding1]
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        
        self.assertEqual(result.total_new, 0)
        self.assertEqual(result.total_fixed, 2)
        self.assertEqual(result.total_unchanged, 1)
        
        # Check fixed findings
        fixed_titles = {f.finding.title for f in result.fixed_findings}
        self.assertIn("Hardcoded Secret", fixed_titles)
        self.assertIn("CVE-2023-1234", fixed_titles)
        
        # Should show improvement
        self.assertEqual(result.trend_direction, TrendDirection.IMPROVED)
    
    def test_compare_severity_changes(self):
        """Test detection of severity changes"""
        # Create finding with different severity
        finding1_degraded = UnifiedFinding(
            finding_id="test-1",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.CRITICAL,  # Changed from HIGH
            category="security",
            file_path="app.py",
            line_start=10,
            line_end=10,
            title="SQL Injection",
            description="Possible SQL injection",
            code_snippet="query = 'SELECT * FROM users WHERE id=' + user_id",
            priority_score=95.0,
        )
        
        baseline_findings = [self.finding1]  # HIGH severity
        latest_findings = [finding1_degraded]  # CRITICAL severity
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        
        self.assertEqual(result.total_changed, 1)
        self.assertEqual(result.severity_degraded_count, 1)
        self.assertEqual(result.severity_improved_count, 0)
        
        # Check changed finding
        changed = result.changed_findings[0]
        self.assertEqual(changed.status, FindingStatus.CHANGED)
        self.assertTrue(changed.severity_changed)
        self.assertEqual(changed.previous_severity, FindingSeverity.HIGH)
        self.assertEqual(changed.finding.severity, FindingSeverity.CRITICAL)
        self.assertTrue(changed.severity_degraded)
        self.assertFalse(changed.severity_improved)
    
    def test_compare_severity_improvement(self):
        """Test detection of severity improvements"""
        # Create finding with improved severity
        finding1_improved = UnifiedFinding(
            finding_id="test-1",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.LOW,  # Improved from HIGH
            category="security",
            file_path="app.py",
            line_start=10,
            line_end=10,
            title="SQL Injection",
            description="Possible SQL injection",
            code_snippet="query = 'SELECT * FROM users WHERE id=' + user_id",
            priority_score=30.0,
        )
        
        baseline_findings = [self.finding1]  # HIGH severity
        latest_findings = [finding1_improved]  # LOW severity
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        
        self.assertEqual(result.total_changed, 1)
        self.assertEqual(result.severity_improved_count, 1)
        self.assertEqual(result.severity_degraded_count, 0)
        
        # Check changed finding
        changed = result.changed_findings[0]
        self.assertTrue(changed.severity_improved)
        self.assertFalse(changed.severity_degraded)
    
    def test_severity_breakdown(self):
        """Test severity breakdown calculation"""
        baseline_findings = [self.finding1, self.finding2]  # HIGH, MEDIUM
        latest_findings = [self.finding1, self.finding3, self.finding4]  # HIGH, CRITICAL, LOW
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        
        # Check baseline counts
        self.assertEqual(result.baseline_severity_counts[FindingSeverity.HIGH], 1)
        self.assertEqual(result.baseline_severity_counts[FindingSeverity.MEDIUM], 1)
        
        # Check latest counts
        self.assertEqual(result.latest_severity_counts[FindingSeverity.CRITICAL], 1)
        self.assertEqual(result.latest_severity_counts[FindingSeverity.HIGH], 1)
        self.assertEqual(result.latest_severity_counts[FindingSeverity.LOW], 1)
        
        # Check deltas
        self.assertEqual(result.severity_delta[FindingSeverity.CRITICAL], 1)
        self.assertEqual(result.severity_delta[FindingSeverity.HIGH], 0)
        self.assertEqual(result.severity_delta[FindingSeverity.MEDIUM], -1)
        self.assertEqual(result.severity_delta[FindingSeverity.LOW], 1)
    
    def test_has_new_critical(self):
        """Test detection of new critical findings"""
        baseline_findings = [self.finding1]
        latest_findings = [self.finding1, self.finding3]  # Add CRITICAL
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        
        self.assertTrue(result.has_new_critical)
        self.assertFalse(result.has_new_high)
    
    def test_has_new_high(self):
        """Test detection of new high findings"""
        baseline_findings = [self.finding2]
        latest_findings = [self.finding1, self.finding2]  # Add HIGH
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        
        self.assertTrue(result.has_new_high)
        self.assertFalse(result.has_new_critical)
    
    def test_critical_and_high_fixed(self):
        """Test counting of fixed critical/high findings"""
        baseline_findings = [self.finding1, self.finding3]  # HIGH, CRITICAL
        latest_findings = [self.finding2]  # MEDIUM
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        
        self.assertEqual(result.critical_fixed, 1)
        self.assertEqual(result.high_fixed, 1)
    
    def test_net_change(self):
        """Test net change calculation"""
        baseline_findings = [self.finding1, self.finding2]
        latest_findings = [self.finding1, self.finding3, self.finding4]
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        
        # 2 new, 1 fixed = +1 net change
        self.assertEqual(result.net_change, 1)
    
    def test_improvement_percentage(self):
        """Test improvement percentage calculation"""
        baseline_findings = [self.finding1, self.finding2, self.finding3, self.finding4]  # 4 findings
        latest_findings = [self.finding1, self.finding2]  # 2 findings
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        
        # (4 - 2) / 4 * 100 = 50% improvement
        self.assertEqual(result.improvement_percentage, 50.0)
    
    def test_degradation_percentage(self):
        """Test degradation percentage calculation"""
        baseline_findings = [self.finding1]  # 1 finding
        latest_findings = [self.finding1, self.finding2, self.finding3]  # 3 findings
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        
        # (1 - 3) / 1 * 100 = -200% (degradation)
        self.assertEqual(result.improvement_percentage, -200.0)
    
    def test_trend_score_calculation(self):
        """Test trend score calculation"""
        # Fix critical and high findings
        baseline_findings = [self.finding1, self.finding3]  # HIGH, CRITICAL
        latest_findings = [self.finding4]  # LOW
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        
        # Should have positive trend score (fixed critical + high)
        self.assertGreater(result.trend_score, 0)
        self.assertEqual(result.trend_direction, TrendDirection.IMPROVED)
    
    def test_generate_summary(self):
        """Test summary generation"""
        baseline_findings = [self.finding1, self.finding2]
        latest_findings = [self.finding1, self.finding3]
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        summary = self.comparator.generate_summary(result)
        
        # Check summary contains key information
        self.assertIn("SECURITY SCAN COMPARISON REPORT", summary)
        self.assertIn("New findings:", summary)
        self.assertIn("Fixed findings:", summary)
        self.assertIn("Severity Breakdown:", summary)
        self.assertIn(result.trend_direction.value, summary)
    
    def test_get_top_new_findings(self):
        """Test getting top new findings"""
        baseline_findings = []
        latest_findings = [self.finding1, self.finding2, self.finding3, self.finding4]
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        top_new = self.comparator.get_top_new_findings(result, limit=2)
        
        self.assertEqual(len(top_new), 2)
        # Should be sorted by priority score
        self.assertEqual(top_new[0].finding.title, "CVE-2023-1234")  # 95.0
        self.assertEqual(top_new[1].finding.title, "SQL Injection")  # 85.0
    
    def test_get_top_fixed_findings(self):
        """Test getting top fixed findings"""
        baseline_findings = [self.finding1, self.finding2, self.finding3, self.finding4]
        latest_findings = []
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        top_fixed = self.comparator.get_top_fixed_findings(result, limit=2)
        
        self.assertEqual(len(top_fixed), 2)
        # Should be sorted by priority score
        self.assertEqual(top_fixed[0].finding.title, "CVE-2023-1234")  # 95.0
        self.assertEqual(top_fixed[1].finding.title, "SQL Injection")  # 85.0
    
    def test_empty_baseline(self):
        """Test comparison with empty baseline"""
        baseline_findings = []
        latest_findings = [self.finding1, self.finding2]
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        
        self.assertEqual(result.total_new, 2)
        self.assertEqual(result.total_fixed, 0)
        self.assertEqual(result.total_unchanged, 0)
    
    def test_empty_latest(self):
        """Test comparison with empty latest scan"""
        baseline_findings = [self.finding1, self.finding2]
        latest_findings = []
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        
        self.assertEqual(result.total_new, 0)
        self.assertEqual(result.total_fixed, 2)
        self.assertEqual(result.total_unchanged, 0)
        self.assertEqual(result.trend_direction, TrendDirection.IMPROVED)
    
    def test_both_empty(self):
        """Test comparison with both scans empty"""
        baseline_findings = []
        latest_findings = []
        
        baseline = self._create_scan_result(baseline_findings)
        latest = self._create_scan_result(latest_findings)
        
        result = self.comparator.compare(baseline, latest)
        
        self.assertEqual(result.total_new, 0)
        self.assertEqual(result.total_fixed, 0)
        self.assertEqual(result.total_unchanged, 0)
        self.assertEqual(result.trend_direction, TrendDirection.STABLE)


class TestMatchingStrategies(unittest.TestCase):
    """Test different matching strategies"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.finding_v1 = UnifiedFinding(
            finding_id="test-1",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.HIGH,
            category="security",
            file_path="app.py",
            line_start=10,
            line_end=10,
            title="SQL Injection",
            description="Possible SQL injection",
            code_snippet="query = 'SELECT * FROM users WHERE id=' + user_id",
            priority_score=85.0,
        )
        
        # Same location, different content
        self.finding_v2_same_location = UnifiedFinding(
            finding_id="test-2",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.HIGH,
            category="security",
            file_path="app.py",
            line_start=10,
            line_end=10,
            title="Different Issue",
            description="Different description",
            code_snippet="different code",
            priority_score=85.0,
        )
        
        # Same content, different location
        self.finding_v2_same_content = UnifiedFinding(
            finding_id="test-3",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.HIGH,
            category="security",
            file_path="app.py",
            line_start=20,  # Different line
            line_end=20,
            title="SQL Injection",
            description="Possible SQL injection",
            code_snippet="query = 'SELECT * FROM users WHERE id=' + user_id",
            priority_score=85.0,
        )
    
    def _create_scan_result(self, findings: list) -> OrchestrationResult:
        """Helper to create OrchestrationResult"""
        result = OrchestrationResult(
            deduplicated_findings=findings,
            scan_time=datetime.now(),
            target="test_project",
        )
        result.total_findings = len(findings)
        return result
    
    def test_content_matching_strategy(self):
        """Test content-based matching"""
        comparator = ReportComparator(matching_strategy="content")
        
        baseline = self._create_scan_result([self.finding_v1])
        latest = self._create_scan_result([self.finding_v2_same_content])
        
        result = comparator.compare(baseline, latest)
        
        # Should match by content (same title + code)
        self.assertEqual(result.total_unchanged, 1)
        self.assertEqual(result.total_new, 0)
    
    def test_location_matching_strategy(self):
        """Test location-based matching"""
        comparator = ReportComparator(matching_strategy="location")
        
        baseline = self._create_scan_result([self.finding_v1])
        latest = self._create_scan_result([self.finding_v2_same_location])
        
        result = comparator.compare(baseline, latest)
        
        # Should match by location (same file + line)
        self.assertEqual(result.total_unchanged, 1)
        self.assertEqual(result.total_new, 0)
    
    def test_both_matching_strategy(self):
        """Test both content and location matching"""
        comparator = ReportComparator(matching_strategy="both")
        
        # Same location but different content - should NOT match
        baseline = self._create_scan_result([self.finding_v1])
        latest = self._create_scan_result([self.finding_v2_same_location])
        
        result = comparator.compare(baseline, latest)
        
        self.assertEqual(result.total_new, 1)
        self.assertEqual(result.total_fixed, 1)
        self.assertEqual(result.total_unchanged, 0)


if __name__ == "__main__":
    unittest.main()
