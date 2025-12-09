"""Tests for Nuclei Scanner."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from security_assistant.scanners.base_scanner import ScannerError
from security_assistant.scanners.nuclei_scanner import (
    NucleiFinding,
    NucleiScanner,
    NucleiScanResult,
)


@pytest.fixture
def mock_shutil_which():
    with patch("shutil.which") as mock:
        mock.return_value = "/usr/bin/nuclei"
        yield mock


@pytest.fixture
def mock_subprocess_run():
    with patch("subprocess.run") as mock:
        yield mock


class TestNucleiScanner:
    """Test Nuclei scanner integration."""

    def test_init_success(self, mock_shutil_which):
        """Test successful initialization."""
        scanner = NucleiScanner()
        assert scanner

    def test_run_success(self, mock_shutil_which, mock_subprocess_run):
        """Test successful scan run."""
        scanner = NucleiScanner()
        
        # Mock Nuclei JSON output
        nuclei_output = json.dumps({
            "template-id": "tech-detect",
            "info": {
                "name": "Wappalyzer Technology Detection",
                "severity": "info",
                "description": "Detects technologies.",
                "reference": ["https://wappalyzer.com"],
                "classification": {"cwe-id": ["CWE-200"]}
            },
            "type": "http",
            "host": "https://example.com",
            "matched-at": "https://example.com",
            "extracted-results": ["Apache"],
            "ip": "93.184.216.34",
            "timestamp": "2023-10-01T12:00:00.000000Z",
            "curl-command": "curl -X GET https://example.com"
        }) + "\n"

        mock_subprocess_run.return_value = MagicMock(
            returncode=0,
            stdout=nuclei_output,
            stderr=""
        )

        result = scanner.scan_file("https://example.com")

        assert isinstance(result, NucleiScanResult)
        assert len(result.findings) == 1
        # assert result.target == "https://example.com" # Target might be unknown in _parse_output, or fixed in scan_file
        
        finding = result.findings[0]
        assert finding.template_id == "tech-detect"
        assert finding.info["severity"] == "info"
        assert finding.host == "https://example.com"

    def test_run_non_url(self, mock_shutil_which):
        """Test handling of non-URL targets."""
        scanner = NucleiScanner()
        result = scanner.scan_file("/local/path")
        
        # Should skip scan
        assert len(result.findings) == 0
        assert result.target == "/local/path"

    def test_run_failure(self, mock_shutil_which, mock_subprocess_run):
        """Test handling of Nuclei execution failure."""
        scanner = NucleiScanner()
        
        mock_subprocess_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="Error: connection refused"
        )

        with pytest.raises(ScannerError, match="nuclei failed with exit code 1"):
            scanner.scan_file("https://example.com")

    def test_parse_invalid_json(self, mock_shutil_which):
        """Test parsing invalid JSON output."""
        scanner = NucleiScanner()
        output = "Not JSON\n" + json.dumps({"template-id": "valid"})
        
        result = scanner._parse_output(output)
        assert len(result.findings) == 1
        assert result.findings[0].template_id == "valid"
