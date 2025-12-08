"""
HTML Reporter Implementation

Generates interactive HTML reports with charts and filtering.

Version: 1.0.0
"""

import json
import logging
from typing import Any, Dict, Optional
from pathlib import Path

from .base_reporter import BaseReporter, ReportFormat
from ..orchestrator import FindingSeverity

logger = logging.getLogger(__name__)

class HTMLReporter(BaseReporter):
    """
    Generates interactive HTML reports.
    Uses built-in HTML generation or Jinja2 templates if available.
    """
    
    def __init__(
        self,
        include_code_snippets: bool = True,
        include_remediation: bool = True,
        max_findings: Optional[int] = None,
        include_charts: bool = True,
        template_dir: Optional[str] = None
    ):
        super().__init__(include_code_snippets, include_remediation, max_findings)
        self.include_charts = include_charts
        self.template_dir = Path(template_dir) if template_dir else None
        
        # Initialize Jinja2 if available
        self.jinja_env = None
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape
            if self.template_dir and self.template_dir.exists():
                self.jinja_env = Environment(
                    loader=FileSystemLoader(str(self.template_dir)),
                    autoescape=select_autoescape(['html', 'xml']),
                    trim_blocks=True,
                    lstrip_blocks=True
                )
        except ImportError:
            pass

    @property
    def format(self) -> ReportFormat:
        return ReportFormat.HTML
    
    def generate(self, result: Any, **kwargs) -> str:
        """
        Generate HTML report.
        
        Args:
            result: OrchestrationResult
            **kwargs: Template variables
        
        Returns:
            HTML content
        """
        context = self._prepare_context(result, kwargs.get('title'))
        
        # Add HTML-specific context
        context.update({
            "include_charts": self.include_charts,
            "chart_script": self._generate_chart_script(result) if self.include_charts else "",
            "css_content": self._get_css_content()
        })
        context.update(kwargs)

        # Use Jinja2 template if available
        if self.jinja_env:
            template_name = kwargs.get('template_name', 'default.html')
            try:
                template = self.jinja_env.get_template(f"html/{template_name}")
                return template.render(**context)
            except Exception as e:
                logger.warning(f"Failed to render template {template_name}: {e}")
        
        # Fallback to built-in generation
        return self._generate_builtin_html(context)

    def _generate_chart_script(self, result: Any) -> str:
        """Generate Chart.js script."""
        severity_data = {
            severity.value: result.findings_by_severity.get(severity, 0)
            for severity in FindingSeverity
        }
        
        scanner_data = {
            scanner.value: count
            for scanner, count in result.findings_by_scanner.items()
        }
        
        return f"""
// Severity Chart
const severityCtx = document.getElementById('severityChart').getContext('2d');
new Chart(severityCtx, {{
    type: 'bar',
    data: {{
        labels: {json.dumps(list(severity_data.keys()))},
        datasets: [{{
            label: 'Findings by Severity',
            data: {json.dumps(list(severity_data.values()))},
            backgroundColor: ['#dc3545', '#fd7e14', '#ffc107', '#28a745', '#6c757d']
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{ title: {{ display: true, text: 'Findings by Severity' }} }}
    }}
}});

// Scanner Chart
const scannerCtx = document.getElementById('scannerChart').getContext('2d');
new Chart(scannerCtx, {{
    type: 'pie',
    data: {{
        labels: {json.dumps(list(scanner_data.keys()))},
        datasets: [{{
            label: 'Findings by Scanner',
            data: {json.dumps(list(scanner_data.values()))},
            backgroundColor: ['#667eea', '#764ba2', '#f093fb']
        }}]
    }},
    options: {{
        responsive: true,
        plugins: {{ title: {{ display: true, text: 'Findings by Scanner' }} }}
    }}
}});
"""

    def _get_css_content(self) -> str:
        """Get default CSS styles."""
        return """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 40px; text-align: center; }
        .content { padding: 40px; }
        .summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px; }
        .stat-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }
        .stat-card .value { font-size: 2em; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        .severity-badge { padding: 4px 12px; border-radius: 12px; font-weight: 600; text-transform: uppercase; font-size: 0.85em; }
        .severity-critical { background: #dc3545; color: white; }
        .severity-high { background: #fd7e14; color: white; }
        .severity-medium { background: #ffc107; color: #333; }
        .severity-low { background: #28a745; color: white; }
        .finding-details { display: none; padding: 20px; background: #f8f9fa; }
        .code-snippet { background: #f1f1f1; padding: 10px; overflow-x: auto; font-family: monospace; }
        .chart-container { margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
        """

    def _generate_builtin_html(self, context: Dict[str, Any]) -> str:
        """Generate HTML using string concatenation (fallback)."""
        html = [
            f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{context['title']}</title>
    <style>{context['css_content']}</style>
    {'''<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>''' if context['include_charts'] else ''}
</head>
<body>
    <div class="container">
        <header>
            <h1>🔒 {context['title']}</h1>
            <p>{context['subtitle']}</p>
        </header>
        <div class="content">
            <div class="summary">
                <div class="stat-card"><h3>Total Findings</h3><div class="value">{context['summary']['total_findings']}</div></div>
                <div class="stat-card"><h3>Critical</h3><div class="value">{context['summary']['critical_count']}</div></div>
                <div class="stat-card"><h3>High</h3><div class="value">{context['summary']['high_count']}</div></div>
            </div>
            """
        ]

        if context['include_charts']:
            html.append(f"""
            <div class="section">
                <h2>📈 Visual Analytics</h2>
                <div style="display: flex; gap: 20px;">
                    <div class="chart-container" style="flex: 1;"><canvas id="severityChart"></canvas></div>
                    <div class="chart-container" style="flex: 1;"><canvas id="scannerChart"></canvas></div>
                </div>
            </div>
            <script>{context['chart_script']}</script>
            """)

        html.append("""
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
                        </tr>
                    </thead>
                    <tbody>
        """)

        for idx, finding in enumerate(context['findings']):
            sev_lower = finding['severity'].lower()
            html.append(f"""
                        <tr onclick="document.getElementById('details-{idx}').style.display = document.getElementById('details-{idx}').style.display === 'block' ? 'none' : 'block'" style="cursor: pointer;">
                            <td><span class="severity-badge severity-{sev_lower}">{finding['severity']}</span></td>
                            <td>{finding['title']}</td>
                            <td>{finding['file_name']}</td>
                            <td>{finding['line_start']}</td>
                            <td>{finding['scanner']}</td>
                        </tr>
                        <tr>
                            <td colspan="5" style="padding: 0;">
                                <div id="details-{idx}" class="finding-details">
                                    <p><strong>Description:</strong> {finding['description']}</p>
                                    <p><strong>Location:</strong> {finding['file_path']}:{finding['line_start']}</p>
            """)
            
            if self.include_code_snippets and 'code_snippet' in finding:
                html.append(f"""
                                    <div class="code-snippet"><pre>{finding['code_snippet']}</pre></div>
                """)
            
            html.append("</div></td></tr>")

        html.append("""
                    </tbody>
                </table>
            </div>
        </div>
        <footer>
            <p>Generated by Security Assistant on """ + context['generated_at'] + """</p>
        </footer>
    </div>
</body>
</html>
        """)
        
        return "\n".join(html)
