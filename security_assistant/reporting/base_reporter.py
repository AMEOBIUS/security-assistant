"""
Base Reporter Abstract Class

Provides common functionality for all report generators:
- Context preparation
- Finding serialization
- Common utilities

All reporters (HTML, JSON, SARIF, etc.) extend this base class.

Version: 1.0.0 (Session 47 Refactoring)
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ReportFormat(str, Enum):
    """Supported report formats"""

    HTML = "html"
    PDF = "pdf"
    SARIF = "sarif"
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    TEXT = "text"


class BaseReporter(ABC):
    """
    Abstract base class for report generators.

    Provides common functionality:
    - Context preparation for templates
    - Finding serialization
    - Statistics calculation

    Subclasses must implement:
    - format: Report format enum
    - generate(): Generate report content

    Example:
        class MyReporter(BaseReporter):
            @property
            def format(self) -> ReportFormat:
                return ReportFormat.JSON

            def generate(self, result, **kwargs) -> str:
                context = self._prepare_context(result)
                return json.dumps(context)
    """

    def __init__(
        self,
        include_code_snippets: bool = True,
        include_remediation: bool = True,
        max_findings: Optional[int] = None,
        llm_service=None,
    ):
        """
        Initialize reporter.

        Args:
            include_code_snippets: Include code snippets in report
            include_remediation: Include remediation advice
            max_findings: Maximum findings to include (None = all)
            llm_service: LLM service for AI features (optional)
        """
        self.include_code_snippets = include_code_snippets
        self.include_remediation = include_remediation
        self.max_findings = max_findings
        self.llm_service = llm_service

    @property
    @abstractmethod
    def format(self) -> ReportFormat:
        """Report format identifier."""
        pass

    @abstractmethod
    def generate(self, result: Any, **kwargs) -> str:
        """
        Generate report content.

        Args:
            result: OrchestrationResult to report on
            **kwargs: Format-specific options

        Returns:
            Report content as string
        """
        pass

    def generate_to_file(self, result: Any, output_path: str, **kwargs) -> str:
        """
        Generate report and save to file.

        Args:
            result: OrchestrationResult to report on
            output_path: Output file path
            **kwargs: Format-specific options

        Returns:
            Path to generated report
        """
        content = self.generate(result, **kwargs)

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            path.write_text(content, encoding="utf-8")

        logger.info(f"Generated {self.format.value} report: {path}")
        return str(path)

    def _prepare_context(
        self, result: Any, title: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Prepare common context data for templates/serialization.

        Args:
            result: OrchestrationResult
            title: Report title (optional)

        Returns:
            Dictionary with context data
        """
        from ..orchestrator import FindingSeverity

        title = title or f"Security Scan Report - {result.target}"

        # Calculate overall risk level
        if result.critical_count > 0:
            overall_risk = "CRITICAL"
        elif result.high_count > 0:
            overall_risk = "HIGH"
        elif result.medium_count > 0:
            overall_risk = "MEDIUM"
        elif result.low_count > 0:
            overall_risk = "LOW"
        else:
            overall_risk = "NONE"

        # Prepare severity breakdown
        total = len(result.deduplicated_findings)
        severity_breakdown = []
        for severity in FindingSeverity:
            count = result.findings_by_severity.get(severity, 0)
            percentage = round((count / total * 100), 1) if total > 0 else 0
            severity_breakdown.append(
                {"name": severity.value, "count": count, "percentage": percentage}
            )

        # Prepare scanner breakdown
        scanner_breakdown = []
        for scanner, count in result.findings_by_scanner.items():
            percentage = round((count / total * 100), 1) if total > 0 else 0
            scanner_breakdown.append(
                {"name": scanner.value, "count": count, "percentage": percentage}
            )

        # Prepare findings
        findings = self._serialize_findings(result.deduplicated_findings)

        # Apply max_findings limit
        if self.max_findings and len(findings) > self.max_findings:
            findings = findings[: self.max_findings]

        return {
            "title": title,
            "subtitle": "Security Analysis Report",
            "generated_at": datetime.now().isoformat(),
            "scan_time": result.scan_time.strftime("%Y-%m-%d %H:%M:%S"),
            "target": result.target,
            "execution_time": round(result.execution_time_seconds, 2),
            "overall_risk": overall_risk,
            "summary": {
                "total_findings": result.total_findings,
                "unique_findings": len(result.deduplicated_findings),
                "critical_count": result.critical_count,
                "high_count": result.high_count,
                "medium_count": result.medium_count,
                "low_count": result.low_count,
                "duplicates_removed": result.duplicates_removed,
            },
            "severity_breakdown": severity_breakdown,
            "scanner_breakdown": scanner_breakdown,
            "findings": findings,
            "top_findings": findings[:10],
        }

    def _serialize_findings(self, findings: List[Any]) -> List[Dict[str, Any]]:
        """
        Serialize findings to dictionaries.

        Args:
            findings: List of UnifiedFinding objects

        Returns:
            List of serialized finding dictionaries
        """
        serialized = []

        for finding in sorted(findings, key=lambda f: f.priority_score, reverse=True):
            finding_dict = {
                "finding_id": finding.finding_id,
                "severity": finding.severity.value,
                "title": finding.title,
                "description": finding.description,
                "file_path": finding.file_path,
                "file_name": Path(finding.file_path).name,
                "line_start": finding.line_start,
                "line_end": finding.line_end,
                "scanner": finding.scanner.value,
                "category": finding.category,
                "priority_score": round(finding.priority_score, 1),
                "cwe_ids": finding.cwe_ids,
                "owasp_categories": finding.owasp_categories,
                "references": finding.references,
                "fix_available": finding.fix_available,
                "fix_version": finding.fix_version,
                "confidence": finding.confidence,
            }

            # Optional fields
            if self.include_code_snippets and finding.code_snippet:
                finding_dict["code_snippet"] = finding.code_snippet

            if finding.fix_guidance:
                finding_dict["fix_guidance"] = finding.fix_guidance

            # Enrichment data
            if hasattr(finding, "is_active_exploit"):
                finding_dict["is_active_exploit"] = finding.is_active_exploit

            if hasattr(finding, "is_false_positive"):
                finding_dict["is_false_positive"] = finding.is_false_positive
                finding_dict["fp_confidence"] = finding.fp_confidence
                finding_dict["fp_reasons"] = finding.fp_reasons

            if hasattr(finding, "is_reachable"):
                finding_dict["is_reachable"] = finding.is_reachable
                if hasattr(finding, "reachability_confidence"):
                    finding_dict["reachability_confidence"] = (
                        finding.reachability_confidence
                    )

            if hasattr(finding, "epss_score") and finding.epss_score is not None:
                finding_dict["epss_score"] = finding.epss_score  # Raw score (0.0-1.0)

            # ML scores
            if finding.ml_score is not None:
                finding_dict["ml_score"] = round(finding.ml_score, 1)
                if finding.ml_confidence_interval:
                    finding_dict["ml_confidence_interval"] = [
                        round(finding.ml_confidence_interval[0], 1),
                        round(finding.ml_confidence_interval[1], 1),
                    ]

            serialized.append(finding_dict)

        return serialized

    def _get_severity_color(self, severity: str) -> str:
        """Get color for severity level."""
        colors = {
            "CRITICAL": "#dc3545",
            "HIGH": "#fd7e14",
            "MEDIUM": "#ffc107",
            "LOW": "#28a745",
            "INFO": "#6c757d",
        }
        return colors.get(severity.upper(), "#6c757d")

    def _get_severity_emoji(self, severity: str) -> str:
        """Get emoji for severity level."""
        emojis = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
            "INFO": "⚪",
        }
        return emojis.get(severity.upper(), "❓")
