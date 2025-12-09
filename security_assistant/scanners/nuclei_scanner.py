"""
Nuclei Scanner Integration.

Wraps the Nuclei CLI tool for DAST scanning of web applications.
"""

import json
import logging
from dataclasses import dataclass
from typing import List, Optional

from security_assistant.gitlab_api import IssueData
from security_assistant.scanners.base_scanner import (
    BaseScanner,
    ScannerError,
    ScannerNotInstalledError,
)

logger = logging.getLogger(__name__)


class NucleiScannerError(ScannerError):
    """Nuclei scanner error."""
    pass


class NucleiNotInstalledError(ScannerNotInstalledError):
    """Nuclei is not installed."""
    pass


@dataclass
class NucleiFinding:
    """Raw finding from Nuclei JSON output."""
    template_id: str
    info: dict
    type: str
    host: str
    matched_at: str
    extracted_results: Optional[List[str]] = None
    ip: Optional[str] = None
    timestamp: Optional[str] = None
    curl_command: Optional[str] = None


@dataclass
class NucleiScanResult:
    """Result of a Nuclei scan."""
    findings: List[NucleiFinding]
    target: str
    duration: float = 0.0


class NucleiScanner(BaseScanner[NucleiFinding, NucleiScanResult]):
    """
    Nuclei scanner wrapper.
    
    Requires 'nuclei' binary to be in PATH.
    """

    @property
    def name(self) -> str:
        return "nuclei"

    @property
    def command(self) -> str:
        return "nuclei"

    def _valid_return_codes(self) -> List[int]:
        """Nuclei returns 0 on success."""
        return [0]

    def _get_not_installed_error(self) -> NucleiNotInstalledError:
        return NucleiNotInstalledError(
            "Nuclei is not installed. Please install it with: go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest"
        )

    def _build_command(self, targets: List[str], **kwargs) -> List[str]:
        """Build Nuclei command."""
        target = targets[0] if targets else ""
        
        # If target is a file, use -l (list of targets), if URL use -target
        # But we assume targets[0] is the target string
        
        cmd = [
            "nuclei",
            "-target", target,
            "-json",
            "-silent",
            "-nc",
        ]
        
        if self.config and self.config.extra_args:
            cmd.extend(self.config.extra_args)
            
        return cmd

    def _parse_output(self, raw: str) -> NucleiScanResult:
        """Parse NDJSON output from Nuclei."""
        findings = []
        for line in raw.splitlines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                findings.append(NucleiFinding(
                    template_id=data.get("template-id", ""),
                    info=data.get("info", {}),
                    type=data.get("type", "unknown"),
                    host=data.get("host", ""),
                    matched_at=data.get("matched-at", ""),
                    extracted_results=data.get("extracted-results"),
                    ip=data.get("ip"),
                    timestamp=data.get("timestamp"),
                    curl_command=data.get("curl-command")
                ))
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse Nuclei JSON line: {line[:50]}...")
                
        return NucleiScanResult(findings=findings, target="unknown")

    # Override scan_file/scan_directory to support URLs
    def scan_file(self, file_path: str) -> NucleiScanResult:
        """Scan a URL (hijacking scan_file)."""
        # If it looks like a URL, scan it
        if file_path.startswith("http://") or file_path.startswith("https://"):
            return self._run_scan([file_path])
        
        # Otherwise, skip (Nuclei is DAST)
        logger.info(f"Skipping Nuclei scan for non-URL target: {file_path}")
        return NucleiScanResult(findings=[], target=file_path)

    def scan_directory(self, directory: str, recursive: bool = True) -> NucleiScanResult:
        """Scan a directory (Nuclei doesn't support directory scanning directly)."""
        logger.info(f"Skipping Nuclei scan for directory: {directory}")
        return NucleiScanResult(findings=[], target=directory)

    # GitLab Integration methods
    def finding_to_issue(self, finding: NucleiFinding, project_name: str = "Unknown") -> IssueData:
        return IssueData(
            title=f"Nuclei: {finding.info.get('name', finding.template_id)}",
            description=f"{finding.info.get('description', '')}\n\nURL: {finding.matched_at}",
            severity=finding.info.get("severity", "unknown"),
            fingerprint=f"nuclei-{finding.template_id}-{finding.host}"
        )

    def _get_findings_from_result(self, result: NucleiScanResult) -> List[NucleiFinding]:
        return result.findings

    def _get_finding_file(self, finding: NucleiFinding) -> str:
        return finding.host

    def _create_grouped_issue(self, file_path: str, findings: List[NucleiFinding], project_name: str) -> IssueData:
        return IssueData(
            title=f"Nuclei Findings for {file_path}",
            description=f"Found {len(findings)} issues on {file_path}",
            severity="medium",
            fingerprint=f"nuclei-group-{file_path}"
        )
