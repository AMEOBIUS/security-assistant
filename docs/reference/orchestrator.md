# Multi-Scanner Orchestration

The `ScanOrchestrator` enables running multiple security scanners in parallel and aggregating their results into a unified format.

## Features

- **Parallel Execution**: Run multiple scanners simultaneously for faster results
- **Result Aggregation**: Combine findings from different scanners
- **Intelligent Deduplication**: Remove duplicate findings using multiple strategies
- **Priority Scoring**: Automatically calculate priority scores (0-100) for findings
- **Unified Format**: Convert scanner-specific findings to a common format
- **GitLab Integration**: Convert findings to GitLab issues

## Supported Scanners

| Scanner | Languages | Focus | Speed |
|---------|-----------|-------|-------|
| **Bandit** | Python | Security vulnerabilities | Fast |
| **Semgrep** | 30+ languages | SAST, custom rules | Medium |
| **Trivy** | All (dependencies) | CVEs, secrets, misconfigs | Medium |

## Quick Start

```python
from security_assistant.orchestrator import ScanOrchestrator, ScannerType

# Initialize orchestrator
orchestrator = ScanOrchestrator(
    max_workers=3,              # Run 3 scanners in parallel
    enable_deduplication=True,  # Remove duplicates
    dedup_strategy="location"   # Deduplicate by file location
)

# Enable scanners
orchestrator.enable_scanner(ScannerType.BANDIT, min_severity="MEDIUM")
orchestrator.enable_scanner(ScannerType.SEMGREP, config="p/security-audit")
orchestrator.enable_scanner(ScannerType.TRIVY, min_severity=TrivySeverity.HIGH)

# Scan directory
result = orchestrator.scan_directory("src/", recursive=True)

# View results
print(f"Found {len(result.deduplicated_findings)} unique issues")
print(f"Critical: {result.critical_count}")
print(f"High: {result.high_count}")
```

## Architecture

### Unified Finding Format

All scanner findings are converted to a common `UnifiedFinding` format:

```python
@dataclass
class UnifiedFinding:
    finding_id: str              # Unique identifier
    scanner: ScannerType         # Which scanner found it
    severity: FindingSeverity    # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str                # security, secret, misconfig, etc.
    file_path: str               # File location
    line_start: int              # Start line
    line_end: int                # End line
    title: str                   # Finding title
    description: str             # Detailed description
    code_snippet: str            # Code context
    cwe_ids: List[str]           # CWE identifiers
    owasp_categories: List[str]  # OWASP categories
    references: List[str]        # External references
    fix_available: bool          # Fix available?
    fix_version: str             # Fixed version (if applicable)
    fix_guidance: str            # How to fix
    priority_score: float        # 0-100 priority score
    confidence: str              # HIGH, MEDIUM, LOW
```

### Orchestration Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    ScanOrchestrator                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │   Parallel Scanner Execution          │
        │   (ThreadPoolExecutor)                │
        └───────────────────────────────────────┘
                            │
        ┌───────────┬───────┴───────┬───────────┐
        ▼           ▼               ▼           ▼
    ┌───────┐  ┌─────────┐    ┌─────────┐  ┌──────┐
    │Bandit │  │ Semgrep │    │  Trivy  │  │ ...  │
    └───────┘  └─────────┘    └─────────┘  └──────┘
        │           │               │           │
        └───────────┴───────┬───────┴───────────┘
                            ▼
        ┌───────────────────────────────────────┐
        │   Convert to Unified Format           │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │   Deduplication                       │
        │   (location/content/both)             │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │   Priority Scoring                    │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │   OrchestrationResult                 │
        │   - Deduplicated findings             │
        │   - Statistics                        │
        │   - Top priority findings             │
        └───────────────────────────────────────┘
```

## Configuration

### Initialization Options

```python
orchestrator = ScanOrchestrator(
    max_workers=3,              # Parallel scanner threads (default: 3)
    enable_deduplication=True,  # Enable deduplication (default: True)
    dedup_strategy="location"   # Deduplication strategy (default: "location")
)
```

### Deduplication Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| `location` | Same file + line range | Different scanners finding same issue |
| `content` | Same title + code hash | Same issue at different locations |
| `both` | Either location OR content | Maximum deduplication |

### Scanner Configuration

Each scanner can be configured independently:

```python
# Bandit (Python)
orchestrator.enable_scanner(
    ScannerType.BANDIT,
    min_severity="MEDIUM",      # LOW, MEDIUM, HIGH
    min_confidence="HIGH",      # LOW, MEDIUM, HIGH
    exclude_dirs=["tests"]
)

# Semgrep (Multi-language)
orchestrator.enable_scanner(
    ScannerType.SEMGREP,
    min_severity="WARNING",     # INFO, WARNING, ERROR
    config="p/security-audit",  # Ruleset
    custom_rules=["custom.yml"]
)

# Trivy (Dependencies)
orchestrator.enable_scanner(
    ScannerType.TRIVY,
    min_severity=TrivySeverity.MEDIUM,
    scan_type=TrivyScanType.FILESYSTEM,
    skip_db_update=False
)
```

## Usage Examples

### Example 1: Basic Multi-Scanner Scan

```python
from security_assistant.orchestrator import ScanOrchestrator, ScannerType

