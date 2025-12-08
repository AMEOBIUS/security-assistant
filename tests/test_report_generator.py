"""
Tests for Report Generator Module

Tests cover:
- HTML report generation
- Markdown report generation
- JSON report generation
- YAML report generation
- SARIF report generation
- Text report generation
- PDF report generation (if weasyprint available)
"""

import pytest
import json
import yaml
from pathlib import Path
from datetime import datetime

from security_assistant.orchestrator import (
    OrchestrationResult,
    UnifiedFinding,
    FindingSeverity,
    ScannerType
)
from security_assistant.report_generator import (
    ReportGenerator,
    ReportFormat
)


@pytest.fixture
def sample_finding():
    """Create a sample finding for testing."""
    return UnifiedFinding(
        finding_id="test-001",
        scanner=ScannerType.BANDIT,
        severity=FindingSeverity.HIGH,
        category="security",
        file_path="test/example.py",
        line_start=10,
        line_end=15,
        title="SQL Injection Vulnerability",
        description="Potential SQL injection detected",
        code_snippet="query = 'SELECT * FROM users WHERE id = ' + user_id",
        cwe_ids=["CWE-89"],
        owasp_categories=["A03:2021"],
        references=["https://owasp.org/www-community/attacks/SQL_Injection"],
        fix_available=True,
        fix_version="2.0.0",
        fix_guidance="Use parameterized queries",
        priority_score=85.5,
        confidence="HIGH"
    )


@pytest.fixture
def sample_result(sample_finding):
    """Create a sample orchestration result for testing."""
    result = OrchestrationResult(
        all_findings=[sample_finding],
        deduplicated_findings=[sample_finding],
        scanner_results={ScannerType.BANDIT: None},
        scan_time=datetime(2025, 11, 29, 12, 0, 0),
        execution_time_seconds=5.5,
        target="test/example.py",
        total_findings=1,
        findings_by_scanner={ScannerType.BANDIT: 1},
        findings_by_severity={FindingSeverity.HIGH: 1},
        duplicates_removed=0
    )
    return result


@pytest.fixture
def report_generator():
    """Create a report generator instance."""
    return ReportGenerator(
        include_charts=True,
        include_code_snippets=True
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "reports"
    output_dir.mkdir()
    return output_dir


class TestReportGenerator:
    """Test ReportGenerator class."""
    
    def test_init(self):
        """Test report generator initialization."""
        generator = ReportGenerator()
        assert generator.include_charts is True
        assert generator.include_code_snippets is True
        # template_dir is now always set to default templates directory
        assert generator.template_dir is not None
        assert generator.template_dir.name == "templates"
    
    def test_init_custom(self):
        """Test report generator with custom settings."""
        generator = ReportGenerator(
            template_dir="custom/templates",
            include_charts=False,
            include_code_snippets=False
        )
        assert generator.include_charts is False
        assert generator.include_code_snippets is False
        assert generator.template_dir == Path("custom/templates")


class TestHTMLReportGeneration:
    """Test HTML report generation."""
    
    def test_generate_html_report(self, report_generator, sample_result, temp_output_dir):
        """Test basic HTML report generation."""
        output_path = temp_output_dir / "test_report.html"
        
        result_path = report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.HTML,
            title="Test Security Report"
        )
        
        assert Path(result_path).exists()
        assert Path(result_path) == output_path
        
        # Verify HTML content
        content = output_path.read_text(encoding='utf-8')
        assert "<!DOCTYPE html>" in content
        assert "Test Security Report" in content
        assert "SQL Injection Vulnerability" in content
        assert "test/example.py" in content
    
    def test_html_report_structure(self, report_generator, sample_result, temp_output_dir):
        """Test HTML report structure."""
        output_path = temp_output_dir / "structure_test.html"
        
        report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.HTML
        )
        
        content = output_path.read_text(encoding='utf-8')
        
        # Check for key sections
        assert "Executive Summary" in content
        assert "Severity Breakdown" in content
        assert "Scanner Breakdown" in content
        assert "Detailed Findings" in content
        
        # Check for statistics
        assert "Total Findings" in content
        assert "Unique Issues" in content
        assert "Critical" in content
        assert "High" in content
    
    def test_html_report_with_charts(self, report_generator, sample_result, temp_output_dir):
        """Test HTML report includes charts."""
        output_path = temp_output_dir / "charts_test.html"
        
        report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.HTML
        )
        
        content = output_path.read_text(encoding='utf-8')
        
        # Check for Chart.js
        assert "chart.js" in content.lower()
        assert "severityChart" in content
        assert "scannerChart" in content
    
    def test_html_report_without_charts(self, sample_result, temp_output_dir):
        """Test HTML report without charts."""
        generator = ReportGenerator(include_charts=False)
        output_path = temp_output_dir / "no_charts_test.html"
        
        generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.HTML
        )
        
        content = output_path.read_text(encoding='utf-8')
        
        # Charts should not be present
        assert "chart.js" not in content.lower()
    
    def test_html_report_code_snippets(self, report_generator, sample_result, temp_output_dir):
        """Test HTML report includes code snippets."""
        output_path = temp_output_dir / "snippets_test.html"
        
        report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.HTML
        )
        
        content = output_path.read_text(encoding='utf-8')
        
        # Check for code snippet
        assert "SELECT * FROM users" in content
        assert "code-snippet" in content


