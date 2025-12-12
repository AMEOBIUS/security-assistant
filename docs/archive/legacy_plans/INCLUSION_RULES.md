# 📚 Documentation Inclusion Rules

## 🎯 Purpose

This document defines what gets included in the public `security-assistant` repository vs. what stays in the private `Workstation` repository.

## ✅ Public Content (OSS User-Facing)

### Required Files
- `README.md` - Project overview and quick start
- `LICENSE` - MIT license
- `CHANGELOG.md` - Release notes for OSS users
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Project metadata and build config

### Documentation Categories (All Allowed)
- **Installation & Setup**
  - `docs/installation.md`
  - `docs/quickstart.md`
  - `docs/troubleshooting.md`
  
- **User Guides**
  - `docs/guides/`/*` (user tutorials, best practices)
  - `docs/guides/cicd-integration.md`
  - `docs/guides/pentest.md`
  
- **Feature Documentation**
  - `docs/features/`/*` (LLM, scanners, reporting)
  - `docs/features/llm.md`
  - `docs/features/auto-poc.md`
  
- **Reference**
  - `docs/reference/`/*` (CLI, API, architecture)
  - `docs/reference/cli.md`
  - `docs/reference/orchestrator.md`
  
- **Integration Examples**
  - `docs/integrations/github_actions.md`
  - `docs/integrations/gitlab_ci.md`
- `docs/integrations/azure_pipelines.md`
  
- **Public Roadmaps**
  - `docs/roadmaps/ROADMAP_DEC_2025.md`
  - `docs/roadmaps/TIMELINE_2026.md`
  - `docs/roadmaps/OFFENSIVE_SECURITY_ROADMAP.md`
  
- **Technical Reference**
  - `docs/analysis/`/*` (reachability algorithm)
  - `docs/config-schema.json` (configuration format)

## ❌ Private Content (Internal Only)

### Never Include
- `docs/INTERNAL/` - Internal documentation
- `docs/deployment/` - WSL/Docker setup guides
- `docs/archive/` - Legacy documents
- `scripts/` with internal sync automation
- `/.agents/` - Agent configurations
- `checkpoints/` - Session tracking and reports
- `frontend/` - Marketing materials
- `backend/` - Enterprise implementation

### Remove Before Sync
1. All session reports and summaries
2. Internal meeting notes or strategies
3. API keys or secrets in any format
4. Personal development notes (unless clearly user-focused)
5. Internal tooling documentation
6. Roadmap discussions and planning documents

### Remove These Files (Examples)
```bash
# Internal process docs
docs/MCP_SETUP_GUIDE.md
docs/DEPLOYMENT_SUCCESS.md
docs/SESSION_XX_SUMMARY.md

# Marketing materials
docs/LAUNCH_PLAN.md
docs/MARKETING_PITCHES.md

# Internal tracking
checkpoints/session_XX.json
```

## 🔍 Quality Guidelines for Public Docs

### Content Standards
1. **User-Centric**: Write for actual users, not internal team members
2. **Version-Agnostic**: All examples work with current releases
3. **Clear Examples**: Code snippets should be copy-paste ready
4. **API Keys**: Never include real keys, use placeholders like `YOUR_API_KEY_HERE`

### Example of Good vs Bad
```markdown
# ✅ GOOD - User-focused, actionable
## Quick Start
```bash
pip install security-assistant
security-assistant scan .
```

# ❌ BAD - Internal jargon
# Internal Development Status
We're currently refactoring the scanner architecture
for better modularity and test-ability. Contact
@dev-team for details.
```

### Content Review Checklist Before Sync
- [ ] No hardcoded credentials or secrets
- [ ] All examples tested with current version
- [ ] No session numbers or internal IDs referenced
- [ ] No internal tooling or processes documented
- [ ] All URLs point to public resources
- [ ] All email addresses are public (GitHub Issues)

## 🚨 AI Agent Guidelines

When creating documentation for OSS users:

### ✅ DO Include
- Installation instructions
- Usage examples with realistic scenarios
- Feature explanations with practical benefits
- Troubleshooting for common issues
- Integration examples (CI/CD, IDE plugins)

### ❌ DON'T Include
- Internal development workflows
- Team-specific processes
- Metrics for internal performance
- Non-public feature requests
- Strategic planning or roadmaps (unless feature-ready)

## 📋 Template for New Documentation

```markdown
# [Feature Name]

## Overview
[Brief description for users]

## Quick Start
[Step-by-step guide]

## Configuration
[User-facing configuration]

## Examples
[Practical usage examples]

## Troubleshooting
[Common issues and solutions]

## See Also
[Related documentation links]
```

--- 

**Version:** 1.0.0  
**Last Updated:** 2025-12-10  
**Maintainer:** Development Team  
**Audience:** OSS Contributors
