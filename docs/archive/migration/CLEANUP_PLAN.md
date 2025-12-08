# Repository Cleanup Plan - Session 28

## 🗑️ Files to Remove

### Temporary Migration Files (Created during Session 28)
- [ ] `MIGRATION_PLAN_WIN11.md` - Архивировать в docs/archive/
- [ ] `REBOOT_INSTRUCTIONS.md` - Архивировать в docs/archive/
- [ ] `CUDA_INSTALLATION_GUIDE.md` - Переместить в docs/guides/
- [ ] `SESSION_28_MIGRATION_REPORT.md` - Переместить в docs/sessions/

### Old/Obsolete Files
- [ ] `frontend_audit_perplexity.md` - Архивировать или удалить
- [ ] `gitlab_duo_bug_report.md` - Архивировать в docs/archive/
- [ ] `update_waitlist_smtp.py` - Проверить актуальность, возможно удалить
- [ ] `check_yaml.py` - Проверить актуальность

### Temporary Directories
- [ ] `.pytest_cache/` - Уже в .gitignore, можно удалить
- [ ] `.cursor/` - IDE кэш, проверить .gitignore
- [ ] `.windsurf/` - IDE кэш, проверить .gitignore
- [ ] `logs-render/` - Старые логи, архивировать или удалить

## 📁 Directory Structure to Create

```
docs/
├── archive/           # Старые документы
│   ├── migration/
│   │   ├── MIGRATION_PLAN_WIN11.md
│   │   └── REBOOT_INSTRUCTIONS.md
│   └── reports/
│       ├── frontend_audit_perplexity.md
│       └── gitlab_duo_bug_report.md
├── guides/            # Руководства
│   └── CUDA_INSTALLATION_GUIDE.md
└── sessions/          # Отчеты по сессиям
    └── SESSION_28_MIGRATION_REPORT.md
```

## 🔧 Actions

### 1. Create Archive Directories
```bash
mkdir -p docs/archive/migration
mkdir -p docs/archive/reports
mkdir -p docs/guides
mkdir -p docs/sessions
```

### 2. Move Migration Files
```bash
# Migration docs
mv MIGRATION_PLAN_WIN11.md docs/archive/migration/
mv REBOOT_INSTRUCTIONS.md docs/archive/migration/

# CUDA guide
mv CUDA_INSTALLATION_GUIDE.md docs/guides/

# Session report
mv SESSION_28_MIGRATION_REPORT.md docs/sessions/
```

### 3. Archive Old Reports
```bash
mv frontend_audit_perplexity.md docs/archive/reports/
mv gitlab_duo_bug_report.md docs/archive/reports/
```

### 4. Clean Temporary Files
```bash
# Remove pytest cache
rm -rf .pytest_cache/

# Check and potentially remove
# - update_waitlist_smtp.py (if obsolete)
# - check_yaml.py (if obsolete)
# - logs-render/ (if old logs)
```

### 5. Update .gitignore
```bash
# Add to .gitignore if not present:
.pytest_cache/
.cursor/
.windsurf/
*.pyc
__pycache__/
.env
logs/
*.log
```

## ✅ Verification

After cleanup:
- [ ] All migration docs archived
- [ ] Repository root clean
- [ ] docs/ structure organized
- [ ] .gitignore updated
- [ ] No temporary files in root
- [ ] Git status clean

## 📊 Expected Result

**Before:**
- 30+ files in root directory
- Migration files scattered
- Temporary caches

**After:**
- ~20 essential files in root
- Organized docs/ structure
- Clean git status
- Professional repository layout

## 🎯 Benefits

1. **Cleaner Repository**
   - Easier navigation
   - Professional appearance
   - Better organization

2. **Better Documentation**
   - Archived migration history
   - Organized guides
   - Session reports preserved

3. **Improved Workflow**
   - Faster file search
   - Clear structure
   - Less clutter

## 📝 Notes

- Keep all migration docs for future reference
- Archive, don't delete (unless truly obsolete)
- Update README.md with new structure
- Commit cleanup as separate commit
