"""
Unit tests for Trivy Scanner

Tests cover:
- TrivyFinding creation and properties
- TrivyScanResult metrics and counters
- TrivyScanner initialization
- Scan operations (image, filesystem, repository)
- JSON parsing
- Severity filtering
- Finding to issue conversion
- SBOM generation
- Error handling
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from security_assistant.gitlab_api import IssueData
from security_assistant.scanners.trivy_scanner import (
    TrivyFinding,
    TrivyNotInstalledError,
    TrivyScanner,
    TrivyScannerError,
    TrivyScanResult,
    TrivyScanType,
    TrivySeverity,
)


class TestTrivyFinding:
    """Test TrivyFinding data class"""
    
    def test_finding_creation(self):
        """Test creating a TrivyFinding"""
        finding = TrivyFinding(
            vulnerability_id="CVE-2021-12345",
            pkg_name="openssl",
            installed_version="1.1.1k",
            fixed_version="1.1.1l",
            severity=TrivySeverity.HIGH,
            title="OpenSSL vulnerability",
            description="Buffer overflow in OpenSSL",
            references=["https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-12345"],
            target="alpine:3.15",
            pkg_type="apk",
            cvss_score=7.5,
            cwe_ids=["CWE-119"],
        )
        
        assert finding.vulnerability_id == "CVE-2021-12345"
        assert finding.pkg_name == "openssl"
        assert finding.severity == TrivySeverity.HIGH
        assert finding.cvss_score == 7.5
        assert "CWE-119" in finding.cwe_ids
    
    def test_severity_emoji(self):
        """Test severity emoji property"""
        finding = TrivyFinding(
            vulnerability_id="CVE-2021-12345",
            pkg_name="test",
            installed_version="1.0",
            fixed_version="2.0",
            severity=TrivySeverity.CRITICAL,
            title="Test",
            description="Test",
            references=[],
            target="test",
            pkg_type="test",
        )
        
        assert finding.severity_emoji == "🔴"
    
    def test_is_fixable(self):
        """Test is_fixable property"""
        fixable = TrivyFinding(
            vulnerability_id="CVE-2021-12345",
            pkg_name="test",
            installed_version="1.0",
            fixed_version="2.0",
            severity=TrivySeverity.HIGH,
            title="Test",
            description="Test",
            references=[],
            target="test",
            pkg_type="test",
        )
        
        not_fixable = TrivyFinding(
            vulnerability_id="CVE-2021-12346",
            pkg_name="test",
            installed_version="1.0",
            fixed_version="",
            severity=TrivySeverity.HIGH,
            title="Test",
            description="Test",
            references=[],
            target="test",
            pkg_type="test",
        )
        
        assert fixable.is_fixable is True
        assert not_fixable.is_fixable is False
    
    def test_is_critical_or_high(self):
        """Test is_critical_or_high property"""
        critical = TrivyFinding(
            vulnerability_id="CVE-2021-12345",
            pkg_name="test",
            installed_version="1.0",
            fixed_version="2.0",
            severity=TrivySeverity.CRITICAL,
            title="Test",
            description="Test",
            references=[],
            target="test",
            pkg_type="test",
        )
        
        high = TrivyFinding(
            vulnerability_id="CVE-2021-12346",
            pkg_name="test",
            installed_version="1.0",
            fixed_version="2.0",
            severity=TrivySeverity.HIGH,
            title="Test",
            description="Test",
            references=[],
            target="test",
            pkg_type="test",
        )
        
        medium = TrivyFinding(
            vulnerability_id="CVE-2021-12347",
            pkg_name="test",
            installed_version="1.0",
            fixed_version="2.0",
            severity=TrivySeverity.MEDIUM,
            title="Test",
            description="Test",
            references=[],
            target="test",
            pkg_type="test",
        )
        
        assert critical.is_critical_or_high is True
        assert high.is_critical_or_high is True
        assert medium.is_critical_or_high is False


class TestTrivyScanResult:
    """Test TrivyScanResult data class"""
    
    def test_scan_result_creation(self):
        """Test creating a TrivyScanResult"""
        findings = [
            TrivyFinding(
                vulnerability_id="CVE-2021-12345",
                pkg_name="openssl",
                installed_version="1.1.1k",
                fixed_version="1.1.1l",
                severity=TrivySeverity.HIGH,
                title="Test",
                description="Test",
                references=[],
                target="alpine:3.15",
                pkg_type="apk",
            ),
        ]
        
        result = TrivyScanResult(
            target="alpine:3.15",
            scan_type=TrivyScanType.IMAGE,
            findings=findings,
            scan_time=datetime.now(),
        )
        
        assert result.target == "alpine:3.15"
        assert result.scan_type == TrivyScanType.IMAGE
        assert len(result.findings) == 1
    
    def test_vulnerability_count(self):
        """Test vulnerability_count property"""
        findings = [
            TrivyFinding(
                vulnerability_id="CVE-2021-12345",
                pkg_name="openssl",
                installed_version="1.1.1k",
                fixed_version="1.1.1l",
                severity=TrivySeverity.HIGH,
                title="Test",
                description="Test",
                references=[],
                target="alpine:3.15",
                pkg_type="apk",
            ),
            TrivyFinding(
                vulnerability_id="SECRET-001",
                pkg_name="Secret",
                installed_version="",
                fixed_version="",
                severity=TrivySeverity.HIGH,
                title="AWS Key",
                description="AWS key found",
                references=[],
                target="app.py",
                pkg_type="secret",
            ),
        ]
        
        result = TrivyScanResult(
            target="alpine:3.15",
            scan_type=TrivyScanType.IMAGE,
            findings=findings,
            scan_time=datetime.now(),
        )
        
        assert result.vulnerability_count == 1
        assert result.secret_count == 1
    
    def test_severity_counts(self):
        """Test severity count properties"""
        findings = [
            TrivyFinding(
                vulnerability_id="CVE-2021-12345",
                pkg_name="test1",
                installed_version="1.0",
                fixed_version="2.0",
                severity=TrivySeverity.CRITICAL,
                title="Test",
                description="Test",
                references=[],
                target="test",
                pkg_type="apk",
            ),
            TrivyFinding(
                vulnerability_id="CVE-2021-12346",
                pkg_name="test2",
                installed_version="1.0",
                fixed_version="2.0",
                severity=TrivySeverity.HIGH,
                title="Test",
                description="Test",
                references=[],
                target="test",
                pkg_type="apk",
            ),
            TrivyFinding(
                vulnerability_id="CVE-2021-12347",
                pkg_name="test3",
                installed_version="1.0",
                fixed_version="2.0",
                severity=TrivySeverity.MEDIUM,
                title="Test",
                description="Test",
                references=[],
                target="test",
                pkg_type="apk",
            ),
        ]
        
        result = TrivyScanResult(
            target="test",
            scan_type=TrivyScanType.IMAGE,
            findings=findings,
            scan_time=datetime.now(),
        )
        
        assert result.critical_count == 1
        assert result.high_count == 1
        assert result.medium_count == 1
        assert result.low_count == 0
    
    def test_fixable_count(self):
        """Test fixable_count property"""
        findings = [
            TrivyFinding(
                vulnerability_id="CVE-2021-12345",
                pkg_name="test1",
                installed_version="1.0",
                fixed_version="2.0",
                severity=TrivySeverity.HIGH,
                title="Test",
                description="Test",
                references=[],
                target="test",
                pkg_type="apk",
            ),
            TrivyFinding(
                vulnerability_id="CVE-2021-12346",
                pkg_name="test2",
                installed_version="1.0",
                fixed_version="",
                severity=TrivySeverity.HIGH,
                title="Test",
                description="Test",
                references=[],
                target="test",
                pkg_type="apk",
            ),
        ]
        
        result = TrivyScanResult(
            target="test",
            scan_type=TrivyScanType.IMAGE,
            findings=findings,
            scan_time=datetime.now(),
        )
        
        assert result.fixable_count == 1
    
    def test_packages_property(self):
        """Test packages property"""
        findings = [
            TrivyFinding(
                vulnerability_id="CVE-2021-12345",
                pkg_name="openssl",
                installed_version="1.0",
                fixed_version="2.0",
                severity=TrivySeverity.HIGH,
                title="Test",
                description="Test",
                references=[],
                target="test",
                pkg_type="apk",
            ),
            TrivyFinding(
                vulnerability_id="CVE-2021-12346",
                pkg_name="openssl",
                installed_version="1.0",
                fixed_version="2.0",
                severity=TrivySeverity.MEDIUM,
                title="Test",
                description="Test",
                references=[],
                target="test",
                pkg_type="apk",
            ),
            TrivyFinding(
                vulnerability_id="CVE-2021-12347",
                pkg_name="curl",
                installed_version="1.0",
                fixed_version="2.0",
                severity=TrivySeverity.LOW,
                title="Test",
                description="Test",
                references=[],
                target="test",
                pkg_type="apk",
            ),
        ]
        
        result = TrivyScanResult(
            target="test",
            scan_type=TrivyScanType.IMAGE,
            findings=findings,
            scan_time=datetime.now(),
        )
        
        assert result.packages == {"openssl", "curl"}


class TestTrivyScanner:
    """Test TrivyScanner class"""
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    def test_scanner_initialization(self, mock_which):
        """Test scanner initialization"""
        mock_which.return_value = "/usr/bin/trivy"
        
        scanner = TrivyScanner(
            min_severity=TrivySeverity.HIGH,
            scan_type=TrivyScanType.IMAGE,
        )
        
        assert scanner.min_severity == TrivySeverity.HIGH
        assert scanner.scan_type == TrivyScanType.IMAGE
    
    @patch("security_assistant.scanners.trivy_scanner.os.getenv")
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    def test_trivy_not_installed(self, mock_which, mock_getenv):
        """Test error when Trivy is not installed"""
        mock_which.return_value = None
        mock_getenv.return_value = None
        
        with pytest.raises(TrivyNotInstalledError):
            TrivyScanner()
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    def test_get_severity_filter(self, mock_which):
        """Test severity filter generation"""
        mock_which.return_value = "/usr/bin/trivy"
        
        scanner = TrivyScanner(min_severity=TrivySeverity.HIGH)
        severity_filter = scanner._get_severity_filter()
        
        assert "CRITICAL" in severity_filter
        assert "HIGH" in severity_filter
        assert "MEDIUM" not in severity_filter
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    @patch("security_assistant.scanners.trivy_scanner.subprocess.run")
    def test_scan_image_success(self, mock_run, mock_which):
        """Test successful image scan"""
        mock_which.return_value = "/usr/bin/trivy"
        
        # Mock Trivy output
        trivy_output = {
            "Results": [
                {
                    "Target": "alpine:3.15",
                    "Type": "apk",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2021-12345",
                            "PkgName": "openssl",
                            "InstalledVersion": "1.1.1k",
                            "FixedVersion": "1.1.1l",
                            "Severity": "HIGH",
                            "Title": "OpenSSL vulnerability",
                            "Description": "Buffer overflow",
                            "References": ["https://example.com"],
                        }
                    ],
                }
            ]
        }
        
        mock_run.return_value = Mock(
            returncode=1,  # Trivy returns 1 when vulnerabilities found
            stdout=json.dumps(trivy_output),
            stderr="",
        )
        
        scanner = TrivyScanner()
        result = scanner.scan_image("alpine:3.15")
        
        assert result.target == "alpine:3.15"
        assert result.vulnerability_count == 1
        assert result.findings[0].vulnerability_id == "CVE-2021-12345"
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    @patch("security_assistant.scanners.trivy_scanner.subprocess.run")
    def test_scan_filesystem_success(self, mock_run, mock_which):
        """Test successful filesystem scan"""
        mock_which.return_value = "/usr/bin/trivy"
        
        trivy_output = {
            "Results": [
                {
                    "Target": "/path/to/project",
                    "Type": "pip",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2021-99999",
                            "PkgName": "requests",
                            "InstalledVersion": "2.25.0",
                            "FixedVersion": "2.26.0",
                            "Severity": "MEDIUM",
                            "Title": "Requests vulnerability",
                            "Description": "Security issue",
                            "References": [],
                        }
                    ],
                }
            ]
        }
        
        mock_run.return_value = Mock(
            returncode=1,
            stdout=json.dumps(trivy_output),
            stderr="",
        )
        
        scanner = TrivyScanner()
        
        with patch("pathlib.Path.exists", return_value=True):
            result = scanner.scan_filesystem("/path/to/project")
        
        assert result.vulnerability_count == 1
        assert result.findings[0].pkg_name == "requests"
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    def test_scan_filesystem_not_found(self, mock_which):
        """Test filesystem scan with non-existent path"""
        mock_which.return_value = "/usr/bin/trivy"
        
        scanner = TrivyScanner()
        
        with pytest.raises(FileNotFoundError):
            scanner.scan_filesystem("/nonexistent/path")
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    @patch("security_assistant.scanners.trivy_scanner.subprocess.run")
    def test_scan_timeout(self, mock_run, mock_which):
        """Test scan timeout handling"""
        mock_which.return_value = "/usr/bin/trivy"
        mock_run.side_effect = subprocess.TimeoutExpired("trivy", 600)
        
        scanner = TrivyScanner(timeout=600)
        
        with pytest.raises(TrivyScannerError, match="timed out"):
            scanner.scan_image("alpine:3.15")
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    @patch("security_assistant.scanners.trivy_scanner.subprocess.run")
    def test_scan_error(self, mock_run, mock_which):
        """Test scan error handling"""
        mock_which.return_value = "/usr/bin/trivy"
        mock_run.return_value = Mock(
            returncode=2,
            stdout="",
            stderr="Trivy error",
        )
        
        scanner = TrivyScanner()
        
        with pytest.raises(TrivyScannerError, match="failed"):
            scanner.scan_image("alpine:3.15")
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    @patch("security_assistant.scanners.trivy_scanner.subprocess.run")
    def test_parse_secrets(self, mock_run, mock_which):
        """Test parsing secret findings"""
        mock_which.return_value = "/usr/bin/trivy"
        
        trivy_output = {
            "Results": [
                {
                    "Target": "app.py",
                    "Type": "secret",
                    "Secrets": [
                        {
                            "RuleID": "aws-access-key-id",
                            "Title": "AWS Access Key ID",
                            "Severity": "HIGH",
                            "Match": "AKIAIOSFODNN7EXAMPLE",
                            "StartLine": 10,
                            "EndLine": 10,
                        }
                    ],
                }
            ]
        }
        
        mock_run.return_value = Mock(
            returncode=1,
            stdout=json.dumps(trivy_output),
            stderr="",
        )
        
        scanner = TrivyScanner()
        
        with patch("pathlib.Path.exists", return_value=True):
            result = scanner.scan_filesystem(".")
        
        assert result.secret_count == 1
        assert result.findings[0].pkg_type == "secret"
        assert result.findings[0].start_line == 10
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    @patch("security_assistant.scanners.trivy_scanner.subprocess.run")
    def test_parse_misconfigurations(self, mock_run, mock_which):
        """Test parsing misconfiguration findings"""
        mock_which.return_value = "/usr/bin/trivy"
        
        trivy_output = {
            "Results": [
                {
                    "Target": "Dockerfile",
                    "Type": "dockerfile",
                    "Misconfigurations": [
                        {
                            "ID": "DS002",
                            "Title": "Image user should not be root",
                            "Severity": "HIGH",
                            "Description": "Running as root is dangerous",
                            "Resolution": "Add USER instruction",
                            "References": ["https://example.com"],
                        }
                    ],
                }
            ]
        }
        
        mock_run.return_value = Mock(
            returncode=1,
            stdout=json.dumps(trivy_output),
            stderr="",
        )
        
        scanner = TrivyScanner()
        
        with patch("pathlib.Path.exists", return_value=True):
            result = scanner.scan_filesystem(".")
        
        assert result.misconfig_count == 1
        assert result.findings[0].pkg_type == "misconfig"
        assert result.findings[0].resolution == "Add USER instruction"
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    def test_finding_to_issue_vulnerability(self, mock_which):
        """Test converting vulnerability finding to issue"""
        mock_which.return_value = "/usr/bin/trivy"
        
        finding = TrivyFinding(
            vulnerability_id="CVE-2021-12345",
            pkg_name="openssl",
            installed_version="1.1.1k",
            fixed_version="1.1.1l",
            severity=TrivySeverity.HIGH,
            title="OpenSSL vulnerability",
            description="Buffer overflow in OpenSSL",
            references=["https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-12345"],
            target="alpine:3.15",
            pkg_type="apk",
            cvss_score=7.5,
            cwe_ids=["CWE-119"],
        )
        
        scanner = TrivyScanner()
        issue = scanner.finding_to_issue(finding, "test/project")
        
        assert "CVE-2021-12345" in issue.title
        assert "openssl" in issue.title
        assert "🟠" in issue.title  # HIGH severity emoji
        assert "openssl" in issue.description
        assert "1.1.1l" in issue.description
        assert "security" in issue.labels
        assert "trivy" in issue.labels
        assert issue.confidential is True
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    def test_finding_to_issue_secret(self, mock_which):
        """Test converting secret finding to issue"""
        mock_which.return_value = "/usr/bin/trivy"
        
        finding = TrivyFinding(
            vulnerability_id="aws-access-key-id",
            pkg_name="Secret",
            installed_version="",
            fixed_version="",
            severity=TrivySeverity.HIGH,
            title="AWS Access Key ID",
            description="Secret found: AKIAIOSFODNN7EXAMPLE",
            references=[],
            target="app.py",
            pkg_type="secret",
            start_line=10,
            end_line=10,
        )
        
        scanner = TrivyScanner()
        issue = scanner.finding_to_issue(finding, "test/project")
        
        assert "Secret Detected" in issue.title
        assert "AWS Access Key ID" in issue.title
        assert "Lines 10-10" in issue.description
        assert "secret-detection" in issue.labels
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    def test_scan_result_to_issues_individual(self, mock_which):
        """Test converting scan result to individual issues"""
        mock_which.return_value = "/usr/bin/trivy"
        
        findings = [
            TrivyFinding(
                vulnerability_id="CVE-2021-12345",
                pkg_name="openssl",
                installed_version="1.0",
                fixed_version="2.0",
                severity=TrivySeverity.HIGH,
                title="Test",
                description="Test",
                references=[],
                target="alpine:3.15",
                pkg_type="apk",
            ),
            TrivyFinding(
                vulnerability_id="CVE-2021-12346",
                pkg_name="curl",
                installed_version="1.0",
                fixed_version="2.0",
                severity=TrivySeverity.MEDIUM,
                title="Test",
                description="Test",
                references=[],
                target="alpine:3.15",
                pkg_type="apk",
            ),
        ]
        
        result = TrivyScanResult(
            target="alpine:3.15",
            scan_type=TrivyScanType.IMAGE,
            findings=findings,
            scan_time=datetime.now(),
        )
        
        scanner = TrivyScanner()
        issues = scanner.scan_result_to_issues(result, "test/project")
        
        assert len(issues) == 2
        assert all(isinstance(issue, IssueData) for issue in issues)
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    def test_scan_result_to_issues_grouped(self, mock_which):
        """Test converting scan result to grouped issues"""
        mock_which.return_value = "/usr/bin/trivy"
        
        findings = [
            TrivyFinding(
                vulnerability_id="CVE-2021-12345",
                pkg_name="openssl",
                installed_version="1.0",
                fixed_version="2.0",
                severity=TrivySeverity.HIGH,
                title="Test",
                description="Test vulnerability 1",
                references=[],
                target="alpine:3.15",
                pkg_type="apk",
            ),
            TrivyFinding(
                vulnerability_id="CVE-2021-12346",
                pkg_name="curl",
                installed_version="1.0",
                fixed_version="2.0",
                severity=TrivySeverity.HIGH,
                title="Test",
                description="Test vulnerability 2",
                references=[],
                target="alpine:3.15",
                pkg_type="apk",
            ),
            TrivyFinding(
                vulnerability_id="CVE-2021-12347",
                pkg_name="zlib",
                installed_version="1.0",
                fixed_version="2.0",
                severity=TrivySeverity.MEDIUM,
                title="Test",
                description="Test vulnerability 3",
                references=[],
                target="alpine:3.15",
                pkg_type="apk",
            ),
        ]
        
        result = TrivyScanResult(
            target="alpine:3.15",
            scan_type=TrivyScanType.IMAGE,
            findings=findings,
            scan_time=datetime.now(),
        )
        
        scanner = TrivyScanner()
        issues = scanner.scan_result_to_issues(result, "test/project", group_by_severity=True)
        
        assert len(issues) == 2  # HIGH and MEDIUM groups
        assert "2 findings" in issues[0].title  # HIGH group
        assert "1 findings" in issues[1].title  # MEDIUM group
        assert "grouped" in issues[0].labels


# Import subprocess for timeout test
import subprocess
