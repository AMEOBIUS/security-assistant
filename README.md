# Security Assistant

🛡️ Open-source CLI security scanner orchestrator

## Features

- **Multi-Scanner Support**: Bandit, Semgrep, Trivy
- **Intelligence Features**: KEV enrichment, False Positive Detection, Reachability Analysis
- **Unified Reporting**: HTML, JSON, SARIF, Markdown
- **CI/CD Ready**: GitLab CI, GitHub Actions integration

## Quick Start

```bash
pip install -e .
security-assistant configure
security-assistant scan .
```

## Installation

```bash
git clone https://github.com/AMEOBIUS/security-assistant.git
cd security-assistant
pip install -r requirements.txt
pip install -e .
```

## Usage

### Basic Scan
```bash
security-assistant scan /path/to/project
```

### With Specific Scanner
```bash
security-assistant scan . --scanner bandit
security-assistant scan . --scanner semgrep
security-assistant scan . --scanner trivy
```

### Generate Reports
```bash
security-assistant scan . --output-format html
security-assistant scan . --output-format json
```

## Documentation

- [Quick Start Guide](docs/guides/quick-start.md)
- [Configuration](docs/configuration.md)
- [CI/CD Integration](docs/guides/cicd-integration.md)
- [API Reference](docs/reference/api.md)
- [Architecture](docs/reference/architecture.md)

## Features in Detail

### Multi-Scanner Orchestration
Unified interface for multiple security scanners:
- **Bandit**: Python SAST
- **Semgrep**: Multi-language SAST
- **Trivy**: Container & dependency scanning

### Intelligent Analysis
- **KEV Enrichment**: CISA Known Exploited Vulnerabilities
- **False Positive Detection**: ML-based filtering
- **Reachability Analysis**: Code path analysis
- **EPSS Scoring**: Exploit prediction

### GitLab Integration
- Automatic issue creation
- Pipeline integration
- Security dashboard support

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

## License

MIT License - see [LICENSE](LICENSE)

## Community Edition

This is the Community Edition (Open Core Model). Enterprise features available separately.

## Support

- [Documentation](docs/)
- [Issue Tracker](https://github.com/AMEOBIUS/security-assistant/issues)
- [Discussions](https://github.com/AMEOBIUS/security-assistant/discussions)
