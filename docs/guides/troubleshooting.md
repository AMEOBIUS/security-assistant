# Troubleshooting Guide

Common issues and solutions for Security Assistant.

## Table of Contents

- [Installation Issues](#installation-issues)
- [Scanner Issues](#scanner-issues)
- [Configuration Issues](#configuration-issues)
- [GitLab Integration Issues](#gitlab-integration-issues)
- [CI/CD Issues](#cicd-issues)
- [Performance Issues](#performance-issues)
- [Report Generation Issues](#report-generation-issues)

## Installation Issues

### Issue: `pip install` fails with dependency conflicts

**Symptoms**:
```
ERROR: Cannot install security-assistant because these package versions have conflicts
```

**Solutions**:

1. **Use virtual environment**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -e .
```

2. **Upgrade pip**:
```bash
python -m pip install --upgrade pip
pip install -e .
```

3. **Install without dependencies, then manually**:
```bash
pip install --no-deps -e .
pip install -r requirements.txt
```

### Issue: `ModuleNotFoundError: No module named 'yaml'`

**Symptoms**:
```
ModuleNotFoundError: No module named 'yaml'
```

**Solution**:
```bash
pip install pyyaml
```

Or install with YAML support:
```bash
pip install -e ".[yaml]"
```

### Issue: Scanner binaries not found

**Symptoms**:
```
[ERROR] Bandit not found. Please install: pip install bandit
[ERROR] Semgrep not found. Please install: pip install semgrep
[ERROR] Trivy not found. Please install from: https://trivy.dev
```

**Solutions**:

1. **Install all scanners at once**:
```bash
pip install -e ".[scanners]"
```

2. **Install individually**:
```bash
# Bandit
pip install bandit

# Semgrep
pip install semgrep

# Trivy (Linux)
wget https://github.com/aquasecurity/trivy/releases/download/v0.48.0/trivy_0.48.0_Linux-64bit.tar.gz
tar zxvf trivy_0.48.0_Linux-64bit.tar.gz
sudo mv trivy /usr/local/bin/

# Trivy (macOS)
brew install trivy

# Trivy (Windows)
# Download from https://github.com/aquasecurity/trivy/releases
```

## Scanner Issues

### Issue: Bandit finds too many false positives

**Symptoms**:
```
[HIGH] B101: Test for use of assert
[MEDIUM] B404: Consider possible security implications
```

**Solutions**:

1. **Configure Bandit exclusions**:
```yaml
# security-assistant.yaml
scanners:
  bandit:
    enabled: true
    config:
      exclude_dirs:
        - tests
        - venv
      skips:
        - B101  # assert_used
        - B404  # import_subprocess
```

2. **Use .bandit file**:
```yaml
# .bandit
exclude_dirs:
  - /tests/
  - /venv/
skips:
  - B101
  - B404
```

3. **Inline comments**:
```python
# nosec B101
assert user.is_authenticated
```

### Issue: Semgrep is too slow

**Symptoms**:
```
[INFO] Semgrep scanning... (running for 10+ minutes)
```

**Solutions**:

1. **Reduce ruleset**:
```yaml
scanners:
  semgrep:
    enabled: true
    config:
      rules:
        - "p/security-audit"  # Instead of "p/default"
```

2. **Exclude directories**:
```yaml
scanners:
  semgrep:
    config:
      exclude:
        - "tests/"
        - "node_modules/"
        - "venv/"
```

3. **Use specific rules**:
```bash
security-assistant scan . --semgrep-rules "p/python"
```

### Issue: Trivy fails with network errors

**Symptoms**:
```
[ERROR] Trivy failed: failed to download vulnerability DB
```

**Solutions**:

1. **Update Trivy DB manually**:
```bash
trivy image --download-db-only
```

2. **Use offline mode** (if DB already downloaded):
```yaml
scanners:
  trivy:
    config:
      offline: true
```

3. **Configure proxy**:
```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

4. **Increase timeout**:
```yaml
scanners:
  trivy:
    config:
      timeout: 600  # 10 minutes
```

## Configuration Issues

### Issue: Configuration file not found

**Symptoms**:
```
[WARNING] Configuration file not found: security-assistant.yaml
[INFO] Using default configuration
```

**Solutions**:

1. **Specify config file explicitly**:
```bash
security-assistant scan . --config /path/to/config.yaml
```

2. **Use default locations**:
- `./security-assistant.yaml`
- `./config/security-assistant.yaml`
- `~/.security-assistant.yaml`

3. **Check file permissions**:
```bash
ls -la security-assistant.yaml
chmod 644 security-assistant.yaml
```

### Issue: Environment variables not working

**Symptoms**:
```
# Set SA_BANDIT_ENABLED=false but Bandit still runs
```

**Solutions**:

1. **Check variable name** (must use `SA_` prefix):
```bash
# Wrong
export BANDIT_ENABLED=false

# Correct
export SA_BANDIT_ENABLED=false
```

2. **Check value format**:
```bash
# Boolean values
export SA_BANDIT_ENABLED=true   # or false

# Lists (comma-separated)
export SA_REPORT_FORMATS=html,json,markdown

# Numbers
export SA_MAX_WORKERS=4
```

3. **Verify environment**:
```bash
env | grep SA_
```

### Issue: YAML parsing errors

**Symptoms**:
```
yaml.scanner.ScannerError: mapping values are not allowed here
```

**Solutions**:

1. **Check indentation** (use spaces, not tabs):
```yaml
# Wrong
scanners:
	bandit:
		enabled: true

# Correct
scanners:
  bandit:
    enabled: true
```

2. **Quote special characters**:
```yaml
# Wrong
gitlab:
  token: abc123!@#

# Correct
gitlab:
  token: "abc123!@#"
```

3. **Validate YAML**:
```bash
python -c "import yaml; yaml.safe_load(open('security-assistant.yaml'))"
```

## GitLab Integration Issues

### Issue: GitLab API authentication fails

**Symptoms**:
```
[ERROR] GitLab API error: 401 Unauthorized
```

**Solutions**:

1. **Check token**:
```bash
# Verify token is set
echo $SA_GITLAB_TOKEN

# Test token
curl --header "PRIVATE-TOKEN: $SA_GITLAB_TOKEN" \
  "https://gitlab.com/api/v4/user"
```

2. **Check token permissions**:
- Token needs `api` scope
- User must have Developer role or higher

3. **Regenerate token**:
- GitLab → Settings → Access Tokens
- Create new token with `api` scope

### Issue: Issues not being created

**Symptoms**:
```
[INFO] Found 10 findings
[INFO] No issues created
```

**Solutions**:

1. **Check priority threshold**:
```bash
# Only creates issues for critical findings
export SA_PRIORITY_THRESHOLD=critical

# Create for high and critical
export SA_PRIORITY_THRESHOLD=high
```

2. **Enable issue creation**:
```bash
export SA_GITLAB_CREATE_ISSUES=true
security-assistant scan . --create-issues
```

3. **Check project ID**:
```bash
# Get project ID
curl --header "PRIVATE-TOKEN: $SA_GITLAB_TOKEN" \
  "https://gitlab.com/api/v4/projects/namespace%2Fproject"

# Set correct ID
export SA_GITLAB_PROJECT_ID=12345
```

### Issue: Duplicate issues created

**Symptoms**:
```
Multiple GitLab issues for the same vulnerability
```

**Solutions**:

1. **Use stricter deduplication**:
```yaml
orchestrator:
  deduplication_strategy: "strict"
```

2. **Check existing issues** before creating:
```python
from security_assistant.gitlab_api import GitLabAPI

api = GitLabAPI(token, project_id)
existing = api.get_existing_issues()
# Filter findings against existing
```

3. **Use labels to track**:
```yaml
gitlab:
  issue_labels:
    - "security-scan"
    - "automated"
```

## CI/CD Issues

### Issue: GitLab CI job fails with "command not found"

**Symptoms**:
```
security-assistant: command not found
```

**Solutions**:

1. **Install in CI job**:
```yaml
security-scan:
  before_script:
    - pip install -e ".[scanners]"
  script:
    - security-assistant scan .
```

2. **Use correct image**:
```yaml
security-scan:
  image: python:3.11
  # ... rest of job
```

3. **Check PATH**:
```yaml
security-scan:
  script:
    - export PATH=$PATH:~/.local/bin
    - security-assistant scan .
```

### Issue: GitHub Actions SARIF upload fails

**Symptoms**:
```
Error: SARIF file not found
```

**Solutions**:

1. **Check file path**:
```yaml
- name: Upload SARIF
  uses: github/codeql-action/upload-sarif@v2
  with:
    sarif_file: security-report.sarif  # Must match output
```

2. **Ensure file is generated**:
```yaml
- name: Run scan
  run: |
    security-assistant scan . --format sarif
    ls -la security-report.sarif  # Verify file exists
```

3. **Check permissions**:
```yaml
permissions:
  security-events: write  # Required for SARIF upload
```

### Issue: Jenkins pipeline fails to publish HTML

**Symptoms**:
```
ERROR: No HTML reports found
```

**Solutions**:

1. **Check report path**:
```groovy
publishHTML([
    reportDir: 'security-reports',  // Must match output_dir
    reportFiles: 'security_report.html',
    reportName: 'Security Report'
])
```

2. **Ensure directory exists**:
```groovy
sh '''
    security-assistant scan . --format html
    ls -la security-reports/
'''
```

3. **Install HTML Publisher plugin**:
- Jenkins → Manage Plugins → Available
- Search "HTML Publisher"
- Install and restart

## Performance Issues

### Issue: Scan takes too long

**Symptoms**:
```
Scan running for 30+ minutes
```

**Solutions**:

1. **Increase parallel workers**:
```yaml
orchestrator:
  max_workers: 8  # Default is 4
```

2. **Disable slow scanners**:
```bash
# Only run fast scanners
export SA_TRIVY_ENABLED=false
security-assistant scan .
```

3. **Exclude large directories**:
```yaml
scanners:
  bandit:
    config:
      exclude_dirs:
        - node_modules
        - venv
        - .git
```

4. **Use quick scan mode**:
```bash
security-assistant scan . --quick
```

### Issue: High memory usage

**Symptoms**:
```
MemoryError: Unable to allocate array
```

**Solutions**:

1. **Reduce parallel workers**:
```yaml
orchestrator:
  max_workers: 2
```

2. **Scan in batches**:
```bash
# Scan subdirectories separately
security-assistant scan ./src
security-assistant scan ./tests
```

3. **Increase system memory**:
```yaml
# GitLab CI
security-scan:
  tags:
    - high-memory  # Use runner with more RAM
```

## Report Generation Issues

### Issue: HTML report not opening

**Symptoms**:
```
File generated but browser shows blank page
```

**Solutions**:

1. **Check file size**:
```bash
ls -lh security_report.html
# If 0 bytes, generation failed
```

2. **Check for errors**:
```bash
security-assistant scan . --format html --verbose
```

3. **Try different format**:
```bash
# Generate JSON first to verify data
security-assistant scan . --format json
cat security_report.json
```

### Issue: SARIF validation fails

**Symptoms**:
```
ERROR: Invalid SARIF format
```

**Solutions**:

1. **Validate SARIF**:
```bash
# Install validator
npm install -g @microsoft/sarif-multitool

# Validate
sarif-multitool validate security-report.sarif
```

2. **Check SARIF version**:
```python
# Ensure using SARIF 2.1.0
import json
with open('security-report.sarif') as f:
    data = json.load(f)
    print(data['version'])  # Should be "2.1.0"
```

3. **Regenerate report**:
```bash
rm security-report.sarif
security-assistant scan . --format sarif
```

## Debug Mode

Enable verbose logging for troubleshooting:

```bash
# CLI
security-assistant scan . --verbose

# Environment variable
export SA_LOG_LEVEL=DEBUG
security-assistant scan .

# Configuration file
```yaml
logging:
  level: DEBUG
  file: security-assistant.log
```

Check logs:
```bash
tail -f security-assistant.log
```

## Getting Help

If issues persist:

1. **Check logs**:
```bash
cat security-assistant.log
```

2. **Run with debug mode**:
```bash
security-assistant scan . --verbose --log-file debug.log
```

3. **Collect system info**:
```bash
python --version
pip list | grep -E "(bandit|semgrep|trivy|security-assistant)"
uname -a  # Linux/Mac
systeminfo  # Windows
```

4. **Open GitHub issue** with:
- Error message
- Debug logs
- System information
- Configuration file (sanitized)

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` | Missing dependency | `pip install <module>` |
| `FileNotFoundError` | Scanner not installed | Install scanner |
| `PermissionError` | Insufficient permissions | Check file/directory permissions |
| `ConnectionError` | Network issue | Check internet connection |
| `TimeoutError` | Scanner timeout | Increase timeout in config |
| `JSONDecodeError` | Invalid JSON | Check JSON syntax |
| `YAMLError` | Invalid YAML | Check YAML syntax |
| `GitLabAPIError` | GitLab API issue | Check token and permissions |

## Quick Fixes

**Reset to defaults**:
```bash
rm security-assistant.yaml
rm -rf ~/.security-assistant/
security-assistant scan . --config /dev/null
```

**Clear cache**:
```bash
rm -rf ~/.cache/security-assistant/
trivy image --clear-cache
```

**Reinstall**:
```bash
pip uninstall security-assistant
pip install -e ".[scanners]"
```

**Verify installation**:
```bash
security-assistant --version
security-assistant config show
```
