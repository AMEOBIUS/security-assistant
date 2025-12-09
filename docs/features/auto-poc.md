# Auto-PoC Generation

Security Assistant can automatically generate Proof-of-Concept (PoC) exploits for detected vulnerabilities. This helps security engineers and developers verify if a finding is actually exploitable (True Positive) or just a theoretical risk.

## How it works

1.  **Detection**: Scanners (Bandit, Semgrep, etc.) find a vulnerability (e.g., SQL Injection in `app.py`).
2.  **Analysis**: The system analyzes the code snippet. If LLM integration is enabled (NVIDIA/OpenAI), it extracts:
    *   Target URL path
    *   Vulnerable parameter names
    *   HTTP Method (GET/POST)
3.  **Generation**: A safe Python or HTML exploit is generated from a template (`sqli.py.j2`, `xss.html.j2`).
4.  **Safety Check**: The generated code is scanned for destructive commands (`rm -rf`, `DROP TABLE`) before being saved.

## Usage

### Generate PoC for a specific finding

First, run a scan to get finding IDs:
```bash
security-assistant scan .
```

Then generate a PoC for a finding ID (e.g., `bandit-b601-main.py-42`):
```bash
security-assistant poc bandit-b601-main.py-42
```

### Save to specific file

```bash
security-assistant poc bandit-b601-main.py-42 --output exploit.py
```

### Run the PoC

```bash
python3 exploit.py http://localhost:8000
```

## Supported Vulnerabilities

| Vulnerability Type | PoC Type | Template |
|--------------------|----------|----------|
| SQL Injection      | Python   | `sqli.py` |
| XSS (Reflected)    | HTML     | `xss.html` |
| Command Injection  | Python   | `cmdi.py` |
| Path Traversal     | Python   | `traversal.py` |

## Safety Mechanisms

The Auto-PoC engine includes a **Safety Checker** that blocks:
- Filesystem deletion (`rm`, `del`)
- System shutdown/reboot
- Fork bombs
- Database destruction (`DROP TABLE`)

If an LLM suggests a dangerous payload, it is sanitized (e.g., `DROP TABLE` becomes `SELECT 1`).
