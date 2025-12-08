# Frequently Asked Questions (FAQ)

Quick answers to common questions about Security Assistant.

## General Questions

### What is Security Assistant?

Security Assistant is a security scanning orchestrator that integrates multiple security tools (Bandit, Semgrep, Trivy) with intelligent deduplication, GitLab issue management, and CI/CD integration.

### Why use Security Assistant instead of running scanners directly?

**Benefits**:
- **Unified interface**: One command for multiple scanners
- **Deduplication**: Eliminates duplicate findings across scanners
- **Prioritization**: Intelligent severity mapping
- **GitLab integration**: Automatic issue creation
- **Multiple formats**: HTML, JSON, Markdown, SARIF, GitLab SAST
- **CI/CD ready**: Templates for GitLab CI, GitHub Actions, Jenkins

### Which scanners are supported?

Currently supported:
- **Bandit**: Python security scanner
- **Semgrep**: Multi-language static analysis
- **Trivy**: Vulnerability and misconfiguration scanner

### What languages are supported?

- **Python**: Bandit, Semgrep, Trivy
- **JavaScript/TypeScript**: Semgrep, Trivy
- **Go**: Semgrep, Trivy
- **Java**: Semgrep, Trivy
- **Ruby**: Semgrep, Trivy
- **PHP**: Semgrep, Trivy
- **C/C++**: Semgrep
- **And more**: See [Semgrep docs](https://semgrep.dev/docs/supported-languages/)

### Is Security Assistant free?

Yes, Security Assistant is open source (MIT License). However:
- **Bandit**: Free and open source
- **Semgrep**: Free tier available, paid for advanced features
- **Trivy**: Free and open source

## Installation

### What are the system requirements?

**Minimum**:
- Python 3.8+
- 2 GB RAM
- 1 GB disk space

**Recommended**:
- Python 3.11+
- 4 GB RAM
- 2 GB disk space

### Do I need to install all scanners?

No. You can:
- Install only the scanners you need
- Disable scanners in configuration
- Use `--scanners` flag to select specific scanners

Example:
```bash
# Only Bandit
pip install bandit
security-assistant scan . --scanners bandit
```

### Can I use Security Assistant without GitLab?

Yes. GitLab integration is optional. You can:
- Run scans locally
- Generate reports (HTML, JSON, Markdown)
- Use in CI/CD without GitLab

### How do I update Security Assistant?

```bash
# From source
cd security-assistant
git pull
pip install -e ".[scanners]"

# From PyPI (when available)
pip install --upgrade security-assistant
```

## Configuration

### Where should I put the configuration file?

Security Assistant looks for configuration in this order:
1. Path specified with `--config` flag
2. `./security-assistant.yaml`
3. `./config/security-assistant.yaml`
4. `~/.security-assistant.yaml`
5. Environment variables
6. Default values

### Can I use JSON instead of YAML?

Yes. Both formats are supported:
```bash
# YAML
security-assistant scan . --config config.yaml

# JSON
security-assistant scan . --config config.json
```

### How do environment variables work?

Environment variables override configuration file values:

```bash
# Disable Bandit
export SA_BANDIT_ENABLED=false

# Set output directory
export SA_OUTPUT_DIR=/tmp/reports

# Multiple formats
export SA_REPORT_FORMATS=html,json,markdown
```

All variables use `SA_` prefix. See [Environment Variables](environment-variables.md).

### Can I use multiple configuration files?

Not directly, but you can:
1. **Merge configurations programmatically**:
```python
from security_assistant.config import SecurityAssistantConfig

config1 = SecurityAssistantConfig.from_file("base.yaml")
config2 = SecurityAssistantConfig.from_file("override.yaml")
merged = config1.merge(config2)
```

2. **Use environment variables** to override specific values

## Scanning

### How long does a scan take?

Depends on:
- **Project size**: 1,000 files ≈ 2-5 minutes
- **Scanners enabled**: All 3 ≈ 5 minutes, Bandit only ≈ 1 minute
- **System resources**: More CPU/RAM = faster

**Typical times**:
- Small project (< 1,000 files): 1-2 minutes
- Medium project (1,000-10,000 files): 5-10 minutes
- Large project (> 10,000 files): 15-30 minutes

### Can I scan specific files or directories?

Yes:
```bash
# Specific directory
security-assistant scan ./src

# Multiple directories
security-assistant scan ./src ./tests

# Specific file
security-assistant scan ./src/app.py
```

### How do I exclude files or directories?

**Configuration file**:
```yaml
scanners:
  bandit:
    config:
      exclude_dirs:
        - tests
        - venv
        - node_modules
```

**Bandit .bandit file**:
```yaml
exclude_dirs:
  - /tests/
  - /venv/
```

**Semgrep .semgrepignore**:
```
tests/
venv/
node_modules/
```

### What is deduplication and which strategy should I use?

**Deduplication** removes duplicate findings from multiple scanners.

**Strategies**:
1. **Strict**: Exact match (file, line, message)
   - Use for: Precise deduplication
   - Pros: No false deduplication
   - Cons: May keep similar findings

2. **Fuzzy**: Similar message and location
   - Use for: General purpose (recommended)
   - Pros: Good balance
   - Cons: May over-deduplicate

3. **Location-based**: Same file and line
   - Use for: Aggressive deduplication
   - Pros: Fewest findings
   - Cons: May lose important details

**Recommendation**: Start with `fuzzy`, adjust if needed.

### How do I fail CI/CD builds on findings?

```bash
# Fail on critical findings
security-assistant scan . --fail-on critical

# Fail on high or critical
security-assistant scan . --fail-on high

# Fail on any findings
security-assistant scan . --fail-on medium
```

**Exit codes**:
- `0`: Success (no findings above threshold)
- `1`: Findings found above threshold
- `2`: Error during scan

## Reports

### Which report format should I use?

**Use case → Format**:
- **Human review**: HTML (interactive, visual)
- **CI/CD integration**: SARIF (GitHub), GitLab SAST (GitLab)
- **Automation**: JSON (machine-readable)
- **Documentation**: Markdown (readable, versionable)

**Multiple formats**:
```bash
security-assistant scan . --format html,json,markdown
```

### Where are reports saved?

Default: `./security-reports/`

**Change location**:
```bash
# CLI
security-assistant scan . --output-dir /tmp/reports

# Environment variable
export SA_OUTPUT_DIR=/tmp/reports

# Configuration
```yaml
report:
  output_dir: /tmp/reports
```

### Can I customize HTML reports?

Not directly, but you can:
1. **Use JSON output** and create custom HTML:
```python
import json
from jinja2 import Template

with open('security_report.json') as f:
    data = json.load(f)

template = Template(open('custom_template.html').read())
html = template.render(findings=data['findings'])
```

2. **Modify report generator** in `security_assistant/report_generator.py`

### How do I share reports?

**Options**:
1. **CI/CD artifacts**:
```yaml
# GitLab CI
artifacts:
  paths:
    - security-reports/
  expire_in: 30 days
```

2. **Upload to storage**:
```bash
# S3
aws s3 cp security_report.html s3://bucket/reports/

# GitLab Pages
mv security_report.html public/index.html
```

3. **Email**:
```bash
# Using mail command
mail -s "Security Report" team@example.com < security_report.html
```

## GitLab Integration

### Do I need a GitLab token?

Only if you want to:
- Create GitLab issues automatically
- Use GitLab API features

For local scanning and reports, no token needed.

### What permissions does the token need?

**Minimum**:
- `api` scope
- Developer role on project

**Recommended**:
- `api` scope
- Maintainer role (for issue management)

### How do I prevent duplicate issues?

Security Assistant checks for existing issues by:
1. **Title matching**: Same vulnerability title
2. **Label matching**: Issues with `security-scan` label
3. **Status**: Only open issues

**Additional prevention**:
```yaml
gitlab:
  issue_labels:
    - security-scan
    - automated
  check_existing: true
```

### Can I customize issue templates?

Yes, modify `security_assistant/gitlab_api.py`:

```python
def create_issue(self, finding):
    return {
        'title': f'[SECURITY] {finding.title}',
        'description': self._format_description(finding),
        'labels': ['security', 'automated', finding.severity.lower()],
        'assignee_ids': [self.default_assignee_id],
        'confidential': finding.severity == 'CRITICAL'
    }
```

### How do I assign issues to specific users?

```yaml
gitlab:
  default_assignee_id: 12345  # User ID
```

Or programmatically:
```python
from security_assistant.gitlab_api import GitLabAPI

api = GitLabAPI(token, project_id)
api.create_issue(finding, assignee_ids=[12345, 67890])
```

## CI/CD Integration

### Which CI/CD platforms are supported?

**Officially supported**:
- GitLab CI/CD
- GitHub Actions
- Jenkins

**Community support**:
- CircleCI
- Travis CI
- Azure Pipelines
- Bitbucket Pipelines

### How do I integrate with GitLab CI?

Copy `.gitlab-ci.yml` template:
```yaml
include:
  - local: .gitlab-ci.yml

security-scan:
  stage: test
  script:
    - security-assistant scan . --format gitlab-sast
  artifacts:
    reports:
      sast: gl-sast-report.json
```

See [CI/CD Integration Guide](cicd-integration.md).

### How do I integrate with GitHub Actions?

Copy `.github/workflows/security-scan.yml` template:
```yaml
name: Security Scan
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install -e ".[scanners]"
      - run: security-assistant scan . --format sarif
      - uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: security-report.sarif
```

### Can I run scans on schedule?

**GitLab CI**:
```yaml
security-scan-scheduled:
  only:
    - schedules
  script:
    - security-assistant scan . --create-issues
```

**GitHub Actions**:
```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
```

**Jenkins**:
```groovy
triggers {
    cron('0 2 * * *')
}
```

### How do I cache scanner databases?

**GitLab CI**:
```yaml
security-scan:
  cache:
    paths:
      - .trivy-cache/
  before_script:
    - export TRIVY_CACHE_DIR=.trivy-cache
```

**GitHub Actions**:
```yaml
- uses: actions/cache@v3
  with:
    path: ~/.cache/trivy
    key: trivy-db-${{ github.run_id }}
    restore-keys: trivy-db-
```

## Performance

### How can I speed up scans?

1. **Increase parallel workers**:
```yaml
orchestrator:
  max_workers: 8
```

2. **Disable slow scanners**:
```bash
export SA_TRIVY_ENABLED=false
```

3. **Exclude unnecessary directories**:
```yaml
scanners:
  bandit:
    config:
      exclude_dirs: [tests, venv, node_modules]
```

4. **Use quick scan mode**:
```bash
security-assistant scan . --quick
```

### Why is Semgrep slow?

Semgrep can be slow on large codebases. Solutions:
1. **Reduce ruleset**: Use specific rules instead of `p/default`
2. **Exclude directories**: Skip tests, dependencies
3. **Use cache**: Semgrep caches results
4. **Increase timeout**: Allow more time for large projects

### How much memory does Security Assistant use?

**Typical usage**:
- Small project: 200-500 MB
- Medium project: 500 MB - 1 GB
- Large project: 1-2 GB

**Peak usage** (all scanners running):
- Small project: 500 MB - 1 GB
- Medium project: 1-2 GB
- Large project: 2-4 GB

## Troubleshooting

### Where can I find logs?

**Default locations**:
- Console output (stdout/stderr)
- `security-assistant.log` (if configured)

**Enable logging**:
```bash
security-assistant scan . --verbose --log-file debug.log
```

### How do I report a bug?

1. **Check existing issues**: [GitHub Issues](https://github.com/yourusername/security-assistant/issues)
2. **Collect information**:
   - Error message
   - Debug logs (`--verbose`)
   - System info (`python --version`, `pip list`)
   - Configuration (sanitized)
3. **Open new issue** with template

### How do I request a feature?

1. **Check roadmap**: See if already planned
2. **Open discussion**: [GitHub Discussions](https://github.com/yourusername/security-assistant/discussions)
3. **Describe use case**: Why is this feature needed?
4. **Provide examples**: How would it work?

## Advanced Usage

### Can I use Security Assistant as a library?

Yes:
```python
from security_assistant.orchestrator import ScanOrchestrator
from security_assistant.config import SecurityAssistantConfig

config = SecurityAssistantConfig.from_file("config.yaml")
orchestrator = ScanOrchestrator(config)
findings = orchestrator.run_scan("/path/to/code")

for finding in findings:
    print(f"{finding.severity}: {finding.title}")
```

See [API Reference](api-reference.md).

### Can I add custom scanners?

Yes, implement the `BaseScanner` interface:
```python
from security_assistant.scanners.base import BaseScanner

class MyScanner(BaseScanner):
    def scan(self, target_path: str) -> List[Finding]:
        # Your scanner logic
        pass
```

Register in orchestrator:
```python
orchestrator.register_scanner(MyScanner())
```

### Can I customize deduplication logic?

Yes, implement custom deduplication:
```python
from security_assistant.orchestrator import ScanOrchestrator

class CustomOrchestrator(ScanOrchestrator):
    def _deduplicate_findings(self, findings):
        # Your deduplication logic
        pass
```

### How do I integrate with other issue trackers?

Implement an adapter:
```python
from security_assistant.gitlab_api import GitLabAPI

class JiraAdapter:
    def create_issue(self, finding):
        # Convert finding to Jira issue
        pass
```

## Best Practices

### When should I run scans?

**Recommended**:
- **Pre-commit**: Quick scan (Bandit only)
- **PR/MR**: Full scan (all scanners)
- **Scheduled**: Daily full scan with issue creation
- **Release**: Full scan with strict thresholds

### What thresholds should I use?

**Development**:
```yaml
thresholds:
  fail_on_critical: false
  fail_on_high: false
```

**Staging**:
```yaml
thresholds:
  fail_on_critical: true
  fail_on_high: false
```

**Production**:
```yaml
thresholds:
  fail_on_critical: true
  fail_on_high: true
  fail_on_medium: true
```

### How do I handle false positives?

1. **Inline suppression**:
```python
# nosec B101
assert user.is_authenticated
```

2. **Configuration exclusion**:
```yaml
scanners:
  bandit:
    config:
      skips: [B101, B404]
```

3. **Custom rules**: Create `.bandit` or `.semgrep.yml`

### Should I commit reports to Git?

**No**, add to `.gitignore`:
```
security-reports/
security_report.*
gl-sast-report.json
```

**Instead**:
- Use CI/CD artifacts
- Upload to external storage
- Create GitLab issues

## Getting Help

**Documentation**:
- [User Guide](user-guide.md)
- [Troubleshooting](troubleshooting.md)
- [API Reference](api-reference.md)

**Community**:
- [GitHub Issues](https://github.com/yourusername/security-assistant/issues)
- [GitHub Discussions](https://github.com/yourusername/security-assistant/discussions)

**Support**:
- Email: security-assistant@example.com
- Slack: [Join workspace](https://slack.example.com)
