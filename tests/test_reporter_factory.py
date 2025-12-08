"""
Tests for ReporterFactory

Tests the reporter factory pattern and registration system.
"""

import pytest
from security_assistant.reporting.reporter_factory import ReporterFactory
from security_assistant.reporting.base_reporter import BaseReporter, ReportFormat
from security_assistant.reporting.json_reporter import JSONReporter
from security_assistant.reporting.markdown_reporter import MarkdownReporter
from security_assistant.reporting.html_reporter import HTMLReporter
from security_assistant.reporting.sarif_reporter import SarifReporter
from security_assistant.reporting.text_reporter import TextReporter
from security_assistant.reporting.yaml_reporter import YAMLReporter


class TestReporterFactory:
    """Test suite for ReporterFactory."""
    
    def test_available_formats(self):
        """Test that all expected formats are available."""
        formats = ReporterFactory.available_formats()
        
        assert "json" in formats
        assert "markdown" in formats
        assert "md" in formats
        assert "html" in formats
        assert "sarif" in formats
        assert "text" in formats
        assert "txt" in formats
        assert "yaml" in formats
        assert "yml" in formats
    
    def test_create_json_reporter(self):
        """Test creating JSON reporter."""
        reporter = ReporterFactory.create("json")
        assert isinstance(reporter, JSONReporter)
        assert reporter.format == "json"
    
    def test_create_markdown_reporter(self):
        """Test creating Markdown reporter."""
        reporter = ReporterFactory.create("markdown")
        assert isinstance(reporter, MarkdownReporter)
        assert reporter.format == "markdown"
    
    def test_create_markdown_reporter_alias(self):
        """Test creating Markdown reporter with 'md' alias."""
        reporter = ReporterFactory.create("md")
        assert isinstance(reporter, MarkdownReporter)
    
    def test_create_html_reporter(self):
        """Test creating HTML reporter."""
        reporter = ReporterFactory.create("html")
        assert isinstance(reporter, HTMLReporter)
        assert reporter.format == "html"
    
    def test_create_sarif_reporter(self):
        """Test creating SARIF reporter."""
        reporter = ReporterFactory.create("sarif")
        assert isinstance(reporter, SarifReporter)
        assert reporter.format == "sarif"
    
    def test_create_text_reporter(self):
        """Test creating Text reporter."""
        reporter = ReporterFactory.create("text")
        assert isinstance(reporter, TextReporter)
        assert reporter.format == "text"
    
    def test_create_text_reporter_alias(self):
        """Test creating Text reporter with 'txt' alias."""
        reporter = ReporterFactory.create("txt")
        assert isinstance(reporter, TextReporter)
    
    def test_create_yaml_reporter(self):
        """Test creating YAML reporter."""
        reporter = ReporterFactory.create("yaml")
        assert isinstance(reporter, YAMLReporter)
        assert reporter.format == "yaml"
    
    def test_create_yaml_reporter_alias(self):
        """Test creating YAML reporter with 'yml' alias."""
        reporter = ReporterFactory.create("yml")
        assert isinstance(reporter, YAMLReporter)
    
    def test_create_with_options(self):
        """Test creating reporter with custom options."""
        reporter = ReporterFactory.create(
            "json",
            include_code_snippets=False,
            max_findings=10
        )
        assert reporter.include_code_snippets is False
        assert reporter.max_findings == 10
    
    def test_create_html_with_charts(self):
        """Test creating HTML reporter with charts option."""
        reporter = ReporterFactory.create(
            "html",
            include_charts=True
        )
        assert reporter.include_charts is True
    
    def test_create_invalid_format(self):
        """Test creating reporter with invalid format raises error."""
        with pytest.raises(ValueError, match="Unknown report format"):
            ReporterFactory.create("invalid_format")
    
    def test_is_supported(self):
        """Test checking if format is supported."""
        assert ReporterFactory.is_supported("json") is True
        assert ReporterFactory.is_supported("html") is True
        assert ReporterFactory.is_supported("invalid") is False
    
    def test_is_supported_case_insensitive(self):
        """Test format support check is case insensitive."""
        assert ReporterFactory.is_supported("JSON") is True
        assert ReporterFactory.is_supported("Html") is True
        assert ReporterFactory.is_supported("YAML") is True
    
    def test_register_custom_reporter(self):
        """Test registering a custom reporter."""
        class CustomReporter(BaseReporter):
            @property
            def format(self):
                return "custom"
            
            def generate(self, result, **kwargs):
                return "custom report"
        
        ReporterFactory.register("custom", CustomReporter)
        
        assert ReporterFactory.is_supported("custom")
        reporter = ReporterFactory.create("custom")
        assert isinstance(reporter, CustomReporter)
    
    def test_register_invalid_reporter(self):
        """Test registering invalid reporter raises error."""
        class NotAReporter:
            pass
        
        with pytest.raises(TypeError, match="must extend BaseReporter"):
            ReporterFactory.register("invalid", NotAReporter)
    
    def test_create_case_insensitive(self):
        """Test creating reporter is case insensitive."""
        reporter1 = ReporterFactory.create("JSON")
        reporter2 = ReporterFactory.create("json")
        
        assert type(reporter1) == type(reporter2)
