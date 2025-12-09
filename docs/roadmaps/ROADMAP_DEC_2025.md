# 🎯 Security Assistant - Roadmap December 2025

**Version:** v1.0.0 → v1.1.0  
**Timeline:** Dec 9, 2025 - Jan 15, 2026  
**Status:** Active Development  
**Current Session:** 62

---

## 📍 Current State (Dec 9, 2025)

### ✅ What's Working (v1.0.0):
- **CLI Tool:** Python-based scanner orchestrator
- **Scanners:** Bandit (SAST), Semgrep (SAST), Trivy (SCA)
- **Intelligence:**
  - KEV Integration (CISA Known Exploited Vulnerabilities)
  - EPSS Scoring (Exploit Prediction)
  - False Positive Detection (Heuristic engine)
  - Reachability Analysis (AST-based dependency tracking)
- **Reporting:** JSON, HTML, SARIF, Markdown, Text
- **Web Dashboard:** React/TypeScript visualizer
- **Remediation:** 20+ templates with code examples
- **Architecture:** Pydantic v2, persistent caching, lazy loading

### 🎯 What's Next:
- LLM Integration (v1.1.0)
- Auto-PoC Generation (v1.2.0)
- Natural Language Queries (v1.3.0)

---

## 🚀 EPIC 1: LLM Integration (v1.1.0) 🧠

**Priority:** P0 (CRITICAL)  
**Timeline:** Jan 8-15, 2026  
**Milestone:** v1.1.0  
**Effort:** 48-66 hours

### Issues for Epic 1:

#### Issue #37: Create LLM base client architecture
- **Labels:** `feature`, `llm`, `P0-critical`, `architecture`
- **Estimate:** 6-8h
- **Description:** Implement `BaseLLMClient` abstract class with `complete()`, `chat()`, `is_available()` methods
- **Acceptance Criteria:**
  - ✅ Abstract base class created
  - ✅ Type hints and docstrings
  - ✅ 5 unit tests passing
- **File:** `security_assistant/llm/base_client.py`

#### Issue #38: Create LLM prompt templates
- **Labels:** `feature`, `llm`, `P0-critical`
- **Estimate:** 2-3h
- **Description:** Create Jinja2 templates for `explain_finding`, `suggest_fix`, `analyze_code`
- **Files:** `security_assistant/llm/prompts/*.txt`

#### Issue #39: Implement OpenAI client
- **Labels:** `feature`, `llm`, `P0-critical`, `integration`
- **Estimate:** 6-8h
- **Description:** OpenAI/GPT integration with error handling, retry logic
- **Dependencies:** Issue #37
- **Tests:** 8 unit tests (mocked API)
- **File:** `security_assistant/llm/openai_client.py`

#### Issue #40: Implement Anthropic client
- **Labels:** `feature`, `llm`, `P0-critical`, `integration`
- **Estimate:** 6-8h
- **Description:** Claude integration (Claude 3.5 Sonnet, Claude 3 Opus)
- **Dependencies:** Issue #37
- **File:** `security_assistant/llm/anthropic_client.py`

#### Issue #41: Implement Ollama client
- **Labels:** `feature`, `llm`, `P1-high`, `integration`
- **Estimate:** 6-8h
- **Description:** Local LLM support (Llama 3, Mistral, CodeLlama)
- **Dependencies:** Issue #37
- **File:** `security_assistant/llm/ollama_client.py`

#### Issue #42: Create LLM service layer
- **Labels:** `feature`, `llm`, `P0-critical`, `service`
- **Estimate:** 6-8h
- **Description:** High-level orchestration service for LLM operations
- **Dependencies:** Issues #39, #40, #41
- **File:** `security_assistant/services/llm_service.py`

#### Issue #43: Add LLM configuration to Pydantic models
- **Labels:** `feature`, `llm`, `P0-critical`, `config`
- **Estimate:** 2-3h
- **Description:** Add `LLMConfig` to `security_assistant/config.py`
- **Schema:** `provider`, `api_key`, `model`, `max_tokens`, `temperature`

