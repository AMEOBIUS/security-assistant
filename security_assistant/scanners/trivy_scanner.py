"""
Trivy Scanner Integration for Security Assistant

This module provides integration with Trivy, a comprehensive security scanner
for containers, filesystems, and repositories. Trivy can detect:
- OS package vulnerabilities (CVEs)
- Application dependency vulnerabilities
- IaC misconfigurations
- Secrets in code
- Software licenses

Trivy supports multiple scan targets:
- Container images (Docker, OCI)
- Filesystem paths
- Git repositories
- SBOM files (CycloneDX, SPDX)

Version: 1.0.0
Compatible with: Trivy v0.67.0+
"""

import json
import logging
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Set
from dataclasses import dataclass, field
from enum import Enum

from ..gitlab_api import IssueData


# Configure logging
logger = logging.getLogger(__name__)


class TrivySeverity(str, Enum):
    """Trivy vulnerability severity levels"""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class TrivyScanType(str, Enum):
    """Trivy scan types"""
    IMAGE = "image"
    FILESYSTEM = "fs"
    REPOSITORY = "repo"
    SBOM = "sbom"
    CONFIG = "config"


class TrivyScanner:
    """Scanner for vulnerabilities using Trivy"""
    
    SEVERITY_PRIORITY = {
        TrivySeverity.CRITICAL: 5,
        TrivySeverity.HIGH: 4,
        TrivySeverity.MEDIUM: 3,
        TrivySeverity.LOW: 2,
        TrivySeverity.UNKNOWN: 1,
    }
    
    SEVERITY_EMOJI = {
        TrivySeverity.CRITICAL: "🔴",
        TrivySeverity.HIGH: "🟠",
        TrivySeverity.MEDIUM: "🟡",
        TrivySeverity.LOW: "🟢",
        TrivySeverity.UNKNOWN: "⚪",
    }
    
    def __init__(
        self,
        min_severity: TrivySeverity = TrivySeverity.MEDIUM,
        scan_type: TrivyScanType = TrivyScanType.IMAGE,
        timeout: int = 600,
        skip_db_update: bool = False,
        offline_scan: bool = False,
    ):
        """
        Initialize Trivy scanner
        
        Args:
            min_severity: Minimum severity level to report (default: MEDIUM)
            scan_type: Type of scan to perform (default: IMAGE)
            timeout: Scan timeout in seconds (default: 600)
            skip_db_update: Skip vulnerability database update (default: False)
            offline_scan: Perform offline scan (default: False)
        
        Raises:
            TrivyNotInstalledError: If Trivy is not installed
        """
        self.min_severity = min_severity
        self.scan_type = scan_type
        self.timeout = timeout
        self.skip_db_update = skip_db_update
        self.offline_scan = offline_scan
        
        # Verify Trivy installation
        if not self._is_trivy_installed():
            raise TrivyNotInstalledError(
                "Trivy is not installed. Install it from: "
                "https://aquasecurity.github.io/trivy/latest/getting-started/installation/"
            )
        
        logger.info(
            f"Initialized TrivyScanner: min_severity={min_severity}, "
            f"scan_type={scan_type}, timeout={timeout}s"
        )
    
    def _is_trivy_installed(self) -> bool:
        """Check if Trivy is installed and accessible"""
        return shutil.which("trivy") is not None
    
    def scan_image(
        self,
        image: str,
        scanners: Optional[List[str]] = None,
    ) -> "TrivyScanResult":
        """
        Scan a container image for vulnerabilities
        
        Args:
            image: Container image name (e.g., "alpine:3.15", "nginx:latest")
            scanners: List of scanners to use (vuln, config, secret, license)
                     Default: ["vuln"] (vulnerabilities only)
        
        Returns:
            TrivyScanResult with findings
        
        Example:
            >>> scanner = TrivyScanner()
            >>> result = scanner.scan_image("alpine:3.15")
            >>> print(f"Found {result.vulnerability_count} vulnerabilities")
        """
        if scanners is None:
            scanners = ["vuln"]
        
        logger.info(f"Scanning container image: {image}")
        
        cmd = [
            "trivy",
            "image",
            "--format", "json",
            "--severity", self._get_severity_filter(),
            "--scanners", ",".join(scanners),
        ]
        
        if self.skip_db_update:
            cmd.append("--skip-db-update")
        
        if self.offline_scan:
            cmd.append("--offline-scan")
        
        cmd.append(image)
        
        return self._run_trivy(cmd, image, TrivyScanType.IMAGE)
    
    def scan_filesystem(
        self,
        path: str,
        scanners: Optional[List[str]] = None,
    ) -> "TrivyScanResult":
        """
        Scan a filesystem path for vulnerabilities
        
        Args:
            path: Path to scan (directory or file)
            scanners: List of scanners to use (vuln, config, secret, license)
                     Default: ["vuln", "secret", "config"]
        
        Returns:
            TrivyScanResult with findings
        
        Example:
            >>> scanner = TrivyScanner()
            >>> result = scanner.scan_filesystem("/path/to/project")
            >>> print(f"Found {len(result.findings)} issues")
        """
        if scanners is None:
            scanners = ["vuln", "secret", "config"]
        
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Path not found: {path}")
        
        logger.info(f"Scanning filesystem: {path}")
        
        cmd = [
            "trivy",
            "fs",
            "--format", "json",
            "--severity", self._get_severity_filter(),
            "--scanners", ",".join(scanners),
        ]
        
        if self.skip_db_update:
            cmd.append("--skip-db-update")
        
        if self.offline_scan:
            cmd.append("--offline-scan")
        
        cmd.append(str(path_obj))
        
        return self._run_trivy(cmd, str(path_obj), TrivyScanType.FILESYSTEM)
    
    def scan_repository(
        self,
        repo_url: str,
        scanners: Optional[List[str]] = None,
    ) -> "TrivyScanResult":
        """
        Scan a Git repository for vulnerabilities
        
        Args:
            repo_url: Git repository URL
            scanners: List of scanners to use
        
        Returns:
            TrivyScanResult with findings
        """
        if scanners is None:
            scanners = ["vuln", "secret", "config"]
        
        logger.info(f"Scanning repository: {repo_url}")
        
        cmd = [
            "trivy",
            "repo",
            "--format", "json",
            "--severity", self._get_severity_filter(),
            "--scanners", ",".join(scanners),
        ]
        
        if self.skip_db_update:
            cmd.append("--skip-db-update")
        
        cmd.append(repo_url)
        
        return self._run_trivy(cmd, repo_url, TrivyScanType.REPOSITORY)
    
    def generate_sbom(
        self,
        target: str,
        output_format: str = "cyclonedx",
        output_file: Optional[str] = None,
    ) -> str:
        """
        Generate SBOM (Software Bill of Materials) for a target
        
        Args:
            target: Target to scan (image, filesystem path)
            output_format: SBOM format (cyclonedx, spdx, spdx-json)
            output_file: Optional output file path
        
        Returns:
            SBOM content as string
        
        Example:
            >>> scanner = TrivyScanner()
            >>> sbom = scanner.generate_sbom("alpine:3.15", "cyclonedx")
        """
        logger.info(f"Generating SBOM for: {target}")
        
        cmd = [
            "trivy",
            "image" if ":" in target else "fs",
            "--format", output_format,
            target,
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True,
            )
            
            sbom_content = result.stdout
            
            if output_file:
                Path(output_file).write_text(sbom_content)
                logger.info(f"SBOM saved to: {output_file}")
            
            return sbom_content
            
        except subprocess.TimeoutExpired:
            raise TrivyScannerError(f"SBOM generation timed out after {self.timeout}s")
        except subprocess.CalledProcessError as e:
            raise TrivyScannerError(f"SBOM generation failed: {e.stderr}")
    
    def _get_severity_filter(self) -> str:
        """Get severity filter string for Trivy command"""
        severities = []
        min_priority = self.SEVERITY_PRIORITY[self.min_severity]
        
        for severity, priority in self.SEVERITY_PRIORITY.items():
            if priority >= min_priority:
                severities.append(severity.value)
        
        return ",".join(severities)
    
    def _run_trivy(
        self,
        cmd: List[str],
        target: str,
        scan_type: TrivyScanType,
    ) -> "TrivyScanResult":
        """
        Run Trivy command and parse results
        
        Args:
            cmd: Trivy command to execute
            target: Scan target (image name, path, etc.)
            scan_type: Type of scan being performed
        
        Returns:
            TrivyScanResult with parsed findings
        """
        logger.debug(f"Running Trivy command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,  # Don't raise on non-zero exit (Trivy returns 1 if vulns found)
            )
            
            # Trivy returns exit code 1 if vulnerabilities are found
            if result.returncode not in [0, 1]:
                raise TrivyScannerError(
                    f"Trivy scan failed with exit code {result.returncode}: {result.stderr}"
                )
            
            if not result.stdout:
                logger.warning("Trivy returned empty output")
                return TrivyScanResult(
                    target=target,
                    scan_type=scan_type,
                    findings=[],
                    scan_time=datetime.now(),
                )
            
            return self._parse_trivy_output(result.stdout, target, scan_type)
            
        except subprocess.TimeoutExpired:
            raise TrivyScannerError(f"Trivy scan timed out after {self.timeout}s")
        except json.JSONDecodeError as e:
            raise TrivyScannerError(f"Failed to parse Trivy JSON output: {e}")
    
    def _parse_trivy_output(
        self,
        json_output: str,
        target: str,
        scan_type: TrivyScanType,
    ) -> "TrivyScanResult":
        """
        Parse Trivy JSON output into TrivyScanResult
        
        Args:
            json_output: Trivy JSON output
            target: Scan target
            scan_type: Type of scan
        
        Returns:
            TrivyScanResult with parsed findings
        """
        try:
            data = json.loads(json_output)
        except json.JSONDecodeError as e:
            raise TrivyScannerError(f"Invalid JSON from Trivy: {e}")
        
        findings: List[TrivyFinding] = []
        
        # Trivy output structure: {"Results": [...]}
        results = data.get("Results", [])
        
        for result in results:
            target_name = result.get("Target", "")
            result_type = result.get("Type", "")
            
            # Parse vulnerabilities
            vulnerabilities = result.get("Vulnerabilities", [])
            for vuln in vulnerabilities:
                finding = TrivyFinding(
                    vulnerability_id=vuln.get("VulnerabilityID", ""),
                    pkg_name=vuln.get("PkgName", ""),
                    installed_version=vuln.get("InstalledVersion", ""),
                    fixed_version=vuln.get("FixedVersion", ""),
                    severity=TrivySeverity(vuln.get("Severity", "UNKNOWN")),
                    title=vuln.get("Title", ""),
                    description=vuln.get("Description", ""),
                    references=vuln.get("References", []),
                    target=target_name,
                    pkg_type=result_type,
                    cvss_score=self._extract_cvss_score(vuln),
                    cwe_ids=vuln.get("CweIDs", []),
                    published_date=vuln.get("PublishedDate", ""),
                    last_modified_date=vuln.get("LastModifiedDate", ""),
                )
                findings.append(finding)
            
            # Parse misconfigurations
            misconfigs = result.get("Misconfigurations", [])
            for misconfig in misconfigs:
                finding = TrivyFinding(
                    vulnerability_id=misconfig.get("ID", ""),
                    pkg_name="Configuration",
                    installed_version="",
                    fixed_version="",
                    severity=TrivySeverity(misconfig.get("Severity", "UNKNOWN")),
                    title=misconfig.get("Title", ""),
                    description=misconfig.get("Description", ""),
                    references=misconfig.get("References", []),
                    target=target_name,
                    pkg_type="misconfig",
                    resolution=misconfig.get("Resolution", ""),
                )
                findings.append(finding)
            
            # Parse secrets
            secrets = result.get("Secrets", [])
            for secret in secrets:
                finding = TrivyFinding(
                    vulnerability_id=secret.get("RuleID", ""),
                    pkg_name="Secret",
                    installed_version="",
                    fixed_version="",
                    severity=TrivySeverity(secret.get("Severity", "HIGH")),
                    title=secret.get("Title", ""),
                    description=f"Secret found: {secret.get('Match', '')}",
                    references=[],
                    target=target_name,
                    pkg_type="secret",
                    start_line=secret.get("StartLine", 0),
                    end_line=secret.get("EndLine", 0),
                )
                findings.append(finding)
        
        return TrivyScanResult(
            target=target,
            scan_type=scan_type,
            findings=findings,
            scan_time=datetime.now(),
            metadata=data.get("Metadata", {}),
        )
    
    def _extract_cvss_score(self, vuln: Dict[str, Any]) -> Optional[float]:
        """Extract CVSS score from vulnerability data"""
        cvss = vuln.get("CVSS", {})
        
        # Try different CVSS versions
        for version in ["nvd", "redhat", "ghsa"]:
            if version in cvss:
                v3_score = cvss[version].get("V3Score")
                if v3_score:
                    return float(v3_score)
        
        return None
    
    def finding_to_issue(
        self,
        finding: "TrivyFinding",
        project_name: str,
    ) -> IssueData:
        """
        Convert a Trivy finding to a GitLab issue
        
        Args:
            finding: TrivyFinding to convert
            project_name: GitLab project name
        
        Returns:
            IssueData ready for GitLab issue creation
        """
        severity_emoji = self.SEVERITY_EMOJI[finding.severity]
        
        # Build title
        if finding.pkg_type == "secret":
            title = f"{severity_emoji} Secret Detected: {finding.title}"
        elif finding.pkg_type == "misconfig":
            title = f"{severity_emoji} Misconfiguration: {finding.title}"
        else:
            title = f"{severity_emoji} {finding.vulnerability_id}: {finding.pkg_name}"
        
        # Build description
        description_parts = [
            f"**Severity:** {finding.severity.value}",
            f"**Target:** `{finding.target}`",
        ]
        
        if finding.pkg_type == "secret":
            description_parts.extend([
                f"**Type:** Secret Detection",
                f"**Rule:** {finding.vulnerability_id}",
                f"**Location:** Lines {finding.start_line}-{finding.end_line}",
                "",
                "### Description",
                finding.description,
                "",
                "### Remediation",
                "1. Remove the secret from the code",
                "2. Rotate the compromised credential",
                "3. Use environment variables or secret management tools",
            ])
        elif finding.pkg_type == "misconfig":
            description_parts.extend([
                f"**Type:** Misconfiguration",
                f"**Check ID:** {finding.vulnerability_id}",
                "",
                "### Description",
                finding.description,
            ])
            if finding.resolution:
                description_parts.extend([
                    "",
                    "### Resolution",
                    finding.resolution,
                ])
        else:
            description_parts.extend([
                f"**Package:** {finding.pkg_name}",
                f"**Installed Version:** {finding.installed_version}",
            ])
            
            if finding.fixed_version:
                description_parts.append(f"**Fixed Version:** {finding.fixed_version}")
            else:
                description_parts.append("**Fixed Version:** Not available")
            
            if finding.cvss_score:
                description_parts.append(f"**CVSS Score:** {finding.cvss_score}")
            
            description_parts.extend([
                "",
                "### Description",
                finding.description or "No description available",
            ])
            
            if finding.cwe_ids:
                cwe_links = [
                    f"[CWE-{cwe}](https://cwe.mitre.org/data/definitions/{cwe}.html)"
                    for cwe in finding.cwe_ids
                ]
                description_parts.extend([
                    "",
                    "### CWE",
                    ", ".join(cwe_links),
                ])
            
            if finding.references:
                description_parts.extend([
                    "",
                    "### References",
                    *[f"- {ref}" for ref in finding.references[:5]],
                ])
        
        description = "\n".join(description_parts)
        
        # Determine labels
        labels = [
            "security",
            "trivy",
            f"severity::{finding.severity.value.lower()}",
        ]
        
        if finding.pkg_type == "secret":
            labels.append("secret-detection")
        elif finding.pkg_type == "misconfig":
            labels.append("misconfiguration")
        else:
            labels.append("vulnerability")
        
        return IssueData(
            title=title,
            description=description,
            labels=labels,
            confidential=True,
        )
    
    def scan_result_to_issues(
        self,
        scan_result: "TrivyScanResult",
        project_name: str,
        group_by_severity: bool = False,
    ) -> List[IssueData]:
        """
        Convert scan results to GitLab issues
        
        Args:
            scan_result: TrivyScanResult to convert
            project_name: GitLab project name
            group_by_severity: Group findings by severity (default: False)
        
        Returns:
            List of IssueData objects
        """
        if not group_by_severity:
            # Create individual issues
            return [
                self.finding_to_issue(finding, project_name)
                for finding in scan_result.findings
            ]
        
        # Group by severity
        issues = []
        by_severity: Dict[TrivySeverity, List[TrivyFinding]] = {}
        
        for finding in scan_result.findings:
            if finding.severity not in by_severity:
                by_severity[finding.severity] = []
            by_severity[finding.severity].append(finding)
        
        for severity, findings in sorted(
            by_severity.items(),
            key=lambda x: self.SEVERITY_PRIORITY[x[0]],
            reverse=True,
        ):
            issue = self._create_grouped_issue(
                severity, findings, scan_result.target, project_name
            )
            issues.append(issue)
        
        return issues
    
    def _create_grouped_issue(
        self,
        severity: TrivySeverity,
        findings: List["TrivyFinding"],
        target: str,
        project_name: str,
    ) -> IssueData:
        """Create a grouped issue for findings of the same severity"""
        severity_emoji = self.SEVERITY_EMOJI[severity]
        
        title = (
            f"{severity_emoji} {severity.value} Security Issues in {target} "
            f"({len(findings)} findings)"
        )
        
        description_parts = [
            f"**Severity:** {severity.value}",
            f"**Target:** `{target}`",
            f"**Total Findings:** {len(findings)}",
            "",
            "## Findings",
            "",
        ]
        
        for i, finding in enumerate(findings, 1):
            description_parts.extend([
                f"### {i}. {finding.vulnerability_id or finding.title}",
                f"- **Package:** {finding.pkg_name}",
            ])
            
            if finding.installed_version:
                description_parts.append(f"- **Installed:** {finding.installed_version}")
            if finding.fixed_version:
                description_parts.append(f"- **Fixed:** {finding.fixed_version}")
            
            description_parts.extend([
                f"- **Description:** {finding.description[:200]}...",
                "",
            ])
        
        description = "\n".join(description_parts)
        
        return IssueData(
            title=title,
            description=description,
            labels=[
                "security",
                "trivy",
                f"severity::{severity.value.lower()}",
                "grouped",
            ],
            confidential=True,
        )


