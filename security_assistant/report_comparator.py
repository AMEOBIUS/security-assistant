"""
Report Comparison and Diff Analysis for Security Assistant

This module provides functionality to compare two security scan results
and generate diff reports showing:
- New findings (appeared in latest scan)
- Fixed findings (disappeared from latest scan)
- Changed findings (severity/details changed)
- Unchanged findings (same in both scans)
- Trend analysis (security posture improvement/degradation)

Version: 1.0.0
"""

import logging
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .orchestrator import (
    OrchestrationResult,
    UnifiedFinding,
    FindingSeverity,
    ScannerType
)


# Configure logging
logger = logging.getLogger(__name__)


class FindingStatus(str, Enum):
    """Status of a finding when comparing two scans"""
    NEW = "NEW"  # Appeared in latest scan
    FIXED = "FIXED"  # Disappeared from latest scan
    CHANGED = "CHANGED"  # Present in both but details changed
    UNCHANGED = "UNCHANGED"  # Same in both scans


class TrendDirection(str, Enum):
    """Overall security trend direction"""
    IMPROVED = "IMPROVED"  # Fewer/less severe findings
    DEGRADED = "DEGRADED"  # More/more severe findings
    STABLE = "STABLE"  # No significant change


@dataclass
class FindingDiff:
    """
    Represents a finding with its comparison status.
    
    Tracks how a finding changed between baseline and latest scans.
    """
    finding: UnifiedFinding
    status: FindingStatus
    
    # For CHANGED findings
    previous_severity: Optional[FindingSeverity] = None
    severity_changed: bool = False
    
    # Metadata
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    
    @property
    def severity_improved(self) -> bool:
        """Check if severity improved (became less severe)"""
        if not self.severity_changed or not self.previous_severity:
            return False
        
        severity_order = [
            FindingSeverity.CRITICAL,
            FindingSeverity.HIGH,
            FindingSeverity.MEDIUM,
            FindingSeverity.LOW,
            FindingSeverity.INFO,
        ]
        
        prev_idx = severity_order.index(self.previous_severity)
        curr_idx = severity_order.index(self.finding.severity)
        
        return curr_idx > prev_idx  # Lower index = more severe
    
    @property
    def severity_degraded(self) -> bool:
        """Check if severity degraded (became more severe)"""
        if not self.severity_changed or not self.previous_severity:
            return False
        
        return not self.severity_improved


@dataclass
class ComparisonResult:
    """
    Results from comparing two scan results.
    
    Contains categorized findings and trend analysis.
    """
    # Scan metadata
    baseline_scan: OrchestrationResult
    latest_scan: OrchestrationResult
    comparison_time: datetime = field(default_factory=datetime.now)
    
    # Categorized findings
    new_findings: List[FindingDiff] = field(default_factory=list)
    fixed_findings: List[FindingDiff] = field(default_factory=list)
    changed_findings: List[FindingDiff] = field(default_factory=list)
    unchanged_findings: List[FindingDiff] = field(default_factory=list)
    
    # Statistics
    total_new: int = 0
    total_fixed: int = 0
    total_changed: int = 0
    total_unchanged: int = 0
    
    # Severity changes
    severity_improved_count: int = 0
    severity_degraded_count: int = 0
    
    # Trend analysis
    trend_direction: TrendDirection = TrendDirection.STABLE
    trend_score: float = 0.0  # Positive = improved, Negative = degraded
    
    # Severity breakdown changes
    baseline_severity_counts: Dict[FindingSeverity, int] = field(default_factory=dict)
    latest_severity_counts: Dict[FindingSeverity, int] = field(default_factory=dict)
    severity_delta: Dict[FindingSeverity, int] = field(default_factory=dict)
    
    @property
    def has_new_critical(self) -> bool:
        """Check if any new CRITICAL findings"""
        return any(
            f.finding.severity == FindingSeverity.CRITICAL
            for f in self.new_findings
        )
    
    @property
    def has_new_high(self) -> bool:
        """Check if any new HIGH findings"""
        return any(
            f.finding.severity == FindingSeverity.HIGH
            for f in self.new_findings
        )
    
    @property
    def critical_fixed(self) -> int:
        """Count of fixed CRITICAL findings"""
        return sum(
            1 for f in self.fixed_findings
            if f.finding.severity == FindingSeverity.CRITICAL
        )
    
    @property
    def high_fixed(self) -> int:
        """Count of fixed HIGH findings"""
        return sum(
            1 for f in self.fixed_findings
            if f.finding.severity == FindingSeverity.HIGH
        )
    
    @property
    def net_change(self) -> int:
        """Net change in findings (positive = more findings)"""
        return self.total_new - self.total_fixed
    
    @property
    def improvement_percentage(self) -> float:
        """
        Calculate improvement percentage.
        
        Returns:
            Positive percentage = improvement (fewer findings)
            Negative percentage = degradation (more findings)
        """
        baseline_total = len(self.baseline_scan.deduplicated_findings)
        if baseline_total == 0:
            return 0.0
        
        latest_total = len(self.latest_scan.deduplicated_findings)
        change = baseline_total - latest_total
        
        return (change / baseline_total) * 100


