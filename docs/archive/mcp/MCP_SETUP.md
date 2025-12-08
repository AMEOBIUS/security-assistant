# 🚀 Quick Setup: Hacker MCP Servers

## ⚡ Fast Installation (5 минут)

### Step 1: Backup Current Config
```cmd
copy "%APPDATA%\GitLab\duo\mcp.json" "%APPDATA%\GitLab\duo\mcp.json.backup"
```

### Step 2: Open Both Files
1. **Current config:** `C:\Users\Администратор\AppData\Roaming\GitLab\duo\mcp.json`
2. **New config:** `C:\Workstation\mcp-config-enhanced.json`

### Step 3: Copy New Servers
Добавь эти секции в твой `mcp.json` (после `gigachat`):

```json
    "cortex": {
      "type": "stdio",
      "command": "python",
      "args": ["C:/Workstation/mcp-servers/cortex-mcp.py"],
      "env": {
        "CORTEX_URL": "http://localhost:9001",
        "CORTEX_API_KEY": ""
      },
      "approvedTools": [
        "cortex_analyze_observable",
        "cortex_list_analyzers",
        "cortex_run_analyzer"
      ],
      "alwaysAllow": ["cortex_list_analyzers"],
      "description": "🔍 Cortex - Observable analysis"
    },

    "thehive": {
      "type": "stdio",
      "command": "python",
      "args": ["C:/Workstation/mcp-servers/thehive-mcp.py"],
      "env": {
        "THEHIVE_URL": "http://localhost:9000",
        "THEHIVE_API_KEY": ""
      },
      "approvedTools": [
        "thehive_list_cases",
        "thehive_create_case",
        "thehive_get_case_details",
        "thehive_add_observable"
      ],
      "alwaysAllow": ["thehive_list_cases"],
      "description": "🎯 TheHive - Incident response"
    },

    "wazuh": {
      "type": "stdio",
      "command": "python",
      "args": ["C:/Workstation/mcp-servers/wazuh-mcp.py"],
      "env": {
        "WAZUH_URL": "https://localhost:55000",
        "WAZUH_API_TOKEN": ""
      },
      "approvedTools": [
        "wazuh_list_alerts",
        "wazuh_get_alert_details",
        "wazuh_search_events"
      ],
      "alwaysAllow": ["wazuh_list_alerts"],
      "description": "🛡️ Wazuh - SIEM monitoring"
    }
```

### Step 4: Save & Restart
1. Сохрани `mcp.json`
2. Перезапусти VS Code или GitLab Duo

---

## ✅ Verification

Проверь что серверы работают:

```
User: List available MCP servers

Expected: Should see cortex, thehive, wazuh in the list
```

---

## 🔑 API Keys (Optional)

Если хочешь использовать серверы, добавь API ключи:

```json
"cortex": {
  "env": {
    "CORTEX_API_KEY": "your-key-here"
  }
}
```

---

## 🎯 Quick Test

```
User: Analyze IP 8.8.8.8 with Cortex

Expected: Cortex should attempt to analyze the IP
```

---

## 📁 Files Created

- ✅ `mcp-config-enhanced.json` - Full config with all servers
- ✅ `docs/mcp-servers-guide.md` - Complete documentation
- ✅ `mcp-servers/cortex-mcp.py` - Cortex server (by DROID)
- ✅ `mcp-servers/thehive-mcp.py` - TheHive server (by DROID)
- ✅ `mcp-servers/wazuh-mcp.py` - Wazuh server (by DROID)

---

## 🚨 Troubleshooting

**Problem:** MCP server not found  
**Solution:** Check file paths in `args` are correct

**Problem:** Python error  
**Solution:** Install dependencies: `pip install aiohttp`

**Problem:** API connection failed  
**Solution:** Check if Cortex/TheHive/Wazuh are running

---

**Ready to hack! 🔥**
