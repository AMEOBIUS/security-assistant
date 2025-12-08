# 🧠 Session 58: LLM Integration (BYOK)

**Priority:** CRITICAL  
**Timeline:** Jan 8-15, 2026 (7 days)  
**Effort:** 1 week  
**Dependencies:** None  
**Blocks:** Session 59 (Auto-PoC needs LLM)

---

## 🎯 **OBJECTIVE**

Implement LLM integration to eliminate website bullshit and add real value.

**Goal:** Users can explain findings and get fix suggestions using their own API keys.

---

## 📦 **DELIVERABLES**

### **1. Core LLM Module**

```
security_assistant/llm/
├── __init__.py              # Public API exports
├── base_client.py           # Abstract LLM client
├── openai_client.py         # OpenAI/GPT integration
├── anthropic_client.py      # Claude integration
├── ollama_client.py         # Local LLM (Ollama)
└── prompts/
    ├── explain_finding.txt  # System prompt for explanations
    ├── suggest_fix.txt      # System prompt for fixes
    └── analyze_code.txt     # System prompt for code analysis
```

### **2. LLM Service**

```
security_assistant/services/
└── llm_service.py           # High-level LLM orchestration
```

### **3. Configuration**

```yaml
# security-assistant.yaml
llm:
  enabled: true
  provider: openai           # openai, anthropic, ollama
  api_key: ${OPENAI_API_KEY}
  model: gpt-4
  max_tokens: 1000
  temperature: 0.3
  timeout: 30
  retry_attempts: 3
```

### **4. CLI Commands**

```bash
# Explain a specific finding
security-assistant explain <finding_id> --llm openai

# Scan with LLM explanations
security-assistant scan ./app --llm claude --explain

# Interactive mode
security-assistant chat
> Explain the SQL injection in api/users.py
> How do I fix the hardcoded secret?
```

### **5. Tests**

```
tests/llm/
├── __init__.py
├── test_base_client.py      # 5 tests
├── test_openai_client.py    # 8 tests
├── test_anthropic_client.py # 8 tests
├── test_ollama_client.py    # 8 tests
└── test_llm_service.py      # 10 tests

Total: 39 tests
```

---

## 🏗️ **IMPLEMENTATION PLAN**

### **Day 1: Architecture & Base Client**

**Tasks:**
1. Create `llm/base_client.py`:
   ```python
   from abc import ABC, abstractmethod
   from typing import Optional, List, Dict, Any
   
   class BaseLLMClient(ABC):
       @abstractmethod
       def complete(self, prompt: str, **kwargs) -> str:
           """Generate completion for prompt."""
           pass
       
       @abstractmethod
       def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
           """Chat completion with message history."""
           pass
       
       @abstractmethod
       def is_available(self) -> bool:
           """Check if LLM is available."""
           pass
   ```

2. Create prompt templates:
   ```
   prompts/explain_finding.txt:
   You are a security expert. Explain this vulnerability in plain language:
   
   Vulnerability: {title}
   Severity: {severity}
   Location: {file_path}:{line_start}
   Code: {code_snippet}
   
   Provide:
   1. What is this vulnerability?
   2. Why is it dangerous?
   3. How to fix it?
   ```

3. Add Pydantic config:
   ```python
   class LLMConfig(BaseModel):
       enabled: bool = False
       provider: str = "openai"
       api_key: Optional[str] = None
       model: str = "gpt-4"
       max_tokens: int = 1000
       temperature: float = 0.3
   ```

**Deliverables:**
- ✅ `base_client.py` (100 lines)
- ✅ 3 prompt templates
- ✅ `LLMConfig` in `config.py`
- ✅ 5 tests for base client

**Time:** 6-8 hours

---

### **Day 2: OpenAI Client**

**Tasks:**
1. Install dependencies:
   ```bash
   pip install openai>=1.0.0
   ```

