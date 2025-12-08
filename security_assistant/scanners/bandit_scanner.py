"""
Bandit Security Scanner Integration
Scans Python code for security vulnerabilities using Bandit.
Converts findings to GitLab issue format.

Checked: bandit@1.7.5+ (Nov 2025) - stable, no critical CVEs
Alternative: ruff (10-100x faster, includes all Bandit rules)
"""

import os
import json
import logging
import subprocess  # For executing bandit CLI
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime

from ..gitlab_api import IssueData


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BanditFinding:
    """Represents a single Bandit security finding."""
    test_id: str
    test_name: str
    severity: str  # HIGH, MEDIUM, LOW
    confidence: str  # HIGH, MEDIUM, LOW
    issue_text: str
    filename: str
    line_number: int
    code: str
    cwe_id: Optional[str] = None
    more_info: Optional[str] = None
    
    @property
    def severity_emoji(self) -> str:
        """Get emoji for severity level."""
        return {
            "HIGH": "🔴",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }.get(self.severity, "⚪")
    
    @property
    def confidence_emoji(self) -> str:
        """Get emoji for confidence level."""
        return {
            "HIGH": "✅",
            "MEDIUM": "⚠️",
            "LOW": "ℹ️"
        }.get(self.confidence, "❓")


@dataclass
class ScanResult:
    """Results from a Bandit scan."""
    findings: List[BanditFinding] = field(default_factory=list)
    scan_time: datetime = field(default_factory=datetime.now)
    files_scanned: int = 0
    lines_scanned: int = 0
    errors: List[str] = field(default_factory=list)
    
    @property
    def high_severity_count(self) -> int:
        """Count of high severity findings."""
        return sum(1 for f in self.findings if f.severity == "HIGH")
    
    @property
    def medium_severity_count(self) -> int:
        """Count of medium severity findings."""
        return sum(1 for f in self.findings if f.severity == "MEDIUM")
    
    @property
    def low_severity_count(self) -> int:
        """Count of low severity findings."""
        return sum(1 for f in self.findings if f.severity == "LOW")
    
    @property
    def has_findings(self) -> bool:
        """Check if scan found any issues."""
        return len(self.findings) > 0


class BanditScannerError(Exception):
    """Base exception for Bandit scanner errors."""
    pass


class BanditNotInstalledError(BanditScannerError):
    """Bandit is not installed."""
    pass


