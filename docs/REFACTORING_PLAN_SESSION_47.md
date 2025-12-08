# Security Assistant Refactoring Plan - Session 47

## Executive Summary

| Metric | Value |
|--------|-------|
| **Issues Found** | 12 major |
| **Components to Refactor** | 5 |
| **Estimated Effort** | 2-3 sessions |
| **Risk Level** | Medium (backward compatibility maintained) |

---

## Current Architecture Analysis

### File Statistics

| File | Lines | Responsibilities | SOLID Violations |
|------|-------|------------------|------------------|
| `orchestrator.py` | ~900 | 9 | SRP, OCP, DIP |
| `report_generator.py` | ~2500 | 8 | SRP, OCP |
| `bandit_scanner.py` | ~350 | 4 | DRY |
| `semgrep_scanner.py` | ~400 | 4 | DRY |
| `trivy_scanner.py` | ~550 | 4 | DRY |

---

## Issue #1: Orchestrator God Object (CRITICAL)

### Problem
`ScanOrchestrator` class has **9 responsibilities**:

1. Scanner management (enable_scanner, disable_scanner)
2. Parallel execution (_run_scanners_parallel)
3. Result conversion (_convert_*_findings)
4. Deduplication (_deduplicate_findings)
5. Priority calculation (_calculate_priority_score)
6. KEV integration (active exploit checking)
7. False positive detection (_detect_false_positives)
8. Reachability analysis (_analyze_reachability)
9. GitLab issue generation (result_to_issues)

### Current Code (Before)
```python
class ScanOrchestrator:
    def __init__(self, max_workers=3, enable_deduplication=True, ...):
        # 15+ initialization parameters
        self._scanners = {}
        self._enabled_scanners = set()
        self._reachability_analyzer = ...
        self._kev_client = ...
        self._fp_detector = ...
        self._meta_validator = ...
        self._ml_scorer = ...
    
    def scan_directory(self, directory):
        # 50+ lines doing everything
        scanner_results = self._run_scanners_parallel(...)
        all_findings = self._convert_to_unified_findings(...)
        deduplicated = self._deduplicate_findings(...)
        self._detect_false_positives(...)
        self._analyze_reachability(...)
        # ... more logic
```

### Proposed Solution (After)
```python
# orchestration/scanner_manager.py
class ScannerManager:
    def __init__(self, max_workers: int = 3):
        self._scanners: Dict[ScannerType, Any] = {}
    
    def enable_scanner(self, scanner_type: ScannerType, **kwargs) -> None: ...
    def disable_scanner(self, scanner_type: ScannerType) -> None: ...
    def run_all(self, target: str) -> Dict[ScannerType, Any]: ...

# orchestration/deduplication_service.py
class DeduplicationService:
    def __init__(self, strategy: str = "location"):
        self.strategy = strategy
    
    def deduplicate(self, findings: List[UnifiedFinding]) -> List[UnifiedFinding]: ...

# orchestration/priority_calculator.py
class PriorityCalculator:
    def __init__(self, kev_client=None, ml_scorer=None):
        self._kev_client = kev_client
        self._ml_scorer = ml_scorer
    
    def calculate(self, finding: UnifiedFinding) -> float: ...

# orchestration/enrichment_service.py
class EnrichmentService:
    def __init__(self, fp_detector=None, reachability_analyzer=None):
        self._fp_detector = fp_detector
        self._reachability_analyzer = reachability_analyzer
    
    def enrich(self, findings: List[UnifiedFinding]) -> None: ...

# orchestrator.py (refactored - 100 lines)
class ScanOrchestrator:
    def __init__(
        self,
        scanner_manager: ScannerManager,
        dedup_service: DeduplicationService,
        priority_calc: PriorityCalculator,
        enrichment_service: EnrichmentService,
    ):
        self._scanner_manager = scanner_manager
        self._dedup_service = dedup_service
        self._priority_calc = priority_calc
        self._enrichment_service = enrichment_service
    
    @classmethod
    def create_default(cls) -> "ScanOrchestrator":
        """Factory for backward compatibility"""
        return cls(
            scanner_manager=ScannerManager(),
            dedup_service=DeduplicationService(),
            priority_calc=PriorityCalculator(),
            enrichment_service=EnrichmentService(),
        )
    
    def scan_directory(self, directory: str) -> OrchestrationResult:
        results = self._scanner_manager.run_all(directory)
        findings = self._convert_to_unified(results)
        deduplicated = self._dedup_service.deduplicate(findings)
        self._enrichment_service.enrich(deduplicated)
        for f in deduplicated:
            f.priority_score = self._priority_calc.calculate(f)
        return self._build_result(deduplicated)
```

### Migration Path
1. Create new `orchestration/` package
2. Extract components one by one
3. Update `ScanOrchestrator` to use new components via DI
4. Add `create_default()` factory for backward compatibility
5. Mark old constructor parameters as deprecated

