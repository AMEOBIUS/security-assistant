# GitLab Integration Setup Guide

This guide will help you set up GitLab integration for the Security Assistant.

## Prerequisites

- GitLab account with access to `macar228228-group/workstation` project
- Python 3.8+ installed
- Security Assistant installed (`pip install -r requirements.txt`)

## Step 1: Create GitLab Access Token

1. **Go to Project Settings**
   - Navigate to: https://gitlab.com/macar228228-group/workstation/-/settings/access_tokens
   - Or: Project → Settings → Access Tokens

2. **Create New Token**
   - Token name: `Security Assistant`
   - Expiration date: Choose appropriate date (e.g., 1 year)
   - Select scopes:
     - ✅ `api` - Full API access
     - ✅ `read_api` - Read API access
     - ✅ `write_repository` - Write to repository
   - Click "Create project access token"

3. **Copy Token**
   - ⚠️ **IMPORTANT:** Copy the token immediately - you won't see it again!
   - Save it securely (e.g., password manager)

## Step 2: Set Environment Variables

### Windows (Command Prompt)

```cmd
# Set GitLab token (replace with your actual token)
setx GITLAB_TOKEN "glpat-xxxxxxxxxxxxxxxxxxxx"

# Set GitLab URL
setx GITLAB_URL "https://gitlab.com"

# Set Project ID
setx GITLAB_PROJECT_ID "76475459"

# Set Test Project
setx GITLAB_TEST_PROJECT "macar228228-group/workstation"
```

### Windows (PowerShell)

```powershell
# Set GitLab token (replace with your actual token)
[System.Environment]::SetEnvironmentVariable('GITLAB_TOKEN', 'glpat-xxxxxxxxxxxxxxxxxxxx', 'User')

# Set GitLab URL
[System.Environment]::SetEnvironmentVariable('GITLAB_URL', 'https://gitlab.com', 'User')

# Set Project ID
[System.Environment]::SetEnvironmentVariable('GITLAB_PROJECT_ID', '76475459', 'User')

# Set Test Project
[System.Environment]::SetEnvironmentVariable('GITLAB_TEST_PROJECT', 'macar228228-group/workstation', 'User')
```

### Linux/macOS

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export GITLAB_TOKEN="glpat-xxxxxxxxxxxxxxxxxxxx"
export GITLAB_URL="https://gitlab.com"
export GITLAB_PROJECT_ID="76475459"
export GITLAB_TEST_PROJECT="macar228228-group/workstation"
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

## Step 3: Restart Terminal/IDE

⚠️ **IMPORTANT:** After setting environment variables, you must:
1. Close all terminal windows
2. Close VS Code / your IDE
3. Reopen them

This ensures the new environment variables are loaded.

## Step 4: Test Connection

Run the connection test script:

```bash
python examples/test_gitlab_connection.py
```

**Expected output:**
```
========================================
GitLab Connection Test
========================================

1. Checking environment variables...
   GITLAB_URL: https://gitlab.com
   GITLAB_PROJECT_ID: 76475459
   GITLAB_TOKEN: ******************** (set)

2. Testing GitLab API connection...
   ✓ GitLabAPI initialized

3. Fetching project information...
   ✓ Project found!

   Project Details:
   - Name: Workstation
   - Path: macar228228-group/workstation
   - ID: 76475459
   - URL: https://gitlab.com/macar228228-group/workstation
   - Visibility: private
   - Default Branch: main

4. Testing issue listing...
   ✓ Found 5 recent issues

========================================
✅ SUCCESS: GitLab connection is working!
========================================
```

## Step 5: Run Integration Tests

Once connection is working, run integration tests:

```bash
# Run all integration tests
pytest tests/test_integration.py -v

# Run specific integration test
pytest tests/test_integration.py::TestGitLabAPIIntegration::test_get_project_info -v
```

## Troubleshooting

### Error: "GITLAB_TOKEN is not set"

**Solution:**
1. Verify you ran `setx GITLAB_TOKEN "your_token"`
2. Restart terminal/IDE
3. Check with: `echo %GITLAB_TOKEN%` (Windows) or `echo $GITLAB_TOKEN` (Linux/macOS)

### Error: "401 Unauthorized"

**Possible causes:**
1. Invalid token - check you copied it correctly
2. Token expired - create a new one
3. Token doesn't have required scopes - recreate with api, read_api, write_repository

**Solution:**
1. Go to https://gitlab.com/macar228228-group/workstation/-/settings/access_tokens
2. Revoke old token
3. Create new token with correct scopes
4. Update environment variable: `setx GITLAB_TOKEN "new_token"`
5. Restart terminal/IDE

### Error: "404 Not Found"

**Possible causes:**
1. Wrong project ID
2. No access to project

**Solution:**
1. Verify project ID: https://gitlab.com/macar228228-group/workstation
2. Check you have access to the project
3. Update project ID: `setx GITLAB_PROJECT_ID "76475459"`

### Error: "403 Forbidden"

**Possible causes:**
1. Token doesn't have required permissions
2. Project settings restrict API access

**Solution:**
1. Recreate token with scopes: api, read_api, write_repository
2. Check project settings allow API access

### Error: "Connection timeout"

**Possible causes:**
1. Network issues
2. Firewall blocking GitLab
3. Proxy configuration needed

**Solution:**
1. Check internet connection
2. Try accessing https://gitlab.com in browser
3. Configure proxy if needed

## Quick Setup Script

For convenience, run the setup script:

```bash
# Windows
scripts\setup_gitlab.bat

# Linux/macOS
chmod +x scripts/setup_gitlab.sh
./scripts/setup_gitlab.sh
```

## Security Best Practices

1. **Never commit tokens to Git**
   - `.env` is in `.gitignore`
   - Use environment variables only

2. **Use Project Access Tokens**
   - Not Personal Access Tokens
   - Scoped to specific project
   - Can be revoked easily

3. **Set expiration dates**
   - Tokens should expire
   - Rotate regularly (e.g., every 6-12 months)

4. **Minimal permissions**
   - Only grant required scopes
   - api, read_api, write_repository

5. **Revoke unused tokens**
   - Regularly audit tokens
   - Revoke old/unused ones

## Next Steps

Once GitLab integration is working:

1. **Run security scans:**
   ```bash
   python examples/scan_and_create_issues.py --directory src/ --min-severity HIGH
   ```

2. **Use orchestrator:**
   ```bash
   python examples/orchestrator_example.py
   ```

3. **Run full test suite:**
   ```bash
   pytest tests/ -v
   ```

4. **Create custom workflows:**
   - See `examples/` directory for more examples
   - Check `docs/` for detailed guides

## Support

If you encounter issues:

1. Check this troubleshooting guide
2. Review error messages carefully
3. Test connection with `test_gitlab_connection.py`
4. Check GitLab project settings
5. Verify token permissions

## References

- [GitLab API Documentation](https://docs.gitlab.com/ee/api/)
- [Project Access Tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)
- [API Scopes](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#personal-access-token-scopes)