class BanditScanner:
    """
    Bandit security scanner integration.
    
    Features:
    - Scan individual files or directories
    - Parse Bandit JSON output
    - Convert findings to GitLab issues
    - Filter by severity and confidence
    """
    
    def __init__(
        self,
        min_severity: str = "LOW",
        min_confidence: str = "LOW",
        exclude_dirs: Optional[List[str]] = None
    ):
        """
        Initialize Bandit scanner.
        
        Args:
            min_severity: Minimum severity to report (LOW, MEDIUM, HIGH)
            min_confidence: Minimum confidence to report (LOW, MEDIUM, HIGH)
            exclude_dirs: Directories to exclude from scanning
        """
        self.min_severity = min_severity
        self.min_confidence = min_confidence
        self.exclude_dirs = exclude_dirs or [
            "venv", ".venv", "env", ".env",
            "node_modules", ".git", "__pycache__",
            "build", "dist", ".tox"
        ]
        
        # Verify Bandit is installed
        if not self._check_bandit_installed():
            raise BanditNotInstalledError(
                "Bandit is not installed. Install with: pip install bandit"
            )
        
        logger.info(f"Bandit scanner initialized (min_severity={min_severity}, min_confidence={min_confidence})")
    
    def _check_bandit_installed(self) -> bool:
        """Check if Bandit is installed."""
        try:
            result = subprocess.run(
                ["bandit", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def scan_file(self, file_path: str) -> ScanResult:
        """
        Scan a single Python file.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            ScanResult with findings
            
        Raises:
            BanditScannerError: On scan errors
            
        Example:
            >>> scanner = BanditScanner(min_severity="MEDIUM")
            >>> result = scanner.scan_file("app.py")
            >>> print(f"Found {len(result.findings)} issues")
        """
        if not os.path.exists(file_path):
            raise BanditScannerError(f"File not found: {file_path}")
        
        if not file_path.endswith('.py'):
            raise BanditScannerError(f"Not a Python file: {file_path}")
        
        logger.info(f"Scanning file: {file_path}")
        
        return self._run_bandit([file_path])
    
    def scan_directory(self, directory_path: str, recursive: bool = True) -> ScanResult:
        """
        Scan a directory for Python files.
        
        Args:
            directory_path: Path to directory
            recursive: Scan subdirectories
            
        Returns:
            ScanResult with findings
            
        Raises:
            BanditScannerError: On scan errors
            
        Example:
            >>> scanner = BanditScanner()
            >>> result = scanner.scan_directory("src/", recursive=True)
            >>> print(f"Scanned {result.files_scanned} files")
        """
        if not os.path.exists(directory_path):
            raise BanditScannerError(f"Directory not found: {directory_path}")
        
        if not os.path.isdir(directory_path):
            raise BanditScannerError(f"Not a directory: {directory_path}")
        
        logger.info(f"Scanning directory: {directory_path} (recursive={recursive})")
        
        args = [directory_path]
        if recursive:
            args.append("-r")
        
        return self._run_bandit(args)
    
    def _run_bandit(self, targets: List[str]) -> ScanResult:
        """
        Run Bandit scanner on targets.
        
        Args:
            targets: List of files/directories to scan
            
        Returns:
            ScanResult with findings
        """
        # Build Bandit command
        cmd = [
            "bandit",
            "-f", "json",  # JSON output
            "-ll",  # Show only issues with severity >= LOW
        ]
        
        # Add exclusions
        if self.exclude_dirs:
            for exclude in self.exclude_dirs:
                cmd.extend(["-x", exclude])
        
        # Add targets
        cmd.extend(targets)
        
        logger.debug(f"Running command: {' '.join(cmd)}")
        
        try:
            # Run Bandit
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Bandit returns exit code 1 if issues found, which is expected
            if result.returncode not in [0, 1]:
                raise BanditScannerError(f"Bandit failed with exit code {result.returncode}: {result.stderr}")
            
            # Parse JSON output
            return self._parse_bandit_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            raise BanditScannerError("Bandit scan timeout (>5 minutes)")
        except subprocess.SubprocessError as e:
            raise BanditScannerError(f"Failed to run Bandit: {str(e)}")
    
    def _parse_bandit_output(self, json_output: str) -> ScanResult:
        """
        Parse Bandit JSON output.
        
        Args:
            json_output: Bandit JSON output string
            
        Returns:
            ScanResult with parsed findings
        """
        try:
            data = json.loads(json_output)
        except json.JSONDecodeError as e:
            raise BanditScannerError(f"Failed to parse Bandit output: {str(e)}")
        
        scan_result = ScanResult()
        
        # Extract metrics
        metrics = data.get("metrics", {})
        total_metrics = metrics.get("_totals", {})
        scan_result.files_scanned = total_metrics.get("loc", 0)
        scan_result.lines_scanned = total_metrics.get("nosec", 0)
        
        # Extract findings
        results = data.get("results", [])
        
        for item in results:
            finding = BanditFinding(
                test_id=item.get("test_id", ""),
                test_name=item.get("test_name", ""),
                severity=item.get("issue_severity", "LOW"),
                confidence=item.get("issue_confidence", "LOW"),
                issue_text=item.get("issue_text", ""),
                filename=item.get("filename", ""),
                line_number=item.get("line_number", 0),
                code=item.get("code", "").strip(),
                cwe_id=item.get("issue_cwe", {}).get("id") if item.get("issue_cwe") else None,
                more_info=item.get("more_info", "")
            )
            
            # Filter by severity and confidence
            if self._should_include_finding(finding):
                scan_result.findings.append(finding)
        
        # Extract errors
        errors = data.get("errors", [])
        scan_result.errors = errors
        
        logger.info(
            f"Scan complete: {len(scan_result.findings)} findings "
            f"({scan_result.high_severity_count} high, "
            f"{scan_result.medium_severity_count} medium, "
            f"{scan_result.low_severity_count} low)"
        )
        
        return scan_result
    
    def _should_include_finding(self, finding: BanditFinding) -> bool:
        """
        Check if finding meets minimum severity and confidence.
        
        Args:
            finding: BanditFinding to check
            
        Returns:
            True if finding should be included
        """
        severity_levels = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
        confidence_levels = {"LOW": 1, "MEDIUM": 2, "HIGH": 3}
        
        min_sev_level = severity_levels.get(self.min_severity, 1)
        min_conf_level = confidence_levels.get(self.min_confidence, 1)
        
        finding_sev_level = severity_levels.get(finding.severity, 1)
        finding_conf_level = confidence_levels.get(finding.confidence, 1)
        
        return (finding_sev_level >= min_sev_level and 
                finding_conf_level >= min_conf_level)
    
    def finding_to_issue(
        self,
        finding: BanditFinding,
        project_name: str = "Unknown Project"
    ) -> IssueData:
        """
        Convert Bandit finding to GitLab issue.
        
        Args:
            finding: BanditFinding to convert
            project_name: Name of the project
            
        Returns:
            IssueData ready for GitLab API
            
        Example:
            >>> scanner = BanditScanner()
            >>> result = scanner.scan_file("app.py")
            >>> for finding in result.findings:
            ...     issue = scanner.finding_to_issue(finding, "MyApp")
            ...     # Create issue in GitLab
        """
        # Build title
        title = f"Security: {finding.test_name} in {Path(finding.filename).name}"
        
        # Build description
        description_parts = [
            f"## {finding.severity_emoji} Security Finding: {finding.test_name}",
            "",
            f"**Severity:** {finding.severity}",
            f"**Confidence:** {finding.confidence} {finding.confidence_emoji}",
            f"**Test ID:** {finding.test_id}",
            "",
            "### Issue Description",
            finding.issue_text,
            "",
            "### Location",
            f"**File:** `{finding.filename}`",
            f"**Line:** {finding.line_number}",
            "",
            "### Code",
            "```python",
            finding.code,
            "```",
        ]
        
        # Add CWE if available
        if finding.cwe_id:
            description_parts.extend([
                "",
                f"**CWE:** [{finding.cwe_id}](https://cwe.mitre.org/data/definitions/{finding.cwe_id}.html)"
            ])
        
        # Add more info link
        if finding.more_info:
            description_parts.extend([
                "",
                f"**More Info:** {finding.more_info}"
            ])
        
        # Add footer
        description_parts.extend([
            "",
            "---",
            f"*Detected by Bandit scanner on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])
        
        description = "\n".join(description_parts)
        
        # Determine labels
        labels = ["security", "bandit"]
        
        # Add severity label
        if finding.severity == "HIGH":
            labels.append("critical")
        elif finding.severity == "MEDIUM":
            labels.append("high-priority")
        
        # Add test-specific label
        labels.append(finding.test_id.lower())
        
        return IssueData(
            title=title,
            description=description,
            labels=labels,
            confidential=True  # Security issues should be confidential
        )
    
    def scan_result_to_issues(
        self,
        scan_result: ScanResult,
        project_name: str = "Unknown Project",
        group_by_file: bool = False
    ) -> List[IssueData]:
        """
        Convert scan results to GitLab issues.
        
        Args:
            scan_result: ScanResult to convert
            project_name: Name of the project
            group_by_file: Group findings by file (one issue per file)
            
        Returns:
            List of IssueData ready for GitLab API
            
        Example:
            >>> scanner = BanditScanner()
            >>> result = scanner.scan_directory("src/")
            >>> issues = scanner.scan_result_to_issues(result, "MyApp")
            >>> print(f"Created {len(issues)} issues")
        """
        if not group_by_file:
            # One issue per finding
            return [
                self.finding_to_issue(finding, project_name)
                for finding in scan_result.findings
            ]
        
        # Group findings by file
        findings_by_file: Dict[str, List[BanditFinding]] = {}
        for finding in scan_result.findings:
            if finding.filename not in findings_by_file:
                findings_by_file[finding.filename] = []
            findings_by_file[finding.filename].append(finding)
        
        # Create one issue per file
        issues = []
        for filename, findings in findings_by_file.items():
            issue = self._create_grouped_issue(filename, findings, project_name)
            issues.append(issue)
        
        return issues
    
    def _create_grouped_issue(
        self,
        filename: str,
        findings: List[BanditFinding],
        project_name: str
    ) -> IssueData:
        """Create a single issue for multiple findings in a file."""
        # Count by severity
        high_count = sum(1 for f in findings if f.severity == "HIGH")
        medium_count = sum(1 for f in findings if f.severity == "MEDIUM")
        low_count = sum(1 for f in findings if f.severity == "LOW")
        
        # Build title
        title = f"Security: {len(findings)} issues in {Path(filename).name}"
        
        # Build description
        description_parts = [
            f"## 🔒 Security Issues Found in {Path(filename).name}",
            "",
            f"**Total Issues:** {len(findings)}",
            f"- 🔴 High: {high_count}",
            f"- 🟡 Medium: {medium_count}",
            f"- 🟢 Low: {low_count}",
            "",
            "---",
            ""
        ]
        
        # Add each finding
        for i, finding in enumerate(findings, 1):
            description_parts.extend([
                f"### {i}. {finding.severity_emoji} {finding.test_name}",
                "",
                f"**Severity:** {finding.severity} | **Confidence:** {finding.confidence}",
                f"**Line:** {finding.line_number}",
                "",
                finding.issue_text,
                "",
                "```python",
                finding.code,
                "```",
                ""
            ])
            
            if finding.more_info:
                description_parts.append(f"[More Info]({finding.more_info})")
                description_parts.append("")
        
        # Add footer
        description_parts.extend([
            "---",
            f"*Detected by Bandit scanner on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
        ])
        
        description = "\n".join(description_parts)
        
        # Determine labels
        labels = ["security", "bandit", "multiple-issues"]
        if high_count > 0:
            labels.append("critical")
        elif medium_count > 0:
            labels.append("high-priority")
        
        return IssueData(
            title=title,
            description=description,
            labels=labels,
            confidential=True
        )
