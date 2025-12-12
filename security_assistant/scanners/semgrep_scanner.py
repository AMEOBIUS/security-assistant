"""
Semgrep Security Scanner Integration
Scans code for security vulnerabilities using Semgrep.
Supports multiple languages: Python, JavaScript, Go, Java, Ruby, PHP, and more.
Converts findings to GitLab issue format.

Checked: semgrep@1.144.0 (Nov 2025) - latest stable
Features: 3x faster multicore, native Windows support, Python 3.14 compatible

Refactored: Session 47 - Now extends BaseScanner
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from ..gitlab_api import IssueData
from .base_scanner import BaseScanner, ScannerConfig, ScannerNotInstalledError

logger = logging.getLogger(__name__)


@dataclass
class SemgrepFinding:
    """Represents a single Semgrep security finding."""

    check_id: str  # e.g., "python.lang.security.audit.dangerous-system-call"
    message: str
    severity: str  # ERROR, WARNING, INFO
    path: str
    start_line: int
    end_line: int
    start_col: int
    end_col: int
    code: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def severity_emoji(self) -> str:
        """Get emoji for severity level."""
        return {"ERROR": "🔴", "WARNING": "🟡", "INFO": "🟢"}.get(self.severity, "⚪")

    @property
    def language(self) -> str:
        """Extract language from check_id."""
        parts = self.check_id.split(".")
        return parts[0] if parts else "unknown"

    @property
    def category(self) -> str:
        """Extract category from metadata or check_id."""
        # Try metadata first
        if "category" in self.metadata:
            return self.metadata["category"]

        # Parse from check_id (e.g., python.lang.security.audit.xxx)
        parts = self.check_id.split(".")
        if len(parts) >= 3:
            return parts[2]  # "security"
        return "unknown"

    @property
    def cwe_ids(self) -> List[str]:
        """Extract CWE IDs from metadata."""
        cwe = self.metadata.get("cwe", [])
        if isinstance(cwe, list):
            return cwe
        elif isinstance(cwe, str):
            return [cwe]
        return []

    @property
    def owasp_categories(self) -> List[str]:
        """Extract OWASP categories from metadata."""
        owasp = self.metadata.get("owasp", [])
        if isinstance(owasp, list):
            return owasp
        elif isinstance(owasp, str):
            return [owasp]
        return []


@dataclass
class SemgrepScanResult:
    """Results from a Semgrep scan."""

    findings: List[SemgrepFinding] = field(default_factory=list)
    scan_time: datetime = field(default_factory=datetime.now)
    files_scanned: int = 0
    rules_used: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        """Count of ERROR severity findings."""
        return sum(1 for f in self.findings if f.severity == "ERROR")

    @property
    def warning_count(self) -> int:
        """Count of WARNING severity findings."""
        return sum(1 for f in self.findings if f.severity == "WARNING")

    @property
    def info_count(self) -> int:
        """Count of INFO severity findings."""
        return sum(1 for f in self.findings if f.severity == "INFO")

    @property
    def has_findings(self) -> bool:
        """Check if scan found any issues."""
        return len(self.findings) > 0

    @property
    def languages(self) -> Set[str]:
        """Get set of languages found in scan."""
        return {f.language for f in self.findings}


class SemgrepScannerError(Exception):
    """Base exception for Semgrep scanner errors."""

    pass


class SemgrepNotInstalledError(ScannerNotInstalledError):
    """Semgrep is not installed."""

    pass


class SemgrepScanner(BaseScanner[SemgrepFinding, SemgrepScanResult]):
    """
    Semgrep security scanner integration.

    Features:
    - Multi-language support (Python, JS, Go, Java, Ruby, PHP, etc.)
    - Scan individual files or directories
    - Parse Semgrep JSON output
    - Convert findings to GitLab issues
    - Filter by severity
    - Custom rules support

    Supported Languages:
    - Python, JavaScript/TypeScript, Go, Java, Ruby, PHP
    - C, C++, C#, Kotlin, Scala, Rust
    - Bash, YAML, JSON, Dockerfile, Terraform

    Extends BaseScanner for common functionality.
    """

    # Semgrep severity mapping to our levels
    SEVERITY_MAP = {"ERROR": "HIGH", "WARNING": "MEDIUM", "INFO": "LOW"}

    # Semgrep uses different severity names
    SEVERITY_LEVELS = {"INFO": 1, "WARNING": 2, "ERROR": 3}

    def __init__(
        self,
        min_severity: str = "INFO",
        config: str = "p/security-audit",
        exclude_dirs: Optional[List[str]] = None,
        custom_rules: Optional[List[str]] = None,
        scanner_config: Optional[ScannerConfig] = None,
        **kwargs,
    ):
        """
        Initialize Semgrep scanner.

        Args:
            min_severity: Minimum severity to report (INFO, WARNING, ERROR)
            config: Semgrep config/ruleset to use:
                - "auto" (default): Auto-detect based on languages
                - "p/security-audit": Security-focused rules
                - "p/owasp-top-ten": OWASP Top 10
                - "p/ci": Fast CI-optimized rules
                - Path to custom rules file/directory
            exclude_dirs: Directories to exclude from scanning
            custom_rules: Additional custom rule files/URLs
            scanner_config: Base scanner configuration (optional)
        """
        self.semgrep_config = config
        self.custom_rules = custom_rules or []

        # Build base config
        if scanner_config is None:
            scanner_config = ScannerConfig(
                min_severity=min_severity,
                timeout=600,  # 10 minute timeout for Semgrep
                exclude_dirs=exclude_dirs
                or [
                    "venv",
                    ".venv",
                    "env",
                    ".env",
                    "node_modules",
                    ".git",
                    "__pycache__",
                    "build",
                    "dist",
                    ".tox",
                    "vendor",
                    ".pytest_cache",
                    ".mypy_cache",
                ],
            )

        # Call parent constructor
        super().__init__(config=scanner_config, **kwargs)

        logger.info(f"Semgrep scanner initialized (config={config})")

    @property
    def name(self) -> str:
        return "semgrep"

    @property
    def command(self) -> str:
        return "semgrep"

    def _get_not_installed_error(self) -> SemgrepNotInstalledError:
        return SemgrepNotInstalledError(
            "Semgrep is not installed. Install with: pip install semgrep"
        )

    def _build_command(self, targets: List[str], **kwargs) -> List[str]:
        """Build Semgrep command with arguments."""
        cmd = [
            "semgrep",
            "--json",
            "--config",
            self.semgrep_config,
            "--metrics",
            "off",
        ]

        # Add custom rules
        for rule in self.custom_rules:
            cmd.extend(["--config", rule])

        # Add exclusions
        for exclude in self.config.exclude_dirs:
            cmd.extend(["--exclude", exclude])

        cmd.extend(targets)
        return cmd

    def _parse_output(self, raw: str) -> SemgrepScanResult:
        """Parse Semgrep JSON output."""
        return self._parse_semgrep_output(raw)

    def _parse_semgrep_output(self, json_output: str) -> SemgrepScanResult:
        """
        Parse Semgrep JSON output.

        Args:
            json_output: Semgrep JSON output string

        Returns:
            SemgrepScanResult with parsed findings
        """
        try:
            data = json.loads(json_output)
        except json.JSONDecodeError as e:
            raise SemgrepScannerError(f"Failed to parse Semgrep output: {str(e)}")

        scan_result = SemgrepScanResult()

        # Extract findings
        results = data.get("results", [])

        for item in results:
            # Extract code snippet
            extra = item.get("extra", {})
            code_lines = extra.get("lines", "").strip()

            # Extract metadata
            metadata = extra.get("metadata", {})

            finding = SemgrepFinding(
                check_id=item.get("check_id", ""),
                message=extra.get("message", ""),
                severity=extra.get("severity", "INFO").upper(),
                path=item.get("path", ""),
                start_line=item.get("start", {}).get("line", 0),
                end_line=item.get("end", {}).get("line", 0),
                start_col=item.get("start", {}).get("col", 0),
                end_col=item.get("end", {}).get("col", 0),
                code=code_lines,
                metadata=metadata,
            )

            # Filter by severity
            if self._should_include_finding(finding):
                scan_result.findings.append(finding)

        # Extract errors
        errors = data.get("errors", [])
        for error in errors:
            error_msg = error.get("message", str(error))
            scan_result.errors.append(error_msg)

        # Extract paths (files scanned)
        paths = data.get("paths", {})
        scanned = paths.get("scanned", [])
        scan_result.files_scanned = len(scanned)

        logger.info(
            f"Scan complete: {len(scan_result.findings)} findings "
            f"({scan_result.error_count} errors, "
            f"{scan_result.warning_count} warnings, "
            f"{scan_result.info_count} info)"
        )

        return scan_result

    def _should_include_finding(self, finding: SemgrepFinding) -> bool:
        """
        Check if finding meets minimum severity.

        Args:
            finding: SemgrepFinding to check

        Returns:
            True if finding should be included
        """
        min_level = self.SEVERITY_LEVELS.get(self.config.min_severity.upper(), 1)
        finding_level = self.SEVERITY_LEVELS.get(finding.severity, 1)
        return finding_level >= min_level

    def _get_findings_from_result(
        self, result: SemgrepScanResult
    ) -> List[SemgrepFinding]:
        """Extract findings list from scan result."""
        return result.findings

    def _get_finding_file(self, finding: SemgrepFinding) -> str:
        """Get file path from finding."""
        return finding.path

    def finding_to_issue(
        self, finding: SemgrepFinding, project_name: str = "Unknown Project"
    ) -> IssueData:
        """
        Convert Semgrep finding to GitLab issue.

        Args:
            finding: SemgrepFinding to convert
            project_name: Name of the project

        Returns:
            IssueData ready for GitLab API

        Example:
            >>> scanner = SemgrepScanner()
            >>> result = scanner.scan_file("app.js")
            >>> for finding in result.findings:
            ...     issue = scanner.finding_to_issue(finding, "MyApp")
            ...     # Create issue in GitLab
        """
        # Build title
        file_name = Path(finding.path).name
        title = f"Security: {finding.check_id.split('.')[-1]} in {file_name}"

        # Build description
        description_parts = [
            f"## {finding.severity_emoji} Security Finding: {finding.check_id}",
            "",
            f"**Severity:** {self.SEVERITY_MAP.get(finding.severity, finding.severity)}",
            f"**Language:** {finding.language.upper()}",
            f"**Category:** {finding.category}",
            "",
            "### Issue Description",
            finding.message,
            "",
            "### Location",
            f"**File:** `{finding.path}`",
            f"**Lines:** {finding.start_line}-{finding.end_line}",
            "",
            "### Code",
            f"```{finding.language}",
            finding.code,
            "```",
        ]

        # Add CWE if available
        if finding.cwe_ids:
            cwe_links = [
                f"[{cwe}](https://cwe.mitre.org/data/definitions/{cwe.replace('CWE-', '')}.html)"
                for cwe in finding.cwe_ids
            ]
            description_parts.extend(["", f"**CWE:** {', '.join(cwe_links)}"])

        # Add OWASP if available
        if finding.owasp_categories:
            description_parts.extend(
                ["", f"**OWASP:** {', '.join(finding.owasp_categories)}"]
            )

        # Add references from metadata
        references = finding.metadata.get("references", [])
        if references:
            description_parts.extend(["", "### References"])
            for ref in references:
                description_parts.append(f"- {ref}")

        # Add fix guidance if available
        fix = finding.metadata.get("fix", "")
        if fix:
            description_parts.extend(["", "### Recommended Fix", fix])

        # Add footer
        description_parts.extend(
            [
                "",
                "---",
                f"*Detected by Semgrep scanner on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
                f"*Rule: `{finding.check_id}`*",
            ]
        )

        description = "\n".join(description_parts)

        # Determine labels
        labels = ["security", "semgrep", finding.language]

        # Add severity label
        if finding.severity == "ERROR":
            labels.append("critical")
        elif finding.severity == "WARNING":
            labels.append("high-priority")

        # Add category label
        if finding.category != "unknown":
            labels.append(finding.category)

        # Add OWASP labels
        for owasp in finding.owasp_categories:
            labels.append(f"owasp-{owasp.lower().replace(' ', '-')}")

        return IssueData(
            title=title,
            description=description,
            labels=labels,
            confidential=True,  # Security issues should be confidential
        )

    def scan_result_to_issues(
        self,
        scan_result: SemgrepScanResult,
        project_name: str = "Unknown Project",
        group_by_file: bool = False,
    ) -> List[IssueData]:
        """
        Convert scan results to GitLab issues.

        Args:
            scan_result: SemgrepScanResult to convert
            project_name: Name of the project
            group_by_file: Group findings by file (one issue per file)

        Returns:
            List of IssueData ready for GitLab API

        Example:
            >>> scanner = SemgrepScanner()
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
        findings_by_file: Dict[str, List[SemgrepFinding]] = {}
        for finding in scan_result.findings:
            if finding.path not in findings_by_file:
                findings_by_file[finding.path] = []
            findings_by_file[finding.path].append(finding)

        # Create one issue per file
        issues = []
        for filepath, findings in findings_by_file.items():
            issue = self._create_grouped_issue(filepath, findings, project_name)
            issues.append(issue)

        return issues

    def _create_grouped_issue(
        self, filepath: str, findings: List[SemgrepFinding], project_name: str
    ) -> IssueData:
        """Create a single issue for multiple findings in a file."""
        # Count by severity
        error_count = sum(1 for f in findings if f.severity == "ERROR")
        warning_count = sum(1 for f in findings if f.severity == "WARNING")
        info_count = sum(1 for f in findings if f.severity == "INFO")

        # Get language
        language = findings[0].language if findings else "unknown"

        # Build title
        file_name = Path(filepath).name
        title = f"Security: {len(findings)} issues in {file_name}"

        # Build description
        description_parts = [
            f"## 🔒 Security Issues Found in {file_name}",
            "",
            f"**Language:** {language.upper()}",
            f"**Total Issues:** {len(findings)}",
            f"- 🔴 Errors: {error_count}",
            f"- 🟡 Warnings: {warning_count}",
            f"- 🟢 Info: {info_count}",
            "",
            "---",
            "",
        ]

        # Add each finding
        for i, finding in enumerate(findings, 1):
            description_parts.extend(
                [
                    f"### {i}. {finding.severity_emoji} {finding.check_id.split('.')[-1]}",
                    "",
                    f"**Severity:** {self.SEVERITY_MAP.get(finding.severity, finding.severity)}",
                    f"**Lines:** {finding.start_line}-{finding.end_line}",
                    "",
                    finding.message,
                    "",
                    f"```{language}",
                    finding.code,
                    "```",
                    "",
                ]
            )

            # Add CWE if available
            if finding.cwe_ids:
                description_parts.append(f"**CWE:** {', '.join(finding.cwe_ids)}")
                description_parts.append("")

        # Add footer
        description_parts.extend(
            [
                "---",
                f"*Detected by Semgrep scanner on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            ]
        )

        description = "\n".join(description_parts)

        # Determine labels
        labels = ["security", "semgrep", language, "multiple-issues"]
        if error_count > 0:
            labels.append("critical")
        elif warning_count > 0:
            labels.append("high-priority")

        return IssueData(
            title=title, description=description, labels=labels, confidential=True
        )
