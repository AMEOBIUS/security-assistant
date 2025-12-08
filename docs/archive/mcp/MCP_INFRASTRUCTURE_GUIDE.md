# 🚀 MCP Infrastructure - Complete Setup Guide

## 📋 Overview

Полная инфраструктура для хакерской станции с 16 MCP серверами:

**Active (7):** perplexity, context7, puppeteer, git, memory, sequentialthinking, filesystem  
**Pending (9):** production-agent, cortex, thehive, wazuh, github-security, docker-pentest, malwarepatrol, volatility, ghidrassist

---

## 🎯 Quick Start (5 минут)

### Step 1: Run Infrastructure Setup
```powershell
.\scripts\start-mcp-infrastructure.ps1
```

**Что делает скрипт:**
- ✅ Проверяет Python, Docker, Node.js
- ✅ Устанавливает зависимости (aiohttp, requests)
- ✅ Создает Production Agent MCP сервер
- ✅ Собирает Docker образы (Volatility, GhidrAssist)
- ✅ Создает startup скрипты для сервисов
- ✅ Генерирует health check утилиту

### Step 2: Start Services
```cmd
.\start-all-mcp-services.bat
```

**Запускает:**
- Cortex (port 9001)
- TheHive (port 9000)
- Wazuh (port 55000)

### Step 3: Verify Health
```powershell
.\scripts\check-mcp-health.ps1
```

### Step 4: Restart GitLab Duo
Перезапустите VS Code или GitLab Duo для загрузки новых серверов.

---

## 🔧 Manual Setup (если нужен контроль)

### Python Servers

#### 1. Production Agent
```powershell
# Already created by infrastructure script
python C:\Workstation\.agent_system\mcp_servers\production_agent_mcp.py
```

#### 2. Cortex
```powershell
# Start Cortex service first
docker run -d -p 9001:9001 thehiveproject/cortex:latest

# MCP server already exists
python C:\Workstation\mcp-servers\cortex-mcp.py
```

#### 3. TheHive
```powershell
# Start TheHive service first
docker run -d -p 9000:9000 thehiveproject/thehive:latest

# MCP server already exists
python C:\Workstation\mcp-servers\thehive-mcp.py
```

#### 4. Wazuh
```powershell
# Start Wazuh service first
docker run -d -p 55000:55000 wazuh/wazuh:latest

# MCP server already exists
python C:\Workstation\mcp-servers\wazuh-mcp.py
```

### Docker Servers

#### 5. GitHub Security
```powershell
# Set GitHub token
$env:GITHUB_TOKEN = "your_token_here"

# Already configured in mcp.json
```

#### 6. Docker Pentest
```powershell
# Requires Docker socket access
# Already configured in mcp.json
```

#### 7. Volatility
```powershell
# Build image (done by infrastructure script)
docker build -t volatility-mcp/memory-analysis -f docker-mcp/Dockerfile.volatility .

# Place memory dumps in C:\Workstation\memory-dumps
```

#### 8. GhidrAssist
```powershell
# Build image (done by infrastructure script)
docker build -t ghidrassistmcp/latest -f docker-mcp/Dockerfile.ghidra .

# Place binaries in C:\Workstation\binaries
```

### Inline Python

#### 9. Malware Patrol
```powershell
# Set API token in mcp.json
"env": {
  "MALWAREPATROL_TOKEN": "your_token_here"
}
```

---

## 🔑 API Keys & Tokens

### Required Tokens

1. **Perplexity** (Already set)
   - Location: `mcp.json` → `perplexity.env.PERPLEXITY_API_KEY`
   - Status: ✅ Active

2. **Context7** (Already set)
   - Location: `mcp.json` → `context7.env.CONTEXT7_API_KEY`
   - Status: ✅ Active

3. **GitHub** (Optional)
   - Location: `mcp.json` → `github-security.env.GITHUB_TOKEN`
   - Get token: https://github.com/settings/tokens
   - Scopes: `repo`, `security_events`

4. **Malware Patrol** (Optional)
   - Location: `mcp.json` → `malwarepatrol.env.MALWAREPATROL_TOKEN`
   - Get token: https://malwarepatrol.net/api

5. **Cortex/TheHive/Wazuh** (Auto-generated)
   - Generated on first service start
   - Check service logs for API keys

---

## 📊 Server Status Matrix

