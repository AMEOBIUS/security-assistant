# Bandit Scanner

[Bandit](https://github.com/PyCQA/bandit) is a tool designed to find common security issues in Python code.

## Configuration

In `security-assistant.yaml`:

```yaml
bandit:
  enabled: true
  severity_level: "medium" # Filter issues by severity
  confidence_level: "medium" # Filter issues by confidence
  exclude_dirs: ["tests", "venv"]
```

## Supported Checks

Bandit checks for various vulnerability classes:
- Hardcoded secrets/passwords
- SQL Injection
- Shell injection (subprocess, os.system)
- Weak cryptography
- Unsafe deserialization (pickle)
- Debug modes enabled

## False Positives

To suppress a specific warning in your code, add a `# nosec` comment:

```python
subprocess.check_call(['ls', '-l'])  # nosec
```
