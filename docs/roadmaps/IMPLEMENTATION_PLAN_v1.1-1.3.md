# 🎯 Implementation Plan v1.1-1.3 (Jan-Mar 2026)

**Goal:** Eliminate website bullshit by implementing missing features  
**Timeline:** 3-4 weeks (Jan 15 - Feb 15, 2026)  
**Current Version:** v1.0.0  
**Target Version:** v1.3.0

---

## 🚨 **PROBLEM: Website Claims vs Reality**

### ❌ **Bullshit on Website:**
1. **Auto-PoC Generation** - NOT IMPLEMENTED
2. **LLM Integration (Claude/GPT)** - NOT IMPLEMENTED  
3. **Natural Language Queries** - NOT IMPLEMENTED
4. **"5+ Scanners"** - Only 3 (Bandit, Semgrep, Trivy)
5. **Nuclei/ZAP/Burp** - NOT IMPLEMENTED

### ✅ **What Actually Works:**
- Multi-scanner orchestration (3 scanners)
- EPSS-based prioritization ✅
- KEV integration ✅
- False Positive Detection ✅
- Reachability Analysis ✅
- Remediation Templates (20+) ✅
- Bulk Operations ✅
- JSON/HTML/SARIF reports ✅

---

## 📅 **ROADMAP: Sessions 58-63**

### **Session 58: LLM Integration (BYOK)** | Jan 8-15, 2026 | 1 week | CRITICAL

**Priority:** CRITICAL (claimed on website)

**Deliverables:**
```
security_assistant/llm/
├── __init__.py
├── base_client.py           # Abstract LLM client
├── openai_client.py         # OpenAI/GPT-4 integration
├── anthropic_client.py      # Claude integration
├── ollama_client.py         # Local LLM (Ollama/LLaMA)
└── prompts/
    ├── explain_finding.txt  # Explain vulnerability
    ├── suggest_fix.txt      # Generate fix
    └── analyze_code.txt     # Analyze code context

security_assistant/services/
└── llm_service.py           # LLM orchestration service

security_assistant/config.py
└── LLMConfig                # Pydantic config model
```

**Features:**
1. **Explain Findings:**
   ```bash
   security-assistant explain <finding_id> --llm openai
   # Output: Plain language explanation + fix suggestion
   ```

2. **Code Analysis:**
   ```bash
   security-assistant scan ./app --llm claude --explain
   # Output: Each finding includes LLM explanation
   ```

3. **Supported Providers:**
   - OpenAI (GPT-4, GPT-3.5)
   - Anthropic (Claude 3.5 Sonnet, Claude 3 Opus)
   - Ollama (Local LLMs: Llama 3, Mistral, CodeLlama)

4. **BYOK (Bring Your Own Key):**
   ```yaml
   llm:
     enabled: true
     provider: openai  # openai, anthropic, ollama
     api_key: ${OPENAI_API_KEY}
     model: gpt-4
     max_tokens: 1000
     temperature: 0.3
   ```

