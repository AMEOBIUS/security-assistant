"""
Multi-Scanner Orchestration for Security Assistant

This module provides orchestration for running multiple security scanners
in parallel and aggregating their results. It handles:
- Parallel scanner execution
- Result aggregation and deduplication
- Priority scoring
- Unified reporting

Supported Scanners:
- Bandit (Python security)
- Semgrep (multi-language SAST)
- Trivy (containers, dependencies, secrets)

Version: 1.0.0
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .gitlab_api import IssueData
from .scanners.bandit_scanner import BanditScanner
from .scanners.semgrep_scanner import SemgrepScanner
from .scanners.trivy_scanner import (
    TrivyScanner,
)
from .security_validator import MetaSecurityValidator

# Import refactored services
from .services.deduplication import DeduplicationService, DeduplicationStrategy
from .services.enrichment_service import EnrichmentService
from .services.finding_converter import FindingConverter
from .services.issue_converter import IssueConverter
from .services.ml_scoring_service import MLScoringService
from .services.priority_calculator import PriorityCalculator
from .services.scan_coordinator_service import ScanCoordinatorService
from .services.scan_coordinator_service import ScannerType as CoordinatorScannerType

# Configure logging
logger = logging.getLogger(__name__)


class ScannerType(str, Enum):
    """Available scanner types"""

    BANDIT = "bandit"
    SEMGREP = "semgrep"
    TRIVY = "trivy"


class FindingSeverity(str, Enum):
    """Unified severity levels across all scanners"""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class UnifiedFinding:
    """
    Unified finding format across all scanners.

    This normalizes findings from different scanners into a common format
    for easier aggregation, deduplication, and reporting.
    """

    # Core identification
    finding_id: str  # Unique ID for this finding
    scanner: ScannerType  # Which scanner found this

    # Severity and classification
    severity: FindingSeverity
    category: str  # e.g., "security", "secret", "misconfig"

    # Location
    file_path: str
    line_start: int
    line_end: int

    # Details
    title: str
    description: str
    code_snippet: str

    # Metadata
    cwe_ids: List[str] = field(default_factory=list)
    owasp_categories: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)

    # Fix information
    fix_available: bool = False
    fix_version: Optional[str] = None
    fix_guidance: Optional[str] = None

    # Scoring
    priority_score: float = 0.0  # Calculated priority (0-100)
    confidence: Optional[str] = None  # HIGH, MEDIUM, LOW

    # ML Scoring (optional)
    ml_score: Optional[float] = None  # ML-based score (0-100)
    ml_confidence_interval: Optional[tuple] = None  # (lower, upper)
    epss_score: Optional[float] = None  # EPSS exploit probability (0-1)

    # Enrichment & Analysis
    is_active_exploit: bool = False  # Is actively exploited (KEV)
    is_false_positive: bool = False  # Is likely false positive
    fp_confidence: float = 0.0  # FP confidence (0-1)
    fp_reasons: List[str] = field(default_factory=list)  # Reasons for FP
    is_reachable: Optional[bool] = None  # Is reachable (True/False/None)
    reachability_confidence: float = 0.0  # Reachability confidence

    # Original finding data
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @property
    def severity_emoji(self) -> str:
        """Get emoji for severity level"""
        return {
            FindingSeverity.CRITICAL: "🔴",
            FindingSeverity.HIGH: "🟠",
            FindingSeverity.MEDIUM: "🟡",
            FindingSeverity.LOW: "🟢",
            FindingSeverity.INFO: "⚪",
        }.get(self.severity, "❓")

    @property
    def location_key(self) -> str:
        """Get unique key for location-based deduplication"""
        return f"{self.file_path}:{self.line_start}-{self.line_end}"

    @property
    def content_key(self) -> str:
        """Get unique key for content-based deduplication"""
        # Use title + file + code snippet for deduplication
        return f"{self.title}:{self.file_path}:{hash(self.code_snippet)}"


@dataclass
class OrchestrationResult:
    """Results from orchestrated multi-scanner execution"""

    # Findings
    all_findings: List[UnifiedFinding] = field(default_factory=list)
    deduplicated_findings: List[UnifiedFinding] = field(default_factory=list)

    # Scanner results
    scanner_results: Dict[ScannerType, Any] = field(default_factory=dict)

    # Execution metadata
    scan_time: datetime = field(default_factory=datetime.now)
    execution_time_seconds: float = 0.0
    target: str = ""

    # Statistics
    total_findings: int = 0
    findings_by_scanner: Dict[ScannerType, int] = field(default_factory=dict)
    findings_by_severity: Dict[FindingSeverity, int] = field(default_factory=dict)
    duplicates_removed: int = 0

    # Errors
    errors: List[str] = field(default_factory=list)

    @property
    def critical_count(self) -> int:
        """Number of CRITICAL findings"""
        return self.findings_by_severity.get(FindingSeverity.CRITICAL, 0)

    @property
    def high_count(self) -> int:
        """Number of HIGH findings"""
        return self.findings_by_severity.get(FindingSeverity.HIGH, 0)

    @property
    def medium_count(self) -> int:
        """Number of MEDIUM findings"""
        return self.findings_by_severity.get(FindingSeverity.MEDIUM, 0)

    @property
    def low_count(self) -> int:
        """Number of LOW findings"""
        return self.findings_by_severity.get(FindingSeverity.LOW, 0)

    @property
    def has_critical_or_high(self) -> bool:
        """Check if any CRITICAL or HIGH findings exist"""
        return self.critical_count > 0 or self.high_count > 0

    @property
    def top_priority_findings(self) -> List[UnifiedFinding]:
        """Get top 10 findings by priority score"""
        return sorted(
            self.deduplicated_findings, key=lambda f: f.priority_score, reverse=True
        )[:10]


@dataclass
class BulkScanResult:
    """Results from scanning multiple targets."""

    results: Dict[str, OrchestrationResult] = field(default_factory=dict)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    total_execution_time: float = 0.0

    @property
    def total_findings(self) -> int:
        return sum(r.total_findings for r in self.results.values())

    @property
    def total_critical(self) -> int:
        return sum(r.critical_count for r in self.results.values())

    @property
    def total_high(self) -> int:
        return sum(r.high_count for r in self.results.values())

    def get_aggregated_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics across all targets."""
        return {
            "targets_scanned": len(self.results),
            "total_findings": self.total_findings,
            "critical": self.total_critical,
            "high": self.total_high,
            "total_time": self.total_execution_time,
        }


