# Update Chat Rules - Add Continuity System

**File to update:** `.gitlab/duo/chat-rules.md`

**Action:** Add the following section at the end of the file (after "Mode Switching" section)

---

## Section to Add

```markdown
---

## 📋 AI Agent Continuity System

**IMPORTANT:** Every new AI agent session MUST use the checkpoint system for continuity.

### 🚀 Quick Start (New Session)

```bash
# 1. Check latest checkpoint
python scripts/checkpoint_manager.py show --latest

# 2. Read session summary and next steps
# (Provides context from previous session)

# 3. Create new checkpoint for current session
python scripts/checkpoint_manager.py create \
  --session XX \
  --name <descriptive_name> \
  --feature "Feature Description" \
  --priority CRITICAL|HIGH|MEDIUM|LOW
```

### 📖 Full Documentation

- **System Guide:** [docs/CHECKPOINT_SYSTEM.md](../../docs/CHECKPOINT_SYSTEM.md)
- **Quick Reference:** [README_CHECKPOINT_SYSTEM.md](../../README_CHECKPOINT_SYSTEM.md)
- **Examples:** [examples/checkpoint_system_example.py](../../examples/checkpoint_system_example.py)

### 🎯 Key Commands

| Command | When to Use |
|---------|-------------|
| `show --latest` | **START of session** (get context) |
| `create` | **START of session** (new checkpoint) |
| `update` | **DURING session** (progress updates) |
| `validate --all` | **BEFORE commit** (quality check) |
| `report` | **END of session** (generate report) |

### ✅ Session Workflow

```
1. START → show --latest (read context)
2. START → create (new checkpoint)
3. DURING → update (progress 25%, 50%, 75%)
4. END → update --status COMPLETED
5. END → validate --all
6. END → report
7. COMMIT → git add checkpoints/ && git commit
```

### 📊 Checkpoint Structure

**Single Source of Truth:** `checkpoints/session_XX_name.json`

**Auto-Generated:**
- GitLab Issue Templates (`.gitlab/issue_templates/`)
- Continuity Reports (`docs/AI_AGENT_CONTINUITY_REPORT.md`)

**Key Fields:**
- `session_summary` - What was done (for next agent)
- `next_steps` - What to do next (priorities)
- `lessons_learned` - Important insights
- `objectives_completed` - Achievements
- `deliverables` - What was created

### 🔍 Finding Context

```bash
# Latest session context
python scripts/checkpoint_manager.py show --latest

# All completed sessions
python scripts/checkpoint_manager.py list --status COMPLETED

# All in-progress sessions
python scripts/checkpoint_manager.py list --status IN_PROGRESS

# Validate before commit
python scripts/checkpoint_manager.py validate --all
```

### ⚠️ CRITICAL RULES

1. **ALWAYS check latest checkpoint** at session start
2. **ALWAYS create checkpoint** for new session
3. **ALWAYS update progress** during session
4. **ALWAYS validate** before commit
5. **NEVER skip** session_summary and next_steps

### 💡 Best Practices

- **Descriptive names:** `session_19_ml_scoring` (not `session_19`)
- **Clear summaries:** "Successfully implemented X. Achieved Y. Status Z."
- **Prioritized next steps:** Use 🔴 CRITICAL, 🟡 HIGH, 🟢 MEDIUM, ⚪ LOW
- **Regular updates:** Update completion % at 25%, 50%, 75%, 100%
- **Validate often:** Run `validate --all` before each commit
```

---

## How to Update

### Option 1: Manual Edit

1. Open `.gitlab/duo/chat-rules.md` in your editor
2. Scroll to the end (after "Mode Switching" section)
3. Add the section above
4. Save the file

### Option 2: Command Line (Windows)

```cmd
# Backup original
copy .gitlab\duo\chat-rules.md .gitlab\duo\chat-rules.md.backup

# Append new section
type docs\UPDATE_CHAT_RULES_CONTENT.txt >> .gitlab\duo\chat-rules.md
```

### Option 3: Command Line (Linux/Mac)

```bash
# Backup original
cp .gitlab/duo/chat-rules.md .gitlab/duo/chat-rules.md.backup

# Append new section
cat docs/UPDATE_CHAT_RULES_CONTENT.txt >> .gitlab/duo/chat-rules.md
```

---

## Verification

After updating, verify the file:

```bash
# Check file size increased
dir .gitlab\duo\chat-rules.md

# Check content
type .gitlab\duo\chat-rules.md | findstr "Continuity System"
```

Expected output: Should show "AI Agent Continuity System" section

---

## Why This Update?

**Problem:** New AI agents don't know about the checkpoint system

**Solution:** Add continuity system info to chat-rules.md so every new agent:
1. Knows to check latest checkpoint first
2. Understands the workflow
3. Uses the system correctly
4. Maintains continuity between sessions

**Impact:**
- ✅ Better context handoff between agents
- ✅ Consistent workflow across sessions
- ✅ No lost information
- ✅ Faster session startup

---

**Version:** 1.0.0  
**Date:** 2025-12-02  
**Status:** Ready to apply
