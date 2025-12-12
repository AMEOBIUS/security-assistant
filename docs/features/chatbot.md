# Security Chatbot Guide

Security Assistant includes an interactive chatbot that allows you to query scan results using natural language.

## 🚀 Quick Start

1. **Run a scan first:**
   ```bash
   security-assistant scan .
   ```

2. **Start the chatbot:**
   ```bash
   security-assistant chat
   ```

3. **Ask questions:**
   - "How many critical issues did you find?"
   - "Explain the SQL injection in login.py"
   - "How do I fix the hardcoded secrets?"
   - "Summarize the security posture of this project"

## 🔧 Configuration

The chatbot requires an LLM provider to be configured.

**Environment Variables:**
```bash
export SA_LLM__PROVIDER=nvidia  # or openai, anthropic, ollama
export SA_LLM__API_KEY=your-api-key
export SA_LLM__MODEL=mistralai/devstral-2-123b-instruct-2512
```

## 📝 Features

- **Context-Aware:** Loads the latest scan report (`scan-results.json`) automatically.
- **Interactive:** Maintains conversation history for follow-up questions.
- **Expert Knowledge:** Uses LLM to provide remediation advice and explanations.
- **Summary Mode:** Can summarize large reports into key takeaways.

## 🔍 Options

| Option | Description |
|--------|-------------|
| `-r`, `--report` | Path to scan results JSON (default: `security-reports/scan-results.json`) |
| `-c`, `--config` | Path to configuration file |

## 💡 Example Session

```
$ security-assistant chat
🔄 Loading scan context from security-reports/scan-results.json...

🤖 Security Assistant Chat
Type 'exit' or 'quit' to end session.
--------------------------------------------------

You: What are the top risks?
Thinking... 🤔

Assistant: Based on the scan results, the top risks are:
1. SQL Injection in `auth.py` (Critical) - Allows attackers to bypass authentication.
2. Hardcoded AWS Key in `config.py` (High) - Exposes cloud credentials.
3. Cross-Site Scripting (XSS) in `templates/index.html` (Medium) - Allows script injection.

I recommend fixing the SQL injection first by using parameterized queries.
--------------------------------------------------
```
