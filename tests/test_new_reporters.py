"""
Tests for New Reporters (HTML and SARIF)

Verifies the integration of HTML and SARIF reporters into the Factory
and their correct generation logic.
"""

import json
import unittest
from datetime import datetime

from security_assistant.orchestrator import (
    FindingSeverity,
    OrchestrationResult,
    ScannerType,
    UnifiedFinding,
)
from security_assistant.reporting.html_reporter import HTMLReporter
from security_assistant.reporting.reporter_factory import ReporterFactory
from security_assistant.reporting.sarif_reporter import SarifReporter


class TestNewReporters(unittest.TestCase):
    
    def setUp(self):
        # Create a mock finding
        self.finding = UnifiedFinding(
            finding_id="test-finding-1",
            title="SQL Injection",
            description="Possible SQL Injection vulnerability",
            severity=FindingSeverity.HIGH,
            scanner=ScannerType.BANDIT,
            file_path="src/db.py",
            line_start=10,
            line_end=12,
            cwe_ids=["CWE-89"],
            confidence=0.9,
            category="injection",
            code_snippet="query = 'SELECT * FROM users WHERE id = ' + user_input"
        )
        
        # Create a mock result
        self.result = OrchestrationResult(
            target="src/",
            scan_time=datetime.now(),
            execution_time_seconds=1.5,
            all_findings=[self.finding],
            deduplicated_findings=[self.finding],
            total_findings=1,
            findings_by_severity={FindingSeverity.HIGH: 1},
            findings_by_scanner={ScannerType.BANDIT: 1}
        )
    
    def test_factory_registration(self):
        """Test that new reporters are registered in the factory."""
        html_reporter = ReporterFactory.create("html")
        self.assertIsInstance(html_reporter, HTMLReporter)
        
        sarif_reporter = ReporterFactory.create("sarif")
        self.assertIsInstance(sarif_reporter, SarifReporter)

    def test_html_generation(self):
        """Test HTML report generation."""
        # Using self.result which is initialized with findings=[self.finding]
        # OrchestrationResult accepts 'all_findings' not 'findings'
        self.result = OrchestrationResult(
            target="src/",
            scan_time=datetime.now(),
            execution_time_seconds=1.5,
            all_findings=[self.finding],
            deduplicated_findings=[self.finding],
            total_findings=1,
            findings_by_severity={FindingSeverity.HIGH: 1},
            findings_by_scanner={ScannerType.BANDIT: 1}
        )
        
        reporter = HTMLReporter(include_charts=True)
        html_content = reporter.generate(self.result, title="Test Report")
        
        self.assertIn("<!DOCTYPE html>", html_content)
        self.assertIn("Test Report", html_content)
        self.assertIn("SQL Injection", html_content)
        self.assertIn("chart.umd.min.js", html_content)
        
    def test_sarif_generation(self):
        """Test SARIF report generation."""
        self.result = OrchestrationResult(
            target="src/",
            scan_time=datetime.now(),
            execution_time_seconds=1.5,
            all_findings=[self.finding],
            deduplicated_findings=[self.finding],
            total_findings=1,
            findings_by_severity={FindingSeverity.HIGH: 1},
            findings_by_scanner={ScannerType.BANDIT: 1}
        )

        reporter = SarifReporter()
        sarif_content = reporter.generate(self.result)
        
        # Parse JSON to verify structure
        sarif_json = json.loads(sarif_content)
        
        self.assertEqual(sarif_json["version"], "2.1.0")
        self.assertEqual(len(sarif_json["runs"]), 1)
        
        run = sarif_json["runs"][0]
        self.assertEqual(run["tool"]["driver"]["name"], "Security Assistant")
        
        # Verify rule
        self.assertEqual(len(run["tool"]["driver"]["rules"]), 1)
        rule = run["tool"]["driver"]["rules"][0]
        self.assertEqual(rule["id"], "CWE-89")
        
        # Verify result
        self.assertEqual(len(run["results"]), 1)
        res = run["results"][0]
        self.assertEqual(res["ruleId"], "CWE-89")
        self.assertEqual(res["level"], "error")  # HIGH -> error
        self.assertEqual(res["locations"][0]["physicalLocation"]["artifactLocation"]["uri"], "src/db.py")

if __name__ == '__main__':
    unittest.main()
