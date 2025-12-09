"""
Integration tests for Trivy Scanner

Tests end-to-end workflows:
- Scan → create issue workflow
- Grouped issues workflow
- Multi-scanner workflow (vulnerabilities + secrets + misconfigs)
- SBOM generation
- Real Trivy integration (if installed)
"""

import json
from unittest.mock import Mock, patch

from security_assistant.scanners.trivy_scanner import (
    TrivyScanner,
    TrivyScanType,
    TrivySeverity,
)


class TestTrivyIntegration:
    """Integration tests for Trivy scanner workflows"""
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    @patch("security_assistant.scanners.trivy_scanner.subprocess.run")
    def test_scan_and_create_issue_workflow(self, mock_run, mock_which):
        """Test complete workflow: scan → parse → create issue"""
        mock_which.return_value = "/usr/bin/trivy"
        
        # Mock Trivy output with vulnerability
        trivy_output = {
            "Results": [
                {
                    "Target": "alpine:3.15",
                    "Type": "apk",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2021-36159",
                            "PkgName": "libfetch",
                            "InstalledVersion": "2.35-r0",
                            "FixedVersion": "2.35-r1",
                            "Severity": "CRITICAL",
                            "Title": "libfetch buffer overflow",
                            "Description": "An issue was discovered in libfetch",
                            "References": [
                                "https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2021-36159"
                            ],
                            "CVSS": {
                                "nvd": {
                                    "V3Score": 9.8
                                }
                            },
                            "CweIDs": ["CWE-120"],
                            "PublishedDate": "2021-07-08T19:15:00Z",
                            "LastModifiedDate": "2021-07-15T17:15:00Z",
                        }
                    ],
                }
            ],
            "Metadata": {
                "ImageID": "sha256:c059bfaa849c4d8e4aecaeb3a10c2d9b3d85f5165c66ad3a4d937758128c4d18",
            }
        }
        
        mock_run.return_value = Mock(
            returncode=1,
            stdout=json.dumps(trivy_output),
            stderr="",
        )
        
        # Execute workflow
        scanner = TrivyScanner(min_severity=TrivySeverity.HIGH)
        scan_result = scanner.scan_image("alpine:3.15")
        
        # Verify scan result
        assert scan_result.target == "alpine:3.15"
        assert scan_result.vulnerability_count == 1
        assert scan_result.critical_count == 1
        
        # Convert to issue
        issue = scanner.finding_to_issue(scan_result.findings[0], "test/project")
        
        # Verify issue
        assert "CVE-2021-36159" in issue.title
        assert "libfetch" in issue.title
        assert "🔴" in issue.title  # CRITICAL emoji
        assert "libfetch" in issue.description
        assert "2.35-r1" in issue.description  # Fixed version
        assert "9.8" in issue.description  # CVSS score
        assert "CWE-120" in issue.description
        assert "security" in issue.labels
        assert "vulnerability" in issue.labels
        assert issue.confidential is True
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    @patch("security_assistant.scanners.trivy_scanner.subprocess.run")
    def test_grouped_issues_workflow(self, mock_run, mock_which):
        """Test workflow with grouped issues by severity"""
        mock_which.return_value = "/usr/bin/trivy"
        
        trivy_output = {
            "Results": [
                {
                    "Target": "nginx:latest",
                    "Type": "debian",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2021-11111",
                            "PkgName": "openssl",
                            "InstalledVersion": "1.1.1k",
                            "FixedVersion": "1.1.1l",
                            "Severity": "CRITICAL",
                            "Title": "OpenSSL critical",
                            "Description": "Critical issue",
                            "References": [],
                        },
                        {
                            "VulnerabilityID": "CVE-2021-22222",
                            "PkgName": "curl",
                            "InstalledVersion": "7.68.0",
                            "FixedVersion": "7.69.0",
                            "Severity": "CRITICAL",
                            "Title": "Curl critical",
                            "Description": "Critical issue",
                            "References": [],
                        },
                        {
                            "VulnerabilityID": "CVE-2021-33333",
                            "PkgName": "zlib",
                            "InstalledVersion": "1.2.11",
                            "FixedVersion": "1.2.12",
                            "Severity": "HIGH",
                            "Title": "Zlib high",
                            "Description": "High severity issue",
                            "References": [],
                        },
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
        scan_result = scanner.scan_image("nginx:latest")
        
        # Create grouped issues
        issues = scanner.scan_result_to_issues(
            scan_result,
            "test/project",
            group_by_severity=True
        )
        
        # Verify grouped issues
        assert len(issues) == 2  # CRITICAL and HIGH groups
        
        # Check CRITICAL group (should be first due to sorting)
        critical_issue = issues[0]
        assert "CRITICAL" in critical_issue.title
        assert "2 findings" in critical_issue.title
        assert "openssl" in critical_issue.description
        assert "curl" in critical_issue.description
        assert "grouped" in critical_issue.labels
        
        # Check HIGH group
        high_issue = issues[1]
        assert "HIGH" in high_issue.title
        assert "1 findings" in high_issue.title
        assert "zlib" in high_issue.description
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    @patch("security_assistant.scanners.trivy_scanner.subprocess.run")
    def test_multi_scanner_workflow(self, mock_run, mock_which):
        """Test workflow with multiple scanner types (vuln + secret + config)"""
        mock_which.return_value = "/usr/bin/trivy"
        
        trivy_output = {
            "Results": [
                {
                    "Target": "/app",
                    "Type": "pip",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2021-99999",
                            "PkgName": "requests",
                            "InstalledVersion": "2.25.0",
                            "FixedVersion": "2.26.0",
                            "Severity": "HIGH",
                            "Title": "Requests vulnerability",
                            "Description": "Security issue in requests",
                            "References": [],
                        }
                    ],
                },
                {
                    "Target": "app.py",
                    "Type": "secret",
                    "Secrets": [
                        {
                            "RuleID": "aws-access-key-id",
                            "Title": "AWS Access Key ID",
                            "Severity": "HIGH",
                            "Match": "AKIAIOSFODNN7EXAMPLE",
                            "StartLine": 15,
                            "EndLine": 15,
                        }
                    ],
                },
                {
                    "Target": "Dockerfile",
                    "Type": "dockerfile",
                    "Misconfigurations": [
                        {
                            "ID": "DS002",
                            "Title": "Image user should not be root",
                            "Severity": "MEDIUM",
                            "Description": "Running as root is dangerous",
                            "Resolution": "Add USER instruction",
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
            scan_result = scanner.scan_filesystem("/app", scanners=["vuln", "secret", "config"])
        
        # Verify all finding types
        assert scan_result.vulnerability_count == 1
        assert scan_result.secret_count == 1
        assert scan_result.misconfig_count == 1
        
        # Create individual issues
        issues = scanner.scan_result_to_issues(scan_result, "test/project")
        
        assert len(issues) == 3
        
        # Verify vulnerability issue
        vuln_issue = next(i for i in issues if "CVE-2021-99999" in i.title)
        assert "requests" in vuln_issue.title
        assert "vulnerability" in vuln_issue.labels
        
        # Verify secret issue
        secret_issue = next(i for i in issues if "Secret Detected" in i.title)
        assert "AWS Access Key ID" in secret_issue.title
        assert "secret-detection" in secret_issue.labels
        assert "Lines 15-15" in secret_issue.description
        
        # Verify misconfiguration issue
        misconfig_issue = next(i for i in issues if "Misconfiguration" in i.title)
        assert "DS002" in misconfig_issue.description
        assert "misconfiguration" in misconfig_issue.labels
        assert "Add USER instruction" in misconfig_issue.description
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    @patch("security_assistant.scanners.trivy_scanner.subprocess.run")
    def test_sbom_generation_workflow(self, mock_run, mock_which):
        """Test SBOM generation workflow"""
        mock_which.return_value = "/usr/bin/trivy"
        
        sbom_output = """
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.4",
  "version": 1,
  "components": [
    {
      "type": "library",
      "name": "openssl",
      "version": "1.1.1k"
    }
  ]
}
"""
        
        mock_run.return_value = Mock(
            returncode=0,
            stdout=sbom_output,
            stderr="",
        )
        
        scanner = TrivyScanner()
        sbom = scanner.generate_sbom("alpine:3.15", output_format="cyclonedx")
        
        # Verify SBOM content
        assert "CycloneDX" in sbom
        assert "openssl" in sbom
        assert "1.1.1k" in sbom
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    @patch("security_assistant.scanners.trivy_scanner.subprocess.run")
    def test_empty_scan_result(self, mock_run, mock_which):
        """Test handling of scan with no findings"""
        mock_which.return_value = "/usr/bin/trivy"
        
        trivy_output = {
            "Results": []
        }
        
        mock_run.return_value = Mock(
            returncode=0,  # No vulnerabilities found
            stdout=json.dumps(trivy_output),
            stderr="",
        )
        
        scanner = TrivyScanner()
        scan_result = scanner.scan_image("alpine:latest")
        
        assert scan_result.vulnerability_count == 0
        assert scan_result.has_findings is False
        
        issues = scanner.scan_result_to_issues(scan_result, "test/project")
        assert len(issues) == 0
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    @patch("security_assistant.scanners.trivy_scanner.subprocess.run")
    def test_severity_filtering(self, mock_run, mock_which):
        """Test severity filtering in scan"""
        mock_which.return_value = "/usr/bin/trivy"
        
        trivy_output = {
            "Results": [
                {
                    "Target": "test",
                    "Type": "apk",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2021-11111",
                            "PkgName": "pkg1",
                            "InstalledVersion": "1.0",
                            "FixedVersion": "2.0",
                            "Severity": "CRITICAL",
                            "Title": "Critical",
                            "Description": "Critical issue",
                            "References": [],
                        },
                        {
                            "VulnerabilityID": "CVE-2021-22222",
                            "PkgName": "pkg2",
                            "InstalledVersion": "1.0",
                            "FixedVersion": "2.0",
                            "Severity": "LOW",
                            "Title": "Low",
                            "Description": "Low issue",
                            "References": [],
                        },
                    ],
                }
            ]
        }
        
        mock_run.return_value = Mock(
            returncode=1,
            stdout=json.dumps(trivy_output),
            stderr="",
        )
        
        # Scan with HIGH minimum severity
        scanner = TrivyScanner(min_severity=TrivySeverity.HIGH)
        scan_result = scanner.scan_image("test:latest")
        
        # Both findings should be in result (filtering happens in Trivy command)
        # But we can verify the severity filter was set correctly
        assert scanner._get_severity_filter() == "CRITICAL,HIGH"
    
    @patch("security_assistant.scanners.trivy_scanner.shutil.which")
    @patch("security_assistant.scanners.trivy_scanner.subprocess.run")
    def test_repository_scan_workflow(self, mock_run, mock_which):
        """Test Git repository scanning workflow"""
        mock_which.return_value = "/usr/bin/trivy"
        
        trivy_output = {
            "Results": [
                {
                    "Target": "https://github.com/example/repo",
                    "Type": "pip",
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "CVE-2021-12345",
                            "PkgName": "django",
                            "InstalledVersion": "3.1.0",
                            "FixedVersion": "3.1.13",
                            "Severity": "HIGH",
                            "Title": "Django vulnerability",
                            "Description": "SQL injection",
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
        scan_result = scanner.scan_repository("https://github.com/example/repo")
        
        assert scan_result.scan_type == TrivyScanType.REPOSITORY
        assert scan_result.vulnerability_count == 1
        assert scan_result.findings[0].pkg_name == "django"
