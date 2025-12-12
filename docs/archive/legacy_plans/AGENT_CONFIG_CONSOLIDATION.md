# Agent Configuration Structure - Consolidation Plan

**Goal:** Eliminate duplication between `.agents/` and `.gitlab/duo/chat-rules.md`

---

## 📊 Current State (Duplication Issues)

### 1. `.gitlab/duo/chat-rules.md`
- Mode switching (BUILDER/EXECUTOR)
- Checkpoint system (full guide)
- Quick commands
- Session workflow

### 2. `.agents/builder-mode.md`
- TDD workflow
- Quality standards
- Tool selection
- **OUTDATED:** Droid-CLI references (removed)

### 3. `.agents/executor-mode.md`
- Pentest workflow
- Security rules
- Priority system
- **OUTDATED:** Droid-CLI references (removed)

**Problem:** Information duplicated in 3 places, outdated references

---

## 🎯 Proposed Structure

### Single Source of Truth: `.gitlab/duo/chat-rules.md`

**Purpose:** Main navigation hub (what we have now)

**Content:**
- Mode switching (BUILDER/EXECUTOR)
- Checkpoint system (quick start + links)
- Links to detailed rules

### Detailed Rules: `.agents/`

**Purpose:** Mode-specific detailed rules

**Content:**
- `.agents/builder-mode.md` - Development workflow
- `.agents/executor-mode.md` - Pentesting workflow

---

## 📋 Consolidation Plan

### Option 1: Minimal (Recommended)

**Keep:**
- `.gitlab/duo/chat-rules.md` - Navigation hub (current state)
- `.agents/builder-mode.md` - Detailed BUILDER rules (cleaned)
- `.agents/executor-mode.md` - Detailed EXECUTOR rules (cleaned)

**Changes:**
- Remove Droid-CLI references from `.agents/*.md`
- Remove duplication (keep only mode-specific details)
- Add cross-references

**Benefits:**
- ✅ Clear separation (navigation vs details)
- ✅ No duplication
- ✅ Easy to maintain

### Option 2: Merge Everything

**Keep:**
- `.gitlab/duo/chat-rules.md` - Everything in one file

**Remove:**
- `.agents/builder-mode.md`
- `.agents/executor-mode.md`

**Benefits:**
- ✅ Single file
- ✅ No duplication

**Drawbacks:**
- ❌ Very long file
- ❌ Hard to navigate

---

## ✅ Recommended: Option 1 (Minimal)

### `.gitlab/duo/chat-rules.md` (Navigation Hub)

**Content:**
```markdown
# Security Workstation - Agent Modes

## 🎯 Default Mode: BUILDER
[Current content - mode switching, checkpoint system]

## 📖 Detailed Rules
- **BUILDER Mode:** [.agents/builder-mode.md](../../.agents/builder-mode.md)
- **EXECUTOR Mode:** [.agents/executor-mode.md](../../.agents/executor-mode.md)
```

### `.agents/builder-mode.md` (Detailed Rules)

**Content:**
- TDD workflow (Test → Implement → Refactor)
- Quality standards (coverage ≥90%, type hints)
- Tool selection (Perplexity, security_check.py)
- Code actualization workflow
- Quality gates

**Remove:**
- ❌ Droid-CLI references
- ❌ Checkpoint format (already in chat-rules.md)
- ❌ Mode switching (already in chat-rules.md)

### `.agents/executor-mode.md` (Detailed Rules)

**Content:**
- Pentest workflow (Scan → Analyze → Prioritize → Report)
- Security rules (authorization, responsible disclosure)
- Priority system (scoring 0-100)
- Tool selection (scanners, reports)
- Quality gates

**Remove:**
- ❌ Droid-CLI references
- ❌ Checkpoint format (already in chat-rules.md)
- ❌ Mode switching (already in chat-rules.md)

---

## 🔄 Implementation Steps

### Step 1: Clean `.agents/builder-mode.md`
- Remove Droid-CLI references
- Remove checkpoint format duplication
- Keep only BUILDER-specific workflow
- Add link to chat-rules.md for checkpoint system

### Step 2: Clean `.agents/executor-mode.md`
- Remove Droid-CLI references
- Remove checkpoint format duplication
- Keep only EXECUTOR-specific workflow
- Add link to chat-rules.md for checkpoint system

### Step 3: Update `.gitlab/duo/chat-rules.md`
- Add "Detailed Rules" section with links
- Keep current checkpoint system section
- Keep mode switching section

### Step 4: Validation
- Check all cross-references work
- Ensure no duplication
- Test navigation flow

---

## 📊 Before/After Comparison

### Before (Current)

**Duplication:**
- Checkpoint format: 3 places
- Mode switching: 2 places
- Tool selection: 2 places
- Droid-CLI: 2 places (outdated)

**Total:** ~300 lines duplicated

### After (Proposed)

**No Duplication:**
- Checkpoint system: 1 place (chat-rules.md)
- Mode switching: 1 place (chat-rules.md)
- BUILDER workflow: 1 place (builder-mode.md)
- EXECUTOR workflow: 1 place (executor-mode.md)
- Droid-CLI: 0 places (removed)

**Total:** 0 lines duplicated

---

## ✅ Benefits

1. **Single Source of Truth**
   - Checkpoint system: chat-rules.md
   - Mode workflows: .agents/*.md

2. **No Duplication**
   - Each piece of info in one place
   - Easy to update

3. **Clear Navigation**
   - chat-rules.md → Quick start + links
   - .agents/*.md → Detailed workflows

4. **Maintainable**
   - Update once, not 3 times
   - No sync issues

5. **Clean**
   - No outdated references
   - No legacy code

---

## 🎯 Next Steps

1. Clean `.agents/builder-mode.md` (remove Droid-CLI, duplication)
2. Clean `.agents/executor-mode.md` (remove Droid-CLI, duplication)
3. Update `.gitlab/duo/chat-rules.md` (add links to detailed rules)
4. Validate cross-references
5. Commit changes

---

**Status:** READY TO IMPLEMENT  
**Estimated Time:** 30 minutes  
**Risk:** LOW (backup exists)
