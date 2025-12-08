# Installation Guide

## Prerequisites

- Python 3.11+
- pip (Python package manager)
- Git (for repository scanning)
- [Optional] Docker (for containerized execution)

## Standard Installation

Install via pip:

```bash
pip install security-assistant
```

## Development Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/your-org/security-assistant.git
cd security-assistant
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

pip install -e .
```

## Scanner Dependencies

Security Assistant orchestrates multiple scanners. While it can install python-based scanners (Bandit, Semgrep), some may require system-level installation.

### Trivy (Container & Dependency Scanning)

**Linux/Mac:**
```bash
curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
```

**Windows:**
Download the binary from [Trivy Releases](https://github.com/aquasecurity/trivy/releases).

### Semgrep

```bash
pip install semgrep
```

### Bandit

```bash
pip install bandit
```
