# Configuration Guide

Security Assistant can be configured via a YAML file (`security-assistant.yaml`) or environment variables.

## JSON Schema Validation

For IDE autocompletion and validation (VS Code, IntelliJ, etc.), you can use the generated JSON Schema:

- **Schema URL**: [docs/config-schema.json](config-schema.json)

To use it in VS Code, add this to the top of your `security-assistant.yaml`:

```yaml
# yaml-language-server: $schema=./docs/config-schema.json
```

## Configuration File

Create a default configuration file:

```bash
security-assistant config --create
```

### Example `security-assistant.yaml`

```yaml
# yaml-language-server: $schema=./docs/config-schema.json

# General Settings
scan_target: "."
verbose: false
log_level: "INFO"

# Scanners
bandit:
  enabled: true
  severity_level: "low"  # low, medium, high
  confidence_level: "low"
  exclude_dirs: ["tests", "venv"]

semgrep:
  enabled: true
  rules: ["auto"]  # or specific rules e.g. "p/security-audit"

trivy:
  enabled: true
  scanners: ["vuln", "secret", "config"]
  severity: ["CRITICAL", "HIGH"]

# Orchestrator
orchestrator:
  max_workers: 4
  deduplication_strategy: "both" # location, content, both

# Reporting
report:
  formats: ["html", "json", "sarif"]
  output_dir: "security-reports"
  include_code_snippets: true

# Thresholds (CI/CD)
thresholds:
  fail_on_critical: true
  fail_on_high: false
```

## Environment Variables

All configuration options can be overridden with environment variables using the `SA_` prefix.

| Variable | Description | Default |
|----------|-------------|---------|
| `SA_BANDIT_ENABLED` | Enable Bandit scanner | `true` |
| `SA_SEMGREP_ENABLED` | Enable Semgrep scanner | `true` |
| `SA_TRIVY_ENABLED` | Enable Trivy scanner | `true` |
| `SA_FAIL_ON_CRITICAL` | Fail build on critical issues | `true` |
| `SA_FAIL_ON_HIGH` | Fail build on high issues | `false` |
| `SA_OUTPUT_DIR` | Report output directory | `security-reports` |
| `SA_MAX_WORKERS` | Parallel scanner threads | `3` |
