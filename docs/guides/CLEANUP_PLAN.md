# 🧹 Repository Cleanup - Session 25

## 🎯 Goal
Clean up repository structure for better navigation and handoff to next AI agent.

---

## 📁 Proposed Structure

```
C:\Workstation\
├── .agents/                    # Agent configuration
├── .github/                    # GitHub workflows
├── .gitlab/                    # GitLab CI
├── backend/                    # FastAPI backend ✅
├── frontend/                   # Landing page ✅
├── security_assistant/         # Core scanner code ✅
├── tests/                      # All tests ✅
├── scripts/                    # Utility scripts ✅
├── checkpoints/                # Session checkpoints ✅
├── docs/                       # Documentation
│   ├── sessions/              # Session summaries (NEW)
│   ├── guides/                # How-to guides ✅
│   ├── roadmaps/              # Strategic plans (NEW)
│   └── deployment/            # Deployment guides (NEW)
├── config/                     # Configuration files ✅
├── templates/                  # Report templates ✅
├── examples/                   # Example code ✅
├── README.md                   # Main readme ✅
├── CHANGELOG.md               # Version history ✅
└── LICENSE                    # License ✅
```

---

## 🗑️ Files to Move/Delete

### Move to docs/sessions/:
```
SESSION_23_DESIGN_COMPLETE.md
SESSION_23_FINAL.md
SESSION_23_SUMMARY.md
SESSION_24_COMPLETE.md
START_HERE_SESSION_22.md
START_HERE_SESSION_24.md
```

### Move to docs/deployment/:
```
AFTER_REBOOT.md
AFTER_WSL_INSTALL.md
DEPLOY_NOW.md
DEPLOYMENT_SUCCESS.md
DOCKER_SOLUTION.md
PODMAN_CLI_FIX.md
PODMAN_PROPER_INSTALL.md
READY_TO_DEPLOY.md
TEST_INTEGRATION.md
КАК_ПОСМОТРЕТЬ.md
```

### Move to docs/roadmaps/:
```
🎯 Security Workstation v2.0.0 - Production Roadmap.md
🚀 Security Workstation Evolution - Dec 2025.md
```

### Move to docs/guides/:
```
QUICK_START.md
COMMIT_COMMANDS.md
RECOMMENDED_SETUP.md
```

### Delete (temporary/obsolete):
```
ALL_FIXES_COMPLETE.md
SARIF_UPLOAD_FIX.md
SECURITY_FIXES_COMPLETE.md
SECURITY_SCAN_FIXES.md
SECURITY_SCAN_INDEX.md
SECURITY_SCAN_README.md
SECURITY_SCAN_SUMMARY.md
SECURITY_WORKFLOWS_GUIDE.md
deploy.bat (move to scripts/)
```

---

## 📋 Cleanup Script

Create: `scripts/cleanup_repo.py`

```python
import os
import shutil

# Define moves
moves = {
    'docs/sessions/': [
        'SESSION_23_DESIGN_COMPLETE.md',
        'SESSION_23_FINAL.md',
        'SESSION_23_SUMMARY.md',
        'SESSION_24_COMPLETE.md',
        'START_HERE_SESSION_22.md',
        'START_HERE_SESSION_24.md',
    ],
    'docs/deployment/': [
        'AFTER_REBOOT.md',
        'AFTER_WSL_INSTALL.md',
        'DEPLOY_NOW.md',
        'DEPLOYMENT_SUCCESS.md',
        'DOCKER_SOLUTION.md',
        'PODMAN_CLI_FIX.md',
        'PODMAN_PROPER_INSTALL.md',
        'READY_TO_DEPLOY.md',
        'TEST_INTEGRATION.md',
        'КАК_ПОСМОТРЕТЬ.md',
    ],
    'docs/roadmaps/': [
        '🎯 Security Workstation v2.0.0 - Production Roadmap.md',
        '🚀 Security Workstation Evolution - Dec 2025.md',
    ],
    'docs/guides/': [
        'QUICK_START.md',
        'COMMIT_COMMANDS.md',
        'RECOMMENDED_SETUP.md',
    ],
    'scripts/': [
        'deploy.bat',
    ]
}

# Delete list
delete = [
    'ALL_FIXES_COMPLETE.md',
    'SARIF_UPLOAD_FIX.md',
    'SECURITY_FIXES_COMPLETE.md',
    'SECURITY_SCAN_FIXES.md',
    'SECURITY_SCAN_INDEX.md',
    'SECURITY_SCAN_README.md',
    'SECURITY_SCAN_SUMMARY.md',
    'SECURITY_WORKFLOWS_GUIDE.md',
]

# Execute moves
for dest_dir, files in moves.items():
    os.makedirs(dest_dir, exist_ok=True)
    for file in files:
        if os.path.exists(file):
            shutil.move(file, os.path.join(dest_dir, file))
            print(f"✅ Moved: {file} → {dest_dir}")

# Execute deletes
for file in delete:
    if os.path.exists(file):
        os.remove(file)
        print(f"🗑️  Deleted: {file}")

print("\n✅ Cleanup complete!")
```

---

## 🎯 Updated README.md

Create clear structure:

```markdown
# Security Workstation

AI-powered security testing platform.

## 🚀 Quick Start

### Backend API:
\`\`\`bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
\`\`\`

### Landing Page:
\`\`\`bash
cd frontend/landing
python -m http.server 8000
\`\`\`

## 📁 Repository Structure

- `backend/` - FastAPI backend
- `frontend/` - Landing page
- `security_assistant/` - Core scanner
- `docs/` - All documentation
  - `sessions/` - Session summaries
  - `roadmaps/` - Strategic plans
  - `deployment/` - Deployment guides
  - `guides/` - How-to guides

## 📊 Current Status

- **Version:** 1.0.0
- **Sessions Complete:** 24/36
- **Production:** Landing page live
- **Backend:** API working locally

## 🗺️ Roadmap

See: `docs/roadmaps/🚀 Security Workstation Evolution - Dec 2025.md`

## 📞 Support

- Issues: GitHub Issues
- Discussions: GitHub Discussions
\`\`\`

---

## ✅ Action Plan

**Want me to:**
1. Create cleanup script
2. Execute cleanup
3. Update README.md
4. Commit changes

**Or do it manually?** 🎯
