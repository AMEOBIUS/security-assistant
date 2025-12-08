# Semgrep Scanner

[Semgrep](https://semgrep.dev/) is a fast, open-source, static analysis engine for finding bugs and enforcing code standards.

## Configuration

In `security-assistant.yaml`:

```yaml
semgrep:
  enabled: true
  rules: ["auto"] # "auto" uses the default security ruleset
  # rules: ["p/security-audit", "p/secrets"]
  exclude_rules: []
```

## Features

- **Multi-language support**: Python, JavaScript, TypeScript, Go, Java, etc.
- **Semantic Analysis**: Understands code structure, not just regex.
- **Custom Rules**: Can run custom rules defined in YAML.

## Rulesets

Security Assistant defaults to the `auto` config which includes:
- `p/security-audit`
- `p/secrets`
- `p/owasp-top-ten`
