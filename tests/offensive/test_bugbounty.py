"""
Test bug bounty integration.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from security_assistant.offensive.authorization import AuthorizationService
from security_assistant.offensive.bugbounty.bugcrowd import BugcrowdClient
from security_assistant.offensive.bugbounty.hackerone import HackerOneClient
from security_assistant.offensive.bugbounty.submission import BugBountySubmission
from security_assistant.offensive.bugbounty.tracking import BountyTracker


def test_hackerone_client_initialization():
    """Test HackerOne client initialization."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    client = HackerOneClient(
        api_token="test_token",
        program_handle="test_program",
        auth_service=auth_service
    )
    
    assert client.api_token == "test_token"
    assert client.program_handle == "test_program"
    assert client.BASE_URL == "https://api.hackerone.com/v1"


def test_hackerone_client_validation():
    """Test HackerOne client validation."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    # Test invalid token
    try:
        HackerOneClient("", "test_program", auth_service)
        pytest.fail("Should raise ValueError for empty token")
    except ValueError:
        pass
    
    # Test invalid program handle
    try:
        HackerOneClient("test_token", "", auth_service)
        pytest.fail("Should raise ValueError for empty program handle")
    except ValueError:
        pass


@patch('requests.Session.request')
def test_hackerone_api_request(mock_request):
    """Test HackerOne API request."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": "test"}
    mock_request.return_value = mock_response
    
    client = HackerOneClient("test_token", "test_program", auth_service)
    result = client._make_request("GET", "test_endpoint")
    
    assert result == {"data": "test"}
    mock_request.assert_called_once()


def test_bugcrowd_client_initialization():
    """Test Bugcrowd client initialization."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    client = BugcrowdClient(
        api_token="test_token",
        program_id="test_program",
        auth_service=auth_service
    )
    
    assert client.api_token == "test_token"
    assert client.program_id == "test_program"
    assert client.BASE_URL == "https://api.bugcrowd.com"


@patch('requests.Session.request')
def test_bugcrowd_api_request(mock_request):
    """Test Bugcrowd API request."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"submissions": []}
    mock_request.return_value = mock_response
    
    client = BugcrowdClient("test_token", "test_program", auth_service)
    result = client._make_request("GET", "test_endpoint")
    
    assert result == {"submissions": []}
    mock_request.assert_called_once()


def test_bugbounty_submission_initialization():
    """Test bug bounty submission initialization."""
    from security_assistant.orchestrator import (
        FindingSeverity,
        ScannerType,
        UnifiedFinding,
    )
    
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    finding = UnifiedFinding(
        finding_id="test-1",
        scanner=ScannerType.BANDIT,
        severity=FindingSeverity.HIGH,
        category="Security",
        file_path="test.py",
        line_start=10,
        line_end=10,
        title="Test Vulnerability",
        description="Test description",
        code_snippet="import os\nprint('test')",
        priority_score=90
    )
    
    submission = BugBountySubmission(finding, "hackerone", auth_service)
    
    assert submission.finding == finding
    assert submission.platform == "hackerone"
    assert len(submission.evidence_files) == 0


def test_bugbounty_submission_validation():
    """Test bug bounty submission validation."""
    from security_assistant.orchestrator import (
        FindingSeverity,
        ScannerType,
        UnifiedFinding,
    )
    
    # Test without ToS acceptance
    auth_service = AuthorizationService()
    
    finding = UnifiedFinding(
        finding_id="test-1",
        scanner=ScannerType.BANDIT,
        severity=FindingSeverity.HIGH,
        category="Security",
        file_path="test.py",
        line_start=10,
        line_end=10,
        title="Test Vulnerability",
        description="Test description",
        code_snippet="import os\nprint('test')",
        priority_score=90
    )
    
    # The submission should be created but with a warning logged
    submission = BugBountySubmission(finding, "hackerone", auth_service)
    assert submission is not None


