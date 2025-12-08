"""
Tests for Custom Template Support in Report Generator

Tests:
- Template loading
- Template rendering
- Custom variables
- Fallback to built-in generation
- Multiple template formats
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from security_assistant.orchestrator import (
    OrchestrationResult,
    UnifiedFinding,
    FindingSeverity,
    ScannerType
)
from security_assistant.report_generator import ReportGenerator, ReportFormat


class TestCustomTemplates(unittest.TestCase):
    """Test custom template functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test templates
        self.temp_dir = tempfile.mkdtemp()
        self.template_dir = Path(self.temp_dir) / "templates"
        self.template_dir.mkdir()
        
        # Create test result
        self.result = OrchestrationResult(
            target="test_project",
            scan_time=datetime.now(),
            execution_time_seconds=1.5,
            total_findings=2,
            deduplicated_findings=[
                UnifiedFinding(
                    finding_id="test-1",
                    scanner=ScannerType.BANDIT,
                    severity=FindingSeverity.HIGH,
                    category="Security",
                    file_path="test.py",
                    line_start=10,
                    line_end=12,
                    title="SQL Injection",
                    description="Possible SQL injection",
                    code_snippet="query = 'SELECT * FROM users WHERE id=' + user_id",
                    cwe_ids=[89],
                    owasp_categories=["A03:2021"],
                    references=["https://cwe.mitre.org/data/definitions/89.html"],
                    fix_available=True,
                    fix_guidance="Use parameterized queries",
                    priority_score=85.0,
                    confidence="HIGH"
                ),
                UnifiedFinding(
                    finding_id="test-2",
                    scanner=ScannerType.BANDIT,
                    severity=FindingSeverity.MEDIUM,
                    category="Security",
                    file_path="test.py",
                    line_start=20,
                    line_end=22,
                    title="Hardcoded Password",
                    description="Password hardcoded in source",
                    code_snippet="password = 'admin123'",
                    cwe_ids=[259],
                    owasp_categories=["A07:2021"],
                    references=["https://cwe.mitre.org/data/definitions/259.html"],
                    fix_available=True,
                    fix_guidance="Use environment variables",
                    priority_score=65.0,
                    confidence="HIGH"
                ),
            ],
            duplicates_removed=0,
            findings_by_severity={
                FindingSeverity.HIGH: 1,
                FindingSeverity.MEDIUM: 1,
            },
            findings_by_scanner={
                ScannerType.BANDIT: 2,
            }
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_template_directory_initialization(self):
        """Test template directory initialization."""
        generator = ReportGenerator(template_dir=str(self.template_dir))
        self.assertEqual(generator.template_dir, self.template_dir)
    
    def test_default_template_directory(self):
        """Test default template directory."""
        generator = ReportGenerator()
        expected_dir = Path(__file__).parent.parent / "templates"
        self.assertEqual(generator.template_dir, expected_dir)
    
    def test_jinja2_environment_creation(self):
        """Test Jinja2 environment creation."""
        # Create a simple template
        html_dir = self.template_dir / "html"
        html_dir.mkdir()
        template_file = html_dir / "test.html"
        template_file.write_text("<html><body>{{ title }}</body></html>")
        
        generator = ReportGenerator(template_dir=str(self.template_dir))
        
        # Check if Jinja2 is available
        try:
            import jinja2
            self.assertIsNotNone(generator.jinja_env)
        except ImportError:
            self.assertIsNone(generator.jinja_env)
    
    def test_prepare_template_context(self):
        """Test template context preparation."""
        generator = ReportGenerator()
        context = generator._prepare_template_context(self.result, "Test Report")
        
        # Check required fields
        self.assertEqual(context["title"], "Test Report")
        self.assertEqual(context["target"], "test_project")
        self.assertIn("summary", context)
        self.assertIn("severity_breakdown", context)
        self.assertIn("scanner_breakdown", context)
        self.assertIn("findings", context)
        
        # Check summary
        self.assertEqual(context["summary"]["total_findings"], 2)
        self.assertEqual(context["summary"]["high_count"], 1)
        self.assertEqual(context["summary"]["medium_count"], 1)
        
        # Check findings
        self.assertEqual(len(context["findings"]), 2)
        self.assertEqual(context["findings"][0]["severity"], "HIGH")
    
    def test_overall_risk_calculation(self):
        """Test overall risk level calculation."""
        generator = ReportGenerator()
        
        # Test with high severity
        context = generator._prepare_template_context(self.result)
        self.assertEqual(context["overall_risk"], "HIGH")
        
        # Test with critical severity
        critical_result = OrchestrationResult(
            target="test",
            scan_time=datetime.now(),
            execution_time_seconds=1.0,
            total_findings=1,
            deduplicated_findings=[
                UnifiedFinding(
                    finding_id="test-critical",
                    scanner=ScannerType.BANDIT,
                    severity=FindingSeverity.CRITICAL,
                    category="Security",
                    file_path="test.py",
                    line_start=1,
                    line_end=1,
                    title="Critical Issue",
                    description="Critical security issue",
                    code_snippet="",  # Add required field
                    priority_score=95.0,
                    confidence="HIGH"
                ),
            ],
            duplicates_removed=0,
            findings_by_severity={FindingSeverity.CRITICAL: 1},
            findings_by_scanner={ScannerType.BANDIT: 1}
        )
        
        context = generator._prepare_template_context(critical_result)
        self.assertEqual(context["overall_risk"], "CRITICAL")
    
    def test_html_report_with_custom_template(self):
        """Test HTML report generation with custom template."""
        # Create custom template
        html_dir = self.template_dir / "html"
        html_dir.mkdir()
        template_file = html_dir / "custom.html"
        template_file.write_text("""
<!DOCTYPE html>
<html>
<head><title>{{ title }}</title></head>
<body>
    <h1>{{ title }}</h1>
    <p>Total Findings: {{ summary.total_findings }}</p>
    <p>Critical: {{ summary.critical_count }}</p>
</body>
</html>
""")
        
        generator = ReportGenerator(template_dir=str(self.template_dir))
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_path = f.name
        
        try:
            # Generate report with custom template
            generator.generate_report(
                self.result,
                output_path,
                format=ReportFormat.HTML,
                template_name="custom.html",
                title="Custom Report"
            )
            
            # Read and verify
            content = Path(output_path).read_text()
            self.assertIn("Custom Report", content)
            self.assertIn("Total Findings: 2", content)
        finally:
            Path(output_path).unlink()
    
    def test_markdown_report_with_template(self):
        """Test Markdown report generation with template."""
        # Create custom template
        md_dir = self.template_dir / "markdown"
        md_dir.mkdir()
        template_file = md_dir / "custom.md"
        template_file.write_text("""# {{ title }}

Total Findings: {{ summary.total_findings }}
Critical: {{ summary.critical_count }}
High: {{ summary.high_count }}
""")
        
        generator = ReportGenerator(template_dir=str(self.template_dir))
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            output_path = f.name
        
        try:
            generator.generate_report(
                self.result,
                output_path,
                format=ReportFormat.MARKDOWN,
                template_name="custom.md",
                title="Custom Markdown Report"
            )
            
            content = Path(output_path).read_text()
            self.assertIn("# Custom Markdown Report", content)
            self.assertIn("Total Findings: 2", content)
            self.assertIn("High: 1", content)
        finally:
            Path(output_path).unlink()
    
    def test_text_report_with_template(self):
        """Test text report generation with template."""
        # Create custom template
        text_dir = self.template_dir / "text"
        text_dir.mkdir()
        template_file = text_dir / "custom.txt"
        template_file.write_text("""{{ title }}
{{ "=" * 80 }}

Total Findings: {{ summary.total_findings }}
Critical: {{ summary.critical_count }}
High: {{ summary.high_count }}
""")
        
        generator = ReportGenerator(template_dir=str(self.template_dir))
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            output_path = f.name
        
        try:
            generator.generate_report(
                self.result,
                output_path,
                format=ReportFormat.TEXT,
                template_name="custom.txt",
                title="Custom Text Report"
            )
            
            content = Path(output_path).read_text()
            self.assertIn("Custom Text Report", content)
            self.assertIn("Total Findings: 2", content)
        finally:
            Path(output_path).unlink()
    
    def test_custom_template_variables(self):
        """Test passing custom variables to templates."""
        # Create template with custom variables
        html_dir = self.template_dir / "html"
        html_dir.mkdir()
        template_file = html_dir / "vars.html"
        template_file.write_text("""
<html>
<body>
    <h1>{{ title }}</h1>
    <p>Company: {{ company_name }}</p>
    <p>Author: {{ report_author }}</p>
</body>
</html>
""")
        
        generator = ReportGenerator(template_dir=str(self.template_dir))
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_path = f.name
        
        try:
            generator.generate_report(
                self.result,
                output_path,
                format=ReportFormat.HTML,
                template_name="vars.html",
                title="Report with Variables",
                company_name="Acme Corp",
                report_author="Security Team"
            )
            
            content = Path(output_path).read_text()
            self.assertIn("Company: Acme Corp", content)
            self.assertIn("Author: Security Team", content)
        finally:
            Path(output_path).unlink()
    
    def test_fallback_to_builtin_generation(self):
        """Test fallback to built-in generation when template not found."""
        generator = ReportGenerator(template_dir=str(self.template_dir))
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_path = f.name
        
        try:
            # Try to use non-existent template
            generator.generate_report(
                self.result,
                output_path,
                format=ReportFormat.HTML,
                template_name="nonexistent.html",
                title="Fallback Report"
            )
            
            # Should still generate report using built-in method
            content = Path(output_path).read_text()
            self.assertIn("Fallback Report", content)
            self.assertTrue(len(content) > 0)
        finally:
            Path(output_path).unlink()
    
    def test_chart_script_generation(self):
        """Test chart script generation."""
        generator = ReportGenerator()
        script = generator._generate_chart_script(self.result)
        
        self.assertIn("severityChart", script)
        self.assertIn("scannerChart", script)
        self.assertIn("Chart(", script)
        self.assertIn("bar", script)
        self.assertIn("pie", script)
    
    def test_css_loading(self):
        """Test CSS file loading."""
        # Create CSS file
        html_dir = self.template_dir / "html"
        html_dir.mkdir()
        css_file = html_dir / "styles.css"
        css_file.write_text("body { color: red; }")
        
        generator = ReportGenerator(template_dir=str(self.template_dir))
        context = generator._prepare_template_context(self.result)
        
        self.assertIn("css_content", context)
        self.assertIn("body { color: red; }", context["css_content"])


class TestTemplateEdgeCases(unittest.TestCase):
    """Test edge cases for template functionality."""
    
    def test_empty_findings(self):
        """Test template rendering with no findings."""
        result = OrchestrationResult(
            target="empty_project",
            scan_time=datetime.now(),
            execution_time_seconds=0.5,
            total_findings=0,
            deduplicated_findings=[],
            duplicates_removed=0,
            findings_by_severity={},
            findings_by_scanner={}
        )
        
        generator = ReportGenerator()
        context = generator._prepare_template_context(result)
        
        self.assertEqual(context["summary"]["total_findings"], 0)
        self.assertEqual(context["overall_risk"], "NONE")
        self.assertEqual(len(context["findings"]), 0)
    
    def test_missing_css_file(self):
        """Test handling of missing CSS file."""
        temp_dir = tempfile.mkdtemp()
        try:
            template_dir = Path(temp_dir) / "templates"
            template_dir.mkdir()
            
            generator = ReportGenerator(template_dir=str(template_dir))
            context = generator._prepare_template_context(
                OrchestrationResult(
                    target="test",
                    scan_time=datetime.now(),
                    execution_time_seconds=1.0,
                    total_findings=0,
                    deduplicated_findings=[],
                    duplicates_removed=0,
                    findings_by_severity={},
                    findings_by_scanner={}
                )
            )
            
            # Should have empty CSS content
            self.assertEqual(context["css_content"], "")
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
