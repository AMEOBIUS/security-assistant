# Screenshot Guide for README

## What to Screenshot

Take a screenshot of the **interactive HTML report** to add visual appeal to the README.

### Recommended Location
Add the screenshot right after the "Quick Start" section, before "How It Works":

```markdown
### 3. View Report
Open `security-reports/report.html` in your browser to see the interactive dashboard.

![Security Assistant Dashboard](docs/assets/dashboard-screenshot.png)
*Interactive HTML report with KEV enrichment, reachability analysis, and remediation guidance*
```

## How to Create the Screenshot

### 1. Generate a Sample Report
```bash
# Scan a real project (or use examples/vulnerable_code.py)
cd examples
security-assistant scan vulnerable_code.py --output ../security-reports
```

### 2. Open in Browser
```bash
# Open the HTML report
start security-reports/report.html  # Windows
open security-reports/report.html   # macOS
xdg-open security-reports/report.html  # Linux
```

### 3. Take Screenshot
- **Zoom level:** 80-90% (to fit more content)
- **Window size:** 1920x1080 or larger
- **Focus on:**
  - Summary cards (Total Findings, Critical, High, etc.)
  - Vulnerability table with KEV/Reachability badges
  - One expanded finding showing remediation advice

### 4. Sanitize
- **Remove** any sensitive data (real file paths, internal URLs)
- **Blur** or replace with generic names if needed
- **Crop** to focus on the dashboard (remove browser chrome if possible)

### 5. Optimize
```bash
# Compress the image
pngquant dashboard-screenshot.png --output docs/assets/dashboard-screenshot.png
# Or use online tools: tinypng.com, squoosh.app
```

### 6. Add to README
Place the image in `docs/assets/` and reference it in README.md:

```markdown
![Security Assistant Dashboard](docs/assets/dashboard-screenshot.png)
```

## Alternative: Use a GIF

For extra impact, create a short GIF showing:
1. Running the scan command
2. Opening the HTML report
3. Filtering by severity
4. Expanding a finding to see remediation

**Tools:**
- **Windows:** ScreenToGif
- **macOS:** Kap, LICEcap
- **Linux:** Peek, SimpleScreenRecorder

**Max size:** 5MB (GitHub limit)

## Example Layout

```
┌─────────────────────────────────────────────────────────┐
│  Security Assistant Report                             │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐                      │
│  │ 42  │ │  5  │ │ 12  │ │ 25  │                      │
│  │Total│ │Crit │ │High │ │Med  │                      │
│  └─────┘ └─────┘ └─────┘ └─────┘                      │
│                                                         │
│  ┌───────────────────────────────────────────────────┐ │
│  │ ID  │ Title              │ Severity │ KEV │ Reach │ │
│  ├─────┼────────────────────┼──────────┼─────┼───────┤ │
│  │ 001 │ SQL Injection      │ CRITICAL │ ✓   │ ✓     │ │
│  │ 002 │ Hardcoded Secret   │ HIGH     │ ✗   │ ✓     │ │
│  │ 003 │ Path Traversal     │ MEDIUM   │ ✗   │ ✗     │ │
│  └─────┴────────────────────┴──────────┴─────┴───────┘ │
│                                                         │
│  ▼ SQL Injection in auth.py:42                         │
│    CWE-89 | Detected by: Semgrep                       │
│    ⚠️ KEV: Actively exploited in the wild              │
│    ✅ Reachable: Function is called from main()        │
│                                                         │
│    Remediation:                                         │
│    Use parameterized queries instead of string concat. │
│    [View Code Example]                                  │
└─────────────────────────────────────────────────────────┘
```

## Next Steps

After adding the screenshot:
1. Sync to public repo: `python scripts/sync_to_public.py`
2. Commit: `git commit -m "Docs: Add dashboard screenshot to README"`
3. Push: `git push origin main`
