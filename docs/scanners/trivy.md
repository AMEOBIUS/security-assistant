# Trivy Scanner

[Trivy](https://github.com/aquasecurity/trivy) is a comprehensive security scanner for vulnerabilities in container images, file systems, and git repositories.

## Configuration

In `security-assistant.yaml`:

```yaml
trivy:
  enabled: true
  severity: ["CRITICAL", "HIGH"]
  scanners: ["vuln", "secret", "config"]
  skip_dirs: ["node_modules", "venv"]
```

## Capabilities

1. **Vulnerability Scanning (SCA)**
   - Checks package dependencies (pip, npm, maven, etc.) against CVE databases.
   
2. **Secret Scanning**
   - Detects hardcoded secrets, keys, and tokens in files.

3. **Misconfiguration Scanning (IaC)**
   - Checks Dockerfiles, Kubernetes configs, and Terraform files for security best practices.
