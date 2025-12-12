# Unified Search MCP Integration Guide

## ✅ Что сделано

1. ✅ Создан MCP сервер `unified-search`
2. ✅ Интеграция с Tavily + DuckDuckGo
3. ✅ Автоматический fallback
4. ✅ Node.js зависимости установлены

## 🔧 Установка

### 1. Скопируй конфигурацию

Замени содержимое `C:\Users\admin\AppData\Roaming\GitLab\duo\mcp.json` на:

```json
{
  "mcpServers": {
    "unified-search": {
      "command": "node",
      "args": ["C:\\Users\\admin\\Desktop\\Workstation\\.mcp\\unified-search\\index.js"],
      "type": "stdio",
      "env": {
        "TAVILY_API_KEY": ""
      },
      "alwaysAllow": [
        "unified_search",
        "unified_research"
      ],
      "approvedTools": [
        "unified_search",
        "unified_research",
        "unified_search_status"
      ]
    },
    "context7": { ... },
    "git": { ... },
    "memory": { ... },
    ...остальные серверы...
  }
}
```

**Полный пример:** `docs/mcp.json.example`

### 2. (Опционально) Добавь Tavily API ключ

Если хочешь лучшее качество поиска:

1. Регистрация: https://tavily.com (бесплатно 1000 req/month)
2. Получи API ключ
3. Добавь в `mcp.json`:
```json
"env": {
  "TAVILY_API_KEY": "tvly-your-key-here"
}
```

**Без ключа работает DuckDuckGo** (бесплатно, без лимитов)

### 3. Перезапусти VS Code / GitLab Duo

Полный рестарт для применения изменений.

## 🎯 Использование

После перезапуска у тебя будут доступны:

### `unified_search` - Быстрый поиск
```
Найди информацию о Python security best practices
```

### `unified_research` - Глубокое исследование
```
Исследуй: What are the latest AI security trends?
```

### `unified_search_status` - Проверка статуса
```
Покажи статус поисковых провайдеров
```

## 📊 Провайдеры

| Провайдер | Статус | Лимиты | Качество |
|-----------|--------|--------|----------|
| DuckDuckGo | ✅ Работает | Без лимитов | Хорошее |
| Tavily | ⚠️ Нужен ключ | 1000/месяц | Отличное |

## 🔄 Автоматический Fallback

1. Если Tavily доступен → используется Tavily
2. Если Tavily недоступен → DuckDuckGo
3. Если DuckDuckGo падает → пробует Tavily

## 🐛 Troubleshooting

### MCP сервер не запускается

```bash
# Проверь Node.js
node --version  # должно быть >= 18

# Проверь Python
python --version  # должно быть >= 3.8

# Проверь зависимости
pip list | findstr "tavily duckduckgo"
```

### Ошибка "Python not found"

Убедись что Python в PATH:
```cmd
where python
```

### Тест вручную

```bash
# Тест Python wrapper
python scripts/unified_search.py search "test" --json

# Тест MCP сервера
node .mcp/unified-search/index.js
```

## 📝 Следующие шаги

1. Скопируй `docs/mcp.json.example` → `C:\Users\admin\AppData\Roaming\GitLab\duo\mcp.json`
2. Перезапусти VS Code
3. Протестируй: "Найди информацию о Python"
4. (Опционально) Добавь Tavily ключ для лучшего качества
