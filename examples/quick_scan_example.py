"""
Quick Scan Example: Scan with Bandit and Create GitLab Issues

This example uses only Bandit scanner (no additional dependencies needed).

Usage:
    python examples/quick_scan_example.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_assistant.gitlab_api import GitLabAPI
from security_assistant.orchestrator import ScannerType, ScanOrchestrator


def main():
    """Run quick security scan with Bandit"""
    print("=" * 80)
    print("Security Assistant - Quick Scan (Bandit Only)")
    print("=" * 80)
    print()
    
    # Configuration
    target_dir = "security_assistant"
    project_id = os.getenv("GITLAB_PROJECT_ID", "76475459")
    gitlab_token = os.getenv("GITLAB_TOKEN")
    
    if not gitlab_token:
        print("❌ ERROR: GITLAB_TOKEN not set")
        return 1
    
    print(f"Target: {target_dir}")
    print(f"Project: {project_id}")
    print()
    
    # Initialize orchestrator
    print("1. Initializing Scanner")
    print("-" * 80)
    orchestrator = ScanOrchestrator(
        max_workers=1,
        enable_deduplication=True,
        dedup_strategy="location"
    )
    
    orchestrator.enable_scanner(ScannerType.BANDIT, min_severity="LOW")
    print("✓ Bandit scanner enabled")
    print()
    
    # Run scan
    print("2. Running Security Scan")
    print("-" * 80)
    result = orchestrator.scan_directory(target_dir, recursive=True)
    
    print(f"✓ Scan complete in {result.execution_time_seconds:.2f}s")
    print()
    
    # Display results
    print("3. Results")
    print("-" * 80)
    print(f"Total findings: {result.total_findings}")
    print(f"Unique findings: {len(result.deduplicated_findings)}")
    print()
    
    print("By Severity:")
    print(f"  🔴 Critical: {result.critical_count}")
    print(f"  🟠 High: {result.high_count}")
    print(f"  🟡 Medium: {result.medium_count}")
    print(f"  🟢 Low: {result.low_count}")
    print()
    
    # Show top findings
    if result.top_priority_findings:
        print("4. Top 10 Priority Findings")
        print("-" * 80)
        for i, finding in enumerate(result.top_priority_findings[:10], 1):
            print(f"{i}. [{finding.severity.value}] {finding.title}")
            print(f"   {finding.file_path}:{finding.line_start}")
            print(f"   Priority: {finding.priority_score:.1f}/100")
            print()
    else:
        print("✅ No security issues found!")
        print()
        return 0
    
    # Create issues
    print("5. Create GitLab Issues?")
    print("-" * 80)
    print("Create issues for top 3 findings? (y/n): ", end="")
    
    try:
        response = input().strip().lower()
    except (EOFError, KeyboardInterrupt):
        response = "n"
        print()
    
    if response == "y":
        api = GitLabAPI(private_token=gitlab_token)
        
        issues = orchestrator.result_to_issues(
            result,
            project_name="Workstation",
            top_n=3
        )
        
        print(f"\nCreating {len(issues)} issues...")
        created = []
        
        for i, issue in enumerate(issues, 1):
            try:
                created_issue = api.create_issue(project_id, issue)
                created.append(created_issue)
                print(f"  {i}. ✓ #{created_issue['iid']}: {issue.title[:60]}...")
            except Exception as e:
                print(f"  {i}. ✗ Error: {e}")
        
        print()
        print(f"✓ Created {len(created)} issues")
        print()
        
        if created:
            print("View issues:")
            for issue in created:
                print(f"  {issue['web_url']}")
            print()
    else:
        print("\nSkipped.")
        print()
    
    print("=" * 80)
    print("✅ Done!")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
