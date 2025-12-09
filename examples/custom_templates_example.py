"""
Example: Using Custom Templates for Report Generation

This example demonstrates how to use custom Jinja2 templates
to generate customized security reports.

Features:
- Default template
- Executive template for management
- Custom template variables
- Multiple report formats with templates
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_assistant.orchestrator import ScannerType, ScanOrchestrator
from security_assistant.report_generator import ReportFormat, ReportGenerator


def main():
    """Generate reports using custom templates."""
    
    print("=" * 80)
    print("Custom Templates Example")
    print("=" * 80)
    
    # Initialize orchestrator
    orchestrator = ScanOrchestrator()
    orchestrator.enable_scanner(ScannerType.BANDIT)
    
    # Scan example vulnerable code
    print("\n1. Scanning example vulnerable code...")
    result = orchestrator.scan_file("examples/vulnerable_code.py")
    
    print("\nScan completed:")
    print(f"  - Total findings: {result.total_findings}")
    print(f"  - Unique findings: {len(result.deduplicated_findings)}")
    print(f"  - Critical: {result.critical_count}")
    print(f"  - High: {result.high_count}")
    print(f"  - Medium: {result.medium_count}")
    print(f"  - Low: {result.low_count}")
    
    # Initialize report generator
    generator = ReportGenerator(
        include_charts=True,
        include_code_snippets=True
    )
    
    # Generate reports with different templates
    print("\n2. Generating reports with custom templates...")
    
    # Default HTML template
    print("\n   a) Default HTML template...")
    generator.generate_report(
        result,
        "reports/custom_default.html",
        format=ReportFormat.HTML,
        title="Security Scan Report - Default Template"
    )
    print("      ✓ Generated: reports/custom_default.html")
    
    # Executive HTML template
    print("\n   b) Executive HTML template...")
    generator.generate_report(
        result,
        "reports/custom_executive.html",
        format=ReportFormat.HTML,
        template_name="executive.html",
        title="Executive Security Report"
    )
    print("      ✓ Generated: reports/custom_executive.html")
    
    # Default Markdown template
    print("\n   c) Default Markdown template...")
    generator.generate_report(
        result,
        "reports/custom_default.md",
        format=ReportFormat.MARKDOWN,
        title="Security Scan Report - Markdown"
    )
    print("      ✓ Generated: reports/custom_default.md")
    
    # Default Text template
    print("\n   d) Default Text template...")
    generator.generate_report(
        result,
        "reports/custom_default.txt",
        format=ReportFormat.TEXT,
        title="Security Scan Report - Text"
    )
    print("      ✓ Generated: reports/custom_default.txt")
    
    # Custom template with additional variables
    print("\n   e) Custom template with variables...")
    generator.generate_report(
        result,
        "reports/custom_with_vars.html",
        format=ReportFormat.HTML,
        template_name="default.html",
        title="Custom Report with Variables",
        # Custom variables
        company_name="Acme Corporation",
        report_author="Security Team",
        compliance_standards=["OWASP Top 10", "CWE Top 25", "PCI DSS"]
    )
    print("      ✓ Generated: reports/custom_with_vars.html")
    
    print("\n" + "=" * 80)
    print("All reports generated successfully!")
    print("=" * 80)
    
    print("\nGenerated reports:")
    print("  - reports/custom_default.html (Default template)")
    print("  - reports/custom_executive.html (Executive template)")
    print("  - reports/custom_default.md (Markdown template)")
    print("  - reports/custom_default.txt (Text template)")
    print("  - reports/custom_with_vars.html (Custom variables)")
    
    print("\nTemplate locations:")
    print("  - templates/html/default.html")
    print("  - templates/html/executive.html")
    print("  - templates/markdown/default.md")
    print("  - templates/text/default.txt")
    print("  - templates/html/styles.css")
    
    print("\nTo create your own template:")
    print("  1. Copy an existing template from templates/")
    print("  2. Modify the template to your needs")
    print("  3. Use template_name parameter to specify your template")
    print("  4. Pass custom variables via **kwargs")


if __name__ == "__main__":
    main()
