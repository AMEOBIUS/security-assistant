"""
Unit tests for Semgrep scanner.
Tests all core functionality with mocked Semgrep calls.
"""

import json
from unittest.mock import Mock, patch

import pytest

from security_assistant.scanners.semgrep_scanner import (
    SemgrepFinding,
    SemgrepNotInstalledError,
    SemgrepScanner,
    SemgrepScannerError,
    SemgrepScanResult,
)

# Sample Semgrep JSON output
SAMPLE_SEMGREP_OUTPUT = {
    "results": [
        {
            "check_id": "python.lang.security.audit.dangerous-system-call",
            "path": "app.py",
            "start": {"line": 10, "col": 5},
            "end": {"line": 10, "col": 25},
            "extra": {
                "message": "Detected use of os.system(). This is dangerous if user input is passed.",
                "severity": "ERROR",
                "lines": "os.system(user_input)",
                "metadata": {
                    "category": "security",
                    "cwe": ["CWE-78"],
                    "owasp": ["A03:2021 - Injection"],
                    "references": [
                        "https://owasp.org/www-community/attacks/Command_Injection"
                    ]
                }
            }
        },
        {
            "check_id": "javascript.express.security.audit.express-cookie-session-no-secret",
            "path": "server.js",
            "start": {"line": 15, "col": 1},
            "end": {"line": 17, "col": 3},
            "extra": {
                "message": "Cookie session without secret detected.",
                "severity": "WARNING",
                "lines": "app.use(cookieSession({\n  name: 'session'\n}))",
                "metadata": {
                    "category": "security",
                    "cwe": ["CWE-614"],
                    "owasp": ["A02:2021 - Cryptographic Failures"]
                }
            }
        },
        {
            "check_id": "python.lang.best-practice.open-never-closed",
            "path": "utils.py",
            "start": {"line": 5, "col": 5},
            "end": {"line": 5, "col": 20},
            "extra": {
                "message": "File opened but never closed.",
                "severity": "INFO",
                "lines": "f = open('file.txt')",
                "metadata": {
                    "category": "best-practice"
                }
            }
        }
    ],
    "errors": [],
    "paths": {
        "scanned": ["app.py", "server.js", "utils.py"]
    }
}


class TestSemgrepFinding:
    """Test SemgrepFinding data model."""
    
    def test_finding_creation(self):
        """Test creating a finding."""
        finding = SemgrepFinding(
            check_id="python.lang.security.audit.dangerous-system-call",
            message="Dangerous system call",
            severity="ERROR",
            path="app.py",
            start_line=10,
            end_line=10,
            start_col=5,
            end_col=25,
            code="os.system(user_input)",
            metadata={"category": "security", "cwe": ["CWE-78"]}
        )
        
        assert finding.check_id == "python.lang.security.audit.dangerous-system-call"
        assert finding.severity == "ERROR"
        assert finding.path == "app.py"
        assert finding.start_line == 10
    
    def test_severity_emoji(self):
        """Test severity emoji property."""
        finding_error = SemgrepFinding(
            check_id="test", message="test", severity="ERROR",
            path="test.py", start_line=1, end_line=1,
            start_col=1, end_col=1, code="test"
        )
        finding_warning = SemgrepFinding(
            check_id="test", message="test", severity="WARNING",
            path="test.py", start_line=1, end_line=1,
            start_col=1, end_col=1, code="test"
        )
        finding_info = SemgrepFinding(
            check_id="test", message="test", severity="INFO",
            path="test.py", start_line=1, end_line=1,
            start_col=1, end_col=1, code="test"
        )
        
        assert finding_error.severity_emoji == "🔴"
        assert finding_warning.severity_emoji == "🟡"
        assert finding_info.severity_emoji == "🟢"
    
    def test_language_extraction(self):
        """Test language extraction from check_id."""
        finding_python = SemgrepFinding(
            check_id="python.lang.security.audit.test",
            message="test", severity="ERROR",
            path="test.py", start_line=1, end_line=1,
            start_col=1, end_col=1, code="test"
        )
        finding_js = SemgrepFinding(
            check_id="javascript.express.security.test",
            message="test", severity="ERROR",
            path="test.js", start_line=1, end_line=1,
            start_col=1, end_col=1, code="test"
        )
        
        assert finding_python.language == "python"
        assert finding_js.language == "javascript"
    
    def test_category_extraction(self):
        """Test category extraction."""
        # From metadata
        finding1 = SemgrepFinding(
            check_id="python.lang.security.audit.test",
            message="test", severity="ERROR",
            path="test.py", start_line=1, end_line=1,
            start_col=1, end_col=1, code="test",
            metadata={"category": "security"}
        )
        
        # From check_id
        finding2 = SemgrepFinding(
            check_id="python.lang.security.audit.test",
            message="test", severity="ERROR",
            path="test.py", start_line=1, end_line=1,
            start_col=1, end_col=1, code="test"
        )
        
        assert finding1.category == "security"
        assert finding2.category == "security"
    
    def test_cwe_extraction(self):
        """Test CWE extraction from metadata."""
        finding = SemgrepFinding(
            check_id="test", message="test", severity="ERROR",
            path="test.py", start_line=1, end_line=1,
            start_col=1, end_col=1, code="test",
            metadata={"cwe": ["CWE-78", "CWE-79"]}
        )
        
        assert finding.cwe_ids == ["CWE-78", "CWE-79"]
    
    def test_owasp_extraction(self):
        """Test OWASP extraction from metadata."""
        finding = SemgrepFinding(
            check_id="test", message="test", severity="ERROR",
            path="test.py", start_line=1, end_line=1,
            start_col=1, end_col=1, code="test",
            metadata={"owasp": ["A03:2021 - Injection"]}
        )
        
        assert finding.owasp_categories == ["A03:2021 - Injection"]


