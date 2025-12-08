# Security Scanners

Production-ready security scanner integrations for Python code analysis.

## Overview

This package provides integrations with popular security scanning tools, converting their findings into GitLab issues automatically.

## Available Scanners

### ✅ Bandit Scanner (Session 3)
**Status:** Production-ready  
**Language:** Python  
**Focus:** Security vulnerabilities

**Features:**
- Scan files and directories
- Filter by severity and confidence
- Rich GitLab issue creation
- CWE mapping
- Comprehensive error handling

**Quick Start:**
```python
from security_assistant.scanners import BanditScanner

scanner = BanditScanner(min_severity="MEDIUM")
result = scanner.scan_file("app.py")

for finding in result.findings:
    print(f"{finding.severity_emoji} {finding.test_name}")
```

### ⏭️ Semgrep Scanner (Session 4)
**Status:** Planned  
**Language:** Multi-language (Python, JS, Go, etc.)  
**Focus:** Custom security rules

### ⏭️ Safety Scanner (Session 5)
**Status:** Planned  
**Language:** Python dependencies  
**Focus:** Known vulnerabilities in packages

## Architecture

### Data Models

**BanditFinding**
```python
@dataclass
class BanditFinding:
    test_id: str          # e.g., "B105"
    test_name: str        # e.g., "hardcoded_password"
    severity: str         # HIGH, MEDIUM, LOW
    confidence: str       # HIGH, MEDIUM, LOW
    issue_text: str       # Description
    filename: str         # File path
    line_number: int      # Line number
    code: str            # Code snippet
    cwe_id: Optional[str] # CWE identifier
    more_info: Optional[str] # Documentation link
```

**ScanResult**
```python
@dataclass
class ScanResult:
    findings: List[BanditFinding]
    scan_time: datetime
    files_scanned: int
    lines_scanned: int
    errors: List[str]
```

### Scanner Interface

All scanners follow a consistent interface:

```python
class Scanner:
    def __init__(self, min_severity: str, min_confidence: str):
        """Initialize scanner with filters."""
        
    def scan_file(self, file_path: str) -> ScanResult:
        """Scan a single file."""
        
    def scan_directory(self, directory_path: str, recursive: bool) -> ScanResult:
        """Scan a directory."""
        
    def finding_to_issue(self, finding, project_name: str) -> IssueData:
        """Convert finding to GitLab issue."""
        
    def scan_result_to_issues(
        self,
        scan_result: ScanResult,
        project_name: str,
        group_by_file: bool
    ) -> List[IssueData]:
        """Convert scan results to GitLab issues."""
```

## Usage Examples

### Scan and Create Issues

```python
from security_assistant.scanners import BanditScanner
from security_assistant.gitlab_api import GitLabAPI

# Initialize
scanner = BanditScanner(min_severity="HIGH")
api = GitLabAPI()

# Scan
result = scanner.scan_directory("src/", recursive=True)

# Convert to issues
issues = scanner.scan_result_to_issues(result, "MyApp")

# Create in GitLab
for issue in issues:
    created = api.create_issue("namespace/project", issue)
    print(f"Created: {created['web_url']}")
```

### Command-Line Usage

```bash
# Scan file
python examples/scan_and_create_issues.py \
  --file app.py \
  --project "namespace/project" \
  --min-severity HIGH

# Scan directory
python examples/scan_and_create_issues.py \
  --directory src/ \
  --recursive \
  --project "namespace/project" \
  --group-by-file

# Dry run (preview)
python examples/scan_and_create_issues.py \
  --directory . \
  --recursive \
  --project "namespace/project" \
  --dry-run
```

### Filtering Results

```python
# High severity only
scanner = BanditScanner(
    min_severity="HIGH",
    min_confidence="MEDIUM"
)

# Exclude directories
scanner = BanditScanner(
    exclude_dirs=["tests", "venv", ".venv"]
)
```

### Grouping Issues

```python
# One issue per finding (default)
issues = scanner.scan_result_to_issues(
    result,
    group_by_file=False
)

# One issue per file (grouped)
issues = scanner.scan_result_to_issues(
    result,
    group_by_file=True
)
```

