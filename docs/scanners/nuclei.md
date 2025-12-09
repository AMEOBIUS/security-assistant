# Nuclei Scanner Integration

Security Assistant integrates with [ProjectDiscovery Nuclei](https://github.com/projectdiscovery/nuclei) to provide fast and customizable vulnerability scanning.

## Capabilities

- **DAST Scanning:** Scans live URLs for vulnerabilities.
- **Template-based:** Uses community-powered templates for latest CVEs.
- **Technology Detection:** Identifies stack technologies (Wappalyzer).

## Configuration

Add the following to your `security-assistant.yaml` or use environment variables:

```yaml
nuclei:
  enabled: true
  # Add custom templates or flags
  extra_args:
    - "-tags"
    - "cve,misconfig"
  severity:
    - "critical"
    - "high"
    - "medium"
  rate_limit: 150
```

### Environment Variables

- `SA_NUCLEI_ENABLED=true`
- `SA_NUCLEI_EXTRA_ARGS="-tags cve"`

## Usage

To scan a target URL:

```bash
security-assistant scan https://example.com --nuclei-only
```

Note: Nuclei requires the target to be a URL (`http://` or `https://`). Directory scans will skip Nuclei.

## Findings

Nuclei findings are mapped as follows:

| Nuclei Severity | Unified Severity |
|-----------------|------------------|
| critical        | CRITICAL         |
| high            | HIGH             |
| medium          | MEDIUM           |
| low             | LOW              |
| info            | INFO             |
| unknown         | INFO             |

## Installation

Ensure `nuclei` is installed and in your PATH:

```bash
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest
```
