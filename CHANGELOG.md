# Changelog

All notable changes to Security Workstation will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-12-08

### Major Release - Enterprise Security Orchestration

This release marks the transition to a production-ready Enterprise Security Orchestration platform. It includes massive architectural improvements, performance optimizations, and comprehensive documentation.

#### Key Features

**1. Intelligent Orchestration & Analysis**
- **Unified Finding Model**: Standardized format for all scanners (Bandit, Semgrep, Trivy).
- **Enrichment Service**:
  - **KEV Integration**: Automatic prioritization of actively exploited vulnerabilities (CISA KEV).
  - **EPSS Scoring**: Exploit Prediction Scoring System integration for risk assessment.
  - **False Positive Detection**: Heuristic engine to identify test code, mocks, and safe contexts.
  - **Reachability Analysis**: Lazy-loaded dependency analysis to filter unreachable libraries.
- **ML Scoring**: Random Forest model for vulnerability scoring (with rule-based fallback).

**2. Configuration & Developer Experience**
- **Pydantic v2 Configuration**:
  - Strongly typed configuration with automatic validation.
  - `security-assistant.yaml` with JSON Schema support for IDE autocompletion.
  - Environment variable overrides (`SA_*`).
- **Web Dashboard**:
  - React/TypeScript frontend for visualizing scan results.
  - Historical trends and remediation tracking.
- **Remediation Templates**: Automated fix suggestions for common vulnerabilities.

**3. Performance & Architecture**
- **Persistent Caching**: File-based caching for KEV and EPSS data (offline support).
- **Lazy Loading**: Heavy analysis modules (Reachability) load only when needed.
- **Refactored Core**: Clean architecture separating Orchestrator, Services, and Scanners.

**4. Reporting & CI/CD**
- **Multi-Format Reporting**: HTML (Interactive), JSON, SARIF, Markdown, Text.
- **GitLab Integration**: Two-way sync with GitLab Issues.
- **Bulk Operations**: Support for scanning multiple repositories in parallel.

#### Documentation
- **JSON Schema**: `docs/config-schema.json` for IDE validation.
- **Updated Guides**:
  - `docs/configuration.md`
  - `docs/installation.md`
  - `docs/integrations/`

#### Quality Assurance
- **Test Suite**: 566 tests passing (99% coverage).
- **Stability**: Fixed flaky integration tests and race conditions.

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