### Test Strategy
- Unit tests for each extracted component
- Integration test for orchestrator with mocked components
- Regression tests using existing test suite

### Estimated Effort
- **Lines to change:** ~600
- **New files:** 5
- **Complexity:** High
- **Time:** 1 session

---

## Issue #2: Report Generator Monolith (HIGH)

### Problem
`ReportGenerator` contains **2500+ lines** with all formats in one file:
- HTML generation (~800 lines of inline HTML/CSS)
- Markdown generation
- JSON generation
- YAML generation
- Text generation
- SARIF generation
- PDF generation
- Bulk report generation

### Current Code (Before)
```python
class ReportGenerator:
    def generate_report(self, result, output_path, format, ...):
        if format == ReportFormat.HTML:
            content = self._generate_html_report(...)
        elif format == ReportFormat.PDF:
            content = self._generate_pdf_report(...)
        elif format == ReportFormat.SARIF:
            content = self._generate_sarif_report(...)
        # ... 7 more formats
    
    def _generate_html_report(self, ...):
        # 300+ lines of HTML generation
    
    def _html_header(self, title):
        # 150 lines of inline CSS
    
    def _html_findings_table(self, result):
        # 200+ lines
```

### Proposed Solution (After)
```python
# reporting/base_reporter.py
from abc import ABC, abstractmethod

class BaseReporter(ABC):
    def __init__(self, include_code_snippets: bool = True):
        self.include_code_snippets = include_code_snippets
    
    @abstractmethod
    def generate(self, result: OrchestrationResult, **kwargs) -> str:
        """Generate report content"""
        pass
    
    def _prepare_context(self, result: OrchestrationResult) -> Dict[str, Any]:
        """Common context preparation"""
        return {
            "scan_time": result.scan_time,
            "target": result.target,
            "findings": result.deduplicated_findings,
            "summary": {...}
        }

# reporting/html_reporter.py
class HTMLReporter(BaseReporter):
    def __init__(self, template_dir=None, include_charts=True, **kwargs):
        super().__init__(**kwargs)
        self.template_dir = template_dir
        self.include_charts = include_charts
    
    def generate(self, result: OrchestrationResult, **kwargs) -> str:
        context = self._prepare_context(result)
        return self._render_template("default.html", context)

# reporting/json_reporter.py
class JSONReporter(BaseReporter):
    def generate(self, result: OrchestrationResult, **kwargs) -> str:
        context = self._prepare_context(result)
        return json.dumps(context, indent=2, default=str)

# reporting/sarif_reporter.py
class SARIFReporter(BaseReporter):
    def generate(self, result: OrchestrationResult, **kwargs) -> str:
        # SARIF-specific generation
        pass

# reporting/reporter_factory.py
class ReporterFactory:
    _reporters = {
        "html": HTMLReporter,
        "json": JSONReporter,
        "sarif": SARIFReporter,
        "markdown": MarkdownReporter,
        "text": TextReporter,
        "yaml": YAMLReporter,
    }
    
    @classmethod
    def create(cls, format: str, **kwargs) -> BaseReporter:
        if format not in cls._reporters:
            raise ValueError(f"Unknown format: {format}")
        return cls._reporters[format](**kwargs)
    
    @classmethod
    def register(cls, format: str, reporter_class: type) -> None:
        """Register custom reporter"""
        cls._reporters[format] = reporter_class

# report_generator.py (facade for backward compatibility)
class ReportGenerator:
    def __init__(self, **kwargs):
        self._kwargs = kwargs
    
    def generate_report(self, result, output_path, format, **kwargs) -> str:
        reporter = ReporterFactory.create(format, **self._kwargs, **kwargs)
        content = reporter.generate(result, **kwargs)
        Path(output_path).write_text(content)
        return str(output_path)
```

### Migration Path
1. Create `reporting/` package
2. Extract `BaseReporter` with common logic
3. Create format-specific reporters
4. Create `ReporterFactory`
5. Update `ReportGenerator` as facade

### Test Strategy
- Unit tests for each reporter
- Test factory registration
- Test backward compatibility with existing API

### Estimated Effort
- **Lines to change:** ~2000
- **New files:** 8
- **Complexity:** Medium
- **Time:** 1 session

---

## Issue #3: Scanner Code Duplication (HIGH)

### Problem
All three scanners have identical patterns:
- `__init__` with installation check
- `scan_file` / `scan_directory` methods
- `_run_*` subprocess execution
- `_parse_*_output` JSON parsing
- `finding_to_issue` conversion
- `scan_result_to_issues` batch conversion
- `_create_grouped_issue` aggregation

**Duplicated code:** ~400 lines across 3 files

