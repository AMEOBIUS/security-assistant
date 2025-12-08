# MCP Server Setup Instructions

## 🚀 Установленные MCP Сервера

### Добавлены в конфигурацию:
- **ghidrassistmcp** - Ghidra reverse engineering
- **volatility-mcp** - Memory forensics  
- **malwarepatrol** - Threat intelligence
- **wazuh-mcp** - SIEM integration
- **github-mcp** - Code analysis
- **docker-mcp** - Container management
- **cortex-mcp** - Observable analysis
- **thehive-mcp** - Incident response

## 🔧 Требования для работы

### Docker Контейнеры (TBD):
```bash
docker pull ghidrassistmcp/latest
docker pull volatility-mcp/memory-analysis
docker pull github-mcp/latest
docker pull docker-mcp/latest
```

### Локальные Python скрипты:
Созданы в `C:\Workstation\mcp-servers\`:
- `wazuh-mcp.py` - Wazuh SIEM интеграция
- `cortex-mcp.py` - Cortex анализ
- `thehive-mcp.py` - TheHive кейс менеджмент

### API Токены:
Замените `YOUR_MALWAREPATROL_TOKEN` в mcp.json

## 🛡️ Безопасность

Все серверы настроены с изолированным запуском:
- Docker контейнеры с флагом `--rm`
- Python скрипты в отдельных процессах
- Только чтение для gitconfig
- Изолированные сети по умолчанию

## ✅ Готово к использованию

Конфигурация обновлена в: `C:\Users\Администратор\.factory\mcp.json`
