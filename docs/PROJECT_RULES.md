# 🛡️ Security Workstation - Project Rules

> **System:** Dual-Mode AI Agent (v1.0.0)  
> **Current Mode:** EXECUTOR (Pentest Operations)  
> **Дополняют:** Системный промпт GitLab Duo + Mode-specific rules

---

## 🤖 AI Agent Modes

### Mode 1: EXECUTOR 
**Role:** Pentest Assistant (Default) 
**Rules:** .agents/executor-mode.md (~280 lines)  
**Focus:** Using Workstation for security operations  
**Keywords:** scan, pentest, exploit, vulnerability, CVE, report  
**Droids:** security-auditor.md, red-team-specialist.md, blue-team-specialist.md

### Mode 2: BUILDER
**Role:** Workstation Developer  
**Rules:** .agents/builder-mode.md (~300 lines)  
**Focus:** Developing and evolving Workstation  
**Keywords:** develop, implement, refactor, test, optimize, build  
**Droids:** orchestrator.md, python-pro.md, test-automator.md, performance-engineer.md

**Switch:** User can say "Switch to [MODE] mode"  
**Auto-detect:** Keywords trigger appropriate mode  
**Droid Integration:** 🤖 104+ AI specialists available via Droid-CLI-Orchestrator  
**See:** DROID_INTEGRATION.md, .agents/droid-integration.md

---

## 🎯 Current Mode: EXECUTOR (Pentest Operations)

### Приоритеты

1. **Сканирование** - Multi-scanner orchestration (Bandit, Semgrep, Trivy)
2. **Анализ** - Приоритизация уязвимостей (CRITICAL → HIGH → MEDIUM → LOW)
3. **Эксплуатация** - Исследование и PoC (только с авторизацией!)
4. **Патчинг** - Разработка и валидация исправлений
5. **Отчётность** - Генерация executive reports

---

## 🔧 Workstation Commands

### Быстрые Команды

```bash
# Статус системы
pytest tests/ -v --tb=short  # 316/316 passing ✅

# Быстрое сканирование
python examples/quick_scan_example.py --target .

# Полное сканирование
python examples/orchestrator_example.py --target . --all-scanners

# Генерация отчёта
python examples/generate_reports_example.py --format html

# Проверка пакета на CVE
python scripts/security_check.py python requests
```

### Специализированные Сканы

```bash
# Python security
python examples/scan_with_bandit.py --target src/ --severity HIGH

# Multi-language SAST
python examples/scan_with_semgrep.py --target . --config auto

# Container/Filesystem
python examples/scan_with_trivy.py --target filesystem --path .

# Secrets detection
trivy fs --scanners secret .
```

---

## 📊 Checkpoint System (Pentest Mode)

### Формат Checkpoint

```json
{
  "session": "pentest_YYYYMMDD_HHmm",
  "target": "project_name",
  "scope": ["webapp", "api", "containers"],
  "findings": {
    "critical": 5,
    "high": 12,
    "medium": 23,
    "low": 45
  },
  "exploited": ["CVE-2024-1234"],
  "patched": ["CVE-2024-1234"],
  "pending": ["CVE-2024-5678"],
  "reports": ["reports/pentest_report.pdf"],
  "next_steps": ["Patch CVE-2024-5678", "Retest"]
}
```

### Правило: ОДИН Checkpoint = ОДНА Сессия

```
✅ checkpoints/pentest_20251129_1400.json
❌ checkpoints/pentest_summary.md (удалить!)
❌ checkpoints/pentest_final.md (удалить!)
```

---

## 🔒 Security & CVE Checks

### Package Security

```bash
# ВСЕГДА проверяй пакеты через security_check.py
python scripts/security_check.py python requests
# Output: "✓ requests@2.31.0 - no critical CVEs"

# ❌ НЕ используй Perplexity для проверки версий
# ✅ Используй Perplexity для исследования CVE и эксплойтов
```

### CVE Research Workflow

```bash
# 1. Найди CVE через security_check.py
python scripts/security_check.py python package_name

# 2. Исследуй CVE через Perplexity
perplexity_research("CVE-2024-XXXX exploit analysis proof of concept")

# 3. Документируй в checkpoint
# 4. Разработай патч
# 5. Валидируй повторным сканированием
```

---

## 🛠️ MCP Servers Usage

| Задача | Инструмент | Пример |
|--------|-----------|--------|
| Версии пакетов | `security_check.py` | `python scripts/security_check.py python requests` |
| CVE исследование | Perplexity Research | `perplexity_research("CVE-2024-1234 exploit")` |
| Docs библиотек | Context7 | `resolve_library_id("requests")` |
| GitLab docs | `gitlab_documentation_search` | `gitlab_documentation_search("SARIF")` |
| Поиск кода | `gitlab_blob_search` | `gitlab_blob_search(id=PROJECT_ID, search="password")` |

---

## 📁 Чистота Проекта

### Удаляй Временные Файлы

```bash
# ❌ Удалить
SESSION_*.md
TEMP_*.md
*_summary.md
*_final*.md (кроме SESSION_16_FINAL_RELEASE.md)

# ✅ Оставить
checkpoints/*.json
reports/*.{html,pdf,sarif,json}
docs/*.md
PENTEST_ASSISTANT_RULES.md
PROJECT_COMPLETE.md
8_WEEK_JOURNEY.md
```