class ScanOrchestrator:
    """
    Orchestrates multiple security scanners in parallel.

    Features:
    - Parallel scanner execution for performance
    - Result aggregation from multiple scanners
    - Intelligent deduplication
    - Priority scoring
    - Unified reporting format

    Example:
        >>> orchestrator = ScanOrchestrator()
        >>> orchestrator.enable_scanner(ScannerType.BANDIT)
        >>> orchestrator.enable_scanner(ScannerType.SEMGREP)
        >>> result = orchestrator.scan_directory("/path/to/project")
        >>> print(f"Found {len(result.deduplicated_findings)} unique issues")
    """

    # Severity priority for scoring
    SEVERITY_WEIGHTS = {
        FindingSeverity.CRITICAL: 100,
        FindingSeverity.HIGH: 75,
        FindingSeverity.MEDIUM: 50,
        FindingSeverity.LOW: 25,
        FindingSeverity.INFO: 10,
    }

    # Confidence weights for scoring
    CONFIDENCE_WEIGHTS = {
        "HIGH": 1.0,
        "MEDIUM": 0.7,
        "LOW": 0.4,
    }

    def __init__(
        self,
        max_workers: int = 3,
        enable_deduplication: bool = True,
        dedup_strategy: str = "location",  # "location", "content", "both"
        enable_meta_security: bool = False,  # Enable meta-security validation (default: False for tests)
        enable_ml_scoring: bool = False,  # Enable ML-based scoring (default: False)
        ml_model_path: Optional[str] = None,  # Path to ML model
        enable_kev: bool = True,  # Enable KEV integration (default: True)
        enable_fp_detection: bool = True,  # Enable FP detection (default: True)
        enable_reachability: bool = True,  # Enable reachability analysis (default: True)
    ):
        """
        Initialize scan orchestrator.

        Args:
            max_workers: Maximum parallel scanner threads (default: 3)
            enable_deduplication: Enable finding deduplication (default: True)
            dedup_strategy: Deduplication strategy:
                - "location": Deduplicate by file location
                - "content": Deduplicate by content similarity
                - "both": Use both strategies
            enable_meta_security: Enable meta-security validation (default: True)
            enable_kev: Enable KEV enrichment
            enable_fp_detection: Enable false positive detection
            enable_reachability: Enable reachability analysis
        """
        self.max_workers = max_workers
        self.enable_deduplication = enable_deduplication
        self.dedup_strategy = dedup_strategy
        self.enable_meta_security = enable_meta_security
        self.enable_ml_scoring = enable_ml_scoring
        self.enable_kev = enable_kev
        self.enable_fp_detection = enable_fp_detection
        self.enable_reachability = enable_reachability

        # Initialize refactored services

        # 1. ML Scoring Service
        self._ml_scoring_service = MLScoringService(
            enable_ml=enable_ml_scoring,
            model_path=ml_model_path,
            enable_epss=True,
        )

        # 2. Enrichment Service (KEV, FP, Reachability)
        self._enrichment_service = EnrichmentService(
            enable_kev=enable_kev,
            enable_fp_detection=enable_fp_detection,
            enable_reachability=enable_reachability,
            project_root=str(Path.cwd()),
        )

        # 3. Scan Coordinator Service
        self._scan_coordinator = ScanCoordinatorService(max_workers=max_workers)

        # 4. Deduplication Service
        strategy_map = {
            "location": DeduplicationStrategy.LOCATION,
            "content": DeduplicationStrategy.CONTENT,
            "both": DeduplicationStrategy.BOTH,
        }
        self._dedup_service = DeduplicationService(
            strategy=strategy_map.get(dedup_strategy, DeduplicationStrategy.LOCATION)
        )

        # 5. Priority Calculator
        self._priority_calculator = PriorityCalculator(
            kev_client=self._enrichment_service.kev_client,
            ml_scorer=self._ml_scoring_service.ml_scorer,
            enable_ml=enable_ml_scoring,
        )

        # 6. Finding Converter
        self._finding_converter = FindingConverter()

        # 7. Issue Converter (for GitLab integration)
        self._issue_converter = IssueConverter()

        # Meta-security validator
        if self.enable_meta_security:
            self._meta_validator = MetaSecurityValidator(
                strict_scanner_validation=True, project_root=Path.cwd()
            )
            logger.info("🛡️  Meta-security validation enabled")
        else:
            self._meta_validator = None
            logger.warning("⚠️  Meta-security validation disabled")

        logger.info(
            f"Initialized ScanOrchestrator: max_workers={max_workers}, "
            f"deduplication={enable_deduplication}, strategy={dedup_strategy}, "
            f"ml_scoring={enable_ml_scoring}"
        )

    @property
    def _enabled_scanners(self) -> Set[ScannerType]:
        """Get enabled scanners (for backward compatibility with tests)."""
        return {ScannerType(s.value) for s in self._scan_coordinator.enabled_scanners}

    def _run_scanner_safe(
        self, scanner_type: ScannerType, scanner: Any, directory: str, recursive: bool
    ) -> Any:
        """Wrapper for backward compatibility with tests."""
        return self._scan_coordinator._run_scanner_safe(
            CoordinatorScannerType(scanner_type.value), scanner, directory, recursive
        )

    def _run_scanner_file_safe(
        self, scanner_type: ScannerType, scanner: Any, file_path: str
    ) -> Any:
        """Wrapper for backward compatibility with tests."""
        return self._scan_coordinator._run_scanner_file_safe(
            CoordinatorScannerType(scanner_type.value), scanner, file_path
        )

    # Backward compatibility wrappers for conversion methods (used by tests)
    def _convert_bandit_findings(self, result):
        """Wrapper for backward compatibility with tests."""
        return self._finding_converter.convert_bandit(result, UnifiedFinding)

    def _convert_semgrep_findings(self, result):
        """Wrapper for backward compatibility with tests."""
        return self._finding_converter.convert_semgrep(result, UnifiedFinding)

    def _convert_trivy_findings(self, result):
        """Wrapper for backward compatibility with tests."""
        return self._finding_converter.convert_trivy(result, UnifiedFinding)

    def _unified_finding_to_issue(
        self, finding: UnifiedFinding, project_name: str
    ) -> IssueData:
        """Wrapper for backward compatibility with tests."""
        return self._issue_converter.convert_finding(finding, project_name)

    def enable_scanner(
        self,
        scanner_type: ScannerType,
        scanner_instance: Optional[Any] = None,
        **scanner_kwargs,
    ) -> None:
        """
        Enable a scanner with optional configuration.

        Args:
            scanner_type: Type of scanner to enable
            scanner_instance: Pre-initialized scanner instance (optional)
            **scanner_kwargs: Scanner-specific configuration

        Example:
            >>> orchestrator.enable_scanner(
            ...     ScannerType.BANDIT,
            ...     min_severity="MEDIUM",
            ...     min_confidence="HIGH"
            ... )

        Raises:
            ValueError: If scanner validation fails (when meta-security enabled)
        """
        # Create scanner instance if not provided
        if scanner_instance is None:
            if scanner_type == ScannerType.BANDIT:
                scanner_instance = BanditScanner(**scanner_kwargs)
            elif scanner_type == ScannerType.SEMGREP:
                scanner_instance = SemgrepScanner(**scanner_kwargs)
            elif scanner_type == ScannerType.TRIVY:
                scanner_instance = TrivyScanner(**scanner_kwargs)
            else:
                raise ValueError(f"Unknown scanner type: {scanner_type}")

        # META-SECURITY: Validate scanner integrity
        if self.enable_meta_security and self._meta_validator:
            validation_result = self._meta_validator.validate_scanner(scanner_instance)

            if not validation_result.is_valid:
                error_msg = (
                    f"Scanner validation failed for {scanner_type.value}:\n"
                    + "\n".join(f"  - {err}" for err in validation_result.errors)
                )
                logger.error(f"🚨 {error_msg}")
                raise ValueError(error_msg)

            # Log warnings
            for warning in validation_result.warnings:
                logger.warning(f"⚠️  Scanner validation warning: {warning}")

        # Register with scan coordinator
        coordinator_type = CoordinatorScannerType(scanner_type.value)
        self._scan_coordinator.register_scanner(coordinator_type, scanner_instance)
        logger.info(f"✓ Enabled scanner: {scanner_type.value}")

    def disable_scanner(self, scanner_type: ScannerType) -> None:
        """Disable a scanner."""
        coordinator_type = CoordinatorScannerType(scanner_type.value)
        self._scan_coordinator.unregister_scanner(coordinator_type)
        logger.info(f"Disabled scanner: {scanner_type.value}")

    def scan_directory(
        self,
        directory: str,
        recursive: bool = True,
    ) -> OrchestrationResult:
        """
        Scan a directory with all enabled scanners in parallel.

        Args:
            directory: Directory path to scan
            recursive: Scan subdirectories (default: True)

        Returns:
            OrchestrationResult with aggregated findings

        Example:
            >>> orchestrator = ScanOrchestrator()
            >>> orchestrator.enable_scanner(ScannerType.BANDIT)
            >>> orchestrator.enable_scanner(ScannerType.SEMGREP)
            >>> result = orchestrator.scan_directory("src/")
            >>> print(f"Critical: {result.critical_count}")
            >>> print(f"High: {result.high_count}")
        """
        if self._scan_coordinator.scanner_count == 0:
            raise ValueError("No scanners enabled. Call enable_scanner() first.")

        path = Path(directory)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not path.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        logger.info(f"Starting orchestrated scan of: {directory}")
        start_time = datetime.now()

        # Run scanners in parallel (using ScanCoordinatorService)
        scanner_results = self._scan_coordinator.scan_directory(directory, recursive)

        # Convert to unified findings
        all_findings = self._convert_to_unified_findings(scanner_results)

        # Deduplicate
        deduplicated = (
            self._deduplicate_findings(all_findings)
            if self.enable_deduplication
            else all_findings
        )

        # Enrichment (FP Detection + Reachability Analysis)
        self._enrichment_service.enrich_findings(deduplicated)

        # Calculate priority scores
        for finding in deduplicated:
            finding.priority_score = self._calculate_priority_score(finding)

        # Build result
        execution_time = (datetime.now() - start_time).total_seconds()

        result = OrchestrationResult(
            all_findings=all_findings,
            deduplicated_findings=deduplicated,
            scanner_results=scanner_results,
            scan_time=start_time,
            execution_time_seconds=execution_time,
            target=directory,
            total_findings=len(all_findings),
            duplicates_removed=len(all_findings) - len(deduplicated),
        )

        # Calculate statistics
        result.findings_by_scanner = self._count_by_scanner(deduplicated)
        result.findings_by_severity = self._count_by_severity(deduplicated)

        logger.info(
            f"Scan complete: {len(deduplicated)} unique findings "
            f"({result.duplicates_removed} duplicates removed) "
            f"in {execution_time:.2f}s"
        )

        return result

    def scan_file(self, file_path: str) -> OrchestrationResult:
        """
        Scan a single file with all enabled scanners.

        Args:
            file_path: File path to scan

        Returns:
            OrchestrationResult with aggregated findings
        """
        if self._scan_coordinator.scanner_count == 0:
            raise ValueError("No scanners enabled. Call enable_scanner() first.")

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not path.is_file():
            raise ValueError(f"Not a file: {file_path}")

        logger.info(f"Starting orchestrated scan of file: {file_path}")
        start_time = datetime.now()

        # Run scanners in parallel (using ScanCoordinatorService)
        scanner_results = self._scan_coordinator.scan_file(file_path)

        # Convert to unified findings
        all_findings = self._convert_to_unified_findings(scanner_results)

        # Deduplicate
        deduplicated = (
            self._deduplicate_findings(all_findings)
            if self.enable_deduplication
            else all_findings
        )

        # Enrichment (FP Detection + Reachability Analysis)
        self._enrichment_service.enrich_findings(deduplicated)

        # Calculate priority scores
        for finding in deduplicated:
            finding.priority_score = self._calculate_priority_score(finding)

        # Build result
        execution_time = (datetime.now() - start_time).total_seconds()

        result = OrchestrationResult(
            all_findings=all_findings,
            deduplicated_findings=deduplicated,
            scanner_results=scanner_results,
            scan_time=start_time,
            execution_time_seconds=execution_time,
            target=file_path,
            total_findings=len(all_findings),
            duplicates_removed=len(all_findings) - len(deduplicated),
        )

        # Calculate statistics
        result.findings_by_scanner = self._count_by_scanner(deduplicated)
        result.findings_by_severity = self._count_by_severity(deduplicated)

        logger.info(
            f"File scan complete: {len(deduplicated)} unique findings in {execution_time:.2f}s"
        )

        return result

    def scan_multiple_targets(self, targets: List[str]) -> BulkScanResult:
        """
        Scan multiple targets (directories or files).

        Args:
            targets: List of paths to scan

        Returns:
            BulkScanResult containing results for each target
        """
        bulk_result = BulkScanResult()

        logger.info(f"Starting bulk scan of {len(targets)} targets")

        for target in targets:
            try:
                target_path = Path(target)
                if target_path.is_file():
                    result = self.scan_file(target)
                elif target_path.is_dir():
                    result = self.scan_directory(target)
                else:
                    logger.warning(f"Target not found or invalid: {target}")
                    continue

                bulk_result.results[target] = result

            except Exception as e:
                logger.error(f"Failed to scan target {target}: {e}")
                # Can store error result if needed

        bulk_result.end_time = datetime.now()
        bulk_result.total_execution_time = (
            bulk_result.end_time - bulk_result.start_time
        ).total_seconds()

        logger.info(
            f"Bulk scan complete. Scanned {len(bulk_result.results)}/{len(targets)} targets "
            f"in {bulk_result.total_execution_time:.2f}s"
        )

        return bulk_result

    def _convert_to_unified_findings(
        self, scanner_results: Dict[ScannerType, Any]
    ) -> List[UnifiedFinding]:
        """Convert scanner-specific findings to unified format."""
        # Use refactored FindingConverter service
        return self._finding_converter.convert_all(scanner_results, UnifiedFinding)

    def _deduplicate_findings(
        self, findings: List[UnifiedFinding]
    ) -> List[UnifiedFinding]:
        """
        Deduplicate findings based on configured strategy.

        Strategies:
        - location: Same file + line range
        - content: Same title + file + code hash
        - both: Either location OR content match
        """
        # Use refactored DeduplicationService
        return self._dedup_service.deduplicate(findings)

    def _calculate_priority_score(self, finding: UnifiedFinding) -> float:
        """
        Calculate priority score (0-100) for a finding.

        Uses PriorityCalculator service which supports:
        - ML-based scoring (when enabled)
        - Rule-based scoring (fallback)
        - KEV integration
        """
        score = self._priority_calculator.calculate(finding)

        # Reachability adjustment (applied after main calculation)
        if finding.is_reachable is False:
            logger.debug(
                f"Reducing score for unreachable finding: {finding.finding_id}"
            )
            score = score * 0.5

        return min(score, 100.0)

    def _count_by_scanner(
        self, findings: List[UnifiedFinding]
    ) -> Dict[ScannerType, int]:
        """Count findings by scanner type."""
        counts = {}
        for finding in findings:
            counts[finding.scanner] = counts.get(finding.scanner, 0) + 1
        return counts

    def _count_by_severity(
        self, findings: List[UnifiedFinding]
    ) -> Dict[FindingSeverity, int]:
        """Count findings by severity."""
        counts = {}
        for finding in findings:
            counts[finding.severity] = counts.get(finding.severity, 0) + 1
        return counts

    def result_to_issues(
        self,
        result: OrchestrationResult,
        project_name: str,
        top_n: Optional[int] = None,
    ) -> List[IssueData]:
        """
        Convert orchestration result to GitLab issues.

        Args:
            result: OrchestrationResult to convert
            project_name: GitLab project name
            top_n: Only create issues for top N priority findings (default: all)

        Returns:
            List of IssueData ready for GitLab

        Example:
            >>> result = orchestrator.scan_directory("src/")
            >>> issues = orchestrator.result_to_issues(result, "MyProject", top_n=20)
            >>> # Create top 20 priority issues in GitLab
        """
        # Use IssueConverter service
        return self._issue_converter.convert_result(result, project_name, top_n)
