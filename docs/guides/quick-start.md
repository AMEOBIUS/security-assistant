# Quick Start Guide

Get Security Assistant up and running in 5 minutes.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Git (optional, for cloning)

## Installation

### Option 1: Install from Source

```bash
# Clone repository
git clone https://github.com/yourusername/security-assistant.git
cd security-assistant

# Install with all scanners
pip install -e ".[scanners]"
```

### Option 2: Install Core Only

```bash
pip install -e .
```

Then install scanners separately:

```bash
# Bandit
pip install bandit

# Semgrep
pip install semgrep

# Trivy (requires Docker or standalone binary)
# See: https://trivy.dev/latest/getting-started/installation/
```

## Verify Installation

```bash
# Check Security Assistant
security-assistant --version

# Check scanners
bandit --version
semgrep --version
trivy --version
```

## First Scan

### 1. Basic Scan

Scan current directory:

```bash
security-assistant scan .
```

Output:
```
[INFO] Starting security scan...
[INFO] Running Bandit scanner...
[INFO] Running Semgrep scanner...
[INFO] Running Trivy scanner...
[INFO] Deduplicating findings...
[INFO] Found 15 unique findings
[INFO] Scan complete!
```

### 2. Generate HTML Report

```bash
security-assistant scan . --format html
```

Opens `security_report.html` in your browser with:
- Summary statistics
- Findings by severity
- Detailed vulnerability information
- Remediation recommendations

### 3. Scan Specific Directory

```bash
security-assistant scan /path/to/your/project
```

### 4. Use Specific Scanners

```bash
# Python only (Bandit + Semgrep)
security-assistant scan . --scanners bandit,semgrep

# Dependencies only (Trivy)
security-assistant scan . --scanners trivy
```

## Configuration

### Quick Configuration File

Create `security-assistant.yaml`:

```yaml
scanners:
  bandit:
    enabled: true
  semgrep:
    enabled: true
  trivy:
    enabled: true

orchestrator:
  deduplication_strategy: "fuzzy"
  max_workers: 4

report:
  formats:
    - html
    - json
  output_dir: "security-reports"
```

Use it:

```bash
security-assistant scan . --config security-assistant.yaml
```

### Environment Variables

```bash
# Enable only Bandit
export SA_BANDIT_ENABLED=true
export SA_SEMGREP_ENABLED=false
export SA_TRIVY_ENABLED=false

# Run scan
security-assistant scan .
```

## GitLab Integration

### 1. Set Up GitLab Token

```bash
export SA_GITLAB_TOKEN="your-gitlab-token"
export SA_GITLAB_PROJECT_ID="12345"
```

### 2. Create Issues Automatically

```bash
security-assistant scan . --create-issues
```

This creates GitLab issues for:
- Critical severity findings
- High severity findings (configurable)

### 3. Filter by Priority

```bash
# Only create issues for critical findings
export SA_PRIORITY_THRESHOLD="critical"
security-assistant scan . --create-issues
```

## CI/CD Integration

### GitLab CI

Add to `.gitlab-ci.yml`:

```yaml
security-scan:
  stage: test
  image: python:3.11
  script:
    - pip install -e ".[scanners]"
    - security-assistant scan . --format gitlab-sast
  artifacts:
    reports:
      sast: gl-sast-report.json
```

### GitHub Actions

Add to `.github/workflows/security.yml`:

```yaml
name: Security Scan
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e ".[scanners]"
      - run: security-assistant scan . --format sarif
      - uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: security-report.sarif
```

## Common Use Cases

### 1. Pre-Commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
security-assistant scan . --fail-on critical
```

### 2. Scheduled Scans

```bash
# Cron job (daily at 2 AM)
0 2 * * * cd /path/to/project && security-assistant scan . --create-issues
```

### 3. Multiple Report Formats

```bash
security-assistant scan . --format html,json,markdown
```

Generates:
- `security_report.html`
- `security_report.json`
- `security_report.md`

### 4. Fail Build on Findings

```bash
# Fail on critical findings
security-assistant scan . --fail-on critical

# Fail on high or critical
security-assistant scan . --fail-on high

# Fail on any findings
security-assistant scan . --fail-on medium
```

## Next Steps

**Learn More**:
- [Configuration Guide](configuration.md) - All configuration options
- [CLI Reference](cli-reference.md) - Complete command reference
- [Best Practices](best-practices.md) - Recommendations

**Integrate**:
- [CI/CD Integration](cicd-integration.md) - Detailed CI/CD setup
- [GitLab Integration](gitlab-integration.md) - Issue management

**Troubleshoot**:
- [Troubleshooting](troubleshooting.md) - Common issues
- [FAQ](faq.md) - Frequently asked questions

## Getting Help

**Found an issue?**
- Check [Troubleshooting Guide](troubleshooting.md)
- Search [FAQ](faq.md)
- Open an issue on GitHub

**Need a feature?**
- Check [Best Practices](best-practices.md)
- Review [API Reference](api-reference.md)
- Request a feature on GitHub

## Summary

You've learned how to:
- ✅ Install Security Assistant
- ✅ Run your first scan
- ✅ Generate reports
- ✅ Configure scanners
- ✅ Integrate with GitLab
- ✅ Set up CI/CD

**Time to scan**: ~2 minutes  
**Time to configure**: ~3 minutes  
**Total time**: ~5 minutes ✨
