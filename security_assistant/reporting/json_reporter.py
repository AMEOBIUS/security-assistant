"""
JSON Reporter

Generates JSON reports for programmatic access.

Version: 1.0.0 (Session 47 Refactoring)
"""

import json
import logging
from typing import Any

from .base_reporter import BaseReporter, ReportFormat

logger = logging.getLogger(__name__)


class JSONReporter(BaseReporter):
    """
    Generate JSON reports.
    
    Example:
        >>> reporter = JSONReporter()
        >>> json_content = reporter.generate(result)
        >>> data = json.loads(json_content)
    """
    
    def __init__(self, indent: int = 2, **kwargs):
        """
        Initialize JSON reporter.
        
        Args:
            indent: JSON indentation (default: 2)
            **kwargs: Base reporter options
        """
        super().__init__(**kwargs)
        self.indent = indent
    
    @property
    def format(self) -> ReportFormat:
        return ReportFormat.JSON
    
    def generate(self, result: Any, **kwargs) -> str:
        """Generate JSON report."""
        context = self._prepare_context(result, kwargs.get('title'))
        
        # Add metadata
        report_data = {
            "metadata": {
                "format": "json",
                "version": "1.0",
                "generated_at": context["generated_at"],
                "target": context["target"],
                "execution_time_seconds": context["execution_time"],
            },
            "summary": context["summary"],
            "overall_risk": context["overall_risk"],
            "severity_breakdown": context["severity_breakdown"],
            "scanner_breakdown": context["scanner_breakdown"],
            "findings": context["findings"],
        }
        
        return json.dumps(report_data, indent=self.indent, default=str)