@dataclass
class TrivyFinding:
    """Represents a single Trivy finding (vulnerability, misconfiguration, or secret)"""
    
    vulnerability_id: str
    pkg_name: str
    installed_version: str
    fixed_version: str
    severity: TrivySeverity
    title: str
    description: str
    references: List[str]
    target: str
    pkg_type: str
    cvss_score: Optional[float] = None
    cwe_ids: List[str] = field(default_factory=list)
    published_date: str = ""
    last_modified_date: str = ""
    resolution: str = ""
    start_line: int = 0
    end_line: int = 0
    
    @property
    def severity_emoji(self) -> str:
        """Get emoji for severity level"""
        return TrivyScanner.SEVERITY_EMOJI[self.severity]
    
    @property
    def is_fixable(self) -> bool:
        """Check if vulnerability has a fix available"""
        return bool(self.fixed_version)
    
    @property
    def is_critical_or_high(self) -> bool:
        """Check if severity is CRITICAL or HIGH"""
        return self.severity in [TrivySeverity.CRITICAL, TrivySeverity.HIGH]


@dataclass
class TrivyScanResult:
    """Results from a Trivy scan"""
    
    target: str
    scan_type: TrivyScanType
    findings: List[TrivyFinding]
    scan_time: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def vulnerability_count(self) -> int:
        """Total number of vulnerabilities found"""
        return len([f for f in self.findings if f.pkg_type not in ["secret", "misconfig"]])
    
    @property
    def secret_count(self) -> int:
        """Total number of secrets found"""
        return len([f for f in self.findings if f.pkg_type == "secret"])
    
    @property
    def misconfig_count(self) -> int:
        """Total number of misconfigurations found"""
        return len([f for f in self.findings if f.pkg_type == "misconfig"])
    
    @property
    def critical_count(self) -> int:
        """Number of CRITICAL findings"""
        return len([f for f in self.findings if f.severity == TrivySeverity.CRITICAL])
    
    @property
    def high_count(self) -> int:
        """Number of HIGH findings"""
        return len([f for f in self.findings if f.severity == TrivySeverity.HIGH])
    
    @property
    def medium_count(self) -> int:
        """Number of MEDIUM findings"""
        return len([f for f in self.findings if f.severity == TrivySeverity.MEDIUM])
    
    @property
    def low_count(self) -> int:
        """Number of LOW findings"""
        return len([f for f in self.findings if f.severity == TrivySeverity.LOW])
    
    @property
    def has_findings(self) -> bool:
        """Check if any findings were detected"""
        return len(self.findings) > 0
    
    @property
    def fixable_count(self) -> int:
        """Number of findings with available fixes"""
        return len([f for f in self.findings if f.is_fixable])
    
    @property
    def packages(self) -> Set[str]:
        """Set of unique package names with findings"""
        return {f.pkg_name for f in self.findings if f.pkg_type not in ["secret", "misconfig"]}


class TrivyScannerError(Exception):
    """Base exception for Trivy scanner errors"""
    pass


class TrivyNotInstalledError(TrivyScannerError):
    """Raised when Trivy is not installed"""
    pass
