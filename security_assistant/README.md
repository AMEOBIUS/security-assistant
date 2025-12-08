# Security Assistant

Automated security vulnerability scanning and GitLab issue management for Python projects.

## Overview

Security Assistant automates the process of scanning code for security vulnerabilities and creating GitLab issues for findings. It integrates with popular security tools and provides a unified interface for vulnerability management.

## Features

### ✅ GitLab API Integration (Session 2)
- **Rate Limiting** - Automatic request throttling (50/min, 2000/hour)
- **Retry Logic** - Exponential backoff for failed requests
- **Error Handling** - Comprehensive exception handling
- **Session Management** - Connection pooling for performance
- **Type Safety** - Dataclasses for structured data

### ✅ Bandit Scanner (Session 3)
- **Python Security Scanning** - Detect vulnerabilities in Python code
- **Severity Filtering** - Filter by HIGH, MEDIUM, LOW
- **Confidence Filtering** - Filter by confidence level
- **GitLab Integration** - Automatic issue creation
- **Rich Formatting** - Markdown issues with code snippets and emojis
- **CWE Mapping** - Link to CWE database
- **CLI Interface** - Command-line scanning tool
- **Grouping Options** - Individual or grouped issues

### ⏭️ Coming Soon
- **Semgrep Scanner** (Session 4) - Multi-language security scanning
- **Safety Scanner** (Session 5) - Python dependency vulnerability scanning
- **Multi-Scanner Orchestration** (Session 5) - Run multiple scanners
- **CI/CD Integration** (Session 8) - Automated scanning in pipelines

## Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install security scanners
pip install bandit>=1.7.5
```

### 2. Configuration

Set environment variables:

```bash
export GITLAB_URL=https://gitlab.com
export GITLAB_TOKEN=your-gitlab-token
```

Or create a `.env` file:

```env
GITLAB_URL=https://gitlab.com
GITLAB_TOKEN=your-gitlab-token
```

### 3. Scan and Create Issues

**Python API:**

```python
from security_assistant.scanners import BanditScanner
from security_assistant.gitlab_api import GitLabAPI

# Initialize scanner
scanner = BanditScanner(min_severity="HIGH")

# Scan code
result = scanner.scan_directory("src/", recursive=True)

# Convert to GitLab issues
issues = scanner.scan_result_to_issues(result, "MyApp")

# Create issues in GitLab
api = GitLabAPI()
for issue in issues:
    created = api.create_issue("namespace/project", issue)
    print(f"✅ Created: {created['web_url']}")
```

**Command-Line:**

```bash
# Scan and create issues
python examples/scan_and_create_issues.py \
  --directory src/ \
  --recursive \
  --project "namespace/project" \
  --min-severity HIGH

# Dry run (preview)
python examples/scan_and_create_issues.py \
  --file app.py \
  --project "namespace/project" \
  --dry-run
```

## Project Structure

```
security_assistant/
├── __init__.py
├── gitlab_api.py          # GitLab API client
├── scanners/
│   ├── __init__.py
│   ├── bandit_scanner.py  # Bandit integration
│   └── README.md          # Scanner documentation
└── README.md              # This file

tests/
├── test_gitlab_api.py           # GitLab API tests
├── test_bandit_scanner.py       # Bandit scanner tests
├── test_scanner_integration.py  # Integration tests
└── test_integration.py          # Real API tests

examples/
├── create_issue_example.py      # GitLab API example
├── scan_and_create_issues.py   # Scanner CLI
├── vulnerable_code.py           # Test vulnerabilities
└── validate_scanner.py          # Validation script

docs/
├── BANDIT_SCANNER_GUIDE.md     # Comprehensive guide
├── REVISED_8_WEEK_PLAN.md      # Project plan
└── ...
```

## Usage Examples

### Scan a Single File

```python
from security_assistant.scanners import BanditScanner

scanner = BanditScanner(min_severity="MEDIUM")
result = scanner.scan_file("app.py")

print(f"Found {len(result.findings)} issues")
for finding in result.findings:
    print(f"  {finding.severity_emoji} {finding.test_name} at line {finding.line_number}")
```

### Scan Directory with Filtering

```python
scanner = BanditScanner(
    min_severity="HIGH",
    min_confidence="MEDIUM",
    exclude_dirs=["tests", "venv"]
)

result = scanner.scan_directory("src/", recursive=True)

print(f"Scanned {result.files_scanned} files")
print(f"High severity: {result.high_severity_count}")
print(f"Medium severity: {result.medium_severity_count}")
```

### Create Grouped Issues

```python
# One issue per file (instead of one per finding)
issues = scanner.scan_result_to_issues(
    result,
    project_name="MyApp",
    group_by_file=True
)

api = GitLabAPI()
for issue in issues:
    api.create_issue("namespace/project", issue)
```

### Manual Issue Creation

```python
from security_assistant.gitlab_api import GitLabAPI, IssueData

api = GitLabAPI()

issue = IssueData(
    title="Security: SQL Injection in login.py",
    description="**Severity:** High\n\n**File:** login.py:42",
    labels=["security", "bug"],
    confidential=True
)

