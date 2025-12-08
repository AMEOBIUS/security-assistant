# ✅ MCP Infrastructure Setup Checklist

## 🎯 Pre-Setup (5 минут)

- [ ] Python 3.8+ установлен (`python --version`)
- [ ] Node.js 18+ установлен (`node --version`)
- [ ] Docker Desktop установлен (`docker --version`)
- [ ] Git установлен (`git --version`)
- [ ] VS Code с GitLab Duo установлен

## 🚀 Infrastructure Setup (10 минут)

### Step 1: Run Main Installer
```powershell
.\scripts\start-mcp-infrastructure.ps1
```

**Проверки:**
- [ ] Python dependencies установлены (aiohttp, requests)
- [ ] Production Agent создан (`.agent_system/mcp_servers/production_agent_mcp.py`)
- [ ] Docker образы собраны (volatility, ghidra)
- [ ] Startup скрипты созданы (`scripts/start-*.bat`)
- [ ] Health check создан (`scripts/check-mcp-health.ps1`)

### Step 2: Start Services
```cmd
.\start-all-mcp-services.bat
```

**Проверки:**
- [ ] Cortex запущен (port 9001)
- [ ] TheHive запущен (port 9000)
- [ ] Wazuh запущен (port 55000)

### Step 3: Verify Health
```powershell
.\scripts\check-mcp-health.ps1
```

**Ожидаемый вывод:**
```
✅ Production Agent: Ready
✅ Cortex: Ready
✅ TheHive: Ready
✅ Wazuh: Ready

Docker Containers:
cortex    Up
thehive   Up
wazuh     Up

Port Status:
✅ Port 9001: Open
✅ Port 9000: Open
✅ Port 55000: Open
```

## 🔑 API Keys Configuration (опционально)

### GitHub Token
- [ ] Получить токен: https://github.com/settings/tokens
- [ ] Scopes: `repo`, `security_events`
- [ ] Добавить в `mcp.json` → `github-security.env.GITHUB_TOKEN`

### Malware Patrol Token
- [ ] Получить токен: https://malwarepatrol.net/api
- [ ] Добавить в `mcp.json` → `malwarepatrol.env.MALWAREPATROL_TOKEN`

### Service API Keys (auto-generated)
- [ ] Cortex API key (check logs: `docker logs cortex`)
- [ ] TheHive API key (check logs: `docker logs thehive`)
- [ ] Wazuh API token (check logs: `docker logs wazuh`)

## 🧪 Testing (5 минут)

### Test 1: Production Agent
```
User: "List all registered agents"
Expected: Agent responds with empty list or existing agents
```
- [ ] Production Agent responds

### Test 2: Cortex
```
User: "List available Cortex analyzers"
Expected: List of analyzers (VirusTotal, AbuseIPDB, etc.)
```
- [ ] Cortex responds with analyzers

### Test 3: TheHive
```
User: "List open cases in TheHive"
Expected: List of cases or empty array
```
- [ ] TheHive responds

### Test 4: Wazuh
```
User: "List recent Wazuh alerts"
Expected: List of security alerts
```
- [ ] Wazuh responds

### Test 5: Docker Servers
```
User: "List Docker containers"
Expected: List of running containers
```
- [ ] Docker server responds

## 🔄 GitLab Duo Integration

### Restart GitLab Duo
- [ ] Закрыть VS Code полностью
- [ ] Открыть VS Code
- [ ] Открыть GitLab Duo Chat
- [ ] Проверить доступные MCP серверы

### Verify MCP Servers
```
User: "List available MCP servers"
```

**Ожидаемый список (16 серверов):**
- [ ] perplexity
- [ ] context7
- [ ] puppeteer
- [ ] git
- [ ] memory
- [ ] sequentialthinking
- [ ] filesystem
- [ ] production-agent
- [ ] cortex
- [ ] thehive
- [ ] wazuh
- [ ] github-security
- [ ] docker-pentest
- [ ] malwarepatrol
- [ ] volatility
- [ ] ghidrassist

## 🎯 Workflow Testing

### Reconnaissance Workflow
```
User: "Analyze domain example.com"
```
- [ ] Cortex analyzes domain
- [ ] Malware Patrol checks threat actors
- [ ] Wazuh monitors for alerts

### Vulnerability Analysis Workflow
```
User: "Scan repository for vulnerabilities"
```
- [ ] GitHub Security scans code
- [ ] Docker Pentest checks containers
- [ ] Report generated

