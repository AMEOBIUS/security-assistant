"""Tests for HTMLReporter - FIXED"""
from pathlib import Path

import pytest

from security_assistant.orchestrator import FindingSeverity, ScannerType
from security_assistant.reporting.html_reporter import HTMLReporter
from tests.conftest_reporters import create_test_finding, create_test_result


@pytest.fixture
def sample_finding():
    return create_test_finding(
        finding_id="html-001",
        scanner=ScannerType.BANDIT,
        severity=FindingSeverity.HIGH,
        title="Command Injection",
        file_path="app/views.py",
        code_snippet="os.system('ls ' + user_input)"
    )

@pytest.fixture
def sample_result(sample_finding):
    return create_test_result(target="web_app", findings=[sample_finding])

class TestHTMLReporter:
    def test_initialization(self):
        reporter = HTMLReporter()
        assert reporter.format == "html"
        assert reporter.include_charts is True
    
    def test_initialization_without_charts(self):
        reporter = HTMLReporter(include_charts=False)
        assert reporter.include_charts is False
    
    def test_generate_basic(self, sample_result):
        reporter = HTMLReporter()
        content = reporter.generate(sample_result)
        assert "<!DOCTYPE html>" in content
        assert "</html>" in content
    
    def test_generate_contains_title(self, sample_result):
        reporter = HTMLReporter()
        content = reporter.generate(sample_result, title="Security Report")
        assert "Security Report" in content
    
    def test_generate_with_charts(self, sample_result):
        reporter = HTMLReporter(include_charts=True)
        content = reporter.generate(sample_result)
        assert "chart" in content.lower() or "Chart" in content
    
    def test_generate_without_charts(self, sample_result):
        reporter = HTMLReporter(include_charts=False)
        content = reporter.generate(sample_result)
        assert "severityChart" not in content
    
    def test_generate_with_code_snippets(self, sample_result):
        reporter = HTMLReporter(include_code_snippets=True)
        content = reporter.generate(sample_result)
        assert "os.system" in content
    
    def test_generate_without_code_snippets(self, sample_result):
        reporter = HTMLReporter(include_code_snippets=False)
        content = reporter.generate(sample_result)
        assert "Command Injection" in content
        assert "os.system" not in content
    
    def test_generate_to_file(self, sample_result, tmp_path):
        reporter = HTMLReporter()
        output_file = tmp_path / "report.html"
        result_path = reporter.generate_to_file(sample_result, str(output_file))
        assert Path(result_path).exists()
    
    def test_multiple_findings(self):
        findings = [create_test_finding(finding_id=f"html-{i}", title=f"Issue {i}") for i in range(3)]
        result = create_test_result(findings=findings)
        reporter = HTMLReporter()
        content = reporter.generate(result)
        assert "Issue 0" in content
        assert "Issue 2" in content
