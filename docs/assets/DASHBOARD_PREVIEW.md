# Security Assistant Dashboard - Preview

```
┌─────────────────────────────────────────────────────────────────────┐
│  🛡️ Security Assistant Report                                      │
│  Generated: 2024-12-08 20:45:32 | Target: ./examples               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📊 Summary                                                         │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐          │
│  │   Total  │ Critical │   High   │  Medium  │   Low    │          │
│  │    42    │    5     │    12    │    18    │    7     │          │
│  └──────────┴──────────┴──────────┴──────────┴──────────┘          │
│                                                                     │
│  🎯 Intelligence                                                    │
│  • KEV Enriched: 2 findings (actively exploited)                   │
│  • Unreachable: 8 findings (not imported)                          │
│  • False Positives: 5 findings (test code)                         │
│  • Actionable: 27 findings                                         │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  🔍 Top Priority Findings                                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  🔴 CRITICAL | SQL Injection in auth.py:42                          │
│  ├─ Scanner: Semgrep                                                │
│  ├─ CWE-89 | Priority: 95/100                                      │
│  ├─ ⚠️ KEV: Actively exploited in the wild                         │
│  ├─ ✅ Reachable: Function called from main()                      │
│  └─ 📝 Remediation: Use parameterized queries [View Code Example]  │
│                                                                     │
│  🔴 CRITICAL | Hardcoded AWS Credentials in config.py:15           │
│  ├─ Scanner: Trivy (Secrets)                                        │
│  ├─ Priority: 92/100                                                │
│  ├─ ✅ Reachable: File in production path                          │
│  └─ 📝 Remediation: Use environment variables [View Example]       │
│                                                                     │
│  🟠 HIGH | Path Traversal in upload.py:28                           │
│  ├─ Scanner: Bandit                                                 │
│  ├─ CWE-22 | Priority: 78/100                                      │
│  ├─ ✅ Reachable: Endpoint is exposed                              │
│  └─ 📝 Remediation: Validate and sanitize paths [View Example]     │
│                                                                     │
│  🟡 MEDIUM | Weak Cryptography in utils.py:156                      │
│  ├─ Scanner: Semgrep                                                │
│  ├─ CWE-327 | Priority: 65/100                                     │
│  ├─ ❌ Unreachable: Module not imported (downgraded)               │
│  └─ 📝 Remediation: Use cryptography.fernet [View Example]         │
│                                                                     │
│  🟢 LOW | Debug Mode Enabled in app.py:8                            │
│  ├─ Scanner: Bandit                                                 │
│  ├─ Priority: 45/100                                                │
│  ├─ 🤔 Possible FP: Detected in test configuration                 │
│  └─ 📝 Remediation: Disable debug in production                    │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  📈 Breakdown by Scanner                                            │
│  • Bandit: 15 findings (Python SAST)                                │
│  • Semgrep: 18 findings (Multi-language SAST)                       │
│  • Trivy: 9 findings (Dependencies + Secrets)                       │
│                                                                     │
│  ⏱️ Execution Time: 12.3s                                           │
│  🔄 Duplicates Removed: 15                                          │
└─────────────────────────────────────────────────────────────────────┘

Interactive Features:
✓ Filter by severity, scanner, or KEV status
✓ Sort by priority score, file, or date
✓ Expand findings to see full code context
✓ Copy remediation code examples
✓ Export filtered results
```

This is a text representation. The actual HTML report includes:
- Interactive tables with sorting/filtering
- Syntax-highlighted code snippets
- Clickable remediation examples
- Responsive design
- Dark mode support (coming soon)
