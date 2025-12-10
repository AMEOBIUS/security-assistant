# CI/CD Integration Guide

**Integrate Security Assistant into your CI/CD pipelines**

---

## 📋 Overview

Security Assistant can be integrated into various CI/CD platforms to automate security scanning as part of your development workflow.

**Supported Platforms:**
- GitLab CI/CD
- GitHub Actions
- Jenkins
- Custom pipelines

---

## 🔧 GitLab CI/CD

### Quick Setup

The project includes a complete `.gitlab-ci.yml` configuration. See [.gitlab-ci.yml](../../.gitlab-ci.yml) for the full implementation.

### Basic Configuration

```yaml
stages:
  - security-scan

security:scan:
  image: python:3.11-slim
  stage: security-scan
  before_script:
    - pip install -r requirements.txt
    - pip install bandit semgrep
    - go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
  script:
    - python examples/orchestrator_example.py --target . --all-scanners --nuclei-enabled
    - python examples/generate_reports_example.py --format sarif
  artifacts:
    reports:
      sast: reports/security.sarif
```

### Advanced Features

**Environment Variables:**
```yaml
variables:
  ENABLE_BANDIT: "true"
  ENABLE_SEMGREP: "true"
  ENABLE_TRIVY: "true"
  ENABLE_NUCLEI: "true"
  DEDUP_STRATEGY: "both"
  FAIL_ON_CRITICAL: "true"
  FAIL_ON_HIGH: "true"
```

**Multiple Jobs:**
- `security:scan` - Full security scan
- `security:quick-scan` - Fast scan for MRs (Bandit only)
- `security:report:html` - Generate HTML report
- `security:report:markdown` - Generate Markdown report
- `security:create-issues` - Create GitLab issues for findings

**Scheduled Scans:**
```yaml
security:scheduled:
  extends: security:scan
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
  variables:
    FAIL_ON_HIGH: "false"
    FAIL_ON_CRITICAL: "false"
```

---

## 🐙 GitHub Actions

### Basic Workflow

```yaml
name: Security Scan

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * 1'  # Weekly on Monday at 2 AM

jobs:
  security-scan:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install bandit semgrep
          go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
      
      - name: Run security scan
        run: |
          python examples/orchestrator_example.py \
            --target . \
            --scanners bandit,semgrep,nuclei \
            --min-severity MEDIUM
      
      - name: Generate SARIF report
        run: |
          python examples/generate_reports_example.py --format sarif
      
      - name: Upload SARIF to GitHub
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: reports/security.sarif
      
      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: security-reports
          path: reports/
```

### Advanced Example

See [examples/cicd_integration.py](../../examples/cicd_integration.py) - `example_github_actions()` function.

---

## 🔨 Jenkins

### Jenkinsfile

```groovy
pipeline {
    agent any
    
    environment {
        ENABLE_BANDIT = 'true'
        ENABLE_SEMGREP = 'true'
        ENABLE_TRIVY = 'true'
        ENABLE_NUCLEI = 'true'
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pip install bandit semgrep'
                sh 'go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest'
            }
        }
        
        stage('Security Scan') {
            steps {
                sh '''
                    python examples/orchestrator_example.py \
                        --target . \
                        --all-scanners \
                        --min-severity MEDIUM
                '''
            }
        }
        
        stage('Generate Reports') {
            steps {
                sh 'python examples/generate_reports_example.py --format html'
                sh 'python examples/generate_reports_example.py --format json'
            }
        }
        
        stage('Publish Reports') {
            steps {
                publishHTML([
                    reportDir: 'reports',
                    reportFiles: 'security_report.html',
                    reportName: 'Security Report'
                ])
            }
        }
    }
    
    post {
        always {
            archiveArtifacts artifacts: 'reports/**/*', allowEmptyArchive: true
        }
        failure {
            emailext(
                subject: "Security Scan Failed: ${env.JOB_NAME}",
                body: "Security scan found critical issues. Check the report.",
                to: "${env.SECURITY_TEAM_EMAIL}"
            )
        }
    }
}
```

### Advanced Example

See [examples/cicd_integration.py](../../examples/cicd_integration.py) - `example_jenkins()` function.

---

## 🔧 Custom Pipelines

### Python Script

