# Architecture Guide

System design and components of Security Assistant.

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Design Decisions](#design-decisions)
- [Extension Points](#extension-points)

## Overview

Security Assistant is a modular security scanning orchestrator designed to:
- Integrate multiple security scanners
- Deduplicate findings across scanners
- Generate reports in multiple formats
- Create GitLab issues automatically
- Integrate with CI/CD pipelines

### Key Principles

1. **Modularity**: Each scanner is independent
2. **Extensibility**: Easy to add new scanners
3. **Configurability**: Flexible configuration system
4. **Performance**: Parallel execution
5. **Reliability**: Comprehensive error handling

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Security Assistant                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    Configuration Layer                      │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │ │
│  │  │   YAML   │  │   JSON   │  │   ENV    │  │ Defaults │  │ │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │ │
│  │       └──────────────┴──────────────┴─────────────┘        │ │
│  │                          │                                  │ │
│  │                   ┌──────▼──────┐                          │ │
│  │                   │   Config    │                          │ │
│  │                   │   Manager   │                          │ │
│  │                   └──────┬──────┘                          │ │
│  └──────────────────────────┼─────────────────────────────────┘ │
│                             │                                    │
│  ┌──────────────────────────▼─────────────────────────────────┐ │
│  │                     Scanner Layer                           │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │ │
│  │  │    Bandit    │  │   Semgrep    │  │    Trivy     │     │ │
│  │  │   Scanner    │  │   Scanner    │  │   Scanner    │     │ │
│  │  │              │  │              │  │              │     │ │
│  │  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │     │ │
│  │  │ │  Bandit  │ │  │ │ Semgrep  │ │  │ │  Trivy   │ │     │ │
│  │  │ │   CLI    │ │  │ │   CLI    │ │  │ │   CLI    │ │     │ │
│  │  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │     │ │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │ │
│  │         │                  │                  │             │ │
│  │         └──────────────────┼──────────────────┘             │ │
│  └────────────────────────────┼────────────────────────────────┘ │
│                               │                                   │
│  ┌────────────────────────────▼────────────────────────────────┐ │
│  │                   Orchestration Layer                        │ │
│  │                                                              │ │
│  │  ┌──────────────────────────────────────────────────────┐  │ │
│  │  │              Scan Orchestrator                        │  │ │
│  │  │                                                       │  │ │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │ │
│  │  │  │  Parallel   │  │ Deduplication│  │ Priority    │  │  │ │
│  │  │  │  Execution  │  │   Engine     │  │  Mapping    │  │  │ │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │ │
│  │  │                                                       │  │ │
│  │  └───────────────────────┬───────────────────────────────┘  │ │
│  └──────────────────────────┼──────────────────────────────────┘ │
│                             │                                     │
│  ┌──────────────────────────▼──────────────────────────────────┐ │
│  │                     Output Layer                             │ │
│  │                                                              │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │ │
│  │  │   Report     │  │    GitLab    │  │     CLI      │     │ │
│  │  │  Generator   │  │     API      │  │   Interface  │     │ │
│  │  │              │  │              │  │              │     │ │
│  │  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │     │ │
│  │  │ │   HTML   │ │  │ │  Issues  │ │  │ │ Commands │ │     │ │
│  │  │ │   JSON   │ │  │ │  Labels  │ │  │ │  Args    │ │     │ │
│  │  │ │ Markdown │ │  │ │ Assignee │ │  │ │  Output  │ │     │ │
│  │  │ │  SARIF   │ │  │ └──────────┘ │  │ └──────────┘ │     │ │
│  │  │ │ GitLab   │ │  │              │  │              │     │ │
│  │  │ └──────────┘ │  │              │  │              │     │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘     │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## Component Details

### Configuration Layer

**Purpose**: Manage configuration from multiple sources with priority merging.

**Components**:

1. **Config Manager** (`security_assistant/config.py`)
   - Loads configuration from files (YAML/JSON)
   - Reads environment variables
   - Merges configurations with priority
   - Validates configuration values

2. **Configuration Classes**:
   ```python
   @dataclass
   class SecurityAssistantConfig:
       scanners: ScannersConfig
       orchestrator: OrchestratorConfig
       report: ReportConfig
       gitlab: GitLabConfig
       thresholds: ThresholdConfig
   ```

**Priority Order**:
1. Environment variables (highest)
2. Configuration file
3. Default values (lowest)

**Example**:
```python
# Load from file
config = SecurityAssistantConfig.from_file("config.yaml")

# Override with environment
config = config.merge_from_env()

# Validate
config.validate()
```

### Scanner Layer

**Purpose**: Execute security scanners and normalize output.

**Base Interface** (`security_assistant/scanners/base.py`):
```python
class BaseScanner(ABC):
    @abstractmethod
    def scan(self, target_path: str) -> List[Finding]:
        """Run scanner and return findings."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if scanner is installed."""
        pass
```

**Implementations**:

1. **Bandit Scanner** (`security_assistant/scanners/bandit_scanner.py`)
   - Executes: `bandit -r -f json <target>`
   - Parses: JSON output
   - Maps: Severity (LOW/MEDIUM/HIGH → Finding.severity)
   - Returns: List[Finding]

2. **Semgrep Scanner** (`security_assistant/scanners/semgrep_scanner.py`)
   - Executes: `semgrep --config <rules> --json <target>`
   - Parses: JSON output
   - Maps: Severity (INFO/WARNING/ERROR → Finding.severity)
   - Returns: List[Finding]

3. **Trivy Scanner** (`security_assistant/scanners/trivy_scanner.py`)
   - Executes: `trivy fs --format json <target>`
   - Parses: JSON output
   - Maps: Severity (LOW/MEDIUM/HIGH/CRITICAL → Finding.severity)
   - Returns: List[Finding]

**Finding Model** (`security_assistant/models.py`):
```python
@dataclass
class Finding:
    scanner: str           # "bandit", "semgrep", "trivy"
    severity: str          # "CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"
    title: str             # Short description
    description: str       # Detailed description
    file_path: str         # Relative path to file
    line_number: int       # Line number (0 if not applicable)
    rule_id: str           # Scanner-specific rule ID
    cwe_id: Optional[str]  # CWE identifier
    confidence: str        # "HIGH", "MEDIUM", "LOW"
    remediation: str       # How to fix
```

### Orchestration Layer

**Purpose**: Coordinate scanner execution, deduplicate findings, and prioritize results.

**Scan Orchestrator** (`security_assistant/orchestrator.py`):

1. **Parallel Execution**:
   ```python
   def run_scan(self, target_path: str) -> List[Finding]:
       with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
           futures = {
               executor.submit(scanner.scan, target_path): scanner
               for scanner in self.enabled_scanners
           }
           
           all_findings = []
           for future in as_completed(futures):
               findings = future.result()
               all_findings.extend(findings)
       
       return self._deduplicate_findings(all_findings)
   ```

2. **Deduplication Strategies**:

   **Strict** - Exact match:
   ```python
   def _strict_dedup(self, findings: List[Finding]) -> List[Finding]:
       seen = set()
       unique = []
       for finding in findings:
           key = (finding.file_path, finding.line_number, finding.rule_id)
           if key not in seen:
               seen.add(key)
               unique.append(finding)
       return unique
   ```

   **Fuzzy** - Similar message and location:
   ```python
   def _fuzzy_dedup(self, findings: List[Finding]) -> List[Finding]:
       unique = []
       for finding in findings:
           if not any(self._is_similar(finding, f) for f in unique):
               unique.append(finding)
       return unique
   
   def _is_similar(self, f1: Finding, f2: Finding) -> bool:
       return (
           f1.file_path == f2.file_path and
           abs(f1.line_number - f2.line_number) <= 2 and
           self._text_similarity(f1.title, f2.title) > 0.8
       )
   ```

   **Location-based** - Same file and line:
   ```python
   def _location_dedup(self, findings: List[Finding]) -> List[Finding]:
       seen = set()
       unique = []
       for finding in findings:
           key = (finding.file_path, finding.line_number)
           if key not in seen:
               seen.add(key)
               unique.append(finding)
       return unique
   ```

3. **Priority Mapping**:
   ```python
   SEVERITY_PRIORITY = {
       "CRITICAL": 1,
       "HIGH": 2,
       "MEDIUM": 3,
       "LOW": 4,
       "INFO": 5,
   }
   
   def prioritize_findings(self, findings: List[Finding]) -> List[Finding]:
       return sorted(findings, key=lambda f: SEVERITY_PRIORITY[f.severity])
   ```

### Output Layer

**Purpose**: Generate reports and create GitLab issues.

**Components**:

1. **Report Generator** (`security_assistant/report_generator.py`)

   **HTML Report**:
   ```python
   def generate_html(self, findings: List[Finding]) -> str:
       template = self._load_template("report.html.j2")
       return template.render(
           findings=findings,
           summary=self._calculate_summary(findings),
           timestamp=datetime.now(),
       )
   ```

   **JSON Report**:
   ```python
   def generate_json(self, findings: List[Finding]) -> str:
       return json.dumps({
           "version": "1.0",
           "findings": [f.to_dict() for f in findings],
           "summary": self._calculate_summary(findings),
       }, indent=2)
   ```

   **SARIF Report** (GitHub Security):
   ```python
   def generate_sarif(self, findings: List[Finding]) -> str:
       return json.dumps({
           "version": "2.1.0",
           "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
           "runs": [{
               "tool": {"driver": {"name": "Security Assistant"}},
               "results": [self._to_sarif_result(f) for f in findings],
           }]
       })
   ```

   **GitLab SAST Report**:
   ```python
   def generate_gitlab_sast(self, findings: List[Finding]) -> str:
       return json.dumps({
           "version": "15.0.0",
           "vulnerabilities": [
               self._to_gitlab_vulnerability(f) for f in findings
           ],
       })
   ```

2. **GitLab API** (`security_assistant/gitlab_api.py`)

   **Create Issue**:
   ```python
   def create_issue(self, finding: Finding) -> dict:
       return self.client.projects.get(self.project_id).issues.create({
           'title': f'[{finding.severity}] {finding.title}',
           'description': self._format_description(finding),
           'labels': self._get_labels(finding),
           'assignee_ids': self.default_assignee_ids,
           'confidential': finding.severity == 'CRITICAL',
       })
   ```

   **Check Existing Issues**:
   ```python
   def get_existing_issues(self, labels: List[str]) -> List[dict]:
       return self.client.projects.get(self.project_id).issues.list(
           labels=labels,
           state='opened',
       )
   ```

3. **CLI Interface** (`security_assistant/cli.py`)

   **Commands**:
   - `scan`: Run security scan
   - `config`: Manage configuration
   - `report`: Generate reports

   **Example**:
   ```python
   @click.command()
   @click.argument('target', type=click.Path(exists=True))
   @click.option('--format', multiple=True, default=['html'])
   @click.option('--create-issues', is_flag=True)
   def scan(target, format, create_issues):
       config = load_config()
       orchestrator = ScanOrchestrator(config)
       findings = orchestrator.run_scan(target)
       
       for fmt in format:
           generate_report(findings, fmt)
       
       if create_issues:
           create_gitlab_issues(findings)
   ```

## Data Flow

### Scan Execution Flow

```
1. CLI/API Call
   ↓
2. Load Configuration
   - Read config file
   - Merge environment variables
   - Validate
   ↓
3. Initialize Orchestrator
   - Create scanner instances
   - Configure deduplication
   - Set up thread pool
   ↓
4. Execute Scanners (Parallel)
   ├─→ Bandit Scanner
   │   ├─ Execute: bandit -r -f json <target>
   │   ├─ Parse JSON output
   │   └─ Return List[Finding]
   │
   ├─→ Semgrep Scanner
   │   ├─ Execute: semgrep --json <target>
   │   ├─ Parse JSON output
   │   └─ Return List[Finding]
   │
   └─→ Trivy Scanner
       ├─ Execute: trivy fs --format json <target>
       ├─ Parse JSON output
       └─ Return List[Finding]
   ↓
5. Collect Results
   - Wait for all scanners
   - Combine findings
   ↓
6. Deduplicate Findings
   - Apply deduplication strategy
   - Remove duplicates
   ↓
7. Prioritize Findings
   - Sort by severity
   - Apply filters
   ↓
8. Generate Outputs
   ├─→ HTML Report
   ├─→ JSON Report
   ├─→ Markdown Report
   ├─→ SARIF Report
   └─→ GitLab SAST Report
   ↓
9. Create GitLab Issues (Optional)
   - Filter by priority threshold
   - Check existing issues
   - Create new issues
   ↓
10. Return Results
    - Exit code (0=success, 1=findings, 2=error)
    - Report files
    - GitLab issue URLs
```

### Configuration Loading Flow

```
1. Start
   ↓
2. Check for --config flag
   ├─ Yes → Load specified file
   └─ No → Check default locations
       ├─ ./security-assistant.yaml
       ├─ ./config/security-assistant.yaml
       └─ ~/.security-assistant.yaml
   ↓
3. Parse Configuration File
   - YAML or JSON
   - Validate syntax
   ↓
4. Load Environment Variables
   - Read SA_* variables
   - Parse values
   ↓
5. Merge Configurations
   - Environment overrides file
   - File overrides defaults
   ↓
6. Validate Configuration
   - Check required fields
   - Validate value ranges
   - Check scanner availability
   ↓
7. Return Config Object
```

## Design Decisions

### Why Dataclasses for Configuration?

**Pros**:
- Type safety
- IDE autocomplete
- Validation
- Immutability (frozen=True)

**Cons**:
- More verbose than dicts
- Requires Python 3.7+

**Decision**: Use dataclasses for type safety and validation.

### Why ThreadPoolExecutor for Parallel Execution?

**Alternatives considered**:
- `multiprocessing.Pool`: Overhead of process creation
- `asyncio`: Scanners are subprocess-based (blocking I/O)
- Sequential: Too slow

**Decision**: ThreadPoolExecutor balances performance and simplicity.

### Why Multiple Deduplication Strategies?

**Rationale**:
- Different use cases need different trade-offs
- Strict: Compliance, audits
- Fuzzy: General purpose
- Location: Quick scans

**Decision**: Provide all three, default to fuzzy.

### Why Normalize to Common Finding Model?

**Alternatives**:
- Keep scanner-specific formats
- Use scanner output directly

**Pros of normalization**:
- Consistent deduplication
- Unified reporting
- Easy to add scanners

**Decision**: Normalize to common model.

### Why Support Multiple Report Formats?

**Rationale**:
- HTML: Human review
- JSON: Automation
- SARIF: GitHub integration
- GitLab SAST: GitLab integration
- Markdown: Documentation

**Decision**: Support all common formats.

## Extension Points

### Adding a New Scanner

1. **Implement BaseScanner**:
```python
from security_assistant.scanners.base import BaseScanner
from security_assistant.models import Finding

class MyScanner(BaseScanner):
    def scan(self, target_path: str) -> List[Finding]:
        # Execute scanner
        result = subprocess.run(
            ['my-scanner', target_path],
            capture_output=True,
            text=True,
        )
        
        # Parse output
        data = json.loads(result.stdout)
        
        # Convert to Finding objects
        findings = []
        for item in data['results']:
            findings.append(Finding(
                scanner='my-scanner',
                severity=self._map_severity(item['severity']),
                title=item['title'],
                description=item['description'],
                file_path=item['file'],
                line_number=item['line'],
                rule_id=item['rule_id'],
                confidence='HIGH',
                remediation=item['fix'],
            ))
        
        return findings
    
    def is_available(self) -> bool:
        return shutil.which('my-scanner') is not None
```

2. **Register in Orchestrator**:
```python
from security_assistant.orchestrator import ScanOrchestrator
from my_scanner import MyScanner

orchestrator = ScanOrchestrator(config)
orchestrator.register_scanner(MyScanner())
```

### Adding a New Report Format

1. **Implement Generator**:
```python
class MyReportGenerator:
    def generate(self, findings: List[Finding]) -> str:
        # Your format logic
        return formatted_output
```

2. **Register in ReportGenerator**:
```python
from security_assistant.report_generator import ReportGenerator

class ExtendedReportGenerator(ReportGenerator):
    def generate_my_format(self, findings: List[Finding]) -> str:
        generator = MyReportGenerator()
        return generator.generate(findings)
```

### Adding a New Deduplication Strategy

1. **Implement Strategy**:
```python
def my_dedup_strategy(findings: List[Finding]) -> List[Finding]:
    # Your deduplication logic
    return unique_findings
```

2. **Register in Orchestrator**:
```python
class ExtendedOrchestrator(ScanOrchestrator):
    DEDUP_STRATEGIES = {
        **ScanOrchestrator.DEDUP_STRATEGIES,
        'my-strategy': my_dedup_strategy,
    }
```

### Adding a New Issue Tracker Integration

1. **Implement Adapter**:
```python
class JiraAdapter:
    def __init__(self, url: str, token: str, project_key: str):
        self.client = JIRA(url, token=token)
        self.project_key = project_key
    
    def create_issue(self, finding: Finding) -> dict:
        return self.client.create_issue(
            project=self.project_key,
            summary=finding.title,
            description=finding.description,
            issuetype={'name': 'Bug'},
            labels=[finding.severity.lower(), 'security'],
        )
```

2. **Use in Workflow**:
```python
from jira_adapter import JiraAdapter

jira = JiraAdapter(url, token, project_key)
for finding in findings:
    if finding.severity in ['CRITICAL', 'HIGH']:
        jira.create_issue(finding)
```

## Performance Characteristics

### Time Complexity

- **Scanner execution**: O(n) where n = number of files
- **Deduplication**: O(m²) where m = number of findings (worst case)
- **Report generation**: O(m) where m = number of findings

### Space Complexity

- **Findings storage**: O(m) where m = number of findings
- **Report generation**: O(m) for in-memory representation

### Typical Performance

**Small project** (< 1,000 files):
- Scan time: 1-2 minutes
- Memory: 200-500 MB

**Medium project** (1,000-10,000 files):
- Scan time: 5-10 minutes
- Memory: 500 MB - 1 GB

**Large project** (> 10,000 files):
- Scan time: 15-30 minutes
- Memory: 1-2 GB

## Security Considerations

### Token Storage

- Never commit tokens to version control
- Use environment variables or CI/CD secrets
- Rotate tokens regularly

### Scanner Execution

- Scanners run as subprocesses
- No shell injection (shell=False)
- Timeout protection
- Error handling

### Report Generation

- Sanitize file paths in reports
- Escape HTML in reports
- Validate JSON/YAML output

### GitLab API

- Use HTTPS only
- Validate SSL certificates
- Rate limiting
- Error handling

## Future Enhancements

### Planned Features

1. **Plugin System**: Dynamic scanner loading
2. **Web UI**: Browser-based interface
3. **Database Storage**: Persistent finding storage
4. **Trend Analysis**: Historical comparison
5. **Custom Rules**: User-defined security rules
6. **Webhook Integration**: Real-time notifications
7. **SBOM Generation**: Software Bill of Materials
8. **License Scanning**: License compliance checking

### Scalability Improvements

1. **Distributed Scanning**: Multiple workers
2. **Incremental Scanning**: Only changed files
3. **Caching**: Cache scanner results
4. **Streaming**: Process findings as they arrive

## Summary

Security Assistant is designed with:
- **Modularity**: Independent components
- **Extensibility**: Easy to add features
- **Performance**: Parallel execution
- **Reliability**: Comprehensive error handling
- **Flexibility**: Multiple configuration options

The architecture supports current needs while allowing for future growth.
