# 🔄 Unified Checkpoint System - Quick Start

**Единая система преемственности ИИ-агентов**

## 🎯 Что это?

Система для управления чекпойнтами сессий разработки с автоматической генерацией всех форматов из единого источника истины (JSON).

## 🚀 Quick Start

### 1. Создать новый чекпойнт

```bash
python scripts/checkpoint_manager.py create \
  --session 19 \
  --name ml_scoring \
  --feature "ML-based Vulnerability Scoring" \
  --priority CRITICAL
```

### 2. Сгенерировать GitLab Issue

```bash
python scripts/checkpoint_manager.py generate-issue --session 19
```

### 3. Обновить статус

```bash
# Начало работы
python scripts/checkpoint_manager.py update \
  --session 19 \
  --status IN_PROGRESS \
  --completion "0%"

# Прогресс
python scripts/checkpoint_manager.py update \
  --session 19 \
  --completion "50%"

# Завершение
python scripts/checkpoint_manager.py update \
  --session 19 \
  --status COMPLETED \
  --completion "100%"
```

### 4. Просмотр и навигация

```bash
# Последний чекпойнт
python scripts/checkpoint_manager.py show --latest

# Все чекпойнты
python scripts/checkpoint_manager.py list

# Только завершенные
python scripts/checkpoint_manager.py list --status COMPLETED
```

### 5. Валидация

```bash
python scripts/checkpoint_manager.py validate --all
```

### 6. Генерация отчета

```bash
python scripts/checkpoint_manager.py report
```

## 📋 Доступные команды

| Команда | Описание | Пример |
|---------|----------|--------|
| `create` | Создать новый чекпойнт | `--session 19 --name ml_scoring` |
| `update` | Обновить чекпойнт | `--session 19 --status COMPLETED` |
| `generate-issue` | Сгенерировать Issue Template | `--session 19` |
| `show` | Показать последний чекпойнт | `--latest` |
| `list` | Список всех чекпойнтов | `--status COMPLETED` |
| `validate` | Валидировать чекпойнты | `--all` |
| `report` | Сгенерировать отчет | (без параметров) |

## 📊 Статусы

- `PLANNED` - Запланировано
- `IN_PROGRESS` - В процессе
- `COMPLETED` - Завершено
- `BLOCKED` - Заблокировано

## 🎨 Приоритеты

- `CRITICAL` - 🔴 Критический
- `HIGH` - 🟡 Высокий
- `MEDIUM` - 🟢 Средний
- `LOW` - ⚪ Низкий

## 🔧 Режимы

- `BUILDER` - Разработка (по умолчанию)
- `EXECUTOR` - Пентестинг

## 📚 Документация

Полная документация: [docs/CHECKPOINT_SYSTEM.md](docs/CHECKPOINT_SYSTEM.md)

## 🧪 Тесты

```bash
pytest tests/test_checkpoint_manager.py -v
```

## 🤝 Workflow

```
1. CREATE checkpoint
   ↓
2. GENERATE issue template
   ↓
3. UPDATE status (IN_PROGRESS)
   ↓
4. UPDATE progress (50%, 75%, ...)
   ↓
5. UPDATE status (COMPLETED)
   ↓
6. VALIDATE
   ↓
7. GENERATE report
```

## 💡 Tips

1. **Всегда валидируйте** перед коммитом:
   ```bash
   python scripts/checkpoint_manager.py validate --all
   ```

2. **Используйте описательные имена**:
   ```bash
   ✅ --name ml_scoring
   ❌ --name feature
   ```

3. **Обновляйте прогресс регулярно**:
   ```bash
   python scripts/checkpoint_manager.py update --session 19 --completion "25%"
   ```

4. **Генерируйте отчеты** после каждой сессии:
   ```bash
   python scripts/checkpoint_manager.py report
   ```

## 🐛 Troubleshooting

### Ошибка: "Checkpoint already exists"

```bash
# Используйте update вместо create
python scripts/checkpoint_manager.py update --session 19 --status COMPLETED
```

### Ошибка: "Checkpoint not found"

```bash
# Проверьте список чекпойнтов
python scripts/checkpoint_manager.py list

# Создайте чекпойнт
python scripts/checkpoint_manager.py create --session 19 --name ml_scoring
```

### Ошибка валидации

```bash
# Посмотрите детали ошибок
python scripts/checkpoint_manager.py validate --all

# Исправьте JSON вручную
nano checkpoints/session_19_ml_scoring.json
```

---

**Version:** 1.0.0  
**Last Updated:** 2025-12-02