### Current Code (Before)
```python
# bandit_scanner.py
class BanditScanner:
    def __init__(self, min_severity="LOW", ...):
        if not self._check_bandit_installed():
            raise BanditNotInstalledError(...)
    
    def _check_bandit_installed(self):
        try:
            result = subprocess.run(["bandit", "--version"], ...)
            return result.returncode == 0
        except: return False
    
    def scan_directory(self, directory_path, recursive=True):
        if not os.path.exists(directory_path): raise ...
        return self._run_bandit([directory_path])
    
    def _run_bandit(self, targets):
        cmd = ["bandit", "-f", "json", ...]
        result = subprocess.run(cmd, capture_output=True, timeout=300)
        return self._parse_bandit_output(result.stdout)

# semgrep_scanner.py - SAME PATTERN
class SemgrepScanner:
    def __init__(self, min_severity="INFO", ...):
        if not self._check_semgrep_installed(): raise ...
    
    def _check_semgrep_installed(self): ...  # Same logic
    def scan_directory(self, ...): ...  # Same logic
    def _run_semgrep(self, targets): ...  # Same pattern

# trivy_scanner.py - SAME PATTERN
class TrivyScanner:
    def __init__(self, min_severity=..., ...):
        if not self._is_trivy_installed(): raise ...
    # ... same patterns
```

### Proposed Solution (After)
```python
# scanners/base_scanner.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import subprocess
import shutil

@dataclass
class ScannerConfig:
    min_severity: str = "LOW"
    timeout: int = 300
    exclude_dirs: List[str] = None

class BaseScanner(ABC):
    """Base class for all security scanners"""
    
    def __init__(self, config: Optional[ScannerConfig] = None):
        self.config = config or ScannerConfig()
        
        if not self._is_installed():
            raise self._get_not_installed_error()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Scanner name (e.g., 'bandit', 'semgrep')"""
        pass
    
    @property
    @abstractmethod
    def command(self) -> str:
        """CLI command name"""
        pass
    
    @abstractmethod
    def _build_command(self, targets: List[str]) -> List[str]:
        """Build scanner command with arguments"""
        pass
    
    @abstractmethod
    def _parse_output(self, raw: str) -> "ScanResult":
        """Parse scanner output to ScanResult"""
        pass
    
    @abstractmethod
    def _get_not_installed_error(self) -> Exception:
        """Return appropriate NotInstalled exception"""
        pass
    
    def _is_installed(self) -> bool:
        """Check if scanner CLI is available"""
        return shutil.which(self.command) is not None
    
    def scan_file(self, file_path: str) -> "ScanResult":
        """Scan a single file"""
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        return self._run_scan([file_path])
    
    def scan_directory(self, directory: str, recursive: bool = True) -> "ScanResult":
        """Scan a directory"""
        if not Path(directory).is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")
        return self._run_scan([directory])
    
    def _run_scan(self, targets: List[str]) -> "ScanResult":
        """Execute scanner and parse results"""
        cmd = self._build_command(targets)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config.timeout
            )
            
            # Most scanners return 1 if issues found
            if result.returncode not in [0, 1]:
                raise ScannerError(f"{self.name} failed: {result.stderr}")
            
            return self._parse_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            raise ScannerError(f"{self.name} timeout after {self.config.timeout}s")

# scanners/bandit_scanner.py (refactored)
class BanditScanner(BaseScanner):
    @property
    def name(self) -> str:
        return "bandit"
    
    @property
    def command(self) -> str:
        return "bandit"
    
    def _build_command(self, targets: List[str]) -> List[str]:
        cmd = ["bandit", "-f", "json", "-ll"]
        for exclude in self.config.exclude_dirs or []:
            cmd.extend(["-x", exclude])
        cmd.extend(targets)
        return cmd
    
    def _parse_output(self, raw: str) -> BanditScanResult:
        data = json.loads(raw)
        findings = [self._parse_finding(f) for f in data.get("results", [])]
        return BanditScanResult(findings=findings)
    
    def _get_not_installed_error(self) -> Exception:
        return BanditNotInstalledError("Install with: pip install bandit")
```

### Migration Path
1. Create `BaseScanner` abstract class
2. Refactor `BanditScanner` to extend `BaseScanner`
3. Refactor `SemgrepScanner`
4. Refactor `TrivyScanner`
5. Update tests

### Test Strategy
- Unit tests for BaseScanner
- Integration tests for each scanner
- Mock subprocess for unit tests

### Estimated Effort
- **Lines reduced:** ~300
- **New files:** 1 (base_scanner.py)
- **Complexity:** Medium
- **Time:** 0.5 session

---

## New Directory Structure

