# GitHub Issues to Create Manually

After pushing the code, create these issues on GitHub to attract contributors:

## Issue 1: Add ESLint Scanner Support
**Title:** [GOOD FIRST ISSUE] Add ESLint scanner for JavaScript/TypeScript security analysis  
**Labels:** `good first issue`, `enhancement`, `integrations`  
**Body:**
```markdown
## Description
Add support for ESLint with security-focused plugins (eslint-plugin-security, @typescript-eslint/eslint-plugin) to scan JavaScript and TypeScript projects.

## Why This Matters
Many projects use JavaScript/TypeScript, and Security Assistant currently only supports Python. Adding ESLint would make the tool useful for a much wider audience.

## Suggested Approach
1. Create `security_assistant/scanners/eslint_scanner.py` following the pattern in `bandit_scanner.py`
2. Implement ESLint execution with security rulesets
3. Parse ESLint JSON output and convert to our Finding format
4. Register the scanner in `orchestrator.py`
5. Add tests in `tests/scanners/test_eslint_scanner.py`

## Acceptance Criteria
- [ ] ESLint scanner class implemented
- [ ] Supports both JavaScript and TypeScript
- [ ] Converts ESLint findings to Security Assistant format
- [ ] Unit tests with >80% coverage
- [ ] Integration test with sample vulnerable JS code
- [ ] Documentation updated

## Resources
- ESLint JSON formatter: https://eslint.org/docs/latest/use/formatters/#json
- eslint-plugin-security: https://github.com/eslint-community/eslint-plugin-security
- Reference implementation: `security_assistant/scanners/bandit_scanner.py`

## Mentorship Available
Tag @AMEOBIUS for questions or guidance!
```

---

## Issue 2: Add Dark Mode to Web Dashboard
**Title:** [GOOD FIRST ISSUE] Implement dark mode toggle for web dashboard  
**Labels:** `good first issue`, `enhancement`, `web-dashboard`, `ui/ux`  
**Body:**
```markdown
## Description
Add a dark mode theme to the web dashboard with a toggle button to switch between light and dark modes.

## Why This Matters
Many developers prefer dark mode for reduced eye strain. This is a highly requested feature that improves user experience.

## Suggested Approach
1. Create CSS variables for colors in `web_dashboard/static/css/dashboard.css`
2. Add dark theme color palette
3. Create a theme toggle button in `web_dashboard/templates/base.html`
4. Implement JavaScript to toggle theme and save preference to localStorage
5. Apply theme on page load based on saved preference

## Acceptance Criteria
- [ ] Dark mode CSS implemented with proper contrast ratios
- [ ] Toggle button in dashboard header
- [ ] Theme preference persists across sessions (localStorage)
- [ ] All dashboard pages support dark mode
- [ ] Smooth transition between themes
- [ ] Respects system preference on first visit

## Resources
- CSS Variables: https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties
- Dark mode best practices: https://web.dev/prefers-color-scheme/
- Example implementation: https://github.com/GoogleChrome/dark-mode-toggle

## Mentorship Available
Tag @AMEOBIUS for questions or guidance!
```

---

## Issue 3: Add CSV Report Format
**Title:** [GOOD FIRST ISSUE] Add CSV export format for vulnerability reports  
**Labels:** `good first issue`, `enhancement`, `reporting`  
**Body:**
```markdown
## Description
Add support for exporting vulnerability reports in CSV format for easy import into spreadsheets and other tools.

## Why This Matters
Many security teams use spreadsheets for tracking and reporting. CSV export makes it easy to integrate Security Assistant into existing workflows.

## Suggested Approach
1. Create `security_assistant/reporting/csv_reporter.py` following the pattern in `json_reporter.py`
2. Implement CSV generation with proper escaping
3. Include columns: ID, Title, Severity, CWE, File, Line, Scanner, KEV Status, Reachability, etc.
4. Add CLI option `--format csv` in `cli.py`
5. Add tests in `tests/test_csv_reporter.py`

## Acceptance Criteria
- [ ] CSV reporter class implemented
- [ ] Proper CSV escaping for special characters
- [ ] All relevant finding fields included
- [ ] CLI integration working
- [ ] Unit tests with >80% coverage
- [ ] Documentation updated

## Resources
- Python CSV module: https://docs.python.org/3/library/csv.html
- Reference implementation: `security_assistant/reporting/json_reporter.py`
- CSV best practices: https://tools.ietf.org/html/rfc4180

## Mentorship Available
Tag @AMEOBIUS for questions or guidance!
```

