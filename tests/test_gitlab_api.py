"""
Unit tests for GitLab API module.
Tests include mocking to avoid real API calls.
"""

import os
import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import Timeout, ConnectionError

from security_assistant.gitlab_api import (
    GitLabAPI,
    IssueData,
    RateLimiter,
    RateLimitConfig,
    GitLabAPIError,
    GitLabAuthError,
    GitLabRateLimitError
)


class TestRateLimiter:
    """Test rate limiter functionality."""
    
    def test_rate_limiter_allows_requests_within_limit(self):
        """Test that requests are allowed within rate limits."""
        config = RateLimitConfig(max_requests_per_minute=5, max_requests_per_hour=10)
        limiter = RateLimiter(config)
        
        # Should allow first 5 requests
        for _ in range(5):
            assert limiter.can_make_request()
            limiter.record_request()
        
        # Should block 6th request
        assert not limiter.can_make_request()
    
    def test_rate_limiter_cleans_old_requests(self):
        """Test that old requests are cleaned up."""
        config = RateLimitConfig(max_requests_per_minute=2, max_requests_per_hour=10)
        limiter = RateLimiter(config)
        
        # Make 2 requests
        limiter.record_request()
        limiter.record_request()
        
        # Should be at limit
        assert not limiter.can_make_request()
        
        # Simulate time passing (mock)
        limiter.minute_requests = [time.time() - 61]  # 61 seconds ago
        limiter._clean_old_requests()
        
        # Should allow new request
        assert limiter.can_make_request()


