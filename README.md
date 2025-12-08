# 🛡️ Security Workstation

**Open-source CLI security scanner orchestrator with GitLab-level intelligence**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Security Workstation** is a CLI-first vulnerability scanner orchestrator that combines multiple security tools (Bandit, Semgrep, Trivy) with intelligent analysis features typically found in enterprise platforms like GitLab Ultimate.

It goes beyond simple scanning by adding **Context Intelligence**:
- 🧠 **KEV Enrichment**: Prioritizes vulnerabilities actively exploited in the wild (CISA KEV).
- 📉 **False Positive Detection**: Automatically filters out test code, mock data, and safe contexts.
- 🕸️ **Reachability Analysis**: Downgrades vulnerabilities in libraries that are installed but not imported.
- 📊 **Unified Reporting**: Generates HTML, JSON, and SARIF reports with remediation guidance.

---

## ⚡ Quick Start

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/AMEOBIUS/Workstation.git
cd workstation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install scanners (optional but recommended)
pip install bandit semgrep
# Note: Trivy must be installed separately (see docs/installation.md)
```

### Running a Scan

```bash
# Basic scan of current directory
python -m security_assistant.cli scan .

# Scan specific target with HTML report
python -m security_assistant.cli scan src/ --format html --output-dir reports

# Scan without reachability analysis (faster)
python -m security_assistant.cli scan . --no-reachability
```

### Viewing Results

Open `reports/report.html` in your browser to view the interactive dashboard.

---

## 🚀 Key Features

### 1. Intelligent Orchestration
Runs multiple scanners in parallel and deduplicates findings.
- **Bandit**: Python SAST
- **Semgrep**: Multi-language SAST
- **Trivy**: Container & Dependency SCA

### 2. Contextual Analysis
- **KEV Integration**: Checks CISA's Known Exploited Vulnerabilities catalog. If a CVE is active, priority is boosted to **CRITICAL**.
- **False Positive Detection**: Uses heuristics to identify findings in test files (`tests/*`), mock data, or sanitized inputs.
- **Reachability Analysis**: Analyzes Python AST and imports to determine if a vulnerable dependency is actually used.

### 3. Unified Reporting
- **Formats**: HTML (interactive), JSON, SARIF (CI/CD friendly), Markdown.
- **Remediation**: Provides tailored fix advice and code examples.

---

## 📊 Web Dashboard

A lightweight web dashboard is included for visualizing scan history.

```bash
# Start the dashboard
cd web_dashboard
pip install -r requirements.txt
cd backend
python main.py
# Open frontend/index.html
```

---

## 📚 Documentation

- [Installation Guide](docs/installation.md)
- [Configuration Guide](docs/configuration.md) (with JSON Schema support)
- [Scanner Documentation](docs/scanners/)
- [CI/CD Integration](docs/integrations/)

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Disclaimer**: This tool is for defensive security purposes only. Use responsibly.