class TestMarkdownReportGeneration:
    """Test Markdown report generation."""
    
    def test_generate_markdown_report(self, report_generator, sample_result, temp_output_dir):
        """Test basic Markdown report generation."""
        output_path = temp_output_dir / "test_report.md"
        
        result_path = report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.MARKDOWN,
            title="Test Security Report"
        )
        
        assert Path(result_path).exists()
        
        # Verify Markdown content
        content = output_path.read_text(encoding='utf-8')
        assert "# Test Security Report" in content
        assert "## 📊 Executive Summary" in content
        assert "SQL Injection Vulnerability" in content
    
    def test_markdown_report_structure(self, report_generator, sample_result, temp_output_dir):
        """Test Markdown report structure."""
        output_path = temp_output_dir / "structure_test.md"
        
        report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.MARKDOWN
        )
        
        content = output_path.read_text(encoding='utf-8')
        
        # Check for sections
        assert "## 📊 Executive Summary" in content
        assert "## 🎯 Severity Breakdown" in content
        assert "## 🔍 Scanner Breakdown" in content
        assert "## 🔎 Top Priority Findings" in content
        
        # Check for tables
        assert "| Severity | Count | Percentage |" in content
        assert "| Scanner | Findings | Percentage |" in content


class TestJSONReportGeneration:
    """Test JSON report generation."""
    
    def test_generate_json_report(self, report_generator, sample_result, temp_output_dir):
        """Test basic JSON report generation."""
        output_path = temp_output_dir / "test_report.json"
        
        result_path = report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.JSON
        )
        
        assert Path(result_path).exists()
        
        # Verify JSON is valid
        content = output_path.read_text(encoding='utf-8')
        data = json.loads(content)
        
        assert "metadata" in data
        assert "summary" in data
        assert "findings" in data
    
    def test_json_report_structure(self, report_generator, sample_result, temp_output_dir):
        """Test JSON report structure."""
        output_path = temp_output_dir / "structure_test.json"
        
        report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.JSON
        )
        
        data = json.loads(output_path.read_text(encoding='utf-8'))
        
        # Check metadata
        assert data["metadata"]["target"] == "test/example.py"
        assert data["metadata"]["execution_time_seconds"] == 5.5
        
        # Check summary
        assert data["summary"]["total_findings"] == 1
        assert data["summary"]["unique_findings"] == 1
        assert data["summary"]["high_count"] == 1
        
        # Check findings
        assert len(data["findings"]) == 1
        finding = data["findings"][0]
        assert finding["title"] == "SQL Injection Vulnerability"
        assert finding["severity"] == "HIGH"
        assert finding["scanner"] == "bandit"


class TestYAMLReportGeneration:
    """Test YAML report generation."""
    
    def test_generate_yaml_report(self, report_generator, sample_result, temp_output_dir):
        """Test basic YAML report generation."""
        output_path = temp_output_dir / "test_report.yaml"
        
        result_path = report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.YAML
        )
        
        assert Path(result_path).exists()
        
        # Verify YAML is valid
        content = output_path.read_text(encoding='utf-8')
        data = yaml.safe_load(content)
        
        assert "metadata" in data
        assert "summary" in data
        assert "findings" in data
    
    def test_yaml_report_structure(self, report_generator, sample_result, temp_output_dir):
        """Test YAML report structure."""
        output_path = temp_output_dir / "structure_test.yaml"
        
        report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.YAML
        )
        
        data = yaml.safe_load(output_path.read_text(encoding='utf-8'))
        
        # Check structure
        assert data["metadata"]["target"] == "test/example.py"
        assert data["summary"]["total_findings"] == 1
        assert len(data["findings"]) == 1