orchestrator = ScanOrchestrator()
orchestrator.enable_scanner(ScannerType.BANDIT)
orchestrator.enable_scanner(ScannerType.SEMGREP, config="auto")

result = orchestrator.scan_directory("src/")

print(f"Findings: {len(result.deduplicated_findings)}")
print(f"Execution time: {result.execution_time_seconds:.2f}s")
```

### Example 2: Scan Single File

```python
result = orchestrator.scan_file("app.py")

for finding in result.deduplicated_findings:
    print(f"[{finding.severity.value}] {finding.title}")
    print(f"  Line {finding.line_start}: {finding.description}")
```

### Example 3: Top Priority Findings

```python
result = orchestrator.scan_directory("src/")

# Get top 10 priority findings
top_findings = result.top_priority_findings

for finding in top_findings:
    print(f"Priority: {finding.priority_score:.1f}/100")
    print(f"[{finding.severity.value}] {finding.title}")
    print(f"Scanner: {finding.scanner.value}")
    print()
```

### Example 4: Create GitLab Issues

```python
from security_assistant.gitlab_api import GitLabAPI

# Scan
result = orchestrator.scan_directory("src/")

# Convert to issues (top 20 priority)
issues = orchestrator.result_to_issues(
    result,
    project_name="MyProject",
    top_n=20
)

# Create in GitLab
gitlab = GitLabAPI(token="your-token", project_id="123")
for issue in issues:
    gitlab.create_issue(issue)
```

### Example 5: Custom Deduplication

```python
# Location-based (same file + lines)
orchestrator = ScanOrchestrator(dedup_strategy="location")
result1 = orchestrator.scan_directory("src/")

# Content-based (same title + code)
orchestrator = ScanOrchestrator(dedup_strategy="content")
result2 = orchestrator.scan_directory("src/")

# Both strategies
orchestrator = ScanOrchestrator(dedup_strategy="both")
result3 = orchestrator.scan_directory("src/")

print(f"Location: {len(result1.deduplicated_findings)} findings")
print(f"Content: {len(result2.deduplicated_findings)} findings")
print(f"Both: {len(result3.deduplicated_findings)} findings")
```

### Example 6: Filter by Severity

```python
result = orchestrator.scan_directory("src/")

# Get only critical and high severity
critical_high = [
    f for f in result.deduplicated_findings
    if f.severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH]
]

print(f"Critical/High: {len(critical_high)}")
```

## Priority Scoring

The orchestrator calculates a priority score (0-100) for each finding based on:

| Factor | Weight | Description |
|--------|--------|-------------|
| **Severity** | 40% | CRITICAL=100, HIGH=75, MEDIUM=50, LOW=25, INFO=10 |
| **Confidence** | 20% | HIGH=100, MEDIUM=70, LOW=40 |
| **Fix Available** | 20% | Has fix=100, No fix=0 |
| **CWE/OWASP** | 10% | Has CWE/OWASP=100, None=0 |
| **Category** | 10% | security=100, secret=100, misconfig=80, vulnerability=90 |

### Priority Score Examples

```python
# Critical + High Confidence + Fix + CWE = ~95/100
finding1 = UnifiedFinding(
    severity=FindingSeverity.CRITICAL,
    confidence="HIGH",
    fix_available=True,
    cwe_ids=["CWE-89"]
)

# Medium + Low Confidence + No Fix = ~35/100
finding2 = UnifiedFinding(
    severity=FindingSeverity.MEDIUM,
    confidence="LOW",
    fix_available=False
)
```

## Result Statistics

The `OrchestrationResult` provides comprehensive statistics:

```python
result = orchestrator.scan_directory("src/")

# Counts
print(f"Total findings: {result.total_findings}")
print(f"Unique findings: {len(result.deduplicated_findings)}")
print(f"Duplicates removed: {result.duplicates_removed}")

# By severity
print(f"Critical: {result.critical_count}")
print(f"High: {result.high_count}")
print(f"Medium: {result.medium_count}")
print(f"Low: {result.low_count}")

# By scanner
for scanner, count in result.findings_by_scanner.items():
    print(f"{scanner.value}: {count}")

# Performance
print(f"Execution time: {result.execution_time_seconds:.2f}s")

# Top priority
for finding in result.top_priority_findings[:5]:
    print(f"{finding.priority_score:.1f} - {finding.title}")
```

## Performance

### Parallel vs Sequential

```python
# Parallel (3 workers) - FAST
orchestrator = ScanOrchestrator(max_workers=3)
orchestrator.enable_scanner(ScannerType.BANDIT)
orchestrator.enable_scanner(ScannerType.SEMGREP)
orchestrator.enable_scanner(ScannerType.TRIVY)

result = orchestrator.scan_directory("large_project/")
# Time: ~30s (scanners run in parallel)

# Sequential (1 worker) - SLOW
orchestrator = ScanOrchestrator(max_workers=1)
# ... same scanners ...
result = orchestrator.scan_directory("large_project/")
# Time: ~80s (scanners run one by one)