```python
from security_assistant.orchestrator import ScanOrchestrator
from security_assistant.scanners.bandit_scanner import BanditScanner
from security_assistant.scanners.semgrep_scanner import SemgrepScanner
from security_assistant.scanners.nuclei_scanner import NucleiScanner
import sys

# Create orchestrator
orchestrator = ScanOrchestrator(
    deduplication_strategy='both',
    max_workers=3
)

# Enable scanners
orchestrator.enable_scanner('bandit', BanditScanner())
orchestrator.enable_scanner('semgrep', SemgrepScanner())
orchestrator.enable_scanner('nuclei', NucleiScanner())

# Run scan
result = orchestrator.scan_directory('.')

# Check thresholds
critical = result.findings_by_severity.get('CRITICAL', 0)
high = result.findings_by_severity.get('HIGH', 0)

if critical > 0:
    print(f"❌ Failed: {critical} critical findings")
    sys.exit(1)

if high > 5:
    print(f"❌ Failed: {high} high findings (max: 5)")
    sys.exit(1)

print("✅ Security scan passed")
```

### Advanced Example

See [examples/cicd_integration.py](../../examples/cicd_integration.py) - `example_custom_pipeline()` function.

---

## 📊 Report Formats

### SARIF (Security Analysis Results Interchange Format)

**Best for:** GitHub, GitLab, Azure DevOps

```bash
python examples/generate_reports_example.py --format sarif
```

**Output:** `reports/security.sarif`

### HTML

**Best for:** Human review, Jenkins, email

```bash
python examples/generate_reports_example.py --format html
```

**Output:** `reports/security_report.html`

### JSON

**Best for:** Automation, custom processing

```bash
python examples/generate_reports_example.py --format json
```

**Output:** `reports/security_report.json`

### Markdown

**Best for:** Documentation, GitLab/GitHub comments

```bash
python examples/generate_reports_example.py --format markdown
```

**Output:** `reports/security_report.md`

---

## 🎯 Best Practices

### 1. Fail Fast on Critical Issues

```yaml
variables:
  FAIL_ON_CRITICAL: "true"
  FAIL_ON_HIGH: "true"
```

### 2. Use Quick Scans for PRs/MRs

```yaml
security:quick-scan:
  variables:
    ENABLE_BANDIT: "true"
    ENABLE_SEMGREP: "false"
    ENABLE_TRIVY: "false"
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

### 3. Full Scans on Main Branch

```yaml
security:full-scan:
  variables:
    ENABLE_BANDIT: "true"
    ENABLE_SEMGREP: "true"
    ENABLE_TRIVY: "true"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### 4. Scheduled Deep Scans

```yaml
security:scheduled:
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
  variables:
    FAIL_ON_HIGH: "false"  # Don't fail scheduled scans
```

### 5. Cache Dependencies

```yaml
cache:
  paths:
    - .cache/pip
    - .semgrep/
```

### 6. Parallel Execution

```yaml
security:scan:
  parallel:
    matrix:
      - SCANNER: [bandit, semgrep, trivy]
```

---

## 🔍 Troubleshooting

### Scanner Not Found

**Problem:** `bandit: command not found`

**Solution:**
```bash
pip install bandit[toml]
```

### Permission Denied

**Problem:** Cannot write to reports directory

**Solution:**
```yaml
before_script:
  - mkdir -p reports
  - chmod 755 reports
```

### Timeout Issues

**Problem:** Scan takes too long

**Solution:**
```python
orchestrator = ScanOrchestrator(
    max_workers=4,  # Increase parallelism
    timeout=300     # 5 minute timeout
)
```

### Memory Issues

**Problem:** Out of memory during scan

**Solution:**
```yaml
variables:
  DOCKER_MEMORY: "4g"
```

---

## 📚 Examples

### Complete Examples

See [examples/cicd_integration.py](../../examples/cicd_integration.py) for complete working examples:

- `example_gitlab_ci()` - GitLab CI/CD integration
- `example_github_actions()` - GitHub Actions integration
- `example_jenkins()` - Jenkins integration
- `example_custom_pipeline()` - Custom pipeline integration

### Live Configuration

See [.gitlab-ci.yml](../../.gitlab-ci.yml) for production-ready GitLab CI/CD configuration.

---

## 🔗 Related Documentation

- [Quick Start](quick-start.md) - Get started with Security Assistant
- [API Reference](../reference/api.md) - Programmatic usage
- [Orchestrator](../reference/orchestrator.md) - Multi-scanner orchestration
- [Best Practices](best-practices.md) - Security best practices

---

**Last Updated:** 2025-12-02  
**Version:** 1.0.0