2. Implement `openai_client.py`:
   ```python
   from openai import OpenAI
   from .base_client import BaseLLMClient
   
   class OpenAIClient(BaseLLMClient):
       def __init__(self, api_key: str, model: str = "gpt-4"):
           self.client = OpenAI(api_key=api_key)
           self.model = model
       
       def complete(self, prompt: str, **kwargs) -> str:
           response = self.client.chat.completions.create(
               model=self.model,
               messages=[{"role": "user", "content": prompt}],
               **kwargs
           )
           return response.choices[0].message.content
       
       def chat(self, messages: List[Dict], **kwargs) -> str:
           response = self.client.chat.completions.create(
               model=self.model,
               messages=messages,
               **kwargs
           )
           return response.choices[0].message.content
       
       def is_available(self) -> bool:
           try:
               self.client.models.list()
               return True
           except:
               return False
   ```

3. Add error handling:
   - Rate limiting (429)
   - Invalid API key (401)
   - Timeout errors
   - Retry logic with exponential backoff

**Deliverables:**
- ✅ `openai_client.py` (150 lines)
- ✅ Error handling
- ✅ 8 tests (mocked API)

**Time:** 6-8 hours

---

### **Day 3: Anthropic & Ollama Clients**

**Tasks:**
1. Install dependencies:
   ```bash
   pip install anthropic>=0.18.0
   pip install ollama>=0.1.0
   ```

2. Implement `anthropic_client.py`:
   ```python
   from anthropic import Anthropic
   from .base_client import BaseLLMClient
   
   class AnthropicClient(BaseLLMClient):
       def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
           self.client = Anthropic(api_key=api_key)
           self.model = model
       
       def complete(self, prompt: str, **kwargs) -> str:
           response = self.client.messages.create(
               model=self.model,
               max_tokens=kwargs.get("max_tokens", 1000),
               messages=[{"role": "user", "content": prompt}]
           )
           return response.content[0].text
   ```

3. Implement `ollama_client.py`:
   ```python
   import ollama
   from .base_client import BaseLLMClient
   
   class OllamaClient(BaseLLMClient):
       def __init__(self, model: str = "llama3"):
           self.model = model
       
       def complete(self, prompt: str, **kwargs) -> str:
           response = ollama.generate(model=self.model, prompt=prompt)
           return response['response']
       
       def is_available(self) -> bool:
           try:
               ollama.list()
               return True
           except:
               return False
   ```

**Deliverables:**
- ✅ `anthropic_client.py` (150 lines)
- ✅ `ollama_client.py` (100 lines)
- ✅ 16 tests (8 per client)

**Time:** 6-8 hours

---

### **Day 4: LLM Service**

**Tasks:**
1. Create `services/llm_service.py`:
   ```python
   class LLMService:
       def __init__(self, config: LLMConfig):
           self.config = config
           self.client = self._create_client()
       
       def _create_client(self) -> BaseLLMClient:
           if self.config.provider == "openai":
               return OpenAIClient(self.config.api_key, self.config.model)
           elif self.config.provider == "anthropic":
               return AnthropicClient(self.config.api_key, self.config.model)
           elif self.config.provider == "ollama":
               return OllamaClient(self.config.model)
           else:
               raise ValueError(f"Unknown provider: {self.config.provider}")
       
       def explain_finding(self, finding: UnifiedFinding) -> str:
           """Explain a finding in plain language."""
           prompt = self._build_explain_prompt(finding)
           return self.client.complete(prompt)
       
       def suggest_fix(self, finding: UnifiedFinding) -> str:
           """Suggest a fix for a finding."""
           prompt = self._build_fix_prompt(finding)
           return self.client.complete(prompt)
       
       def analyze_code(self, code: str, context: str) -> str:
           """Analyze code snippet."""
           prompt = self._build_analyze_prompt(code, context)
           return self.client.complete(prompt)
   ```

2. Add caching:
   - Cache LLM responses (finding_id → explanation)
   - TTL: 7 days
   - Reduce API costs

**Deliverables:**
- ✅ `llm_service.py` (200 lines)
- ✅ Prompt builders
- ✅ Response caching
- ✅ 10 tests

**Time:** 6-8 hours

---