#### Issue #44: Implement CLI command: explain
- **Labels:** `feature`, `llm`, `P0-critical`, `cli`
- **Estimate:** 4-6h
- **Description:** `security-assistant explain <finding_id> --llm openai`
- **Dependencies:** Issue #42

#### Issue #45: Add --llm flag to scan command
- **Labels:** `feature`, `llm`, `P0-critical`, `cli`
- **Estimate:** 4-6h
- **Description:** `security-assistant scan ./app --llm claude --explain`
- **Dependencies:** Issue #42

#### Issue #46: LLM integration documentation
- **Labels:** `documentation`, `llm`, `P1-high`
- **Estimate:** 4-6h
- **Description:** Create `docs/integrations/llm.md` with setup guides
- **Examples:** BYOK setup for each provider

#### Issue #47: LLM integration tests
- **Labels:** `testing`, `llm`, `P0-critical`
- **Estimate:** 6-8h
- **Description:** 39 total tests across all LLM clients
- **Coverage:** >90%

#### Issue #48: Update README with LLM features
- **Labels:** `documentation`, `llm`, `P1-high`
- **Estimate:** 2-3h
- **Description:** Add LLM integration section to main README

---

## 🎯 EPIC 2: Auto-PoC Generation (v1.2.0) 🎯

**Priority:** P0 (CRITICAL)  
**Timeline:** Jan 16-31, 2026  
**Milestone:** v1.2.0  
**Effort:** 57-79 hours

### Issues for Epic 2:

#### Issue #49: Create PoC generator architecture
- **Labels:** `feature`, `poc`, `P0-critical`, `architecture`
- **Estimate:** 6-8h
- **Description:** Implement `PoCGenerator` class with template engine
- **File:** `security_assistant/poc/generator.py`

#### Issue #50: Create PoC templates for SQL Injection
- **Labels:** `feature`, `poc`, `P0-critical`, `templates`
- **Estimate:** 4-6h
- **Description:** Jinja2 templates for MySQL, PostgreSQL, SQLite
- **Files:** `security_assistant/poc/templates/sql_injection_*.j2`

#### Issue #51: Create PoC templates for XSS
- **Labels:** `feature`, `poc`, `P0-critical`, `templates`
- **Estimate:** 4-6h
- **Description:** Templates for Reflected, Stored, DOM-based XSS
- **Files:** `security_assistant/poc/templates/xss_*.j2`

#### Issue #52: Create PoC templates for Command Injection
- **Labels:** `feature`, `poc`, `P0-critical`, `templates`
- **Estimate:** 3-4h
- **Description:** OS command execution templates (Bash, PowerShell)

#### Issue #53: Create PoC templates for Path Traversal, SSRF, XXE, CSRF
- **Labels:** `feature`, `poc`, `P1-high`, `templates`
- **Estimate:** 6-8h
- **Description:** Templates for 4 additional vulnerability types

#### Issue #54: Implement syntax validators
- **Labels:** `feature`, `poc`, `P0-critical`, `validation`
- **Estimate:** 4-6h
- **Description:** Validate Python, Bash, HTML syntax before output
- **File:** `security_assistant/poc/validators/syntax_validator.py`

#### Issue #55: Implement safety checker
- **Labels:** `feature`, `poc`, `P0-critical`, `security`
- **Estimate:** 4-6h
- **Description:** Blacklist dangerous patterns (DROP TABLE, rm -rf)
- **File:** `security_assistant/poc/validators/safety_checker.py`

#### Issue #56: Integrate LLM for PoC enhancement
- **Labels:** `feature`, `poc`, `P1-high`, `llm`
- **Estimate:** 6-8h
- **Description:** Use LLM to customize PoCs for specific context
- **Dependencies:** Epic 1 (LLM Integration)
- **File:** `security_assistant/poc/enhancers/llm_enhancer.py`

#### Issue #57: Implement CLI command: poc
- **Labels:** `feature`, `poc`, `P0-critical`, `cli`
- **Estimate:** 4-6h
- **Description:** `security-assistant poc <finding_id> --output poc.py`

#### Issue #58: Auto-PoC tests
- **Labels:** `testing`, `poc`, `P0-critical`
- **Estimate:** 8-10h
- **Description:** 25+ tests for generator, validators, templates

