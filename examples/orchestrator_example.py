"""
Multi-Scanner Orchestration Example

This example demonstrates how to use the ScanOrchestrator to run
multiple security scanners in parallel and aggregate their results.

Features demonstrated:
- Enabling multiple scanners
- Parallel execution
- Result aggregation
- Deduplication
- Priority scoring
- GitLab issue creation
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_assistant.orchestrator import (
    ScannerType,
    ScanOrchestrator,
)


def example_basic_scan():
    """Example 1: Basic multi-scanner scan"""
    print("=" * 80)
    print("Example 1: Basic Multi-Scanner Scan")
    print("=" * 80)
    
    # Initialize orchestrator
    orchestrator = ScanOrchestrator(
        max_workers=3,
        enable_deduplication=True,
        dedup_strategy="location"
    )
    
    # Enable scanners
    print("\n1. Enabling scanners...")
    orchestrator.enable_scanner(ScannerType.BANDIT, min_severity="MEDIUM")
    orchestrator.enable_scanner(ScannerType.SEMGREP, config="auto", min_severity="WARNING")
    print("   ✓ Bandit enabled (Python security)")
    print("   ✓ Semgrep enabled (multi-language SAST)")
    
    # Scan directory
    print("\n2. Scanning directory...")
    target_dir = "security_assistant"
    
    try:
        result = orchestrator.scan_directory(target_dir, recursive=True)
        
        print("\n3. Scan Results:")
        print(f"   Target: {result.target}")
        print(f"   Execution time: {result.execution_time_seconds:.2f}s")
        print(f"   Total findings: {result.total_findings}")
        print(f"   Unique findings: {len(result.deduplicated_findings)}")
        print(f"   Duplicates removed: {result.duplicates_removed}")
        
        print("\n4. Findings by Severity:")
        print(f"   🔴 Critical: {result.critical_count}")
        print(f"   🟠 High: {result.high_count}")
        print(f"   🟡 Medium: {result.medium_count}")
        print(f"   🟢 Low: {result.low_count}")
        
        print("\n5. Findings by Scanner:")
        for scanner, count in result.findings_by_scanner.items():
            print(f"   {scanner.value}: {count}")
        
        # Show top priority findings
        if result.top_priority_findings:
            print("\n6. Top 5 Priority Findings:")
            for i, finding in enumerate(result.top_priority_findings[:5], 1):
                print(f"   {i}. [{finding.severity.value}] {finding.title}")
                print(f"      File: {finding.file_path}:{finding.line_start}")
                print(f"      Priority: {finding.priority_score:.1f}/100")
                print(f"      Scanner: {finding.scanner.value}")
                print()
        
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_trivy_scan():
    """Example 2: Scan with Trivy for dependencies"""
    print("\n" + "=" * 80)
    print("Example 2: Multi-Scanner with Trivy")
    print("=" * 80)
    
    orchestrator = ScanOrchestrator()
    
    # Enable all three scanners
    print("\n1. Enabling all scanners...")
    orchestrator.enable_scanner(ScannerType.BANDIT, min_severity="LOW")
    orchestrator.enable_scanner(ScannerType.SEMGREP, config="p/security-audit")
    
    try:
        from security_assistant.scanners.trivy_scanner import TrivySeverity
        orchestrator.enable_scanner(
            ScannerType.TRIVY,
            min_severity=TrivySeverity.MEDIUM,
            skip_db_update=True
        )
        print("   ✓ Bandit enabled")
        print("   ✓ Semgrep enabled")
        print("   ✓ Trivy enabled")
    except Exception as e:
        print(f"   ✗ Trivy not available: {e}")
        print("   ✓ Bandit enabled")
        print("   ✓ Semgrep enabled")
    
    # Scan
    print("\n2. Scanning project...")
    target_dir = "."
    
    try:
        result = orchestrator.scan_directory(target_dir, recursive=True)
        
        print("\n3. Comprehensive Scan Results:")
        print(f"   Execution time: {result.execution_time_seconds:.2f}s")
        print(f"   Unique findings: {len(result.deduplicated_findings)}")
        
        # Group by category
        by_category = {}
        for finding in result.deduplicated_findings:
            cat = finding.category
            by_category[cat] = by_category.get(cat, 0) + 1
        
        print("\n4. Findings by Category:")
        for category, count in sorted(by_category.items()):
            print(f"   {category}: {count}")
        
        # Show fixable vulnerabilities
        fixable = [f for f in result.deduplicated_findings if f.fix_available]
        if fixable:
            print(f"\n5. Fixable Vulnerabilities: {len(fixable)}")
            for finding in fixable[:5]:
                print(f"   • {finding.title}")
                print(f"     Fix: {finding.fix_version or finding.fix_guidance}")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_custom_deduplication():
    """Example 3: Custom deduplication strategies"""
    print("\n" + "=" * 80)
    print("Example 3: Deduplication Strategies")
    print("=" * 80)
    
    target_dir = "security_assistant/scanners"
    
    # Test different strategies
    strategies = ["location", "content", "both"]
    
    for strategy in strategies:
        print(f"\n{strategy.upper()} Strategy:")
        print("-" * 40)
        
        orchestrator = ScanOrchestrator(
            enable_deduplication=True,
            dedup_strategy=strategy
        )
        
        orchestrator.enable_scanner(ScannerType.BANDIT)
        orchestrator.enable_scanner(ScannerType.SEMGREP, config="auto")
        
        try:
            result = orchestrator.scan_directory(target_dir)
            
            print(f"Total findings: {result.total_findings}")
            print(f"Unique findings: {len(result.deduplicated_findings)}")
            print(f"Duplicates removed: {result.duplicates_removed}")
            print(f"Deduplication rate: {(result.duplicates_removed / result.total_findings * 100) if result.total_findings > 0 else 0:.1f}%")
            
        except Exception as e:
            print(f"Error: {e}")


def example_gitlab_integration():
    """Example 4: Create GitLab issues from findings"""
    print("\n" + "=" * 80)
    print("Example 4: GitLab Integration")
    print("=" * 80)
    
    # Initialize orchestrator
    orchestrator = ScanOrchestrator()
    orchestrator.enable_scanner(ScannerType.BANDIT, min_severity="HIGH")
    orchestrator.enable_scanner(ScannerType.SEMGREP, config="p/security-audit")
    
    # Scan
    print("\n1. Scanning for high-severity issues...")
    target_dir = "security_assistant"
    
    try:
        result = orchestrator.scan_directory(target_dir)
        
        print(f"   Found {len(result.deduplicated_findings)} unique findings")
        
        # Convert to issues (top 10 priority)
        print("\n2. Converting top 10 findings to GitLab issues...")
        issues = orchestrator.result_to_issues(
            result,
            project_name="Security Assistant",
            top_n=10
        )
        
        print(f"   Created {len(issues)} issue objects")
        
        # Show issue preview
        if issues:
            print("\n3. Issue Preview (first issue):")
            print(f"   Title: {issues[0].title}")
            print(f"   Labels: {', '.join(issues[0].labels)}")
            print(f"   Confidential: {issues[0].confidential}")
            print("\n   Description (first 200 chars):")
            print(f"   {issues[0].description[:200]}...")
        
        # Note: Actual GitLab API call would be:
        # gitlab_api = GitLabAPI(token="your-token", project_id="your-project")
        # for issue in issues:
        #     gitlab_api.create_issue(issue)
        
        print("\n4. To create issues in GitLab:")
        print("   - Set GITLAB_TOKEN environment variable")
        print("   - Set GITLAB_PROJECT_ID environment variable")
        print("   - Uncomment GitLab API code above")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_single_file_scan():
    """Example 5: Scan a single file"""
    print("\n" + "=" * 80)
    print("Example 5: Single File Scan")
    print("=" * 80)
    
    orchestrator = ScanOrchestrator()
    orchestrator.enable_scanner(ScannerType.BANDIT)
    orchestrator.enable_scanner(ScannerType.SEMGREP, config="auto")
    
    # Scan a single file
    target_file = "security_assistant/orchestrator.py"
    
    print(f"\n1. Scanning file: {target_file}")
    
    try:
        result = orchestrator.scan_file(target_file)
        
        print("\n2. Results:")
        print(f"   Execution time: {result.execution_time_seconds:.2f}s")
        print(f"   Findings: {len(result.deduplicated_findings)}")
        
        if result.deduplicated_findings:
            print("\n3. Findings:")
            for finding in result.deduplicated_findings:
                print(f"   • [{finding.severity.value}] {finding.title}")
                print(f"     Line {finding.line_start}: {finding.description[:60]}...")
        else:
            print("\n3. ✓ No issues found!")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")


def example_performance_comparison():
    """Example 6: Compare parallel vs sequential execution"""
    print("\n" + "=" * 80)
    print("Example 6: Performance Comparison")
    print("=" * 80)
    
    target_dir = "security_assistant"
    
    # Parallel execution (default)
    print("\n1. Parallel Execution (3 workers):")
    orchestrator_parallel = ScanOrchestrator(max_workers=3)
    orchestrator_parallel.enable_scanner(ScannerType.BANDIT)
    orchestrator_parallel.enable_scanner(ScannerType.SEMGREP, config="auto")
    
    try:
        result_parallel = orchestrator_parallel.scan_directory(target_dir)
        print(f"   Time: {result_parallel.execution_time_seconds:.2f}s")
        print(f"   Findings: {len(result_parallel.deduplicated_findings)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Sequential execution (1 worker)
    print("\n2. Sequential Execution (1 worker):")
    orchestrator_sequential = ScanOrchestrator(max_workers=1)
    orchestrator_sequential.enable_scanner(ScannerType.BANDIT)
    orchestrator_sequential.enable_scanner(ScannerType.SEMGREP, config="auto")
    
    try:
        result_sequential = orchestrator_sequential.scan_directory(target_dir)
        print(f"   Time: {result_sequential.execution_time_seconds:.2f}s")
        print(f"   Findings: {len(result_sequential.deduplicated_findings)}")
        
        # Calculate speedup
        if result_sequential.execution_time_seconds > 0:
            speedup = result_sequential.execution_time_seconds / result_parallel.execution_time_seconds
            print(f"\n3. Speedup: {speedup:.2f}x faster with parallel execution")
    except Exception as e:
        print(f"   Error: {e}")


def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("MULTI-SCANNER ORCHESTRATION EXAMPLES")
    print("=" * 80)
    
    examples = [
        ("Basic Scan", example_basic_scan),
        ("Trivy Integration", example_trivy_scan),
        ("Deduplication Strategies", example_custom_deduplication),
        ("GitLab Integration", example_gitlab_integration),
        ("Single File Scan", example_single_file_scan),
        ("Performance Comparison", example_performance_comparison),
    ]
    
    print("\nAvailable examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    print(f"  {len(examples) + 1}. Run all examples")
    
    try:
        choice = input(f"\nSelect example (1-{len(examples) + 1}): ")
        choice = int(choice)
        
        if 1 <= choice <= len(examples):
            examples[choice - 1][1]()
        elif choice == len(examples) + 1:
            for name, func in examples:
                func()
        else:
            print("Invalid choice")
    except (ValueError, KeyboardInterrupt):
        print("\nExiting...")
    
    print("\n" + "=" * 80)
    print("Examples complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