result = api.create_issue("namespace/project", issue)
print(f"Issue created: {result['web_url']}")
```

## API Reference

### BanditScanner

```python
class BanditScanner:
    def __init__(
        self,
        min_severity: str = "LOW",      # LOW, MEDIUM, HIGH
        min_confidence: str = "LOW",    # LOW, MEDIUM, HIGH
        exclude_dirs: Optional[List[str]] = None
    )
    
    def scan_file(self, file_path: str) -> ScanResult
    
    def scan_directory(
        self,
        directory_path: str,
        recursive: bool = True
    ) -> ScanResult
    
    def finding_to_issue(
        self,
        finding: BanditFinding,
        project_name: str = "Unknown Project"
    ) -> IssueData
    
    def scan_result_to_issues(
        self,
        scan_result: ScanResult,
        project_name: str = "Unknown Project",
        group_by_file: bool = False
    ) -> List[IssueData]
```

### GitLabAPI

```python
class GitLabAPI:
    def __init__(
        self,
        gitlab_url: Optional[str] = None,
        private_token: Optional[str] = None,
        rate_limit_config: Optional[RateLimitConfig] = None
    )
    
    def create_issue(
        self,
        project_id: str,
        issue_data: IssueData
    ) -> Dict[str, Any]
    
    def get_project(self, project_id: str) -> Dict[str, Any]
    
    def list_issues(
        self,
        project_id: str,
        labels: Optional[List[str]] = None,
        state: str = "opened"
    ) -> List[Dict[str, Any]]
```

### Data Models

```python
@dataclass
class BanditFinding:
    test_id: str
    test_name: str
    severity: str  # HIGH, MEDIUM, LOW
    confidence: str  # HIGH, MEDIUM, LOW
    issue_text: str
    filename: str
    line_number: int
    code: str
    cwe_id: Optional[str] = None
    more_info: Optional[str] = None

@dataclass
class ScanResult:
    findings: List[BanditFinding]
    scan_time: datetime
    files_scanned: int
    lines_scanned: int
    errors: List[str]

@dataclass
class IssueData:
    title: str
    description: str
    labels: Optional[List[str]] = None
    assignee_ids: Optional[List[int]] = None
    confidential: bool = True
    due_date: Optional[str] = None
```

## Testing

### Run All Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_bandit_scanner.py -v

# With coverage
pytest tests/ --cov=security_assistant --cov-report=html
```

### Test Results

```
✅ Unit Tests: 19/19 passed
✅ Integration Tests: 5/5 passed
✅ GitLab API Tests: 15/15 passed
✅ Total: 39/39 tests passed
✅ Coverage: 90%+
```

### Validation

```bash
# Demo without Bandit installation
python examples/validate_scanner.py

# Test with vulnerable code
python -c "
from security_assistant.scanners import BanditScanner
scanner = BanditScanner()
result = scanner.scan_file('examples/vulnerable_code.py')
print(f'Found {len(result.findings)} issues')
"
```

## Error Handling

All modules provide specific exceptions:

```python
from security_assistant.gitlab_api import GitLabAuthError, GitLabAPIError
from security_assistant.scanners.bandit_scanner import BanditScannerError

try:
    api = GitLabAPI()
    scanner = BanditScanner()
    result = scanner.scan_file("app.py")
    issues = scanner.scan_result_to_issues(result)
    
    for issue in issues:
        api.create_issue("namespace/project", issue)
        
except GitLabAuthError:
    print("Invalid GitLab token")
except BanditScannerError as e:
    print(f"Scanner error: {e}")
except GitLabAPIError as e:
    print(f"API error: {e}")
```

## Documentation

- **Bandit Scanner Guide:** [docs/BANDIT_SCANNER_GUIDE.md](../docs/BANDIT_SCANNER_GUIDE.md)
- **Scanner Package:** [scanners/README.md](scanners/README.md)
- **Project Plan:** [docs/REVISED_8_WEEK_PLAN.md](../docs/REVISED_8_WEEK_PLAN.md)
- **Session Summaries:** `SESSION_*.md` files in project root

## CI/CD Integration

### GitLab CI Example

```yaml
security_scan:
  stage: test
  script:
    - pip install -r requirements.txt
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

## Security Notes

⚠️ **Important Security Practices:**

- Never commit GitLab tokens to version control
- Use environment variables or `.env` files
- Add `.env` to `.gitignore`
- Use GitLab CI/CD variables for automation
- Rotate tokens regularly
- Use confidential issues for security findings

## Troubleshooting

### Bandit Not Found

```bash
pip install bandit>=1.7.5
bandit --version
```

### GitLab Authentication Error

```bash
# Check token
echo $GITLAB_TOKEN

# Set token
export GITLAB_TOKEN="your-token-here"
```

### No Findings

Lower severity threshold:

```python
scanner = BanditScanner(
    min_severity="LOW",
    min_confidence="LOW"
)
```

## Contributing

See main project documentation for contribution guidelines.

## Progress

- ✅ **Session 2:** GitLab API Integration
- ✅ **Session 3:** Bandit Scanner Integration
- ⏭️ **Session 4:** Semgrep Scanner Integration
- ⏭️ **Session 5:** Multi-Scanner Orchestration
- ⏭️ **Session 6:** Basic CLI
- ⏭️ **Session 8:** CI/CD Automation

**Overall:** 3/16 sessions (18.75%) - Ahead of schedule

## License

Part of the Security Assistant project.
