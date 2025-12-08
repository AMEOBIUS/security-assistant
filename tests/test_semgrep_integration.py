"""
Integration tests for Semgrep scanner.
Tests end-to-end workflows with mocked GitLab API.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from security_assistant.scanners.semgrep_scanner import (
    SemgrepScanner,
    SemgrepScanResult,
    SemgrepFinding
)
from security_assistant.gitlab_api import GitLabAPI, IssueData


# Sample multi-language vulnerable code
SAMPLE_VULNERABLE_CODE = {
    "app.py": """
import os

def run_command(user_input):
    # Dangerous: command injection
    os.system(user_input)
    
def get_password():
    # Dangerous: hardcoded password
    password = "admin123"
    return password
""",
    "server.js": """
const express = require('express');
const app = express();

// Dangerous: no helmet protection
app.get('/user/:id', (req, res) => {
    // Dangerous: SQL injection
    const query = "SELECT * FROM users WHERE id = " + req.params.id;
    db.query(query);
});
""",
    "config.go": """
package main

import "crypto/md5"

func hashPassword(password string) string {
    // Dangerous: weak hash
    h := md5.New()
    h.Write([]byte(password))
    return string(h.Sum(nil))
}
"""
}


@pytest.fixture
def mock_semgrep_output():
    """Mock Semgrep JSON output with multi-language findings."""
    return {
        "results": [
            {
                "check_id": "python.lang.security.audit.dangerous-system-call",
                "path": "app.py",
                "start": {"line": 5, "col": 5},
                "end": {"line": 5, "col": 25},
                "extra": {
                    "message": "Detected use of os.system(). This is dangerous.",
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
                "check_id": "python.lang.security.audit.hardcoded-password",
                "path": "app.py",
                "start": {"line": 9, "col": 5},
                "end": {"line": 9, "col": 30},
                "extra": {
                    "message": "Hardcoded password detected.",
                    "severity": "WARNING",
                    "lines": 'password = "admin123"',
                    "metadata": {
                        "category": "security",
                        "cwe": ["CWE-798"],
                        "owasp": ["A07:2021 - Identification and Authentication Failures"]
                    }
                }
            },
            {
                "check_id": "javascript.express.security.audit.express-sql-injection",
                "path": "server.js",
                "start": {"line": 8, "col": 5},
                "end": {"line": 8, "col": 70},
                "extra": {
                    "message": "SQL injection vulnerability detected.",
                    "severity": "ERROR",
                    "lines": 'const query = "SELECT * FROM users WHERE id = " + req.params.id;',
                    "metadata": {
                        "category": "security",
                        "cwe": ["CWE-89"],
                        "owasp": ["A03:2021 - Injection"]
                    }
                }
            },
            {
                "check_id": "go.lang.security.audit.crypto.use-of-weak-crypto",
                "path": "config.go",
                "start": {"line": 6, "col": 5},
                "end": {"line": 6, "col": 20},
                "extra": {
                    "message": "Use of weak cryptographic algorithm MD5.",
                    "severity": "WARNING",
                    "lines": "h := md5.New()",
                    "metadata": {
                        "category": "security",
                        "cwe": ["CWE-327"],
                        "owasp": ["A02:2021 - Cryptographic Failures"]
                    }
                }
            }
        ],
        "errors": [],
        "paths": {
            "scanned": ["app.py", "server.js", "config.go"]
        }
    }


class TestSemgrepIntegration:
    """Integration tests for Semgrep scanner."""
    
    @patch('security_assistant.scanners.semgrep_scanner.subprocess.run')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_scan_and_create_issues_workflow(
        self,
        mock_isdir,
        mock_exists,
        mock_run,
        mock_semgrep_output
    ):
        """Test complete workflow: scan → create issues."""
        # Mock directory existence
        mock_exists.return_value = True
        mock_isdir.return_value = True
        
        # Mock Semgrep version check
        version_result = Mock(returncode=0, stdout="1.144.0")
        
        # Mock Semgrep scan
        scan_result = Mock(
            returncode=1,
            stdout=json.dumps(mock_semgrep_output),
            stderr=""
        )
        
        mock_run.side_effect = [version_result, scan_result]
        
        # Initialize scanner
        scanner = SemgrepScanner(min_severity="WARNING", config="p/security-audit")
        
        # Scan directory
        result = scanner.scan_directory("src/")
        
        # Verify scan results
        assert result.has_findings
        assert len(result.findings) == 4
        assert result.error_count == 2
        assert result.warning_count == 2
        assert result.files_scanned == 3
        assert result.languages == {"python", "javascript", "go"}
        
        # Convert to issues
        issues = scanner.scan_result_to_issues(result, "MyProject")
        
        # Verify issues
        assert len(issues) == 4
        assert all(isinstance(issue, IssueData) for issue in issues)
        assert all(issue.confidential for issue in issues)
        
        # Verify labels
        python_issues = [i for i in issues if "python" in i.labels]
        js_issues = [i for i in issues if "javascript" in i.labels]
        go_issues = [i for i in issues if "go" in i.labels]
        
        assert len(python_issues) == 2
        assert len(js_issues) == 1
        assert len(go_issues) == 1
    
    @patch('security_assistant.scanners.semgrep_scanner.subprocess.run')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_grouped_issues_workflow(
        self,
        mock_isdir,
        mock_exists,
        mock_run,
        mock_semgrep_output
    ):
        """Test workflow with grouped issues (one per file)."""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        
        version_result = Mock(returncode=0)
        scan_result = Mock(
            returncode=1,
            stdout=json.dumps(mock_semgrep_output),
            stderr=""
        )
        
        mock_run.side_effect = [version_result, scan_result]
        
        scanner = SemgrepScanner()
        result = scanner.scan_directory("src/")
        
        # Group by file
        issues = scanner.scan_result_to_issues(result, "MyProject", group_by_file=True)
        
        # Should have 3 issues (one per file)
        assert len(issues) == 3
        
        # Verify grouped issue structure
        for issue in issues:
            assert "Security:" in issue.title
            assert "issues in" in issue.title
            assert "multiple-issues" in issue.labels
    
    @patch('security_assistant.scanners.semgrep_scanner.subprocess.run')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    @patch('security_assistant.gitlab_api.GitLabAPI.create_issue')
    def test_full_integration_with_gitlab(
        self,
        mock_create_issue,
        mock_isdir,
        mock_exists,
        mock_run,
        mock_semgrep_output
    ):
        """Test full integration: scan → create GitLab issues."""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        
        version_result = Mock(returncode=0)
        scan_result = Mock(
            returncode=1,
            stdout=json.dumps(mock_semgrep_output),
            stderr=""
        )
        
        mock_run.side_effect = [version_result, scan_result]
        
        # Mock GitLab API
        mock_create_issue.return_value = {
            "id": 123,
            "iid": 1,
            "web_url": "https://gitlab.com/test/project/-/issues/1"
        }
        
        # Scan
        scanner = SemgrepScanner(min_severity="ERROR")
        result = scanner.scan_directory("src/")
        
        # Convert to issues
        issues = scanner.scan_result_to_issues(result, "MyProject")
        
        # Create issues in GitLab (mocked)
        gitlab = GitLabAPI(private_token="fake-token")
        created_issues = []
        
        for issue in issues:
            created = gitlab.create_issue(
                project_id="test/project",
                issue_data=issue
            )
            created_issues.append(created)
        
        # Verify
        assert len(created_issues) == 2  # Only ERROR severity
        assert mock_create_issue.call_count == 2
    
    @patch('security_assistant.scanners.semgrep_scanner.subprocess.run')
    @patch('os.path.exists')
    @patch('os.path.isfile')
    def test_multi_language_detection(
        self,
        mock_isfile,
        mock_exists,
        mock_run,
        mock_semgrep_output
    ):
        """Test detection of multiple languages."""
        mock_exists.return_value = True
        mock_isfile.return_value = True
        
        version_result = Mock(returncode=0)
        scan_result = Mock(
            returncode=1,
            stdout=json.dumps(mock_semgrep_output),
            stderr=""
        )
        
        mock_run.side_effect = [version_result, scan_result]
        
        scanner = SemgrepScanner()
        result = scanner.scan_file("app.py")
        
        # Verify languages detected
        assert "python" in result.languages
        assert "javascript" in result.languages
        assert "go" in result.languages
        
        # Verify findings per language
        python_findings = [f for f in result.findings if f.language == "python"]
        js_findings = [f for f in result.findings if f.language == "javascript"]
        go_findings = [f for f in result.findings if f.language == "go"]
        
        assert len(python_findings) == 2
        assert len(js_findings) == 1
        assert len(go_findings) == 1
    
    @patch('security_assistant.scanners.semgrep_scanner.subprocess.run')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_issue_description_formatting(
        self,
        mock_isdir,
        mock_exists,
        mock_run,
        mock_semgrep_output
    ):
        """Test issue description formatting."""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        
        version_result = Mock(returncode=0)
        scan_result = Mock(
            returncode=1,
            stdout=json.dumps(mock_semgrep_output),
            stderr=""
        )
        
        mock_run.side_effect = [version_result, scan_result]
        
        scanner = SemgrepScanner()
        result = scanner.scan_directory("src/")
        issues = scanner.scan_result_to_issues(result, "MyProject")
        
        # Check first issue (Python command injection)
        issue = issues[0]
        
        # Verify description contains key elements
        assert "Security Finding:" in issue.description
        assert "Severity:" in issue.description
        assert "Language:" in issue.description
        assert "Category:" in issue.description
        assert "Location" in issue.description
        assert "Code" in issue.description
        assert "CWE" in issue.description
        assert "OWASP" in issue.description
        assert "Detected by Semgrep scanner" in issue.description
        
        # Verify code block formatting
        assert "```python" in issue.description or "```javascript" in issue.description or "```go" in issue.description
    
    @patch('security_assistant.scanners.semgrep_scanner.subprocess.run')
    def test_custom_config_usage(self, mock_run):
        """Test using custom Semgrep config."""
        version_result = Mock(returncode=0)
        mock_run.return_value = version_result
        
        # Test different configs
        configs = [
            "auto",
            "p/security-audit",
            "p/owasp-top-ten",
            "p/ci",
            "custom_rules.yaml"
        ]
        
        for config in configs:
            scanner = SemgrepScanner(config=config)
            assert scanner.config == config
    
    @patch('security_assistant.scanners.semgrep_scanner.subprocess.run')
    @patch('os.path.exists')
    @patch('os.path.isdir')
    def test_error_handling_in_scan(
        self,
        mock_isdir,
        mock_exists,
        mock_run
    ):
        """Test error handling during scan."""
        mock_exists.return_value = True
        mock_isdir.return_value = True
        
        version_result = Mock(returncode=0)
        
        # Mock scan with errors
        output_with_errors = {
            "results": [],
            "errors": [
                {"message": "Failed to parse file.py"},
                {"message": "Timeout scanning large_file.js"}
            ],
            "paths": {"scanned": []}
        }
        
        scan_result = Mock(
            returncode=0,
            stdout=json.dumps(output_with_errors),
            stderr=""
        )
        
        mock_run.side_effect = [version_result, scan_result]
        
        scanner = SemgrepScanner()
        result = scanner.scan_directory("src/")
        
        # Verify errors captured
        assert len(result.errors) == 2
        assert "Failed to parse file.py" in result.errors
        assert "Timeout scanning large_file.js" in result.errors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
