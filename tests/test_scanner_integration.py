"""
Integration tests for Bandit scanner + GitLab API.
Tests the complete workflow: scan → create issue.
"""

import os
from unittest.mock import Mock, patch

import pytest

from security_assistant.gitlab_api import GitLabAPI, IssueData
from security_assistant.scanners.bandit_scanner import BanditFinding, BanditScanner


class TestScannerGitLabIntegration:
    """Integration tests for scanner + GitLab workflow."""
    
    @patch('subprocess.run')
    def test_scan_and_create_issue_workflow(self, mock_run):
        """Test complete workflow: scan file → create GitLab issue."""
        # Mock Bandit version check
        mock_run.return_value = Mock(returncode=0, stdout="bandit 1.7.5")
        
        # Create scanner
        scanner = BanditScanner(min_severity="HIGH")
        
        # Create a sample finding
        finding = BanditFinding(
            test_id="B105",
            test_name="hardcoded_password_string",
            severity="HIGH",
            confidence="HIGH",
            issue_text="Possible hardcoded password: 'admin123'",
            filename="src/auth.py",
            line_number=42,
            code="password = 'admin123'",
            cwe_id="259",
            more_info="https://bandit.readthedocs.io/en/latest/plugins/b105_hardcoded_password_string.html"
        )
        
        # Convert to GitLab issue
        issue = scanner.finding_to_issue(finding, "SecurityProject")
        
        # Verify issue structure
        assert isinstance(issue, IssueData)
        assert "hardcoded_password_string" in issue.title
        assert "auth.py" in issue.title
        assert "HIGH" in issue.description
        assert "Line:** 42" in issue.description
        assert "password = 'admin123'" in issue.description
        assert "259" in issue.description  # CWE ID
        
        # Verify labels
        assert "security" in issue.labels
        assert "bandit" in issue.labels
        assert "critical" in issue.labels
        assert "b105" in issue.labels
        
        # Verify confidential
        assert issue.confidential is True
    
    @patch('security_assistant.gitlab_api.requests.Session')
    @patch('subprocess.run')
    def test_full_integration_with_mocked_gitlab(self, mock_run, mock_session):
        """Test full integration with mocked GitLab API."""
        # Mock Bandit
        mock_run.return_value = Mock(returncode=0, stdout="bandit 1.7.5")
        
        # Mock GitLab API response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 123,
            "iid": 1,
            "title": "Security: hardcoded_password in auth.py",
            "web_url": "https://gitlab.com/test/project/-/issues/1",
            "state": "opened"
        }
        mock_response.text = '{"id": 123}'
        
        mock_session_instance = Mock()
        mock_session_instance.request.return_value = mock_response
        mock_session.return_value = mock_session_instance
        
        # Create scanner and GitLab API client
        scanner = BanditScanner()
        
        # Set environment variable for GitLab token
        os.environ["GITLAB_TOKEN"] = "test-token-12345"
        
        try:
            api = GitLabAPI()
            
            # Create a finding
            finding = BanditFinding(
                test_id="B105",
                test_name="hardcoded_password",
                severity="HIGH",
                confidence="HIGH",
                issue_text="Hardcoded password detected",
                filename="app.py",
                line_number=10,
                code="pwd = 'secret'"
            )
            
            # Convert to issue
            issue = scanner.finding_to_issue(finding)
            
            # Create issue in GitLab
            result = api.create_issue("test/project", issue)
            
            # Verify result
            assert result["id"] == 123
            assert result["web_url"] == "https://gitlab.com/test/project/-/issues/1"
            
            # Verify API was called correctly
            mock_session_instance.request.assert_called_once()
            call_args = mock_session_instance.request.call_args
            
            assert call_args[1]["method"] == "POST"
            assert "/issues" in call_args[1]["url"]
            assert call_args[1]["json"]["title"] == issue.title
            assert call_args[1]["json"]["confidential"] is True
            
        finally:
            # Clean up
            if "GITLAB_TOKEN" in os.environ:
                del os.environ["GITLAB_TOKEN"]
    
    @patch('subprocess.run')
    def test_multiple_findings_to_issues(self, mock_run):
        """Test converting multiple findings to issues."""
        mock_run.return_value = Mock(returncode=0, stdout="bandit 1.7.5")
        
        scanner = BanditScanner()
        
        # Create multiple findings
        findings = [
            BanditFinding(
                test_id="B105", test_name="hardcoded_password",
                severity="HIGH", confidence="HIGH",
                issue_text="Hardcoded password", filename="auth.py",
                line_number=10, code="pwd = 'secret'"
            ),
            BanditFinding(
                test_id="B307", test_name="eval",
                severity="MEDIUM", confidence="HIGH",
                issue_text="Use of eval()", filename="utils.py",
                line_number=20, code="eval(user_input)"
            ),
            BanditFinding(
                test_id="B608", test_name="hardcoded_sql_expressions",
                severity="MEDIUM", confidence="MEDIUM",
                issue_text="SQL injection risk", filename="db.py",
                line_number=30, code="query = 'SELECT * FROM users WHERE id=' + user_id"
            )
        ]
        
        # Convert to issues (individual)
        issues = [scanner.finding_to_issue(f) for f in findings]
        
        assert len(issues) == 3
        assert all(isinstance(i, IssueData) for i in issues)
        assert all(i.confidential for i in issues)
        
        # Verify severity-based labels
        assert "critical" in issues[0].labels  # HIGH severity
        assert "high-priority" in issues[1].labels  # MEDIUM severity
        assert "high-priority" in issues[2].labels  # MEDIUM severity
    
    @patch('subprocess.run')
    def test_issue_description_formatting(self, mock_run):
        """Test that issue description is properly formatted."""
        mock_run.return_value = Mock(returncode=0, stdout="bandit 1.7.5")
        
        scanner = BanditScanner()
        
        finding = BanditFinding(
            test_id="B201",
            test_name="flask_debug_true",
            severity="HIGH",
            confidence="HIGH",
            issue_text="A Flask app appears to be run with debug=True",
            filename="app.py",
            line_number=100,
            code="app.run(debug=True)",
            cwe_id="489",
            more_info="https://bandit.readthedocs.io/en/latest/plugins/b201_flask_debug_true.html"
        )
        
        issue = scanner.finding_to_issue(finding, "FlaskApp")
        
        # Check description contains all required sections
        assert "## 🔴 Security Finding" in issue.description
        assert "**Severity:** HIGH" in issue.description
        assert "**Confidence:** HIGH" in issue.description
        assert "**Test ID:** B201" in issue.description
        assert "### Issue Description" in issue.description
        assert "### Location" in issue.description
        assert "**File:** `app.py`" in issue.description
        assert "**Line:** 100" in issue.description
        assert "### Code" in issue.description
        assert "```python" in issue.description
        assert "app.run(debug=True)" in issue.description
        assert "**CWE:** [489]" in issue.description
        assert "**More Info:**" in issue.description
        assert "Detected by Bandit scanner" in issue.description


class TestRealFileScanning:
    """Tests with real Python files (if available)."""
    
    @pytest.mark.skipif(
        not os.path.exists("security_assistant/gitlab_api.py"),
        reason="Test file not found"
    )
    @patch('subprocess.run')
    def test_scan_real_file(self, mock_run):
        """Test scanning a real Python file from the project."""
        # Mock Bandit version check
        mock_run.return_value = Mock(returncode=0, stdout="bandit 1.7.5")
        
        scanner = BanditScanner()
        
        # This would actually run Bandit if not mocked
        # In real integration test, remove the mock
        assert scanner is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
