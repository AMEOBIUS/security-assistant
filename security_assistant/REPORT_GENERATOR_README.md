# Report Generator Module

Comprehensive security report generation in multiple formats.

## Features

### Supported Formats
- **HTML** - Interactive reports with Chart.js visualizations
- **PDF** - Executive summaries (requires weasyprint)
- **SARIF** - CI/CD integration (SARIF 2.1.0 compliant)
- **JSON** - Programmatic access
- **YAML** - Configuration-friendly
- **Markdown** - Documentation-ready
- **Text** - Terminal-friendly

### HTML Report Features
- 📈 Interactive charts (severity bar chart, scanner pie chart)
- 🎨 Modern responsive design
- 🔍 Collapsible finding details
- 🎯 Color-coded severity badges
- 📊 Executive summary dashboard
- 🖱️ Click-to-expand interactions
- 🖨️ Print-friendly CSS

### SARIF Compliance
- ✅ SARIF 2.1.0 specification
- ✅ GitHub/GitLab Security compatible
- ✅ Rule definitions
- ✅ Location mapping
- ✅ Fix suggestions
- ✅ CWE mapping

## Quick Start

```python
from security_assistant.orchestrator import ScanOrchestrator, ScannerType
from security_assistant.report_generator import ReportGenerator, ReportFormat

# Scan code
orchestrator = ScanOrchestrator()
orchestrator.enable_scanner(ScannerType.BANDIT)
result = orchestrator.scan_directory("src/")

# Generate HTML report
generator = ReportGenerator()
generator.generate_report(
    result,
    "security_report.html",
    format=ReportFormat.HTML,
    title="Security Scan Report"
)
```

## Usage Examples

### Generate Multiple Formats

```python
generator = ReportGenerator(
    include_charts=True,
    include_code_snippets=True
)

formats = [
    (ReportFormat.HTML, "report.html"),
    (ReportFormat.SARIF, "report.sarif"),
    (ReportFormat.JSON, "report.json"),
    (ReportFormat.MARKDOWN, "report.md"),
]

for fmt, filename in formats:
    generator.generate_report(
        result,
        filename,
        format=fmt,
        title="Security Analysis"
    )
```

### Customize Report Options

```python
# Minimal report (no charts, no code snippets)
generator = ReportGenerator(
    include_charts=False,
    include_code_snippets=False
)

# Generate lightweight HTML
generator.generate_report(
    result,
    "minimal_report.html",
    format=ReportFormat.HTML
)
```

### Generate PDF Report

```python
# Requires: pip install weasyprint
generator = ReportGenerator()

generator.generate_report(
    result,
    "executive_summary.pdf",
    format=ReportFormat.PDF,
    title="Executive Security Summary"
)
```

## Report Formats

### HTML Report
- **File:** `report.html`
- **Use Case:** Interactive viewing, web hosting
- **Features:** Charts, collapsible details, responsive design
- **Size:** ~50-200 KB (depending on findings)

### SARIF Report
- **File:** `report.sarif`
- **Use Case:** CI/CD integration, GitHub/GitLab Security
- **Features:** Standardized format, tool integration
- **Size:** ~10-50 KB

### JSON Report
- **File:** `report.json`
- **Use Case:** Programmatic access, automation
- **Features:** Structured data, complete metadata
- **Size:** ~10-50 KB

### Markdown Report
- **File:** `report.md`
- **Use Case:** Documentation, wikis, README
- **Features:** Tables, formatting, top findings
- **Size:** ~5-20 KB

### Text Report
- **File:** `report.txt`
- **Use Case:** Terminal output, logs
- **Features:** Simple formatting, ASCII-only
- **Size:** ~5-15 KB

## API Reference

### ReportGenerator Class

```python
class ReportGenerator:
    def __init__(
        self,
        template_dir: Optional[str] = None,
        include_charts: bool = True,
        include_code_snippets: bool = True,
    ):
        """
        Initialize report generator.
        
        Args:
            template_dir: Custom template directory (optional)
            include_charts: Include charts in HTML reports
            include_code_snippets: Include code snippets in reports
        """
```

### generate_report Method

```python
def generate_report(
    self,
    result: OrchestrationResult,
    output_path: str,
    format: str = ReportFormat.HTML,
    title: Optional[str] = None,
    **kwargs
) -> str:
    """
    Generate a security scan report.
    
    Args:
        result: OrchestrationResult to report on
        output_path: Output file path
        format: Report format (html, pdf, sarif, json, yaml, markdown, text)
        title: Report title (optional)
        **kwargs: Format-specific options
    
    Returns:
        Path to generated report
    """
```

