# Reachability Analysis

Security Assistant includes a **Reachability Analysis** engine to reduce false positives in Software Composition Analysis (SCA) findings.

## What is Reachability Analysis?

Traditional SCA tools (like Trivy) detect vulnerabilities by checking if an installed library has known CVEs. However, just because a library is installed doesn't mean the vulnerable code is actually used by your application.

Reachability Analysis determines if the vulnerable part of a library is **reachable** from your application code.

## How It Works

1.  **Static Analysis (AST Parsing):** The engine parses your Python source code using the Abstract Syntax Tree (AST) module.
2.  **Import Tracking:** It identifies all third-party libraries imported in your project.
3.  **Usage Verification:**
    *   If a vulnerable library is **never imported**, the finding is marked as **Unreachable**.
    *   The priority score is reduced (e.g., by 50%), and the finding is flagged in reports.

## Usage

Reachability Analysis is enabled by default.

### CLI

To disable reachability analysis:

```bash
security-assistant scan . --no-reachability
```

### Reporting

In HTML reports, reachable findings are treated normally. Unreachable findings (where the library is installed but not imported) are logged and their priority score is lowered.

## Limitations (v1.0)

*   **Language Support:** Currently supports **Python** only.
*   **Granularity:** Checks for *module-level* imports. It does not yet verify if the specific vulnerable *function* within the library is called (Call Graph analysis is planned for v2.0).
*   **Dynamic Imports:** Libraries imported dynamically (e.g., `importlib.import_module`) may be missed.
