
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from security_assistant.orchestrator import (
    BulkScanResult,
    FindingSeverity,
    OrchestrationResult,
    ScannerType,
    ScanOrchestrator,
    UnifiedFinding,
)
from security_assistant.report_generator import ReportFormat, ReportGenerator


@pytest.fixture
def sample_orchestration_result():
    return OrchestrationResult(
        total_findings=5,
        findings_by_severity={FindingSeverity.HIGH: 2, FindingSeverity.MEDIUM: 3},
        execution_time_seconds=1.5,
        target="src/project1"
    )

class TestBulkOperations:
    
    def test_bulk_scan_result_aggregation(self, sample_orchestration_result):
        """Test aggregation logic in BulkScanResult."""
        bulk_result = BulkScanResult()
        
        # Result 1
        bulk_result.results["project1"] = sample_orchestration_result
        
        # Result 2 (different stats)
        result2 = OrchestrationResult(
            total_findings=10,
            findings_by_severity={FindingSeverity.CRITICAL: 1, FindingSeverity.HIGH: 4},
            execution_time_seconds=2.0,
            target="src/project2"
        )
        bulk_result.results["project2"] = result2
        
        assert bulk_result.total_findings == 15
        assert bulk_result.total_critical == 1
        assert bulk_result.total_high == 6
        
        stats = bulk_result.get_aggregated_stats()
        assert stats["targets_scanned"] == 2
        assert stats["total_findings"] == 15

    @patch("security_assistant.orchestrator.ScanOrchestrator.scan_directory")
    @patch("security_assistant.orchestrator.ScanOrchestrator.scan_file")
    def test_orchestrator_scan_multiple_targets(self, mock_scan_file, mock_scan_dir):
        """Test scan_multiple_targets method."""
        orchestrator = ScanOrchestrator(max_workers=1)
        orchestrator.enable_scanner(ScannerType.BANDIT, MagicMock())
        
        # Mock return values
        mock_scan_dir.return_value = OrchestrationResult(target="dir1")
        mock_scan_file.return_value = OrchestrationResult(target="file1.py")
        
        with patch("pathlib.Path.is_file") as mock_is_file:
            with patch("pathlib.Path.is_dir") as mock_is_dir:
                # Setup path mocks
                def is_file_side_effect(self):
                    return str(self) == "file1.py"
                def is_dir_side_effect(self):
                    return str(self) == "dir1"
                
                # Use side_effects but we need to be careful with how Path is mocked
                # Easier approach: rely on the orchestrator calling checks
                # Actually orchestrator calls `Path(target).is_file()`
                
                # Let's mock Path in orchestrator module specifically or just mock methods behavior
                pass 

        # Integration-style test with mocks
        # We'll just mock the underlying scan methods and assume Path works (or mock Path)
        
        with patch("security_assistant.orchestrator.Path") as MockPath:
            # Mock behavior for "dir1"
            dir_path = MagicMock()
            dir_path.is_file.return_value = False
            dir_path.is_dir.return_value = True
            
            # Mock behavior for "file1.py"
            file_path = MagicMock()
            file_path.is_file.return_value = True
            file_path.is_dir.return_value = False
            
            # Side effect for Path constructor
            def path_side_effect(arg):
                if arg == "dir1":
                    return dir_path
                if arg == "file1.py":
                    return file_path
                return MagicMock()
            
            MockPath.side_effect = path_side_effect
            
            targets = ["dir1", "file1.py"]
            bulk_result = orchestrator.scan_multiple_targets(targets)
            
            assert len(bulk_result.results) == 2
            assert "dir1" in bulk_result.results
            assert "file1.py" in bulk_result.results
            
            mock_scan_dir.assert_called_with("dir1")
            mock_scan_file.assert_called_with("file1.py")

    def test_generate_bulk_report(self, tmp_path):
        """Test bulk report generation (CSV/JSON/HTML)."""
        generator = ReportGenerator()
        
        bulk_result = BulkScanResult()
        # Add a sample result with findings
        finding = UnifiedFinding(
            finding_id="test-1",
            scanner=ScannerType.BANDIT,
            severity=FindingSeverity.HIGH,
            category="security",
            file_path="test.py",
            line_start=1,
            line_end=1,
            title="Test Finding",
            description="Desc",
            code_snippet="code",
            cwe_ids=["CWE-89"]
        )
        
        result = OrchestrationResult(
            deduplicated_findings=[finding],
            findings_by_severity={FindingSeverity.HIGH: 1},
            total_findings=1
        )
        bulk_result.results["project1"] = result
        
        output_dir = tmp_path / "reports"
        
        paths = generator.generate_bulk_report(
            bulk_result, 
            str(output_dir), 
            formats=[ReportFormat.JSON, ReportFormat.HTML, "csv"]
        )
        
        assert "json" in paths
        assert "html" in paths
        assert "csv" in paths
        
        assert Path(paths["json"]).exists()
        assert Path(paths["html"]).exists()
        assert Path(paths["csv"]).exists()
        
        # Verify CSV content
        csv_content = Path(paths["csv"]).read_text(encoding="utf-8")
        assert "project1" in csv_content
        assert "Test Finding" in csv_content
        assert "CWE-89" in csv_content
