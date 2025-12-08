"""
Tests for ReportGenerator - Public API Only

Tests only the public interface of ReportGenerator.
Internal methods are tested via reporter-specific tests.
"""

import pytest
from pathlib import Path

from security_assistant.report_generator import ReportGenerator
from security_assistant.reporting.base_reporter import ReportFormat
from tests.conftest_reporters import create_test_result, create_test_finding


class TestReportGenerator:
    """Test ReportGenerator public API."""
    
    def test_init_default(self):
        """Test default initialization."""
        gen = ReportGenerator()
        assert gen.include_charts is True
        assert gen.include_code_snippets is True
        assert gen.enable_remediation is True
    
    def test_init_custom(self):
        """Test custom initialization."""
        gen = ReportGenerator(
            template_dir="custom/templates",
            include_charts=False,
            include_code_snippets=False,
            enable_remediation=False
        )
        assert gen.template_dir == "custom/templates"
        assert gen.include_charts is False
        assert gen.include_code_snippets is False
        assert gen.enable_remediation is False
    
    def test_generate_html_report(self, tmp_path):
        """Test generating HTML report."""
        gen = ReportGenerator()
        finding = create_test_finding()
        result = create_test_result(findings=[finding])
        
        output_file = tmp_path / "report.html"
        path = gen.generate_report(result, str(output_file), format="html")
        
        assert Path(path).exists()
        content = Path(path).read_text()
        assert "<!DOCTYPE html>" in content
    
    def test_generate_json_report(self, tmp_path):
        """Test generating JSON report."""
        gen = ReportGenerator()
        finding = create_test_finding()
        result = create_test_result(findings=[finding])
        
        output_file = tmp_path / "report.json"
        path = gen.generate_report(result, str(output_file), format="json")
        
        assert Path(path).exists()
        content = Path(path).read_text()
        assert "metadata" in content
    
    def test_generate_markdown_report(self, tmp_path):
        """Test generating Markdown report."""
        gen = ReportGenerator()
        finding = create_test_finding()
        result = create_test_result(findings=[finding])
        
        output_file = tmp_path / "report.md"
        path = gen.generate_report(result, str(output_file), format="markdown")
        
        assert Path(path).exists()
        content = Path(path).read_text()
        assert "#" in content
    
    def test_generate_sarif_report(self, tmp_path):
        """Test generating SARIF report."""
        gen = ReportGenerator()
        finding = create_test_finding()
        result = create_test_result(findings=[finding])
        
        output_file = tmp_path / "report.sarif"
        path = gen.generate_report(result, str(output_file), format="sarif")
        
        assert Path(path).exists()
        content = Path(path).read_text()
        assert "sarif-schema" in content
    
    def test_generate_text_report(self, tmp_path):
        """Test generating text report."""
        gen = ReportGenerator()
        finding = create_test_finding()
        result = create_test_result(findings=[finding])
        
        output_file = tmp_path / "report.txt"
        path = gen.generate_report(result, str(output_file), format="text")
        
        assert Path(path).exists()
        content = Path(path).read_text()
        assert "Security Scan Report" in content
    
    def test_generate_yaml_report(self, tmp_path):
        """Test generating YAML report."""
        gen = ReportGenerator()
        finding = create_test_finding()
        result = create_test_result(findings=[finding])
        
        output_file = tmp_path / "report.yaml"
        path = gen.generate_report(result, str(output_file), format="yaml")
        
        assert Path(path).exists()
        content = Path(path).read_text()
        assert "metadata:" in content
    
    def test_generate_with_title(self, tmp_path):
        """Test generating report with custom title."""
        gen = ReportGenerator()
        finding = create_test_finding()
        result = create_test_result(findings=[finding])
        
        output_file = tmp_path / "report.html"
        path = gen.generate_report(
            result,
            str(output_file),
            format="html",
            title="Custom Title"
        )
        
        content = Path(path).read_text()
        assert "Custom Title" in content
    
    def test_generate_invalid_format(self, tmp_path):
        """Test generating report with invalid format."""
        gen = ReportGenerator()
        finding = create_test_finding()
        result = create_test_result(findings=[finding])
        
        output_file = tmp_path / "report.txt"
        
        with pytest.raises(ValueError, match="Unknown report format"):
            gen.generate_report(result, str(output_file), format="invalid")
    
    def test_generate_comparison_report(self, tmp_path):
        """Test generating comparison report."""
        from security_assistant.report_comparator import ReportComparator, ComparisonResult
        from datetime import datetime
        
        gen = ReportGenerator()
        finding = create_test_finding()
        baseline = create_test_result(findings=[finding])
        latest = create_test_result(findings=[])
        
        comparator = ReportComparator()
        comparison = comparator.compare(baseline, latest)
        
        output_file = tmp_path / "comparison.txt"
        path = gen.generate_comparison_report(comparison, str(output_file))
        
        assert Path(path).exists()
        content = Path(path).read_text()
        assert "Comparison" in content or "Fixed" in content
    
    def test_generate_bulk_report(self, tmp_path):
        """Test generating bulk reports."""
        from security_assistant.orchestrator import BulkScanResult
        
        gen = ReportGenerator()
        finding = create_test_finding()
        result1 = create_test_result(target="app1", findings=[finding])
        result2 = create_test_result(target="app2", findings=[])
        
        bulk_result = BulkScanResult(
            results={"app1": result1, "app2": result2},
            total_execution_time=10.0
        )
        
        output_dir = tmp_path / "bulk"
        paths = gen.generate_bulk_report(bulk_result, str(output_dir), formats=["json", "html", "csv"])
        
        assert "json" in paths
        assert "html" in paths
        assert "csv" in paths
        assert Path(paths["json"]).exists()