def test_bugbounty_submission_report_generation():
    """Test bug bounty report generation."""
    from security_assistant.orchestrator import (
        FindingSeverity,
        ScannerType,
        UnifiedFinding,
    )
    
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    finding = UnifiedFinding(
        finding_id="test-1",
        scanner=ScannerType.BANDIT,
        severity=FindingSeverity.HIGH,
        category="command_injection",
        file_path="test.py",
        line_start=10,
        line_end=10,
        title="Command Injection Vulnerability",
        description="Found command injection in test.py",
        code_snippet="import subprocess\nsubprocess.call('cmd', shell=True)",
        priority_score=90,
        cwe_ids=["CWE-78"],
        epss_score=0.85
    )
    
    submission = BugBountySubmission(finding, "hackerone", auth_service)
    
    # Test HackerOne report generation
    report = submission.generate_report_data()
    assert "title" in report
    assert "vulnerability_information" in report
    assert report["severity"] == "high"
    
    # Test Bugcrowd report generation
    submission.platform = "bugcrowd"
    bugcrowd_report = submission.generate_report_data()
    assert "title" in bugcrowd_report
    assert "description" in bugcrowd_report


def test_bounty_tracker_initialization():
    """Test bounty tracker initialization."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir) / "test_tracker.json"
        tracker = BountyTracker(str(storage_path), auth_service)
        
        assert len(tracker.submissions) == 0
        assert tracker.storage_path == storage_path


def test_bounty_tracker_submission_tracking():
    """Test bounty submission tracking."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir) / "test_tracker.json"
        tracker = BountyTracker(str(storage_path), auth_service)
        
        # Track a submission
        submission = tracker.track_submission(
            submission_id="sub-123",
            platform="hackerone",
            program="test-program",
            title="Test Submission",
            severity="high",
            status="submitted",
            bounty_amount=500.0
        )
        
        assert submission["submission_id"] == "sub-123"
        assert submission["platform"] == "hackerone"
        assert submission["status"] == "submitted"
        assert len(tracker.submissions) == 1


def test_bounty_tracker_stats():
    """Test bounty tracker statistics."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir) / "test_tracker.json"
        tracker = BountyTracker(str(storage_path), auth_service)
        
        # Add some test submissions
        tracker.track_submission("sub-1", "hackerone", "prog-1", "Test 1", "high", "triaged", 500.0)
        tracker.track_submission("sub-2", "bugcrowd", "prog-2", "Test 2", "medium", "submitted")
        tracker.track_submission("sub-3", "hackerone", "prog-1", "Test 3", "low", "resolved", 100.0)
        
        stats = tracker.get_stats()
        
        assert stats["total_submissions"] == 3
        assert stats["total_bounties"] == 600.0
        assert stats["average_bounty"] == 300.0
        assert stats["by_platform"]["hackerone"] == 2
        assert stats["by_platform"]["bugcrowd"] == 1


def test_bounty_tracker_report_generation():
    """Test bounty report generation."""
    auth_service = AuthorizationService()
    auth_service.accept_tos()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        storage_path = Path(temp_dir) / "test_tracker.json"
        tracker = BountyTracker(str(storage_path), auth_service)
        
        # Add a test submission
        tracker.track_submission("sub-1", "hackerone", "prog-1", "Test", "high", "triaged", 500.0)
        
        # Generate report
        report_path = Path(temp_dir) / "report.json"
        result = tracker.generate_report(str(report_path))
        
        assert report_path.exists()
        
        # Verify report content
        with open(report_path) as f:
            report_data = json.load(f)
            assert "generated_at" in report_data
            assert "stats" in report_data
            assert "submissions" in report_data


if __name__ == "__main__":
    test_hackerone_client_initialization()
    test_hackerone_client_validation()
    test_hackerone_api_request()
    test_bugcrowd_client_initialization()
    test_bugcrowd_api_request()
    test_bugbounty_submission_initialization()
    test_bugbounty_submission_validation()
    test_bugbounty_submission_report_generation()
    test_bounty_tracker_initialization()
    test_bounty_tracker_submission_tracking()
    test_bounty_tracker_stats()
    test_bounty_tracker_report_generation()
    print("✅ All bug bounty tests passed!")