class TestSemgrepScanResult:
    """Test SemgrepScanResult data model."""
    
    def test_scan_result_creation(self):
        """Test creating a scan result."""
        result = SemgrepScanResult()
        
        assert result.findings == []
        assert result.files_scanned == 0
        assert result.errors == []
    
    def test_severity_counts(self):
        """Test severity counting properties."""
        result = SemgrepScanResult()
        
        result.findings = [
            SemgrepFinding(
                check_id="test1", message="test", severity="ERROR",
                path="test.py", start_line=1, end_line=1,
                start_col=1, end_col=1, code="test"
            ),
            SemgrepFinding(
                check_id="test2", message="test", severity="ERROR",
                path="test.py", start_line=2, end_line=2,
                start_col=1, end_col=1, code="test"
            ),
            SemgrepFinding(
                check_id="test3", message="test", severity="WARNING",
                path="test.py", start_line=3, end_line=3,
                start_col=1, end_col=1, code="test"
            ),
            SemgrepFinding(
                check_id="test4", message="test", severity="INFO",
                path="test.py", start_line=4, end_line=4,
                start_col=1, end_col=1, code="test"
            )
        ]
        
        assert result.error_count == 2
        assert result.warning_count == 1
        assert result.info_count == 1
        assert result.has_findings is True
    
    def test_languages_property(self):
        """Test languages extraction."""
        result = SemgrepScanResult()
        
        result.findings = [
            SemgrepFinding(
                check_id="python.lang.test", message="test", severity="ERROR",
                path="test.py", start_line=1, end_line=1,
                start_col=1, end_col=1, code="test"
            ),
            SemgrepFinding(
                check_id="javascript.lang.test", message="test", severity="ERROR",
                path="test.js", start_line=1, end_line=1,
                start_col=1, end_col=1, code="test"
            ),
            SemgrepFinding(
                check_id="python.lang.test2", message="test", severity="ERROR",
                path="test2.py", start_line=1, end_line=1,
                start_col=1, end_col=1, code="test"
            )
        ]
        
        assert result.languages == {"python", "javascript"}


