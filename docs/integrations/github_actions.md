# GitHub Actions Integration

Integrate Security Assistant into your GitHub CI/CD pipeline.

## Workflow Example

Create `.github/workflows/security-scan.yml`:

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  security-assistant:
    runs-on: ubuntu-latest
    permissions:
      security-events: write # Required for SARIF upload
      contents: read
      
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install Security Assistant
        run: |
          pip install security-assistant
          # Install scanners dependencies
          curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
          pip install semgrep bandit
          
      - name: Run Scan
        run: |
          security-assistant scan . --format sarif,html --output-dir reports --fail-on-critical
          
      - name: Upload SARIF to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: reports/report.sarif
          category: security-assistant
          
      - name: Upload HTML Report
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: security-report
          path: reports/report.html
```

## Features

- **PR Blocking**: Fails the build if critical issues are found.
- **Security Tab**: Results appear in the GitHub "Security" tab via SARIF upload.
- **Artifacts**: HTML report is downloadable as a build artifact.