# Speedup: 2.7x faster with parallel execution
```

### Optimization Tips

1. **Use appropriate severity filters**: Higher thresholds = faster scans
   ```python
   orchestrator.enable_scanner(ScannerType.BANDIT, min_severity="HIGH")
   ```

2. **Exclude unnecessary directories**:
   ```python
   orchestrator.enable_scanner(
       ScannerType.SEMGREP,
       exclude_dirs=["tests", "docs", "vendor"]
   )
   ```

3. **Use targeted rulesets**:
   ```python
   orchestrator.enable_scanner(
       ScannerType.SEMGREP,
       config="p/ci"  # Fast CI-optimized rules
   )
   ```

4. **Adjust worker count**:
   ```python
   # More workers = faster (up to number of scanners)
   orchestrator = ScanOrchestrator(max_workers=5)
   ```

## Error Handling

The orchestrator handles scanner failures gracefully:

```python
result = orchestrator.scan_directory("src/")

# Check for errors
if result.errors:
    print("Errors occurred:")
    for error in result.errors:
        print(f"  - {error}")

# Results from successful scanners are still available
print(f"Successful findings: {len(result.deduplicated_findings)}")
```

## Integration with CI/CD

### GitLab CI Example

```yaml
security_scan:
  stage: test
  script:
    - pip install -r requirements.txt
    - python -c "
      from security_assistant.orchestrator import ScanOrchestrator, ScannerType;
      orch = ScanOrchestrator();
      orch.enable_scanner(ScannerType.BANDIT);
      orch.enable_scanner(ScannerType.SEMGREP);
      result = orch.scan_directory('src/');
      exit(1 if result.has_critical_or_high else 0)
      "
  allow_failure: false
```

### GitHub Actions Example

```yaml
- name: Security Scan
  run: |
    python -c "
    from security_assistant.orchestrator import ScanOrchestrator, ScannerType
    orch = ScanOrchestrator()
    orch.enable_scanner(ScannerType.BANDIT)
    orch.enable_scanner(ScannerType.SEMGREP)
    result = orch.scan_directory('src/')
    if result.has_critical_or_high:
        print(f'Found {result.critical_count + result.high_count} critical/high issues')
        exit(1)
    "
```

## API Reference

### ScanOrchestrator

```python
class ScanOrchestrator:
    def __init__(
        self,
        max_workers: int = 3,
        enable_deduplication: bool = True,
        dedup_strategy: str = "location"
    )
    
    def enable_scanner(
        self,
        scanner_type: ScannerType,
        **scanner_kwargs
    ) -> None
    
    def disable_scanner(self, scanner_type: ScannerType) -> None
    
    def scan_directory(
        self,
        directory: str,
        recursive: bool = True
    ) -> OrchestrationResult
    
    def scan_file(self, file_path: str) -> OrchestrationResult
    
    def result_to_issues(
        self,
        result: OrchestrationResult,
        project_name: str,
        top_n: Optional[int] = None
    ) -> List[IssueData]
```

### OrchestrationResult

```python
@dataclass
class OrchestrationResult:
    all_findings: List[UnifiedFinding]
    deduplicated_findings: List[UnifiedFinding]
    scanner_results: Dict[ScannerType, Any]
    scan_time: datetime
    execution_time_seconds: float
    target: str
    total_findings: int
    findings_by_scanner: Dict[ScannerType, int]
    findings_by_severity: Dict[FindingSeverity, int]
    duplicates_removed: int
    errors: List[str]
    
    # Properties
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    has_critical_or_high: bool
    top_priority_findings: List[UnifiedFinding]
```

## Best Practices

1. **Start with high-severity filters** to reduce noise
2. **Use location-based deduplication** for most cases
3. **Enable all relevant scanners** for comprehensive coverage
4. **Review top priority findings first** (use `top_n` parameter)
5. **Adjust max_workers** based on available CPU cores
6. **Exclude test/vendor directories** for faster scans
7. **Use targeted rulesets** in CI/CD for speed

## Troubleshooting

### Issue: Slow scans

**Solution**: Increase `max_workers`, use higher severity filters, exclude directories

```python
orchestrator = ScanOrchestrator(max_workers=5)
orchestrator.enable_scanner(ScannerType.BANDIT, min_severity="HIGH")
```

### Issue: Too many duplicates

**Solution**: Use "both" deduplication strategy

```python
orchestrator = ScanOrchestrator(dedup_strategy="both")
```

### Issue: Scanner not found

**Solution**: Ensure scanner is installed

```bash
pip install bandit semgrep
# Trivy: https://aquasecurity.github.io/trivy/latest/getting-started/installation/
```

### Issue: Out of memory

**Solution**: Reduce `max_workers`, scan smaller directories

```python
orchestrator = ScanOrchestrator(max_workers=1)
```

## See Also

- [Bandit Scanner Guide](bandit_scanner.md)
- [Semgrep Scanner Guide](semgrep_scanner.md)
- [Trivy Scanner Guide](trivy_scanner.md)
- [GitLab Integration Guide](gitlab_integration.md)
