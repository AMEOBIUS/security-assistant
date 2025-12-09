# LLM Integration Guide

Security Assistant integrates with Large Language Models (LLMs) to provide:
- 🧠 **Plain language explanations** of security vulnerabilities
- 🛠️ **Context-aware fix suggestions**
- 🕵️ **Code analysis** for finding complex issues

## Supported Providers

| Provider | Supported Models | Configuration Key |
|----------|------------------|-------------------|
| **OpenAI** | GPT-4, GPT-4o, GPT-3.5 | `openai` |
| **Anthropic** | Claude 3.5 Sonnet, Opus | `anthropic` |
| **NVIDIA NIM** | Devstral 2 (123B), Mistral | `nvidia` |
| **Ollama** | Llama 3, Mistral (Local) | `ollama` |

---

## 🚀 Quick Start

### 1. Configure Provider

You can configure LLM settings via `config.yaml` or Environment Variables.

#### Option A: Environment Variables (Recommended)

```bash
# NVIDIA NIM (Recommended for Coding)
export SA_LLM__PROVIDER=nvidia
export SA_LLM__API_KEY=nvapi-xxxxxxxxxxxxxxxxx
export SA_LLM__MODEL=mistralai/devstral-2-123b-instruct-2512

# OpenAI
export SA_LLM__PROVIDER=openai
export SA_LLM__API_KEY=sk-xxxxxxxxxxxxxxxxx

# Anthropic
export SA_LLM__PROVIDER=anthropic
export SA_LLM__API_KEY=sk-ant-xxxxxxxxxxxxxxxxx

# Ollama (Local)
export SA_LLM__PROVIDER=ollama
export SA_LLM__API_BASE=http://localhost:11434
export SA_LLM__MODEL=llama3
```

#### Option B: Configuration File

Add to your `security-assistant.yaml`:

```yaml
llm:
  provider: nvidia
  api_key: nvapi-xxxxxxxxxxxxxxxxx
  model: mistralai/devstral-2-123b-instruct-2512
  temperature: 0.2
  max_tokens: 2000
```

---

## 🛠️ Usage

### 1. Explain Findings During Scan

Run a scan and automatically explain the most critical findings:

```bash
security-assistant scan ./src --llm nvidia --explain
```

### 2. Explain Specific Finding

Explain a finding from a previous scan report:

```bash
# List findings first (if you need IDs)
# Then explain by ID
security-assistant explain FINDING_ID
```

Example:
```bash
security-assistant explain bandit-b101-main.py-10 --report reports/scan-results.json
```

### 3. Suggest Fixes

Get a concrete code fix for a vulnerability:

```bash
security-assistant explain bandit-b101-main.py-10 --fix
```

### 4. Overriding Provider via CLI

You can switch providers on the fly:

```bash
security-assistant scan . --llm ollama --explain
```

---

## 🔒 Security & Privacy

- **Code Snippets:** When using `explain` or `fix`, code snippets related to the finding are sent to the LLM provider.
- **Local Mode:** Use **Ollama** if you cannot send code to external APIs.
- **API Keys:** Never commit API keys to version control. Use `.env` or environment variables.

## 🤖 NVIDIA NIM Integration

We officially support NVIDIA NIM for high-performance inference.
Recommended model: **mistralai/devstral-2-123b-instruct-2512**

1. Get API Key at [build.nvidia.com](https://build.nvidia.com)
2. Set `SA_LLM__PROVIDER=nvidia`
3. Set `SA_LLM__API_KEY=nvapi-...`
