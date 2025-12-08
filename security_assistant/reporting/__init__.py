"""
Reporting package for Security Assistant.

Provides modular report generation in multiple formats:
- HTML (interactive with charts)
- JSON (programmatic access)
- SARIF (tool integration)
- Markdown (documentation)
- Text (plain text)
- YAML (configuration)

Version: 1.0.0 (Session 47 Refactoring)
"""

from .base_reporter import BaseReporter, ReportFormat
from .json_reporter import JSONReporter
from .markdown_reporter import MarkdownReporter
from .reporter_factory import ReporterFactory

__all__ = [
    "BaseReporter",
    "ReportFormat",
    "ReporterFactory",
    "JSONReporter",
    "MarkdownReporter",
]
