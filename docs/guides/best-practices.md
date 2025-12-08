# Best Practices Guide

Recommendations and guidelines for using Security Assistant effectively.

## Table of Contents

- [Configuration Best Practices](#configuration-best-practices)
- [Scanning Best Practices](#scanning-best-practices)
- [CI/CD Integration Best Practices](#cicd-integration-best-practices)
- [GitLab Integration Best Practices](#gitlab-integration-best-practices)
- [Performance Optimization](#performance-optimization)
- [Security Best Practices](#security-best-practices)
- [Team Workflows](#team-workflows)

## Configuration Best Practices

### Use Environment-Specific Configurations

Create separate configurations for different environments:

**Development** (`config/dev.yaml`):
```yaml
scanners:
  bandit:
    enabled: true
  semgrep:
    enabled: true
    config:
      rules: ["p/python"]  # Faster, Python-only
  trivy:
    enabled: false  # Skip in dev

orchestrator:
  deduplication_strategy: "fuzzy"
  max_workers: 4

thresholds:
  fail_on_critical: false  # Don't block development
  fail_on_high: false
```

**Staging** (`config/staging.yaml`):
```yaml
scanners:
  bandit:
    enabled: true
  semgrep:
    enabled: true
    config:
      rules: ["p/security-audit"]
  trivy:
    enabled: true

orchestrator:
  deduplication_strategy: "fuzzy"
  max_workers: 8

thresholds:
  fail_on_critical: true  # Block critical issues
  fail_on_high: false
```

**Production** (`config/prod.yaml`):
```yaml
scanners:
  bandit:
    enabled: true
  semgrep:
    enabled: true
    config:
      rules: ["p/default"]  # Comprehensive
  trivy:
    enabled: true

orchestrator:
  deduplication_strategy: "strict"  # No false deduplication
  max_workers: 16

thresholds:
  fail_on_critical: true
  fail_on_high: true
  fail_on_medium: true  # Strict for production

gitlab:
  create_issues: true
  priority_threshold: "high"
```

### Use Version Control for Configurations

**Commit configurations**:
```bash
git add config/*.yaml
git commit -m "Add environment-specific security configs"
```

**Use .gitignore for secrets**:
```gitignore
# .gitignore
config/local.yaml
config/*-secret.yaml
.env
```

### Leverage Environment Variables for Secrets

**Never commit tokens**:
```yaml
# config/prod.yaml - GOOD
gitlab:
  url: "https://gitlab.com"
  project_id: 12345
  # Token from environment: SA_GITLAB_TOKEN
```

```yaml
# config/prod.yaml - BAD
gitlab:
  token: "glpat-abc123..."  # Never do this!
```

**Use .env files locally**:
```bash
# .env (not committed)
SA_GITLAB_TOKEN=glpat-your-token
SA_GITLAB_PROJECT_ID=12345
```

## Scanning Best Practices

### Choose the Right Scanners for Your Stack

**Python projects**:
```yaml
scanners:
  bandit:
    enabled: true  # Python security
  semgrep:
    enabled: true  # Multi-language
    config:
      rules: ["p/python", "p/django", "p/flask"]
  trivy:
    enabled: true  # Dependencies
```

**JavaScript/TypeScript projects**:
```yaml
scanners:
  bandit:
    enabled: false  # Python only
  semgrep:
    enabled: true
    config:
      rules: ["p/javascript", "p/typescript", "p/react"]
  trivy:
    enabled: true
```

**Multi-language projects**:
```yaml
scanners:
  bandit:
    enabled: true
  semgrep:
    enabled: true
    config:
      rules: ["p/default"]  # All languages
  trivy:
    enabled: true
```

### Exclude Unnecessary Directories

**Always exclude**:
```yaml
scanners:
  bandit:
    config:
      exclude_dirs:
        - tests          # Test code
        - venv           # Virtual environment
        - .venv
        - node_modules   # Dependencies
        - .git           # Git metadata
        - __pycache__    # Python cache
        - build          # Build artifacts
        - dist
        - .tox
```

**Consider excluding**:
```yaml
scanners:
  bandit:
    config:
      exclude_dirs:
        - docs           # Documentation
        - examples       # Example code
        - migrations     # Database migrations
        - static         # Static files
```

### Use Appropriate Deduplication Strategy

**Strict** - When you need all findings:
```yaml
orchestrator:
  deduplication_strategy: "strict"
```
- Use for: Compliance audits, security reviews
- Pros: No false deduplication
- Cons: More findings to review

**Fuzzy** - Recommended for most cases:
```yaml
orchestrator:
  deduplication_strategy: "fuzzy"
```
- Use for: Regular scans, CI/CD
- Pros: Good balance
- Cons: May miss some edge cases

**Location-based** - For aggressive deduplication:
```yaml
orchestrator:
  deduplication_strategy: "location"
```
- Use for: Quick scans, development
- Pros: Fewest findings
- Cons: May over-deduplicate

### Handle False Positives Properly

**1. Inline suppression** (preferred for specific cases):
```python
# nosec B101 - Assert is safe in test context
assert user.is_authenticated
```

**2. Configuration exclusion** (for systematic false positives):
```yaml
scanners:
  bandit:
    config:
      skips:
        - B101  # assert_used - safe in tests
        - B404  # import_subprocess - needed for CLI
```

**3. Custom rules** (for complex cases):
```yaml
# .bandit
tests:
  - B101
  - B601
```

**Document suppressions**:
```python
# nosec B603 - subprocess.call is safe here because:
# 1. Input is validated against whitelist
# 2. Shell=False prevents injection
# 3. Timeout prevents DoS
subprocess.call([validated_command], timeout=5)
```

## CI/CD Integration Best Practices

### Use Different Scan Strategies for Different Triggers

**Pre-commit** (local):
```bash
# .git/hooks/pre-commit
#!/bin/bash
security-assistant scan . \
  --scanners bandit \
  --fail-on critical \
  --quick
```

**Pull/Merge Request**:
```yaml
# .gitlab-ci.yml
security-scan-mr:
  stage: test
  only:
    - merge_requests
  script:
    - security-assistant scan . \
        --format gitlab-sast,html \
        --fail-on high
  artifacts:
    reports:
      sast: gl-sast-report.json
    paths:
      - security_report.html
```

**Main branch**:
```yaml
security-scan-main:
  stage: security
  only:
    - main
  script:
    - security-assistant scan . \
        --format gitlab-sast,json \
        --create-issues \
        --fail-on critical
```

**Scheduled** (nightly):
```yaml
security-scan-scheduled:
  stage: security
  only:
    - schedules
  script:
    - security-assistant scan . \
        --format html,json,markdown \
        --create-issues \
        --fail-on medium
  artifacts:
    paths:
      - security-reports/
    expire_in: 30 days
```

### Cache Scanner Databases

**GitLab CI**:
```yaml
security-scan:
  cache:
    key: security-scanners
    paths:
      - .trivy-cache/
      - .semgrep-cache/
  before_script:
    - export TRIVY_CACHE_DIR=.trivy-cache
    - export SEMGREP_CACHE_DIR=.semgrep-cache
```

**GitHub Actions**:
```yaml
- uses: actions/cache@v3
  with:
    path: |
      ~/.cache/trivy
      ~/.cache/semgrep
    key: security-scanners-${{ runner.os }}-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      security-scanners-${{ runner.os }}-
```

### Use Artifacts Wisely

**Keep reports**:
```yaml
artifacts:
  paths:
    - security-reports/
  reports:
    sast: gl-sast-report.json
  expire_in: 30 days  # Balance storage vs. history
```

**Don't commit reports**:
```gitignore
# .gitignore
security-reports/
security_report.*
gl-sast-report.json
```

### Set Appropriate Failure Thresholds

**Development branches**:
```yaml
thresholds:
  fail_on_critical: true   # Block only critical
  fail_on_high: false      # Warn but don't block
```

**Release branches**:
```yaml
thresholds:
  fail_on_critical: true
  fail_on_high: true       # Block high and critical
  fail_on_medium: false
```

**Production deployments**:
```yaml
thresholds:
  fail_on_critical: true
  fail_on_high: true
  fail_on_medium: true     # Block all significant issues
```

## GitLab Integration Best Practices

### Use Priority Filtering

**Create issues only for actionable findings**:
```yaml
gitlab:
  create_issues: true
  priority_threshold: "high"  # Only high and critical
```

**Different thresholds for different projects**:
```yaml
# Critical infrastructure
gitlab:
  priority_threshold: "medium"

# Internal tools
gitlab:
  priority_threshold: "high"

# Experimental projects
gitlab:
  priority_threshold: "critical"
```

### Use Labels Effectively

**Categorize issues**:
```yaml
gitlab:
  issue_labels:
    - "security"
    - "automated"
    - "security-scan"
    - "{{ severity }}"  # critical, high, medium, low
    - "{{ scanner }}"   # bandit, semgrep, trivy
```

**Enable filtering**:
- View all security issues: `label:security`
- View automated issues: `label:automated`
- View critical issues: `label:critical`
- View Bandit findings: `label:bandit`

### Assign Issues Appropriately

**Security team**:
```yaml
gitlab:
  default_assignee_id: 12345  # Security team lead
```

**Component owners** (programmatically):
```python
from security_assistant.gitlab_api import GitLabAPI

# Map file paths to owners
OWNERS = {
    "src/auth/": 67890,      # Auth team
    "src/api/": 11111,       # API team
    "src/frontend/": 22222,  # Frontend team
}

def get_assignee(finding):
    for path, assignee_id in OWNERS.items():
        if finding.file_path.startswith(path):
            return assignee_id
    return DEFAULT_ASSIGNEE

api = GitLabAPI(token, project_id)
for finding in findings:
    api.create_issue(finding, assignee_ids=[get_assignee(finding)])
```

### Prevent Duplicate Issues

**Check existing issues**:
```python
from security_assistant.gitlab_api import GitLabAPI

api = GitLabAPI(token, project_id)
existing_issues = api.get_existing_issues(labels=["security-scan"])

# Filter findings
new_findings = [
    f for f in findings
    if not any(f.title in issue['title'] for issue in existing_issues)
]

# Create only new issues
for finding in new_findings:
    api.create_issue(finding)
```

**Use unique identifiers**:
```python
def create_issue_with_id(finding):
    # Add unique ID to description
    unique_id = hashlib.sha256(
        f"{finding.file_path}:{finding.line}:{finding.rule_id}".encode()
    ).hexdigest()[:8]
    
    description = f"""
    {finding.description}
    
    <!-- security-scan-id: {unique_id} -->
    """
    
    return api.create_issue(finding, description=description)
```

## Performance Optimization

### Optimize Parallel Execution

**Match CPU cores**:
```yaml
orchestrator:
  max_workers: 8  # For 8-core CPU
```

**Consider I/O vs. CPU**:
```yaml
# I/O-bound (network, disk)
orchestrator:
  max_workers: 16  # More than CPU cores

# CPU-bound (analysis)
orchestrator:
  max_workers: 8   # Match CPU cores
```

### Use Quick Scan Mode for Development

**Full scan** (CI/CD, scheduled):
```bash
security-assistant scan .
```

**Quick scan** (pre-commit, development):
```bash
security-assistant scan . \
  --scanners bandit \
  --quick \
  --fail-on critical
```

### Optimize Scanner Configuration

**Semgrep** - Use specific rules:
```yaml
scanners:
  semgrep:
    config:
      rules:
        - "p/python"        # Instead of p/default
        - "p/security-audit"
```

**Trivy** - Skip unnecessary scans:
```yaml
scanners:
  trivy:
    config:
      scanners:
        - vuln              # Only vulnerabilities
        # - config          # Skip config scanning
        # - secret          # Skip secret scanning
```

**Bandit** - Exclude tests:
```yaml
scanners:
  bandit:
    config:
      exclude_dirs:
        - tests
        - test_*.py
```

### Monitor Performance

**Enable timing**:
```bash
security-assistant scan . --verbose
```

Output:
```
[INFO] Bandit scan completed in 12.3s
[INFO] Semgrep scan completed in 45.6s
[INFO] Trivy scan completed in 23.1s
[INFO] Deduplication completed in 0.5s
[INFO] Total scan time: 81.5s
```

**Optimize bottlenecks**:
- Bandit slow? → Exclude more directories
- Semgrep slow? → Use specific rules
- Trivy slow? → Check network, use cache

## Security Best Practices

### Protect Sensitive Information

**Never commit tokens**:
```bash
# .gitignore
.env
.env.*
config/*-secret.yaml
*-token.txt
```

**Use environment variables**:
```bash
export SA_GITLAB_TOKEN="glpat-..."
export SA_GITLAB_PROJECT_ID="12345"
```

**Use CI/CD secrets**:
```yaml
# GitLab CI
security-scan:
  variables:
    SA_GITLAB_TOKEN: $GITLAB_TOKEN  # From CI/CD variables
```

### Limit Token Permissions

**Minimum required scopes**:
- `api` - For issue creation
- `read_api` - For read-only operations

**Avoid**:
- `sudo` - Never needed
- `admin_mode` - Never needed
- `write_repository` - Usually not needed

### Rotate Tokens Regularly

**Set expiration**:
- Development: 90 days
- Production: 30 days
- CI/CD: 365 days (with monitoring)

**Automate rotation**:
```bash
# Cron job to check token expiration
0 0 * * * check-token-expiration.sh
```

### Review Findings Before Creating Issues

**Manual review for sensitive projects**:
```bash
# Generate report first
security-assistant scan . --format html

# Review in browser
# Then create issues manually
security-assistant scan . --create-issues
```

**Automated for trusted pipelines**:
```yaml
# Only on main branch, scheduled
security-scan-scheduled:
  only:
    - schedules
  script:
    - security-assistant scan . --create-issues
```

## Team Workflows

### Establish Clear Ownership

**RACI matrix**:
- **Responsible**: Security team runs scans
- **Accountable**: Development teams fix issues
- **Consulted**: Security team for guidance
- **Informed**: Management via reports

**Document in README**:
```markdown
## Security Scanning

- **Scans run**: Every MR, nightly on main
- **Issue creation**: Automated for high/critical
- **Ownership**: Issues assigned to component owners
- **SLA**: Critical (24h), High (1 week), Medium (1 month)
```

### Create Remediation Workflow

**1. Issue created** (automated):
```yaml
gitlab:
  issue_labels:
    - "security"
    - "needs-triage"
```

**2. Triage** (security team):
- Review finding
- Confirm severity
- Add labels: `confirmed` or `false-positive`
- Assign to component owner

**3. Fix** (development team):
- Implement fix
- Add tests
- Update documentation
- Link MR to issue

**4. Verify** (security team):
- Review fix
- Re-scan
- Close issue

### Use Metrics for Improvement

**Track**:
- Time to fix (by severity)
- False positive rate
- Scan duration
- Issue backlog

**Report**:
```python
# Monthly security report
from security_assistant.gitlab_api import GitLabAPI

api = GitLabAPI(token, project_id)
issues = api.get_issues(labels=["security-scan"])

metrics = {
    "total_issues": len(issues),
    "open_issues": len([i for i in issues if i['state'] == 'opened']),
    "critical": len([i for i in issues if 'critical' in i['labels']]),
    "high": len([i for i in issues if 'high' in i['labels']]),
    "avg_time_to_close": calculate_avg_time(issues),
}
```

### Continuous Improvement

**Regular reviews**:
- Weekly: Review new findings
- Monthly: Review false positives, update rules
- Quarterly: Review scanner configuration
- Annually: Review overall security posture

**Feedback loop**:
```yaml
# Document false positives
scanners:
  bandit:
    config:
      skips:
        - B101  # Added 2024-01: Assert safe in tests
        - B404  # Added 2024-02: Subprocess needed for CLI
```

## Summary

**Key takeaways**:
1. ✅ Use environment-specific configurations
2. ✅ Choose appropriate scanners for your stack
3. ✅ Exclude unnecessary directories
4. ✅ Use different scan strategies for different triggers
5. ✅ Cache scanner databases in CI/CD
6. ✅ Set appropriate failure thresholds
7. ✅ Use GitLab labels and assignments effectively
8. ✅ Protect sensitive information
9. ✅ Establish clear ownership and workflows
10. ✅ Monitor and improve continuously

**Next steps**:
- Review your current configuration
- Implement environment-specific configs
- Set up CI/CD integration
- Establish team workflows
- Monitor and iterate
