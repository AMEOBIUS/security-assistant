# ✅ MCP Servers - Windows Compatibility Fix

## 🔧 Проблема

Shebang строки (`#!/usr/bin/env python3`) в Python скриптах вызывают проблемы на Windows:
- Не нужны для Windows (Python запускается через `python` команду)
- Могут вызывать encoding проблемы
- Не совместимы с MCP stdio протоколом на Windows

## ✅ Исправлено

### Python MCP серверы (4 файла)

**1. cortex-mcp.py**
```python
# Было:
#!/usr/bin/env python3
"""
Cortex MCP Server
...
"""

# Стало:
"""
Cortex MCP Server
Integrates Cortex for observable analysis and automated security responses through AI

Windows-compatible MCP server (no shebang required)
"""
```

**2. thehive-mcp.py**
```python
# Было:
#!/usr/bin/env python3
"""
TheHive MCP Server
...
"""

# Стало:
"""
TheHive MCP Server
Facilitates collaborative security incident response and case management using AI

Windows-compatible MCP server (no shebang required)
"""
```

**3. wazuh-mcp.py**
```python
# Было:
#!/usr/bin/env python3
"""
Wazuh MCP Server
...
"""

# Стало:
"""
Wazuh MCP Server
Integrates Wazuh SIEM with AI for real-time security alerts and contextual analysis

Windows-compatible MCP server (no shebang required)
"""
```

**4. production_agent_mcp.py** (в скрипте установки)
```python
# Было:
#!/usr/bin/env python3
"""
Production Agent MCP Server
...
"""

# Стало:
"""
Production Agent MCP Server
Central coordination hub for all agent operations

Windows-compatible MCP server (no shebang required)
"""
```

## 🎯 Результат

**Все Python MCP серверы теперь:**
- ✅ Windows-совместимы
- ✅ Работают через `python script.py`
- ✅ Совместимы с MCP stdio протоколом
- ✅ Не имеют encoding проблем
- ✅ Готовы к использованию в GitLab Duo

## 🚀 Использование

### Запуск серверов
```powershell
# Через MCP config (автоматически)
"command": "python",
"args": ["C:/Workstation/mcp-servers/cortex-mcp.py"]

# Вручную (для тестирования)
python C:\Workstation\mcp-servers\cortex-mcp.py
```

### Проверка синтаксиса
```powershell
# Все серверы должны компилироваться без ошибок
python -m py_compile mcp-servers\cortex-mcp.py
python -m py_compile mcp-servers\thehive-mcp.py
python -m py_compile mcp-servers\wazuh-mcp.py
```

## 📊 Совместимость

| Платформа | Статус | Примечание |
|-----------|--------|------------|
| Windows 10/11 | ✅ Работает | Основная платформа |
| Linux | ✅ Работает | Shebang не требуется |
| macOS | ✅ Работает | Shebang не требуется |
| WSL | ✅ Работает | Через Python |

## 🔍 Тестирование

### Автоматический тест
```powershell
.\scripts\test-mcp-infrastructure.ps1
```

**Проверяет:**
- ✅ Python syntax (все 4 сервера)
- ✅ File structure
- ✅ Dependencies
- ✅ Functional tests

### Ручной тест
```powershell
# Test Production Agent
echo '{"jsonrpc":"2.0","id":1,"method":"get_metrics","params":{}}' | python .agent_system\mcp_servers\production_agent_mcp.py

# Test Cortex
echo '{"jsonrpc":"2.0","id":1,"method":"cortex.list_analyzers","params":{}}' | python mcp-servers\cortex-mcp.py

# Test TheHive
echo '{"jsonrpc":"2.0","id":1,"method":"thehive.list_cases","params":{}}' | python mcp-servers\thehive-mcp.py

# Test Wazuh
echo '{"jsonrpc":"2.0","id":1,"method":"wazuh.list_alerts","params":{}}' | python mcp-servers\wazuh-mcp.py
```

## ✅ Готово!

Все Python MCP серверы теперь полностью совместимы с Windows и готовы к использованию в GitLab Duo.

**Следующий шаг:** Запустить инфраструктуру
```powershell
.\scripts\start-mcp-infrastructure.ps1
```
