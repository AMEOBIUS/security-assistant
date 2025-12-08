# 🔥 Hacker Workstation - MCP Infrastructure

## 🎯 Быстрый старт (30 секунд)

```powershell
# 1. Запустить инфраструктуру
.\scripts\start-mcp-infrastructure.ps1

# 2. Запустить сервисы
.\start-all-mcp-services.bat

# 3. Проверить здоровье
.\scripts\check-mcp-health.ps1
```

**Готово! Все 16 MCP серверов настроены.**

---

## 📊 Что установлено

### ✅ Активные серверы (7)
- **perplexity** - AI исследования и поиск
- **context7** - Документация библиотек
- **puppeteer** - Автоматизация браузера
- **git** - Управление Git
- **memory** - Граф знаний
- **sequentialthinking** - Последовательное мышление
- **filesystem** - Файловая система

### 🟡 Готовые к запуску (9)
- **production-agent** - Центральная координация агентов
- **cortex** - Анализ observable и threat intelligence
- **thehive** - Incident response и case management
- **wazuh** - SIEM мониторинг и threat detection
- **github-security** - Security code analysis
- **docker-pentest** - Container security scanning
- **malwarepatrol** - Threat actor intelligence (200+ профилей)
- **volatility** - Memory forensics
- **ghidrassist** - Reverse engineering (31 инструмент)

---

## 🚀 Созданные файлы

### Скрипты запуска
```
✅ scripts/start-mcp-infrastructure.ps1  - Главный установщик
✅ start-all-mcp-services.bat            - Запуск всех сервисов
✅ scripts/start-cortex.bat              - Cortex
✅ scripts/start-thehive.bat             - TheHive
✅ scripts/start-wazuh.bat               - Wazuh
✅ scripts/check-mcp-health.ps1          - Health check
```

### MCP серверы
```
✅ .agent_system/mcp_servers/production_agent_mcp.py  - Production Agent
✅ mcp-servers/cortex-mcp.py                          - Cortex
✅ mcp-servers/thehive-mcp.py                         - TheHive
✅ mcp-servers/wazuh-mcp.py                           - Wazuh
```

### Docker образы
```
✅ docker-mcp/Dockerfile.volatility  - Volatility 3
✅ docker-mcp/Dockerfile.ghidra      - Ghidra 10.4
```

### Документация
```
✅ docs/MCP_INFRASTRUCTURE_GUIDE.md  - Полное руководство
✅ README_MCP_INFRASTRUCTURE.md      - Этот файл
```

---

## 🎯 Использование

### Reconnaissance
```
User: "Analyze domain evil.com"

Agent:
1. cortex → Check domain reputation
2. malwarepatrol → Search threat actors
3. wazuh → Monitor for alerts
```

### Vulnerability Analysis
```
User: "Scan GitHub repo for vulnerabilities"

Agent:
1. github-security → Clone and scan
2. docker-pentest → Check containers
3. Report findings
```

### Incident Response
```
User: "Investigate alert #1234"

Agent:
1. wazuh → Fetch alert details
2. thehive → Create case
3. cortex → Analyze observables
4. Generate report
```

### Forensics
```
User: "Analyze memory dump suspect.raw"

Agent:
1. volatility → Extract processes
2. volatility → Detect rootkits
3. ghidrassist → Analyze suspicious binaries
4. Timeline analysis
```

---

## 🔑 API Keys (опционально)

Для полной функциональности добавьте токены в `mcp.json`:

```json
{
  "github-security": {
    "env": {
      "GITHUB_TOKEN": "ghp_your_token_here"
    }
  },
  "malwarepatrol": {
    "env": {
      "MALWAREPATROL_TOKEN": "your_token_here"
    }
  }
}
```

**Где получить:**
- GitHub: https://github.com/settings/tokens (scopes: `repo`, `security_events`)
- Malware Patrol: https://malwarepatrol.net/api

---

## 🔍 Проверка статуса

### Быстрая проверка
```powershell
.\scripts\check-mcp-health.ps1
```

**Вывод:**
```
🔍 MCP Infrastructure Health Check

✅ Production Agent: Ready
✅ Cortex: Ready
✅ TheHive: Ready
✅ Wazuh: Ready

Docker Containers:
cortex    Up 5 minutes
thehive   Up 5 minutes
wazuh     Up 5 minutes

Port Status:
✅ Port 9001: Open
✅ Port 9000: Open
✅ Port 55000: Open
```

### Ручная проверка
```powershell
# Проверить Python серверы
Get-ChildItem C:\Workstation\mcp-servers\*.py

# Проверить Docker контейнеры
docker ps

# Проверить порты
Test-NetConnection localhost -Port 9000,9001,55000
```

---

## 🛠️ Troubleshooting

### Проблема: Python модули не найдены
```powershell
pip install aiohttp requests asyncio
```

### Проблема: Docker не запускается
```powershell
# Запустить Docker Desktop
Start-Service docker
```

### Проблема: Порт занят
```powershell
# Найти процесс
netstat -ano | findstr :9000

# Убить процесс
taskkill /PID <PID> /F
```

### Проблема: MCP сервер не виден в GitLab Duo
1. Проверить синтаксис `mcp.json`
2. Перезапустить VS Code
3. Проверить логи: `%APPDATA%\GitLab\duo\logs`

---

## 📈 Производительность

### Рекомендуемые ресурсы
- **RAM**: 16GB (минимум 8GB)
- **CPU**: 4+ ядра
- **Disk**: SSD для Docker volumes
- **Network**: Стабильное подключение для API

### Оптимизация
```json
// Ограничить ресурсы Docker
"volatility": {
  "args": [
    "run", "--rm", "-i",
    "--memory=4g",
    "--cpus=2",
    ...
  ]
}
```

---

## 🔐 Безопасность

### Best Practices
1. ✅ API ключи в переменных окружения
2. ✅ Docker контейнеры изолированы
3. ✅ Только read-only операции в `alwaysAllow`
4. ✅ Логирование всех операций
5. ✅ Ротация токенов каждый месяц

### Meta-Security
```json
"security": {
  "sandboxed_execution": true,
  "zero_trust": true,
  "container_isolation": true,
  "log_sanitization": true,
  "token_encryption": true,
  "meta_security_validation": true
}
```

---

## 📚 Документация

- **Полное руководство**: `docs/MCP_INFRASTRUCTURE_GUIDE.md`
- **MCP Protocol**: https://modelcontextprotocol.io
- **Cortex**: https://github.com/TheHive-Project/Cortex
- **TheHive**: https://github.com/TheHive-Project/TheHive
- **Wazuh**: https://documentation.wazuh.com
- **Volatility**: https://volatility3.readthedocs.io
- **Ghidra**: https://ghidra-sre.org

---

## 🎯 Следующие шаги

1. ✅ Запустить инфраструктуру: `.\scripts\start-mcp-infrastructure.ps1`
2. ✅ Запустить сервисы: `.\start-all-mcp-services.bat`
3. ✅ Проверить здоровье: `.\scripts\check-mcp-health.ps1`
4. ✅ Добавить API ключи (опционально)
5. ✅ Перезапустить GitLab Duo
6. 🚀 Начать пентестинг!

---

## 🔥 Готово к бою!

**Ваша хакерская станция теперь имеет:**
- 🎯 16 специализированных MCP серверов
- 🛡️ Enterprise-level security tools
- 🔍 Threat intelligence integration
- 🧠 Memory forensics capabilities
- 🔬 Reverse engineering tools
- 🚀 Automated workflows

**Welcome to the next level of security operations! 🔥**