class TestSARIFReportGeneration:
    """Test SARIF report generation."""
    
    def test_generate_sarif_report(self, report_generator, sample_result, temp_output_dir):
        """Test basic SARIF report generation."""
        output_path = temp_output_dir / "test_report.sarif"
        
        result_path = report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.SARIF
        )
        
        assert Path(result_path).exists()
        
        # Verify SARIF is valid JSON
        content = output_path.read_text(encoding='utf-8')
        data = json.loads(content)
        
        assert data["version"] == "2.1.0"
        assert "$schema" in data
        assert "runs" in data
    
    def test_sarif_report_structure(self, report_generator, sample_result, temp_output_dir):
        """Test SARIF report structure."""
        output_path = temp_output_dir / "structure_test.sarif"
        
        report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.SARIF
        )
        
        data = json.loads(output_path.read_text(encoding='utf-8'))
        
        # Check SARIF structure
        assert len(data["runs"]) == 1
        run = data["runs"][0]
        
        # Check tool info
        assert run["tool"]["driver"]["name"] == "Security Assistant"
        assert run["tool"]["driver"]["version"] == "1.0.0"
        
        # Check rules
        assert len(run["tool"]["driver"]["rules"]) > 0
        
        # Check results
        assert len(run["results"]) == 1
        result = run["results"][0]
        assert result["level"] == "error"  # HIGH severity
        assert "locations" in result
    
    def test_sarif_severity_mapping(self, report_generator, temp_output_dir):
        """Test SARIF severity level mapping."""
        # Create findings with different severities
        findings = [
            UnifiedFinding(
                finding_id=f"test-{i}",
                scanner=ScannerType.BANDIT,
                severity=severity,
                category="security",
                file_path="test.py",
                line_start=i,
                line_end=i,
                title=f"Test {severity.value}",
                description="Test finding",
                code_snippet="",
                priority_score=50.0
            )
            for i, severity in enumerate([
                FindingSeverity.CRITICAL,
                FindingSeverity.HIGH,
                FindingSeverity.MEDIUM,
                FindingSeverity.LOW,
                FindingSeverity.INFO
            ])
        ]
        
        result = OrchestrationResult(
            all_findings=findings,
            deduplicated_findings=findings,
            scanner_results={},
            scan_time=datetime.now(),
            execution_time_seconds=1.0,
            target="test.py",
            total_findings=len(findings),
            findings_by_scanner={ScannerType.BANDIT: len(findings)},
            findings_by_severity={
                FindingSeverity.CRITICAL: 1,
                FindingSeverity.HIGH: 1,
                FindingSeverity.MEDIUM: 1,
                FindingSeverity.LOW: 1,
                FindingSeverity.INFO: 1,
            }
        )
        
        output_path = temp_output_dir / "severity_test.sarif"
        report_generator.generate_report(result, str(output_path), format=ReportFormat.SARIF)
        
        data = json.loads(output_path.read_text(encoding='utf-8'))
        results = data["runs"][0]["results"]
        
        # Check severity mapping
        assert results[0]["level"] == "error"  # CRITICAL
        assert results[1]["level"] == "error"  # HIGH
        assert results[2]["level"] == "warning"  # MEDIUM
        assert results[3]["level"] == "note"  # LOW
        assert results[4]["level"] == "note"  # INFO


class TestTextReportGeneration:
    """Test text report generation."""
    
    def test_generate_text_report(self, report_generator, sample_result, temp_output_dir):
        """Test basic text report generation."""
        output_path = temp_output_dir / "test_report.txt"
        
        result_path = report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.TEXT,
            title="Test Security Report"
        )
        
        assert Path(result_path).exists()
        
        # Verify text content
        content = output_path.read_text(encoding='utf-8')
        assert "Test Security Report" in content
        assert "EXECUTIVE SUMMARY" in content
        assert "SQL Injection Vulnerability" in content
    
    def test_text_report_structure(self, report_generator, sample_result, temp_output_dir):
        """Test text report structure."""
        output_path = temp_output_dir / "structure_test.txt"
        
        report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.TEXT
        )
        
        content = output_path.read_text(encoding='utf-8')
        
        # Check for sections
        assert "EXECUTIVE SUMMARY" in content
        assert "TOP PRIORITY FINDINGS" in content
        assert "Total Findings:" in content
        assert "Unique Issues:" in content


class TestPDFReportGeneration:
    """Test PDF report generation."""
    
    def test_generate_pdf_report_fallback(self, report_generator, sample_result, temp_output_dir):
        """Test PDF report generation falls back to HTML if weasyprint not available."""
        import sys
        if sys.platform == 'win32':
            pytest.skip("WeasyPrint requires GTK on Windows")
        
        output_path = temp_output_dir / "test_report.pdf"
        
        # This should work even without weasyprint (falls back to HTML bytes)
        result_path = report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.PDF,
            title="Test Security Report"
        )
        
        assert Path(result_path).exists()


class TestReportGeneratorEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_result(self, report_generator, temp_output_dir):
        """Test report generation with empty result."""
        empty_result = OrchestrationResult(
            all_findings=[],
            deduplicated_findings=[],
            scanner_results={},
            scan_time=datetime.now(),
            execution_time_seconds=0.1,
            target="empty.py",
            total_findings=0,
            findings_by_scanner={},
            findings_by_severity={},
            duplicates_removed=0
        )
        
        output_path = temp_output_dir / "empty_report.html"
        
        result_path = report_generator.generate_report(
            empty_result,
            str(output_path),
            format=ReportFormat.HTML
        )
        
        assert Path(result_path).exists()
        content = output_path.read_text(encoding='utf-8')
        assert "0" in content  # Should show zero findings
    
    def test_invalid_format(self, report_generator, sample_result, temp_output_dir):
        """Test report generation with invalid format."""
        output_path = temp_output_dir / "invalid.report"
        
        with pytest.raises(ValueError, match="Unsupported report format"):
            report_generator.generate_report(
                sample_result,
                str(output_path),
                format="invalid_format"
            )
    
    def test_output_directory_creation(self, report_generator, sample_result, tmp_path):
        """Test automatic output directory creation."""
        output_path = tmp_path / "nested" / "dir" / "report.html"
        
        result_path = report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.HTML
        )
        
        assert Path(result_path).exists()
        assert output_path.parent.exists()
    
    def test_multiple_findings(self, report_generator, temp_output_dir):
        """Test report with multiple findings."""
        findings = [
            UnifiedFinding(
                finding_id=f"test-{i}",
                scanner=ScannerType.BANDIT,
                severity=FindingSeverity.HIGH,
                category="security",
                file_path=f"test{i}.py",
                line_start=i * 10,
                line_end=i * 10 + 5,
                title=f"Vulnerability {i}",
                description=f"Description {i}",
                code_snippet=f"code {i}",
                priority_score=90.0 - i
            )
            for i in range(10)
        ]
        
        result = OrchestrationResult(
            all_findings=findings,
            deduplicated_findings=findings,
            scanner_results={ScannerType.BANDIT: None},
            scan_time=datetime.now(),
            execution_time_seconds=5.0,
            target="test/",
            total_findings=10,
            findings_by_scanner={ScannerType.BANDIT: 10},
            findings_by_severity={FindingSeverity.HIGH: 10}
        )
        
        output_path = temp_output_dir / "multiple_findings.html"
        report_generator.generate_report(result, str(output_path), format=ReportFormat.HTML)
        
        content = output_path.read_text(encoding='utf-8')
        
        # Check all findings are present
        for i in range(10):
            assert f"Vulnerability {i}" in content


    def test_percentage_calculation_with_duplicates(self, report_generator, temp_output_dir):
        """Test percentage calculation with duplicate findings."""
        finding1 = UnifiedFinding(
            finding_id="test-001",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.HIGH,
            category="security",
            file_path="test/example.py",
            line_start=10,
            line_end=15,
            title="SQL Injection Vulnerability",
            description="Potential SQL injection detected",
            code_snippet="query = 'SELECT * FROM users WHERE id = ' + user_id",
            priority_score=85.5
        )
        finding2 = UnifiedFinding(
            finding_id="test-002",
            scanner=ScannerType.SEMGREP,
            severity=FindingSeverity.MEDIUM,
            category="security",
            file_path="test/example.py",
            line_start=20,
            line_end=25,
            title="Cross-Site Scripting",
            description="Potential XSS detected",
            code_snippet="<p>{user_input}</p>",
            priority_score=65.5
        )

        result_with_duplicates = OrchestrationResult(
            all_findings=[finding1, finding1, finding2],
            deduplicated_findings=[finding1, finding2],
            scanner_results={ScannerType.BANDIT: None, ScannerType.SEMGREP: None},
            scan_time=datetime(2025, 11, 29, 12, 0, 0),
            execution_time_seconds=5.5,
            target="test/example.py",
            total_findings=3,
            findings_by_scanner={ScannerType.BANDIT: 2, ScannerType.SEMGREP: 1},
            findings_by_severity={FindingSeverity.HIGH: 2, FindingSeverity.MEDIUM: 1},
            duplicates_removed=1
        )

        output_path = temp_output_dir / "percentage_test.html"
        report_generator.generate_report(result_with_duplicates, str(output_path), format=ReportFormat.HTML)

        content = output_path.read_text(encoding='utf-8')

        # High severity should be 66.7% of total findings (2 out of 3)
        assert "<td>66.7%</td>" in content
