# 🔥 Hacker Workstation MCP Servers Configuration

## 📋 Overview

Enhanced MCP configuration for Security Pentest Workstation with **9 specialized security servers** + existing productivity tools.

**Configuration File:** `mcp-config-enhanced.json`  
**Installation:** Copy to `C:\Users\Администратор\AppData\Roaming\GitLab\duo\mcp.json`

---

## 🛡️ Security MCP Servers

### 1. **Cortex** - Observable Analysis
**Purpose:** Automated threat intelligence and observable analysis

**Capabilities:**
- `cortex_analyze_observable` - Analyze IPs, domains, hashes, URLs
- `cortex_list_analyzers` - List available Cortex analyzers
- `cortex_run_analyzer` - Run specific analyzer on observable

**Configuration:**
```json
{
  "CORTEX_URL": "http://localhost:9001",
  "CORTEX_API_KEY": "your-api-key-here"
}
```

**Example Usage:**
```
Analyze this IP address: 192.168.1.100
Run VirusTotal analyzer on hash: abc123...
```

---

### 2. **TheHive** - Incident Response
**Purpose:** Collaborative security case management

**Capabilities:**
- `thehive_list_cases` - List open/closed cases
- `thehive_create_case` - Create new incident case
- `thehive_get_case_details` - Get case information
- `thehive_add_observable` - Add IOCs to case

**Configuration:**
```json
{
  "THEHIVE_URL": "http://localhost:9000",
  "THEHIVE_API_KEY": "your-api-key-here"
}
```

**Example Usage:**
```
Create incident case for suspicious login attempts
Add IP 10.0.0.5 as observable to case #123
List all critical severity cases
```

---

### 3. **Wazuh** - SIEM Monitoring
**Purpose:** Real-time security event monitoring and threat detection

**Capabilities:**
- `wazuh_list_alerts` - List security alerts
- `wazuh_get_alert_details` - Get alert information
- `wazuh_search_events` - Search security events

**Configuration:**
```json
{
  "WAZUH_URL": "https://localhost:55000",
  "WAZUH_API_TOKEN": "your-token-here"
}
```

**Example Usage:**
```
Show critical alerts from last hour
Search for failed SSH login attempts
Get details for alert ID 12345
```

---

### 4. **Malware Patrol** - Threat Intelligence
**Purpose:** Threat actor intelligence database (200+ profiles)

**Capabilities:**
- `malwarepatrol_list_threat_actors` - List known threat actors
- `malwarepatrol_get_actor_profile` - Get actor details
- `malwarepatrol_search_campaigns` - Search attack campaigns

**Configuration:**
```json
{
  "MALWAREPATROL_TOKEN": "your-token-here"
}
```

**Example Usage:**
```
List APT groups targeting financial sector
Get profile for Lazarus Group
Search campaigns using ransomware
```

---

### 5. **Volatility** - Memory Forensics
**Purpose:** Memory dump analysis and malware detection

**Capabilities:**
- `volatility_analyze_memory_dump` - Analyze memory dump
- `volatility_extract_processes` - Extract running processes
- `volatility_detect_rootkits` - Detect kernel rootkits
- `volatility_timeline_analysis` - Create timeline

**Configuration:**
```json
{
  "MEMORY_DUMPS_PATH": "C:/Workstation/memory-dumps"
}
```

**Example Usage:**
```
Analyze memory dump from infected machine
Extract process list from dump.raw
Detect rootkits in memory image
```

---

### 6. **GhidrAssist** - Reverse Engineering
**Purpose:** Binary analysis with 31 specialized tools

**Capabilities:**
- `ghidra_decompile_binary` - Decompile executable
- `ghidra_analyze_functions` - Analyze function calls
- `ghidra_extract_strings` - Extract strings
- `ghidra_detect_crypto` - Detect cryptographic functions
- `ghidra_find_vulnerabilities` - Find potential vulnerabilities

**Configuration:**
```json
{
  "BINARIES_PATH": "C:/Workstation/binaries",
  "DISPLAY": "host.docker.internal:0"
}
```

**Example Usage:**
```
Decompile malware.exe
Find crypto functions in binary
Extract all strings from suspicious.dll
```