class TestSemgrepScanner:
    """Test SemgrepScanner class."""
    
    @patch('security_assistant.scanners.base_scanner.shutil.which')
    def test_scanner_initialization(self, mock_which):
        """Test scanner initialization."""
        # Mock Semgrep installation check
        mock_which.return_value = "/usr/bin/semgrep"
        
        scanner = SemgrepScanner(min_severity="WARNING", config="p/security-audit")
        
        assert scanner.config.min_severity == "WARNING"
        assert scanner.semgrep_config == "p/security-audit"
        assert "venv" in scanner.config.exclude_dirs
    
    @patch('security_assistant.scanners.base_scanner.shutil.which')
    def test_semgrep_not_installed(self, mock_which):
        """Test error when Semgrep not installed."""
        mock_which.return_value = None
        
        with pytest.raises(SemgrepNotInstalledError):
            SemgrepScanner()
    
    @patch('security_assistant.scanners.base_scanner.shutil.which')
    def test_scan_file_not_found(self, mock_which):
        """Test scanning non-existent file."""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()
        
        with pytest.raises(FileNotFoundError):
            scanner.scan_file("nonexistent.py")
    
    @patch('security_assistant.scanners.base_scanner.subprocess.run')
    @patch('security_assistant.scanners.base_scanner.shutil.which')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.exists')
    def test_scan_file_success(self, mock_exists, mock_is_file, mock_which, mock_run):
        """Test successful file scan."""
        # Mock installation and file checks
        mock_which.return_value = "/usr/bin/semgrep"
        mock_exists.return_value = True
        mock_is_file.return_value = True
        
        # Mock Semgrep scan
        mock_run.return_value = Mock(
            returncode=1,  # Exit code 1 means findings found
            stdout=json.dumps(SAMPLE_SEMGREP_OUTPUT),
            stderr=""
        )
        
        scanner = SemgrepScanner()
        result = scanner.scan_file("app.py")
        
        assert result.has_findings
        assert len(result.findings) == 3
        assert result.files_scanned == 3
    
    @patch('security_assistant.scanners.base_scanner.subprocess.run')
    @patch('security_assistant.scanners.base_scanner.shutil.which')
    @patch('pathlib.Path.is_dir')
    @patch('pathlib.Path.exists')
    def test_scan_directory_success(self, mock_exists, mock_is_dir, mock_which, mock_run):
        """Test successful directory scan."""
        # Mock installation and directory checks
        mock_which.return_value = "/usr/bin/semgrep"
        mock_exists.return_value = True
        mock_is_dir.return_value = True
        
        # Mock Semgrep scan
        mock_run.return_value = Mock(
            returncode=1,
            stdout=json.dumps(SAMPLE_SEMGREP_OUTPUT),
            stderr=""
        )
        
        scanner = SemgrepScanner()
        result = scanner.scan_directory("src/")
        
        assert result.has_findings
        assert len(result.findings) == 3
    
    @patch('security_assistant.scanners.base_scanner.shutil.which')
    def test_parse_semgrep_output(self, mock_which):
        """Test parsing Semgrep JSON output."""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()
        
        result = scanner._parse_semgrep_output(json.dumps(SAMPLE_SEMGREP_OUTPUT))
        
        assert len(result.findings) == 3
        assert result.files_scanned == 3
        
        # Check first finding
        finding = result.findings[0]
        assert finding.check_id == "python.lang.security.audit.dangerous-system-call"
        assert finding.severity == "ERROR"
        assert finding.path == "app.py"
        assert finding.start_line == 10
        assert "CWE-78" in finding.cwe_ids
    
    @patch('security_assistant.scanners.base_scanner.shutil.which')
    def test_severity_filtering(self, mock_which):
        """Test filtering by severity."""
        mock_which.return_value = "/usr/bin/semgrep"
        
        # Only ERROR severity
        scanner = SemgrepScanner(min_severity="ERROR")
        result = scanner._parse_semgrep_output(json.dumps(SAMPLE_SEMGREP_OUTPUT))
        
        assert len(result.findings) == 1
        assert all(f.severity == "ERROR" for f in result.findings)
        
        # WARNING and above
        scanner = SemgrepScanner(min_severity="WARNING")
        result = scanner._parse_semgrep_output(json.dumps(SAMPLE_SEMGREP_OUTPUT))
        
        assert len(result.findings) == 2
        assert all(f.severity in ["ERROR", "WARNING"] for f in result.findings)
    
    @patch('security_assistant.scanners.base_scanner.shutil.which')
    def test_finding_to_issue(self, mock_which):
        """Test converting finding to GitLab issue."""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()
        
        finding = SemgrepFinding(
            check_id="python.lang.security.audit.dangerous-system-call",
            message="Dangerous system call",
            severity="ERROR",
            path="app.py",
            start_line=10,
            end_line=10,
            start_col=5,
            end_col=25,
            code="os.system(user_input)",
            metadata={
                "category": "security",
                "cwe": ["CWE-78"],
                "owasp": ["A03:2021 - Injection"]
            }
        )
        
        issue = scanner.finding_to_issue(finding, "TestProject")
        
        assert "dangerous-system-call" in issue.title
        assert "app.py" in issue.title
        assert "ERROR" in issue.description or "HIGH" in issue.description
        assert "CWE-78" in issue.description
        assert "A03:2021 - Injection" in issue.description
        assert "security" in issue.labels
        assert "semgrep" in issue.labels
        assert "python" in issue.labels
        assert issue.confidential is True
    
    @patch('security_assistant.scanners.base_scanner.shutil.which')
    def test_scan_result_to_individual_issues(self, mock_which):
        """Test converting scan result to individual issues."""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()
        
        result = scanner._parse_semgrep_output(json.dumps(SAMPLE_SEMGREP_OUTPUT))
        issues = scanner.scan_result_to_issues(result, "TestProject", group_by_file=False)
        
        assert len(issues) == 3
        assert all(isinstance(issue.title, str) for issue in issues)
        assert all(issue.confidential for issue in issues)
    
    @patch('security_assistant.scanners.base_scanner.shutil.which')
    def test_scan_result_to_grouped_issues(self, mock_which):
        """Test converting scan result to grouped issues."""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()
        
        result = scanner._parse_semgrep_output(json.dumps(SAMPLE_SEMGREP_OUTPUT))
        issues = scanner.scan_result_to_issues(result, "TestProject", group_by_file=True)
        
        # 3 findings in 3 different files = 3 issues
        assert len(issues) == 3
        assert all("Security:" in issue.title for issue in issues)
    
    @patch('security_assistant.scanners.base_scanner.subprocess.run')
    @patch('security_assistant.scanners.base_scanner.shutil.which')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.exists')
    def test_timeout_handling(self, mock_exists, mock_is_file, mock_which, mock_run):
        """Test timeout handling."""
        from security_assistant.scanners.base_scanner import ScannerError
        mock_which.return_value = "/usr/bin/semgrep"
        mock_exists.return_value = True
        mock_is_file.return_value = True
        
        scanner = SemgrepScanner()
        
        # Mock timeout
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("semgrep", 600)
        
        with pytest.raises(ScannerError, match="timed out"):
            scanner.scan_file("app.py")
    
    @patch('security_assistant.scanners.base_scanner.shutil.which')
    def test_invalid_json_handling(self, mock_which):
        """Test handling of invalid JSON output."""
        mock_which.return_value = "/usr/bin/semgrep"
        scanner = SemgrepScanner()
        
        with pytest.raises(SemgrepScannerError, match="Failed to parse"):
            scanner._parse_semgrep_output("invalid json {")
    
    @patch('security_assistant.scanners.base_scanner.subprocess.run')
    @patch('security_assistant.scanners.base_scanner.shutil.which')
    @patch('pathlib.Path.is_file')
    @patch('pathlib.Path.exists')
    def test_custom_rules(self, mock_exists, mock_is_file, mock_which, mock_run):
        """Test using custom rules."""
        mock_which.return_value = "/usr/bin/semgrep"
        mock_exists.return_value = True
        mock_is_file.return_value = True
        
        # Mock scan
        mock_run.return_value = Mock(
            returncode=0,
            stdout=json.dumps({"results": [], "errors": [], "paths": {"scanned": []}}),
            stderr=""
        )
        
        scanner = SemgrepScanner(custom_rules=["custom_rules.yaml", "p/custom"])
        scanner.scan_file("app.py")
        
        # Verify custom rules were added to command
        call_args = mock_run.call_args[0][0]
        assert "--config" in call_args
        assert "custom_rules.yaml" in call_args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
