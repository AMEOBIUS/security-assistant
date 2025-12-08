"""
Test GitLab Connection

This script tests the GitLab API connection and displays project information.
It helps verify that your GITLAB_TOKEN is set correctly.

Usage:
    python examples/test_gitlab_connection.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_assistant.gitlab_api import GitLabAPI


def test_connection():
    """Test GitLab API connection"""
    print("=" * 80)
    print("GitLab Connection Test")
    print("=" * 80)
    print()
    
    # Check environment variables
    print("1. Checking environment variables...")
    gitlab_url = os.getenv("GITLAB_URL", "https://gitlab.com")
    gitlab_token = os.getenv("GITLAB_TOKEN")
    project_id = os.getenv("GITLAB_PROJECT_ID", "76475459")
    
    print(f"   GITLAB_URL: {gitlab_url}")
    print(f"   GITLAB_PROJECT_ID: {project_id}")
    
    if gitlab_token:
        print(f"   GITLAB_TOKEN: {'*' * 20} (set)")
    else:
        print("   GITLAB_TOKEN: (not set)")
        print()
        print("❌ ERROR: GITLAB_TOKEN is not set!")
        print()
        print("To set your token:")
        print("1. Go to: https://gitlab.com/macar228228-group/workstation/-/settings/access_tokens")
        print("2. Create a new Project Access Token with scopes: api, read_api, write_repository")
        print("3. Run: setx GITLAB_TOKEN \"your_token_here\"")
        print("4. Restart your terminal/IDE")
        print()
        return False
    
    print()
    
    # Test connection
    print("2. Testing GitLab API connection...")
    try:
        api = GitLabAPI(
            private_token=gitlab_token,
            gitlab_url=gitlab_url
        )
        
        print("   ✓ GitLabAPI initialized")
        print()
        
        # Get project info
        print("3. Fetching project information...")
        project = api.get_project(project_id)
        
        print(f"   ✓ Project found!")
        print()
        print("   Project Details:")
        print(f"   - Name: {project.get('name')}")
        print(f"   - Path: {project.get('path_with_namespace')}")
        print(f"   - ID: {project.get('id')}")
        print(f"   - URL: {project.get('web_url')}")
        print(f"   - Visibility: {project.get('visibility')}")
        print(f"   - Default Branch: {project.get('default_branch')}")
        print(f"   - Stars: {project.get('star_count', 0)}")
        print(f"   - Forks: {project.get('forks_count', 0)}")
        print()
        
        # Test issue listing
        print("4. Testing issue listing...")
        issues = api.list_issues(project_id, state="all")
        print(f"   ✓ Found {len(issues)} recent issues")
        
        if issues:
            print()
            print("   Recent Issues:")
            for i, issue in enumerate(issues[:3], 1):
                print(f"   {i}. #{issue.get('iid')}: {issue.get('title')}")
                print(f"      State: {issue.get('state')}")
                print(f"      Labels: {', '.join(issue.get('labels', []))}")
                print()
        
        print("=" * 80)
        print("✅ SUCCESS: GitLab connection is working!")
        print("=" * 80)
        print()
        print("You can now:")
        print("1. Run security scans: python examples/scan_and_create_issues.py")
        print("2. Use orchestrator: python examples/orchestrator_example.py")
        print("3. Run integration tests: pytest tests/test_integration.py -v")
        print()
        
        return True
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
        print()
        print("=" * 80)
        print("❌ FAILED: Could not connect to GitLab")
        print("=" * 80)
        print()
        print("Possible issues:")
        print("1. Invalid token - check that it's correct")
        print("2. Token expired - create a new one")
        print("3. Insufficient permissions - token needs: api, read_api, write_repository")
        print("4. Wrong project ID - verify project ID is correct")
        print("5. Network issues - check internet connection")
        print()
        return False


def main():
    """Main function"""
    success = test_connection()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