---

### 7. **GitHub Security** - Code Analysis
**Purpose:** Repository security scanning and code analysis

**Capabilities:**
- `github_search_repositories` - Search repos
- `github_create_issue` - Create security issue
- `github_list_commits` - List commits
- `github_analyze_code` - Analyze code security
- `github_security_scan` - Run security scan

**Configuration:**
```json
{
  "GITHUB_TOKEN": "your-github-token"
}
```

**Example Usage:**
```
Scan repository for vulnerabilities
Create security issue for CVE-2024-1234
Analyze code for SQL injection
```

---

### 8. **Docker Pentest** - Container Security
**Purpose:** Container orchestration and security scanning

**Capabilities:**
- `docker_list_containers` - List containers
- `docker_create_container` - Create container
- `docker_execute_command` - Execute in container
- `docker_inspect_image` - Inspect image
- `docker_security_scan` - Scan for vulnerabilities

**Example Usage:**
```
List all running containers
Scan nginx:latest for vulnerabilities
Execute security audit in container
```

---

## 🎯 Pentest Workflows

### Reconnaissance Phase
**Servers:** Cortex, Malware Patrol, Wazuh

**Workflow:**
1. Search threat intelligence (Malware Patrol)
2. Analyze observables (Cortex)
3. Monitor security events (Wazuh)

**Example:**
```
Search for threat actors targeting our industry
Analyze suspicious IP 192.168.1.100 with Cortex
Check Wazuh alerts for related activity
```

---

### Vulnerability Analysis
**Servers:** GitHub Security, Docker Pentest, GhidrAssist

**Workflow:**
1. Scan code repositories (GitHub)
2. Analyze containers (Docker)
3. Reverse engineer binaries (Ghidra)

**Example:**
```
Scan our web app repository for vulnerabilities
Check Docker images for CVEs
Decompile suspicious binary found in container
```

---

### Incident Response
**Servers:** TheHive, Wazuh, Cortex

**Workflow:**
1. Create incident case (TheHive)
2. Gather alerts (Wazuh)
3. Analyze IOCs (Cortex)
4. Document findings (TheHive)

**Example:**
```
Create case for ransomware incident
Get Wazuh alerts from last 24 hours
Analyze malicious IP with Cortex
Add findings to TheHive case
```

---

### Forensics Investigation
**Servers:** Volatility, GhidrAssist

**Workflow:**
1. Analyze memory dump (Volatility)
2. Extract artifacts
3. Reverse engineer malware (Ghidra)
4. Document IOCs

**Example:**
```
Analyze memory dump from compromised server
Extract process list and network connections
Decompile extracted malware binary
```

---

### Threat Hunting
**Servers:** Malware Patrol, Wazuh, Cortex

**Workflow:**
1. Research threat actors (Malware Patrol)
2. Search for IOCs (Wazuh)
3. Analyze suspicious observables (Cortex)

**Example:**
```
Research APT29 tactics and IOCs
Search Wazuh for related indicators
Analyze suspicious domains with Cortex
```

---

## 🔧 Installation

### 1. Copy Configuration
```bash
# Backup existing config
copy "%APPDATA%\GitLab\duo\mcp.json" "%APPDATA%\GitLab\duo\mcp.json.backup"

# Copy new config
copy "C:\Workstation\mcp-config-enhanced.json" "%APPDATA%\GitLab\duo\mcp.json"
```

### 2. Configure API Keys

Edit `mcp.json` and add your API keys:

```json
{
  "cortex": {
    "env": {
      "CORTEX_API_KEY": "your-cortex-key"
    }
  },
  "thehive": {
    "env": {
      "THEHIVE_API_KEY": "your-thehive-key"
    }
  },
  "wazuh": {
    "env": {
      "WAZUH_API_TOKEN": "your-wazuh-token"
    }
  },
  "malwarepatrol": {
    "env": {
      "MALWAREPATROL_TOKEN": "your-malwarepatrol-token"
    }
  },
  "github-security": {
    "env": {
      "GITHUB_TOKEN": "your-github-token"
    }
  }
}
```

### 3. Install Docker Images (Optional)

