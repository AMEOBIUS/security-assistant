# Natural Language Queries

Security Assistant allows you to filter and explore scan results using plain English queries.

## Usage

```bash
security-assistant query "YOUR QUERY HERE"
```

## Examples

### Filtering by Severity
> "Show me all critical vulnerabilities"
> "List high severity issues"

### Filtering by Type
> "Find SQL injections"
> "Show me secrets found by Trivy"

### Filtering by File
> "What issues are in app.py?"
> "Count findings in src/"

### Statistics
> "How many critical issues?"
> "Count findings by severity"

## How it works

1.  **Parsing**: Your query is parsed by an LLM (if enabled) or a heuristic engine to extract intents (`find`, `count`) and filters (`severity`, `file`, `scanner`).
2.  **Execution**: The filters are applied to the `scan-results.json` file.
3.  **Result**: The tool prints the matching findings or statistics.

## Configuration

Requires an LLM provider for best results (NVIDIA, OpenAI, Anthropic).

```bash
export SA_LLM__PROVIDER=nvidia
export SA_LLM__API_KEY=nvapi-...
```

If no LLM is configured, a basic Regex-based parser is used (supports simple queries like "critical findings").