#### Issue #59: Auto-PoC documentation
- **Labels:** `documentation`, `poc`, `P1-high`
- **Estimate:** 4-6h
- **Description:** Create `docs/features/auto-poc.md`

---

## 💬 EPIC 3: Natural Language Queries (v1.3.0) 💬

**Priority:** P1 (HIGH)  
**Timeline:** Feb 1-7, 2026  
**Milestone:** v1.3.0  
**Effort:** 39-54 hours

### Issues for Epic 3:

#### Issue #60: Create NL query parser
- **Labels:** `feature`, `nl-queries`, `P1-high`
- **Estimate:** 6-8h
- **Description:** Parse natural language queries into structured filters
- **File:** `security_assistant/nl/query_parser.py`

#### Issue #61: Implement intent classifier
- **Labels:** `feature`, `nl-queries`, `P1-high`, `ml`
- **Estimate:** 6-8h
- **Description:** Classify intent: find, show, list, explain
- **File:** `security_assistant/nl/intent_classifier.py`

#### Issue #62: Create query executor
- **Labels:** `feature`, `nl-queries`, `P1-high`
- **Estimate:** 4-6h
- **Description:** Execute queries on scan results with filters
- **File:** `security_assistant/nl/query_executor.py`

#### Issue #63: Implement filter modules
- **Labels:** `feature`, `nl-queries`, `P1-high`
- **Estimate:** 6-8h
- **Description:** Severity, category, path, scanner filters
- **Files:** `security_assistant/nl/filters/*.py`

#### Issue #64: Add LLM fallback for complex queries
- **Labels:** `feature`, `nl-queries`, `P2-medium`, `llm`
- **Estimate:** 4-6h
- **Description:** Delegate complex queries to LLM
- **Dependencies:** Epic 1

#### Issue #65: Implement CLI commands: query, ask
- **Labels:** `feature`, `nl-queries`, `P1-high`, `cli`
- **Estimate:** 4-6h
- **Description:** `security-assistant query "Find SQL injections in /api"`

#### Issue #66: NL queries tests
- **Labels:** `testing`, `nl-queries`, `P1-high`
- **Estimate:** 6-8h
- **Description:** 25+ tests for parser, classifier, executor

#### Issue #67: NL queries documentation
- **Labels:** `documentation`, `nl-queries`, `P2-medium`
- **Estimate:** 3-4h
- **Description:** Create `docs/features/natural-language-queries.md`

---

## 🔍 EPIC 4: Scanner Expansion (v1.3.0) 🔍

**Priority:** P2 (MEDIUM)  
**Timeline:** Feb 8-12, 2026  
**Milestone:** v1.3.0  
**Effort:** 22-31 hours

### Issues for Epic 4:

#### Issue #68: Implement Nuclei scanner integration
- **Labels:** `feature`, `scanners`, `P2-medium`, `integration`
- **Estimate:** 8-10h
- **Description:** Nuclei scanner with template support
- **File:** `security_assistant/scanners/nuclei_scanner.py`

#### Issue #69: Convert Nuclei findings to UnifiedFinding
- **Labels:** `feature`, `scanners`, `P2-medium`
- **Estimate:** 4-6h
- **Description:** Map Nuclei JSON output to UnifiedFinding model

#### Issue #70: Add Nuclei template support
- **Labels:** `feature`, `scanners`, `P2-medium`
- **Estimate:** 4-6h
- **Description:** Support CVE templates, misconfiguration checks

#### Issue #71: Nuclei scanner tests
- **Labels:** `testing`, `scanners`, `P2-medium`
- **Estimate:** 4-6h
- **Description:** 15+ tests for Nuclei integration

#### Issue #72: Update scanner documentation
- **Labels:** `documentation`, `scanners`, `P2-medium`
- **Estimate:** 2-3h
- **Description:** Add Nuclei to `docs/scanners/nuclei.md`

---

## 📝 EPIC 5: Website & Documentation (v1.3.0) 📝

**Priority:** P2 (MEDIUM)  
**Timeline:** Feb 13-15, 2026  
**Milestone:** v1.3.0  
**Effort:** 9-13 hours

