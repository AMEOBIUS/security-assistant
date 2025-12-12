"""
Base Scanner Abstract Class

Provides common functionality for all security scanners:
- Installation verification
- Subprocess execution with timeout
- Error handling
- Common scan workflow

All scanners (Bandit, Semgrep, Trivy) extend this base class.

Version: 1.0.0
"""

import logging
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Generic, List, Optional, TypeVar

from ..common.executor import CommandExecutionError, CommandExecutor
from ..gitlab_api import IssueData

logger = logging.getLogger(__name__)


@dataclass
class ScannerConfig:
    """Configuration for scanner initialization."""

    min_severity: str = "LOW"
    timeout: int = 300
    extra_args: List[str] = field(default_factory=list)
    exclude_dirs: List[str] = field(
        default_factory=lambda: [
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
        ]
    )


class ScannerError(Exception):
    """Base exception for scanner errors."""

    pass


class ScannerNotInstalledError(ScannerError):
    """Scanner tool is not installed."""

    pass


# Generic type for finding
F = TypeVar("F")
# Generic type for scan result
R = TypeVar("R")


class BaseScanner(ABC, Generic[F, R]):
    """
    Abstract base class for security scanners.

    Provides common functionality:
    - Installation check
    - Subprocess execution with timeout
    - Error handling
    - Logging

    Subclasses must implement:
    - name: Scanner name
    - command: CLI command
    - _build_command(): Build command arguments
    - _parse_output(): Parse JSON output
    - _get_not_installed_error(): Return appropriate exception

    Example:
        class MyScanner(BaseScanner):
            @property
            def name(self) -> str:
                return "my-scanner"

            @property
            def command(self) -> str:
                return "my-scanner"

            def _build_command(self, targets: List[str]) -> List[str]:
                return ["my-scanner", "--json"] + targets

            def _parse_output(self, raw: str) -> MyScanResult:
                data = json.loads(raw)
                return MyScanResult(...)
    """

    SEVERITY_LEVELS = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

    def __init__(self, config: Optional[ScannerConfig] = None, **kwargs):
        """
        Initialize scanner.

        Args:
            config: Scanner configuration
            **kwargs: Additional config overrides (min_severity, timeout, exclude_dirs)
        """
        self.config = config or ScannerConfig()

        # Apply kwargs overrides
        if "min_severity" in kwargs:
            self.config.min_severity = kwargs["min_severity"]
        if "timeout" in kwargs:
            self.config.timeout = kwargs["timeout"]
        if "extra_args" in kwargs:
            self.config.extra_args = kwargs["extra_args"]
        if "exclude_dirs" in kwargs:
            self.config.exclude_dirs = kwargs["exclude_dirs"]

        # Verify installation
        if not self._is_installed():
            raise self._get_not_installed_error()

        logger.info(
            f"{self.name} scanner initialized (min_severity={self.config.min_severity})"
        )

    @property
    @abstractmethod
    def name(self) -> str:
        """Scanner name for logging and identification."""
        pass

    @property
    @abstractmethod
    def command(self) -> str:
        """CLI command name to execute."""
        pass

    @abstractmethod
    def _build_command(self, targets: List[str], **kwargs) -> List[str]:
        """
        Build scanner command with arguments.

        Args:
            targets: Files or directories to scan
            **kwargs: Additional options

        Returns:
            Command as list of strings
        """
        pass

    @abstractmethod
    def _parse_output(self, raw: str) -> R:
        """
        Parse scanner JSON output.

        Args:
            raw: Raw JSON string from scanner

        Returns:
            Parsed scan result
        """
        pass

    @abstractmethod
    def _get_not_installed_error(self) -> ScannerNotInstalledError:
        """Return appropriate NotInstalled exception with install instructions."""
        pass

    def _is_installed(self) -> bool:
        """Check if scanner CLI is available in PATH."""
        return shutil.which(self.command) is not None

    def scan_file(self, file_path: str) -> R:
        """
        Scan a single file.

        Args:
            file_path: Path to file

        Returns:
            Scan result

        Raises:
            FileNotFoundError: If file doesn't exist
            ScannerError: On scan failure
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        logger.info(f"[{self.name}] Scanning file: {file_path}")
        return self._run_scan([str(path)])

    def scan_directory(self, directory: str, recursive: bool = True) -> R:
        """
        Scan a directory.

        Args:
            directory: Path to directory
            recursive: Scan subdirectories (default: True)

        Returns:
            Scan result

        Raises:
            NotADirectoryError: If path is not a directory
            ScannerError: On scan failure
        """
        path = Path(directory)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        logger.info(
            f"[{self.name}] Scanning directory: {directory} (recursive={recursive})"
        )
        return self._run_scan([str(path)], recursive=recursive)

    def _run_scan(self, targets: List[str], **kwargs) -> R:
        """
        Execute scanner and parse results.

        Args:
            targets: Files/directories to scan
            **kwargs: Additional command options

        Returns:
            Parsed scan result

        Raises:
            ScannerError: On execution failure
        """
        cmd = self._build_command(targets, **kwargs)
        
        try:
            result = CommandExecutor.run(
                cmd,
                timeout=self.config.timeout,
                check=True,
                valid_return_codes=self._valid_return_codes()
            )
            
            # Additional JSON validation logic which was present before
            import json
            try:
                return self._parse_output(result.stdout)
            except json.JSONDecodeError as e:
                raise ScannerError(f"{self.name} returned invalid JSON: {e}")

        except CommandExecutionError as e:
            raise ScannerError(f"{self.name} failed: {e}") from e
        except Exception as e:
            raise ScannerError(f"Failed to run {self.name}: {e}") from e

    def _valid_return_codes(self) -> List[int]:
        """Return codes considered successful (override if needed)."""
        return [0, 1]

    def _should_include_finding(self, severity: str) -> bool:
        """
        Check if finding meets minimum severity threshold.

        Args:
            severity: Finding severity level

        Returns:
            True if severity >= min_severity
        """
        min_level = self.SEVERITY_LEVELS.get(self.config.min_severity.upper(), 1)
        finding_level = self.SEVERITY_LEVELS.get(severity.upper(), 1)
        return finding_level >= min_level

    @abstractmethod
    def finding_to_issue(self, finding: F, project_name: str = "Unknown") -> IssueData:
        """
        Convert a finding to GitLab issue.

        Args:
            finding: Scanner finding
            project_name: Project name for issue

        Returns:
            IssueData ready for GitLab API
        """
        pass

    def scan_result_to_issues(
        self, scan_result: R, project_name: str = "Unknown", group_by_file: bool = False
    ) -> List[IssueData]:
        """
        Convert scan results to GitLab issues.

        Args:
            scan_result: Scan result to convert
            project_name: Project name for issues
            group_by_file: Group findings by file (one issue per file)

        Returns:
            List of IssueData
        """
        findings = self._get_findings_from_result(scan_result)

        if not group_by_file:
            return [self.finding_to_issue(f, project_name) for f in findings]

        # Group by file
        by_file: Dict[str, List[F]] = {}
        for finding in findings:
            file_path = self._get_finding_file(finding)
            if file_path not in by_file:
                by_file[file_path] = []
            by_file[file_path].append(finding)

        return [
            self._create_grouped_issue(file_path, file_findings, project_name)
            for file_path, file_findings in by_file.items()
        ]

    @abstractmethod
    def _get_findings_from_result(self, result: R) -> List[F]:
        """Extract findings list from scan result."""
        pass

    @abstractmethod
    def _get_finding_file(self, finding: F) -> str:
        """Get file path from finding."""
        pass

    @abstractmethod
    def _create_grouped_issue(
        self, file_path: str, findings: List[F], project_name: str
    ) -> IssueData:
        """Create grouped issue for multiple findings in a file."""
        pass