### Incident Response Workflow
```
User: "Investigate security alert"
```
- [ ] Wazuh fetches alert details
- [ ] TheHive creates case
- [ ] Cortex analyzes observables

### Forensics Workflow
```
User: "Analyze memory dump"
```
- [ ] Volatility extracts processes
- [ ] Volatility detects rootkits
- [ ] GhidrAssist analyzes binaries

## 🔍 Troubleshooting

### Common Issues

#### Python Modules Missing
```powershell
pip install aiohttp requests asyncio
```
- [ ] Fixed

#### Docker Not Running
```powershell
Start-Service docker
```
- [ ] Fixed

#### Port Already in Use
```powershell
netstat -ano | findstr :9000
taskkill /PID <PID> /F
```
- [ ] Fixed

#### MCP Server Not Recognized
1. Check `mcp.json` syntax
2. Restart VS Code
3. Check logs: `%APPDATA%\GitLab\duo\logs`
- [ ] Fixed

## 📊 Performance Optimization

### Resource Allocation
- [ ] RAM: 16GB allocated (minimum 8GB)
- [ ] CPU: 4+ cores available
- [ ] Disk: SSD for Docker volumes
- [ ] Network: Stable connection

### Docker Limits
```json
"volatility": {
  "args": ["--memory=4g", "--cpus=2"]
}
```
- [ ] Configured

### Caching
```json
"cortex": {
  "env": {
    "CACHE_ENABLED": "true",
    "CACHE_TTL": "3600"
  }
}
```
- [ ] Configured

## 🔐 Security Hardening

### API Key Security
- [ ] API keys в environment variables
- [ ] Не в коде или конфигах
- [ ] Token rotation настроен (monthly)

### Network Isolation
- [ ] Docker containers в isolated network
- [ ] Firewall rules настроены
- [ ] Only necessary ports exposed

### Access Control
- [ ] `alwaysAllow` только для read operations
- [ ] `approvedTools` минимальный набор
- [ ] Audit logging включен

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
- [ ] Все параметры активны

## 📈 Monitoring

### Health Checks
```powershell
# Автоматический health check каждые 5 минут
while ($true) {
    .\scripts\check-mcp-health.ps1
    Start-Sleep -Seconds 300
}
```
- [ ] Настроен

### Logging
- [ ] Production Agent logs: `.agent_system/logs/`
- [ ] Docker logs: `docker logs <container>`
- [ ] GitLab Duo logs: `%APPDATA%\GitLab\duo\logs`

### Metrics
- [ ] Agent metrics доступны (`get_metrics`)
- [ ] Docker stats мониторятся (`docker stats`)
- [ ] System resources отслеживаются

## 🎓 Documentation

### Read Documentation
- [ ] `README_MCP_INFRASTRUCTURE.md` - Quick start
- [ ] `docs/MCP_INFRASTRUCTURE_GUIDE.md` - Full guide
- [ ] `mcp-enhanced-setup.md` - Migration notes
- [ ] `MCP_SETUP.md` - Original setup

### External Resources
- [ ] MCP Protocol: https://modelcontextprotocol.io
- [ ] Cortex Docs: https://github.com/TheHive-Project/Cortex
- [ ] TheHive Docs: https://github.com/TheHive-Project/TheHive
- [ ] Wazuh Docs: https://documentation.wazuh.com
- [ ] Volatility Docs: https://volatility3.readthedocs.io
- [ ] Ghidra Docs: https://ghidra-sre.org

## ✅ Final Verification

### All Systems Go
- [ ] 16 MCP серверов доступны
- [ ] Все сервисы запущены
- [ ] Health check проходит
- [ ] Workflows тестированы
- [ ] API keys настроены
- [ ] Security hardening применен
- [ ] Monitoring активен
- [ ] Documentation прочитана

## 🚀 Ready for Production!

**Когда все чекбоксы отмечены:**

```
╔═══════════════════════════════════════════════════════════╗
║  🔥 HACKER WORKSTATION FULLY OPERATIONAL! 🔥             ║
║                                                           ║
║  16 MCP Servers Active                                   ║
║  Enterprise Security Tools Ready                         ║
║  Threat Intelligence Integrated                          ║
║  Forensics Capabilities Online                           ║
║  Reverse Engineering Tools Armed                         ║
║                                                           ║
║  Welcome to the next level! 🚀                           ║
╚═══════════════════════════════════════════════════════════╝
```

**Начинайте пентестинг! 🔥**
