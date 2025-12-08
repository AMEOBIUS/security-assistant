"""
Example: Report Comparison and Diff Analysis

This example demonstrates how to compare two security scan results
and analyze trends over time.

Features demonstrated:
- Comparing baseline and latest scans
- Detecting new/fixed/changed findings
- Severity change tracking
- Trend analysis
- Summary generation
- Top findings extraction
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security_assistant.orchestrator import (
    ScanOrchestrator,
    ScannerType,
)
from security_assistant.report_comparator import (
    ReportComparator,
    TrendDirection,
)


def example_basic_comparison():
    """Example 1: Basic scan comparison"""
    print("=" * 70)
    print("Example 1: Basic Scan Comparison")
    print("=" * 70)
    print()
    
    # Set up orchestrator
    orchestrator = ScanOrchestrator()
    orchestrator.enable_scanner(ScannerType.BANDIT)
    orchestrator.enable_scanner(ScannerType.SEMGREP)
    
    # Simulate baseline scan (e.g., from last week)
    print("Running baseline scan...")
    baseline_result = orchestrator.scan_directory("security_assistant")
    print(f"Baseline: {len(baseline_result.deduplicated_findings)} findings")
    print()
    
    # Simulate latest scan (current state)
    print("Running latest scan...")
    latest_result = orchestrator.scan_directory("security_assistant")
    print(f"Latest: {len(latest_result.deduplicated_findings)} findings")
    print()
    
    # Compare scans
    comparator = ReportComparator()
    comparison = comparator.compare(baseline_result, latest_result)
    
    # Print results
    print(f"New findings: {comparison.total_new}")
    print(f"Fixed findings: {comparison.total_fixed}")
    print(f"Changed findings: {comparison.total_changed}")
    print(f"Unchanged findings: {comparison.total_unchanged}")
    print(f"Trend: {comparison.trend_direction.value}")
    print()


def example_trend_analysis():
    """Example 2: Detailed trend analysis"""
    print("=" * 70)
    print("Example 2: Detailed Trend Analysis")
    print("=" * 70)
    print()
    
    # Set up orchestrator
    orchestrator = ScanOrchestrator()
    orchestrator.enable_scanner(ScannerType.BANDIT)
    orchestrator.enable_scanner(ScannerType.SEMGREP)
    
    # Run scans
    baseline_result = orchestrator.scan_directory("security_assistant")
    latest_result = orchestrator.scan_directory("security_assistant")
    
    # Compare with trend tracking
    comparator = ReportComparator(
        matching_strategy="content",
        track_severity_changes=True
    )
    comparison = comparator.compare(baseline_result, latest_result)
    
    # Analyze trend
    print(f"Trend Direction: {comparison.trend_direction.value}")
    print(f"Trend Score: {comparison.trend_score:+.1f}")
    print(f"Improvement: {comparison.improvement_percentage:+.1f}%")
    print(f"Net Change: {comparison.net_change:+d} findings")
    print()
    
    # Severity breakdown
    print("Severity Changes:")
    print(f"  {'Severity':<12} {'Baseline':>10} {'Latest':>10} {'Delta':>10}")
    print(f"  {'-'*12} {'-'*10} {'-'*10} {'-'*10}")
    
    from security_assistant.orchestrator import FindingSeverity
    for severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH, 
                    FindingSeverity.MEDIUM, FindingSeverity.LOW]:
        baseline_count = comparison.baseline_severity_counts.get(severity, 0)
        latest_count = comparison.latest_severity_counts.get(severity, 0)
        delta = comparison.severity_delta.get(severity, 0)
        delta_str = f"{delta:+d}" if delta != 0 else "0"
        
        print(f"  {severity.value:<12} {baseline_count:>10} {latest_count:>10} {delta_str:>10}")
    
    print()


def example_new_critical_findings():
    """Example 3: Detect new critical findings"""
    print("=" * 70)
    print("Example 3: Detect New Critical Findings")
    print("=" * 70)
    print()
    
    # Set up orchestrator
    orchestrator = ScanOrchestrator()
    orchestrator.enable_scanner(ScannerType.BANDIT)
    orchestrator.enable_scanner(ScannerType.SEMGREP)
    orchestrator.enable_scanner(ScannerType.TRIVY, scan_types=["vuln"])
    
    # Run scans
    baseline_result = orchestrator.scan_directory("security_assistant")
    latest_result = orchestrator.scan_directory("security_assistant")
    
    # Compare
    comparator = ReportComparator()
    comparison = comparator.compare(baseline_result, latest_result)
    
    # Check for new critical findings
    if comparison.has_new_critical:
        print("⚠️  WARNING: New CRITICAL findings detected!")
        print()
        
        from security_assistant.orchestrator import FindingSeverity
        critical_new = [
            f for f in comparison.new_findings
            if f.finding.severity == FindingSeverity.CRITICAL
        ]
        
        for i, diff in enumerate(critical_new[:5], 1):
            finding = diff.finding
            print(f"{i}. {finding.title}")
            print(f"   File: {finding.file_path}:{finding.line_start}")
            print(f"   Scanner: {finding.scanner.value}")
            print(f"   Priority: {finding.priority_score:.1f}/100")
            print()
    else:
        print("✅ No new critical findings")
        print()


def example_fixed_findings():
    """Example 4: Track fixed findings"""
    print("=" * 70)
    print("Example 4: Track Fixed Findings")
    print("=" * 70)
    print()
    
    # Set up orchestrator
    orchestrator = ScanOrchestrator()
    orchestrator.enable_scanner(ScannerType.BANDIT)
    orchestrator.enable_scanner(ScannerType.SEMGREP)
    
    # Run scans
    baseline_result = orchestrator.scan_directory("security_assistant")
    latest_result = orchestrator.scan_directory("security_assistant")
    
    # Compare
    comparator = ReportComparator()
    comparison = comparator.compare(baseline_result, latest_result)
    
    # Show fixed findings
    if comparison.total_fixed > 0:
        print(f"✅ {comparison.total_fixed} findings fixed!")
        print()
        
        # Get top fixed findings
        top_fixed = comparator.get_top_fixed_findings(comparison, limit=5)
        
        print("Top Fixed Findings:")
        for i, diff in enumerate(top_fixed, 1):
            finding = diff.finding
            print(f"{i}. {finding.severity_emoji} {finding.title}")
            print(f"   File: {finding.file_path}:{finding.line_start}")
            print(f"   Severity: {finding.severity.value}")
            print(f"   Priority: {finding.priority_score:.1f}/100")
            print()
    else:
        print("No findings fixed in this scan")
        print()


def example_severity_changes():
    """Example 5: Track severity changes"""
    print("=" * 70)
    print("Example 5: Track Severity Changes")
    print("=" * 70)
    print()
    
    # Set up orchestrator
    orchestrator = ScanOrchestrator()
    orchestrator.enable_scanner(ScannerType.BANDIT)
    orchestrator.enable_scanner(ScannerType.SEMGREP)
    
    # Run scans
    baseline_result = orchestrator.scan_directory("security_assistant")
    latest_result = orchestrator.scan_directory("security_assistant")
    
    # Compare with severity tracking
    comparator = ReportComparator(track_severity_changes=True)
    comparison = comparator.compare(baseline_result, latest_result)
    
    # Show severity changes
    if comparison.total_changed > 0:
        print(f"🔄 {comparison.total_changed} findings changed")
        print(f"   ⬇️  Improved: {comparison.severity_improved_count}")
        print(f"   ⬆️  Degraded: {comparison.severity_degraded_count}")
        print()
        
        # Show degraded findings
        if comparison.severity_degraded_count > 0:
            print("Severity Degradations:")
            degraded = [f for f in comparison.changed_findings if f.severity_degraded]
            
            for i, diff in enumerate(degraded[:5], 1):
                finding = diff.finding
                print(f"{i}. {finding.title}")
                print(f"   {diff.previous_severity.value} → {finding.severity.value}")
                print(f"   File: {finding.file_path}:{finding.line_start}")
                print()
    else:
        print("No severity changes detected")
        print()


def example_full_summary():
    """Example 6: Generate full comparison summary"""
    print("=" * 70)
    print("Example 6: Full Comparison Summary")
    print("=" * 70)
    print()
    
    # Set up orchestrator
    orchestrator = ScanOrchestrator()
    orchestrator.enable_scanner(ScannerType.BANDIT)
    orchestrator.enable_scanner(ScannerType.SEMGREP)
    
    # Run scans
    baseline_result = orchestrator.scan_directory("security_assistant")
    latest_result = orchestrator.scan_directory("security_assistant")
    
    # Compare
    comparator = ReportComparator()
    comparison = comparator.compare(baseline_result, latest_result)
    
    # Generate and print summary
    summary = comparator.generate_summary(comparison)
    print(summary)


def example_matching_strategies():
    """Example 7: Different matching strategies"""
    print("=" * 70)
    print("Example 7: Matching Strategies")
    print("=" * 70)
    print()
    
    # Set up orchestrator
    orchestrator = ScanOrchestrator()
    orchestrator.enable_scanner(ScannerType.BANDIT)
    
    # Run scans
    baseline_result = orchestrator.scan_directory("security_assistant")
    latest_result = orchestrator.scan_directory("security_assistant")
    
    # Compare with different strategies
    strategies = ["content", "location", "both"]
    
    for strategy in strategies:
        comparator = ReportComparator(matching_strategy=strategy)
        comparison = comparator.compare(baseline_result, latest_result)
        
        print(f"Strategy: {strategy}")
        print(f"  New: {comparison.total_new}")
        print(f"  Fixed: {comparison.total_fixed}")
        print(f"  Changed: {comparison.total_changed}")
        print(f"  Unchanged: {comparison.total_unchanged}")
        print()


def example_top_findings():
    """Example 8: Extract top new/fixed findings"""
    print("=" * 70)
    print("Example 8: Top New and Fixed Findings")
    print("=" * 70)
    print()
    
    # Set up orchestrator
    orchestrator = ScanOrchestrator()
    orchestrator.enable_scanner(ScannerType.BANDIT)
    orchestrator.enable_scanner(ScannerType.SEMGREP)
    
    # Run scans
    baseline_result = orchestrator.scan_directory("security_assistant")
    latest_result = orchestrator.scan_directory("security_assistant")
    
    # Compare
    comparator = ReportComparator()
    comparison = comparator.compare(baseline_result, latest_result)
    
    # Top new findings
    if comparison.total_new > 0:
        print("Top 5 New Findings (by priority):")
        top_new = comparator.get_top_new_findings(comparison, limit=5)
        
        for i, diff in enumerate(top_new, 1):
            finding = diff.finding
            print(f"{i}. {finding.severity_emoji} {finding.title}")
            print(f"   Priority: {finding.priority_score:.1f}/100")
            print(f"   File: {finding.file_path}:{finding.line_start}")
            print()
    
    # Top fixed findings
    if comparison.total_fixed > 0:
        print("Top 5 Fixed Findings (by priority):")
        top_fixed = comparator.get_top_fixed_findings(comparison, limit=5)
        
        for i, diff in enumerate(top_fixed, 1):
            finding = diff.finding
            print(f"{i}. {finding.severity_emoji} {finding.title}")
            print(f"   Priority: {finding.priority_score:.1f}/100")
            print(f"   File: {finding.file_path}:{finding.line_start}")
            print()


def main():
    """Run all examples"""
    examples = [
        ("Basic Comparison", example_basic_comparison),
        ("Trend Analysis", example_trend_analysis),
        ("New Critical Findings", example_new_critical_findings),
        ("Fixed Findings", example_fixed_findings),
        ("Severity Changes", example_severity_changes),
        ("Full Summary", example_full_summary),
        ("Matching Strategies", example_matching_strategies),
        ("Top Findings", example_top_findings),
    ]
    
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "REPORT COMPARISON EXAMPLES" + " " * 27 + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n")
    
    for i, (name, func) in enumerate(examples, 1):
        print(f"\n[{i}/{len(examples)}] {name}")
        print("-" * 70)
        
        try:
            func()
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
