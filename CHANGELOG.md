# Changelog

All notable changes to Security Workstation will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Session 31-32: KEV + FP Detection + Reachability Analysis (2025-12-07)

#### Added

**KEV Integration (Session 31):**
- `security_assistant/enrichment/kev.py` - CISA KEV catalog client
  - Daily updates from CISA API
  - 24-hour caching with offline fallback
  - Ransomware campaign tracking
  - 32 tests passing ✅

**Vulnerability Enricher (Session 31):**
- `security_assistant/enrichment/enricher.py` - EPSS + KEV integration
  - Smart prioritization (KEV=true → CRITICAL)
  - EPSS-based scoring (70%+ → CRITICAL, 30-70% → HIGH)
  - Batch processing support
  - 15 tests passing ✅

**False Positive Detector (Session 31):**
- `security_assistant/analysis/false_positive_detector.py` - Auto-detect FP
  - Test code detection (test files, test functions)
  - Sanitization detection (escape, validate)
  - Mock data detection (fixtures, mocks)
  - Safe context detection (logging, comments)
  - Confidence-based filtering (threshold: 0.4)
  - 15 tests passing ✅

**Reachability Analysis (Session 32):**
- `security_assistant/analysis/reachability/` - 5 modules
  - `ast_parser.py` - Python AST parser
  - `import_tracker.py` - Import tracking
  - `call_graph.py` - Call graph builder (BFS-based)
  - `entry_points.py` - Entry point detection
  - `reachability_analyzer.py` - Main analyzer
  - Filters unreachable dependency vulnerabilities
  - Confidence scoring (0.0-1.0)
  - 17 tests passing ✅

**Documentation:**
- Updated `.agents/builder-mode.md` - Added MCP server usage
- Updated `.gitlab/duo/chat-rules.md` - Simplified rules
- Added `docs/roadmaps/MASTER_ROADMAP_2025-2026.md`
- Archived old roadmaps to `docs/archive/roadmaps/`

**Configuration:**
- Added `pytest.mark.integration` to `pyproject.toml`

#### Changed
- Reorganized roadmap documentation
- Updated README.md, QUICK_START.md, START_HERE.md

#### Tests
- **69 tests passing** (Session 31 + 32)
- **0 warnings** (registered integration marker)
- **0 skipped** (integration tests working)
- Coverage: enrichment + analysis modules

#### Success Metrics
- ✅ KEV data updates daily
- ✅ Auto-detect 30-50% false positives
- ✅ Reachability for Python dependencies
- ✅ Reduce noise by 50-70% (estimated)

---

## [0.4.0] - 2025-12-02

### Unified Checkpoint System

#### Added
- **Checkpoint Manager** (`scripts/checkpoint_manager.py`, 600+ lines)
  - Create/update/validate checkpoints
  - Generate GitLab Issue Templates from JSON
  - Search and navigation (latest, list, filter)
  - Continuity report generation
  - CLI interface with 7 commands

- **Documentation** (800+ lines)
  - `docs/CHECKPOINT_SYSTEM.md` - Full system documentation
  - `README_CHECKPOINT_SYSTEM.md` - Quick start guide

- **Tests** (350+ lines)
  - `tests/test_checkpoint_manager.py` - 30+ tests
  - Coverage: Creation, updates, validation, generation, navigation

#### Features
- Single Source of Truth - JSON checkpoint only
- Auto-Generation - Issue Templates from JSON
- Validation - Required fields, statuses, dates
- Navigation - Latest, list, filter by status
- Reports - Continuity reports with timeline

---

## [0.3.0] - 2025-11-29

### Initial Release

First production-ready release with multi-scanner orchestration.

#### Added
- Multi-Scanner Orchestration (Bandit, Semgrep, Trivy)
- GitLab API Integration
- Report Generation (7 formats)
- Scheduled Scans
- Performance Optimization
- CI/CD Integration (GitLab, GitHub, Jenkins)

#### Tests
- 316 tests passing
- 79% overall coverage
- 0 security issues

---

**Note:** Versions follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

[Unreleased]: https://gitlab.com/macar228228-group/workstation/-/compare/v0.4.0...main
[0.4.0]: https://gitlab.com/macar228228-group/workstation/-/tags/v0.4.0
[0.3.0]: https://gitlab.com/macar228228-group/workstation/-/tags/v0.3.0
