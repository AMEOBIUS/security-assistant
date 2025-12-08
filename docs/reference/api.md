# API Reference

Complete API documentation for programmatic usage of Security Assistant.

## Table of Contents

- [Core Classes](#core-classes)
- [Scanner API](#scanner-api)
- [Configuration API](#configuration-api)
- [Orchestrator API](#orchestrator-api)
- [Report Generator API](#report-generator-api)
- [GitLab API](#gitlab-api)
- [Models](#models)
- [Examples](#examples)

## Core Classes

### ScanOrchestrator

Main orchestrator for running security scans.

**Location**: `security_assistant/orchestrator.py`

**Constructor**:
```python
from security_assistant.orchestrator import ScanOrchestrator
from security_assistant.config import SecurityAssistantConfig

config = SecurityAssistantConfig.from_file("config.yaml")
orchestrator = ScanOrchestrator(config)
```

**Methods**:

#### `run_scan(target_path: str) -> List[Finding]`

Run security scan on target path.

**Parameters**:
- `target_path` (str): Path to scan (file or directory)

**Returns**:
- `List[Finding]`: List of security findings

**Raises**:
- `ValueError`: If target_path doesn't exist
- `RuntimeError`: If no scanners are enabled

**Example**:
```python
findings = orchestrator.run_scan("/path/to/code")
for finding in findings:
    print(f"{finding.severity}: {finding.title}")
```

#### `register_scanner(scanner: BaseScanner) -> None`

Register a custom scanner.

**Parameters**:
- `scanner` (BaseScanner): Scanner instance

**Example**:
```python
from my_scanner import MyScanner

orchestrator.register_scanner(MyScanner())
findings = orchestrator.run_scan("/path/to/code")
```

#### `get_enabled_scanners() -> List[BaseScanner]`

Get list of enabled scanners.

**Returns**:
- `List[BaseScanner]`: Enabled scanner instances

**Example**:
```python
scanners = orchestrator.get_enabled_scanners()
print(f"Enabled scanners: {[s.name for s in scanners]}")
```

## Scanner API

### BaseScanner

Abstract base class for all scanners.

**Location**: `security_assistant/scanners/base.py`

**Interface**:
```python
from abc import ABC, abstractmethod
from typing import List
from security_assistant.models import Finding

class BaseScanner(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Scanner name."""
        pass
    
    @abstractmethod
    def scan(self, target_path: str) -> List[Finding]:
        """Run scanner and return findings."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if scanner is installed."""
        pass
```

### BanditScanner

Python security scanner.

**Location**: `security_assistant/scanners/bandit_scanner.py`

**Constructor**:
```python
from security_assistant.scanners.bandit_scanner import BanditScanner

scanner = BanditScanner(
    exclude_dirs=["tests", "venv"],
    skips=["B101", "B404"],
    confidence_level="HIGH"
)
```

**Parameters**:
- `exclude_dirs` (List[str], optional): Directories to exclude
- `skips` (List[str], optional): Rule IDs to skip
- `confidence_level` (str, optional): Minimum confidence level

**Methods**:

#### `scan(target_path: str) -> List[Finding]`

Scan target with Bandit.

**Example**:
```python
findings = scanner.scan("/path/to/code")
```

#### `is_available() -> bool`

Check if Bandit is installed.

**Example**:
```python
if scanner.is_available():
    findings = scanner.scan("/path/to/code")
else:
    print("Bandit not installed")
```

### SemgrepScanner

Multi-language static analysis scanner.

**Location**: `security_assistant/scanners/semgrep_scanner.py`

**Constructor**:
```python
from security_assistant.scanners.semgrep_scanner import SemgrepScanner

scanner = SemgrepScanner(
    rules=["p/python", "p/security-audit"],
    exclude=["tests/", "venv/"],
    timeout=300
)
```

**Parameters**:
- `rules` (List[str], optional): Semgrep rulesets
- `exclude` (List[str], optional): Paths to exclude
- `timeout` (int, optional): Timeout in seconds

**Methods**:

#### `scan(target_path: str) -> List[Finding]`

Scan target with Semgrep.

**Example**:
```python
findings = scanner.scan("/path/to/code")
```

### TrivyScanner

Vulnerability and misconfiguration scanner.

**Location**: `security_assistant/scanners/trivy_scanner.py`

**Constructor**:
```python
from security_assistant.scanners.trivy_scanner import TrivyScanner

scanner = TrivyScanner(
    scanners=["vuln", "config", "secret"],
    severity=["CRITICAL", "HIGH"],
    timeout=600
)
```

**Parameters**:
- `scanners` (List[str], optional): Scanner types
- `severity` (List[str], optional): Severity levels to report
- `timeout` (int, optional): Timeout in seconds

**Methods**:

#### `scan(target_path: str) -> List[Finding]`

Scan target with Trivy.

**Example**:
```python
findings = scanner.scan("/path/to/code")
```

## Configuration API

### SecurityAssistantConfig

Main configuration class.

**Location**: `security_assistant/config.py`

**Constructor**:
```python
from security_assistant.config import SecurityAssistantConfig

config = SecurityAssistantConfig(
    scanners=ScannersConfig(...),
    orchestrator=OrchestratorConfig(...),
    report=ReportConfig(...),
    gitlab=GitLabConfig(...),
    thresholds=ThresholdConfig(...)
)
```

**Class Methods**:

#### `from_file(file_path: str) -> SecurityAssistantConfig`

Load configuration from file.

**Parameters**:
- `file_path` (str): Path to YAML or JSON file

**Returns**:
- `SecurityAssistantConfig`: Configuration object

**Raises**:
- `FileNotFoundError`: If file doesn't exist
- `ValueError`: If file format is invalid

**Example**:
```python
config = SecurityAssistantConfig.from_file("config.yaml")
```

#### `from_env() -> SecurityAssistantConfig`

Load configuration from environment variables.

**Returns**:
- `SecurityAssistantConfig`: Configuration object

**Example**:
```python
import os
os.environ['SA_BANDIT_ENABLED'] = 'true'
os.environ['SA_SEMGREP_ENABLED'] = 'false'

config = SecurityAssistantConfig.from_env()
```

#### `from_dict(data: dict) -> SecurityAssistantConfig`

Load configuration from dictionary.

**Parameters**:
- `data` (dict): Configuration dictionary

**Returns**:
- `SecurityAssistantConfig`: Configuration object

**Example**:
```python
config = SecurityAssistantConfig.from_dict({
    'scanners': {
        'bandit': {'enabled': True},
        'semgrep': {'enabled': True},
        'trivy': {'enabled': False}
    }
})
```

**Instance Methods**:

#### `merge(other: SecurityAssistantConfig) -> SecurityAssistantConfig`

Merge with another configuration.

**Parameters**:
- `other` (SecurityAssistantConfig): Configuration to merge

**Returns**:
- `SecurityAssistantConfig`: Merged configuration

**Example**:
```python
base_config = SecurityAssistantConfig.from_file("base.yaml")
override_config = SecurityAssistantConfig.from_file("override.yaml")
merged = base_config.merge(override_config)
```

#### `validate() -> None`

Validate configuration.

**Raises**:
- `ValueError`: If configuration is invalid

**Example**:
```python
config = SecurityAssistantConfig.from_file("config.yaml")
config.validate()  # Raises ValueError if invalid
```

#### `to_dict() -> dict`

Convert to dictionary.

**Returns**:
- `dict`: Configuration as dictionary

**Example**:
```python
config_dict = config.to_dict()
print(json.dumps(config_dict, indent=2))
```

## Orchestrator API

### Deduplication Strategies

**Location**: `security_assistant/orchestrator.py`

#### `strict_deduplication(findings: List[Finding]) -> List[Finding]`

Exact match deduplication.

**Parameters**:
- `findings` (List[Finding]): Findings to deduplicate

**Returns**:
- `List[Finding]`: Deduplicated findings

**Example**:
```python
from security_assistant.orchestrator import strict_deduplication

unique_findings = strict_deduplication(findings)
```

#### `fuzzy_deduplication(findings: List[Finding]) -> List[Finding]`

Fuzzy match deduplication.

**Example**:
```python
from security_assistant.orchestrator import fuzzy_deduplication

unique_findings = fuzzy_deduplication(findings)
```

#### `location_deduplication(findings: List[Finding]) -> List[Finding]`

Location-based deduplication.

**Example**:
```python
from security_assistant.orchestrator import location_deduplication

unique_findings = location_deduplication(findings)
```

## Report Generator API

### ReportGenerator

Generate reports in multiple formats.

**Location**: `security_assistant/report_generator.py`

**Constructor**:
```python
from security_assistant.report_generator import ReportGenerator

generator = ReportGenerator(output_dir="security-reports")
```

**Parameters**:
- `output_dir` (str, optional): Output directory for reports

**Methods**:

#### `generate_html(findings: List[Finding], output_file: str = None) -> str`

Generate HTML report.

**Parameters**:
- `findings` (List[Finding]): Findings to report
- `output_file` (str, optional): Output file path

**Returns**:
- `str`: HTML content

**Example**:
```python
html = generator.generate_html(findings, "security_report.html")
```

#### `generate_json(findings: List[Finding], output_file: str = None) -> str`

Generate JSON report.

**Example**:
```python
json_content = generator.generate_json(findings, "security_report.json")
```

#### `generate_markdown(findings: List[Finding], output_file: str = None) -> str`

Generate Markdown report.

**Example**:
```python
markdown = generator.generate_markdown(findings, "security_report.md")
```

#### `generate_sarif(findings: List[Finding], output_file: str = None) -> str`

Generate SARIF report (GitHub Security).

**Example**:
```python
sarif = generator.generate_sarif(findings, "security-report.sarif")
```

#### `generate_gitlab_sast(findings: List[Finding], output_file: str = None) -> str`

Generate GitLab SAST report.

**Example**:
```python
gitlab_sast = generator.generate_gitlab_sast(findings, "gl-sast-report.json")
```

## GitLab API

### GitLabAPI

Interact with GitLab API.

**Location**: `security_assistant/gitlab_api.py`

**Constructor**:
```python
from security_assistant.gitlab_api import GitLabAPI

api = GitLabAPI(
    url="https://gitlab.com",
    token="glpat-...",
    project_id=12345
)
```

**Parameters**:
- `url` (str): GitLab instance URL
- `token` (str): Personal access token
- `project_id` (int): Project ID

**Methods**:

#### `create_issue(finding: Finding, **kwargs) -> dict`

Create GitLab issue from finding.

**Parameters**:
- `finding` (Finding): Security finding
- `**kwargs`: Additional issue parameters

**Returns**:
- `dict`: Created issue data

**Example**:
```python
issue = api.create_issue(
    finding,
    assignee_ids=[12345],
    labels=["security", "critical"],
    confidential=True
)
print(f"Created issue: {issue['web_url']}")
```

#### `get_existing_issues(labels: List[str] = None) -> List[dict]`

Get existing issues.

**Parameters**:
- `labels` (List[str], optional): Filter by labels

**Returns**:
- `List[dict]`: List of issues

**Example**:
```python
issues = api.get_existing_issues(labels=["security-scan"])
print(f"Found {len(issues)} existing issues")
```

#### `update_issue(issue_id: int, **kwargs) -> dict`

Update existing issue.

**Parameters**:
- `issue_id` (int): Issue ID
- `**kwargs`: Fields to update

**Returns**:
- `dict`: Updated issue data

**Example**:
```python
updated = api.update_issue(
    issue_id=123,
    state_event="close",
    labels=["security", "resolved"]
)
```

#### `add_issue_comment(issue_id: int, comment: str) -> dict`

Add comment to issue.

**Parameters**:
- `issue_id` (int): Issue ID
- `comment` (str): Comment text

**Returns**:
- `dict`: Created comment data

**Example**:
```python
comment = api.add_issue_comment(
    issue_id=123,
    comment="Fixed in commit abc123"
)
```

## Models

### Finding

Security finding model.

**Location**: `security_assistant/models.py`

**Attributes**:
```python
@dataclass
class Finding:
    scanner: str           # Scanner name
    severity: str          # CRITICAL, HIGH, MEDIUM, LOW, INFO
    title: str             # Short description
    description: str       # Detailed description
    file_path: str         # Relative file path
    line_number: int       # Line number (0 if N/A)
    rule_id: str           # Scanner-specific rule ID
    cwe_id: Optional[str]  # CWE identifier
    confidence: str        # HIGH, MEDIUM, LOW
    remediation: str       # How to fix
```

**Methods**:

#### `to_dict() -> dict`

Convert to dictionary.

**Example**:
```python
finding_dict = finding.to_dict()
```

#### `from_dict(data: dict) -> Finding`

Create from dictionary.

**Example**:
```python
finding = Finding.from_dict({
    'scanner': 'bandit',
    'severity': 'HIGH',
    'title': 'SQL Injection',
    # ... other fields
})
```

#### `__str__() -> str`

String representation.

**Example**:
```python
print(finding)
# Output: [HIGH] SQL Injection (bandit:B608)
```

## Examples

### Basic Scan

```python
from security_assistant.orchestrator import ScanOrchestrator
from security_assistant.config import SecurityAssistantConfig

# Load configuration
config = SecurityAssistantConfig.from_file("config.yaml")

# Create orchestrator
orchestrator = ScanOrchestrator(config)

# Run scan
findings = orchestrator.run_scan("/path/to/code")

# Print results
for finding in findings:
    print(f"[{finding.severity}] {finding.title}")
    print(f"  File: {finding.file_path}:{finding.line_number}")
    print(f"  Scanner: {finding.scanner}")
    print()
```

### Custom Scanner

```python
from security_assistant.scanners.base import BaseScanner
from security_assistant.models import Finding
from typing import List
import subprocess
import json

class MyScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "my-scanner"
    
    def scan(self, target_path: str) -> List[Finding]:
        # Execute scanner
        result = subprocess.run(
            ['my-scanner', '--json', target_path],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse output
        data = json.loads(result.stdout)
        
        # Convert to Finding objects
        findings = []
        for item in data['results']:
            findings.append(Finding(
                scanner=self.name,
                severity=item['severity'],
                title=item['title'],
                description=item['description'],
                file_path=item['file'],
                line_number=item['line'],
                rule_id=item['rule_id'],
                confidence='HIGH',
                remediation=item['fix']
            ))
        
        return findings
    
    def is_available(self) -> bool:
        import shutil
        return shutil.which('my-scanner') is not None

# Use custom scanner
orchestrator = ScanOrchestrator(config)
orchestrator.register_scanner(MyScanner())
findings = orchestrator.run_scan("/path/to/code")
```

### Generate Multiple Reports

```python
from security_assistant.report_generator import ReportGenerator

generator = ReportGenerator(output_dir="reports")

# Generate all formats
html = generator.generate_html(findings, "security_report.html")
json_report = generator.generate_json(findings, "security_report.json")
markdown = generator.generate_markdown(findings, "security_report.md")
sarif = generator.generate_sarif(findings, "security-report.sarif")
gitlab_sast = generator.generate_gitlab_sast(findings, "gl-sast-report.json")

print("Reports generated:")
print("- security_report.html")
print("- security_report.json")
print("- security_report.md")
print("- security-report.sarif")
print("- gl-sast-report.json")
```

### Create GitLab Issues

```python
from security_assistant.gitlab_api import GitLabAPI

api = GitLabAPI(
    url="https://gitlab.com",
    token=os.environ['GITLAB_TOKEN'],
    project_id=12345
)

# Filter high and critical findings
critical_findings = [
    f for f in findings
    if f.severity in ['CRITICAL', 'HIGH']
]

# Create issues
for finding in critical_findings:
    issue = api.create_issue(
        finding,
        labels=['security', 'automated', finding.severity.lower()],
        assignee_ids=[67890],
        confidential=(finding.severity == 'CRITICAL')
    )
    print(f"Created issue: {issue['web_url']}")
```

### Configuration Merging

```python
# Load base configuration
base_config = SecurityAssistantConfig.from_file("config/base.yaml")

# Load environment-specific overrides
env_config = SecurityAssistantConfig.from_file(f"config/{env}.yaml")

# Merge configurations
config = base_config.merge(env_config)

# Override with environment variables
config = config.merge_from_env()

# Validate
config.validate()

# Use merged configuration
orchestrator = ScanOrchestrator(config)
findings = orchestrator.run_scan("/path/to/code")
```

### Filtering Findings

```python
# Filter by severity
critical_findings = [f for f in findings if f.severity == 'CRITICAL']
high_findings = [f for f in findings if f.severity == 'HIGH']

# Filter by scanner
bandit_findings = [f for f in findings if f.scanner == 'bandit']
semgrep_findings = [f for f in findings if f.scanner == 'semgrep']

# Filter by file
auth_findings = [f for f in findings if 'auth' in f.file_path]

# Filter by CWE
sql_injection = [f for f in findings if f.cwe_id == 'CWE-89']

# Combine filters
critical_auth_findings = [
    f for f in findings
    if f.severity == 'CRITICAL' and 'auth' in f.file_path
]
```

### Error Handling

```python
from security_assistant.orchestrator import ScanOrchestrator
from security_assistant.config import SecurityAssistantConfig

try:
    # Load configuration
    config = SecurityAssistantConfig.from_file("config.yaml")
    config.validate()
    
    # Run scan
    orchestrator = ScanOrchestrator(config)
    findings = orchestrator.run_scan("/path/to/code")
    
    # Generate reports
    generator = ReportGenerator()
    generator.generate_html(findings)
    
except FileNotFoundError as e:
    print(f"Configuration file not found: {e}")
except ValueError as e:
    print(f"Invalid configuration: {e}")
except RuntimeError as e:
    print(f"Scan failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
    raise
```

## Type Hints

All APIs use type hints for better IDE support:

```python
from typing import List, Optional, Dict, Any
from security_assistant.models import Finding
from security_assistant.config import SecurityAssistantConfig

def process_findings(
    findings: List[Finding],
    severity_filter: Optional[str] = None,
    scanner_filter: Optional[str] = None
) -> Dict[str, Any]:
    """Process findings with optional filters."""
    filtered = findings
    
    if severity_filter:
        filtered = [f for f in filtered if f.severity == severity_filter]
    
    if scanner_filter:
        filtered = [f for f in filtered if f.scanner == scanner_filter]
    
    return {
        'total': len(filtered),
        'findings': filtered,
        'by_severity': group_by_severity(filtered),
    }
```

## See Also

- [CLI Reference](cli-reference.md) - Command-line interface
- [Configuration Guide](configuration.md) - Configuration options
- [Examples](../examples/) - More code examples
