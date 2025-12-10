# Nuclei Scanner Integration

Security Assistant integrates with [ProjectDiscovery Nuclei](https://github.com/projectdiscovery/nuclei) to provide fast and customizable vulnerability scanning.

## Capabilities

- **DAST Scanning:** Scans live URLs for vulnerabilities.
- **Template-based:** Uses community-powered templates for latest CVEs.
- **Technology Detection:** Identifies stack technologies (Wappalyzer).
- **Custom Templates:** Support for custom templates via configuration.

## Configuration

Add the following to your `security-assistant.yaml` or use environment variables:

```yaml
nuclei:
  enabled: true
  
  # Templates to use (optional)
  templates:
    - "cves/"
    - "vulnerabilities/"
    - "technologies/tech-detect.yaml"
    
  # Filter by severity
  severity:
    - "critical"
    - "high"
    - "medium"
    
  # Performance settings
  rate_limit: 150
  
  # Advanced arguments
  extra_args:
    - "-tags"
    - "cve,misconfig"
    - "-retries"
    - "1"
```

### Environment Variables

- `SA_NUCLEI_ENABLED=true`
- `SA_NUCLEI_EXTRA_ARGS="-tags cve"`

## Usage

To scan a target URL:

```bash
security-assistant scan https://example.com --nuclei-only
```

To run as part of a full scan (will only activate if target is a URL):

```bash
security-assistant scan https://example.com --preset full
```

Note: Nuclei requires the target to be a URL (`http://` or `https://`). Directory scans will skip Nuclei automatically.

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
