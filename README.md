# 🛡️ Security Assistant

**Open-source security scanner orchestrator. Free forever, no license required.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![GitHub release](https://img.shields.io/github/v/tag/AMEOBIUS/security-assistant?label=version)](https://github.com/AMEOBIUS/security-assistant/releases)
[![Stars](https://img.shields.io/github/stars/AMEOBIUS/security-assistant?style=social)](https://github.com/AMEOBIUS/security-assistant)

**Security Assistant** orchestrates multiple security scanners (Bandit, Semgrep, Trivy, Nuclei), deduplicates findings, and prioritizes them using **Context Intelligence** (KEV, Reachability, False Positive Detection).

> **🚀 Live Demo:** Try our AI-powered security assistant at [workstation-five.vercel.app](https://workstation-five.vercel.app)

---

## 🎯 Who is this for?

- **Developers:** Get immediate security feedback without waiting for CI pipeline
- **SecOps:** Unified reports from multiple tools without glue code
- **Startups:** Enterprise-grade security features (SAST, SCA, Secrets) for free
- **Pentesters:** CLI-first automation for vulnerability discovery

---

## ⚡ Quick Start

Get running in 30 seconds. Works on **Linux/macOS/WSL**; Windows via PowerShell supported.

### 1. Install

```bash
pip install security-assistant

# Install required scanners (if not already present)
pip install bandit semgrep

# Note: Trivy and Nuclei must be installed separately
# See docs/installation.md for details
```

### 2. Scan

```bash
# Scan current directory
security-assistant scan .

# With specific scanners
security-assistant scan . --scanners bandit,semgrep,trivy

# With LLM explanations (bring your own API key)
export OPENAI_API_KEY=your_api_key_here
security-assistant scan . --llm openai
```

### 3. View Report

Open `security-reports/report.html` in your browser to see the interactive dashboard.

---

## 🚀 Key Features

### ✅ Available Now (v1.3.0)

| Feature | Description |
|---------|-------------|
| **Multi-Scanner Orchestration** | Bandit, Semgrep, Trivy, Nuclei (DAST) |
| **Intelligent Deduplication** | Merge identical findings across scanners |
| **Context Intelligence** | KEV (CISA), Reachability Analysis, FP Detection |
| **LLM Integration** | Explain vulns & suggest fixes (OpenAI, Anthropic, NVIDIA NIM) |
| **Auto-PoC Generation** | Template-based exploits for SQLi, XSS (experimental) |
| **CI/CD Ready** | SARIF for GitHub, JSON for GitLab Code Quality |
| **Output Formats** | JSON, HTML, Markdown, SARIF |

### 🚧 Roadmap

| Feature | Status |
|---------|--------|
| Web Dashboard (React) | 🔨 In Progress |
| GitHub Actions Plugin | 📋 Examples available |
| GitLab CI Plugin | 📋 Examples available |
| SIEM Integration | 🗓️ Planned Q2 2025 |

---

## 🏗️ How It Works

```
┌─────────────┐
│   Your Code │
└──────┬──────┘
       │
       v
┌─────────────────────────────────┐
│     Security Assistant Core     │
│  ┌───────────────────────────┐  │
│  │ Scanner Orchestration     │  │
│  │ (Parallel Execution)      │  │
│  └────────┬──────────────────┘  │
│           │                      │
│  ┌────────v──────────────────┐  │
│  │ Normalization & Dedup     │  │
│  └────────┬──────────────────┘  │
│           │                      │
│  ┌────────v──────────────────┐  │
│  │ Context Intelligence      │  │
│  │ - KEV (CISA)              │  │
│  │ - Reachability            │  │
│  │ - FP Detection            │  │
│  └────────┬──────────────────┘  │
│           │                      │
│  ┌────────v──────────────────┐  │
│  │ Optional: LLM Analysis    │  │
│  │ (BYOK - Your API Key)     │  │
│  └────────┬──────────────────┘  │
└───────────┼──────────────────────┘
            │
            v
   ┌────────────────┐
   │ HTML/JSON/SARIF│
   │    Reports     │
   └────────────────┘
```

---

## 🆚 Why Security Assistant?

| Feature | Standalone Tools | Security Assistant |
| :--- | :---: | :---: |
| **Unified Output** | ❌ Separate formats | ✅ Single JSON/HTML/SARIF |
| **Noise Reduction** | ❌ High | ✅ Low (Deduplication + FP Detection) |
| **Prioritization** | ❌ Severity only | ✅ Severity + **KEV** + **Reachability** |
| **Remediation** | ⚠️ Basic messages | ✅ **Code Examples** & Fix Templates |
| **Setup Time** | 🕒 Hours (configs, scripts) | ⚡ **Seconds** (one command) |
| **Price** | 💰 Varies | ✅ **$0** (OSS, MIT License) |

---

## 🤖 CI/CD Integration

### GitHub Actions

```yaml
name: Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install Security Assistant
        run: pip install security-assistant
      
      - name: Install Scanners
        run: |
          pip install bandit semgrep
          # Install Trivy (see docs/installation.md)
      
      - name: Run Scan
        run: security-assistant scan . --format sarif
      
      - name: Upload SARIF
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: security-reports/report.sarif
```

### GitLab CI

```yaml
security_scan:
  image: python:3.11
  script:
    - pip install security-assistant
    - security-assistant scan . --format json
  artifacts:
    reports:
      codequality: security-reports/report.json
```

More examples in [`docs/integrations/`](docs/integrations/).

---

## 📖 Documentation

- [Installation Guide](docs/installation.md)
- [Configuration Guide](docs/configuration.md)
- [Scanner Documentation](docs/scanners/)
- [CI/CD Integration Examples](docs/integrations/)
- [Product Roadmap](ROADMAP.md)

---

## 🤝 Contributing

We love contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Looking for something to do?

- [Good First Issues](https://github.com/AMEOBIUS/security-assistant/labels/good%20first%20issue)
- [Feature Requests](https://github.com/AMEOBIUS/security-assistant/issues?q=is%3Aissue+is%3Aopen+label%3Aenhancement)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

**Disclaimer:** This tool is for defensive security purposes only. Use responsibly.

---

## 🌟 Star History

If you find this useful, give us a star! ⭐

[![Star History Chart](https://api.star-history.com/svg?repos=AMEOBIUS/security-assistant&type=Date)](https://star-history.com/#AMEOBIUS/security-assistant&Date)

---

## 📬 Contact

- **Issues:** [GitHub Issues](https://github.com/AMEOBIUS/security-assistant/issues)
- **Discussions:** [GitHub Discussions](https://github.com/AMEOBIUS/security-assistant/discussions)
- **Website:** [workstation-five.vercel.app](https://workstation-five.vercel.app)

