"""
Example: Generate Security Reports in Multiple Formats

This example demonstrates how to generate comprehensive security reports
in various formats (HTML, PDF, SARIF, JSON, YAML, Markdown, Text).

Usage:
    python examples/generate_reports_example.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_assistant.orchestrator import ScanOrchestrator, ScannerType
from security_assistant.report_generator import ReportGenerator, ReportFormat


def main():
    """Generate reports in multiple formats."""
    
    print("=" * 80)
    print("Security Report Generation Example")
    print("=" * 80)
    print()
    
    # Initialize orchestrator
    print("1. Initializing scan orchestrator...")
    orchestrator = ScanOrchestrator(
        max_workers=3,
        enable_deduplication=True,
        dedup_strategy="both"
    )
    
    # Enable scanners
    print("2. Enabling scanners...")
    orchestrator.enable_scanner(ScannerType.BANDIT)
    
    # Try to enable optional scanners
    try:
        # Use specific config instead of auto to avoid metrics requirement
        orchestrator.enable_scanner(ScannerType.SEMGREP, config="p/security-audit")
        print("   ✓ Semgrep enabled")
    except Exception as e:
        print(f"   ⚠️  Semgrep not available: {e}")
    
    try:
        orchestrator.enable_scanner(ScannerType.TRIVY, scan_type="fs")
        print("   ✓ Trivy enabled")
    except Exception as e:
        print(f"   ⚠️  Trivy not available: {e}")
    
    print("   ✓ Bandit enabled")
    print()
    
    # Scan example vulnerable code
    print("3. Scanning example vulnerable code...")
    target = "examples/vulnerable_code.py"
    
    if not Path(target).exists():
        print(f"   ⚠️  Target file not found: {target}")
        print("   Creating example vulnerable code...")
        
        # Create example vulnerable code
        Path(target).write_text("""
import pickle
import os

# Vulnerable: SQL Injection
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return query

# Vulnerable: Command Injection
def run_command(cmd):
    os.system(cmd)

# Vulnerable: Pickle deserialization
def load_data(data):
    return pickle.loads(data)

# Vulnerable: Hardcoded credentials
API_KEY = "sk-1234567890abcdef"
PASSWORD = "admin123"
""")
    
    result = orchestrator.scan_file(target)
    print(f"   ✓ Scan complete: {len(result.deduplicated_findings)} unique findings")
    print(f"   - Critical: {result.critical_count}")
    print(f"   - High: {result.high_count}")
    print(f"   - Medium: {result.medium_count}")
    print(f"   - Low: {result.low_count}")
    print()
    
    # Initialize report generator
    print("4. Initializing report generator...")
    generator = ReportGenerator(
        include_charts=True,
        include_code_snippets=True
    )
    print("   ✓ Report generator ready")
    print()
    
    # Create reports directory
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    # Generate reports in different formats
    print("5. Generating reports...")
    
    formats = [
        (ReportFormat.HTML, "security_report.html", "HTML Report"),
        (ReportFormat.MARKDOWN, "security_report.md", "Markdown Report"),
        (ReportFormat.JSON, "security_report.json", "JSON Report"),
        (ReportFormat.YAML, "security_report.yaml", "YAML Report"),
        (ReportFormat.SARIF, "security_report.sarif", "SARIF Report"),
        (ReportFormat.TEXT, "security_report.txt", "Text Report"),
    ]
    
    for format_type, filename, description in formats:
        output_path = reports_dir / filename
        
        try:
            generator.generate_report(
                result,
                str(output_path),
                format=format_type,
                title="Security Scan Report - Example"
            )
            print(f"   ✓ {description}: {output_path}")
        except Exception as e:
            print(f"   ✗ {description}: {e}")
    
    print()
    
    # Generate PDF (optional, requires weasyprint)
    print("6. Generating PDF report (optional)...")
    try:
        pdf_path = reports_dir / "security_report.pdf"
        generator.generate_report(
            result,
            str(pdf_path),
            format=ReportFormat.PDF,
            title="Security Scan Report - Example"
        )
        print(f"   ✓ PDF Report: {pdf_path}")
    except ImportError:
        print("   ⚠️  PDF generation requires weasyprint")
        print("      Install with: pip install weasyprint")
    except Exception as e:
        print(f"   ✗ PDF generation failed: {e}")
    
    print()
    print("=" * 80)
    print("Report Generation Complete!")
    print("=" * 80)
    print()
    print(f"Reports saved to: {reports_dir.absolute()}")
    print()
    print("Next steps:")
    print("1. Open security_report.html in your browser for interactive view")
    print("2. Use security_report.sarif for CI/CD integration")
    print("3. Use security_report.json for programmatic access")
    print("4. Share security_report.pdf with stakeholders")
    print()


if __name__ == "__main__":
    main()
