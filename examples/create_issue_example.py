"""
Example: Create a security issue in GitLab
Demonstrates basic usage of GitLab API integration.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from security_assistant.gitlab_api import GitLabAPI, IssueData

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


def main():
    """Create a sample security issue."""
    
    # Load .env file explicitly
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment from {env_path}")
    
    # Check for required environment variables
    if not os.getenv("GITLAB_TOKEN"):
        print("Error: GITLAB_TOKEN environment variable not set")
        print("Please set your GitLab personal access token:")
        print("  PowerShell: $env:GITLAB_TOKEN='your-token-here'")
        print("  CMD: set GITLAB_TOKEN=your-token-here")
        print("  Or add to .env file: GITLAB_TOKEN=your-token-here")
        return
    
    project_id = os.getenv("GITLAB_TEST_PROJECT", "macar228228-group/Workstation")
    
    print(f"Creating security issue in project: {project_id}")
    print("-" * 60)
    
    # Initialize API client
    with GitLabAPI() as api:
        # Verify project access
        try:
            project = api.get_project(project_id)
            print(f"✅ Project found: {project['name']}")
            print(f"   URL: {project['web_url']}")
        except Exception as e:
            print(f"❌ Error accessing project: {e}")
            return
        
        # Create issue data
        issue_data = IssueData(
            title="Security: Example SQL Injection Vulnerability",
            description="""
## Vulnerability Details

**Severity:** High  
**Type:** SQL Injection  
**File:** `app/database/queries.py`  
**Line:** 42

### Description
User input is directly concatenated into SQL query without sanitization.

### Vulnerable Code
```python
query = f"SELECT * FROM users WHERE username = '{user_input}'"
cursor.execute(query)
```

### Recommendation
Use parameterized queries:
```python
query = "SELECT * FROM users WHERE username = %s"
cursor.execute(query, (user_input,))
```

### References
- [OWASP SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [CWE-89](https://cwe.mitre.org/data/definitions/89.html)

---
*This issue was created automatically by Security Assistant*
            """.strip(),
            labels=["security", "vulnerability", "high-priority"],
            confidential=True
        )
        
        # Create the issue
        try:
            result = api.create_issue(project_id, issue_data)
            print(f"\n✅ Issue created successfully!")
            print(f"   Issue #: {result['iid']}")
            print(f"   URL: {result['web_url']}")
            print(f"   ID: {result['id']}")
        except Exception as e:
            print(f"\n❌ Error creating issue: {e}")


if __name__ == "__main__":
    main()