class TestGitLabAPI:
    """Test GitLab API client."""
    
    @patch.dict(os.environ, {"GITLAB_TOKEN": "test-token"})
    def test_init_with_env_variables(self):
        """Test initialization with environment variables."""
        api = GitLabAPI()
        assert api.gitlab_url == "https://gitlab.com"
        assert api.private_token == "test-token"
        assert api.api_url == "https://gitlab.com/api/v4"
    
    def test_init_without_token_raises_error(self):
        """Test that missing token raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(GitLabAuthError):
                GitLabAPI()
    
    @patch.dict(os.environ, {"GITLAB_TOKEN": "test-token"})
    def test_init_with_custom_url(self):
        """Test initialization with custom GitLab URL."""
        api = GitLabAPI(gitlab_url="https://gitlab.example.com")
        assert api.gitlab_url == "https://gitlab.example.com"
        assert api.api_url == "https://gitlab.example.com/api/v4"
    
    @patch.dict(os.environ, {"GITLAB_TOKEN": "test-token"})
    @patch("security_assistant.gitlab_api.requests.Session")
    def test_create_issue_success(self, mock_session_class):
        """Test successful issue creation."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 123,
            "iid": 1,
            "title": "Test Issue",
            "web_url": "https://gitlab.com/project/issues/1"
        }
        mock_response.text = '{"id": 123}'
        
        # Mock session
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session
        
        # Create API client
        api = GitLabAPI()
        
        # Create issue
        issue_data = IssueData(
            title="Test Issue",
            description="Test description",
            labels=["bug", "security"]
        )
        
        result = api.create_issue("test/project", issue_data)
        
        # Verify
        assert result["id"] == 123
        assert result["web_url"] == "https://gitlab.com/project/issues/1"
        mock_session.request.assert_called_once()
    
    @patch.dict(os.environ, {"GITLAB_TOKEN": "test-token"})
    @patch("security_assistant.gitlab_api.requests.Session")
    def test_create_issue_auth_error(self, mock_session_class):
        """Test authentication error handling."""
        # Mock 401 response
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = '{"message": "Unauthorized"}'
        
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session
        
        api = GitLabAPI()
        issue_data = IssueData(title="Test", description="Test")
        
        with pytest.raises(GitLabAuthError):
            api.create_issue("test/project", issue_data)
    
    @patch.dict(os.environ, {"GITLAB_TOKEN": "test-token"})
    @patch("security_assistant.gitlab_api.requests.Session")
    def test_create_issue_rate_limit_error(self, mock_session_class):
        """Test rate limit error handling."""
        # Mock 429 response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_response.text = '{"message": "Rate limit exceeded"}'
        
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session
        
        api = GitLabAPI()
        issue_data = IssueData(title="Test", description="Test")
        
        with pytest.raises(GitLabRateLimitError):
            api.create_issue("test/project", issue_data)
    
    @patch.dict(os.environ, {"GITLAB_TOKEN": "test-token"})
    @patch("security_assistant.gitlab_api.requests.Session")
    def test_create_issue_timeout(self, mock_session_class):
        """Test timeout handling."""
        mock_session = Mock()
        mock_session.request.side_effect = Timeout("Request timeout")
        mock_session.headers = {}
        mock_session_class.return_value = mock_session
        
        api = GitLabAPI()
        issue_data = IssueData(title="Test", description="Test")
        
        with pytest.raises(GitLabAPIError, match="Request timeout"):
            api.create_issue("test/project", issue_data)
    
    @patch.dict(os.environ, {"GITLAB_TOKEN": "test-token"})
    @patch("security_assistant.gitlab_api.requests.Session")
    def test_create_issue_connection_error(self, mock_session_class):
        """Test connection error handling."""
        mock_session = Mock()
        mock_session.request.side_effect = ConnectionError("Connection failed")
        mock_session.headers = {}
        mock_session_class.return_value = mock_session
        
        api = GitLabAPI()
        issue_data = IssueData(title="Test", description="Test")
        
        with pytest.raises(GitLabAPIError, match="Connection error"):
            api.create_issue("test/project", issue_data)
    
    @patch.dict(os.environ, {"GITLAB_TOKEN": "test-token"})
    @patch("security_assistant.gitlab_api.requests.Session")
    def test_get_project(self, mock_session_class):
        """Test get project functionality."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 123,
            "name": "Test Project",
            "path_with_namespace": "test/project"
        }
        mock_response.text = '{"id": 123}'
        
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session
        
        api = GitLabAPI()
        result = api.get_project("test/project")
        
        assert result["id"] == 123
        assert result["name"] == "Test Project"
    
    @patch.dict(os.environ, {"GITLAB_TOKEN": "test-token"})
    @patch("security_assistant.gitlab_api.requests.Session")
    def test_list_issues(self, mock_session_class):
        """Test list issues functionality."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": 1, "title": "Issue 1"},
            {"id": 2, "title": "Issue 2"}
        ]
        mock_response.text = '[{"id": 1}]'
        
        mock_session = Mock()
        mock_session.request.return_value = mock_response
        mock_session.headers = {}
        mock_session_class.return_value = mock_session
        
        api = GitLabAPI()
        result = api.list_issues("test/project", labels=["bug"])
        
        assert len(result) == 2
        assert result[0]["title"] == "Issue 1"
    
    @patch.dict(os.environ, {"GITLAB_TOKEN": "test-token"})
    def test_context_manager(self):
        """Test context manager usage."""
        with patch("security_assistant.gitlab_api.requests.Session"):
            with GitLabAPI() as api:
                assert api is not None
            # Session should be closed after exit


class TestIssueData:
    """Test IssueData dataclass."""
    
    def test_issue_data_creation(self):
        """Test creating IssueData instance."""
        issue = IssueData(
            title="Test Issue",
            description="Test description",
            labels=["bug", "security"],
            confidential=True
        )
        
        assert issue.title == "Test Issue"
        assert issue.description == "Test description"
        assert issue.labels == ["bug", "security"]
        assert issue.confidential is True
    
    def test_issue_data_defaults(self):
        """Test IssueData default values."""
        issue = IssueData(
            title="Test",
            description="Test"
        )
        
        assert issue.labels is None
        assert issue.assignee_ids is None
        assert issue.confidential is True
        assert issue.due_date is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