```
security_assistant/
├── __init__.py
├── orchestrator.py              # Facade (100 lines)
├── report_generator.py          # Facade (50 lines)
├── models.py                    # Unified data models
│
├── orchestration/               # NEW
│   ├── __init__.py
│   ├── scanner_manager.py       # Scanner coordination
│   ├── deduplication_service.py # Finding deduplication
│   ├── priority_calculator.py   # Priority scoring
│   ├── enrichment_service.py    # FP, KEV, Reachability
│   └── finding_converter.py     # Result conversion
│
├── reporting/                   # NEW
│   ├── __init__.py
│   ├── base_reporter.py         # Abstract base
│   ├── html_reporter.py         # HTML generation
│   ├── json_reporter.py         # JSON generation
│   ├── sarif_reporter.py        # SARIF format
│   ├── markdown_reporter.py     # Markdown
│   ├── text_reporter.py         # Plain text
│   └── reporter_factory.py      # Factory pattern
│
├── scanners/
│   ├── __init__.py
│   ├── base_scanner.py          # NEW: Abstract base
│   ├── bandit_scanner.py        # Refactored
│   ├── semgrep_scanner.py       # Refactored
│   └── trivy_scanner.py         # Refactored
│
├── analysis/                    # Existing
├── enrichment/                  # Existing
├── remediation/                 # Existing
└── ml/                          # Existing
```

---

## Implementation Order

### Phase 1: Base Abstractions (0.5 session)
1. [ ] Create `scanners/base_scanner.py`
2. [ ] Create `reporting/base_reporter.py`
3. [ ] Add unit tests

### Phase 2: Scanner Refactoring (0.5 session)
1. [ ] Refactor `BanditScanner` to use `BaseScanner`
2. [ ] Refactor `SemgrepScanner`
3. [ ] Refactor `TrivyScanner`
4. [ ] Update tests

### Phase 3: Reporter Refactoring (1 session)
1. [ ] Create `reporting/html_reporter.py`
2. [ ] Create `reporting/json_reporter.py`
3. [ ] Create `reporting/sarif_reporter.py`
4. [ ] Create `reporting/markdown_reporter.py`
5. [ ] Create `reporting/reporter_factory.py`
6. [ ] Update `ReportGenerator` as facade
7. [ ] Update tests

### Phase 4: Orchestrator Refactoring (1 session)
1. [ ] Create `orchestration/scanner_manager.py`
2. [ ] Create `orchestration/deduplication_service.py`
3. [ ] Create `orchestration/priority_calculator.py`
4. [ ] Create `orchestration/enrichment_service.py`
5. [ ] Update `ScanOrchestrator` with DI
6. [ ] Add `create_default()` factory
7. [ ] Update tests

### Phase 5: Validation (0.5 session)
1. [ ] Run full test suite
2. [ ] Verify backward compatibility
3. [ ] Performance benchmarking
4. [ ] Documentation update

---

## Success Criteria

### Technical
- [ ] Test coverage >= 90%
- [ ] All existing tests pass
- [ ] No performance regression
- [ ] Backward compatible API
- [ ] SOLID principles followed
- [ ] No code duplication (DRY)

### Metrics After Refactoring

| File | Lines Before | Lines After | Reduction |
|------|--------------|-------------|-----------|
| `orchestrator.py` | ~900 | ~100 | 89% |
| `report_generator.py` | ~2500 | ~50 | 98% |
| Scanners (total) | ~1300 | ~800 | 38% |

### Code Quality
- [ ] Each class has single responsibility
- [ ] Easy to add new scanners (extend BaseScanner)
- [ ] Easy to add new report formats (extend BaseReporter)
- [ ] Components easily mockable for testing
- [ ] Clear dependency injection

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking changes | Low | High | Backward-compatible facades |
| Test failures | Medium | Medium | Incremental refactoring |
| Performance regression | Low | Medium | Benchmark before/after |
| Missing edge cases | Medium | Low | Comprehensive test coverage |

---

## Backward Compatibility

### For Users (CLI)
- **No changes required**
- All CLI commands work unchanged
- Same output formats

### For Developers
- Old API still works (deprecated warnings)
- New API recommended
- Migration examples provided

```python
# OLD (still works, deprecated)
orchestrator = ScanOrchestrator(max_workers=3, enable_deduplication=True)

# NEW (recommended)
orchestrator = ScanOrchestrator.create_default()

# NEW (with custom components)
orchestrator = ScanOrchestrator(
    scanner_manager=ScannerManager(max_workers=3),
    dedup_service=DeduplicationService(strategy="location"),
    priority_calc=PriorityCalculator(),
    enrichment_service=EnrichmentService(),
)
```

---

## Questions to Resolve

1. Should we use async/await for parallel scanning?
2. Should reporters support streaming for large results?
3. Should we add plugin system for custom scanners?
4. Should enrichment be optional per-finding?

---

*Plan created: Session 47 - 2025-12-08*
*Author: Claude Opus 4.5*
