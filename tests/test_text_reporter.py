"""Tests for TextReporter - FIXED"""
from pathlib import Path

import pytest

from security_assistant.orchestrator import FindingSeverity, ScannerType
from security_assistant.reporting.text_reporter import TextReporter
from tests.conftest_reporters import create_test_finding, create_test_result


@pytest.fixture
def sample_finding():
    return create_test_finding(
        finding_id="test-001",
        scanner=ScannerType.BANDIT,
        severity=FindingSeverity.HIGH,
        title="SQL Injection",
        file_path="test/file.py",
        code_snippet="cursor.execute('SELECT * FROM users WHERE id = ' + user_id)"
    )

@pytest.fixture
def sample_result(sample_finding):
    return create_test_result(target="test_project", findings=[sample_finding])

class TestTextReporter:
    def test_initialization(self):
        reporter = TextReporter()
        assert reporter.format == "text"
    
    def test_generate_basic(self, sample_result):
        reporter = TextReporter()
        content = reporter.generate(sample_result)
        assert "Security Scan Report" in content
        assert "test_project" in content
    
    def test_generate_contains_summary(self, sample_result):
        reporter = TextReporter()
        content = reporter.generate(sample_result)
        assert "EXECUTIVE SUMMARY" in content
    
    def test_generate_with_code_snippets(self, sample_result):
        reporter = TextReporter(include_code_snippets=True)
        content = reporter.generate(sample_result)
        assert "cursor.execute" in content
    
    def test_generate_without_code_snippets(self, sample_result):
        reporter = TextReporter(include_code_snippets=False)
        content = reporter.generate(sample_result)
        assert "SQL Injection" in content
        assert "cursor.execute" not in content
    
    def test_generate_to_file(self, sample_result, tmp_path):
        reporter = TextReporter()
        output_file = tmp_path / "report.txt"
        result_path = reporter.generate_to_file(sample_result, str(output_file))
        assert Path(result_path).exists()
    
    def test_generate_empty_result(self):
        empty_result = create_test_result(target="empty", findings=[])
        reporter = TextReporter()
        content = reporter.generate(empty_result)
        assert "Total Findings:      0" in content
    
    def test_multiple_findings(self):
        findings = [create_test_finding(finding_id=f"test-{i}", title=f"Issue {i}") for i in range(5)]
        result = create_test_result(findings=findings)
        reporter = TextReporter()
        content = reporter.generate(result)
        assert "Issue 0" in content
