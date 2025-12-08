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


try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False


logger = logging.getLogger(__name__)


class ReportFormat:
    """Supported report formats"""
    HTML = "html"
    PDF = "pdf"
    SARIF = "sarif"
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    TEXT = "text"


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
        # Set template directory
        if template_dir:
            self.template_dir = Path(template_dir)
        else:
            # Use default templates directory
            self.template_dir = Path(__file__).parent.parent / "templates"
        
        self.include_charts = include_charts
        self.include_code_snippets = include_code_snippets
        self.enable_remediation = enable_remediation and REMEDIATION_AVAILABLE
        
        # Initialize Remediation Advisor
        self.remediation_advisor = None
        if self.enable_remediation:
            try:
                self.remediation_advisor = RemediationAdvisor()
                logger.info("🛡️ Remediation Advisor initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Remediation Advisor: {e}")
                self.enable_remediation = False
        
        # Initialize Jinja2 environment if available
        self.jinja_env = None
        if JINJA2_AVAILABLE and self.template_dir.exists():
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.template_dir)),
                autoescape=select_autoescape(['html', 'xml']),
                trim_blocks=True,
                lstrip_blocks=True
            )
            logger.info(f"Jinja2 templates loaded from: {self.template_dir}")
        elif not JINJA2_AVAILABLE:
            logger.warning("Jinja2 not available. Install with: pip install jinja2")
        
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
        
        Example:
            >>> generator.generate_report(
            ...     result,
            ...     "security_report.html",
            ...     format=ReportFormat.HTML,
            ...     title="Security Scan Report"
            ... )
            
            >>> # Use executive template
            >>> generator.generate_report(
            ...     result,
            ...     "executive_report.html",
            ...     format=ReportFormat.HTML,
            ...     template_name="executive.html"
            ... )
        """
        output_path = Path(output_path)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate report based on format
        if format == ReportFormat.HTML:
            content = self._generate_html_report(result, title, template_name, **kwargs)
        elif format == ReportFormat.PDF:
            content = self._generate_pdf_report(result, title, template_name, **kwargs)
        elif format == ReportFormat.SARIF:
            content = self._generate_sarif_report(result, **kwargs)
        elif format == ReportFormat.JSON:
            content = self._generate_json_report(result, **kwargs)
        elif format == ReportFormat.YAML:
            content = self._generate_yaml_report(result, **kwargs)
        elif format == ReportFormat.MARKDOWN:
            content = self._generate_markdown_report(result, title, template_name, **kwargs)
        elif format == ReportFormat.TEXT:
            content = self._generate_text_report(result, title, template_name, **kwargs)
        else:
            raise ValueError(f"Unsupported report format: {format}")
        
        # Write report
        if isinstance(content, str):
            output_path.write_text(content, encoding='utf-8')
        else:
            output_path.write_bytes(content)
        
        logger.info(f"Generated {format} report: {output_path}")
        return str(output_path)
    
    def _prepare_template_context(self, result: OrchestrationResult, title: Optional[str] = None) -> Dict[str, Any]:
        """
        Prepare context data for template rendering.
        
        Args:
            result: OrchestrationResult to extract data from
            title: Report title (optional)
        
        Returns:
            Dictionary with template context
        """
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
        total = result.total_findings
        severity_breakdown = []
        for severity in FindingSeverity:
            count = result.findings_by_severity.get(severity, 0)
            percentage = round((count / total * 100), 1) if total > 0 else 0
            severity_breakdown.append({
                "name": severity.value,
                "count": count,
                "percentage": percentage
            })

        # Prepare scanner breakdown
        scanner_breakdown = []
        for scanner, count in result.findings_by_scanner.items():
            percentage = round((count / total * 100), 1) if total > 0 else 0
            scanner_breakdown.append({
                "name": scanner.value,
                "count": count,
                "percentage": percentage
            })
        
        # Prepare findings
        findings = []
        for finding in sorted(result.deduplicated_findings, key=lambda f: f.priority_score, reverse=True):
            finding_dict = {
                "severity": finding.severity.value,
                "severity_emoji": finding.severity_emoji,
                "title": finding.title,
                "description": finding.description,
                "file_path": finding.file_path,
                "file_name": Path(finding.file_path).name,
                "line_start": finding.line_start,
                "line_end": finding.line_end,
                "scanner": finding.scanner.value,
                "priority_score": round(finding.priority_score, 1),
                "code_snippet": finding.code_snippet,
                "cwe_ids": finding.cwe_ids,
                "fix_available": finding.fix_available,
                "fix_version": finding.fix_version,
                "fix_guidance": finding.fix_guidance,
                "is_active_exploit": finding.is_active_exploit,
                "is_false_positive": finding.is_false_positive,
                "fp_confidence": finding.fp_confidence,
                "fp_reasons": finding.fp_reasons,
            }
            
            # Add ML scoring metadata if available
            if finding.ml_score is not None:
                finding_dict["ml_score"] = round(finding.ml_score, 1)
                finding_dict["has_ml_score"] = True
                if finding.ml_confidence_interval:
                    finding_dict["ml_confidence_lower"] = round(finding.ml_confidence_interval[0], 1)
                    finding_dict["ml_confidence_upper"] = round(finding.ml_confidence_interval[1], 1)
                if finding.epss_score is not None:
                    finding_dict["epss_score"] = round(finding.epss_score * 100, 1)  # Convert to percentage
            else:
                finding_dict["has_ml_score"] = False
            
            # Add Remediation Advice
            if self.enable_remediation and self.remediation_advisor:
                try:
                    # Safely determine vulnerability type
                    vuln_type = finding.title # Default
                    
                    if finding.scanner == ScannerType.BANDIT:
                        bf = finding.raw_data.get("bandit_finding")
                        if bf:
                            # Handle both dict (from JSON/dict conversion) and object (direct from scanner)
                            if isinstance(bf, dict):
                                vuln_type = bf.get("test_id", "") or bf.get("test_name", "") or vuln_type
                            else:
                                vuln_type = getattr(bf, "test_id", "") or getattr(bf, "test_name", "") or vuln_type
                                
                    elif finding.scanner == ScannerType.SEMGREP:
                        sf = finding.raw_data.get("semgrep_finding")
                        if sf:
                            if isinstance(sf, dict):
                                check_id = sf.get("check_id", "")
                            else:
                                check_id = getattr(sf, "check_id", "")
                            
                            if check_id:
                                vuln_type = check_id.split(".")[-1]

                    # Prepare vulnerability data for advisor
                    vuln_data = {
                        "type": vuln_type,
                        "severity": finding.severity.value,
                        "file_path": finding.file_path,
                    }
                    
                    advice = self.remediation_advisor.analyze_vulnerability(vuln_data)

                    if advice:
                        finding_dict["remediation"] = {
                            "description": advice.description,
                            "steps": advice.remediation_steps,
                            "code_example": advice.code_example,
                        }
                except Exception as e:
                    logger.warning(f"Failed to generate remediation advice for {finding.finding_id}: {e}")

            findings.append(finding_dict)

        
        # Top findings for executive summary
        top_findings = findings[:10]  # Top 10
        top_risks = findings[:5]  # Top 5 for executive template
        
        # Load CSS content
        css_file = self.template_dir / "html" / "styles.css"
        css_content = ""
        if css_file.exists():
            css_content = css_file.read_text(encoding='utf-8')
        
        # Prepare chart script
        chart_script = self._generate_chart_script(result)
        
        return {
            "title": title,
            "subtitle": "Comprehensive Security Analysis Report",
            "scan_time": result.scan_time.strftime('%Y-%m-%d %H:%M:%S'),
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
                "execution_time": round(result.execution_time_seconds, 1),
            },
            "severity_breakdown": severity_breakdown,
            "scanner_breakdown": scanner_breakdown,
            "findings": findings,
            "top_findings": top_findings,
            "top_risks": top_risks,
            "include_charts": self.include_charts,
            "include_code_snippets": self.include_code_snippets,
            "css_content": css_content,
            "chart_script": chart_script,
        }
    
    def _generate_chart_script(self, result: OrchestrationResult) -> str:
        """Generate Chart.js script for visualizations."""
        # Prepare data for charts
        severity_data = {
            severity.value: result.findings_by_severity.get(severity, 0)
            for severity in FindingSeverity
        }
        
        scanner_data = {
            scanner.value: count
            for scanner, count in result.findings_by_scanner.items()
        }
        
        # Convert to JSON for JavaScript
        severity_labels = json.dumps(list(severity_data.keys()))
        severity_values = json.dumps(list(severity_data.values()))
        scanner_labels = json.dumps(list(scanner_data.keys()))
        scanner_values = json.dumps(list(scanner_data.values()))
        
        return f"""
