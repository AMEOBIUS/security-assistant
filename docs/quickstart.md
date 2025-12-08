# Quick Start Guide

Get started with Security Assistant in minutes.

## Basic Scan

Scan the current directory with default settings:

```bash
security-assistant scan .
```

## Targeted Scan

Scan a specific directory or file:

```bash
security-assistant scan ./src
security-assistant scan ./app.py
```

## Output Formats

Generate reports in multiple formats (HTML, JSON, SARIF, Markdown):

```bash
security-assistant scan . --format html,json,sarif --output-dir reports
```

Check `reports/report.html` for a visual dashboard.

## Filter Scanners

Run specific scanners only:

```bash
# Run only Bandit (Python SAST)
security-assistant scan . --bandit-only

# Run only Trivy (SCA + Secrets)
security-assistant scan . --trivy-only
```

## Failure Thresholds

Fail the build (exit code 1) if critical issues are found (useful for CI/CD):

```bash
security-assistant scan . --fail-on-critical
security-assistant scan . --fail-on-high
```

## Bulk Scanning

Scan multiple repositories or directories at once:

```bash
security-assistant scan repo1/ repo2/ repo3/ --format html
```

Or use a targets file:

```bash
# targets.txt
# /path/to/repo1
# /path/to/repo2

security-assistant scan --targets-file targets.txt
```
