# Pre-commit Hooks Guide

Security Assistant provides pre-commit hooks to automatically scan your code for vulnerabilities before you commit.

## 🚀 Quick Start

1. **Install Hooks**
   ```bash
   python scripts/install_hooks.py
   ```

2. **Verify Installation**
   ```bash
   pre-commit run --all-files
   ```

## ⚙️ Configuration

The hooks are configured in `.pre-commit-hooks.yaml`. You can add this to your project's `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/AMEOBIUS/security-assistant
    rev: v1.3.0
    hooks:
      - id: security-assistant
```

## 🛡️ Available Hooks

| Hook ID | Description | Speed | Scanners |
|---------|-------------|-------|----------|
| `security-assistant` | Fast scan for staged files | <5s | Bandit (Python) |
| `security-assistant-full` | Full deep scan | Slow | Bandit, Semgrep, Trivy, Nuclei |

##  bypassing Hooks

If you need to commit code that fails security checks (e.g., for testing), use:

```bash
git commit -m "wip" --no-verify
```

## 🔧 Customizing the Scan

You can override arguments in your `.pre-commit-config.yaml`:

```yaml
- id: security-assistant
  args: ["--preset", "full", "--fail-on-high"]
```