## Issue Format

### Individual Issue

**Title:** `Security: hardcoded_password_string in auth.py`

**Labels:** `security`, `bandit`, `critical`, `b105`

**Description:**
```markdown
## 🔴 Security Finding: hardcoded_password_string

**Severity:** HIGH
**Confidence:** HIGH ✅
**Test ID:** B105

### Issue Description
Possible hardcoded password: 'admin123'

### Location
**File:** `src/auth.py`
**Line:** 42

### Code
```python
password = 'admin123'
```

**CWE:** [259](https://cwe.mitre.org/data/definitions/259.html)
**More Info:** https://bandit.readthedocs.io/...
```

### Grouped Issue

**Title:** `Security: 3 issues in auth.py`

**Labels:** `security`, `bandit`, `multiple-issues`, `critical`

**Description:**
```markdown
## 🔒 Security Issues Found in auth.py

**Total Issues:** 3
- 🔴 High: 2
- 🟡 Medium: 1

### 1. 🔴 hardcoded_password_string
...

### 2. 🔴 hardcoded_sql_expressions
...

### 3. 🟡 eval
...
```

## Testing

### Run All Tests

```bash
# Unit tests
pytest tests/test_bandit_scanner.py -v

# Integration tests
pytest tests/test_scanner_integration.py -v

# All tests
pytest tests/ -v
```

### Validation Script

```bash
# Demo without Bandit installation
python examples/validate_scanner.py
```

## Error Handling

All scanners use custom exceptions:

```python
try:
    scanner = BanditScanner()
    result = scanner.scan_file("app.py")
except BanditNotInstalledError:
    print("Install Bandit: pip install bandit")
except BanditScannerError as e:
    print(f"Scan failed: {e}")
```

## Best Practices

### 1. Start with High Severity
```python
scanner = BanditScanner(min_severity="HIGH")
```

### 2. Use Dry Run First
```bash
python examples/scan_and_create_issues.py \
  --directory src/ \
  --project "namespace/project" \
  --dry-run
```

### 3. Group for Large Scans
```python
issues = scanner.scan_result_to_issues(
    result,
    group_by_file=True  # Avoid too many issues
)
```

### 4. Exclude Test Files
```python
scanner = BanditScanner(
    exclude_dirs=["tests", "test_*"]
)
```

## CI/CD Integration

### GitLab CI Example

```yaml
security_scan:
  stage: test
  script:
    - pip install bandit
    - python examples/scan_and_create_issues.py \
        --directory src/ \
        --recursive \
        --project "$CI_PROJECT_PATH" \
        --min-severity HIGH
  only:
    - merge_requests
    - main
```

## Documentation

- **Bandit Scanner Guide:** [docs/BANDIT_SCANNER_GUIDE.md](../../docs/BANDIT_SCANNER_GUIDE.md)
- **API Reference:** See module docstrings
- **Examples:** [examples/](../../examples/)

## Development

### Adding a New Scanner

1. Create `security_assistant/scanners/new_scanner.py`
2. Implement scanner interface
3. Create data models (Finding, ScanResult)
4. Add unit tests
5. Add integration tests
6. Update `__init__.py`
7. Create documentation

### Running Tests

```bash
# With coverage
pytest tests/ --cov=security_assistant.scanners --cov-report=html

# Specific scanner
pytest tests/test_bandit_scanner.py -v
```

## Troubleshooting

### Scanner Not Found

**Error:** `BanditNotInstalledError`

**Solution:**
```bash
pip install bandit>=1.7.5
bandit --version
```

### No Findings

**Issue:** Scanner returns 0 findings

**Solutions:**
1. Lower severity threshold
2. Check file paths
3. Verify scanner installation

### GitLab API Errors

**Error:** `GitLabAuthError`

**Solution:**
```bash
export GITLAB_TOKEN="your-token-here"
```

## Resources

- **Bandit:** https://bandit.readthedocs.io/
- **Semgrep:** https://semgrep.dev/
- **CWE Database:** https://cwe.mitre.org/
- **OWASP:** https://owasp.org/

## License

Part of the Security Assistant project.

## Contributing

See main project README for contribution guidelines.