### Issues for Epic 5:

#### Issue #73: Remove bullshit claims from website
- **Labels:** `documentation`, `website`, `P0-critical`, `honesty`
- **Estimate:** 2-3h
- **Description:** Update "Available Now" section with only real features
- **Files:** `web_dashboard/frontend/index.html`

#### Issue #74: Add beta disclaimer to website
- **Labels:** `documentation`, `website`, `P1-high`
- **Estimate:** 1-2h
- **Description:** Add disclaimer for features in development

#### Issue #75: Update website with v1.3.0 features
- **Labels:** `documentation`, `website`, `P1-high`
- **Estimate:** 3-4h
- **Description:** Add LLM, Auto-PoC, NL Queries to website

#### Issue #76: Fix GitHub links on website
- **Labels:** `documentation`, `website`, `P2-medium`, `bug`
- **Estimate:** 1h
- **Description:** Update all GitHub repository links

#### Issue #77: Create "What's New in v1.3" section
- **Labels:** `documentation`, `website`, `P2-medium`
- **Estimate:** 2-3h
- **Description:** Highlight new features in v1.3.0

---

## 📊 SUMMARY

**Total Issues Created:** 41 (Issues #37-#77)  
**Total Epics:** 5  
**Total Milestones:** 3  
**Timeline:** Jan 8 - Feb 15, 2026 (5 weeks)  
**Total Effort:** 188-264 hours

### Breakdown by Epic:
- **Epic 1 (LLM):** 12 issues, 48-66h
- **Epic 2 (Auto-PoC):** 11 issues, 57-79h
- **Epic 3 (NL Queries):** 8 issues, 39-54h
- **Epic 4 (Scanners):** 5 issues, 22-31h
- **Epic 5 (Website):** 5 issues, 9-13h

### Priority Distribution:
- **P0 (Critical):** 18 issues
- **P1 (High):** 15 issues
- **P2 (Medium):** 8 issues

---

## 🎯 MILESTONES

### v1.1.0 - LLM Integration (Jan 15, 2026)
- ✅ OpenAI, Anthropic, Ollama support
- ✅ Explain findings in plain language
- ✅ BYOK (Bring Your Own Key)
- ✅ 39+ tests passing

### v1.2.0 - Auto-PoC Generation (Jan 31, 2026)
- ✅ Template-based PoC generation
- ✅ 8+ vulnerability types
- ✅ LLM-enhanced PoCs
- ✅ Safety checks
- ✅ 25+ tests passing

### v1.3.0 - Natural Language + Nuclei (Feb 15, 2026)
- ✅ Natural Language Queries
- ✅ Nuclei scanner integration
- ✅ Website updated (no more bullshit)
- ✅ 40+ new tests passing

---

## 🚀 IMMEDIATE ACTIONS (Session 62)

### Today (Dec 9, 2025):
1. ✅ Create Session 62 checkpoint
2. 🎯 Clean up outdated roadmaps
3. 🎯 Create actualized roadmap (this file)
4. 🎯 Archive old plans

### This Week:
1. Review current v1.0.0 features
2. Validate all scanners working
3. Prepare for LLM integration (Session 63)

### Next Session (63):
1. Start Epic 1: LLM Integration
2. Create `security_assistant/llm/` directory
3. Implement base client architecture

---

## 📁 ROADMAP FILES

**Active (This File):**
- `docs/roadmaps/ROADMAP_DEC_2025.md` ← YOU ARE HERE

**To Archive:**
- `docs/roadmaps/IMPLEMENTATION_PLAN_v1.1-1.3.md` → archive
- `docs/roadmaps/MASTER_ROADMAP_2025-2026.md` → archive
- `docs/roadmaps/ROADMAP_EXECUTION_SUMMARY.md` → archive
- `docs/roadmaps/SESSION_58_LLM_INTEGRATION.md` → archive
- `docs/roadmaps/SESSION_58_QUICK_START.md` → archive

---

**Created:** 2025-12-09  
**Last Updated:** 2025-12-09  
**Status:** Active Planning  
**Session:** 62
