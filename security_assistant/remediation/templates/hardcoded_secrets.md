# Hardcoded Secrets Remediation

## Description
Storing sensitive information such as passwords, API keys, or cryptographic secrets directly in source code increases the risk of exposure if the code is shared or leaked.

## Remediation
1. **Environment Variables**: Store secrets in environment variables and access them via `os.environ`.
2. **Secrets Management**: Use a dedicated secrets management service (e.g., HashiCorp Vault, AWS Secrets Manager).
3. **Configuration Files**: Use external configuration files that are not committed to version control.
4. **Scan Pre-Commit**: Use tools like `git-secrets` or `trufflehog` to detect secrets before committing.
