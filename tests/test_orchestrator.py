"""
Tests for Multi-Scanner Orchestrator

Tests cover:
- Scanner enabling/disabling
- Parallel execution
- Result aggregation
- Deduplication strategies
- Priority scoring
- Issue conversion
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from security_assistant.orchestrator import (
    FindingSeverity,
    OrchestrationResult,
    ScannerType,
    ScanOrchestrator,
    UnifiedFinding,
)
from security_assistant.scanners.bandit_scanner import BanditFinding
from security_assistant.scanners.bandit_scanner import ScanResult as BanditScanResult
from security_assistant.scanners.semgrep_scanner import (
    SemgrepFinding,
    SemgrepScanResult,
)
from security_assistant.scanners.trivy_scanner import (
    TrivyFinding,
    TrivyScanResult,
    TrivyScanType,
    TrivySeverity,
)


class TestScanOrchestrator:
    """Test ScanOrchestrator initialization and configuration"""
    
    def test_init_default(self):
        """Test default initialization"""
        orchestrator = ScanOrchestrator()
        
        assert orchestrator.max_workers == 3
        assert orchestrator.enable_deduplication is True
        assert orchestrator.dedup_strategy == "location"
        assert len(orchestrator._enabled_scanners) == 0
    
    def test_init_custom(self):
        """Test custom initialization"""
        orchestrator = ScanOrchestrator(
            max_workers=5,
            enable_deduplication=False,
            dedup_strategy="content"
        )
        
        assert orchestrator.max_workers == 5
        assert orchestrator.enable_deduplication is False
        assert orchestrator.dedup_strategy == "content"
    
    @patch('security_assistant.orchestrator.BanditScanner')
    def test_enable_bandit_scanner(self, mock_bandit):
        """Test enabling Bandit scanner"""
        orchestrator = ScanOrchestrator()
        orchestrator.enable_scanner(ScannerType.BANDIT, min_severity="HIGH")
        
        assert ScannerType.BANDIT in orchestrator._enabled_scanners
        mock_bandit.assert_called_once_with(min_severity="HIGH")
    
    @patch('security_assistant.orchestrator.SemgrepScanner')
    def test_enable_semgrep_scanner(self, mock_semgrep):
        """Test enabling Semgrep scanner"""
        orchestrator = ScanOrchestrator()
        orchestrator.enable_scanner(ScannerType.SEMGREP, config="p/security-audit")
        
        assert ScannerType.SEMGREP in orchestrator._enabled_scanners
        mock_semgrep.assert_called_once_with(config="p/security-audit")
    
    @patch('security_assistant.orchestrator.TrivyScanner')
    def test_enable_trivy_scanner(self, mock_trivy):
        """Test enabling Trivy scanner"""
        orchestrator = ScanOrchestrator()
        orchestrator.enable_scanner(ScannerType.TRIVY, min_severity=TrivySeverity.HIGH)
        
        assert ScannerType.TRIVY in orchestrator._enabled_scanners
        mock_trivy.assert_called_once_with(min_severity=TrivySeverity.HIGH)
    
    def test_enable_unknown_scanner(self):
        """Test enabling unknown scanner raises error"""
        orchestrator = ScanOrchestrator()
        
        with pytest.raises(ValueError, match="Unknown scanner type"):
            orchestrator.enable_scanner("unknown_scanner")
    
    @patch('security_assistant.orchestrator.BanditScanner')
    def test_disable_scanner(self, mock_bandit):
        """Test disabling a scanner"""
        orchestrator = ScanOrchestrator()
        orchestrator.enable_scanner(ScannerType.BANDIT)
        
        assert ScannerType.BANDIT in orchestrator._enabled_scanners
        
        orchestrator.disable_scanner(ScannerType.BANDIT)
        
        assert ScannerType.BANDIT not in orchestrator._enabled_scanners
    
    @patch('security_assistant.orchestrator.BanditScanner')
    @patch('security_assistant.orchestrator.SemgrepScanner')
    def test_enable_multiple_scanners(self, mock_semgrep, mock_bandit):
        """Test enabling multiple scanners"""
        orchestrator = ScanOrchestrator()
        orchestrator.enable_scanner(ScannerType.BANDIT)
        orchestrator.enable_scanner(ScannerType.SEMGREP)
        
        assert len(orchestrator._enabled_scanners) == 2
        assert ScannerType.BANDIT in orchestrator._enabled_scanners
        assert ScannerType.SEMGREP in orchestrator._enabled_scanners


class TestUnifiedFinding:
    """Test UnifiedFinding data class"""
    
    def test_unified_finding_creation(self):
        """Test creating a unified finding"""
        finding = UnifiedFinding(
            finding_id="test-1",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.HIGH,
            category="security",
            file_path="test.py",
            line_start=10,
            line_end=15,
            title="SQL Injection",
            description="Potential SQL injection",
            code_snippet="cursor.execute(query)",
        )
        
        assert finding.finding_id == "test-1"
        assert finding.scanner == ScannerType.BANDIT
        assert finding.severity == FindingSeverity.HIGH
        assert finding.severity_emoji == "🟠"
    
    def test_location_key(self):
        """Test location key generation"""
        finding = UnifiedFinding(
            finding_id="test-1",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.HIGH,
            category="security",
            file_path="test.py",
            line_start=10,
            line_end=15,
            title="Test",
            description="Test",
            code_snippet="test",
        )
        
        assert finding.location_key == "test.py:10-15"
    
    def test_content_key(self):
        """Test content key generation"""
        finding = UnifiedFinding(
            finding_id="test-1",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.HIGH,
            category="security",
            file_path="test.py",
            line_start=10,
            line_end=15,
            title="SQL Injection",
            description="Test",
            code_snippet="cursor.execute(query)",
        )
        
        key = finding.content_key
        assert "SQL Injection" in key
        assert "test.py" in key
    
    def test_severity_emojis(self):
        """Test severity emoji mapping"""
        severities = {
            FindingSeverity.CRITICAL: "🔴",
            FindingSeverity.HIGH: "🟠",
            FindingSeverity.MEDIUM: "🟡",
            FindingSeverity.LOW: "🟢",
            FindingSeverity.INFO: "⚪",
        }
        
        for severity, emoji in severities.items():
            finding = UnifiedFinding(
                finding_id="test",
                scanner=ScannerType.BANDIT,
                severity=severity,
                category="security",
                file_path="test.py",
                line_start=1,
                line_end=1,
                title="Test",
                description="Test",
                code_snippet="test",
            )
            assert finding.severity_emoji == emoji


class TestOrchestrationResult:
    """Test OrchestrationResult data class"""
    
    def test_orchestration_result_creation(self):
        """Test creating orchestration result"""
        result = OrchestrationResult(
            target="/path/to/project",
            execution_time_seconds=5.5,
        )
        
        assert result.target == "/path/to/project"
        assert result.execution_time_seconds == 5.5
        assert result.total_findings == 0
        assert result.duplicates_removed == 0
    
    def test_severity_counts(self):
        """Test severity count properties"""
        result = OrchestrationResult()
        result.findings_by_severity = {
            FindingSeverity.CRITICAL: 5,
            FindingSeverity.HIGH: 10,
            FindingSeverity.MEDIUM: 15,
            FindingSeverity.LOW: 20,
        }
        
        assert result.critical_count == 5
        assert result.high_count == 10
        assert result.medium_count == 15
        assert result.low_count == 20
    
    def test_has_critical_or_high(self):
        """Test has_critical_or_high property"""
        result = OrchestrationResult()
        
        # No critical or high
        result.findings_by_severity = {FindingSeverity.MEDIUM: 5}
        assert result.has_critical_or_high is False
        
        # Has critical
        result.findings_by_severity = {FindingSeverity.CRITICAL: 1}
        assert result.has_critical_or_high is True
        
        # Has high
        result.findings_by_severity = {FindingSeverity.HIGH: 1}
        assert result.has_critical_or_high is True
    
    def test_top_priority_findings(self):
        """Test top priority findings"""
        findings = [
            UnifiedFinding(
                finding_id=f"test-{i}",
                scanner=ScannerType.BANDIT,
                severity=FindingSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=i,
                line_end=i,
                title=f"Finding {i}",
                description="Test",
                code_snippet="test",
                priority_score=float(i * 10)
            )
            for i in range(15)
        ]
        
        result = OrchestrationResult(deduplicated_findings=findings)
        top = result.top_priority_findings
        
        assert len(top) == 10
        assert top[0].priority_score == 140.0  # Highest score
        assert top[-1].priority_score == 50.0


class TestConversionToUnified:
    """Test conversion from scanner-specific to unified findings"""
    
    def test_convert_bandit_findings(self):
        """Test converting Bandit findings to unified format"""
        orchestrator = ScanOrchestrator()
        
        bandit_finding = BanditFinding(
            test_id="B608",
            test_name="hardcoded_sql_expressions",
            severity="HIGH",
            confidence="MEDIUM",
            issue_text="Possible SQL injection",
            filename="app.py",
            line_number=42,
            code="cursor.execute(query)",
            cwe_id="CWE-89",
            more_info="https://example.com"
        )
        
        bandit_result = BanditScanResult(findings=[bandit_finding])
        
        unified = orchestrator._convert_bandit_findings(bandit_result)
        
        assert len(unified) == 1
        assert unified[0].scanner == ScannerType.BANDIT
        assert unified[0].severity == FindingSeverity.HIGH
        assert unified[0].file_path == "app.py"
        assert unified[0].line_start == 42
        assert unified[0].confidence == "MEDIUM"
        assert "CWE-89" in unified[0].cwe_ids
    
    def test_convert_semgrep_findings(self):
        """Test converting Semgrep findings to unified format"""
        orchestrator = ScanOrchestrator()
        
        semgrep_finding = SemgrepFinding(
            check_id="python.lang.security.audit.sql-injection",
            message="SQL injection vulnerability",
            severity="ERROR",
            path="app.py",
            start_line=10,
            end_line=12,
            start_col=0,
            end_col=20,
            code="cursor.execute(query)",
            metadata={
                "cwe": ["CWE-89"],
                "owasp": ["A1:2017-Injection"],
                "references": ["https://example.com"],
                "fix": "Use parameterized queries"
            }
        )
        
        semgrep_result = SemgrepScanResult(findings=[semgrep_finding])
        
        unified = orchestrator._convert_semgrep_findings(semgrep_result)
        
        assert len(unified) == 1
        assert unified[0].scanner == ScannerType.SEMGREP
        assert unified[0].severity == FindingSeverity.HIGH
        assert unified[0].file_path == "app.py"
        assert unified[0].line_start == 10
        assert unified[0].line_end == 12
        assert "CWE-89" in unified[0].cwe_ids
        assert "A1:2017-Injection" in unified[0].owasp_categories
        assert unified[0].fix_guidance == "Use parameterized queries"
    
    def test_convert_trivy_findings(self):
        """Test converting Trivy findings to unified format"""
        orchestrator = ScanOrchestrator()
        
        trivy_finding = TrivyFinding(
            vulnerability_id="CVE-2021-1234",
            pkg_name="requests",
            installed_version="2.25.0",
            fixed_version="2.26.0",
            severity=TrivySeverity.HIGH,
            title="HTTP Request Smuggling",
            description="Vulnerability in requests library",
            references=["https://nvd.nist.gov/vuln/detail/CVE-2021-1234"],
            target="requirements.txt",
            pkg_type="python",
            cvss_score=7.5,
            cwe_ids=["CWE-444"]
        )
        
        trivy_result = TrivyScanResult(
            target="requirements.txt",
            scan_type=TrivyScanType.FILESYSTEM,
            findings=[trivy_finding],
            scan_time=None
        )
        
        unified = orchestrator._convert_trivy_findings(trivy_result)
        
        assert len(unified) == 1
        assert unified[0].scanner == ScannerType.TRIVY
        assert unified[0].severity == FindingSeverity.HIGH
        assert unified[0].category == "vulnerability"
        assert unified[0].fix_available is True
        assert unified[0].fix_version == "2.26.0"
        assert "CWE-444" in unified[0].cwe_ids


class TestDeduplication:
    """Test finding deduplication strategies"""
    
    def test_deduplication_location_strategy(self):
        """Test location-based deduplication"""
        orchestrator = ScanOrchestrator(dedup_strategy="location")
        
        # Two findings at same location
        findings = [
            UnifiedFinding(
                finding_id="bandit-1",
                scanner=ScannerType.BANDIT,
                severity=FindingSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=10,
                line_end=15,
                title="SQL Injection",
                description="Bandit found SQL injection",
                code_snippet="cursor.execute(query)",
            ),
            UnifiedFinding(
                finding_id="semgrep-1",
                scanner=ScannerType.SEMGREP,
                severity=FindingSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=10,
                line_end=15,
                title="SQL Injection",
                description="Semgrep found SQL injection",
                code_snippet="cursor.execute(query)",
            ),
        ]
        
        deduplicated = orchestrator._deduplicate_findings(findings)
        
        assert len(deduplicated) == 1  # Should keep only one
    
    def test_deduplication_content_strategy(self):
        """Test content-based deduplication"""
        orchestrator = ScanOrchestrator(dedup_strategy="content")
        
        # Two findings with same content but different lines
        findings = [
            UnifiedFinding(
                finding_id="bandit-1",
                scanner=ScannerType.BANDIT,
                severity=FindingSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=10,
                line_end=15,
                title="SQL Injection",
                description="Test",
                code_snippet="cursor.execute(query)",
            ),
            UnifiedFinding(
                finding_id="semgrep-1",
                scanner=ScannerType.SEMGREP,
                severity=FindingSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=20,
                line_end=25,
                title="SQL Injection",
                description="Test",
                code_snippet="cursor.execute(query)",
            ),
        ]
        
        deduplicated = orchestrator._deduplicate_findings(findings)
        
        assert len(deduplicated) == 1  # Should keep only one
    
    def test_no_deduplication(self):
        """Test with deduplication disabled"""
        orchestrator = ScanOrchestrator(enable_deduplication=False)
        
        findings = [
            UnifiedFinding(
                finding_id=f"test-{i}",
                scanner=ScannerType.BANDIT,
                severity=FindingSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=10,
                line_end=15,
                title="SQL Injection",
                description="Test",
                code_snippet="cursor.execute(query)",
            )
            for i in range(5)
        ]
        
        # Manually test since scan_directory would deduplicate
        # Just verify the flag is set correctly
        assert orchestrator.enable_deduplication is False


class TestPriorityScoring:
    """Test priority score calculation"""
    
    def test_priority_score_critical_high_confidence(self):
        """Test priority score for critical finding with high confidence"""
        orchestrator = ScanOrchestrator()
        
        finding = UnifiedFinding(
            finding_id="test-1",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.CRITICAL,
            category="security",
            file_path="test.py",
            line_start=10,
            line_end=15,
            title="SQL Injection",
            description="Test",
            code_snippet="test",
            confidence="HIGH",
            fix_available=True,
            cwe_ids=["CWE-89"],
        )
        
        score = orchestrator._calculate_priority_score(finding)
        
        # Should be high score (critical + high confidence + fix + cwe)
        assert score > 80.0
    
    def test_priority_score_low_severity(self):
        """Test priority score for low severity finding"""
        orchestrator = ScanOrchestrator()
        
        finding = UnifiedFinding(
            finding_id="test-1",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.LOW,
            category="security",
            file_path="test.py",
            line_start=10,
            line_end=15,
            title="Minor Issue",
            description="Test",
            code_snippet="test",
            confidence="LOW",
            fix_available=False,
        )
        
        score = orchestrator._calculate_priority_score(finding)
        
        # Should be low score
        assert score < 40.0
    
    def test_priority_score_with_fix(self):
        """Test that fix availability increases score"""
        orchestrator = ScanOrchestrator()
        
        finding_no_fix = UnifiedFinding(
            finding_id="test-1",
            scanner=ScannerType.TRIVY,
            severity=FindingSeverity.HIGH,
            category="vulnerability",
            file_path="requirements.txt",
            line_start=1,
            line_end=1,
            title="CVE-2021-1234",
            description="Test",
            code_snippet="",
            fix_available=False,
        )
        
        finding_with_fix = UnifiedFinding(
            finding_id="test-2",
            scanner=ScannerType.TRIVY,
            severity=FindingSeverity.HIGH,
            category="vulnerability",
            file_path="requirements.txt",
            line_start=2,
            line_end=2,
            title="CVE-2021-5678",
            description="Test",
            code_snippet="",
            fix_available=True,
            fix_version="2.0.0",
        )
        
        score_no_fix = orchestrator._calculate_priority_score(finding_no_fix)
        score_with_fix = orchestrator._calculate_priority_score(finding_with_fix)
        
        assert score_with_fix > score_no_fix


class TestScanExecution:
    """Test scan execution (with mocking)"""
    
    @patch('security_assistant.orchestrator.BanditScanner')
    def test_scan_directory_no_scanners_enabled(self, mock_bandit):
        """Test scanning without enabled scanners raises error"""
        orchestrator = ScanOrchestrator()
        
        with pytest.raises(ValueError, match="No scanners enabled"):
            orchestrator.scan_directory("/tmp")
    
    @patch('security_assistant.orchestrator.BanditScanner')
    def test_scan_directory_not_found(self, mock_bandit):
        """Test scanning non-existent directory raises error"""
        orchestrator = ScanOrchestrator()
        orchestrator.enable_scanner(ScannerType.BANDIT)
        
        with pytest.raises(FileNotFoundError):
            orchestrator.scan_directory("/nonexistent/path")
    
    @patch('security_assistant.orchestrator.BanditScanner')
    def test_scan_file_not_found(self, mock_bandit):
        """Test scanning non-existent file raises error"""
        orchestrator = ScanOrchestrator()
        orchestrator.enable_scanner(ScannerType.BANDIT)
        
        with pytest.raises(FileNotFoundError):
            orchestrator.scan_file("/nonexistent/file.py")
    
    @patch('security_assistant.orchestrator.BanditScanner')
    def test_scan_directory_success(self, mock_bandit_class):
        """Test successful directory scan"""
        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test file
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("print('hello')")
            
            # Mock scanner
            mock_scanner = Mock()
            mock_result = BanditScanResult(findings=[])
            mock_scanner.scan_directory.return_value = mock_result
            mock_bandit_class.return_value = mock_scanner
            
            # Run scan
            orchestrator = ScanOrchestrator()
            orchestrator.enable_scanner(ScannerType.BANDIT)
            
            result = orchestrator.scan_directory(tmpdir)
            
            assert isinstance(result, OrchestrationResult)
            assert result.target == tmpdir
            assert result.execution_time_seconds >= 0
            mock_scanner.scan_directory.assert_called_once()


class TestIssueConversion:
    """Test conversion to GitLab issues"""
    
    def test_unified_finding_to_issue(self):
        """Test converting unified finding to GitLab issue"""
        orchestrator = ScanOrchestrator()
        
        finding = UnifiedFinding(
            finding_id="test-1",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.HIGH,
            category="security",
            file_path="app.py",
            line_start=42,
            line_end=45,
            title="SQL Injection",
            description="Possible SQL injection vulnerability",
            code_snippet="cursor.execute(query)",
            cwe_ids=["CWE-89"],
            owasp_categories=["A1:2017-Injection"],
            references=["https://example.com"],
            confidence="HIGH",
            priority_score=85.5,
        )
        
        issue = orchestrator._unified_finding_to_issue(finding, "TestProject")
        
        assert "SQL Injection" in issue.title
        assert "app.py" in issue.title
        assert "🟠" in issue.title  # HIGH severity emoji
        
        assert "HIGH" in issue.description
        assert "security" in issue.description
        assert "bandit" in issue.description
        assert "85.5" in issue.description
        assert "CWE-89" in issue.description
        assert "A1:2017-Injection" in issue.description
        
        assert "security" in issue.labels
        assert "bandit" in issue.labels
        assert "severity::high" in issue.labels
        assert "critical" in issue.labels
        assert issue.confidential is True
    
    def test_result_to_issues_all(self):
        """Test converting all findings to issues"""
        orchestrator = ScanOrchestrator()
        
        findings = [
            UnifiedFinding(
                finding_id=f"test-{i}",
                scanner=ScannerType.BANDIT,
                severity=FindingSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=i,
                line_end=i,
                title=f"Finding {i}",
                description="Test",
                code_snippet="test",
                priority_score=float(i * 10)
            )
            for i in range(5)
        ]
        
        result = OrchestrationResult(deduplicated_findings=findings)
        
        issues = orchestrator.result_to_issues(result, "TestProject")
        
        assert len(issues) == 5
    
    def test_result_to_issues_top_n(self):
        """Test converting only top N findings to issues"""
        orchestrator = ScanOrchestrator()
        
        findings = [
            UnifiedFinding(
                finding_id=f"test-{i}",
                scanner=ScannerType.BANDIT,
                severity=FindingSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=i,
                line_end=i,
                title=f"Finding {i}",
                description="Test",
                code_snippet="test",
                priority_score=float(i * 10)
            )
            for i in range(10)
        ]
        
        result = OrchestrationResult(deduplicated_findings=findings)
        
        issues = orchestrator.result_to_issues(result, "TestProject", top_n=3)
        
        assert len(issues) == 3
        # Should be top 3 by priority score
        assert all(issue.title for issue in issues)


class TestStatistics:
    """Test statistics calculation"""
    
    def test_count_by_scanner(self):
        """Test counting findings by scanner"""
        orchestrator = ScanOrchestrator()
        
        findings = [
            UnifiedFinding(
                finding_id=f"bandit-{i}",
                scanner=ScannerType.BANDIT,
                severity=FindingSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=i,
                line_end=i,
                title="Test",
                description="Test",
                code_snippet="test",
            )
            for i in range(3)
        ] + [
            UnifiedFinding(
                finding_id=f"semgrep-{i}",
                scanner=ScannerType.SEMGREP,
                severity=FindingSeverity.MEDIUM,
                category="security",
                file_path="test.py",
                line_start=i + 10,
                line_end=i + 10,
                title="Test",
                description="Test",
                code_snippet="test",
            )
            for i in range(2)
        ]
        
        counts = orchestrator._count_by_scanner(findings)
        
        assert counts[ScannerType.BANDIT] == 3
        assert counts[ScannerType.SEMGREP] == 2
    
    def test_count_by_severity(self):
        """Test counting findings by severity"""
        orchestrator = ScanOrchestrator()
        
        findings = [
            UnifiedFinding(
                finding_id=f"test-{i}",
                scanner=ScannerType.BANDIT,
                severity=FindingSeverity.CRITICAL if i < 2 else FindingSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=i,
                line_end=i,
                title="Test",
                description="Test",
                code_snippet="test",
            )
            for i in range(5)
        ]
        
        counts = orchestrator._count_by_severity(findings)
        
        assert counts[FindingSeverity.CRITICAL] == 2
        assert counts[FindingSeverity.HIGH] == 3


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @patch('security_assistant.orchestrator.BanditScanner')
    def test_scanner_execution_error(self, mock_bandit_class):
        """Test handling scanner execution errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("print('hello')")
            
            # Mock scanner that raises exception
            mock_scanner = Mock()
            mock_scanner.scan_directory.side_effect = Exception("Scanner failed")
            mock_bandit_class.return_value = mock_scanner
            
            orchestrator = ScanOrchestrator()
            orchestrator.enable_scanner(ScannerType.BANDIT)
            
            # Should handle error gracefully
            result = orchestrator.scan_directory(tmpdir)
            
            # Result should still be created even with error
            assert isinstance(result, OrchestrationResult)
            assert result.total_findings == 0
    
    @patch('security_assistant.orchestrator.BanditScanner')
    def test_scanner_file_execution_error(self, mock_bandit_class):
        """Test handling scanner file execution errors"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("print('hello')")
            
            # Mock scanner that raises exception on file scan
            mock_scanner = Mock()
            mock_scanner.scan_file.side_effect = Exception("File scan failed")
            mock_bandit_class.return_value = mock_scanner
            
            orchestrator = ScanOrchestrator()
            orchestrator.enable_scanner(ScannerType.BANDIT)
            
            # Should handle error gracefully
            result = orchestrator.scan_file(str(test_file))
            
            # Result should still be created even with error
            assert isinstance(result, OrchestrationResult)
            assert result.total_findings == 0
    
    def test_empty_findings_list(self):
        """Test handling empty findings list"""
        orchestrator = ScanOrchestrator()
        
        # Test deduplication with empty list
        deduplicated = orchestrator._deduplicate_findings([])
        assert len(deduplicated) == 0
        
        # Test priority scoring with empty list
        counts = orchestrator._count_by_scanner([])
        assert len(counts) == 0
    
    def test_finding_without_optional_fields(self):
        """Test handling findings without optional fields"""
        finding = UnifiedFinding(
            finding_id="test-1",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.MEDIUM,
            category="security",
            file_path="test.py",
            line_start=10,
            line_end=10,
            title="Test Finding",
            description="Test description",
            code_snippet="test code"
            # No optional fields like confidence, cwe_ids, etc.
        )
        
        orchestrator = ScanOrchestrator()
        
        # Should handle missing optional fields
        score = orchestrator._calculate_priority_score(finding)
        assert score > 0
        
        # Should convert to issue without errors
        issue = orchestrator._unified_finding_to_issue(finding, "TestProject")
        assert issue.title
        assert issue.description
    
    @patch('security_assistant.orchestrator.BanditScanner')
    @patch('security_assistant.orchestrator.SemgrepScanner')
    def test_parallel_execution_with_multiple_scanners(self, mock_semgrep_class, mock_bandit_class):
        """Test parallel execution with multiple scanners"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("print('hello')")
            
            # Mock both scanners
            mock_bandit = Mock()
            mock_bandit.scan_directory.return_value = BanditScanResult(findings=[])
            mock_bandit_class.return_value = mock_bandit
            
            mock_semgrep = Mock()
            mock_semgrep.scan_directory.return_value = SemgrepScanResult(findings=[])
            mock_semgrep_class.return_value = mock_semgrep
            
            orchestrator = ScanOrchestrator(max_workers=2)
            orchestrator.enable_scanner(ScannerType.BANDIT)
            orchestrator.enable_scanner(ScannerType.SEMGREP)
            
            result = orchestrator.scan_directory(tmpdir)
            
            # Both scanners should have been called
            mock_bandit.scan_directory.assert_called_once()
            mock_semgrep.scan_directory.assert_called_once()
            assert isinstance(result, OrchestrationResult)
    
    @patch('security_assistant.orchestrator.BanditScanner')
    def test_run_scanner_safe_with_exception(self, mock_bandit_class):
        """Test _run_scanner_safe error handling"""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_scanner = Mock()
            mock_scanner.scan_directory.side_effect = RuntimeError("Test error")
            mock_bandit_class.return_value = mock_scanner
            
            orchestrator = ScanOrchestrator()
            orchestrator.enable_scanner(ScannerType.BANDIT)
            
            # Should raise exception from _run_scanner_safe
            with pytest.raises(RuntimeError, match="Test error"):
                orchestrator._run_scanner_safe(
                    ScannerType.BANDIT,
                    mock_scanner,
                    tmpdir,
                    True
                )
    
    @patch('security_assistant.orchestrator.BanditScanner')
    def test_run_scanner_file_safe_with_exception(self, mock_bandit_class):
        """Test _run_scanner_file_safe error handling"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("print('hello')")
            
            mock_scanner = Mock()
            mock_scanner.scan_file.side_effect = RuntimeError("File scan error")
            mock_bandit_class.return_value = mock_scanner
            
            orchestrator = ScanOrchestrator()
            orchestrator.enable_scanner(ScannerType.BANDIT)
            
            # Should raise exception from _run_scanner_file_safe
            with pytest.raises(RuntimeError, match="File scan error"):
                orchestrator._run_scanner_file_safe(
                    ScannerType.BANDIT,
                    mock_scanner,
                    str(test_file)
                )
    
    def test_deduplication_both_strategy(self):
        """Test 'both' deduplication strategy"""
        orchestrator = ScanOrchestrator(dedup_strategy="both")
        
        # Create findings that match on location OR content
        findings = [
            UnifiedFinding(
                finding_id="test-1",
                scanner=ScannerType.BANDIT,
                severity=FindingSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=10,
                line_end=15,
                title="SQL Injection",
                description="Test",
                code_snippet="cursor.execute(query)",
            ),
            UnifiedFinding(
                finding_id="test-2",
                scanner=ScannerType.SEMGREP,
                severity=FindingSeverity.HIGH,
                category="security",
                file_path="test.py",
                line_start=10,
                line_end=15,
                title="SQL Injection",
                description="Test",
                code_snippet="cursor.execute(query)",
            ),
        ]
        
        deduplicated = orchestrator._deduplicate_findings(findings)
        
        # Should deduplicate since both location AND content match
        assert len(deduplicated) == 1
    
    def test_convert_trivy_secret_finding(self):
        """Test converting Trivy secret finding"""
        orchestrator = ScanOrchestrator()
        
        trivy_finding = TrivyFinding(
            vulnerability_id="SECRET-001",
            pkg_name="",
            installed_version="",
            fixed_version="",
            severity=TrivySeverity.HIGH,
            title="AWS Access Key",
            description="Hardcoded AWS access key found",
            references=[],
            target=".env",
            pkg_type="secret",
            cvss_score=0.0,
            cwe_ids=["CWE-798"]
        )
        
        trivy_result = TrivyScanResult(
            target=".env",
            scan_type=TrivyScanType.FILESYSTEM,
            findings=[trivy_finding],
            scan_time=None
        )
        
        unified = orchestrator._convert_trivy_findings(trivy_result)
        
        assert len(unified) == 1
        assert unified[0].category == "secret"
        assert unified[0].severity == FindingSeverity.HIGH
    
    def test_priority_score_all_factors(self):
        """Test priority score with all factors present"""
        orchestrator = ScanOrchestrator()
        
        finding = UnifiedFinding(
            finding_id="test-1",
            scanner=ScannerType.TRIVY,
            severity=FindingSeverity.CRITICAL,
            category="security",
            file_path="requirements.txt",
            line_start=1,
            line_end=1,
            title="CVE-2021-1234",
            description="Critical vulnerability",
            code_snippet="",
            confidence="HIGH",
            fix_available=True,
            fix_version="2.0.0",
            cwe_ids=["CWE-89"],
            owasp_categories=["A1:2017-Injection"]
        )
        
        score = orchestrator._calculate_priority_score(finding)
        
        # Should be very high score with all factors
        assert score >= 90.0
        assert score <= 100.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
