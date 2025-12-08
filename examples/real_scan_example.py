"""
Real-World Example: Scan Project and Create GitLab Issues

This example demonstrates a complete workflow:
1. Scan project with multiple scanners (Bandit + Semgrep)
2. Aggregate and deduplicate findings
3. Calculate priority scores
4. Create top priority issues in GitLab

Usage:
    python examples/real_scan_example.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_assistant.orchestrator import ScanOrchestrator, ScannerType
from security_assistant.gitlab_api import GitLabAPI


def main():
    """Run real security scan and create GitLab issues"""
    print("=" * 80)
    print("Security Assistant - Real Scan Example")
    print("=" * 80)
    print()
    
    # Configuration
    target_dir = "security_assistant"  # Scan our own code
    project_id = os.getenv("GITLAB_PROJECT_ID", "76475459")
    gitlab_token = os.getenv("GITLAB_TOKEN")
    
    if not gitlab_token:
        print("❌ ERROR: GITLAB_TOKEN not set")
        return 1
    
    print(f"Target directory: {target_dir}")
    print(f"GitLab project: {project_id}")
    print()
    
    # Step 1: Initialize orchestrator
    print("Step 1: Initializing Multi-Scanner Orchestrator")
    print("-" * 80)
    orchestrator = ScanOrchestrator(
        max_workers=2,
        enable_deduplication=True,
        dedup_strategy="both"
    )
    
    # Enable scanners
    print("Enabling scanners:")
    orchestrator.enable_scanner(ScannerType.BANDIT, min_severity="MEDIUM")
    print("  ✓ Bandit (Python security)")
    
    orchestrator.enable_scanner(ScannerType.SEMGREP, config="auto", min_severity="WARNING")
    print("  ✓ Semgrep (multi-language SAST)")
    print()
    
    # Step 2: Run scan
    print("Step 2: Running Security Scan")
    print("-" * 80)
    print(f"Scanning: {target_dir}")
    print()
    
    result = orchestrator.scan_directory(target_dir, recursive=True)
    
    print(f"✓ Scan complete in {result.execution_time_seconds:.2f}s")
    print()
    
    # Step 3: Display results
    print("Step 3: Scan Results")
    print("-" * 80)
    print(f"Total findings: {result.total_findings}")
    print(f"Unique findings: {len(result.deduplicated_findings)}")
    print(f"Duplicates removed: {result.duplicates_removed}")
    print()
    
    print("Findings by Severity:")
    print(f"  🔴 Critical: {result.critical_count}")
    print(f"  🟠 High: {result.high_count}")
    print(f"  🟡 Medium: {result.medium_count}")
    print(f"  🟢 Low: {result.low_count}")
    print()
    
    print("Findings by Scanner:")
    for scanner, count in result.findings_by_scanner.items():
        print(f"  {scanner.value}: {count}")
    print()
    
    # Step 4: Show top priority findings
    print("Step 4: Top Priority Findings")
    print("-" * 80)
    
    if result.top_priority_findings:
        for i, finding in enumerate(result.top_priority_findings[:5], 1):
            print(f"{i}. [{finding.severity.value}] {finding.title}")
            print(f"   File: {finding.file_path}:{finding.line_start}")
            print(f"   Priority: {finding.priority_score:.1f}/100")
            print(f"   Scanner: {finding.scanner.value}")
            print()
    else:
        print("✅ No security issues found!")
        print()
    
    # Step 5: Create GitLab issues (if findings exist)
    if result.deduplicated_findings:
        print("Step 5: Creating GitLab Issues")
        print("-" * 80)
        
        # Ask for confirmation
        print(f"Found {len(result.deduplicated_findings)} unique findings.")
        print(f"Create issues for top 5 priority findings? (y/n): ", end="")
        
        try:
            response = input().strip().lower()
        except (EOFError, KeyboardInterrupt):
            response = "n"
            print()
        
        if response == "y":
            # Initialize GitLab API
            api = GitLabAPI(private_token=gitlab_token)
            
            # Convert top 5 findings to issues
            issues = orchestrator.result_to_issues(
                result,
                project_name="Workstation",
                top_n=5
            )
            
            print(f"\nCreating {len(issues)} issues...")
            created_issues = []
            
            for i, issue in enumerate(issues, 1):
                try:
                    created = api.create_issue(project_id, issue)
                    created_issues.append(created)
                    print(f"  {i}. ✓ Issue #{created['iid']}: {issue.title}")
                except Exception as e:
                    print(f"  {i}. ✗ Failed: {e}")
            
            print()
            print(f"✓ Created {len(created_issues)} issues successfully!")
            print()
            
            if created_issues:
                print("View issues:")
                for issue in created_issues:
                    print(f"  - {issue['web_url']}")
                print()
        else:
            print("\nSkipped issue creation.")
            print()
    
    # Summary
    print("=" * 80)
    print("✅ Scan Complete!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  - Scanned: {target_dir}")
    print(f"  - Execution time: {result.execution_time_seconds:.2f}s")
    print(f"  - Findings: {len(result.deduplicated_findings)}")
    print(f"  - Critical/High: {result.critical_count + result.high_count}")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