class ReportComparator:
    """
    Compare two security scan results and generate diff reports.
    
    Features:
    - Finding matching across scans
    - Status categorization (new/fixed/changed/unchanged)
    - Severity change tracking
    - Trend analysis
    - Diff report generation
    
    Example:
        >>> comparator = ReportComparator()
        >>> comparison = comparator.compare(baseline_result, latest_result)
        >>> print(f"New findings: {comparison.total_new}")
        >>> print(f"Fixed findings: {comparison.total_fixed}")
        >>> print(f"Trend: {comparison.trend_direction.value}")
    """
    
    # Weights for trend score calculation
    SEVERITY_TREND_WEIGHTS = {
        FindingSeverity.CRITICAL: 10.0,
        FindingSeverity.HIGH: 5.0,
        FindingSeverity.MEDIUM: 2.0,
        FindingSeverity.LOW: 1.0,
        FindingSeverity.INFO: 0.5,
    }
    
    def __init__(
        self,
        matching_strategy: str = "content",  # "content", "location", "both"
        track_severity_changes: bool = True,
    ):
        """
        Initialize report comparator.
        
        Args:
            matching_strategy: How to match findings across scans:
                - "content": Match by title + file + code hash
                - "location": Match by file + line range
                - "both": Require both content and location match
            track_severity_changes: Track severity changes in matched findings
        """
        self.matching_strategy = matching_strategy
        self.track_severity_changes = track_severity_changes
        
        logger.info(
            f"Initialized ReportComparator: strategy={matching_strategy}, "
            f"track_severity={track_severity_changes}"
        )
    
    def compare(
        self,
        baseline: OrchestrationResult,
        latest: OrchestrationResult,
    ) -> ComparisonResult:
        """
        Compare two scan results.
        
        Args:
            baseline: Earlier/baseline scan result
            latest: Latest/current scan result
        
        Returns:
            ComparisonResult with categorized findings and trends
        
        Example:
            >>> baseline = orchestrator.scan_directory("src/")
            >>> # ... make code changes ...
            >>> latest = orchestrator.scan_directory("src/")
            >>> comparison = comparator.compare(baseline, latest)
            >>> 
            >>> print(f"New issues: {comparison.total_new}")
            >>> print(f"Fixed issues: {comparison.total_fixed}")
            >>> print(f"Trend: {comparison.trend_direction.value}")
        """
        logger.info(
            f"Comparing scans: baseline={len(baseline.deduplicated_findings)} findings, "
            f"latest={len(latest.deduplicated_findings)} findings"
        )
        
        # Build finding maps for matching
        baseline_map = self._build_finding_map(baseline.deduplicated_findings)
        latest_map = self._build_finding_map(latest.deduplicated_findings)
        
        # Categorize findings
        new_findings = []
        fixed_findings = []
        changed_findings = []
        unchanged_findings = []
        
        # Find new and changed findings
        for key, latest_finding in latest_map.items():
            if key not in baseline_map:
                # New finding
                diff = FindingDiff(
                    finding=latest_finding,
                    status=FindingStatus.NEW,
                    first_seen=latest.scan_time,
                    last_seen=latest.scan_time,
                )
                new_findings.append(diff)
            else:
                # Existing finding - check if changed
                baseline_finding = baseline_map[key]
                
                if self.track_severity_changes and baseline_finding.severity != latest_finding.severity:
                    # Severity changed
                    diff = FindingDiff(
                        finding=latest_finding,
                        status=FindingStatus.CHANGED,
                        previous_severity=baseline_finding.severity,
                        severity_changed=True,
                        first_seen=baseline.scan_time,
                        last_seen=latest.scan_time,
                    )
                    changed_findings.append(diff)
                else:
                    # Unchanged
                    diff = FindingDiff(
                        finding=latest_finding,
                        status=FindingStatus.UNCHANGED,
                        first_seen=baseline.scan_time,
                        last_seen=latest.scan_time,
                    )
                    unchanged_findings.append(diff)
        
        # Find fixed findings
        for key, baseline_finding in baseline_map.items():
            if key not in latest_map:
                # Fixed finding
                diff = FindingDiff(
                    finding=baseline_finding,
                    status=FindingStatus.FIXED,
                    first_seen=baseline.scan_time,
                    last_seen=baseline.scan_time,
                )
                fixed_findings.append(diff)
        
        # Calculate severity change counts
        severity_improved = sum(1 for f in changed_findings if f.severity_improved)
        severity_degraded = sum(1 for f in changed_findings if f.severity_degraded)
        
        # Build result
        result = ComparisonResult(
            baseline_scan=baseline,
            latest_scan=latest,
            new_findings=new_findings,
            fixed_findings=fixed_findings,
            changed_findings=changed_findings,
            unchanged_findings=unchanged_findings,
            total_new=len(new_findings),
            total_fixed=len(fixed_findings),
            total_changed=len(changed_findings),
            total_unchanged=len(unchanged_findings),
            severity_improved_count=severity_improved,
            severity_degraded_count=severity_degraded,
        )
        
        # Calculate severity breakdowns
        result.baseline_severity_counts = self._count_by_severity(baseline.deduplicated_findings)
        result.latest_severity_counts = self._count_by_severity(latest.deduplicated_findings)
        result.severity_delta = self._calculate_severity_delta(
            result.baseline_severity_counts,
            result.latest_severity_counts
        )
        
        # Calculate trend
        result.trend_score = self._calculate_trend_score(result)
        result.trend_direction = self._determine_trend_direction(result.trend_score)
        
        logger.info(
            f"Comparison complete: {result.total_new} new, {result.total_fixed} fixed, "
            f"{result.total_changed} changed, trend={result.trend_direction.value}"
        )
        
        return result
    
    def _build_finding_map(
        self,
        findings: List[UnifiedFinding]
    ) -> Dict[str, UnifiedFinding]:
        """
        Build a map of findings using matching strategy.
        
        Returns:
            Dict mapping finding key to finding
        """
        finding_map = {}
        
        for finding in findings:
            key = self._get_finding_key(finding)
            finding_map[key] = finding
        
        return finding_map
    
    def _get_finding_key(self, finding: UnifiedFinding) -> str:
        """
        Get unique key for finding based on matching strategy.
        
        Strategies:
        - content: title + file + code hash
        - location: file + line range
        - both: content + location
        """
        if self.matching_strategy == "content":
            return finding.content_key
        elif self.matching_strategy == "location":
            return finding.location_key
        else:  # "both"
            return f"{finding.content_key}|{finding.location_key}"
    
    def _count_by_severity(
        self,
        findings: List[UnifiedFinding]
    ) -> Dict[FindingSeverity, int]:
        """Count findings by severity."""
        counts = {}
        for finding in findings:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        return counts
    
    def _calculate_severity_delta(
        self,
        baseline_counts: Dict[FindingSeverity, int],
        latest_counts: Dict[FindingSeverity, int]
    ) -> Dict[FindingSeverity, int]:
        """
        Calculate delta in severity counts.
        
        Returns:
            Dict with severity deltas (positive = increase, negative = decrease)
        """
        delta = {}
        
        all_severities = set(baseline_counts.keys()) | set(latest_counts.keys())
        
        for severity in all_severities:
            baseline_count = baseline_counts.get(severity, 0)
            latest_count = latest_counts.get(severity, 0)
            delta[severity] = latest_count - baseline_count
        
        return delta
    
    def _calculate_trend_score(self, result: ComparisonResult) -> float:
        """
        Calculate trend score.
        
        Positive score = improvement (security posture improved)
        Negative score = degradation (security posture degraded)
        
        Factors:
        - Fixed findings (positive)
        - New findings (negative)
        - Severity changes (weighted)
        """
        score = 0.0
        
        # Fixed findings contribute positively (weighted by severity)
        for diff in result.fixed_findings:
            weight = self.SEVERITY_TREND_WEIGHTS.get(diff.finding.severity, 1.0)
            score += weight
        
        # New findings contribute negatively (weighted by severity)
        for diff in result.new_findings:
            weight = self.SEVERITY_TREND_WEIGHTS.get(diff.finding.severity, 1.0)
            score -= weight
        
        # Severity improvements contribute positively
        for diff in result.changed_findings:
            if diff.severity_improved:
                prev_weight = self.SEVERITY_TREND_WEIGHTS.get(diff.previous_severity, 1.0)
                curr_weight = self.SEVERITY_TREND_WEIGHTS.get(diff.finding.severity, 1.0)
                score += (prev_weight - curr_weight) * 0.5
            elif diff.severity_degraded:
                prev_weight = self.SEVERITY_TREND_WEIGHTS.get(diff.previous_severity, 1.0)
                curr_weight = self.SEVERITY_TREND_WEIGHTS.get(diff.finding.severity, 1.0)
                score -= (curr_weight - prev_weight) * 0.5
        
        return score
    
    def _determine_trend_direction(self, trend_score: float) -> TrendDirection:
        """
        Determine trend direction from score.
        
        Args:
            trend_score: Calculated trend score
        
        Returns:
            TrendDirection enum value
        """
        # Thresholds for trend determination
        IMPROVEMENT_THRESHOLD = 2.0
        DEGRADATION_THRESHOLD = -2.0
        
        if trend_score >= IMPROVEMENT_THRESHOLD:
            return TrendDirection.IMPROVED
        elif trend_score <= DEGRADATION_THRESHOLD:
            return TrendDirection.DEGRADED
        else:
            return TrendDirection.STABLE
    
    def generate_summary(self, result: ComparisonResult) -> str:
        """
        Generate a text summary of the comparison.
        
        Args:
            result: ComparisonResult to summarize
        
        Returns:
            Formatted text summary
        
        Example:
            >>> summary = comparator.generate_summary(comparison)
            >>> print(summary)
        """
        lines = []
        
        # Header
        lines.append("=" * 70)
        lines.append("SECURITY SCAN COMPARISON REPORT")
        lines.append("=" * 70)
        lines.append("")
        
        # Scan info
        lines.append(f"Baseline Scan: {result.baseline_scan.scan_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Latest Scan:   {result.latest_scan.scan_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Target:        {result.latest_scan.target}")
        lines.append("")
        
        # Overall trend
        trend_emoji = {
            TrendDirection.IMPROVED: "✅",
            TrendDirection.STABLE: "➖",
            TrendDirection.DEGRADED: "❌",
        }
        
        lines.append(f"Overall Trend: {trend_emoji[result.trend_direction]} {result.trend_direction.value}")
        lines.append(f"Trend Score:   {result.trend_score:+.1f}")
        lines.append(f"Improvement:   {result.improvement_percentage:+.1f}%")
        lines.append("")
        
        # Summary statistics
        lines.append("Summary:")
        lines.append(f"  🆕 New findings:       {result.total_new}")
        lines.append(f"  ✅ Fixed findings:     {result.total_fixed}")
        lines.append(f"  🔄 Changed findings:   {result.total_changed}")
        lines.append(f"  ➖ Unchanged findings: {result.total_unchanged}")
        lines.append(f"  📊 Net change:         {result.net_change:+d}")
        lines.append("")
        
        # Severity breakdown
        lines.append("Severity Breakdown:")
        lines.append(f"  {'Severity':<12} {'Baseline':>10} {'Latest':>10} {'Delta':>10}")
        lines.append(f"  {'-'*12} {'-'*10} {'-'*10} {'-'*10}")
        
        for severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH, 
                        FindingSeverity.MEDIUM, FindingSeverity.LOW, FindingSeverity.INFO]:
            baseline_count = result.baseline_severity_counts.get(severity, 0)
            latest_count = result.latest_severity_counts.get(severity, 0)
            delta = result.severity_delta.get(severity, 0)
            delta_str = f"{delta:+d}" if delta != 0 else "0"
            
            lines.append(f"  {severity.value:<12} {baseline_count:>10} {latest_count:>10} {delta_str:>10}")
        
        lines.append("")
        
        # Critical new findings
        if result.has_new_critical:
            lines.append("⚠️  WARNING: New CRITICAL findings detected!")
            critical_new = [f for f in result.new_findings if f.finding.severity == FindingSeverity.CRITICAL]
            for diff in critical_new[:5]:  # Show top 5
                lines.append(f"  - {diff.finding.title} ({diff.finding.file_path})")
            lines.append("")
        
        # High priority fixes
        if result.critical_fixed > 0 or result.high_fixed > 0:
            lines.append(f"✅ Good news: {result.critical_fixed} CRITICAL and {result.high_fixed} HIGH findings fixed!")
            lines.append("")
        
        # Severity changes
        if result.severity_improved_count > 0 or result.severity_degraded_count > 0:
            lines.append("Severity Changes:")
            lines.append(f"  ⬇️  Improved:  {result.severity_improved_count}")
            lines.append(f"  ⬆️  Degraded:  {result.severity_degraded_count}")
            lines.append("")
        
        # Footer
        lines.append("=" * 70)
        
        return "\n".join(lines)
    
    def get_top_new_findings(
        self,
        result: ComparisonResult,
        limit: int = 10
    ) -> List[FindingDiff]:
        """
        Get top new findings by priority score.
        
        Args:
            result: ComparisonResult
            limit: Maximum number of findings to return
        
        Returns:
            List of top new findings sorted by priority
        """
        return sorted(
            result.new_findings,
            key=lambda f: f.finding.priority_score,
            reverse=True
        )[:limit]
    
    def get_top_fixed_findings(
        self,
        result: ComparisonResult,
        limit: int = 10
    ) -> List[FindingDiff]:
        """
        Get top fixed findings by priority score.
        
        Args:
            result: ComparisonResult
            limit: Maximum number of findings to return
        
        Returns:
            List of top fixed findings sorted by priority
        """
        return sorted(
            result.fixed_findings,
            key=lambda f: f.finding.priority_score,
            reverse=True
        )[:limit]
