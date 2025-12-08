# CLI Reference

Complete command-line interface reference for Security Assistant.

## Table of Contents

- [Installation](#installation)
- [Global Options](#global-options)
- [Commands](#commands)
- [Environment Variables](#environment-variables)
- [Exit Codes](#exit-codes)
- [Examples](#examples)

## Installation

```bash
# Install from source
pip install -e .

# Install with all scanners
pip install -e ".[scanners]"

# Verify installation
security-assistant --version
```

## Global Options

Options available for all commands:

```
--version              Show version and exit
--help                 Show help message and exit
--config PATH          Configuration file path
--verbose, -v          Enable verbose output
--quiet, -q            Suppress output (errors only)
--log-file PATH        Write logs to file
--log-level LEVEL      Set log level (DEBUG, INFO, WARNING, ERROR)
```

**Examples**:
```bash
# Show version
security-assistant --version

# Use custom config
security-assistant --config /path/to/config.yaml scan .

# Verbose output
security-assistant -v scan .

# Write logs to file
security-assistant --log-file scan.log scan .
```

## Commands

### scan

Run security scan on target path.

**Usage**:
```bash
security-assistant scan [OPTIONS] TARGET
```

**Arguments**:
- `TARGET`: Path to scan (file or directory)

**Options**:

#### Scanner Selection

```
--scanners TEXT        Comma-separated list of scanners to use
                       Choices: bandit, semgrep, trivy
                       Default: all enabled in config
```

**Examples**:
```bash
# Use all scanners
security-assistant scan .

# Use only Bandit
security-assistant scan . --scanners bandit

# Use Bandit and Semgrep
security-assistant scan . --scanners bandit,semgrep
```

#### Deduplication

```
--dedup-strategy TEXT  Deduplication strategy
                       Choices: strict, fuzzy, location
                       Default: fuzzy
```

**Examples**:
```bash
# Strict deduplication
security-assistant scan . --dedup-strategy strict

# Location-based deduplication
security-assistant scan . --dedup-strategy location
```

#### Report Generation

```
--format TEXT          Report format(s) (comma-separated)
                       Choices: html, json, markdown, sarif, gitlab-sast
                       Default: html

--output-dir PATH      Output directory for reports
                       Default: ./security-reports

--no-report            Skip report generation
```

**Examples**:
```bash
# HTML report (default)
security-assistant scan .

# Multiple formats
security-assistant scan . --format html,json,markdown

# Custom output directory
security-assistant scan . --output-dir /tmp/reports

# No report (findings only)
security-assistant scan . --no-report
```

#### GitLab Integration

```
--create-issues        Create GitLab issues for findings
--gitlab-url URL       GitLab instance URL
                       Default: https://gitlab.com
--gitlab-token TOKEN   GitLab personal access token
                       Default: from SA_GITLAB_TOKEN env var
--gitlab-project-id ID GitLab project ID
                       Default: from SA_GITLAB_PROJECT_ID env var
--priority-threshold   Minimum priority for issue creation
                       Choices: critical, high, medium, low
                       Default: high
```

**Examples**:
```bash
# Create issues for high and critical findings
security-assistant scan . --create-issues

# Create issues only for critical findings
security-assistant scan . --create-issues --priority-threshold critical

# Use custom GitLab instance
security-assistant scan . \
  --create-issues \
  --gitlab-url https://gitlab.example.com \
  --gitlab-token glpat-... \
  --gitlab-project-id 12345
```

#### Failure Thresholds

```
--fail-on LEVEL        Fail (exit 1) if findings at or above this level
                       Choices: critical, high, medium, low, info
                       Default: none (never fail)
```

**Examples**:
```bash
# Fail on critical findings
security-assistant scan . --fail-on critical

# Fail on high or critical
security-assistant scan . --fail-on high

# Fail on any findings
security-assistant scan . --fail-on info
```

#### Performance

```
--max-workers INT      Maximum parallel workers
                       Default: 4

--timeout INT          Scanner timeout in seconds
                       Default: 300 (5 minutes)

--quick                Quick scan mode (faster, less comprehensive)
```

**Examples**:
```bash
# Use 8 parallel workers
security-assistant scan . --max-workers 8

# Increase timeout to 10 minutes
security-assistant scan . --timeout 600

# Quick scan for development
security-assistant scan . --quick
```

#### Scanner-Specific Options

```
--bandit-config PATH   Bandit configuration file (.bandit)
--semgrep-rules TEXT   Semgrep rules (comma-separated)
                       Default: p/default
--trivy-severity TEXT  Trivy severity levels (comma-separated)
                       Default: CRITICAL,HIGH,MEDIUM,LOW
```

**Examples**:
```bash
# Custom Bandit config
security-assistant scan . --bandit-config .bandit

# Specific Semgrep rules
security-assistant scan . --semgrep-rules "p/python,p/security-audit"

# Only critical and high for Trivy
security-assistant scan . --trivy-severity CRITICAL,HIGH
```

**Complete Example**:
```bash
security-assistant scan /path/to/code \
  --scanners bandit,semgrep,trivy \
  --dedup-strategy fuzzy \
  --format html,json,gitlab-sast \
  --output-dir ./reports \
  --create-issues \
  --priority-threshold high \
  --fail-on critical \
  --max-workers 8 \
  --verbose
```

### config

Manage configuration.

**Usage**:
```bash
security-assistant config [COMMAND] [OPTIONS]
```

**Commands**:

#### show

Show current configuration.

```bash
security-assistant config show [OPTIONS]
```

**Options**:
```
--format TEXT          Output format
                       Choices: yaml, json, table
                       Default: yaml
```

**Examples**:
```bash
# Show as YAML
security-assistant config show

# Show as JSON
security-assistant config show --format json

# Show as table
security-assistant config show --format table
```

#### validate

Validate configuration file.

```bash
security-assistant config validate [OPTIONS]
```

**Options**:
```
--config PATH          Configuration file to validate
                       Default: ./security-assistant.yaml
```

**Examples**:
```bash
# Validate default config
security-assistant config validate

# Validate specific file
security-assistant config validate --config /path/to/config.yaml
```

**Output**:
```
✓ Configuration is valid
  - Scanners: bandit, semgrep, trivy
  - Deduplication: fuzzy
  - Report formats: html, json
  - GitLab integration: enabled
```

#### init

Initialize configuration file.

```bash
security-assistant config init [OPTIONS]
```

**Options**:
```
--output PATH          Output file path
                       Default: ./security-assistant.yaml
--template TEXT        Configuration template
                       Choices: minimal, python, strict, gitlab, quick
                       Default: minimal
--force                Overwrite existing file
```

**Examples**:
```bash
# Create minimal config
security-assistant config init

# Create Python-focused config
security-assistant config init --template python

# Create strict security config
security-assistant config init --template strict

# Overwrite existing
security-assistant config init --force
```

### report

Generate reports from existing findings.

**Usage**:
```bash
security-assistant report [OPTIONS]
```

**Options**:
```
--input PATH           Input file (JSON findings)
                       Required
--format TEXT          Report format(s) (comma-separated)
                       Choices: html, json, markdown, sarif, gitlab-sast
                       Default: html
--output-dir PATH      Output directory
                       Default: ./security-reports
```

**Examples**:
```bash
# Generate HTML from JSON findings
security-assistant report --input findings.json

# Generate multiple formats
security-assistant report \
  --input findings.json \
  --format html,markdown,sarif

# Custom output directory
security-assistant report \
  --input findings.json \
  --output-dir /tmp/reports
```

## Environment Variables

All configuration options can be set via environment variables with `SA_` prefix.

### Scanner Configuration

```bash
# Enable/disable scanners
export SA_BANDIT_ENABLED=true
export SA_SEMGREP_ENABLED=true
export SA_TRIVY_ENABLED=false

# Scanner-specific config
export SA_BANDIT_EXCLUDE_DIRS=tests,venv
export SA_SEMGREP_RULES=p/python,p/security-audit
export SA_TRIVY_SEVERITY=CRITICAL,HIGH
```

### Orchestrator Configuration

```bash
# Deduplication strategy
export SA_DEDUP_STRATEGY=fuzzy

# Parallel workers
export SA_MAX_WORKERS=8

# Timeout
export SA_TIMEOUT=600
```

### Report Configuration

```bash
# Report formats
export SA_REPORT_FORMATS=html,json,markdown

# Output directory
export SA_OUTPUT_DIR=./security-reports
```

### GitLab Integration

```bash
# GitLab URL
export SA_GITLAB_URL=https://gitlab.com

# GitLab token (required for issue creation)
export SA_GITLAB_TOKEN=glpat-your-token

# GitLab project ID
export SA_GITLAB_PROJECT_ID=12345

# Create issues
export SA_GITLAB_CREATE_ISSUES=true

# Priority threshold
export SA_PRIORITY_THRESHOLD=high
```

### Thresholds

```bash
# Fail on findings
export SA_FAIL_ON_CRITICAL=true
export SA_FAIL_ON_HIGH=false
export SA_FAIL_ON_MEDIUM=false
```

### Logging

```bash
# Log level
export SA_LOG_LEVEL=DEBUG

# Log file
export SA_LOG_FILE=security-assistant.log

# Verbose output
export SA_VERBOSE=true
```

### Scan Target

```bash
# Default scan target
export SA_SCAN_TARGET=/path/to/code
```

**Example .env file**:
```bash
# .env
SA_BANDIT_ENABLED=true
SA_SEMGREP_ENABLED=true
SA_TRIVY_ENABLED=true

SA_DEDUP_STRATEGY=fuzzy
SA_MAX_WORKERS=8

SA_REPORT_FORMATS=html,json,gitlab-sast
SA_OUTPUT_DIR=./security-reports

SA_GITLAB_TOKEN=glpat-your-token
SA_GITLAB_PROJECT_ID=12345
SA_GITLAB_CREATE_ISSUES=true
SA_PRIORITY_THRESHOLD=high

SA_FAIL_ON_CRITICAL=true
SA_FAIL_ON_HIGH=true

SA_LOG_LEVEL=INFO
```

## Exit Codes

Security Assistant uses standard exit codes:

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Scan completed, no findings above threshold |
| 1 | Findings | Findings found at or above failure threshold |
| 2 | Error | Error during scan (scanner not found, config invalid, etc.) |

**Examples**:

```bash
# Exit 0: No critical findings
security-assistant scan . --fail-on critical
echo $?  # 0

# Exit 1: Critical findings found
security-assistant scan . --fail-on critical
echo $?  # 1

# Exit 2: Scanner not installed
security-assistant scan . --scanners nonexistent
echo $?  # 2
```

**Use in scripts**:
```bash
#!/bin/bash
set -e

# Run scan
if security-assistant scan . --fail-on high; then
    echo "✓ No high or critical findings"
    exit 0
else
    exit_code=$?
    if [ $exit_code -eq 1 ]; then
        echo "✗ High or critical findings detected"
        exit 1
    else
        echo "✗ Scan failed with error"
        exit 2
    fi
fi
```

## Examples

### Basic Usage

```bash
# Scan current directory
security-assistant scan .

# Scan specific directory
security-assistant scan /path/to/code

# Scan with verbose output
security-assistant scan . -v
```

### Scanner Selection

```bash
# Use only Bandit (fast)
security-assistant scan . --scanners bandit

# Use Bandit and Semgrep (no dependencies)
security-assistant scan . --scanners bandit,semgrep

# Use all scanners
security-assistant scan .
```

### Report Generation

```bash
# HTML report (default)
security-assistant scan .

# JSON report
security-assistant scan . --format json

# Multiple formats
security-assistant scan . --format html,json,markdown

# SARIF for GitHub
security-assistant scan . --format sarif

# GitLab SAST format
security-assistant scan . --format gitlab-sast
```

### GitLab Integration

```bash
# Create issues for high and critical findings
export SA_GITLAB_TOKEN=glpat-your-token
export SA_GITLAB_PROJECT_ID=12345
security-assistant scan . --create-issues

# Create issues only for critical
security-assistant scan . \
  --create-issues \
  --priority-threshold critical

# Custom GitLab instance
security-assistant scan . \
  --create-issues \
  --gitlab-url https://gitlab.example.com \
  --gitlab-token glpat-... \
  --gitlab-project-id 12345
```

### CI/CD Usage

```bash
# Fail build on critical findings
security-assistant scan . --fail-on critical

# Fail on high or critical
security-assistant scan . --fail-on high

# Generate GitLab SAST report
security-assistant scan . \
  --format gitlab-sast \
  --output-dir .

# Generate SARIF for GitHub
security-assistant scan . \
  --format sarif \
  --output-dir .
```

### Development Workflow

```bash
# Quick scan (pre-commit)
security-assistant scan . \
  --scanners bandit \
  --quick \
  --fail-on critical

# Full scan (pre-push)
security-assistant scan . \
  --format html \
  --fail-on high

# Comprehensive scan (CI/CD)
security-assistant scan . \
  --format html,json,gitlab-sast \
  --create-issues \
  --fail-on medium
```

### Configuration Management

```bash
# Show current config
security-assistant config show

# Validate config
security-assistant config validate

# Initialize new config
security-assistant config init --template python

# Use custom config
security-assistant scan . --config /path/to/config.yaml
```

### Advanced Usage

```bash
# Parallel execution with 16 workers
security-assistant scan . --max-workers 16

# Increase timeout to 15 minutes
security-assistant scan . --timeout 900

# Strict deduplication
security-assistant scan . --dedup-strategy strict

# Custom Semgrep rules
security-assistant scan . \
  --semgrep-rules "p/python,p/django,p/flask"

# Only critical and high from Trivy
security-assistant scan . \
  --trivy-severity CRITICAL,HIGH
```

### Combining Options

```bash
# Complete example
security-assistant scan /path/to/code \
  --config config/production.yaml \
  --scanners bandit,semgrep,trivy \
  --dedup-strategy fuzzy \
  --format html,json,gitlab-sast \
  --output-dir ./reports \
  --create-issues \
  --gitlab-url https://gitlab.com \
  --gitlab-token $GITLAB_TOKEN \
  --gitlab-project-id 12345 \
  --priority-threshold high \
  --fail-on critical \
  --max-workers 8 \
  --timeout 600 \
  --verbose \
  --log-file scan.log
```

## Shell Completion

### Bash

```bash
# Add to ~/.bashrc
eval "$(_SECURITY_ASSISTANT_COMPLETE=bash_source security-assistant)"
```

### Zsh

```bash
# Add to ~/.zshrc
eval "$(_SECURITY_ASSISTANT_COMPLETE=zsh_source security-assistant)"
```

### Fish

```bash
# Add to ~/.config/fish/config.fish
eval (env _SECURITY_ASSISTANT_COMPLETE=fish_source security-assistant)
```

## Tips and Tricks

### Use Aliases

```bash
# Add to ~/.bashrc or ~/.zshrc
alias sa='security-assistant'
alias sa-scan='security-assistant scan'
alias sa-quick='security-assistant scan . --quick --scanners bandit'
alias sa-full='security-assistant scan . --format html,json --create-issues'

# Usage
sa-quick
sa-full
```

### Pre-commit Hook

```bash
# .git/hooks/pre-commit
#!/bin/bash
security-assistant scan . \
  --scanners bandit \
  --quick \
  --fail-on critical \
  --no-report

if [ $? -ne 0 ]; then
    echo "❌ Security scan failed. Fix critical issues before committing."
    exit 1
fi
```

### Makefile Integration

```makefile
# Makefile
.PHONY: security-scan security-quick security-full

security-scan:
	security-assistant scan .

security-quick:
	security-assistant scan . --quick --scanners bandit

security-full:
	security-assistant scan . \
		--format html,json,gitlab-sast \
		--create-issues \
		--fail-on high

# Usage: make security-scan
```

### Docker Integration

```dockerfile
# Dockerfile
FROM python:3.11

WORKDIR /app
COPY . .

RUN pip install -e ".[scanners]"

CMD ["security-assistant", "scan", "."]
```

```bash
# Build and run
docker build -t security-scan .
docker run -v $(pwd):/app security-scan
```

## See Also

- [API Reference](api-reference.md) - Programmatic usage
- [Configuration Guide](configuration.md) - Configuration options
- [Quick Start](quick-start.md) - Getting started guide
- [Examples](../examples/) - More examples
