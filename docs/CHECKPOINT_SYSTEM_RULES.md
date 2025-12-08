# CRITICAL: Single Source of Truth - Checkpoint System Rules

## 🚨 MANDATORY RULES FOR ALL AI AGENTS

### Rule 1: ONE SOURCE OF TRUTH
**ONLY `checkpoints/*.json` contains session data.**

❌ **NEVER create:**
- `docs/SESSION_*.md`
- `docs/sessions/SESSION_*.md`
- Any session summary files outside checkpoints/

✅ **ALWAYS use:**
- `checkpoints/session_XX_name.json` - Complete session data
- Technical docs in `docs/` (guides, references, NOT session summaries)

---

### Rule 2: CHECKPOINT STRUCTURE

**Every session MUST have ONE checkpoint file:**
```
checkpoints/session_25_security_fixes.json
```

**This file contains EVERYTHING:**
- Session summary
- Objectives completed
- Deliverables (code, tests, docs)
- Lessons learned
- Next steps
- Metrics
- All session data

**NO separate markdown summaries!**

---

### Rule 3: DOCUMENTATION TYPES

**Technical Documentation (docs/):**
- ✅ `docs/SECURITY_IMPROVEMENTS.md` - Technical guide
- ✅ `docs/DOPPLER_MIGRATION_GUIDE.md` - How-to guide
- ✅ `docs/API_REFERENCE.md` - Reference docs
- ✅ `docs/ARCHITECTURE.md` - System design

**Session Data (checkpoints/):**
- ✅ `checkpoints/session_25_*.json` - Session data
- ❌ NO `docs/SESSION_25_*.md` files!

---

### Rule 4: SESSION WORKFLOW

**START of session:**
```bash
# 1. Read latest checkpoint
python scripts/checkpoint_manager.py show --latest

# 2. Create new checkpoint
python scripts/checkpoint_manager.py create \
  --session 26 \
  --name feature_name \
  --feature "Description" \
  --priority HIGH
```

**DURING session:**
- Work on code/features
- Create technical docs in docs/ (if needed)
- Update checkpoint JSON (not markdown!)

**END of session:**
```bash
# 1. Update checkpoint with real data
# Edit checkpoints/session_26_*.json directly

# 2. Validate
python scripts/checkpoint_manager.py validate --all

# 3. Generate report
python scripts/checkpoint_manager.py report

# 4. Commit
git add checkpoints/ docs/
git commit -m "Session 26: Feature complete"
```

**❌ DO NOT create `docs/SESSION_26_SUMMARY.md`!**

---

### Rule 5: WHAT GOES WHERE

**checkpoints/session_XX.json:**
- Session summary
- Objectives
- Deliverables
- Lessons learned
- Next steps
- Metrics
- ALL session-specific data

**docs/:**
- Technical guides (how to use features)
- API references
- Architecture docs
- Deployment guides
- NOT session summaries!

**README.md:**
- Project overview
- Quick start
- Links to docs/

---

## 🧹 CLEANUP REQUIRED

**Files to DELETE (data already in checkpoints/):**
```
docs/SESSION_19_COMPLETE_SUMMARY.md
docs/SESSION_20_PROGRESS.md
docs/SESSION_20_START.md
docs/SESSION_20_SUMMARY.md
docs/SESSION_21_SUMMARY.md
docs/SESSION_25_COMPLETE.md
docs/SESSION_25_FINAL.md
docs/SESSION_25_SUMMARY.md
docs/SESSION_25_TESTING_COMPLETE.md
docs/SESSIONS_20_21_COMPLETE.md
docs/QUICK_START_SESSIONS_20_21.md
docs/REPOSITORY_CLEANUP_SUMMARY.md
```

**Files to KEEP (technical documentation):**
```
docs/SECURITY_IMPROVEMENTS.md
docs/DOPPLER_MIGRATION_GUIDE.md
docs/DOPPLER_QUICK_START.md
docs/DOPPLER_SETUP_COMPLETE.md
docs/SECURITY_TESTING_GUIDE.md
docs/LAUNCH_PLAN.md
docs/CHECKPOINT_SYSTEM.md
docs/AI_AGENT_CONTINUITY_REPORT.md (auto-generated)
```

---

## 🔧 ENFORCEMENT

### Update .agents/builder-mode.md

Add at the TOP:

```markdown
# 🚨 CRITICAL: SINGLE SOURCE OF TRUTH

## Checkpoint System - MANDATORY

**ONLY `checkpoints/*.json` contains session data.**

### ❌ NEVER CREATE:
- `docs/SESSION_*.md`
- `docs/sessions/SESSION_*.md`
- Session summaries outside checkpoints/

### ✅ ALWAYS:
1. Update `checkpoints/session_XX.json` with REAL data
2. Create technical docs ONLY for features (not sessions)
3. One session = One checkpoint JSON file

### Session Workflow:
1. START → `checkpoint_manager.py show --latest`
2. CREATE → `checkpoint_manager.py create --session XX`
3. WORK → Code + features
4. UPDATE → Edit checkpoint JSON (fill all fields!)
5. VALIDATE → `checkpoint_manager.py validate --all`
6. COMMIT → Only checkpoint + technical docs
```

### Update Pre-commit Hook

Block SESSION_*.md files:

```bash
# Check for session summary files in docs/
if git diff --cached --name-only | grep -E "docs/SESSION_.*\.md"; then
    echo "❌ ERROR: Session summaries must be in checkpoints/*.json, not docs/"
    echo "Move data to checkpoint JSON file instead"
    exit 1
fi
```

---

## 🚀 Implementation Plan

Want me to:
1. ✅ Create cleanup script
2. ✅ Update .agents/builder-mode.md
3. ✅ Update pre-commit hook
4. ✅ Delete duplicate SESSION_*.md files
5. ✅ Consolidate remaining data into checkpoints

**Implement now?**
