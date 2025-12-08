"""
Quick Integration Test - Create Test Issue in GitLab

This script creates a test issue in your GitLab project to verify
that the integration is working correctly.
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_assistant.gitlab_api import GitLabAPI, IssueData


def main():
    """Create a test issue in GitLab"""
    print("=" * 80)
    print("GitLab Integration Test - Create Test Issue")
    print("=" * 80)
    print()
    
    # Get configuration
    gitlab_token = os.getenv("GITLAB_TOKEN")
    project_id = os.getenv("GITLAB_PROJECT_ID", "76475459")
    
    if not gitlab_token:
        print("❌ ERROR: GITLAB_TOKEN not set")
        return 1
    
    print(f"Project ID: {project_id}")
    print()
    
    # Initialize API
    print("1. Initializing GitLab API...")
    api = GitLabAPI(private_token=gitlab_token)
    print("   ✓ API initialized")
    print()
    
    # Get project info
    print("2. Fetching project information...")
    project = api.get_project(project_id)
    print(f"   ✓ Project: {project['name']}")
    print(f"   ✓ URL: {project['web_url']}")
    print()
    
    # Create test issue
    print("3. Creating test issue...")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    issue_data = IssueData(
        title=f"🧪 [TEST] Security Assistant Integration Test - {timestamp}",
        description=f"""
## ✅ Integration Test Successful!

This is an automated test issue created by Security Assistant to verify GitLab integration.

### Test Details
- **Created:** {timestamp}
- **Purpose:** Verify GitLab API integration
- **Status:** ✅ All systems operational

### Verified Features
- ✅ GitLab API connection
- ✅ Authentication with project token
- ✅ Issue creation
- ✅ Rate limiting
- ✅ Error handling

### Next Steps
This issue can be safely closed. The Security Assistant is ready to:
1. Scan code for security vulnerabilities
2. Create issues automatically
3. Run multi-scanner orchestration
4. Generate security reports

---
*Created by Security Assistant v7.0*
*Session 7: Multi-Scanner Orchestration Complete*
        """.strip(),
        labels=["test", "automation", "security-assistant"],
        confidential=False  # Not confidential for test
    )
    
    try:
        created_issue = api.create_issue(project_id, issue_data)
        
        print(f"   ✓ Issue created successfully!")
        print()
        print("   Issue Details:")
        print(f"   - IID: #{created_issue['iid']}")
        print(f"   - Title: {created_issue['title']}")
        print(f"   - URL: {created_issue['web_url']}")
        print(f"   - State: {created_issue['state']}")
        print(f"   - Labels: {', '.join(created_issue.get('labels', []))}")
        print()
        
        # List recent issues
        print("4. Listing recent issues...")
        issues = api.list_issues(project_id, state="all")
        print(f"   ✓ Found {len(issues)} total issues in project")
        print()
        
        print("=" * 80)
        print("✅ SUCCESS: GitLab Integration Test Passed!")
        print("=" * 80)
        print()
        print("You can now:")
        print("1. View the test issue:", created_issue['web_url'])
        print("2. Run security scans: python examples/scan_and_create_issues.py")
        print("3. Use orchestrator: python examples/orchestrator_example.py")
        print("4. Close the test issue when done")
        print()
        
        return 0
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print()
        print("=" * 80)
        print("❌ FAILED: Could not create issue")
        print("=" * 80)
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
