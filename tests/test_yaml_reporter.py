"""Tests for YAMLReporter - FIXED"""
from pathlib import Path

import pytest
import yaml

from security_assistant.orchestrator import FindingSeverity, ScannerType
from security_assistant.reporting.yaml_reporter import YAMLReporter
from tests.conftest_reporters import create_test_finding, create_test_result


@pytest.fixture
def sample_finding():
    return create_test_finding(
        finding_id="yaml-001",
        scanner=ScannerType.SEMGREP,
        severity=FindingSeverity.CRITICAL,
        title="Hardcoded Secret",
        code_snippet='API_KEY = "sk-1234"'
    )

@pytest.fixture
def sample_result(sample_finding):
    return create_test_result(target="secure_app", findings=[sample_finding])

class TestYAMLReporter:
    def test_initialization(self):
        reporter = YAMLReporter()
        assert reporter.format == "yaml"
    
    def test_generate_basic(self, sample_result):
        reporter = YAMLReporter()
        content = reporter.generate(sample_result)
        data = yaml.safe_load(content)
        assert isinstance(data, dict)
    
    def test_generate_contains_metadata(self, sample_result):
        reporter = YAMLReporter()
        content = reporter.generate(sample_result)
        data = yaml.safe_load(content)
        assert "metadata" in data
        assert data["metadata"]["target"] == "secure_app"
    
    def test_generate_contains_findings(self, sample_result):
        reporter = YAMLReporter()
        content = reporter.generate(sample_result)
        data = yaml.safe_load(content)
        assert "findings" in data
        assert len(data["findings"]) == 1
    
    def test_generate_with_code_snippets(self, sample_result):
        reporter = YAMLReporter(include_code_snippets=True)
        content = reporter.generate(sample_result)
        data = yaml.safe_load(content)
        assert 'API_KEY' in data["findings"][0]["code_snippet"]
    
    def test_generate_without_code_snippets(self, sample_result):
        reporter = YAMLReporter(include_code_snippets=False)
        content = reporter.generate(sample_result)
        data = yaml.safe_load(content)
        # Code snippet should be empty or not present
        assert data["findings"][0].get("code_snippet", "") == ""
    
    def test_generate_to_file(self, sample_result, tmp_path):
        reporter = YAMLReporter()
        output_file = tmp_path / "report.yaml"
        result_path = reporter.generate_to_file(sample_result, str(output_file))
        assert Path(result_path).exists()
    
    def test_generate_empty_result(self):
        empty_result = create_test_result(target="clean", findings=[])
        reporter = YAMLReporter()
        content = reporter.generate(empty_result)
        data = yaml.safe_load(content)
        assert data["summary"]["total_findings"] == 0
