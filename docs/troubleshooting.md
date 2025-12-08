# Troubleshooting Guide

## Common Issues

### "Trivy is not installed"

**Error:** `Scan failed: Trivy is not installed.`

**Solution:**
Security Assistant does not bundle the Trivy binary. You must install it separately.
See [Installation Guide](../installation.md) for instructions.

### "Semgrep failed with exit code 2"

**Error:** `[ERROR]: Cannot create auto config when metrics are off.`

**Solution:**
This usually happens in CI environments or when running without internet access.
Try creating a `.semgrepignore` file or specifying explicit rules in `security-assistant.yaml`:
```yaml
semgrep:
  config: ["p/security-audit"]
```

### "Bandit failed to parse output"

**Error:** `Failed to parse Bandit output: Expecting value...`

**Solution:**
This can happen if Bandit crashes or outputs non-JSON data.
Run with `-v` (verbose) to see the raw output:
```bash
security-assistant scan . -v
```

### Permission Denied (Docker)

**Error:** `permission denied` when accessing files.

**Solution:**
Ensure the user running the scan has read access to the target directory.
In Docker, you may need to run as the correct user UID:
```bash
docker run -v $(pwd):/app -u $(id -u):$(id -g) security-assistant
```