```bash
# Pull security images
docker pull volatility-mcp/memory-analysis
docker pull ghidrassistmcp/latest
docker pull mcp/github
docker pull mcp/docker
```

### 4. Restart GitLab Duo

Close and reopen VS Code or restart GitLab Duo Chat.

---

## 🛡️ Security Features

### Meta-Security Validation
All MCP servers are validated by the meta-security system:
- ✅ Scanner integrity validation
- ✅ Configuration sandboxing
- ✅ Container isolation
- ✅ Token encryption
- ✅ Log sanitization

### Zero-Trust Architecture
- All servers run in isolated environments
- Docker containers with `--rm` flag (auto-cleanup)
- Read-only volume mounts where possible
- Separate Python processes for each server

### Sandboxed Execution
- Python MCP servers: Isolated processes
- Docker MCP servers: Container isolation
- No direct filesystem access
- Network isolation where applicable

---

## 📊 Server Status

### Always Available (No Setup Required)
- ✅ Perplexity
- ✅ Context7
- ✅ Puppeteer
- ✅ Git
- ✅ Memory
- ✅ Filesystem
- ✅ GigaChat

### Requires API Keys
- ⚙️ Cortex
- ⚙️ TheHive
- ⚙️ Wazuh
- ⚙️ Malware Patrol
- ⚙️ GitHub Security

### Requires Docker Images
- 🐳 Volatility
- 🐳 GhidrAssist
- 🐳 Docker Pentest

---

## 🎓 Usage Examples

### Example 1: Investigate Suspicious IP
```
User: Investigate IP 192.168.1.100

GitLab Duo:
1. Checking Malware Patrol for known threats...
2. Analyzing with Cortex observables...
3. Searching Wazuh alerts...
4. Creating TheHive case...

Results:
- IP associated with Emotet botnet
- 15 Wazuh alerts in last 24h
- Cortex analysis: High risk
- Case #456 created in TheHive
```

### Example 2: Analyze Memory Dump
```
User: Analyze memory dump from infected server

GitLab Duo:
1. Loading dump with Volatility...
2. Extracting process list...
3. Detecting rootkits...
4. Creating timeline...

Findings:
- Suspicious process: svchost.exe (PID 1234)
- Rootkit detected: TDL4
- Network connections to C2: 10.0.0.5:443
- Timeline shows infection at 2025-12-01 10:30
```

### Example 3: Reverse Engineer Malware
```
User: Decompile malware.exe and find crypto functions

GitLab Duo:
1. Loading binary in GhidrAssist...
2. Decompiling...
3. Analyzing functions...
4. Detecting crypto...

Results:
- Binary: PE32 executable
- Crypto: AES-256, RSA-2048
- C2 domains: evil.com, bad.net
- Ransomware variant: LockBit 3.0
```

---

## 🚨 Troubleshooting

### MCP Server Not Responding
```bash
# Check if Python server is running
tasklist | findstr python

# Check Docker containers
docker ps -a

# View logs
type "%APPDATA%\GitLab\duo\mcp.log"
```

### API Key Issues
```bash
# Verify environment variables
echo %CORTEX_API_KEY%
echo %THEHIVE_API_KEY%
```

### Docker Connection Issues
```bash
# Check Docker daemon
docker info

# Test container
docker run --rm hello-world
```

---

## 📚 Resources

- **Cortex:** https://github.com/TheHive-Project/Cortex
- **TheHive:** https://thehive-project.org/
- **Wazuh:** https://wazuh.com/
- **Volatility:** https://www.volatilityfoundation.org/
- **Ghidra:** https://ghidra-sre.org/
- **Malware Patrol:** https://malwarepatrol.net/

---

## ✅ Next Steps

1. ✅ Copy `mcp-config-enhanced.json` to GitLab Duo config
2. ⚙️ Configure API keys for security servers
3. 🐳 Install Docker images (optional)
4. 🔄 Restart GitLab Duo
5. 🎯 Start pentesting!

---

**Created:** 2025-12-01  
**Version:** 2.0.0  
**Workstation:** Security Pentest Station  
**Mode:** BUILDER → EXECUTOR ready