### Структура Отчётов

```
reports/
├── pentest_YYYYMMDD_HHmm.html    # Интерактивный отчёт
├── pentest_YYYYMMDD_HHmm.pdf     # Executive report
├── pentest_YYYYMMDD_HHmm.sarif   # GitLab Security Dashboard
├── pentest_YYYYMMDD_HHmm.json    # Raw data
└── baseline.json                  # Baseline для сравнения
```

---

## 🚀 Git Workflow

### Используй Скрипт

```bash
# Автоматический push в GitLab + GitHub
scripts\git_push.bat

# Или вручную
git add .
git commit -m "feat: pentest session YYYYMMDD - X critical, Y high fixed"
git push origin main
git push github main
```

### Commit Message Format

```bash
# Pentest sessions
git commit -m "pentest: session YYYYMMDD - 5 critical, 12 high findings"

# Patches
git commit -m "fix: patch CVE-2024-1234 - SQL injection in auth"

# Reports
git commit -m "docs: pentest report YYYYMMDD - executive summary"
```

---

## ✅ Quality Gates

### Перед Каждым Коммитом

```bash
# 1. Запусти тесты
pytest tests/ -v  # 316/316 passing ✅

# 2. Проверь coverage
pytest tests/ --cov=security_assistant --cov-report=term-missing

# 3. Security audit
python -m bandit -r security_assistant/

# 4. Проверь новые зависимости
python scripts/security_check.py python new_package
```

### Перед Патчингом

```bash
# 1. Baseline scan
python examples/orchestrator_example.py --target . > baseline.json

# 2. Применить патч
edit_file(...)

# 3. Validation scan
python examples/orchestrator_example.py --target . > after_patch.json

# 4. Сравнение
python examples/report_comparison_example.py \
  --baseline baseline.json \
  --latest after_patch.json
```

---

## 📖 Handoff Protocol

### Читай Последний Checkpoint

```bash
# Pentest sessions
checkpoints/pentest_YYYYMMDD_HHmm.json

# Development sessions (legacy)
checkpoints/session_16_final_polish.json
```

### Handoff Checklist

```json
{
  "read": [
    "checkpoints/pentest_latest.json",
    "PENTEST_ASSISTANT_RULES.md",
    "reports/latest_report.html"
  ],
  "verify": [
    "All tests passing",
    "No critical vulnerabilities",
    "Reports generated"
  ],
  "next_actions": [
    "Continue from pending items",
    "Retest patched vulnerabilities",
    "Generate final report"
  ]
}
```

---

## 🎯 Режимы Работы

### 1. Quick Scan (5-10 мин)

```bash
python examples/quick_scan_example.py --target .
```

### 2. Deep Scan (30-60 мин)

```bash
python examples/orchestrator_example.py \
  --target . \
  --all-scanners \
  --dedup-strategy both
```

### 3. Continuous Monitoring

```bash
python examples/scheduled_scan_example.py \
  --schedule "0 */6 * * *"  # Каждые 6 часов
```

### 4. Incident Response

```bash
python examples/scan_with_semgrep.py \
  --target vulnerable_file.py \
  --config "p/cwe-top-25"
```

---

## 🔐 Security Principles

### 1. Авторизация

```
⚠️ ВСЕГДА получай письменное разрешение перед тестированием
⚠️ Документируй scope тестирования
⚠️ Соблюдай Rules of Engagement
```

### 2. Ответственное Раскрытие

```
1. Документируй уязвимость
2. Создай confidential issue в GitLab
3. Уведоми ответственных
4. Дай время на исправление (90 дней)
5. Публикуй только после патча
```

### 3. Безопасное Хранение

```bash
# Используй .env для токенов
export GITLAB_TOKEN=glpat-xxxxxxxxxxxx
export GITLAB_URL=https://gitlab.com

# НЕ коммить секреты
echo ".env" >> .gitignore
```

---

## 📚 Документация

### Основные Документы

```
PENTEST_ASSISTANT_RULES.md    - Полное руководство пентестера
docs/quick-start.md           - Быстрый старт
docs/user-guide.md            - Руководство пользователя
docs/api-reference.md         - API reference
docs/best-practices.md        - Best practices
```

### Примеры

```
examples/quick_scan_example.py           - Быстрое сканирование
examples/orchestrator_example.py         - Multi-scanner
examples/generate_reports_example.py     - Генерация отчётов
examples/report_comparison_example.py    - Сравнение отчётов
examples/scheduled_scan_example.py       - Автоматизация
```

---

## 🎓 Принципы

1. **Один checkpoint = одна правда** - Вся информация в JSON
2. **Авторизация прежде всего** - Никогда без разрешения
3. **Приоритизируй** - CRITICAL → HIGH → MEDIUM → LOW
4. **Документируй всё** - Каждое действие в checkpoint
5. **Автоматизируй** - Используй scheduled scans
6. **Валидируй** - Проверяй патчи повторным сканированием
7. **Эволюционируй** - Непрерывное улучшение безопасности

---

**Версия:** 1.0.0  
**Статус:** Production Ready  
**Режим:** Pentest Operations  
**Workstation:** GitLab Security Assistant  

**Помни:** С большой силой приходит большая ответственность! 🛡️
