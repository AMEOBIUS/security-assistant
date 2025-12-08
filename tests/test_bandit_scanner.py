"""
Unit tests for Bandit scanner integration.
Tests scanner functionality with mocked Bandit output.
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from security_assistant.scanners.bandit_scanner import (
    BanditScanner,
    BanditFinding,
    ScanResult,
    BanditScannerError,
    BanditNotInstalledError
)
from security_assistant.gitlab_api import IssueData


# Sample Bandit JSON output for testing
SAMPLE_BANDIT_OUTPUT = {
    "errors": [],
    "generated_at": "2025-11-27T10:00:00Z",
    "metrics": {
        "_totals": {
            "loc": 150,
            "nosec": 0
        }
    },
    "results": [
        {
            "code": "password = 'hardcoded_password'",
            "filename": "test_file.py",
            "issue_confidence": "HIGH",
            "issue_severity": "HIGH",
            "issue_text": "Possible hardcoded password: 'hardcoded_password'",
            "line_number": 42,
            "line_range": [42],
            "more_info": "https://bandit.readthedocs.io/en/latest/plugins/b105_hardcoded_password_string.html",
            "test_id": "B105",
            "test_name": "hardcoded_password_string",
            "issue_cwe": {
                "id": 259,
                "link": "https://cwe.mitre.org/data/definitions/259.html"
            }
        },
        {
            "code": "eval(user_input)",
            "filename": "test_file.py",
            "issue_confidence": "HIGH",
            "issue_severity": "MEDIUM",
            "issue_text": "Use of possibly insecure function - consider using safer ast.literal_eval.",
            "line_number": 55,
            "line_range": [55],
            "more_info": "https://bandit.readthedocs.io/en/latest/plugins/b307_eval.html",
            "test_id": "B307",
            "test_name": "eval"
        },
        {
            "code": "# Low severity finding",
            "filename": "test_file.py",
            "issue_confidence": "LOW",
            "issue_severity": "LOW",
            "issue_text": "Consider possible security implications",
            "line_number": 100,
            "line_range": [100],
            "more_info": "https://bandit.readthedocs.io/",
            "test_id": "B999",
            "test_name": "low_severity_test"
        }
    ]
}


class TestBanditFinding:
    """Test BanditFinding dataclass."""
    
    def test_finding_creation(self):
        """Test creating a BanditFinding."""
        finding = BanditFinding(
            test_id="B105",
            test_name="hardcoded_password",
            severity="HIGH",
            confidence="HIGH",
            issue_text="Hardcoded password found",
            filename="app.py",
            line_number=42,
            code="password = 'secret'",
            cwe_id="259"
        )
        
        assert finding.test_id == "B105"
        assert finding.severity == "HIGH"
        assert finding.line_number == 42
    
    def test_severity_emoji(self):
        """Test severity emoji property."""
        high_finding = BanditFinding(
            test_id="B105", test_name="test", severity="HIGH",
            confidence="HIGH", issue_text="test", filename="test.py",
            line_number=1, code="test"
        )
        assert high_finding.severity_emoji == "🔴"
        
        medium_finding = BanditFinding(
            test_id="B105", test_name="test", severity="MEDIUM",
            confidence="HIGH", issue_text="test", filename="test.py",
            line_number=1, code="test"
        )
        assert medium_finding.severity_emoji == "🟡"
        
        low_finding = BanditFinding(
            test_id="B105", test_name="test", severity="LOW",
            confidence="HIGH", issue_text="test", filename="test.py",
            line_number=1, code="test"
        )
        assert low_finding.severity_emoji == "🟢"
    
    def test_confidence_emoji(self):
        """Test confidence emoji property."""
        high_conf = BanditFinding(
            test_id="B105", test_name="test", severity="HIGH",
            confidence="HIGH", issue_text="test", filename="test.py",
            line_number=1, code="test"
        )
        assert high_conf.confidence_emoji == "✅"


class TestScanResult:
    """Test ScanResult dataclass."""
    
    def test_empty_scan_result(self):
        """Test empty scan result."""
        result = ScanResult()
        assert len(result.findings) == 0
        assert result.high_severity_count == 0
        assert result.has_findings is False
    
    def test_scan_result_with_findings(self):
        """Test scan result with findings."""
        findings = [
            BanditFinding(
                test_id="B105", test_name="test", severity="HIGH",
                confidence="HIGH", issue_text="test", filename="test.py",
                line_number=1, code="test"
            ),
            BanditFinding(
                test_id="B307", test_name="test", severity="MEDIUM",
                confidence="HIGH", issue_text="test", filename="test.py",
                line_number=2, code="test"
            ),
            BanditFinding(
                test_id="B999", test_name="test", severity="LOW",
                confidence="LOW", issue_text="test", filename="test.py",
                line_number=3, code="test"
            )
        ]
        
        result = ScanResult(findings=findings)
        assert len(result.findings) == 3
        assert result.high_severity_count == 1
        assert result.medium_severity_count == 1
        assert result.low_severity_count == 1
        assert result.has_findings is True


class TestBanditScanner:
    """Test BanditScanner class."""
    
    @patch('security_assistant.scanners.bandit_scanner.subprocess.run')
    def test_scanner_initialization(self, mock_run):
        """Test scanner initialization."""
        # Mock Bandit version check
        mock_run.return_value = Mock(returncode=0, stdout="bandit 1.7.5")
        
        scanner = BanditScanner(min_severity="MEDIUM", min_confidence="HIGH")
        assert scanner.min_severity == "MEDIUM"
        assert scanner.min_confidence == "HIGH"
        assert "venv" in scanner.exclude_dirs
    
    @patch('security_assistant.scanners.bandit_scanner.subprocess.run')
    def test_bandit_not_installed(self, mock_run):
        """Test error when Bandit not installed."""
        mock_run.side_effect = FileNotFoundError()
        
        with pytest.raises(BanditNotInstalledError):
            BanditScanner()
    
    @patch('security_assistant.scanners.bandit_scanner.subprocess.run')
    @patch('os.path.exists')
    def test_scan_file_not_found(self, mock_exists, mock_run):
        """Test scanning non-existent file."""
        mock_run.return_value = Mock(returncode=0)
        mock_exists.return_value = False
        
        scanner = BanditScanner()
        
        with pytest.raises(BanditScannerError, match="File not found"):
            scanner.scan_file("nonexistent.py")
    
    @patch('security_assistant.scanners.bandit_scanner.subprocess.run')
    @patch('os.path.exists')
    def test_scan_non_python_file(self, mock_exists, mock_run):
        """Test scanning non-Python file."""
        mock_run.return_value = Mock(returncode=0)
        mock_exists.return_value = True
        
        scanner = BanditScanner()
        
        with pytest.raises(BanditScannerError, match="Not a Python file"):
            scanner.scan_file("test.txt")
    
    @patch('os.path.exists')
    @patch('security_assistant.scanners.bandit_scanner.subprocess.run')
    def test_scan_file_success(self, mock_run, mock_exists):
        """Test successful file scan."""
        # Mock Bandit version check first
        mock_run.return_value = Mock(returncode=0, stdout="bandit 1.7.5")
        
        # Mock file exists
        mock_exists.return_value = True
        
        scanner = BanditScanner()
        
        # Now mock Bandit execution
        mock_run.return_value = Mock(
            returncode=1,  # Bandit returns 1 when issues found
            stdout=json.dumps(SAMPLE_BANDIT_OUTPUT),
            stderr=""
        )
        
        result = scanner.scan_file("test_file.py")
        
        assert isinstance(result, ScanResult)
        assert len(result.findings) == 3
        assert result.high_severity_count == 1
        assert result.medium_severity_count == 1
    
    @patch('security_assistant.scanners.bandit_scanner.subprocess.run')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_scan_directory_success(self, mock_isdir, mock_exists, mock_run):
        """Test successful directory scan."""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps(SAMPLE_BANDIT_OUTPUT),
            stderr=""
        )
        
        scanner = BanditScanner()
        result = scanner.scan_directory("src/", recursive=True)
        
        assert isinstance(result, ScanResult)
        assert len(result.findings) == 3
    
    @patch('security_assistant.scanners.bandit_scanner.subprocess.run')
    def test_parse_bandit_output(self, mock_run):
        """Test parsing Bandit JSON output."""
        mock_run.return_value = Mock(returncode=0)
        
        scanner = BanditScanner()
        result = scanner._parse_bandit_output(json.dumps(SAMPLE_BANDIT_OUTPUT))
        
        assert len(result.findings) == 3
        
        # Check first finding
        finding = result.findings[0]
        assert finding.test_id == "B105"
        assert finding.severity == "HIGH"
        assert finding.confidence == "HIGH"
        assert finding.line_number == 42
        assert finding.cwe_id == 259
    
    @patch('security_assistant.scanners.bandit_scanner.subprocess.run')
    def test_severity_filtering(self, mock_run):
        """Test filtering by severity."""
        mock_run.return_value = Mock(returncode=0)
        
        # Only HIGH severity
        scanner = BanditScanner(min_severity="HIGH")
        result = scanner._parse_bandit_output(json.dumps(SAMPLE_BANDIT_OUTPUT))
        
        assert len(result.findings) == 1
        assert result.findings[0].severity == "HIGH"
    
    @patch('security_assistant.scanners.bandit_scanner.subprocess.run')
    def test_confidence_filtering(self, mock_run):
        """Test filtering by confidence."""
        mock_run.return_value = Mock(returncode=0)
        
        # Only HIGH confidence
        scanner = BanditScanner(min_confidence="HIGH")
        result = scanner._parse_bandit_output(json.dumps(SAMPLE_BANDIT_OUTPUT))
        
        # Should exclude the LOW confidence finding
        assert len(result.findings) == 2
        assert all(f.confidence == "HIGH" for f in result.findings)
    
    @patch('security_assistant.scanners.bandit_scanner.subprocess.run')
    def test_finding_to_issue(self, mock_run):
        """Test converting finding to GitLab issue."""
        mock_run.return_value = Mock(returncode=0)
        
        scanner = BanditScanner()
        
        finding = BanditFinding(
            test_id="B105",
            test_name="hardcoded_password",
            severity="HIGH",
            confidence="HIGH",
            issue_text="Hardcoded password found",
            filename="app.py",
            line_number=42,
            code="password = 'secret'",
            cwe_id="259",
            more_info="https://example.com"
        )
        
        issue = scanner.finding_to_issue(finding, "TestProject")
        
        assert isinstance(issue, IssueData)
        assert "hardcoded_password" in issue.title
        assert "app.py" in issue.title
        assert "HIGH" in issue.description
        assert "security" in issue.labels
        assert "bandit" in issue.labels
        assert "critical" in issue.labels
        assert issue.confidential is True
    
    @patch('security_assistant.scanners.bandit_scanner.subprocess.run')
    def test_scan_result_to_issues_individual(self, mock_run):
        """Test converting scan result to individual issues."""
        mock_run.return_value = Mock(returncode=0)
        
        scanner = BanditScanner()
        result = scanner._parse_bandit_output(json.dumps(SAMPLE_BANDIT_OUTPUT))
        
        issues = scanner.scan_result_to_issues(result, "TestProject", group_by_file=False)
        
        assert len(issues) == 3
        assert all(isinstance(issue, IssueData) for issue in issues)
        assert all(issue.confidential for issue in issues)
    
    @patch('security_assistant.scanners.bandit_scanner.subprocess.run')
    def test_scan_result_to_issues_grouped(self, mock_run):
        """Test converting scan result to grouped issues."""
        mock_run.return_value = Mock(returncode=0)
        
        scanner = BanditScanner()
        result = scanner._parse_bandit_output(json.dumps(SAMPLE_BANDIT_OUTPUT))
        
        issues = scanner.scan_result_to_issues(result, "TestProject", group_by_file=True)
        
        # All findings are in same file, so should be 1 grouped issue
        assert len(issues) == 1
        assert "3 issues" in issues[0].title
        assert "multiple-issues" in issues[0].labels
    
    @patch('security_assistant.scanners.bandit_scanner.subprocess.run')
    def test_bandit_timeout(self, mock_run):
        """Test Bandit timeout handling."""
        # Mock version check first
        mock_run.return_value = Mock(returncode=0, stdout="bandit 1.7.5")
        
        scanner = BanditScanner()
        
        # Now mock timeout
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("bandit", 300)
        
        with pytest.raises(BanditScannerError, match="timeout"):
            scanner._run_bandit(["test.py"])
    
    @patch('security_assistant.scanners.bandit_scanner.subprocess.run')
    def test_invalid_json_output(self, mock_run):
        """Test handling invalid JSON output."""
        mock_run.return_value = Mock(returncode=0)
        
        scanner = BanditScanner()
        
        with pytest.raises(BanditScannerError, match="Failed to parse"):
            scanner._parse_bandit_output("invalid json")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