### **Day 5: CLI Integration**

**Tasks:**
1. Add CLI commands:
   ```python
   # security_assistant/cli.py
   
   @click.command()
   @click.argument('finding_id')
   @click.option('--llm', type=click.Choice(['openai', 'anthropic', 'ollama']))
   def explain(finding_id: str, llm: str):
       """Explain a finding using LLM."""
       # Load scan results
       # Find finding by ID
       # Call LLM service
       # Print explanation
       pass
   
   @click.command()
   @click.argument('target')
   @click.option('--llm', type=click.Choice(['openai', 'anthropic', 'ollama']))
   @click.option('--explain', is_flag=True)
   def scan(target: str, llm: str, explain: bool):
       """Scan with optional LLM explanations."""
       # Run scan
       # If --explain: add LLM explanations to findings
       # Generate report
       pass
   ```

2. Update report generators:
   - Add "LLM Explanation" section to HTML reports
   - Add `llm_explanation` field to JSON output

**Deliverables:**
- ✅ CLI commands: `explain`, `scan --llm`
- ✅ Report integration
- ✅ 5 tests

**Time:** 4-6 hours

---

### **Day 6: Testing & Documentation**

**Tasks:**
1. Write comprehensive tests:
   - Unit tests (mocked API calls)
   - Integration tests (with real API, optional)
   - Error handling tests

2. Update documentation:
   ```
   docs/integrations/llm.md
   ├── Setup (API keys)
   ├── Providers (OpenAI, Anthropic, Ollama)
   ├── CLI Usage
   ├── Configuration
   └── Troubleshooting
   ```

3. Update README:
   ```markdown
   ## LLM Integration (Optional)
   
   Explain findings and get fix suggestions using LLMs:
   
   ```bash
   # Setup
   export OPENAI_API_KEY="sk-..."
   
   # Explain a finding
   security-assistant explain <finding_id> --llm openai
   
   # Scan with explanations
   security-assistant scan ./app --llm claude --explain
   ```
   
   Supported providers: OpenAI, Anthropic, Ollama (local)
   ```

**Deliverables:**
- ✅ 39 tests passing
- ✅ `docs/integrations/llm.md`
- ✅ README updated

**Time:** 6-8 hours

---

### **Day 7: Polish & Release**

**Tasks:**
1. Fix bugs from testing
2. Update CHANGELOG.md:
   ```markdown
   ## [1.1.0] - 2026-01-15
   
   ### Added
   - LLM Integration (OpenAI, Anthropic, Ollama)
   - CLI command: `explain`
   - CLI flag: `--llm` for scan command
   - LLM explanations in HTML reports
   
   ### Configuration
   - New `llm` section in config
   - Environment variable: `SA_LLM_API_KEY`
   ```

3. Create release:
   ```bash
   git tag v1.1.0
   git push origin v1.1.0
   ```

4. Update website (if features work)

**Deliverables:**
- ✅ v1.1.0 released
- ✅ CHANGELOG updated
- ✅ All tests passing

**Time:** 4-6 hours

---

## 📊 **SUCCESS METRICS**

**Code Quality:**
- ✅ 39+ tests passing
- ✅ 95%+ test coverage
- ✅ Type hints everywhere
- ✅ Docstrings for all public methods

**Functionality:**
- ✅ All 3 providers working (OpenAI, Anthropic, Ollama)
- ✅ CLI commands functional
- ✅ Error handling robust
- ✅ Caching reduces API costs

**Documentation:**
- ✅ Setup guide clear
- ✅ Examples working
- ✅ Troubleshooting comprehensive

**User Experience:**
- ✅ First explanation in <30 seconds
- ✅ API key setup in <5 minutes
- ✅ Ollama works offline (no API key needed)

---

## 🔧 **TECHNICAL DETAILS**

### **API Costs (Estimated):**

**OpenAI GPT-4:**
- Input: $0.03/1K tokens
- Output: $0.06/1K tokens
- Per explanation: ~500 tokens = $0.045
- 100 explanations: ~$4.50

