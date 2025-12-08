"""
Quick validation script for Bandit scanner.
Demonstrates scanner functionality without requiring Bandit installation.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_assistant.scanners.bandit_scanner import (
    BanditFinding,
    ScanResult,
    BanditScanner
)
from unittest.mock import Mock, patch
import json


def demo_scanner_without_bandit():
    """Demonstrate scanner with mocked Bandit."""
    print("=" * 80)
    print("Bandit Scanner Demo (Mocked)")
    print("=" * 80)
    print()
    
    # Sample Bandit output
    sample_output = {
        "errors": [],
        "metrics": {"_totals": {"loc": 100, "nosec": 0}},
        "results": [
            {
                "code": "password = 'admin123'",
                "filename": "auth.py",
                "issue_confidence": "HIGH",
                "issue_severity": "HIGH",
                "issue_text": "Possible hardcoded password: 'admin123'",
                "line_number": 42,
                "more_info": "https://bandit.readthedocs.io/",
                "test_id": "B105",
                "test_name": "hardcoded_password_string",
                "issue_cwe": {"id": 259}
            },
            {
                "code": "eval(user_input)",
                "filename": "utils.py",
                "issue_confidence": "HIGH",
                "issue_severity": "MEDIUM",
                "issue_text": "Use of possibly insecure function - eval()",
                "line_number": 55,
                "more_info": "https://bandit.readthedocs.io/",
                "test_id": "B307",
                "test_name": "eval"
            }
        ]
    }
    
    # Mock Bandit
    with patch('security_assistant.scanners.bandit_scanner.subprocess.run') as mock_run:
        # Mock version check
        mock_run.return_value = Mock(returncode=0, stdout="bandit 1.7.5")
        
        # Create scanner
        scanner = BanditScanner(min_severity="MEDIUM")
        print("✅ Scanner initialized")
        print(f"   Min Severity: MEDIUM")
        print(f"   Min Confidence: LOW")
        print()
        
        # Parse sample output
        result = scanner._parse_bandit_output(json.dumps(sample_output))
        
        print("Scan Results:")
        print(f"  Total findings: {len(result.findings)}")
        print(f"  🔴 High: {result.high_severity_count}")
        print(f"  🟡 Medium: {result.medium_severity_count}")
        print(f"  🟢 Low: {result.low_severity_count}")
        print()
        
        # Show findings
        print("Findings:")
        for i, finding in enumerate(result.findings, 1):
            print(f"  {i}. {finding.severity_emoji} {finding.test_name}")
            print(f"     File: {finding.filename}:{finding.line_number}")
            print(f"     Severity: {finding.severity} | Confidence: {finding.confidence}")
            print(f"     Issue: {finding.issue_text}")
            print()
        
        # Convert to GitLab issues
        print("Converting to GitLab issues...")
        issues = scanner.scan_result_to_issues(result, "DemoProject")
        print(f"✅ Created {len(issues)} issue(s)")
        print()
        
        # Show first issue
        if issues:
            issue = issues[0]
            print("Sample Issue:")
            print(f"  Title: {issue.title}")
            print(f"  Labels: {', '.join(issue.labels)}")
            print(f"  Confidential: {issue.confidential}")
            print()
            print("  Description (first 300 chars):")
            print("  " + "-" * 76)
            for line in issue.description[:300].split('\n'):
                print(f"  {line}")
            print("  ...")
            print()


def demo_data_models():
    """Demonstrate data models."""
    print("=" * 80)
    print("Data Models Demo")
    print("=" * 80)
    print()
    
    # Create a finding
    finding = BanditFinding(
        test_id="B105",
        test_name="hardcoded_password",
        severity="HIGH",
        confidence="HIGH",
        issue_text="Hardcoded password detected",
        filename="app.py",
        line_number=10,
        code="password = 'secret123'",
        cwe_id="259",
        more_info="https://bandit.readthedocs.io/"
    )
    
    print("BanditFinding:")
    print(f"  Test: {finding.test_id} - {finding.test_name}")
    print(f"  Severity: {finding.severity} {finding.severity_emoji}")
    print(f"  Confidence: {finding.confidence} {finding.confidence_emoji}")
    print(f"  Location: {finding.filename}:{finding.line_number}")
    print(f"  CWE: {finding.cwe_id}")
    print()
    
    # Create scan result
    result = ScanResult(
        findings=[finding],
        files_scanned=10,
        lines_scanned=500
    )
    
    print("ScanResult:")
    print(f"  Files scanned: {result.files_scanned}")
    print(f"  Lines scanned: {result.lines_scanned}")
    print(f"  Total findings: {len(result.findings)}")
    print(f"  High severity: {result.high_severity_count}")
    print(f"  Has findings: {result.has_findings}")
    print()


if __name__ == "__main__":
    demo_data_models()
    print()
    demo_scanner_without_bandit()
    
    print("=" * 80)
    print("✅ Validation Complete")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Install Bandit: pip install bandit")
    print("  2. Scan real code: python examples/scan_and_create_issues.py --file app.py --project namespace/project --dry-run")
    print("  3. Run tests: pytest tests/test_bandit_scanner.py -v")
