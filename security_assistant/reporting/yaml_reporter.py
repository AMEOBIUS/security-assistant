"""
YAML Reporter Implementation

Generates YAML reports for configuration and data interchange.

Version: 1.0.0
"""

import logging
from typing import Any

import yaml

from .base_reporter import BaseReporter, ReportFormat

logger = logging.getLogger(__name__)


class YAMLReporter(BaseReporter):
    """
    Generates YAML reports.
    Suitable for configuration files and human-readable data.
    """

    @property
    def format(self) -> ReportFormat:
        return ReportFormat.YAML

    def generate(self, result: Any, **kwargs) -> str:
        """
        Generate YAML report.

        Args:
            result: OrchestrationResult
            **kwargs: Additional options

        Returns:
            YAML content as string
        """
        context = self._prepare_context(result, kwargs.get("title"))

        report_data = {
            "metadata": {
                "generated_at": context["generated_at"],
                "target": context["target"],
                "execution_time_seconds": context["execution_time"],
            },
            "summary": context["summary"],
            "severity_breakdown": {
                item["name"]: {"count": item["count"], "percentage": item["percentage"]}
                for item in context["severity_breakdown"]
            },
            "scanner_breakdown": {
                item["name"]: {"count": item["count"], "percentage": item["percentage"]}
                for item in context["scanner_breakdown"]
            },
            "findings": context["findings"],
        }

        return yaml.dump(
            report_data, default_flow_style=False, sort_keys=False, allow_unicode=True
        )