// Severity Chart
const severityCtx = document.getElementById('severityChart').getContext('2d');
new Chart(severityCtx, {{
    type: 'bar',
    data: {{
        labels: {severity_labels},
        datasets: [{{
            label: 'Findings by Severity',
            data: {severity_values},
            backgroundColor: [
                '#dc3545',
                '#fd7e14',
                '#ffc107',
                '#28a745',
                '#6c757d'
            ]
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{
            title: {{
                display: true,
                text: 'Findings by Severity'
            }}
        }}
    }}
}});

// Scanner Chart
const scannerCtx = document.getElementById('scannerChart').getContext('2d');
new Chart(scannerCtx, {{
    type: 'pie',
    data: {{
        labels: {scanner_labels},
        datasets: [{{
            label: 'Findings by Scanner',
            data: {scanner_values},
            backgroundColor: [
                '#667eea',
                '#764ba2',
                '#f093fb'
            ]
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{
            title: {{
                display: true,
                text: 'Findings by Scanner'
            }}
        }}
    }}
}});
"""
    
    def _generate_html_report(
        self,
        result: OrchestrationResult,
        title: Optional[str] = None,
        template_name: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate interactive HTML report.
        
        Args:
            result: OrchestrationResult to report on
            title: Report title (optional)
            template_name: Custom template name (optional, e.g., "executive.html")
            **kwargs: Additional template variables
        
        Returns:
            HTML content as string
        """
        # Try to use Jinja2 template if available
        if self.jinja_env and template_name:
            try:
                template_path = f"html/{template_name}"
                template = self.jinja_env.get_template(template_path)
                context = self._prepare_template_context(result, title)
                context.update(kwargs)  # Add any custom variables
                return template.render(**context)
            except Exception as e:
                logger.warning(f"Failed to load template {template_name}: {e}")
                logger.info("Falling back to default HTML generation")
        
        # Try default template
        if self.jinja_env:
            try:
                template = self.jinja_env.get_template("html/default.html")
                context = self._prepare_template_context(result, title)
                context.update(kwargs)
                return template.render(**context)
            except Exception as e:
                logger.warning(f"Failed to load default template: {e}")
                logger.info("Falling back to built-in HTML generation")
        
        # Fallback to built-in HTML generation
        title = title or f"Security Scan Report - {result.target}"
        
        # Build HTML structure
        html_parts = [
            self._html_header(title),
            self._html_summary_section(result),
            self._html_severity_breakdown(result),
            self._html_scanner_breakdown(result),
            self._html_findings_table(result),
            self._html_footer(result),
        ]
        
        if self.include_charts:
            html_parts.insert(3, self._html_charts_section(result))
        
        return "\n".join(html_parts)
    
    def _html_header(self, title: str) -> str:
        """Generate HTML header with CSS."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .content {{
            padding: 40px;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .stat-card h3 {{
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        
        .stat-card.critical {{
            border-left-color: #dc3545;
        }}
        
        .stat-card.high {{
            border-left-color: #fd7e14;
        }}
        
        .stat-card.medium {{
            border-left-color: #ffc107;
        }}
        
        .stat-card.low {{
            border-left-color: #28a745;
        }}
        
        .section {{
            margin-bottom: 40px;
        }}
        
        .section h2 {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #333;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .severity-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .severity-critical {{
            background: #dc3545;
            color: white;
        }}
        
        .severity-high {{
            background: #fd7e14;
            color: white;
        }}
        
        .severity-medium {{
            background: #ffc107;
            color: #333;
        }}
        
        .severity-low {{
            background: #28a745;
            color: white;
        }}
        
        .severity-info {{
            background: #6c757d;
            color: white;
        }}
        
        .scanner-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            background: #e9ecef;
            color: #495057;
        }}
        
        .code-snippet {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 10px 0;
            overflow-x: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }}
        
        .finding-details {{
            display: none;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 4px;
            margin-top: 10px;
        }}
        
        .finding-row {{
            cursor: pointer;
        }}
        
        .finding-row:hover {{
            background: #e9ecef;
        }}

        /* Enrichment Badges */
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 700;
            text-transform: uppercase;
            margin-left: 8px;
        }}

        .badge-exploit {{
            background-color: #dc3545;
            color: white;
            border: 1px solid #a71d2a;
            animation: pulse 2s infinite;
        }}

        .badge-fp {{
            background-color: #6c757d;
            color: white;
            border: 1px solid #545b62;
            opacity: 0.8;
            text-decoration: line-through;
        }}

        .fp-row {{
            opacity: 0.6;
            background-color: #f8f9fa;
        }}
        
        @keyframes pulse {{
            0% {{ box-shadow: 0 0 0 0 rgba(220, 53, 69, 0.4); }}
            70% {{ box-shadow: 0 0 0 10px rgba(220, 53, 69, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(220, 53, 69, 0); }}
        }}
        
        footer {{
            background: #f8f9fa;
            padding: 20px 40px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        
        .chart-container {{
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            
            .container {{
                box-shadow: none;
            }}
            
            .finding-details {{
                display: block !important;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔒 {title}</h1>
            <p>Comprehensive Security Analysis Report</p>
        </header>
"""
    
    def _html_summary_section(self, result: OrchestrationResult) -> str:
        """Generate summary statistics section."""
        return f"""
        <div class="content">
            <div class="section">
                <h2>📊 Executive Summary</h2>
                <div class="summary">
                    <div class="stat-card">
                        <h3>Total Findings</h3>
                        <div class="value">{result.total_findings}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Unique Issues</h3>
                        <div class="value">{len(result.deduplicated_findings)}</div>
                    </div>
                    <div class="stat-card critical">
                        <h3>Critical</h3>
                        <div class="value">{result.critical_count}</div>
                    </div>
                    <div class="stat-card high">
                        <h3>High</h3>
                        <div class="value">{result.high_count}</div>
                    </div>
                    <div class="stat-card medium">
                        <h3>Medium</h3>
                        <div class="value">{result.medium_count}</div>
                    </div>
                    <div class="stat-card low">
                        <h3>Low</h3>
                        <div class="value">{result.low_count}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Scan Time</h3>
                        <div class="value">{result.execution_time_seconds:.1f}s</div>
                    </div>
                    <div class="stat-card">
                        <h3>Duplicates Removed</h3>
                        <div class="value">{result.duplicates_removed}</div>
                    </div>
                </div>
            </div>
"""
    
    def _html_severity_breakdown(self, result: OrchestrationResult) -> str:
        """Generate severity breakdown section."""
        severity_html = """
            <div class="section">
                <h2>🎯 Severity Breakdown</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Severity</th>
                            <th>Count</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        total = len(result.deduplicated_findings)
        if total == 0:
            severity_html += """
                        <tr>
                            <td colspan="3" style="text-align: center;">No findings</td>
                        </tr>
"""
        else:
            for severity in FindingSeverity:
                count = result.findings_by_severity.get(severity, 0)
                percentage = (count / total * 100) if total > 0 else 0
                
                severity_class = severity.value.lower()
                severity_html += f"""
                        <tr>
                            <td><span class="severity-badge severity-{severity_class}">{severity.value}</span></td>
                            <td>{count}</td>
                            <td>{percentage:.1f}%</td>
                        </tr>
"""
        
        severity_html += """
                    </tbody>
                </table>
            </div>
"""
        return severity_html
    
    def _html_scanner_breakdown(self, result: OrchestrationResult) -> str:
        """Generate scanner breakdown section."""
        scanner_html = """
            <div class="section">
                <h2>🔍 Scanner Breakdown</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Scanner</th>
                            <th>Findings</th>
                            <th>Percentage</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        total = len(result.deduplicated_findings)
        for scanner, count in result.findings_by_scanner.items():
            percentage = (count / total * 100) if total > 0 else 0
            scanner_html += f"""
                        <tr>
                            <td><span class="scanner-badge">{scanner.value}</span></td>
                            <td>{count}</td>
                            <td>{percentage:.1f}%</td>
                        </tr>
"""
        
        scanner_html += """
                    </tbody>
                </table>
            </div>
"""
        return scanner_html
    
    def _html_charts_section(self, result: OrchestrationResult) -> str:
        """Generate charts section with Chart.js."""
        # Prepare data for charts
        severity_data = {
            severity.value: result.findings_by_severity.get(severity, 0)
            for severity in FindingSeverity
        }
        
        scanner_data = {
            scanner.value: count
            for scanner, count in result.findings_by_scanner.items()
        }
        
        # Convert to JSON for JavaScript
        severity_labels = json.dumps(list(severity_data.keys()))
        severity_values = json.dumps(list(severity_data.values()))
        scanner_labels = json.dumps(list(scanner_data.keys()))
        scanner_values = json.dumps(list(scanner_data.values()))
        
        return f"""
            <div class="section">
                <h2>📈 Visual Analytics</h2>
                <div class="chart-container">
                    <canvas id="severityChart" width="400" height="200"></canvas>
                </div>
                <div class="chart-container">
                    <canvas id="scannerChart" width="400" height="200"></canvas>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
            <script>
                // Severity Chart
                const severityCtx = document.getElementById('severityChart').getContext('2d');
                new Chart(severityCtx, {{
                    type: 'bar',
                    data: {{
                        labels: {severity_labels},
                        datasets: [{{
                            label: 'Findings by Severity',
                            data: {severity_values},
                            backgroundColor: [
                                '#dc3545',
                                '#fd7e14',
                                '#ffc107',
                                '#28a745',
                                '#6c757d'
                            ]
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            title: {{
                                display: true,
                                text: 'Findings by Severity'
                            }}
                        }}
                    }}
                }});
                
                // Scanner Chart
                const scannerCtx = document.getElementById('scannerChart').getContext('2d');
                new Chart(scannerCtx, {{
                    type: 'pie',
                    data: {{
                        labels: {scanner_labels},
                        datasets: [{{
                            label: 'Findings by Scanner',
                            data: {scanner_values},
                            backgroundColor: [
                                '#667eea',
                                '#764ba2',
                                '#f093fb'
                            ]
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            title: {{
                                display: true,
                                text: 'Findings by Scanner'
                            }}
                        }}
                    }}
                }});
            </script>
"""
    
    def _html_findings_table(self, result: OrchestrationResult) -> str:
        """Generate findings table."""
        # Check if any findings have ML scores
        has_ml_scores = any(f.ml_score is not None for f in result.deduplicated_findings)
        
        findings_html = """
            <div class="section">
                <h2>🔎 Detailed Findings</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Severity</th>
                            <th>Title</th>
                            <th>File</th>
                            <th>Line</th>
                            <th>Scanner</th>
                            <th>Priority</th>
"""
        
        if has_ml_scores:
            findings_html += """
                            <th>ML Score</th>
                            <th>EPSS</th>
"""
        
        findings_html += """
                        </tr>
                    </thead>
                    <tbody>
"""
        
        # Sort by priority score
        sorted_findings = sorted(
            result.deduplicated_findings,
            key=lambda f: f.priority_score,
            reverse=True
        )
        
        for idx, finding in enumerate(sorted_findings):
            severity_class = finding.severity.value.lower()
            file_name = Path(finding.file_path).name
            
            # Determine row classes and badges
            row_class = "finding-row"
            title_badges = ""
            
            if hasattr(finding, 'is_active_exploit') and finding.is_active_exploit:
                title_badges += '<span class="badge badge-exploit">ACTIVE EXPLOIT</span>'
            
            if hasattr(finding, 'is_false_positive') and finding.is_false_positive:
                row_class += " fp-row"
                title_badges += '<span class="badge badge-fp">FALSE POSITIVE</span>'
            
            # Build table row
            row_html = f"""
                        <tr class="{row_class}" onclick="toggleDetails({idx})">
                            <td><span class="severity-badge severity-{severity_class}">{finding.severity.value}</span></td>
                            <td>{finding.title} {title_badges}</td>
                            <td>{file_name}</td>
                            <td>{finding.line_start}</td>
                            <td><span class="scanner-badge">{finding.scanner.value}</span></td>
                            <td>{finding.priority_score:.1f}</td>
"""
            
            # Add ML score columns if available
            if has_ml_scores:
                if finding.ml_score is not None:
                    row_html += f"""
                            <td>{finding.ml_score:.1f}</td>
                            <td>{finding.epss_score * 100:.1f}%</td>
"""
                else:
                    row_html += """
                            <td>-</td>
                            <td>-</td>
"""
            
            colspan = "8" if has_ml_scores else "6"
            row_html += f"""
                        </tr>
                        <tr>
                            <td colspan="{colspan}">
                                <div id="details-{idx}" class="finding-details">
                                    <p><strong>Description:</strong> {finding.description}</p>
"""

            # Add FP details if available
            if hasattr(finding, 'is_false_positive') and finding.is_false_positive:
                row_html += f"""
                                    <div style="background-color: #e2e3e5; padding: 10px; border-radius: 4px; margin-bottom: 10px;">
                                        <strong>⚠️ Likely False Positive</strong> (Confidence: {finding.fp_confidence:.2f})
                                        <ul>
"""
                for reason in finding.fp_reasons:
                    row_html += f"<li>{reason}</li>"
                row_html += """
                                        </ul>
                                    </div>
"""

            row_html += f"""
                                    <p><strong>File:</strong> {finding.file_path}</p>
                                    <p><strong>Lines:</strong> {finding.line_start}-{finding.line_end}</p>
"""
            
            # Add ML score details if available
            if finding.ml_score is not None:
                row_html += f"""
                                    <p><strong>ML Score:</strong> {finding.ml_score:.1f}/100</p>
"""
                if finding.ml_confidence_interval:
                    row_html += f"""
                                    <p><strong>ML Confidence Interval:</strong> [{finding.ml_confidence_interval[0]:.1f}, {finding.ml_confidence_interval[1]:.1f}]</p>
"""
                if finding.epss_score is not None:
                    row_html += f"""
                                    <p><strong>EPSS (Exploit Probability):</strong> {finding.epss_score * 100:.1f}%</p>
"""
            
            findings_html += row_html
            findings_html += """
"""
            
            if self.include_code_snippets and finding.code_snippet:
                findings_html += f"""
                                    <div class="code-snippet">
                                        <pre>{finding.code_snippet}</pre>
                                    </div>
"""
            
            if finding.cwe_ids:
                cwe_links = ", ".join(str(cwe) for cwe in finding.cwe_ids)
                findings_html += f"""
                                    <p><strong>CWE:</strong> {cwe_links}</p>
"""
            
            if finding.fix_available:
                findings_html += f"""
                                    <p><strong>Fix Available:</strong> Yes</p>
"""
                if finding.fix_version:
                    findings_html += f"""
                                    <p><strong>Fix Version:</strong> {finding.fix_version}</p>
"""
            
            # Add Remediation Advice to HTML
            remediation_html = ""
            if self.enable_remediation and self.remediation_advisor:
                try:
                    # Safely determine vulnerability type
                    vuln_type = finding.title # Default
                    
                    if finding.scanner == ScannerType.BANDIT:
                        bf = finding.raw_data.get("bandit_finding")
                        if bf:
                            # Handle both dict (from JSON/dict conversion) and object (direct from scanner)
                            if isinstance(bf, dict):
                                vuln_type = bf.get("test_id", "") or bf.get("test_name", "") or vuln_type
                            else:
                                vuln_type = getattr(bf, "test_id", "") or getattr(bf, "test_name", "") or vuln_type
                                
                    elif finding.scanner == ScannerType.SEMGREP:
                        sf = finding.raw_data.get("semgrep_finding")
                        if sf:
                            if isinstance(sf, dict):
                                check_id = sf.get("check_id", "")
                            else:
                                check_id = getattr(sf, "check_id", "")
                            
                            if check_id:
                                vuln_type = check_id.split(".")[-1]

                    # Prepare vulnerability data for advisor
                    vuln_data = {
                        "type": vuln_type,
                        "severity": finding.severity.value,
                        "file_path": finding.file_path,
                    }
                    
                    advice = self.remediation_advisor.analyze_vulnerability(vuln_data)

                    if advice:
                        remediation_html += f"""
                                    <div class="remediation-section" style="margin-top: 20px; border-top: 1px solid #ddd; padding-top: 10px;">
                                        <h4>🛡️ Recommended Remediation</h4>
                                        <div style="margin: 10px 0;">
                                            <strong>Steps:</strong>
                                            <ul>
"""
                        for step in advice.remediation_steps:
                            remediation_html += f"<li>{step}</li>"
                        
                        remediation_html += """
                                            </ul>
                                        </div>
"""
                        if advice.code_example:
                             remediation_html += f"""
                                        <div style="margin-top: 10px;">
                                            <strong>Secure Example:</strong>
                                            <div class="code-snippet">
                                                <pre>{advice.code_example}</pre>
                                            </div>
                                        </div>
"""
                        remediation_html += """
                                    </div>
"""
                except Exception as e:
                    logger.warning(f"Failed to generate remediation advice for {finding.finding_id}: {e}")

            findings_html += remediation_html

            findings_html += """
                                </div>
                            </td>
                        </tr>
"""
        
        findings_html += """
                    </tbody>
                </table>
            </div>
            
            <script>
                function toggleDetails(idx) {
                    const details = document.getElementById('details-' + idx);
                    if (details.style.display === 'block') {
                        details.style.display = 'none';
                    } else {
                        details.style.display = 'block';
                    }
                }
            </script>
"""
        return findings_html
    
    def _html_footer(self, result: OrchestrationResult) -> str:
        """Generate HTML footer."""
        return f"""
        </div>
        <footer>
            <p>Generated by Security Assistant on {result.scan_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Target: {result.target} | Execution Time: {result.execution_time_seconds:.2f}s</p>
        </footer>
    </div>
</body>
</html>
"""
    
    def _generate_markdown_report(
        self,
        result: OrchestrationResult,
        title: Optional[str] = None,
        template_name: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate Markdown report.
        
        Args:
            result: OrchestrationResult to report on
            title: Report title (optional)
            template_name: Custom template name (optional)
            **kwargs: Additional template variables
        
        Returns:
            Markdown content as string
        """
        # Try to use Jinja2 template if available
        if self.jinja_env and template_name:
            try:
                template_path = f"markdown/{template_name}"
                template = self.jinja_env.get_template(template_path)
                context = self._prepare_template_context(result, title)
                context.update(kwargs)
                return template.render(**context)
            except Exception as e:
                logger.warning(f"Failed to load template {template_name}: {e}")
        
        # Try default template
        if self.jinja_env:
            try:
                template = self.jinja_env.get_template("markdown/default.md")
                context = self._prepare_template_context(result, title)
                context.update(kwargs)
                return template.render(**context)
            except Exception as e:
                logger.warning(f"Failed to load default markdown template: {e}")
        
        # Fallback to built-in generation
        title = title or f"Security Scan Report - {result.target}"
        
        md_parts = [
            f"# {title}\n",
            f"**Generated:** {result.scan_time.strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Target:** `{result.target}`  ",
            f"**Execution Time:** {result.execution_time_seconds:.2f}s\n",
            "---\n",
            "## 📊 Executive Summary\n",
            f"- **Total Findings:** {result.total_findings}",
            f"- **Unique Issues:** {len(result.deduplicated_findings)}",
            f"- **Critical:** {result.critical_count}",
            f"- **High:** {result.high_count}",
            f"- **Medium:** {result.medium_count}",
            f"- **Low:** {result.low_count}",
            f"- **Duplicates Removed:** {result.duplicates_removed}\n",
            "---\n",
            "## 🎯 Severity Breakdown\n",
            "| Severity | Count | Percentage |",
            "|----------|-------|------------|",
        ]
        
        total = len(result.deduplicated_findings)
        for severity in FindingSeverity:
            count = result.findings_by_severity.get(severity, 0)
            percentage = (count / total * 100) if total > 0 else 0
            md_parts.append(f"| {severity.value} | {count} | {percentage:.1f}% |")
        
        md_parts.extend([
            "\n---\n",
            "## 🔍 Scanner Breakdown\n",
            "| Scanner | Findings | Percentage |",
            "|---------|----------|------------|",
        ])
        
        for scanner, count in result.findings_by_scanner.items():
            percentage = (count / total * 100) if total > 0 else 0
            md_parts.append(f"| {scanner.value} | {count} | {percentage:.1f}% |")
        
        md_parts.extend([
            "\n---\n",
            "## 🔎 Top Priority Findings\n",
        ])
        
        for idx, finding in enumerate(result.top_priority_findings, 1):
            md_parts.extend([
                f"\n### {idx}. {finding.severity_emoji} {finding.title}",
                f"**Severity:** {finding.severity.value}  ",
                f"**File:** `{finding.file_path}`  ",
                f"**Lines:** {finding.line_start}-{finding.line_end}  ",
                f"**Scanner:** {finding.scanner.value}  ",
                f"**Priority Score:** {finding.priority_score:.1f}/100\n",
                f"**Description:** {finding.description}\n",
            ])
            
            if self.include_code_snippets and finding.code_snippet:
                md_parts.extend([
                    "**Code:**",
                    "```",
                    finding.code_snippet,
                    "```\n",
                ])
        
        md_parts.append(f"\n---\n*Report generated by Security Assistant*")
        
        return "\n".join(md_parts)
    
    def _generate_text_report(
        self,
        result: OrchestrationResult,
        title: Optional[str] = None,
        template_name: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate plain text report.
        
        Args:
            result: OrchestrationResult to report on
            title: Report title (optional)
            template_name: Custom template name (optional)
            **kwargs: Additional template variables
        
        Returns:
            Plain text content as string
        """
        # Try to use Jinja2 template if available
        if self.jinja_env and template_name:
            try:
                template_path = f"text/{template_name}"
                template = self.jinja_env.get_template(template_path)
                context = self._prepare_template_context(result, title)
                context.update(kwargs)
                return template.render(**context)
            except Exception as e:
                logger.warning(f"Failed to load template {template_name}: {e}")
        
        # Try default template
        if self.jinja_env:
            try:
                template = self.jinja_env.get_template("text/default.txt")
                context = self._prepare_template_context(result, title)
                context.update(kwargs)
                return template.render(**context)
            except Exception as e:
                logger.warning(f"Failed to load default text template: {e}")
        
        # Fallback to built-in generation
        title = title or f"Security Scan Report - {result.target}"
        
        lines = [
            "=" * 80,
            title.center(80),
            "=" * 80,
            "",
            f"Generated: {result.scan_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Target: {result.target}",
            f"Execution Time: {result.execution_time_seconds:.2f}s",
            "",
            "-" * 80,
            "EXECUTIVE SUMMARY",
            "-" * 80,
            f"Total Findings:      {result.total_findings}",
            f"Unique Issues:       {len(result.deduplicated_findings)}",
            f"Critical:            {result.critical_count}",
            f"High:                {result.high_count}",
            f"Medium:              {result.medium_count}",
            f"Low:                 {result.low_count}",
            f"Duplicates Removed:  {result.duplicates_removed}",
            "",
            "-" * 80,
            "TOP PRIORITY FINDINGS",
            "-" * 80,
        ]
        
        for idx, finding in enumerate(result.top_priority_findings, 1):
            lines.extend([
                "",
                f"{idx}. [{finding.severity.value}] {finding.title}",
                f"   File: {finding.file_path}:{finding.line_start}",
                f"   Scanner: {finding.scanner.value}",
                f"   Priority: {finding.priority_score:.1f}/100",
                f"   {finding.description}",
            ])
        
        lines.extend([
            "",
            "=" * 80,
            "Report generated by Security Assistant".center(80),
            "=" * 80,
        ])
        
        return "\n".join(lines)
    
    def _generate_json_report(
        self,
        result: OrchestrationResult,
        **kwargs
    ) -> str:
        """Generate JSON report."""
        report_data = {
            "metadata": {
                "generated_at": result.scan_time.isoformat(),
                "target": result.target,
                "execution_time_seconds": result.execution_time_seconds,
            },
            "summary": {
                "total_findings": result.total_findings,
                "unique_findings": len(result.deduplicated_findings),
                "duplicates_removed": result.duplicates_removed,
                "critical_count": result.critical_count,
                "high_count": result.high_count,
                "medium_count": result.medium_count,
                "low_count": result.low_count,
            },
            "findings_by_severity": {
                severity.value: count
                for severity, count in result.findings_by_severity.items()
            },
            "findings_by_scanner": {
                scanner.value: count
                for scanner, count in result.findings_by_scanner.items()
            },
            "findings": [
                self._finding_to_dict(finding)
                for finding in result.deduplicated_findings
            ],
        }
        
        return json.dumps(report_data, indent=2, default=str)

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

    
    def _generate_yaml_report(
        self,
        result: OrchestrationResult,
        **kwargs
    ) -> str:
        """Generate YAML report."""
        report_data = {
            "metadata": {
                "generated_at": result.scan_time.isoformat(),
                "target": result.target,
                "execution_time_seconds": result.execution_time_seconds,
            },
            "summary": {
                "total_findings": result.total_findings,
                "unique_findings": len(result.deduplicated_findings),
                "duplicates_removed": result.duplicates_removed,
                "critical_count": result.critical_count,
                "high_count": result.high_count,
                "medium_count": result.medium_count,
                "low_count": result.low_count,
            },
            "findings_by_severity": {
                severity.value: count
                for severity, count in result.findings_by_severity.items()
            },
            "findings_by_scanner": {
                scanner.value: count
                for scanner, count in result.findings_by_scanner.items()
            },
            "findings": [
                self._finding_to_dict(finding)
                for finding in result.deduplicated_findings
            ],
        }
        
        return yaml.dump(report_data, default_flow_style=False, sort_keys=False)
    
    def _generate_sarif_report(
        self,
        result: OrchestrationResult,
        **kwargs
    ) -> str:
        """
        Generate SARIF 2.1.0 format report.
        
        SARIF (Static Analysis Results Interchange Format) is an industry-standard
        format for static analysis tools. It's supported by GitHub, GitLab, and
        many other platforms.
        """
        sarif_report = {
            "version": "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "Security Assistant",
                            "version": "1.0.0",
                            "informationUri": "https://gitlab.com/security-assistant",
                            "rules": self._generate_sarif_rules(result),
                        }
                    },
                    "results": self._generate_sarif_results(result),
                    "properties": {
                        "scan_time": result.scan_time.isoformat(),
                        "execution_time_seconds": result.execution_time_seconds,
                        "target": result.target,
                        "total_findings": result.total_findings,
                        "unique_findings": len(result.deduplicated_findings),
                    }
                }
            ]
        }
        
        return json.dumps(sarif_report, indent=2)
    
    def _generate_sarif_rules(self, result: OrchestrationResult) -> List[Dict]:
        """Generate SARIF rules from findings."""
        rules = {}
        
        for finding in result.deduplicated_findings:
            rule_id = f"{finding.scanner.value}-{finding.title.replace(' ', '-').lower()}"
            
            if rule_id not in rules:
                rules[rule_id] = {
                    "id": rule_id,
                    "name": finding.title,
                    "shortDescription": {
                        "text": finding.title
                    },
                    "fullDescription": {
                        "text": finding.description
                    },
                    "defaultConfiguration": {
                        "level": self._severity_to_sarif_level(finding.severity)
                    },
                    "properties": {
                        "category": finding.category,
                        "scanner": finding.scanner.value,
                    }
                }
                
                if finding.cwe_ids:
                    rules[rule_id]["properties"]["cwe"] = finding.cwe_ids
        
        return list(rules.values())
    
    def _generate_sarif_results(self, result: OrchestrationResult) -> List[Dict]:
        """Generate SARIF results from findings."""
        results = []
        
        for finding in result.deduplicated_findings:
            rule_id = f"{finding.scanner.value}-{finding.title.replace(' ', '-').lower()}"
            
            sarif_result = {
                "ruleId": rule_id,
                "level": self._severity_to_sarif_level(finding.severity),
                "message": {
                    "text": finding.description
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": finding.file_path
                            },
                            "region": {
                                "startLine": finding.line_start,
                                "endLine": finding.line_end,
                            }
                        }
                    }
                ],
                "properties": {
                    "priority_score": finding.priority_score,
                    "scanner": finding.scanner.value,
                    "category": finding.category,
                }
            }
            
            if finding.code_snippet:
                sarif_result["locations"][0]["physicalLocation"]["region"]["snippet"] = {
                    "text": finding.code_snippet
                }
            
            if finding.fix_available:
                sarif_result["fixes"] = [
                    {
                        "description": {
                            "text": finding.fix_guidance or "Fix available"
                        }
                    }
                ]
            
            results.append(sarif_result)
        
        return results
    
    def _severity_to_sarif_level(self, severity: FindingSeverity) -> str:
        """Convert FindingSeverity to SARIF level."""
        mapping = {
            FindingSeverity.CRITICAL: "error",
            FindingSeverity.HIGH: "error",
            FindingSeverity.MEDIUM: "warning",
            FindingSeverity.LOW: "note",
            FindingSeverity.INFO: "note",
        }
        return mapping.get(severity, "warning")
    
    def _generate_pdf_report(
        self,
        result: OrchestrationResult,
        title: Optional[str] = None,
        template_name: Optional[str] = None,
        **kwargs
    ) -> bytes:
        """
        Generate PDF report.
        
        Args:
            result: OrchestrationResult to report on
            title: Report title (optional)
            template_name: Custom template name (optional)
            **kwargs: Additional template variables
        
        Returns:
            PDF content as bytes
        
        Note: Requires weasyprint library.
        Install with: pip install weasyprint
        """
        try:
            from weasyprint import HTML
        except ImportError:
            logger.warning("weasyprint not installed, generating HTML instead")
            return self._generate_html_report(result, title, template_name, **kwargs).encode('utf-8')
        
        # Generate HTML first
        html_content = self._generate_html_report(result, title, template_name, **kwargs)
        
        # Convert to PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        return pdf_bytes
    
    def _finding_to_dict(self, finding: UnifiedFinding) -> Dict:
        """Convert UnifiedFinding to dictionary."""
        finding_dict = {
            "finding_id": finding.finding_id,
            "scanner": finding.scanner.value,
            "severity": finding.severity.value,
            "category": finding.category,
            "file_path": finding.file_path,
            "line_start": finding.line_start,
            "line_end": finding.line_end,
            "title": finding.title,
            "description": finding.description,
            "code_snippet": finding.code_snippet if self.include_code_snippets else "",
            "cwe_ids": finding.cwe_ids,
            "owasp_categories": finding.owasp_categories,
            "references": finding.references,
            "fix_available": finding.fix_available,
            "fix_version": finding.fix_version,
            "fix_guidance": finding.fix_guidance,
            "priority_score": finding.priority_score,
            "confidence": finding.confidence,
        }
        
        # Add ML scoring metadata if available
        if finding.ml_score is not None:
            finding_dict["ml_score"] = finding.ml_score
            finding_dict["ml_confidence_interval"] = finding.ml_confidence_interval
            finding_dict["epss_score"] = finding.epss_score
        
        return finding_dict
    
    def generate_comparison_report(
        self,
        comparison_result,  # ComparisonResult from report_comparator
        output_path: str,
        format: str = ReportFormat.HTML,
        title: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate a comparison/diff report.
        
        Args:
            comparison_result: ComparisonResult from ReportComparator
            output_path: Output file path
            format: Report format (html, markdown, text, json)
            title: Report title (optional)
            **kwargs: Format-specific options
        
        Returns:
            Path to generated report
        
        Example:
            >>> from security_assistant.report_comparator import ReportComparator
            >>> comparator = ReportComparator()
            >>> comparison = comparator.compare(baseline, latest)
            >>> generator = ReportGenerator()
            >>> generator.generate_comparison_report(
            ...     comparison,
            ...     "diff_report.html",
            ...     format=ReportFormat.HTML
            ... )
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Generate report based on format
        if format == ReportFormat.HTML:
            content = self._generate_html_comparison_report(comparison_result, title, **kwargs)
        elif format == ReportFormat.MARKDOWN:
            content = self._generate_markdown_comparison_report(comparison_result, title, **kwargs)
        elif format == ReportFormat.TEXT:
            content = self._generate_text_comparison_report(comparison_result, title, **kwargs)
        elif format == ReportFormat.JSON:
            content = self._generate_json_comparison_report(comparison_result, **kwargs)
        else:
            raise ValueError(f"Unsupported comparison report format: {format}")
        
        # Write report
        output_path.write_text(content, encoding='utf-8')
        
        logger.info(f"Generated {format} comparison report: {output_path}")
        return str(output_path)
    
    def _generate_html_comparison_report(
        self,
        comparison,  # ComparisonResult
        title: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate HTML comparison report."""
        title = title or "Security Scan Comparison Report"
        
        # Trend emoji
        from .report_comparator import TrendDirection
        trend_emoji = {
            TrendDirection.IMPROVED: "✅",
            TrendDirection.STABLE: "➖",
            TrendDirection.DEGRADED: "❌",
        }
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
            border-radius: 8px 8px 0 0;
        }}
        header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .content {{ padding: 40px; }}
        .trend-indicator {{
            display: inline-block;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 1.2em;
            font-weight: bold;
            margin: 20px 0;
        }}
        .trend-improved {{ background: #d4edda; color: #155724; }}
        .trend-stable {{ background: #fff3cd; color: #856404; }}
        .trend-degraded {{ background: #f8d7da; color: #721c24; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .stat-card h3 {{
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            margin-bottom: 10px;
        }}
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }}
        .stat-card.new {{ border-left-color: #fd7e14; }}
        .stat-card.fixed {{ border-left-color: #28a745; }}
        .stat-card.changed {{ border-left-color: #ffc107; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        tr:hover {{ background: #f8f9fa; }}
        .severity-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .severity-critical {{ background: #dc3545; color: white; }}
        .severity-high {{ background: #fd7e14; color: white; }}
        .severity-medium {{ background: #ffc107; color: #333; }}
        .severity-low {{ background: #28a745; color: white; }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .status-new {{ background: #fd7e14; color: white; }}
        .status-fixed {{ background: #28a745; color: white; }}
        .status-changed {{ background: #ffc107; color: #333; }}
        .section {{ margin: 40px 0; }}
        .section h2 {{
            font-size: 1.8em;
            margin-bottom: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 {title}</h1>
            <p>Baseline: {comparison.baseline_scan.scan_time.strftime('%Y-%m-%d %H:%M:%S')} → 
               Latest: {comparison.latest_scan.scan_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </header>
        
        <div class="content">
            <div class="section">
                <h2>Overall Trend</h2>
                <div class="trend-indicator trend-{comparison.trend_direction.value.lower()}">
                    {trend_emoji[comparison.trend_direction]} {comparison.trend_direction.value}
                </div>
                <p><strong>Trend Score:</strong> {comparison.trend_score:+.1f}</p>
                <p><strong>Improvement:</strong> {comparison.improvement_percentage:+.1f}%</p>
                <p><strong>Net Change:</strong> {comparison.net_change:+d} findings</p>
            </div>
            
            <div class="section">
                <h2>Summary</h2>
                <div class="summary">
                    <div class="stat-card new">
                        <h3>New Findings</h3>
                        <div class="value">{comparison.total_new}</div>
                    </div>
                    <div class="stat-card fixed">
                        <h3>Fixed Findings</h3>
                        <div class="value">{comparison.total_fixed}</div>
                    </div>
                    <div class="stat-card changed">
                        <h3>Changed Findings</h3>
                        <div class="value">{comparison.total_changed}</div>
                    </div>
                    <div class="stat-card">
                        <h3>Unchanged</h3>
                        <div class="value">{comparison.total_unchanged}</div>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <h2>Severity Breakdown</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Severity</th>
                            <th>Baseline</th>
                            <th>Latest</th>
                            <th>Delta</th>
                        </tr>
                    </thead>
                    <tbody>
"""
        
        for severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH, 
                        FindingSeverity.MEDIUM, FindingSeverity.LOW]:
            baseline_count = comparison.baseline_severity_counts.get(severity, 0)
            latest_count = comparison.latest_severity_counts.get(severity, 0)
            delta = comparison.severity_delta.get(severity, 0)
            delta_str = f"{delta:+d}" if delta != 0 else "0"
            severity_class = severity.value.lower()
            
            html += f"""
                        <tr>
                            <td><span class="severity-badge severity-{severity_class}">{severity.value}</span></td>
                            <td>{baseline_count}</td>
                            <td>{latest_count}</td>
                            <td>{delta_str}</td>
                        </tr>
"""
        
        html += """
                    </tbody>
                </table>
            </div>
"""
        
        # New findings
        if comparison.total_new > 0:
            html += """
            <div class="section">
                <h2>🆕 New Findings</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Severity</th>
                            <th>Title</th>
                            <th>File</th>
                            <th>Line</th>
                            <th>Priority</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            for diff in sorted(comparison.new_findings, key=lambda f: f.finding.priority_score, reverse=True)[:20]:
                finding = diff.finding
                severity_class = finding.severity.value.lower()
                file_name = Path(finding.file_path).name
                
                html += f"""
                        <tr>
                            <td><span class="severity-badge severity-{severity_class}">{finding.severity.value}</span></td>
                            <td>{finding.title}</td>
                            <td>{file_name}</td>
                            <td>{finding.line_start}</td>
                            <td>{finding.priority_score:.1f}</td>
                        </tr>
"""
            
            html += """
                    </tbody>
                </table>
            </div>
"""
        
        # Fixed findings
        if comparison.total_fixed > 0:
            html += """
            <div class="section">
                <h2>✅ Fixed Findings</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Severity</th>
                            <th>Title</th>
                            <th>File</th>
                            <th>Line</th>
                            <th>Priority</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            for diff in sorted(comparison.fixed_findings, key=lambda f: f.finding.priority_score, reverse=True)[:20]:
                finding = diff.finding
                severity_class = finding.severity.value.lower()
                file_name = Path(finding.file_path).name
                
                html += f"""
                        <tr>
                            <td><span class="severity-badge severity-{severity_class}">{finding.severity.value}</span></td>
                            <td>{finding.title}</td>
                            <td>{file_name}</td>
                            <td>{finding.line_start}</td>
                            <td>{finding.priority_score:.1f}</td>
                        </tr>
"""
            
            html += """
                    </tbody>
                </table>
            </div>
"""
        
        html += """
        </div>
    </div>
</body>
</html>
"""
        
        return html
    
    def _generate_markdown_comparison_report(
        self,
        comparison,  # ComparisonResult
        title: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate Markdown comparison report."""
        from .report_comparator import TrendDirection
        
        title = title or "Security Scan Comparison Report"
        
        trend_emoji = {
            TrendDirection.IMPROVED: "✅",
            TrendDirection.STABLE: "➖",
            TrendDirection.DEGRADED: "❌",
        }
        
        md = [
            f"# {title}\n",
            f"**Baseline:** {comparison.baseline_scan.scan_time.strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Latest:** {comparison.latest_scan.scan_time.strftime('%Y-%m-%d %H:%M:%S')}  ",
            f"**Target:** `{comparison.latest_scan.target}`\n",
            "---\n",
            "## Overall Trend\n",
            f"**Status:** {trend_emoji[comparison.trend_direction]} {comparison.trend_direction.value}  ",
            f"**Trend Score:** {comparison.trend_score:+.1f}  ",
            f"**Improvement:** {comparison.improvement_percentage:+.1f}%  ",
            f"**Net Change:** {comparison.net_change:+d} findings\n",
            "---\n",
            "## Summary\n",
            f"- 🆕 **New Findings:** {comparison.total_new}",
            f"- ✅ **Fixed Findings:** {comparison.total_fixed}",
            f"- 🔄 **Changed Findings:** {comparison.total_changed}",
            f"- ➖ **Unchanged:** {comparison.total_unchanged}\n",
            "---\n",
            "## Severity Breakdown\n",
            "| Severity | Baseline | Latest | Delta |",
            "|----------|----------|--------|-------|",
        ]
        
        for severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH, 
                        FindingSeverity.MEDIUM, FindingSeverity.LOW]:
            baseline_count = comparison.baseline_severity_counts.get(severity, 0)
            latest_count = comparison.latest_severity_counts.get(severity, 0)
            delta = comparison.severity_delta.get(severity, 0)
            delta_str = f"{delta:+d}" if delta != 0 else "0"
            
            md.append(f"| {severity.value} | {baseline_count} | {latest_count} | {delta_str} |")
        
        # New findings
        if comparison.total_new > 0:
            md.extend([
                "\n---\n",
                "## 🆕 New Findings\n",
            ])
            
            for i, diff in enumerate(sorted(comparison.new_findings, key=lambda f: f.finding.priority_score, reverse=True)[:10], 1):
                finding = diff.finding
                md.extend([
                    f"\n### {i}. {finding.severity_emoji} {finding.title}",
                    f"**Severity:** {finding.severity.value}  ",
                    f"**File:** `{finding.file_path}:{finding.line_start}`  ",
                    f"**Priority:** {finding.priority_score:.1f}/100\n",
                ])
        
        # Fixed findings
        if comparison.total_fixed > 0:
            md.extend([
                "\n---\n",
                "## ✅ Fixed Findings\n",
            ])
            
            for i, diff in enumerate(sorted(comparison.fixed_findings, key=lambda f: f.finding.priority_score, reverse=True)[:10], 1):
                finding = diff.finding
                md.extend([
                    f"\n### {i}. {finding.severity_emoji} {finding.title}",
                    f"**Severity:** {finding.severity.value}  ",
                    f"**File:** `{finding.file_path}:{finding.line_start}`  ",
                    f"**Priority:** {finding.priority_score:.1f}/100\n",
                ])
        
        md.append("\n---\n*Comparison report generated by Security Assistant*")
        
        return "\n".join(md)
    
    def _generate_text_comparison_report(
        self,
        comparison,  # ComparisonResult
        title: Optional[str] = None,
        **kwargs
    ) -> str:
        """Generate plain text comparison report."""
        from .report_comparator import ReportComparator
        
        comparator = ReportComparator()
        return comparator.generate_summary(comparison)
    
    def _generate_json_comparison_report(
        self,
        comparison,  # ComparisonResult
        **kwargs
    ) -> str:
        """Generate JSON comparison report."""
        report_data = {
            "metadata": {
                "baseline_scan_time": comparison.baseline_scan.scan_time.isoformat(),
                "latest_scan_time": comparison.latest_scan.scan_time.isoformat(),
                "comparison_time": comparison.comparison_time.isoformat(),
                "target": comparison.latest_scan.target,
            },
            "trend": {
                "direction": comparison.trend_direction.value,
                "score": comparison.trend_score,
                "improvement_percentage": comparison.improvement_percentage,
                "net_change": comparison.net_change,
            },
            "summary": {
                "total_new": comparison.total_new,
                "total_fixed": comparison.total_fixed,
                "total_changed": comparison.total_changed,
                "total_unchanged": comparison.total_unchanged,
                "severity_improved_count": comparison.severity_improved_count,
                "severity_degraded_count": comparison.severity_degraded_count,
            },
            "severity_breakdown": {
                "baseline": {k.value: v for k, v in comparison.baseline_severity_counts.items()},
                "latest": {k.value: v for k, v in comparison.latest_severity_counts.items()},
                "delta": {k.value: v for k, v in comparison.severity_delta.items()},
            },
            "new_findings": [
                {
                    "title": diff.finding.title,
                    "severity": diff.finding.severity.value,
                    "file_path": diff.finding.file_path,
                    "line_start": diff.finding.line_start,
                    "priority_score": diff.finding.priority_score,
                }
                for diff in comparison.new_findings
            ],
            "fixed_findings": [
                {
                    "title": diff.finding.title,
                    "severity": diff.finding.severity.value,
                    "file_path": diff.finding.file_path,
                    "line_start": diff.finding.line_start,
                    "priority_score": diff.finding.priority_score,
                }
                for diff in comparison.fixed_findings
            ],
        }
        
        return json.dumps(report_data, indent=2, default=str)

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

