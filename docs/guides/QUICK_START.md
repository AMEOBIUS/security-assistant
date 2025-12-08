# 🚀 Security Scan - Quick Start

## 1️⃣ Выбери workflow (30 секунд)

### Вариант A: No-SARIF ⭐ **РЕКОМЕНДУЕТСЯ**
**Для личных репозиториев (твой случай)**

```bash
git mv .github/workflows/security-scan.yml .github/workflows/security-scan.yml.backup
git mv .github/workflows/security-scan-no-sarif.yml .github/workflows/security-scan.yml
git add .github/workflows/
git commit -m "chore: use no-sarif workflow"
git push
```

**Результат:**
- ✅ Чистый вывод без ошибок
- ✅ Markdown summary в PR
- ✅ Все отчёты в артефактах

### Вариант B: С SARIF (текущий)
**Если планируешь перенос в Organization**

```bash
# Ничего не делать - уже настроен
# Просто закоммить изменения
git add .
git commit -m "fix: security scan workflow fixes"
git push
```

**Результат:**
- ⚠️ Warning о SARIF upload (но не критично)
- ✅ Готов к Advanced Security
- ✅ Все отчёты в артефактах

---

## 2️⃣ Проверь работу (2 минуты)

### Создай тестовый PR:
```bash
# Создай новую ветку
git checkout -b test/security-scan

# Сделай любое изменение
echo "# Test" >> README.md

# Закоммить и запушить
git add README.md
git commit -m "test: security scan"
git push -u origin test/security-scan

# Создай PR через GitHub UI
```

### Проверь результаты:
1. **Actions tab** → Security Scan должен запуститься
2. **PR** → Должен появиться комментарий с результатами
3. **Artifacts** → Должны быть доступны отчёты

---

## 3️⃣ Настрой (опционально)

### Изменить параметры сканирования:

**Файл:** `.github/workflows/security-scan.yml`

```yaml
env:
  ENABLE_BANDIT: 'true'      # Python security
  ENABLE_SEMGREP: 'true'     # Multi-language SAST
  ENABLE_TRIVY: 'true'       # Containers, dependencies
  
  FAIL_ON_HIGH: 'false'      # Не прерывать на HIGH
  FAIL_ON_CRITICAL: 'true'   # Прерывать на CRITICAL
  
  DEDUP_STRATEGY: 'both'     # location, content, both
```

### Настроить расписание:

```yaml
schedule:
  - cron: '0 9 * * 1'  # Каждый понедельник в 9:00 UTC
  # Или:
  - cron: '0 0 * * *'  # Каждый день в полночь
```

---

## 📊 Что получаешь

### В каждом PR:
- 🔒 Комментарий с результатами сканирования
- 📊 Статистика по severity
- 🎯 Top 5 приоритетных находок
- 📁 Ссылка на полные отчёты

### В артефактах:
- `scan-results.json` - JSON с полными данными
- `results.sarif` - SARIF отчёт
- `report.html` - Красивый HTML отчёт
- `SUMMARY.md` - Markdown сводка

### Автоматически:
- ✅ Сканирование при каждом PR
- ✅ Сканирование при push в main
- ✅ Еженедельное сканирование
- ✅ Ручной запуск (workflow_dispatch)

---

## 🎯 Рекомендации

### Для личного репозитория (сейчас):
```bash
# 1. Используй no-sarif workflow
git mv .github/workflows/security-scan.yml .github/workflows/security-scan.yml.backup
git mv .github/workflows/security-scan-no-sarif.yml .github/workflows/security-scan.yml

# 2. Коммит
git add .github/workflows/ scripts/ *.md
git commit -m "feat: setup security scanning (no-sarif)"
git push

# 3. Создай тестовый PR
```

### Если перенесёшь в Organization:
```bash
# 1. Верни SARIF workflow
git mv .github/workflows/security-scan.yml.backup .github/workflows/security-scan.yml

# 2. Включи Advanced Security в Settings
# 3. Profit! 🎉
```

---

## ❓ Проблемы?

### "Resource not accessible by integration"
✅ **Решено:** Используй `security-scan-no-sarif.yml`

### "Scanner validation failed"
✅ **Решено:** Обновлён вызов `enable_scanner()`

### "Enum not serializable"
✅ **Решено:** Добавлено `.value` для Enum

### Workflow не запускается
- Проверь `.github/workflows/security-scan.yml` существует
- Проверь синтаксис YAML
- Проверь permissions в workflow

---

## 📖 Документация

- [RECOMMENDED_SETUP.md](RECOMMENDED_SETUP.md) - Детальная настройка
- [SECURITY_WORKFLOWS_GUIDE.md](SECURITY_WORKFLOWS_GUIDE.md) - Сравнение workflows
- [SECURITY_SCAN_FIXES.md](SECURITY_SCAN_FIXES.md) - Технические исправления
- [SARIF_UPLOAD_FIX.md](SARIF_UPLOAD_FIX.md) - Решение проблемы SARIF

---

## ✅ Готово!

**Выбери workflow и запускай.** Всё настроено и работает! 🚀

**Рекомендация:** Используй `security-scan-no-sarif.yml` для личного репозитория.
