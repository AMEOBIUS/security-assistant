# Migration Guide

Guide for upgrading Security Assistant and migrating from other tools.

## Table of Contents

- [Upgrading Security Assistant](#upgrading-security-assistant)
- [Migrating from Manual Scanning](#migrating-from-manual-scanning)
- [Migrating from Other Tools](#migrating-from-other-tools)
- [Platform Migration](#platform-migration)
- [Breaking Changes](#breaking-changes)

## Upgrading Security Assistant

### Version 1.0.0 (Current)

**Initial release** - No migration needed.

### Future Upgrades

**General upgrade process**:

1. **Backup configuration**:
```bash
cp security-assistant.yaml security-assistant.yaml.backup
```

2. **Update code**:
```bash
cd security-assistant
git pull origin main
```

3. **Update dependencies**:
```bash
pip install --upgrade -e ".[scanners]"
```

4. **Check for breaking changes**:
```bash
# Review CHANGELOG.md
cat CHANGELOG.md

# Test configuration
security-assistant config validate
```

5. **Update configuration** (if needed):
```bash
# Compare with new example
diff security-assistant.yaml config/security-assistant.example.yaml
```

6. **Test**:
```bash
# Dry run
security-assistant scan . --dry-run

# Full scan
security-assistant scan .
```

## Migrating from Manual Scanning

### From Individual Scanner Scripts

**Before** (manual Bandit):
```bash
#!/bin/bash
bandit -r src/ -f json -o bandit-report.json
```

**After** (Security Assistant):
```bash
security-assistant scan src/ --format json
```

**Migration steps**:

1. **Install Security Assistant**:
```bash
pip install -e ".[scanners]"
```

2. **Create configuration**:
```yaml
# security-assistant.yaml
scanners:
  bandit:
    enabled: true
    config:
      exclude_dirs:
        - tests
        - venv

report:
  formats:
    - json
  output_dir: "reports"
```

3. **Update scripts**:
```bash
# Old
./run-bandit.sh

# New
security-assistant scan src/
```

4. **Update CI/CD**:
```yaml
# .gitlab-ci.yml
security-scan:
  script:
    - security-assistant scan . --format gitlab-sast
  artifacts:
    reports:
      sast: gl-sast-report.json
```

### From Multiple Scanner Scripts

**Before** (multiple scripts):
```bash
#!/bin/bash
# run-all-scanners.sh
bandit -r src/ -f json -o bandit.json
semgrep --config auto src/ --json -o semgrep.json
trivy fs src/ --format json -o trivy.json

# Manually combine results
python combine-results.py
```

**After** (Security Assistant):
```bash
security-assistant scan src/ --format json
```

**Benefits**:
- ✅ Single command
- ✅ Automatic deduplication
- ✅ Unified report format
- ✅ Parallel execution

**Migration steps**:

1. **Map scanner configurations**:

   **Bandit** (`.bandit`):
   ```yaml
   # Old: .bandit
   exclude_dirs:
     - /tests/
   skips:
     - B101
   ```

   ```yaml
   # New: security-assistant.yaml
   scanners:
     bandit:
       config:
         exclude_dirs:
           - tests
         skips:
           - B101
   ```

   **Semgrep** (`.semgrepignore`):
   ```
   # Old: .semgrepignore
   tests/
   venv/
   ```

   ```yaml
   # New: security-assistant.yaml
   scanners:
     semgrep:
       config:
         exclude:
           - tests/
           - venv/
   ```

2. **Replace scripts**:
```bash
# Remove old scripts
rm run-bandit.sh run-semgrep.sh run-trivy.sh combine-results.py

# Use Security Assistant
security-assistant scan .
```

3. **Update documentation**:
```markdown
# Old
## Running Security Scans

1. Run Bandit: `./run-bandit.sh`
2. Run Semgrep: `./run-semgrep.sh`
3. Run Trivy: `./run-trivy.sh`
4. Combine results: `python combine-results.py`

# New
## Running Security Scans

```bash
security-assistant scan .
```
```

## Migrating from Other Tools

### From SonarQube

**Differences**:
- SonarQube: Centralized server, web UI
- Security Assistant: CLI tool, CI/CD focused

**Migration strategy**:

1. **Keep SonarQube for**:
   - Code quality metrics
   - Technical debt tracking
   - Team dashboards

2. **Use Security Assistant for**:
   - Security-focused scanning
   - GitLab integration
   - CI/CD pipeline integration

**Parallel usage**:
```yaml
# .gitlab-ci.yml
code-quality:
  stage: test
  script:
    - sonar-scanner

security-scan:
  stage: security
  script:
    - security-assistant scan . --format gitlab-sast
```

### From Snyk

**Differences**:
- Snyk: SaaS platform, dependency focus
- Security Assistant: Self-hosted, code + dependencies

**Migration strategy**:

1. **Map Snyk configuration**:

   **Snyk** (`.snyk`):
   ```yaml
   # .snyk
   ignore:
     SNYK-PYTHON-REQUESTS-1234567:
       - '*':
           reason: False positive
   ```

   **Security Assistant**:
   ```yaml
   # security-assistant.yaml
   scanners:
     trivy:
       config:
         ignore_unfixed: true
         severity:
           - CRITICAL
           - HIGH
   ```

2. **Replace Snyk CLI**:
```bash
# Old
snyk test --json > snyk-report.json

# New
security-assistant scan . --scanners trivy --format json
```

3. **Update CI/CD**:
```yaml
# Old
security:
  script:
    - snyk test --severity-threshold=high

# New
security:
  script:
    - security-assistant scan . --fail-on high
```

### From OWASP Dependency-Check

**Differences**:
- Dependency-Check: Java-based, dependency focus
- Security Assistant: Python-based, code + dependencies

**Migration strategy**:

1. **Replace Dependency-Check**:
```bash
# Old
dependency-check.sh --project myapp --scan ./

# New
security-assistant scan . --scanners trivy
```

2. **Map configuration**:

   **Dependency-Check** (`dependency-check.properties`):
   ```properties
   suppression.file=suppressions.xml
   failOnCVSS=7
   ```

   **Security Assistant**:
   ```yaml
   scanners:
     trivy:
       enabled: true
       config:
         severity:
           - CRITICAL
           - HIGH
   
   thresholds:
     fail_on_high: true
   ```

3. **Update reports**:
```bash
# Old: HTML report
dependency-check.sh --format HTML

# New: HTML report
security-assistant scan . --format html
```

## Platform Migration

### From Jenkins to GitLab CI

**Migration steps**:

1. **Convert Jenkinsfile to .gitlab-ci.yml**:

   **Jenkins** (`Jenkinsfile`):
   ```groovy
   pipeline {
       agent any
       stages {
           stage('Security Scan') {
               steps {
                   sh 'security-assistant scan .'
               }
           }
       }
   }
   ```

   **GitLab CI** (`.gitlab-ci.yml`):
   ```yaml
   security-scan:
     stage: test
     script:
       - security-assistant scan .
   ```

2. **Migrate artifacts**:

   **Jenkins**:
   ```groovy
   publishHTML([
       reportDir: 'security-reports',
       reportFiles: 'security_report.html',
       reportName: 'Security Report'
   ])
   ```

   **GitLab CI**:
   ```yaml
   artifacts:
     paths:
       - security-reports/
     reports:
       sast: gl-sast-report.json
   ```

3. **Migrate environment variables**:

   **Jenkins**: Configure in Jenkins UI
   **GitLab CI**: Settings → CI/CD → Variables

### From GitHub Actions to GitLab CI

**Migration steps**:

1. **Convert workflow**:

   **GitHub Actions** (`.github/workflows/security.yml`):
   ```yaml
   name: Security Scan
   on: [push, pull_request]
   
   jobs:
     security:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - run: security-assistant scan .
   ```

   **GitLab CI** (`.gitlab-ci.yml`):
   ```yaml
   security-scan:
     stage: test
     script:
       - security-assistant scan .
   ```

2. **Migrate SARIF to GitLab SAST**:

   **GitHub Actions**:
   ```yaml
   - run: security-assistant scan . --format sarif
   - uses: github/codeql-action/upload-sarif@v2
     with:
       sarif_file: security-report.sarif
   ```

   **GitLab CI**:
   ```yaml
   script:
     - security-assistant scan . --format gitlab-sast
   artifacts:
     reports:
       sast: gl-sast-report.json
   ```

### From Travis CI to GitLab CI

**Migration steps**:

1. **Convert .travis.yml**:

   **Travis CI** (`.travis.yml`):
   ```yaml
   language: python
   python:
     - "3.11"
   script:
     - security-assistant scan .
   ```

   **GitLab CI** (`.gitlab-ci.yml`):
   ```yaml
   security-scan:
     image: python:3.11
     script:
       - security-assistant scan .
   ```

2. **Migrate caching**:

   **Travis CI**:
   ```yaml
   cache:
     directories:
       - $HOME/.cache/trivy
   ```

   **GitLab CI**:
   ```yaml
   cache:
     paths:
       - .trivy-cache/
   ```

## Breaking Changes

### Version 1.0.0 → 2.0.0 (Future)

**Hypothetical breaking changes** (for reference):

#### Configuration Format Changes

**Old** (v1.0.0):
```yaml
bandit:
  enabled: true
  exclude: ["tests", "venv"]
```

**New** (v2.0.0):
```yaml
scanners:
  bandit:
    enabled: true
    config:
      exclude_dirs:
        - tests
        - venv
```

**Migration**:
```bash
# Use migration tool
security-assistant migrate-config security-assistant.yaml
```

#### CLI Changes

**Old** (v1.0.0):
```bash
security-assistant scan . --output-format html
```

**New** (v2.0.0):
```bash
security-assistant scan . --format html
```

**Migration**:
```bash
# Update scripts
sed -i 's/--output-format/--format/g' *.sh
```

#### API Changes

**Old** (v1.0.0):
```python
from security_assistant import SecurityAssistant

sa = SecurityAssistant()
findings = sa.scan("/path/to/code")
```

**New** (v2.0.0):
```python
from security_assistant.orchestrator import ScanOrchestrator
from security_assistant.config import SecurityAssistantConfig

config = SecurityAssistantConfig.from_file("config.yaml")
orchestrator = ScanOrchestrator(config)
findings = orchestrator.run_scan("/path/to/code")
```

**Migration**:
```python
# Update imports and usage
# See API Reference for details
```

## Migration Checklist

### Pre-Migration

- [ ] Backup current configuration
- [ ] Document current workflow
- [ ] Review breaking changes
- [ ] Test in development environment
- [ ] Update documentation

### Migration

- [ ] Install new version
- [ ] Update configuration
- [ ] Update scripts
- [ ] Update CI/CD pipelines
- [ ] Update documentation

### Post-Migration

- [ ] Test all workflows
- [ ] Verify reports
- [ ] Check GitLab integration
- [ ] Monitor for issues
- [ ] Update team documentation

### Rollback Plan

If migration fails:

1. **Restore backup**:
```bash
cp security-assistant.yaml.backup security-assistant.yaml
```

2. **Downgrade version**:
```bash
git checkout v1.0.0
pip install -e ".[scanners]"
```

3. **Verify functionality**:
```bash
security-assistant scan . --dry-run
```

## Getting Help

**Migration issues?**
- Check [Troubleshooting Guide](troubleshooting-guide.md)
- Review [FAQ](faq.md)
- Open GitHub issue with:
  - Current version
  - Target version
  - Error messages
  - Configuration files

**Need assistance?**
- Email: security-assistant@example.com
- Slack: [Join workspace](https://slack.example.com)
- GitHub Discussions: [Ask question](https://github.com/yourusername/security-assistant/discussions)
