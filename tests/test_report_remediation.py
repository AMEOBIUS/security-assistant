
import pytest
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

class TestReportGeneratorRemediation:
    """Test Remediation Advice integration in ReportGenerator."""
    
    def test_remediation_in_html_report(self, report_generator, sample_result, temp_output_dir):
        """Test that remediation advice appears in HTML report."""
        # Ensure remediation is enabled
        assert report_generator.enable_remediation is True
        
        output_path = temp_output_dir / "remediation_test.html"
        
        # Modify sample finding to match a known template (e.g. SQL Injection)
        # sample_finding already has "SQL Injection" title, which should match
        
        report_generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.HTML
        )
        
        content = output_path.read_text(encoding='utf-8')
        
        # Check for remediation section
        assert "Recommended Remediation" in content
        assert "Secure Example" in content
        assert "parameterized queries" in content or "Use parameterized queries" in content

    def test_remediation_disabled(self, sample_result, temp_output_dir):
        """Test report generation when remediation is disabled."""
        generator = ReportGenerator(enable_remediation=False)
        output_path = temp_output_dir / "no_remediation_test.html"
        
        generator.generate_report(
            sample_result,
            str(output_path),
            format=ReportFormat.HTML
        )
        
        content = output_path.read_text(encoding='utf-8')
        
        # Remediation section should not be present
        assert "Recommended Remediation" not in content