**Anthropic Claude 3.5 Sonnet:**
- Input: $0.003/1K tokens
- Output: $0.015/1K tokens
- Per explanation: ~500 tokens = $0.009
- 100 explanations: ~$0.90

**Ollama (Local):**
- Cost: $0 (runs locally)
- Speed: Slower (depends on hardware)
- Privacy: 100% local

**Recommendation:** Start with Ollama for testing, use Claude for production (10x cheaper than GPT-4).

---

### **Prompt Engineering:**

**Explain Finding Prompt:**
```
You are a security expert explaining vulnerabilities to developers.

Vulnerability Details:
- Title: {title}
- Severity: {severity}
- Category: {category}
- Location: {file_path}:{line_start}-{line_end}
- Scanner: {scanner}

Code Snippet:
```{language}
{code_snippet}
```

Provide a clear, concise explanation:
1. What is this vulnerability? (2-3 sentences)
2. Why is it dangerous? (1-2 sentences)
3. How to fix it? (3-5 bullet points with code examples)

Keep it practical and actionable. No marketing fluff.
```

**Expected Output:**
```
1. What is this vulnerability?
This is a SQL injection vulnerability where user input is directly concatenated 
into a SQL query without sanitization. An attacker can manipulate the query 
to bypass authentication or extract sensitive data.

2. Why is it dangerous?
SQL injection can lead to complete database compromise, including data theft, 
modification, or deletion. It's consistently in OWASP Top 10.

3. How to fix it?
• Use parameterized queries (prepared statements)
• Example: cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
• Validate and sanitize all user inputs
• Use an ORM (SQLAlchemy, Django ORM) which handles escaping
• Never concatenate user input into SQL strings
```

---

## 🧪 **TESTING STRATEGY**

### **Unit Tests (Mocked):**
```python
# tests/llm/test_openai_client.py

@patch('openai.OpenAI')
def test_openai_complete(mock_openai):
    # Mock API response
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Test explanation"
    mock_openai.return_value.chat.completions.create.return_value = mock_response
    
    # Test
    client = OpenAIClient(api_key="test-key")
    result = client.complete("Explain this vulnerability")
    
    assert result == "Test explanation"
    assert mock_openai.called
```

### **Integration Tests (Optional, Real API):**
```python
# tests/llm/test_llm_integration.py

@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="No API key")
def test_real_openai_explain():
    client = OpenAIClient(api_key=os.getenv("OPENAI_API_KEY"))
    result = client.complete("Explain SQL injection")
    
    assert len(result) > 100
    assert "SQL" in result
```

---

## 📋 **CHECKLIST**

**Day 1:**
- [ ] Create `llm/base_client.py`
- [ ] Create prompt templates
- [ ] Add `LLMConfig` to config
- [ ] Write 5 base client tests

**Day 2:**
- [ ] Implement `openai_client.py`
- [ ] Add error handling
- [ ] Write 8 OpenAI tests
- [ ] Test with real API (optional)

**Day 3:**
- [ ] Implement `anthropic_client.py`
- [ ] Implement `ollama_client.py`
- [ ] Write 16 tests (8 per client)

**Day 4:**
- [ ] Create `llm_service.py`
- [ ] Add response caching
- [ ] Write 10 service tests

**Day 5:**
- [ ] Add CLI commands (`explain`, `scan --llm`)
- [ ] Update report generators
- [ ] Write 5 CLI tests

**Day 6:**
- [ ] Write documentation (`docs/integrations/llm.md`)
- [ ] Update README
- [ ] Run full test suite (566 + 39 = 605 tests)

**Day 7:**
- [ ] Fix bugs
- [ ] Update CHANGELOG
- [ ] Create checkpoint
- [ ] Release v1.1.0

---

## 🚀 **NEXT SESSION**

After Session 58 completion:
- **Session 59:** Auto-PoC Generation (uses LLM for enhancement)
- **Session 60:** Natural Language Queries (uses LLM for complex queries)

---

**Ready to start?** 🎯

**Created:** 2025-12-08  
**Status:** Planning
