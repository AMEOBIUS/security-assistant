"""
Reporter Factory

Factory for creating report generators.

Version: 1.0.0 (Session 47 Refactoring)
"""

import logging
from typing import Dict, Type


logger = logging.getLogger(__name__)


class ReporterFactory:
    """
    Factory for creating report generators.
    
    Supports:
    - Built-in reporters (JSON, Markdown, etc.)
    - Custom reporter registration
    
    Example:
        >>> reporter = ReporterFactory.create("json")
        >>> content = reporter.generate(result)
        
        >>> # Register custom reporter
        >>> ReporterFactory.register("custom", MyCustomReporter)
        >>> reporter = ReporterFactory.create("custom")
    """
    
    _reporters: Dict[str, Type[BaseReporter]] = {}
    
    @classmethod
    def _ensure_registered(cls) -> None:
        """Ensure built-in reporters are registered."""
        if not cls._reporters:
            from .json_reporter import JSONReporter
            from .markdown_reporter import MarkdownReporter
            from .html_reporter import HTMLReporter
            from .sarif_reporter import SarifReporter
            from .text_reporter import TextReporter
            from .yaml_reporter import YAMLReporter
            
            cls._reporters = {
                "json": JSONReporter,
                "markdown": MarkdownReporter,
                "md": MarkdownReporter,
                "html": HTMLReporter,
                "sarif": SarifReporter,
                "text": TextReporter,
                "txt": TextReporter,
                "yaml": YAMLReporter,
                "yml": YAMLReporter,
            }
    
    @classmethod
    def create(cls, format: str, **kwargs) -> BaseReporter:
        """
        Create a reporter instance.
        
        Args:
            format: Report format (json, markdown, html, etc.)
            **kwargs: Reporter-specific options
        
        Returns:
            Reporter instance
        
        Raises:
            ValueError: If format is not supported
        """
        cls._ensure_registered()
        
        format_lower = format.lower()
        
        if format_lower not in cls._reporters:
            available = ", ".join(cls._reporters.keys())
            raise ValueError(
                f"Unknown report format: {format}. "
                f"Available formats: {available}"
            )
        
        reporter_class = cls._reporters[format_lower]
        return reporter_class(**kwargs)
    
    @classmethod
    def register(cls, format: str, reporter_class: Type[BaseReporter]) -> None:
        """
        Register a custom reporter.
        
        Args:
            format: Format identifier
            reporter_class: Reporter class (must extend BaseReporter)
        
        Example:
            >>> class MyReporter(BaseReporter):
            ...     pass
            >>> ReporterFactory.register("my-format", MyReporter)
        """
        cls._ensure_registered()
        
        if not issubclass(reporter_class, BaseReporter):
            raise TypeError(
                f"Reporter class must extend BaseReporter, got {reporter_class}"
            )
        
        cls._reporters[format.lower()] = reporter_class
        logger.info(f"Registered reporter: {format}")
    
    @classmethod
    def available_formats(cls) -> list:
        """Get list of available formats."""
        cls._ensure_registered()
        return list(cls._reporters.keys())
    
    @classmethod
    def is_supported(cls, format: str) -> bool:
        """Check if format is supported."""
        cls._ensure_registered()
        return format.lower() in cls._reporters