| Server | Type | Status | Port | Dependencies |
|--------|------|--------|------|--------------|
| perplexity | NPX | ✅ Active | - | API Key |
| context7 | NPX | ✅ Active | - | API Key |
| puppeteer | NPX | ✅ Active | - | None |
| git | NPX | ✅ Active | - | None |
| memory | NPX | ✅ Active | - | None |
| sequentialthinking | NPX | ✅ Active | - | None |
| filesystem | NPX | ✅ Active | - | None |
| production-agent | Python | 🟡 Ready | - | aiohttp |
| cortex | Python | 🟡 Ready | 9001 | Docker, aiohttp |
| thehive | Python | 🟡 Ready | 9000 | Docker, aiohttp |
| wazuh | Python | 🟡 Ready | 55000 | Docker, aiohttp |
| github-security | Docker | 🟡 Ready | - | Token |
| docker-pentest | Docker | 🟡 Ready | - | Docker socket |
| malwarepatrol | Inline | 🟡 Ready | - | Token |
| volatility | Docker | 🟡 Ready | - | Image built |
| ghidrassist | Docker | 🟡 Ready | - | Image built |

**Legend:**
- ✅ Active: Currently running
- 🟡 Ready: Configured, needs manual start
- ❌ Missing: Not configured

---

## 🎯 Pentest Workflows

### Reconnaissance
```
User: "Start reconnaissance on target.com"

Agent uses:
- cortex → Analyze domain observables
- malwarepatrol → Check threat actor associations
- wazuh → Monitor for suspicious activity
```

### Vulnerability Analysis
```
User: "Analyze binary sample.exe"

Agent uses:
- ghidrassist → Decompile and analyze
- volatility → Memory forensics (if dump available)
- github-security → Check for known vulnerabilities
```

### Incident Response
```
User: "Investigate security alert #1234"

Agent uses:
- thehive → Create case
- wazuh → Fetch alert details
- cortex → Analyze observables
```

### Forensics
```
User: "Analyze memory dump from compromised host"

Agent uses:
- volatility → Extract processes, detect rootkits
- ghidrassist → Analyze suspicious binaries
```

---

## 🔍 Troubleshooting

### Python Servers Not Starting

**Problem:** `ModuleNotFoundError: No module named 'aiohttp'`

**Solution:**
```powershell
pip install aiohttp requests asyncio
```

### Docker Containers Not Running

**Problem:** `Cannot connect to Docker daemon`

**Solution:**
```powershell
# Start Docker Desktop
# Or check Docker service
Get-Service docker
Start-Service docker
```

### Port Already in Use

**Problem:** `Port 9000 already in use`

**Solution:**
```powershell
# Find process using port
netstat -ano | findstr :9000

# Kill process
taskkill /PID <PID> /F
```

### MCP Server Not Recognized

**Problem:** GitLab Duo doesn't see new servers

**Solution:**
1. Check `mcp.json` syntax (valid JSON)
2. Restart VS Code completely
3. Check GitLab Duo logs: `%APPDATA%\GitLab\duo\logs`

---

## 🚀 Advanced Configuration

### Custom Analyzer Paths

Edit `mcp.json` to customize paths:

```json
"cortex": {
  "args": ["C:/Custom/Path/cortex-mcp.py"]
}
```

### Resource Limits

For Docker servers, add resource limits:

```json
"volatility": {
  "args": [
    "run", "--rm", "-i",
    "--memory=4g",
    "--cpus=2",
    "-v", "C:/Workstation/memory-dumps:/dumps:ro",
    "volatility-mcp/memory-analysis"
  ]
}
```

### Logging

Enable verbose logging:

```json
"production-agent": {
  "env": {
    "LOG_LEVEL": "DEBUG"
  }
}
```

---

## 📈 Performance Optimization

### Parallel Execution

MCP servers run independently. For best performance:

1. **Use SSD** for Docker volumes
2. **Allocate RAM**: 8GB minimum, 16GB recommended
3. **CPU cores**: 4+ cores for parallel analysis

### Caching

Enable caching for frequently used analyzers:

```json
"cortex": {
  "env": {
    "CACHE_ENABLED": "true",
    "CACHE_TTL": "3600"
  }
}
```

---

## 🔐 Security Best Practices

1. **API Keys**: Store in environment variables, not in code
2. **Network Isolation**: Run Docker containers in isolated network
3. **Least Privilege**: Use `alwaysAllow` only for read operations
4. **Audit Logs**: Enable logging for all MCP operations
5. **Token Rotation**: Rotate API tokens monthly

---

## 📚 Resources

- **MCP Protocol**: https://modelcontextprotocol.io
- **Cortex Docs**: https://github.com/TheHive-Project/Cortex
- **TheHive Docs**: https://github.com/TheHive-Project/TheHive
- **Wazuh Docs**: https://documentation.wazuh.com
- **Volatility Docs**: https://volatility3.readthedocs.io
- **Ghidra Docs**: https://ghidra-sre.org

---

## 🎯 Next Steps

1. ✅ Run infrastructure setup
2. ✅ Start services
3. ✅ Verify health
4. ✅ Test with simple query
5. 🚀 Start pentesting!

**Your hacker workstation is now fully armed! 🔥**