---

## Issue 4: Improve Test Coverage for Reachability Analysis
**Title:** [GOOD FIRST ISSUE] Increase test coverage for reachability analyzer  
**Labels:** `good first issue`, `testing`  
**Body:**
```markdown
## Description
Add more test cases for the reachability analyzer, especially edge cases like circular imports, dynamic imports, and complex call graphs.

## Why This Matters
Reachability analysis is a critical feature that reduces false positives. Better test coverage ensures it works correctly in all scenarios.

## Current Status
- Current coverage: ~75%
- Target coverage: 90%+

## Suggested Approach
1. Review `security_assistant/analysis/reachability/` modules
2. Identify untested code paths using `pytest --cov`
3. Add test cases in `tests/analysis/test_reachability.py`
4. Focus on edge cases:
   - Circular imports
   - Dynamic imports (`importlib`, `__import__`)
   - Conditional imports
   - Star imports (`from module import *`)
   - Nested function calls

## Acceptance Criteria
- [ ] Test coverage increased to 90%+
- [ ] All edge cases covered
- [ ] Tests are well-documented
- [ ] No regression in existing tests

## Resources
- pytest-cov: https://pytest-cov.readthedocs.io/
- Existing tests: `tests/analysis/test_reachability.py`
- Reachability analyzer: `security_assistant/analysis/reachability/`

## Mentorship Available
Tag @AMEOBIUS for questions or guidance!
```

---

## Issue 5: Create Video Tutorial
**Title:** [HELP WANTED] Record a video tutorial for Security Assistant  
**Labels:** `help wanted`, `documentation`, `marketing`  
**Body:**
```markdown
## Description
Create a 5-10 minute video tutorial showing how to install, configure, and use Security Assistant.

## Why This Matters
Video tutorials are highly effective for onboarding new users. This will help grow the community and make the tool more accessible.

## Content to Cover
1. **Installation** (1-2 min)
   - Show `pipx install` or `pip install`
   - Verify installation with `security-assistant --version`

2. **First Scan** (2-3 min)
   - Clone a sample vulnerable project
   - Run `security-assistant scan`
   - Show progress and output

3. **Viewing Reports** (2-3 min)
   - Open HTML report in browser
   - Explain severity levels, KEV enrichment, reachability
   - Show how to filter and sort findings

4. **CI/CD Integration** (2-3 min)
   - Show GitHub Actions or GitLab CI example
   - Explain how to configure thresholds
   - Show automated security checks in action

## Deliverables
- [ ] Video uploaded to YouTube
- [ ] Link added to README.md
- [ ] Thumbnail image created
- [ ] Video description includes links to repo and docs

## Tools
- Screen recording: OBS Studio, Loom, or QuickTime
- Video editing: DaVinci Resolve (free), iMovie, or Camtasia
- Thumbnail: Canva

## Mentorship Available
Tag @AMEOBIUS for questions or guidance!
```

---

## How to Create These Issues

1. Go to: https://github.com/AMEOBIUS/security-assistant/issues/new/choose
2. Select the appropriate template (Feature Request or Good First Issue)
3. Copy the title and body from above
4. Add the specified labels
5. Submit the issue

Alternatively, use GitHub CLI:
```bash
gh issue create --title "[GOOD FIRST ISSUE] Add ESLint scanner" --body "..." --label "good first issue,enhancement,integrations"
```
