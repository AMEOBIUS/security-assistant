"""
Integration tests for GitLab API.
These tests require a real GitLab token and project.
Set GITLAB_PERSONAL_TOKEN (or GITLAB_TOKEN) and GITLAB_TEST_PROJECT environment variables to run.
"""

import os
import pytest
from datetime import datetime

from security_assistant.gitlab_api import GitLabAPI, IssueData


# Skip integration tests if credentials not provided
pytestmark = pytest.mark.skipif(
    not (os.getenv("GITLAB_TOKEN") or os.getenv("GITLAB_PERSONAL_TOKEN")) or not os.getenv("GITLAB_TEST_PROJECT"),
    reason="Integration tests require GITLAB_TOKEN and GITLAB_TEST_PROJECT"
)


class TestGitLabAPIIntegration:
    """Integration tests with real GitLab API."""
    
    @pytest.fixture
    def api(self):
        """Create GitLab API client."""
        return GitLabAPI()
    
    @pytest.fixture
    def test_project(self):
        """Get test project ID from environment."""
        return os.getenv("GITLAB_TEST_PROJECT")
    
    def test_get_project_info(self, api, test_project):
        """Test fetching real project information."""
        project = api.get_project(test_project)
        
        assert "id" in project
        assert "name" in project
        assert "path_with_namespace" in project
        
        print(f"\nProject: {project['name']}")
        print(f"URL: {project['web_url']}")
    
    def test_create_and_list_issue(self, api, test_project):
        """Test creating a real issue and listing it."""
        # Create test issue
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        issue_data = IssueData(
            title=f"[TEST] Security Assistant Integration Test - {timestamp}",
            description=f"""
## Test Issue

This is an automated test issue created by Security Assistant integration tests.

**Created:** {timestamp}
**Purpose:** Verify GitLab API integration

### Details
- Rate limiting: ✅
- Error handling: ✅
- Issue creation: ✅

**Note:** This issue can be safely closed.
            """.strip(),
            labels=["test", "automation"],
            confidential=False  # Not confidential for test
        )
        
        # Create issue
        created_issue = api.create_issue(test_project, issue_data)
        
        assert "id" in created_issue
        assert "iid" in created_issue
        assert "web_url" in created_issue
        assert created_issue["title"] == issue_data.title
        
        print(f"\nIssue created: {created_issue['web_url']}")
        print(f"Issue IID: {created_issue['iid']}")
        
        # List issues with test label
        issues = api.list_issues(test_project, labels=["test"])
        
        assert len(issues) > 0
        assert any(issue["id"] == created_issue["id"] for issue in issues)
        
        print(f"Found {len(issues)} test issues")
    
    def test_rate_limiting(self, api, test_project):
        """Test that rate limiting works correctly."""
        # Make multiple requests
        for i in range(5):
            project = api.get_project(test_project)
            assert "id" in project
        
        # Should complete without rate limit errors
        print("\nRate limiting test passed - 5 requests completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
