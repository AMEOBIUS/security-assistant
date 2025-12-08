"""Tests for SarifReporter - FIXED"""
import pytest
import json
from pathlib import Path
from security_assistant.reporting.sarif_reporter import SarifReporter
from security_assistant.orchestrator import FindingSeverity, ScannerType
from tests.conftest_reporters import create_test_result, create_test_finding

@pytest.fixture
def sample_finding():
    return create_test_finding(
        finding_id="sarif-001",
        scanner=ScannerType.SEMGREP,
        severity=FindingSeverity.CRITICAL,
        title="Weak Crypto",
        file_path="crypto/hash.py",
        code_snippet="hashlib.md5(password)"
    )

@pytest.fixture
def sample_result(sample_finding):
    return create_test_result(target="crypto_app", findings=[sample_finding])

class TestSarifReporter:
    def test_initialization(self):
        reporter = SarifReporter()
        assert reporter.format == "sarif"
    
    def test_generate_basic(self, sample_result):
        reporter = SarifReporter()
        content = reporter.generate(sample_result)
        data = json.loads(content)
        assert isinstance(data, dict)
    
    def test_generate_valid_sarif_schema(self, sample_result):
        reporter = SarifReporter()
        content = reporter.generate(sample_result)
        data = json.loads(content)
        assert "$schema" in data
        assert "sarif-schema-2.1.0.json" in data["$schema"]
        assert data["version"] == "2.1.0"
    
    def test_generate_contains_runs(self, sample_result):
        reporter = SarifReporter()
        content = reporter.generate(sample_result)
        data = json.loads(content)
        assert "runs" in data
        assert len(data["runs"]) > 0
    
    def test_generate_contains_tool_info(self, sample_result):
        reporter = SarifReporter()
        content = reporter.generate(sample_result)
        data = json.loads(content)
        tool = data["runs"][0]["tool"]
        assert tool["driver"]["name"] == "Security Assistant"
    
    def test_generate_contains_results(self, sample_result):
        reporter = SarifReporter()
        content = reporter.generate(sample_result)
        data = json.loads(content)
        results = data["runs"][0]["results"]
        assert len(results) == 1
    
    def test_result_has_location(self, sample_result):
        reporter = SarifReporter()
        content = reporter.generate(sample_result)
        data = json.loads(content)
        result = data["runs"][0]["results"][0]
        location = result["locations"][0]["physicalLocation"]
        assert location["artifactLocation"]["uri"] == "crypto/hash.py"
    
    def test_severity_mapping(self, sample_result):
        reporter = SarifReporter()
        content = reporter.generate(sample_result)
        data = json.loads(content)
        result = data["runs"][0]["results"][0]
        assert result["level"] == "error"
    
    def test_generate_with_code_snippets(self, sample_result):
        reporter = SarifReporter(include_code_snippets=True)
        content = reporter.generate(sample_result)
        data = json.loads(content)
        result = data["runs"][0]["results"][0]
        region = result["locations"][0]["physicalLocation"]
        assert "contextRegion" in region or "snippet" in region.get("region", {})
    
    def test_generate_to_file(self, sample_result, tmp_path):
        reporter = SarifReporter()
        output_file = tmp_path / "report.sarif"
        result_path = reporter.generate_to_file(sample_result, str(output_file))
        assert Path(result_path).exists()
    
    def test_multiple_findings(self):
        findings = [create_test_finding(finding_id=f"sarif-{i}", title=f"Issue {i}") for i in range(4)]
        result = create_test_result(findings=findings)
        reporter = SarifReporter()
        content = reporter.generate(result)
        data = json.loads(content)
        assert len(data["runs"][0]["results"]) == 4
