# Product Roadmap

This document outlines the development plan for **Security Assistant**.
Our goal is to bring enterprise-grade security orchestration to every developer's workstation.

## ✅ Completed (v1.3.0)

### Core Platform
- [x] **Unified Orchestration**: Parallel execution of Bandit, Semgrep, Trivy, and Nuclei.
- [x] **Context Intelligence**: KEV enrichment, Reachability analysis, and Heuristic FP detection.
- [x] **Reporting**: Interactive HTML dashboard and standardized JSON/SARIF output.

### Advanced Features
- [x] **LLM Integration**: Support for NVIDIA NIM, OpenAI, and Anthropic for vulnerability explanation.
- [x] **Auto-PoC Engine**: Automatic generation of safe Proof-of-Concept exploits (SQLi, XSS).
- [x] **Natural Language CLI**: Query findings using plain English (e.g., "Show me critical SQL injections").

---

## 🚧 Short-term Goals (v1.4 - v1.5)

### Expanded Scanner Support
- [x] **OWASP ZAP**: Integration for DAST web scanning.
- [x] **Gitleaks**: Dedicated secret scanning integration.
- [x] **Checkov**: IaC (Infrastructure as Code) security scanning.
- [x] **Nuclei**: Web vulnerability discovery and exploitation testing.

### Developer Experience
- [ ] **VS Code Extension**: View findings directly in the editor.
- [ ] **Pre-commit Hooks**: Official hooks for blocking bad commits locally.
- [ ] **Config UI**: Web-based configuration generator.

---

## 🔮 Long-term Vision (v2.0+)

### Enterprise Features
- [ ] **SaaS Dashboard**: Centralized view for multiple repositories/teams.
- [ ] **RBAC & SSO**: Enterprise authentication and role management.
- [ ] **Compliance Mapping**: Map findings to SOC2, ISO27001, and HIPAA controls.
- [ ] **Custom Policies**: Rego-based policy engine for advanced governance.

### AI & Automation
- [ ] **Auto-Fix PRs**: Automatically open Pull Requests with generated fixes.
- [ ] **Agentic Security**: Autonomous security agent that can investigate and patch vulnerabilities.

---

*Note: Timelines and priorities are subject to change based on community feedback. Feel free to open a [Feature Request](https://github.com/AMEOBIUS/security-assistant/issues/new?template=feature_request.md) to influence the roadmap.*
