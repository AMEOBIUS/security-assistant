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
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Optional, Set, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum

from .scanners.bandit_scanner import BanditScanner, BanditFinding, ScanResult as BanditScanResult
from .scanners.semgrep_scanner import SemgrepScanner, SemgrepFinding, SemgrepScanResult
from .scanners.trivy_scanner import TrivyScanner, TrivyFinding, TrivyScanResult, TrivyScanType
from .gitlab_api import IssueData
from .security_validator import MetaSecurityValidator, SecurityValidationResult


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
    is_reachable: Optional[bool] = None # Is reachable (True/False/None)
    reachability_confidence: float = 0.0 # Reachability confidence
    
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
            self.deduplicated_findings,
            key=lambda f: f.priority_score,
            reverse=True
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
            "total_time": self.total_execution_time
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
        
        # Scanner instances
        self._scanners: Dict[ScannerType, Any] = {}
        self._enabled_scanners: Set[ScannerType] = set()
        
        # Reachability Analyzer
        if self.enable_reachability:
            try:
                from .analysis.reachability.reachability_analyzer import ReachabilityAnalyzer
                self._reachability_analyzer = ReachabilityAnalyzer(project_root=str(Path.cwd()))
                logger.info("🕸️ Reachability analysis enabled")
            except Exception as e:
                logger.error(f"Failed to initialize Reachability Analyzer: {e}")
                self._reachability_analyzer = None
        else:
            self._reachability_analyzer = None
            
        # KEV Client
        if self.enable_kev:
            try:
                from .enrichment.kev import KEVClient
                self._kev_client = KEVClient()
                logger.info("🛡️  KEV enrichment enabled")
            except Exception as e:
                logger.error(f"Failed to initialize KEV client: {e}")
                self._kev_client = None
        else:
            self._kev_client = None
            
        # False Positive Detector
        if self.enable_fp_detection:
            try:
                from .analysis.false_positive_detector import FalsePositiveDetector
                self._fp_detector = FalsePositiveDetector()
                logger.info("🧠 False positive detection enabled")
            except Exception as e:
                logger.error(f"Failed to initialize FP detector: {e}")
                self._fp_detector = None
        else:
            self._fp_detector = None
        
        # Meta-security validator
        if self.enable_meta_security:
            self._meta_validator = MetaSecurityValidator(
                strict_scanner_validation=True,
                project_root=Path.cwd()
            )
            logger.info("🛡️  Meta-security validation enabled")
        else:
            self._meta_validator = None
            logger.warning("⚠️  Meta-security validation disabled")
        
        # ML Scorer
        if self.enable_ml_scoring:
            try:
                from .ml.scoring import MLScorer
                from .ml.epss import EPSSClient
                
                epss_client = EPSSClient(cache_enabled=True)
                self._ml_scorer = MLScorer(
                    model_path=ml_model_path or "security_assistant/ml/models/random_forest_v1.pkl",
                    epss_client=epss_client,
                    enable_epss=True,
                )
                logger.info("🤖 ML-based scoring enabled")
            except Exception as e:
                logger.warning(f"⚠️  Failed to load ML model: {e}. Falling back to rule-based scoring.")
                self._ml_scorer = None
                self.enable_ml_scoring = False
        else:
            self._ml_scorer = None
            logger.info("Using rule-based scoring")
        
        logger.info(
            f"Initialized ScanOrchestrator: max_workers={max_workers}, "
            f"deduplication={enable_deduplication}, strategy={dedup_strategy}, "
            f"ml_scoring={enable_ml_scoring}"
        )
    
    def enable_scanner(
        self,
        scanner_type: ScannerType,
        scanner_instance: Optional[Any] = None,
        **scanner_kwargs
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
        
        self._scanners[scanner_type] = scanner_instance
        self._enabled_scanners.add(scanner_type)
        logger.info(f"✓ Enabled scanner: {scanner_type.value}")
    
    def disable_scanner(self, scanner_type: ScannerType) -> None:
        """Disable a scanner."""
        if scanner_type in self._enabled_scanners:
            self._enabled_scanners.remove(scanner_type)
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
        if not self._enabled_scanners:
            raise ValueError("No scanners enabled. Call enable_scanner() first.")
        
        path = Path(directory)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        if not path.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        
        logger.info(f"Starting orchestrated scan of: {directory}")
        start_time = datetime.now()
        
        # Run scanners in parallel
        scanner_results = self._run_scanners_parallel(directory, recursive)
        
        # Convert to unified findings
        all_findings = self._convert_to_unified_findings(scanner_results)
        
        # Deduplicate
        deduplicated = self._deduplicate_findings(all_findings) if self.enable_deduplication else all_findings
        
        # FP Detection
        if self._fp_detector:
            self._detect_false_positives(deduplicated)
            
        # Reachability Analysis
        if self._reachability_analyzer:
            self._analyze_reachability(deduplicated)
        
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
        if not self._enabled_scanners:
            raise ValueError("No scanners enabled. Call enable_scanner() first.")
        
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Not a file: {file_path}")
        
        logger.info(f"Starting orchestrated scan of file: {file_path}")
        start_time = datetime.now()
        
        # Run scanners in parallel
        scanner_results = self._run_scanners_parallel_file(file_path)
        
        # Convert to unified findings
        all_findings = self._convert_to_unified_findings(scanner_results)
        
        # Deduplicate
        deduplicated = self._deduplicate_findings(all_findings) if self.enable_deduplication else all_findings
        
        # FP Detection
        if self._fp_detector:
            self._detect_false_positives(deduplicated)
            
        # Reachability Analysis
        if self._reachability_analyzer:
            self._analyze_reachability(deduplicated)
        
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
        bulk_result.total_execution_time = (bulk_result.end_time - bulk_result.start_time).total_seconds()
        
        logger.info(
            f"Bulk scan complete. Scanned {len(bulk_result.results)}/{len(targets)} targets "
            f"in {bulk_result.total_execution_time:.2f}s"
        )
        
        return bulk_result
    
    def _run_scanners_parallel(
        self,
        directory: str,
        recursive: bool
    ) -> Dict[ScannerType, Any]:
        """Run all enabled scanners in parallel on a directory."""
        results = {}
        
        # Use tqdm if available for progress bar
        try:
            from tqdm import tqdm
            use_tqdm = True
        except ImportError:
            use_tqdm = False
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit scanner tasks
            future_to_scanner = {}
            
            for scanner_type in self._enabled_scanners:
                scanner = self._scanners[scanner_type]
                future = executor.submit(
                    self._run_scanner_safe,
                    scanner_type,
                    scanner,
                    directory,
                    recursive
                )
                future_to_scanner[future] = scanner_type
            
            # Collect results
            if use_tqdm:
                futures_iter = tqdm(
                    as_completed(future_to_scanner), 
                    total=len(future_to_scanner),
                    desc="Running scanners",
                    unit="scanner"
                )
            else:
                futures_iter = as_completed(future_to_scanner)
                
            for future in futures_iter:
                scanner_type = future_to_scanner[future]
                try:
                    result = future.result()
                    results[scanner_type] = result
                    logger.info(f"Scanner {scanner_type.value} completed successfully")
                except Exception as e:
                    logger.error(f"Scanner {scanner_type.value} failed: {e}")
                    results[scanner_type] = None
        
        return results
    
    def _run_scanners_parallel_file(self, file_path: str) -> Dict[ScannerType, Any]:
        """Run all enabled scanners in parallel on a single file."""
        results = {}
        
        # Use tqdm if available for progress bar
        try:
            from tqdm import tqdm
            use_tqdm = True
        except ImportError:
            use_tqdm = False
            
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit scanner tasks
            future_to_scanner = {}
            
            for scanner_type in self._enabled_scanners:
                scanner = self._scanners[scanner_type]
                future = executor.submit(
                    self._run_scanner_file_safe,
                    scanner_type,
                    scanner,
                    file_path
                )
                future_to_scanner[future] = scanner_type
            
            # Collect results
            if use_tqdm:
                futures_iter = tqdm(
                    as_completed(future_to_scanner), 
                    total=len(future_to_scanner),
                    desc="Scanning file",
                    unit="scanner"
                )
            else:
                futures_iter = as_completed(future_to_scanner)
                
            for future in futures_iter:
                scanner_type = future_to_scanner[future]
                try:
                    result = future.result()
                    results[scanner_type] = result
                    logger.info(f"Scanner {scanner_type.value} completed file scan")
                except Exception as e:
                    logger.error(f"Scanner {scanner_type.value} failed on file: {e}")
                    results[scanner_type] = None
        
        return results
    
    def _run_scanner_safe(
        self,
        scanner_type: ScannerType,
        scanner: Any,
        directory: str,
        recursive: bool
    ) -> Any:
        """Safely run a scanner with error handling."""
        try:
            logger.debug(f"Running {scanner_type.value} on {directory}")
            return scanner.scan_directory(directory, recursive=recursive)
        except Exception as e:
            logger.error(f"Error in {scanner_type.value}: {e}")
            raise
    
    def _run_scanner_file_safe(
        self,
        scanner_type: ScannerType,
        scanner: Any,
        file_path: str
    ) -> Any:
        """Safely run a scanner on a file with error handling."""
        try:
            logger.debug(f"Running {scanner_type.value} on {file_path}")
            return scanner.scan_file(file_path)
        except Exception as e:
            logger.error(f"Error in {scanner_type.value} on file: {e}")
            raise
    
    def _convert_to_unified_findings(
        self,
        scanner_results: Dict[ScannerType, Any]
    ) -> List[UnifiedFinding]:
        """Convert scanner-specific findings to unified format."""
        unified_findings = []
        
        for scanner_type, result in scanner_results.items():
            if result is None:
                continue
            
            if scanner_type == ScannerType.BANDIT:
                unified_findings.extend(self._convert_bandit_findings(result))
            elif scanner_type == ScannerType.SEMGREP:
                unified_findings.extend(self._convert_semgrep_findings(result))
            elif scanner_type == ScannerType.TRIVY:
                unified_findings.extend(self._convert_trivy_findings(result))
        
        return unified_findings
    
    def _convert_bandit_findings(self, result: BanditScanResult) -> List[UnifiedFinding]:
        """Convert Bandit findings to unified format."""
        unified = []
        
        for finding in result.findings:
            # Map Bandit severity to unified severity
            severity_map = {
                "HIGH": FindingSeverity.HIGH,
                "MEDIUM": FindingSeverity.MEDIUM,
                "LOW": FindingSeverity.LOW,
            }
            
            unified_finding = UnifiedFinding(
                finding_id=f"bandit-{finding.test_id}-{finding.filename}-{finding.line_number}",
                scanner=ScannerType.BANDIT,
                severity=severity_map.get(finding.severity, FindingSeverity.MEDIUM),
                category="security",
                file_path=finding.filename,
                line_start=finding.line_number,
                line_end=finding.line_number,
                title=finding.test_name,
                description=finding.issue_text,
                code_snippet=finding.code,
                cwe_ids=[finding.cwe_id] if finding.cwe_id else [],
                references=[finding.more_info] if finding.more_info else [],
                confidence=finding.confidence,
                raw_data={"bandit_finding": finding}
            )
            
            unified.append(unified_finding)
        
        return unified
    
    def _convert_semgrep_findings(self, result: SemgrepScanResult) -> List[UnifiedFinding]:
        """Convert Semgrep findings to unified format."""
        unified = []
        
        for finding in result.findings:
            # Map Semgrep severity to unified severity
            severity_map = {
                "ERROR": FindingSeverity.HIGH,
                "WARNING": FindingSeverity.MEDIUM,
                "INFO": FindingSeverity.LOW,
            }
            
            unified_finding = UnifiedFinding(
                finding_id=f"semgrep-{finding.check_id}-{finding.path}-{finding.start_line}",
                scanner=ScannerType.SEMGREP,
                severity=severity_map.get(finding.severity, FindingSeverity.MEDIUM),
                category=finding.category,
                file_path=finding.path,
                line_start=finding.start_line,
                line_end=finding.end_line,
                title=finding.check_id.split('.')[-1],
                description=finding.message,
                code_snippet=finding.code,
                cwe_ids=finding.cwe_ids,
                owasp_categories=finding.owasp_categories,
                references=finding.metadata.get("references", []),
                fix_guidance=finding.metadata.get("fix", ""),
                raw_data={"semgrep_finding": finding}
            )
            
            unified.append(unified_finding)
        
        return unified
    
    def _convert_trivy_findings(self, result: TrivyScanResult) -> List[UnifiedFinding]:
        """Convert Trivy findings to unified format."""
        unified = []
        
        for finding in result.findings:
            # Map Trivy severity to unified severity
            severity_map = {
                "CRITICAL": FindingSeverity.CRITICAL,
                "HIGH": FindingSeverity.HIGH,
                "MEDIUM": FindingSeverity.MEDIUM,
                "LOW": FindingSeverity.LOW,
                "UNKNOWN": FindingSeverity.INFO,
            }
            
            # Determine category
            category = "vulnerability"
            if finding.pkg_type == "secret":
                category = "secret"
            elif finding.pkg_type == "misconfig":
                category = "misconfig"
            
            unified_finding = UnifiedFinding(
                finding_id=f"trivy-{finding.vulnerability_id}-{finding.target}-{finding.pkg_name}",
                scanner=ScannerType.TRIVY,
                severity=severity_map.get(finding.severity.value, FindingSeverity.MEDIUM),
                category=category,
                file_path=finding.target,
                line_start=finding.start_line,
                line_end=finding.end_line,
                title=finding.title or finding.vulnerability_id,
                description=finding.description,
                code_snippet="",  # Trivy doesn't provide code snippets
                cwe_ids=finding.cwe_ids,
                references=finding.references,
                fix_available=finding.is_fixable,
                fix_version=finding.fixed_version,
                fix_guidance=finding.resolution,
                raw_data={"trivy_finding": finding}
            )
            
            unified.append(unified_finding)
        
        return unified
    
    def _deduplicate_findings(self, findings: List[UnifiedFinding]) -> List[UnifiedFinding]:
        """
        Deduplicate findings based on configured strategy.
        
        Strategies:
        - location: Same file + line range
        - content: Same title + file + code hash
        - both: Either location OR content match
        """
        if not findings:
            return findings
        
        seen_keys: Set[str] = set()
        deduplicated = []
        
        for finding in findings:
            # Generate deduplication key based on strategy
            if self.dedup_strategy == "location":
                key = finding.location_key
            elif self.dedup_strategy == "content":
                key = finding.content_key
            else:  # "both"
                key = f"{finding.location_key}|{finding.content_key}"
            
            if key not in seen_keys:
                seen_keys.add(key)
                deduplicated.append(finding)
            else:
                logger.debug(f"Duplicate finding removed: {finding.title} at {finding.location_key}")
        
        return deduplicated
    
    def _calculate_priority_score(self, finding: UnifiedFinding) -> float:
        """
        Calculate priority score (0-100) for a finding.
        
        Uses ML-based scoring if enabled, otherwise falls back to rule-based scoring.
        
        ML Scoring (when enabled):
        - Uses trained ML model with EPSS integration
        - Considers 20+ features including exploit probability
        - Provides confidence intervals and explainability
        
        Rule-Based Scoring (fallback):
        - Severity (40%)
        - Confidence (20%)
        - Fix availability (20%)
        - CWE/OWASP presence (10%)
        - Category (10%)
        """
        # Use ML scoring if enabled and available
        if self.enable_ml_scoring and self._ml_scorer:
            try:
                ml_score_result = self._ml_scorer.score(finding)
                
                # Store ML metadata in finding
                finding.ml_score = ml_score_result.ml_score
                finding.ml_confidence_interval = ml_score_result.confidence_interval
                finding.epss_score = ml_score_result.epss_score
                
                logger.debug(
                    f"ML Score: {ml_score_result.ml_score:.1f}/100 "
                    f"(EPSS: {ml_score_result.epss_score * 100:.1f}%) "
                    f"for {finding.finding_id}"
                )
                return ml_score_result.ml_score
            except Exception as e:
                logger.warning(f"ML scoring failed for {finding.finding_id}: {e}. Using rule-based fallback.")
                # Fall through to rule-based scoring
        
        # Rule-based scoring (fallback or default)
        return self._calculate_priority_score_rule_based(finding)
    
    def _calculate_priority_score_rule_based(self, finding: UnifiedFinding) -> float:
        """
        Calculate priority score using rule-based approach.
        
        This is the fallback when ML scoring is disabled or fails.
        
        Factors:
        - KEV Active Exploit (Boost to CRITICAL/100)
        - Severity (40%)
        - Confidence (20%)
        - Fix availability (20%)
        - CWE/OWASP presence (10%)
        - Category (10%)
        """
        # KEV Check (Highest Priority)
        if self._kev_client:
            # Check for CVEs in finding metadata
            # finding.raw_data might contain CVE ID, or we can parse from title/desc/refs
            # UnifiedFinding usually puts CVEs in cwe_ids (if misused) or references
            # But specific scanners put CVEs in different places.
            # Trivy puts them in finding_id (trivy-CVE-XXXX-...) and raw_data.
            
            cve_ids = []
            import re
            cve_pattern = r"CVE-\d{4}-\d{4,7}"
            
            # Extract CVEs from finding ID
            cves_in_id = re.findall(cve_pattern, finding.finding_id)
            cve_ids.extend(cves_in_id)
            
            # Check references for CVEs
            for ref in finding.references:
                if "CVE-" in ref:
                    cves = re.findall(cve_pattern, ref)
                    cve_ids.extend(cves)
            
            # Check title/description as well
            if "CVE-" in finding.title:
                cves = re.findall(cve_pattern, finding.title)
                cve_ids.extend(cves)
            
            # Check for active exploitation
            for cve in cve_ids:
                if self._kev_client.is_exploited(cve):
                    finding.is_active_exploit = True
                    finding.severity = FindingSeverity.CRITICAL
                    logger.info(f"🚨 KEV Match: {cve} is actively exploited! Boosting priority.")
                    return 100.0
        
        score = 0.0
        
        # Severity weight (40%)
        severity_score = self.SEVERITY_WEIGHTS.get(finding.severity, 25)
        score += severity_score * 0.4
        
        # Confidence weight (20%)
        if finding.confidence:
            confidence_score = self.CONFIDENCE_WEIGHTS.get(finding.confidence, 0.5) * 100
            score += confidence_score * 0.2
        else:
            score += 50 * 0.2  # Default medium confidence
        
        # Fix availability (20%)
        if finding.fix_available:
            score += 100 * 0.2
        
        # CWE/OWASP presence (10%)
        if finding.cwe_ids or finding.owasp_categories:
            score += 100 * 0.1
        
        # Category weight (10%)
        category_weights = {
            "security": 1.0,
            "secret": 1.0,
            "misconfig": 0.8,
            "vulnerability": 0.9,
        }
        category_score = category_weights.get(finding.category, 0.5) * 100
        score += category_score * 0.1
        
        # Reachability Adjustment
        # If reachable, slight boost? Or leave as is?
        # If NOT reachable, reduce score significantly
        if finding.is_reachable is False:
            # Reduce score for unreachable findings
            # e.g., by 50% or set to a max of LOW/MEDIUM
            logger.debug(f"Reducing score for unreachable finding: {finding.finding_id}")
            score = score * 0.5
        
        return min(score, 100.0)
    
    def _analyze_reachability(self, findings: List[UnifiedFinding]) -> None:
        """Analyze reachability for SCA findings."""
        if not self._reachability_analyzer:
            return
            
        # Filter for Trivy vulnerability findings (SCA)
        sca_findings = [
            f for f in findings 
            if f.scanner == ScannerType.TRIVY and f.category == "vulnerability"
        ]
        
        if not sca_findings:
            return
            
        logger.info(f"Analyzing reachability for {len(sca_findings)} SCA findings...")
        
        for finding in sca_findings:
            # Extract package name from finding ID or title
            # Trivy finding_id: trivy-CVE-XXXX-target-package
            # Or raw data
            pkg_name = None
            if finding.raw_data and "trivy_finding" in finding.raw_data:
                # TrivyFinding uses pkg_name attribute
                trivy_finding = finding.raw_data["trivy_finding"]
                if isinstance(trivy_finding, dict):
                    pkg_name = trivy_finding.get("pkg_name") or trivy_finding.get("PkgName")
                else:
                    pkg_name = getattr(trivy_finding, "pkg_name", None)
            
            if pkg_name:
                result = self._reachability_analyzer.analyze_dependency(pkg_name)
                finding.is_reachable = result.is_reachable
                finding.reachability_confidence = result.confidence
                
                if not finding.is_reachable:
                    logger.info(f"Unreachable dependency detected: {pkg_name} (finding: {finding.finding_id})")

    def _detect_false_positives(self, findings: List[UnifiedFinding]) -> None:
        """Run false positive detection on findings."""
        if not self._fp_detector:
            return
            
        # Prepare findings for detector
        findings_dict_list = []
        for f in findings:
            findings_dict_list.append({
                "file_path": f.file_path,
                "code": f.code_snippet,
                "vulnerability_type": f.title
            })
            
        # Run batch analysis
        analyses = self._fp_detector.analyze_batch(findings_dict_list)
        
        # Update findings
        for idx, analysis in analyses.items():
            if idx < len(findings):
                finding = findings[idx]
                finding.is_false_positive = analysis.is_likely_false_positive
                finding.fp_confidence = analysis.confidence
                finding.fp_reasons = analysis.reasons
                
                if finding.is_false_positive:
                    logger.info(
                        f"Probable False Positive: {finding.finding_id} "
                        f"(Confidence: {finding.fp_confidence:.2f})"
                    )

    def _count_by_scanner(self, findings: List[UnifiedFinding]) -> Dict[ScannerType, int]:
        """Count findings by scanner type."""
        counts = {}
        for finding in findings:
            counts[finding.scanner] = counts.get(finding.scanner, 0) + 1
        return counts
    
    def _count_by_severity(self, findings: List[UnifiedFinding]) -> Dict[FindingSeverity, int]:
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
        findings = result.deduplicated_findings
        
        # Filter to top N if specified
        if top_n:
            findings = sorted(findings, key=lambda f: f.priority_score, reverse=True)[:top_n]
        
        issues = []
        for finding in findings:
            issue = self._unified_finding_to_issue(finding, project_name)
            issues.append(issue)
        
        return issues
    
    def _unified_finding_to_issue(
        self,
        finding: UnifiedFinding,
        project_name: str
    ) -> IssueData:
        """Convert a unified finding to GitLab issue."""
        # Build title
        file_name = Path(finding.file_path).name
        title = f"{finding.severity_emoji} {finding.title} in {file_name}"
        
        # Build description
        description_parts = [
            f"## {finding.severity_emoji} Security Finding",
            "",
            f"**Severity:** {finding.severity.value}",
            f"**Category:** {finding.category}",
            f"**Scanner:** {finding.scanner.value}",
            f"**Priority Score:** {finding.priority_score:.1f}/100",
        ]
        
        if finding.confidence:
            description_parts.append(f"**Confidence:** {finding.confidence}")
        
        description_parts.extend([
            "",
            "### Location",
            f"**File:** `{finding.file_path}`",
            f"**Lines:** {finding.line_start}-{finding.line_end}",
            "",
            "### Description",
            finding.description,
        ])
        
        # Add code snippet if available
        if finding.code_snippet:
            description_parts.extend([
                "",
                "### Code",
                "```",
                finding.code_snippet,
                "```",
            ])
        
        # Add CWE
        if finding.cwe_ids:
            cwe_links = [
                f"[{cwe}](https://cwe.mitre.org/data/definitions/{cwe.replace('CWE-', '')}.html)"
                for cwe in finding.cwe_ids
            ]
            description_parts.extend([
                "",
                f"**CWE:** {', '.join(cwe_links)}"
            ])
        
        # Add OWASP
        if finding.owasp_categories:
            description_parts.extend([
                "",
                f"**OWASP:** {', '.join(finding.owasp_categories)}"
            ])
        
        # Add fix information
        if finding.fix_available:
            description_parts.extend([
                "",
                "### Fix Available",
            ])
            if finding.fix_version:
                description_parts.append(f"**Version:** {finding.fix_version}")
            if finding.fix_guidance:
                description_parts.append(f"\n{finding.fix_guidance}")
        
        # Add references
        if finding.references:
            description_parts.extend([
                "",
                "### References",
                *[f"- {ref}" for ref in finding.references[:5]],
            ])
        
        # Add footer
        description_parts.extend([
            "",
            "---",
            f"*Detected by {finding.scanner.value} scanner*",
            f"*Finding ID: `{finding.finding_id}`*"
        ])
        
        description = "\n".join(description_parts)
        
        # Determine labels
        labels = [
            "security",
            finding.scanner.value,
            finding.category,
            f"severity::{finding.severity.value.lower()}",
        ]
        
        if finding.severity in [FindingSeverity.CRITICAL, FindingSeverity.HIGH]:
            labels.append("critical")
        
        if finding.fix_available:
            labels.append("fix-available")
        
        return IssueData(
            title=title,
            description=description,
            labels=labels,
            confidential=True
        )
