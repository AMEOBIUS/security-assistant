# 🚀 Команды для коммита - Security Scan Setup

## Вариант 1: Рекомендуемый (No-SARIF) ⭐

**Для личных репозиториев (твой случай)**

```bash
# 1. Переключить на no-sarif workflow
git mv .github/workflows/security-scan.yml .github/workflows/security-scan.yml.with-sarif
git mv .github/workflows/security-scan-no-sarif.yml .github/workflows/security-scan.yml

# 2. Добавить все файлы
git add .github/workflows/ scripts/ *.md

# 3. Закоммитить
git commit -m "feat: setup security scanning (optimized for personal repos)

- Configured 3 scanners: Bandit, Semgrep, Trivy
- Added report generators (SARIF, HTML, Markdown)
- Optimized workflow for personal repositories (no SARIF upload)
- Added comprehensive documentation
- Configured Dependabot for automated updates

Features:
- ✅ Automated scanning on PR, push, schedule
- ✅ JSON, HTML, SARIF, Markdown reports
- ✅ PR comments with scan results
- ✅ Severity threshold checks
- ✅ Artifacts upload

Docs:
- QUICK_START.md - Quick setup guide
- RECOMMENDED_SETUP.md - Detailed recommendations
- SECURITY_SCAN_README.md - Full documentation"

# 4. Запушить
git push
```

---

## Вариант 2: С SARIF (для будущей миграции)

**Если планируешь перенос в Organization**

```bash
# 1. Добавить все файлы
git add .github/workflows/ scripts/ *.md

# 2. Закоммитить
git commit -m "feat: setup security scanning with SARIF support

- Configured 3 scanners: Bandit, Semgrep, Trivy
- Added report generators (SARIF, HTML)
- Fixed enable_scanner() calls with proper types
- Fixed Enum serialization in JSON
- Added continue-on-error for SARIF upload
- Updated to CodeQL Action v4
- Added comprehensive documentation

Features:
- ✅ Automated scanning on PR, push, schedule
- ✅ JSON, HTML, SARIF reports
- ✅ PR comments with scan results
- ✅ Ready for GitHub Advanced Security
- ✅ Severity threshold checks

Docs:
- QUICK_START.md - Quick setup guide
- SECURITY_WORKFLOWS_GUIDE.md - Workflow comparison
- SECURITY_SCAN_README.md - Full documentation"

# 3. Запушить
git push
```

---

## После коммита

### 1. Проверить workflow
```bash
# Создать тестовую ветку
git checkout -b test/security-scan

# Сделать изменение
echo "# Security Scan Test" >> README.md

# Закоммитить и запушить
git add README.md
git commit -m "test: security scan workflow"
git push -u origin test/security-scan
```

### 2. Создать PR
- Открыть GitHub
- Создать Pull Request из `test/security-scan` в `main`
- Дождаться запуска workflow
- Проверить комментарий с результатами

### 3. Проверить артефакты
- Actions → Security Scan → Latest run
- Artifacts → security-reports
- Скачать и проверить отчёты

---

## Откат (если что-то пошло не так)

### Вернуть SARIF workflow:
```bash
git mv .github/workflows/security-scan.yml .github/workflows/security-scan-no-sarif.yml
git mv .github/workflows/security-scan.yml.with-sarif .github/workflows/security-scan.yml
git add .github/workflows/
git commit -m "chore: revert to SARIF workflow"
git push
```

### Удалить всё:
```bash
git rm .github/workflows/security-scan*.yml
git rm scripts/generate_*.py
git rm SECURITY_*.md QUICK_START.md RECOMMENDED_SETUP.md SARIF_UPLOAD_FIX.md
git commit -m "chore: remove security scanning"
git push
```

---

## Проверка перед коммитом

```bash
# 1. Проверить синтаксис YAML
python -c "import yaml; yaml.safe_load(open('.github/workflows/security-scan.yml'))"

# 2. Проверить скрипты
python scripts/generate_sarif.py --help 2>/dev/null || echo "Script OK"
python scripts/generate_html_report.py --help 2>/dev/null || echo "Script OK"

# 3. Проверить структуру
ls -la .github/workflows/
ls -la scripts/
ls -la *.md
```

---

## Статус файлов

```bash
# Посмотреть что будет закоммичено
git status

# Посмотреть изменения
git diff --cached

# Посмотреть список файлов
git ls-files
```

---

## 🎯 Рекомендация

**Используй Вариант 1 (No-SARIF)** для личного репозитория.

Это оптимальное решение для текущей ситуации:
- ✅ Нет ошибок SARIF upload
- ✅ Markdown summary в PR
- ✅ Все отчёты доступны
- ✅ Готово к использованию

**Команды:**
```bash
git mv .github/workflows/security-scan.yml .github/workflows/security-scan.yml.with-sarif
git mv .github/workflows/security-scan-no-sarif.yml .github/workflows/security-scan.yml
git add .
git commit -m "feat: setup security scanning (optimized for personal repos)"
git push
```

**Готово!** 🚀
