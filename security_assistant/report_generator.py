"""
Report Generation Module for Security Assistant

This module provides comprehensive report generation capabilities:
- HTML reports with interactive charts and filtering
- PDF reports for executive summaries
- SARIF format for tool integration
- JSON/YAML for programmatic access
- Markdown for documentation
- Custom templates support with Jinja2

Version: 2.0.0
"""

import logging
import json
import yaml
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

from .orchestrator import (
    OrchestrationResult,
    UnifiedFinding,
    FindingSeverity,
    ScannerType,
    BulkScanResult
)

# Remediation Advisor Integration
try:
    from .remediation.advisor import RemediationAdvisor, RemediationAdvice
    REMEDIATION_AVAILABLE = True
except ImportError:
    REMEDIATION_AVAILABLE = False


from .reporting.reporter_factory import ReporterFactory
from .reporting.base_reporter import ReportFormat

logger = logging.getLogger(__name__)

class ReportGenerator:
    """
    Generate security scan reports in multiple formats.
    
    Features:
    - Multiple output formats (HTML, PDF, SARIF, JSON, YAML, Markdown)
    - Customizable templates with Jinja2
    - Interactive HTML reports with charts
    - Executive-friendly PDF summaries
    - SARIF for CI/CD integration
    - Automated Remediation Advice integration
    
    Example:
        >>> generator = ReportGenerator()
        >>> result = orchestrator.scan_directory("src/")
        >>> generator.generate_report(
        ...     result,
        ...     output_path="report.html",
        ...     format=ReportFormat.HTML
        ... )
    """
    
    def __init__(
        self,
        template_dir: Optional[str] = None,
        include_charts: bool = True,
        include_code_snippets: bool = True,
        enable_remediation: bool = True,
    ):
        """
        Initialize report generator.
        
        Args:
            template_dir: Custom template directory (optional)
            include_charts: Include charts in HTML reports (default: True)
            include_code_snippets: Include code snippets (default: True)
            enable_remediation: Enable automated remediation advice (default: True)
        """
        self.template_dir = template_dir
        self.include_charts = include_charts
        self.include_code_snippets = include_code_snippets
        self.enable_remediation = enable_remediation
        
        logger.info(
            f"Initialized ReportGenerator: charts={include_charts}, "
            f"snippets={include_code_snippets}, templates={self.template_dir}, "
            f"remediation={self.enable_remediation}"
        )

    
    def generate_report(
        self,
        result: OrchestrationResult,
        output_path: str,
        format: str = ReportFormat.HTML,
        title: Optional[str] = None,
        template_name: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate a security scan report.
        
        Args:
            result: OrchestrationResult to report on
            output_path: Output file path
            format: Report format (html, pdf, sarif, json, yaml, markdown, text)
            title: Report title (optional)
            template_name: Custom template name (optional, e.g., "executive.html")
            **kwargs: Format-specific options
        
        Returns:
            Path to generated report
        """
        try:
            # Prepare reporter kwargs
            reporter_kwargs = {
                'include_code_snippets': self.include_code_snippets,
                'include_remediation': self.enable_remediation,
            }
            
            # Add HTML-specific args only for HTML reporter
            if format.lower() in ['html', 'htm']:
                reporter_kwargs['include_charts'] = self.include_charts
                reporter_kwargs['template_dir'] = self.template_dir
            
            # Create reporter via factory
            reporter = ReporterFactory.create(format, **reporter_kwargs)
            
            # Add common args
            kwargs['title'] = title
            kwargs['template_name'] = template_name
            
            # Generate and save
            return reporter.generate_to_file(result, output_path, **kwargs)
            
        except Exception as e:
            logger.error(f"Failed to generate {format} report: {e}")
            raise
    
    def generate_bulk_report(
        self,
        bulk_result: BulkScanResult,
        output_dir: str,
        formats: List[str] = [ReportFormat.HTML, ReportFormat.JSON]
    ) -> Dict[str, str]:
        """
        Generate aggregated reports for bulk scan results.
        
        Args:
            bulk_result: BulkScanResult object
            output_dir: Directory to save reports
            formats: List of formats to generate (html, json, csv)
            
        Returns:
            Dictionary mapping format to report path
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        generated_reports = {}
        
        # CSV Export
        if "csv" in formats:
            csv_path = output_path / "bulk_report.csv"
            self._generate_bulk_csv(bulk_result, csv_path)
            generated_reports["csv"] = str(csv_path)
            
        # JSON Export
        if ReportFormat.JSON in formats:
            json_path = output_path / "bulk_report.json"
            self._generate_bulk_json(bulk_result, json_path)
            generated_reports["json"] = str(json_path)
            
        # HTML Summary (basic implementation for now)
        if ReportFormat.HTML in formats:
            html_path = output_path / "bulk_report.html"
            self._generate_bulk_html(bulk_result, html_path)
            generated_reports["html"] = str(html_path)
            
        return generated_reports

    def _generate_bulk_csv(self, bulk_result: BulkScanResult, output_path: Path):
        import csv
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow([
                "Target", "Finding ID", "Severity", "Title", "File", "Line", 
                "Scanner", "Category", "CWE", "Fix Available"
            ])
            
            for target, result in bulk_result.results.items():
                for finding in result.deduplicated_findings:
                    writer.writerow([
                        target,
                        finding.finding_id,
                        finding.severity.value,
                        finding.title,
                        finding.file_path,
                        finding.line_start,
                        finding.scanner.value,
                        finding.category,
                        ",".join(finding.cwe_ids),
                        finding.fix_available
                    ])

    def _generate_bulk_json(self, bulk_result: BulkScanResult, output_path: Path):
        data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_targets": len(bulk_result.results),
                "total_time_seconds": bulk_result.total_execution_time
            },
            "aggregated_stats": bulk_result.get_aggregated_stats(),
            "targets": {}
        }
        
        for target, result in bulk_result.results.items():
            data["targets"][target] = {
                "stats": {
                    "total": result.total_findings,
                    "critical": result.critical_count,
                    "high": result.high_count,
                    "medium": result.medium_count
                },
                "findings": [self._finding_to_dict(f) for f in result.deduplicated_findings]
            }
            
        output_path.write_text(json.dumps(data, indent=2, default=str), encoding='utf-8')

    def _generate_bulk_html(self, bulk_result: BulkScanResult, output_path: Path):
        # Simple HTML aggregation
        stats = bulk_result.get_aggregated_stats()
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Bulk Security Scan Report</title>
    <style>
        body {{ font-family: system-ui; padding: 20px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .critical {{ color: #dc3545; font-weight: bold; }}
        .high {{ color: #fd7e14; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>Bulk Security Scan Report</h1>
    <p>Generated: {datetime.now()}</p>
    
    <h2>Aggregated Statistics</h2>
    <ul>
        <li>Targets Scanned: {stats['targets_scanned']}</li>
        <li>Total Findings: {stats['total_findings']}</li>
        <li class="critical">Critical: {stats['critical']}</li>
        <li class="high">High: {stats['high']}</li>
        <li>Total Time: {stats['total_time']:.2f}s</li>
    </ul>
    
    <h2>Target Breakdown</h2>
    <table>
        <thead>
            <tr>
                <th>Target</th>
                <th>Total Findings</th>
                <th>Critical</th>
                <th>High</th>
                <th>Medium</th>
                <th>Low</th>
            </tr>
        </thead>
        <tbody>"""
        
        for target, result in bulk_result.results.items():
            html += f"""
            <tr>
                <td>{target}</td>
                <td>{result.total_findings}</td>
                <td class="critical">{result.critical_count}</td>
                <td class="high">{result.high_count}</td>
                <td>{result.medium_count}</td>
                <td>{result.low_count}</td>
            </tr>"""
            
        html += """
        </tbody>
    </table>
</body>
</html>"""
        
        output_path.write_text(html, encoding='utf-8')

    
    def _finding_to_dict(self, finding: UnifiedFinding) -> Dict[str, Any]:
        """Convert a finding object to dictionary."""
        # Helper to maintain compatibility
        reporter = ReporterFactory.create("json", include_code_snippets=self.include_code_snippets)
        return reporter._serialize_findings([finding])[0]

    def generate_comparison_report(
        self,
        comparison_result,  # ComparisonResult from report_comparator
        output_path: str,
        **kwargs
    ) -> str:
        """
        Generate a comparison/diff report.
        
        Args:
            comparison_result: ComparisonResult from ReportComparator
            output_path: Output file path
            **kwargs: Additional options (ignored for now)
        
        Returns:
            Path to generated report
        
        Example:
            >>> from security_assistant.report_comparator import ReportComparator
            >>> comparator = ReportComparator()
            >>> comparison = comparator.compare(baseline, latest)
            >>> generator = ReportGenerator()
            >>> generator.generate_comparison_report(comparison, "diff_report.txt")
        """
        from .report_comparator import ReportComparator
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use ReportComparator to generate summary
        comparator = ReportComparator()
        content = comparator.generate_summary(comparison_result)
        
        # Write report
        output_path.write_text(content, encoding='utf-8')
        
        logger.info(f"Generated comparison report: {output_path}")
        return str(output_path)
    