**Implementation Steps:**
1. Create `llm/base_client.py` with abstract interface
2. Implement OpenAI client (priority #1)
3. Implement Anthropic client
4. Implement Ollama client (local, free)
5. Create `llm_service.py` for orchestration
6. Add CLI commands: `explain`, `--llm` flag
7. Update config schema
8. Write 15+ tests (mocked API calls)

**Tests:**
- `tests/llm/test_openai_client.py` (5 tests)
- `tests/llm/test_anthropic_client.py` (5 tests)
- `tests/llm/test_ollama_client.py` (5 tests)
- `tests/llm/test_llm_service.py` (10 tests)

**Success Criteria:**
- ✅ All 3 providers working
- ✅ CLI commands functional
- ✅ 25+ tests passing
- ✅ Documentation updated

**Time Estimate:** 5-7 days

---

### **Session 59: Auto-PoC Generation** | Jan 16-31, 2026 | 1-2 weeks | CRITICAL

**Priority:** CRITICAL (claimed on website)

**Deliverables:**
```
security_assistant/poc/
├── __init__.py
├── generator.py             # Main PoC generator
├── templates/
│   ├── sql_injection.py.j2
│   ├── sql_injection.sh.j2
│   ├── xss_reflected.html.j2
│   ├── xss_stored.html.j2
│   ├── command_injection.sh.j2
│   ├── path_traversal.py.j2
│   ├── ssrf.py.j2
│   ├── xxe.py.j2
│   └── csrf.html.j2
├── validators/
│   ├── syntax_validator.py  # Validate generated code
│   └── safety_checker.py    # Prevent dangerous PoCs
└── enhancers/
    └── llm_enhancer.py      # LLM-based PoC improvement
```

**Features:**
1. **Template-Based Generation:**
   ```bash
   security-assistant poc <finding_id> --output poc.py
   # Generates PoC from Jinja2 template
   ```

2. **LLM-Enhanced PoCs:**
   ```bash
   security-assistant poc <finding_id> --llm --validate
   # Uses LLM to customize PoC for specific context
   ```

3. **Safety Checks:**
   - No destructive operations (DROP TABLE, rm -rf)
   - Syntax validation before output
   - Dry-run mode by default

4. **Supported Vulnerabilities:**
   - SQL Injection (MySQL, PostgreSQL, SQLite)
   - XSS (Reflected, Stored, DOM-based)
   - Command Injection (OS command execution)
   - Path Traversal (LFI/RFI)
   - SSRF (Server-Side Request Forgery)
   - XXE (XML External Entity)
   - CSRF (Cross-Site Request Forgery)

**Implementation Steps:**
1. Create Jinja2 templates for each vuln type
2. Implement `PoCGenerator` class
3. Add syntax validators (Python, Bash, HTML)
4. Add safety checker (blacklist dangerous patterns)
5. Integrate with LLM service (optional enhancement)
6. Add CLI command: `poc`
7. Write 20+ tests

**Example Output:**
```python
# Generated PoC for SQL Injection in api/users.py:45
import requests

target_url = "http://localhost:8000/api/users"
payload = "' OR '1'='1' --"

response = requests.get(target_url, params={"id": payload})
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")

# Expected: Bypass authentication or dump data
```

**Tests:**
- `tests/poc/test_generator.py` (10 tests)
- `tests/poc/test_validators.py` (5 tests)
- `tests/poc/test_templates.py` (10 tests)

**Success Criteria:**
- ✅ 8+ vulnerability types supported
- ✅ Template + LLM modes working
- ✅ Safety checks prevent dangerous PoCs
- ✅ 25+ tests passing

**Time Estimate:** 7-10 days

---

### **Session 60: Natural Language Queries** | Feb 1-7, 2026 | 1 week | HIGH

**Priority:** HIGH (claimed on website)

**Deliverables:**
```
security_assistant/nl/
├── __init__.py
├── query_parser.py          # Parse NL queries
├── intent_classifier.py     # Classify intent
├── query_executor.py        # Execute queries
└── filters/
    ├── severity_filter.py
    ├── category_filter.py
    └── path_filter.py
```

**Features:**
1. **Simple NL Parser:**
   ```bash
   security-assistant query "Find SQL injections in /api"
   security-assistant ask "Show critical findings"
   security-assistant query "List all XSS vulnerabilities"
   ```

2. **Intent Classification:**
   - `find` - Search for specific vulnerability types
   - `show` - Display findings with filters
   - `list` - List findings by criteria
   - `explain` - Explain a finding (delegates to LLM)

3. **Filters:**
   - Severity: critical, high, medium, low
   - Category: sql-injection, xss, command-injection
   - Path: /api, /auth, *.py
   - Scanner: bandit, semgrep, trivy

**Implementation:**
```python
# Example: "Find SQL injections in /api"
query = NLQuery("Find SQL injections in /api")
intent = query.intent  # "find"
filters = query.filters  # {category: "sql-injection", path: "/api"}
results = query.execute(scan_result)
```

**LLM Fallback:**
- If query too complex → delegate to LLM
- LLM generates filter parameters
- Execute filters on scan results

**Tests:**
- `tests/nl/test_query_parser.py` (10 tests)
- `tests/nl/test_intent_classifier.py` (5 tests)
- `tests/nl/test_query_executor.py` (10 tests)

**Success Criteria:**
- ✅ 10+ query patterns supported
- ✅ LLM fallback working
- ✅ 25+ tests passing

**Time Estimate:** 5-7 days

---

### **Session 61: Nuclei Scanner Integration** | Feb 8-12, 2026 | 3-5 days | MEDIUM

**Priority:** MEDIUM (adds 4th scanner)

**Deliverables:**
```
security_assistant/scanners/
└── nuclei_scanner.py        # Nuclei integration

# Features:
# - Template-based scanning
# - CVE detection
# - Misconfiguration checks
# - Web vulnerability scanning
```

**Features:**
1. **Nuclei Integration:**
   ```bash
   security-assistant scan ./app --scanners nuclei
   ```

2. **Template Support:**
   - CVE templates (nuclei-templates/cves/)
   - Misconfiguration templates
   - Custom templates

3. **Unified Finding Conversion:**
   - Convert Nuclei JSON → UnifiedFinding
   - Map severity levels
   - Extract CVE IDs

**Implementation:**
```python
class NucleiScanner(BaseScanner):
    def scan_target(self, target: str) -> NucleiScanResult:
        # Run: nuclei -target <url> -json-export output.json
        # Parse JSON output
        # Convert to UnifiedFinding
        pass
```

**Tests:**
- `tests/test_nuclei_scanner.py` (10 tests)
- `tests/test_nuclei_integration.py` (5 tests)

**Success Criteria:**
- ✅ Nuclei scanner working
- ✅ Unified finding conversion
- ✅ 15+ tests passing

**Time Estimate:** 3-5 days

---

### **Session 62: Website Honesty Update** | Feb 13-14, 2026 | 1-2 days | CRITICAL

**Priority:** CRITICAL (fix bullshit)

**Changes:**

1. **Update "Available Now" section:**
   ```html
   <li><strong>LLM:</strong> Claude/GPT integration (BYOK) ✅</li>
   <li><strong>Auto-PoC:</strong> Template-based PoC generation ✅</li>
   <li><strong>NL Queries:</strong> Natural language search ✅</li>
   <li><strong>Scanners:</strong> Bandit, Semgrep, Trivy, Nuclei ✅</li>
   ```

2. **Update Hero Section:**
   ```html
   <p>Orchestrate Bandit, Semgrep, Trivy, Nuclei with LLM-powered analysis 
   and auto-PoC generation. Open source, self-hosted, no vendor lock-in.</p>
   ```

3. **Add "What's New in v1.3" section:**
   ```html
   <section id="whats-new">
       <h2>What's New in v1.3</h2>
       <ul>
           <li>✅ LLM Integration (OpenAI, Anthropic, Ollama)</li>
           <li>✅ Auto-PoC Generation (8+ vulnerability types)</li>
           <li>✅ Natural Language Queries</li>
           <li>✅ Nuclei Scanner Integration</li>
       </ul>
   </section>
   ```

4. **Fix GitHub links:**
   - `https://github.com/AMEOBIUS/Workstation` → `https://github.com/AMEOBIUS/security-assistant`

**Time Estimate:** 1-2 days

---

## 📊 **TIMELINE SUMMARY**

| Week | Session | Feature | Status |
|------|---------|---------|--------|
| **Jan 8-15** | 58 | LLM Integration | 🚧 Planned |
| **Jan 16-31** | 59 | Auto-PoC Generation | 🚧 Planned |
| **Feb 1-7** | 60 | Natural Language Queries | 🚧 Planned |
| **Feb 8-12** | 61 | Nuclei Scanner | 🚧 Planned |
| **Feb 13-14** | 62 | Website Update | 🚧 Planned |
| **Feb 15** | - | **v1.3.0 Release** | 🎯 Target |

---

## 🎯 **MILESTONES**

### **v1.1.0 - LLM Integration** (Jan 15, 2026)
- ✅ OpenAI, Anthropic, Ollama support
- ✅ Explain findings in plain language
- ✅ BYOK (Bring Your Own Key)
- ✅ 25+ tests passing

### **v1.2.0 - Auto-PoC Generation** (Jan 31, 2026)
- ✅ Template-based PoC generation
- ✅ 8+ vulnerability types
- ✅ LLM-enhanced PoCs
- ✅ Safety checks
- ✅ 25+ tests passing

### **v1.3.0 - Natural Language + Nuclei** (Feb 15, 2026)
- ✅ Natural Language Queries
- ✅ Nuclei scanner integration
- ✅ Website updated (no more bullshit)
- ✅ 40+ new tests passing

---

## 💡 **ALTERNATIVE: Quick Fix (1 day)**

**If no time for implementation:**

### **Session 58: Website Honesty Update** | 1 day | CRITICAL

**Changes:**
1. Move Auto-PoC, LLM, NL to "Roadmap (Q1 2026)"
2. Update "Available Now" with only real features
3. Add disclaimer:
   ```html
   <div class="beta-disclaimer">
       ⚠️ Beta Status: Auto-PoC, LLM integration, and Natural Language Queries 
       are planned for Q1 2026. Current version (v1.0.0) focuses on scanner 
       orchestration, EPSS prioritization, and multi-format reporting.
   </div>
   ```
4. Fix GitHub links

**Time:** 1 day

---

## 🤔 **RECOMMENDATION**

**Option 1: Implement Everything (3-4 weeks)**
- ✅ Honest website
- ✅ Real features
- ✅ Competitive advantage
- ❌ 3-4 weeks delay

**Option 2: Fix Website Now, Implement Later**
- ✅ Honest immediately
- ✅ No false promises
- ✅ Can implement features later
- ❌ Less impressive website

**Option 3: Hybrid (RECOMMENDED)**
- Week 1: Fix website + Start LLM integration
- Week 2-3: Finish LLM + Auto-PoC
- Week 4: NL Queries + Nuclei
- Week 5: Update website with real features

**My Vote:** **Option 3 (Hybrid)**
- Honesty first (fix website in 1 day)
- Then implement features (3 weeks)
- Update website when features are ready

---

## 📋 **NEXT STEPS**

**Immediate (Today):**
1. Fix GitHub links on website
2. Add beta disclaimer
3. Move unimplemented features to "Roadmap"

**This Week:**
1. Create Session 58 checkpoint
2. Start LLM integration
3. Update roadmap with progress

**This Month:**
1. Complete Sessions 58-60
2. Release v1.3.0
3. Update website with real features

---

**Created:** 2025-12-08  
**Last Updated:** 2025-12-08  
**Status:** Active Planning
