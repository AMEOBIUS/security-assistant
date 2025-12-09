"""
Test fixtures and helpers for reporter tests.

Provides common fixtures for creating test data.
"""

from datetime import datetime
from typing import List

from security_assistant.orchestrator import (
    FindingSeverity,
    OrchestrationResult,
    ScannerType,
    UnifiedFinding,
)


def create_test_result(
    target: str = "test_project",
    findings: List[UnifiedFinding] = None,
    execution_time: float = 1.0
) -> OrchestrationResult:
    """
    Create a test OrchestrationResult with correct parameters.
    
    Args:
        target: Target name
        findings: List of findings (default: empty)
        execution_time: Execution time in seconds
    
    Returns:
        OrchestrationResult instance
    """
    findings = findings or []
    
    # Calculate severity counts
    findings_by_severity = {}
    for finding in findings:
        findings_by_severity[finding.severity] = findings_by_severity.get(finding.severity, 0) + 1
    
    # Calculate scanner counts
    findings_by_scanner = {}
    for finding in findings:
        findings_by_scanner[finding.scanner] = findings_by_scanner.get(finding.scanner, 0) + 1
    
    # Sort by priority for top findings
    top_priority = sorted(findings, key=lambda f: f.priority_score, reverse=True)[:10]
    
    return OrchestrationResult(
        target=target,
        all_findings=findings,
        deduplicated_findings=findings,
        scanner_results={},
        scan_time=datetime.now(),
        execution_time_seconds=execution_time,
        total_findings=len(findings),
        findings_by_scanner=findings_by_scanner,
        findings_by_severity=findings_by_severity,
        duplicates_removed=0,
        errors=[]
    )


def create_test_finding(
    finding_id: str = "test-001",
    scanner: ScannerType = ScannerType.BANDIT,
    severity: FindingSeverity = FindingSeverity.HIGH,
    title: str = "Test Finding",
    file_path: str = "test/file.py",
    line_start: int = 10,
    code_snippet: str = "test code",
    priority_score: float = 80.0
) -> UnifiedFinding:
    """
    Create a test UnifiedFinding.
    
    Args:
        finding_id: Finding ID
        scanner: Scanner type
        severity: Severity level
        title: Finding title
        file_path: File path
        line_start: Line number
        code_snippet: Code snippet
        priority_score: Priority score
    
    Returns:
        UnifiedFinding instance
    """
    return UnifiedFinding(
        finding_id=finding_id,
        scanner=scanner,
        severity=severity,
        confidence=0.9,
        category="Security",
        file_path=file_path,
        line_start=line_start,
        line_end=line_start + 5,
        title=title,
        description=f"Description for {title}",
        code_snippet=code_snippet,
        cwe_ids=["CWE-89"],
        owasp_categories=["A03:2021"],
        references=[],
        fix_available=True,
        fix_guidance="Fix guidance",
        priority_score=priority_score,
        raw_data={}
    )