## Integration Examples

### CI/CD Pipeline

```yaml
# .gitlab-ci.yml
security_scan:
  script:
    - python -m security_assistant scan src/
    - python -m security_assistant report --format sarif
  artifacts:
    reports:
      sast: security_report.sarif
```

### Automated Reporting

```python
# Generate all formats
formats = [
    ReportFormat.HTML,
    ReportFormat.SARIF,
    ReportFormat.JSON,
    ReportFormat.MARKDOWN,
]

for fmt in formats:
    generator.generate_report(
        result,
        f"reports/security_report.{fmt}",
        format=fmt
    )
```

### Custom Processing

```python
import json

# Generate JSON report
generator.generate_report(result, "report.json", format=ReportFormat.JSON)

# Load and process
with open("report.json") as f:
    data = json.load(f)
    
# Filter critical findings
critical = [
    f for f in data["findings"]
    if f["severity"] == "CRITICAL"
]

print(f"Critical issues: {len(critical)}")
```

## Report Structure

### HTML Report Sections
1. **Header** - Title and branding
2. **Executive Summary** - Key statistics
3. **Severity Breakdown** - Table with percentages
4. **Scanner Breakdown** - Findings by scanner
5. **Visual Analytics** - Interactive charts
6. **Detailed Findings** - Expandable table
7. **Footer** - Metadata and timestamp

### SARIF Report Structure
```json
{
  "version": "2.1.0",
  "$schema": "...",
  "runs": [{
    "tool": {
      "driver": {
        "name": "Security Assistant",
        "version": "1.0.0",
        "rules": [...]
      }
    },
    "results": [...]
  }]
}
```

### JSON Report Structure
```json
{
  "metadata": {
    "generated_at": "2025-11-29T08:00:00",
    "target": "src/",
    "execution_time_seconds": 5.5
  },
  "summary": {
    "total_findings": 13,
    "unique_findings": 13,
    "critical_count": 0,
    "high_count": 3
  },
  "findings": [...]
}
```

## Performance

### Generation Times
- **HTML:** ~50-100ms
- **PDF:** ~500-1000ms (with weasyprint)
- **SARIF:** ~20-50ms
- **JSON:** ~10-30ms
- **YAML:** ~20-40ms
- **Markdown:** ~30-60ms
- **Text:** ~10-20ms

### File Sizes
- **HTML:** 50-200 KB (with charts)
- **PDF:** 100-500 KB
- **SARIF:** 10-50 KB
- **JSON:** 10-50 KB
- **YAML:** 15-60 KB
- **Markdown:** 5-20 KB
- **Text:** 5-15 KB

## Testing

Run tests:
```bash
pytest tests/test_report_generator.py -v
```

Coverage:
```bash
pytest tests/test_report_generator.py --cov=security_assistant.report_generator
```

## Dependencies

### Required
- `pyyaml>=6.0.0` - YAML generation

### Optional
- `jinja2>=3.1.6` - Template engine (future)
- `markdown>=3.10` - Markdown processing (future)
- `weasyprint>=66.0` - PDF generation

Install all:
```bash
pip install pyyaml jinja2 markdown weasyprint
```

## Troubleshooting

### PDF Generation Fails
**Issue:** `weasyprint not installed`

**Solution:**
```bash
pip install weasyprint
```

If weasyprint installation fails, PDF generation will fallback to HTML.

### Charts Not Showing
**Issue:** Charts not visible in HTML report

**Solution:** Ensure internet connection for Chart.js CDN, or use `include_charts=False`

### Large Report Files
**Issue:** HTML reports are too large

**Solution:**
```python
generator = ReportGenerator(
    include_charts=False,
    include_code_snippets=False
)
```

## Advanced Usage

### Custom Templates (Future)
```python
generator = ReportGenerator(
    template_dir="custom/templates"
)
```

### Format-Specific Options
```python
# HTML with custom title
generator.generate_report(
    result,
    "report.html",
    format=ReportFormat.HTML,
    title="Custom Security Report"
)

# SARIF with custom properties
generator.generate_report(
    result,
    "report.sarif",
    format=ReportFormat.SARIF,
    custom_properties={"team": "security"}
)
```

## See Also

- [Orchestrator Documentation](orchestrator.md)
- [Scanner Documentation](scanners/README.md)
- [Examples](../examples/)
- [API Reference](../docs/api-reference.md)
