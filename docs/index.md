# Security Assistant Documentation

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](../LICENSE)
[![Code Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen.svg)](../tests/)

**Security Assistant** is a comprehensive security scanning orchestrator that integrates multiple security tools (Bandit, Semgrep, Trivy) with GitLab issue management and CI/CD pipelines.

## 📚 Documentation Index

### Getting Started
- [User Guide](user-guide.md) - Complete guide for end users
- [Quick Start](quick-start.md) - Get up and running in 5 minutes
- [Installation](installation.md) - Detailed installation instructions

### Configuration
- [Configuration Guide](configuration.md) - All configuration options
- [Environment Variables](environment-variables.md) - Environment variable reference
- [Scanner Configuration](scanner-configuration.md) - Configure individual scanners

### Integration
- [CI/CD Integration](cicd-integration.md) - GitLab, GitHub, Jenkins setup
- [GitLab Integration](gitlab-integration.md) - Issue creation and management
- [API Usage](api-reference.md) - Programmatic usage

### Advanced Topics
- [Architecture](architecture.md) - System design and components
- [Best Practices](best-practices.md) - Recommendations and guidelines
- [Troubleshooting](troubleshooting.md) - Common issues and solutions
- [Migration Guide](migration-guide.md) - Upgrade and migration paths

### Reference
- [API Reference](api-reference.md) - Complete API documentation
- [CLI Reference](cli-reference.md) - Command-line interface
- [FAQ](faq.md) - Frequently asked questions

## 🎯 Quick Links

### For Users
- **First time?** → [Quick Start](quick-start.md)
- **Need help?** → [Troubleshooting](troubleshooting.md)
- **Common questions?** → [FAQ](faq.md)

### For Developers
- **API usage?** → [API Reference](api-reference.md)
- **Architecture?** → [Architecture](architecture.md)
- **Best practices?** → [Best Practices](best-practices.md)

### For DevOps
- **CI/CD setup?** → [CI/CD Integration](cicd-integration.md)
- **Configuration?** → [Configuration Guide](configuration.md)
- **GitLab integration?** → [GitLab Integration](gitlab-integration.md)

## 🚀 Quick Example

```bash
# Install
pip install -e .

# Run scan
security-assistant scan /path/to/code

# Generate report
security-assistant report --format html

# Create GitLab issues
security-assistant scan --create-issues
```

## 📊 Features

- **Multi-Scanner Support**: Bandit, Semgrep, Trivy
- **Intelligent Deduplication**: 3 strategies (strict, fuzzy, location-based)
- **GitLab Integration**: Automatic issue creation with priority filtering
- **Multiple Report Formats**: HTML, Markdown, JSON, SARIF, GitLab SAST
- **CI/CD Ready**: Templates for GitLab CI, GitHub Actions, Jenkins
- **Flexible Configuration**: YAML, JSON, environment variables
- **CLI & API**: Use as command-line tool or Python library

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Security Assistant                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    Bandit    │  │   Semgrep    │  │    Trivy     │  │
│  │   Scanner    │  │   Scanner    │  │   Scanner    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │          │
│         └──────────────────┼──────────────────┘          │
│                            │                             │
│                   ┌────────▼────────┐                    │
│                   │  Orchestrator   │                    │
│                   │  - Deduplication│                    │
│                   │  - Prioritization│                   │
│                   └────────┬────────┘                    │
│                            │                             │
│         ┌──────────────────┼──────────────────┐          │
│         │                  │                  │          │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐  │
│  │   Reports    │  │    GitLab    │  │     CLI      │  │
│  │ HTML/MD/JSON │  │    Issues    │  │   Interface  │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 📈 Project Status

- **Version**: 1.0.0
- **Status**: Production Ready
- **Test Coverage**: 95%+
- **Scanners**: 3 integrated
- **CI/CD Platforms**: 3 supported
- **Report Formats**: 5 available

## 🤝 Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

## 📝 License

MIT License - see [LICENSE](../LICENSE) for details.

## 🔗 Related Projects

- [Bandit](https://github.com/PyCQA/bandit) - Python security scanner
- [Semgrep](https://semgrep.dev/) - Static analysis tool
- [Trivy](https://trivy.dev/) - Vulnerability scanner
- [GitLab](https://gitlab.com/) - DevOps platform

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/security-assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/security-assistant/discussions)
- **Email**: security-assistant@example.com
